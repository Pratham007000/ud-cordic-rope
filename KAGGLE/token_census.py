#!/usr/bin/env python3
"""How many tokens does the paper actually evaluate on?

The paper states evaluation is the *full* WikiText-2 raw test split. A run
launched with --max_tokens silently evaluates a prefix instead, and the only
record of that is total_tokens in the result JSON. This script answers two
questions without a GPU and without downloading model weights:

  1. How many tokens is the full split, per tokenizer? Tokenizers differ, so
     there is no single number to quote.
  2. Which of your completed runs were truncated? Point --scan at the
     directory holding the result JSONs.

Run it on Kaggle, where transformers and datasets are already present.

    python token_census.py                       # count the full split
    python token_census.py --scan /kaggle/working   # audit finished runs
    python token_census.py --scan . --max_tokens 150000

Tokenizer downloads for gated repos (LLaMA-2) need HF_TOKEN set, the same way
eval_perplexity.py does. Open models need nothing.
"""
import argparse, glob, json, os, sys

# Models the paper reports. Gated ones are marked; a missing token is not
# fatal, the script just reports them as unavailable and carries on.
MODELS = [
    ("meta-llama/Llama-2-7b-hf", 10**4, True),
    ("Qwen/Qwen2-7B",            10**6, False),
    ("mistralai/Mistral-7B-v0.1", 10**4, True),
    ("tiiuae/falcon-7b",          10**4, False),
    ("EleutherAI/gpt-neox-20b",   10**4, False),
]


def load_split_text():
    from datasets import load_dataset
    try:
        ds = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")
    except Exception:
        ds = load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1",
                          split="test")
    # Identical joining to eval_perplexity.py. If these two ever diverge the
    # counts below stop describing the evaluation.
    return "\n\n".join(ds["text"])


def count_full_split(max_tokens):
    from transformers import AutoTokenizer
    text = load_split_text()
    print(f"\nWikiText-2 raw test split: {len(text):,} characters\n")
    print(f"{'model':34} {'base':>8} {'full tokens':>13} "
          f"{'{} is'.format(max_tokens):>12}")
    print("-" * 72)
    for name, base, gated in MODELS:
        try:
            tok = AutoTokenizer.from_pretrained(name)
            n = tok(text, return_tensors="pt").input_ids.shape[1]
        except Exception as e:
            why = "gated, needs HF_TOKEN" if gated else type(e).__name__
            print(f"{name:34} {base:>8} {'unavailable':>13}   ({why})")
            continue
        frac = f"{100.0 * max_tokens / n:.0f}% of it" if max_tokens else "-"
        print(f"{name:34} {base:>8} {n:>13,} {frac:>12}")
    print()


def scan_runs(d, max_tokens):
    paths = sorted(glob.glob(os.path.join(d, "**", "*.json"), recursive=True))
    rows = []
    for p in paths:
        try:
            with open(p) as fh:
                j = json.load(fh)
            meta = j.get("meta", {})
            if "total_tokens" not in meta:
                continue
            rows.append((os.path.basename(p), meta.get("model", "?"),
                         meta.get("total_tokens"), meta.get("rope_theta"),
                         bool(meta.get("rope_theta_overridden"))))
        except Exception:
            continue

    if not rows:
        print(f"\nNo result JSONs with a total_tokens field under {d}\n")
        return

    print(f"\n{'file':40} {'model':26} {'tokens':>9}  {'base':>9} ovr")
    print("-" * 94)
    for f, m, t, base, ovr in rows:
        print(f"{f:40} {m[-26:]:26} {t:>9,}  {base:>9} {'yes' if ovr else ''}")

    counts = {t for _, _, t, _, _ in rows}
    print()
    if max_tokens and counts == {max_tokens}:
        print(f"Every run evaluated exactly {max_tokens:,} tokens, so each was "
              f"truncated.\nThe paper must not call this the full test split.")
    elif len(counts) > 1:
        print("Runs disagree on token count:", ", ".join(f"{c:,}" for c in
                                                         sorted(counts)))
        print("Perplexities are only comparable across runs with equal counts.")
    else:
        print(f"All runs evaluated {counts.pop():,} tokens. Compare that "
              f"against the full-split figure above\nbefore describing it as "
              f"the whole split.")
    print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", metavar="DIR",
                    help="audit result JSONs under DIR instead of counting")
    ap.add_argument("--max_tokens", type=int, default=150000,
                    help="the truncation length to check against")
    ap.add_argument("--both", action="store_true",
                    help="scan, then also count the full split")
    a = ap.parse_args()

    if a.scan:
        scan_runs(a.scan, a.max_tokens)
        if not a.both:
            sys.exit(0)
    count_full_split(a.max_tokens)
