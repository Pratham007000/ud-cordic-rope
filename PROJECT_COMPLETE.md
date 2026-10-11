# UD-CORDIC RoPE Accelerator — Complete Project Record

**APCCAS 2026 rejection → ISCAS 2027 submission.**

| | |
|---|---|
| Written | 2026-10-09 |
| Deadline | **2026-10-13** — 4 days |
| Prior submission | APCCAS 2026 #2130 — rejected |
| Target | ISCAS 2027 · 4 pages technical + 1 references page · not double-blind |
| Experiments | **Complete** — 17/17 synthesis runs, 0 failures |
| Manuscript | **Complete** — 0 placeholders, 27 citations, 3 tables, 1 figure |
| Remaining | Page fit (±2 lines), repo URL, author names |

Supersedes `PROJECT_NARRATIVE.md` (2026-09-27), written before the synthesis
data landed. `ISCAS_REVISION_PLAN.md` remains the operational checklist.

---

## 1. One page

The submitted paper claimed a multiplier-free RoPE accelerator on UD-CORDIC.
Four reviewers rejected it, most seriously on the grounds that its novelty
belonged to the prior work it built on. Investigation found deeper problems the
reviewers had missed: **the angle encoder never converged**, so every accuracy
number was wrong; **the recommended precision was wrong by three bits**; **the
datapath could not hold real LLM activations at all**; and **the headline
architecture was named after a digit set it does not implement**.

All four are fixed, measured and written up. Three genuinely new results came
out of the repair work. The synthesis campaign then **overturned the paper's
central claim once and rebuilt it on a sounder basis**, and **reversed the
choice of headline architecture**. What remains is cosmetic.

---

## 2. What the reviewers said

| | Objection | Status |
|---|---|---|
| **P1** | **Novelty not established** — Z-path removal and stage merging come from prior UD-CORDIC work | Answered: three RoPE-specific results, §I restructured to lead with them |
| P2 | Related-work survey incomplete for RoPE-specific hardware | Answered: 27 citations, prior-work comparison in §IV-B |
| P3 | Missing detail: angle range, gain compensation, Binary UD encoding, incomplete Eq. 8, power methodology | All answered with measurements |
| P4 | No latency/throughput/energy, no integration cost | Answered: §IV-B carries all three |
| P5 | No block diagram; FP8/FP4 not considered | Fig. 1 added; block-floating-point discussion in §III-B |

**ISCAS has no rebuttal phase**, so every objection had to be answered inside
the manuscript. That constraint shaped the whole revision.

---

## 3. The four things that were actually wrong

### 3.1 The angle encoder never converged

A UD-CORDIC stage rotates by `arctan(2^-(i+1))`, not `2^-(i+1)`. Those weights
are only approximately geometric — 0.927, 0.980, 0.995, 0.999 — so taking
digits straight from the binary representation of θ, which is what the UD
formulation implies, **mis-encodes the leading stages with an error independent
of pipeline depth**.

The evidence was in the published Table I and nobody saw it: the error barely
moved with N. Binary UD 3.88° → 2.20° on doubling the stages; merged 3.38° →
3.13°. A working datapath improves ~4× per doubling. A flat column is the
signature of an encoder that never converged.

**Fix:** the tail is geometric to better than 0.13%, so only the two leading
stages need explicit resolution. One adder, three constant comparators, a 4:1
mux, one subtractor — fully combinational, so the Z-path-free property
survives.

| Method | N | Published | Corrected | change |
|---|---|---|---|---|
| Binary UD | 5 | 3.88° | 2.004° | 2× |
| Binary UD | 10 | 2.20° | **0.0634°** | 35× |
| Merged UD | 5 | 3.38° | **0.0431°** | 78× |

Synthesised: **136 µm²**, 0.094° RMS (the 0.0634° is the algorithmic bound).

### 3.2 Fixed-point RoPE cannot hold real activations

At F=14 — nearly full precision — perplexity came out 27034 against a baseline
of 5.5, with a rotation error of only 0.00165. The rotation was fine.

Hooking Qwen2 showed why: **|q| reaches 132 and |k| reaches 178**, median ~20,
against the [−2, 2) range of Q(1,F). The datapath saturated on essentially
every value. Block floating point is a **functional requirement**, absent from
the published paper entirely.

Synthesised: 824 µm²/lane at W=14 including the return path, 19% of a rotator.
Architecture-neutral — the multiplier and LUT need it too.

### 3.3 The precision claim was wrong by three bits

Published: "F=7 saturates, F=9 optimal." Measured:

| F | LLaMA-2-7B | Qwen2-7B |
|---|---|---|
| 11 | +0.005% | +0.018% |
| 10 | +0.020% | +0.103% |
| 9 | +0.078% | **+6.36%** |
| 8 | +0.318% | +131% |

The models disagree by two bits, and **not because of scale** — both are 7B
with the same head dimension. Qwen2 uses a RoPE base of 10⁶ against LLaMA-2's
10⁴, so Θᵢ spans a far wider range and the low-frequency pairs get angles too
small to resolve. Below the LSB a pair **stops rotating entirely** and its
positional signal is discarded rather than degraded — a cliff, not a slope.

Recommendation: **F=11 (W=13)**.

### 3.4 The architecture was named after a digit set it does not implement

`csd_control.v` implements textbook radix-4 Booth, emitting {0, ±1, ±2}
**assuming weight 2**. But `csd_ud_stage.v` builds the magnitude-2 digit as
`x_s1 + x_s2` with SHIFT1 = 2i, SHIFT2 = 2i+1:

```
x·2^-2i + x·2^-(2i+1) = 1.5 · x · 2^-2i
```

**The digit labelled `+2` is physically a ×1.5.** Control and datapath disagree
by 4/3 on the largest digit. The realised set {0, ±1, ±3/2} is neither CSD nor
Booth. Renamed **merged UD-CORDIC**.

Worse, on regeneration the textbook ±2 set proved **better on both axes** —
marginally more accurate (0.040° vs 0.043° at N=5) and strictly cheaper (±2 is
a single shift, no adder). Its only deficit is gain spread, which matters only
because merged UD needs compensation anyway. The paper now says the 3/2 set is
reported because it is what was synthesised, not because it is preferable.

---

## 4. What the synthesis campaign changed

All 17 runs, zero failures. Two findings reversed earlier conclusions.

### 4.1 The crossover claim was overturned, then rebuilt

Before synthesis, a fit on two measured word lengths put the multiplier/CORDIC
area crossover at **W ≈ 11.3**, below the measured precision requirement of
W=13. That was the paper's spine.

**It did not survive.** The fit used merged-UD *datapath only*, before gain
compensation existed as a measured quantity. H1 came in at 886/1032 µm² against
an estimated ~150, moving the crossover against the bare multiplier to
**W ≈ 15** — above the operating point. At W=12–14 the bare multiplier is
13–16% *smaller* than either CORDIC variant.

**The rebuild:** `LUT − multiplier = 955 µm² (W=12), 1190 µm² (W=14)`. That
difference *is* the sin/cos storage. **The LUT row is the completed
multiplier-based design**; the bare multiplier is the same design with its
angle source deleted. Against the completed design, CORDIC wins at every width.

### 4.2 The headline architecture flipped

| | Binary UD | Merged UD + H1 |
|---|---|---|
| Area @ W=14 | **4346** | 4499 |
| Energy @ W=14 | 5.61 pJ | **3.72 pJ** |
| Gain error | **zero by construction** | 0.6–0.8% perplexity |
| Encoder | **built, 136 µm²** | constant table, not built |

Merged UD + **H2** reaches 5286 µm² — **940 µm² worse than Binary UD**, which
has zero gain error. H2 is strictly dominated. S-13 therefore lands as a
verdict: merging saves 879 µm² of datapath, then forfeits the property that
makes the scale factor free and spends 1032–1819 µm² buying a weaker version
back. **Binary UD leads; merged UD is the energy-optimal variant.**

### 4.3 Finer BFP blocks are better on all three axes

| D | area (64 pairs) | rot. error | slack |
|---|---|---|---|
| 8 | **22112 µm²** | **0.00120** | **293 ps** |
| 64 | 23877 µm² | 0.00204 | 4 ps |

7% cheaper, 1.7× more accurate, 73× more timing margin. The paper previously
argued for the coarse block "to save logic on 63 of every 64 lanes" — that
justification was wrong. Now recommends **D=8**.

### 4.4 Cross-validation

Runs 14 and 15 reproduced the earlier campaign **exactly** — 3961 and
4346 µm². Old and new numbers sit on one measurement basis, which the paper
states.

---

## 5. Final measured results

**Complete RoPE units, 45 nm, 500 MHz, identical flow/library/corner**

| W=14 | Area µm² | Power mW | Energy pJ | Slack ps |
|---|---|---|---|---|
| Std CORDIC (N=10) | 5378 | 4.896 | 9.79 | 1174 |
| Sin/cos LUT | 5375 | 4.544 | 9.09 | **26** |
| Multiplier† | 4185 | 2.092 | 4.18 | 600 |
| **Binary UD (N=10)** | **4346** | 2.805 | 5.61 | **1342** |
| Merged UD (N=5) + H1 | 4499 | **1.860** | **3.72** | 1105 |

† not a complete unit — consumes sin/cos it does not generate

**Headline claims:**
- vs standard CORDIC @ W=14: **19.2% area, 42.7% power**
- vs LUT (only self-contained baseline) @ W=14: **19.1% area, 38% energy**
- @ W=12: areas comparable; **18% less energy, 1499 ps slack vs 201 ps**

---

## 6. Obstacles along the way

| | What happened | Cost |
|---|---|---|
| **Perplexity double shift** | Pre-shifted targets passed to `labels=`, framework shifts internally → scored P(t+2\|t). Baseline 18738 instead of ~7. A tiny-model smoke test could not catch it — a uniform-output model is shift-invariant. | ~1 day |
| **Silent config no-op** | A rope-base experiment returned byte-identical results for all three bases. `cfg.rope_theta` does not exist in transformers 5.x; the value lives in `cfg.rope_parameters`. The log said `None -> 10000.0` and the `None` was missed. | ~1 day |
| **Confounded re-run** | After the fix, LLaMA-2 forced to base 10⁶ degraded its *own* baseline 2.45×, so deltas were measured against a broken model. Experiment abandoned; replaced with an analytical derivation. | ~0.5 day |
| **Comparison basis wrong** | Merged UD at N stages was being compared against standard at N stages, giving it 2× the precision free. **Caught by the user, not by us.** Every area claim depended on it. | reopened the verdict |
| **Config shim broke two models** | Clearing `rope_scaling` fixed Phi-3, broke Falcon and Gemma-2 — the fields are aliases in transformers 5.x. Made opt-in. | ~0.5 day |
| **Gemma-2 needs bf16** | fp16 baseline came out 196.88. Caught automatically by a plausibility guard. Dropped from the model set. | model set 7 → 5 |
| **BFP off-by-one-bit** | One's-complement magnitude reports 2^k−1 for \|v\|=2^k, over-shifting. Fixed with a single `+1`. | ~2 h |
| **Gain-comp truncation** | Five independent `>>>` truncations accumulating 3e-3 error. Fixed with a wide accumulator and one final round. | ~2 h |
| **Stale tarball** | The synthesis package shipped to the Genus machine predated the critical-path reorder. Caught before it mattered. | — |
| **Undefined citations** | `c4` and `c11` rendered as `[?]`. Found by reading the compiled PDF. | — |
| **Page fitting** | Eight compile-measure-cut cycles. Column estimates ran 2–3× optimistic until switching to counting lines. Reflow once made a cut *worse*. | ~1 day |
| **Credentials** | A live HF token was pasted into a notebook cell and shared in screenshots. Revoked; now in Kaggle Secrets. **Git history still needs scrubbing.** | open |

---

## 7. What exists

| | |
|---|---|
| `PAPER/iscas2027_main.tex` | Complete. 0 placeholders, 27 citations, 3 tables, Fig. 1 in TikZ |
| `RTL/` | 14 modules. New: angle encoder, gain compensation, BFP normalise/denormalise |
| `VERIFY/` | 24 scripts, one command, **7 PASS / 0 FAIL**. 2000 vectors, mutation-verified |
| `SCRIPTS/` | 17 runs reduced to one command; parameter substitution that **aborts rather than silently using defaults** |
| `KAGGLE/` | Five models, full WikiText-2, precision + long-context + gain sweeps |
| `ISCAS_REVISION_PLAN.md` | Operational ledger, 37 tracked issues, consistency-checked by script |

---

## 8. What is left

| | Item | Effort |
|---|---|---|
| **P0** | Page fit — content must end on page 4 (±2 lines as of last compile) | iterate |
| **P0** | **Repo URL** — reference [1] is still `github.com/anon-researcher-2026-create/…`, a dead link in a non-blind submission, cited twice | ~1 h |
| **P0** | **Scrub git history** before the repo is public — `git log -p \| grep -iE 'hf_\|token\|api[_-]key'` | ~30 min |
| **P0** | Author names, affiliations, emails (3 placeholders) | 5 min |
| P2 | Fig. 2 (`cordic_comparison.jpg`) — staged as a comment, needs 2 label fixes, only if space appears | — |
| P2 | Polynomial baseline + the `\todocite{poly}` citation | optional |

---

## 9. Assessment

**~65% acceptance probability**, against an ISCAS baseline near 48%.

**For:** every reviewer objection answered with measurements; all baselines on
one flow; honest about weak points (the bare multiplier is smaller, merging
does not pay off, the corner is optimistic); topical.

**Against:** the gains are respectable rather than striking; the novelty
objection can still be made since the architecture is Garrido's; the
prior-work comparison is qualitative because neither published RoPE
accelerator reports absolute area or a node.

**Highest-leverage remaining:** the repo URL. A reviewer clicking reference [1]
and getting a 404 revises their view of everything else in the paper.

---

## 10. What is genuinely new

Three results true for RoPE and false for rotation in general:

1. **Free gain compensation** — K² folds into the attention scale at zero cost,
   and provably only without stage merging.
2. **Angle front-end co-design** — the digit string *is* the angle, so no
   sin/cos ROM; 136 µm², amortised 1024× across heads and layers because it
   never depends on the data.
3. **Precision set by the frequency schedule**, not model size — derived
   analytically, confirmed on five models.

Plus one correction to a field assumption: **a fixed-point RoPE datapath is not
deployable without shared-exponent normalisation**, because real activations
exceed its range by two orders of magnitude.
