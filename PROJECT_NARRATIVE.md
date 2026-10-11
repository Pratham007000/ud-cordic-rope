# UD-CORDIC RoPE Accelerator — Full Project Narrative

**From the APCCAS 2026 rejection to the ISCAS 2027 submission.**

| | |
|---|---|
| Written | 2026-09-27 |
| Deadline | **2026-10-13** — 16 days |
| Prior submission | APCCAS 2026 #2130 — rejected |
| Target | ISCAS 2027, 4 pages + 1 references page |
| Status | Experiments complete · paper drafted · **blocked on one synthesis session** |

This is the explanatory companion to `ISCAS_REVISION_PLAN.md`. The plan is the
operational checklist; this document is the story — what we did, what went
wrong, why, and what is left.

---

## 0. The one-paragraph version

The submitted paper claimed a multiplier-free RoPE accelerator based on
UD-CORDIC. Four reviewers rejected it, the most serious objection being that
its novelty belonged to the prior work it built on. On investigation the paper
had deeper problems than the reviewers found: the angle encoder never
converged, so every accuracy number in it was wrong; the recommended precision
was wrong by three bits; the datapath as published could not hold real LLM
activations at all; and the headline architecture was named after a digit set
it does not implement. All four are now fixed, measured and drafted, and three
genuinely new results came out of the repair work. **What remains is a single
Genus session — four runs on the critical path — after which nine numbers get
filled in and the paper is submittable.**

---

## 1. Where we started

### 1.1 The paper as submitted

A parameterised, fully pipelined RoPE rotation datapath in two variants:

- **Binary UD-CORDIC** — Garrido et al.'s uniformly distributed CORDIC, which
  replaces the arctan angle set with a uniform one so micro-rotation directions
  can be read from the angle directly, eliminating the closed-loop Z-path.
- **"CSD UD-CORDIC"** — radix-4 stage merging, halving pipeline depth to N/2.

Synthesised in 45 nm, compared against LUT and multiplier baselines, validated
end-to-end on seven LLMs. Headline claims: 27–31% area reduction, 63–65% power
reduction versus standard CORDIC, and F=7 (W=9) as the optimal operating point.

### 1.2 What the reviewers said

Five distinct problems across four reviewers, ranked by reject risk:

| | Objection | Who |
|---|---|---|
| **P1** | **Novelty is not established** — Z-path removal and CSD stage merging both come from prior UD-CORDIC work; this paper adds pipelining | R3, echoed by R2 |
| P2 | Related-work survey incomplete for RoPE-specific hardware and LUT/polynomial RoPE | R2 |
| P3 | Missing hardware detail: angle range handling, CORDIC gain compensation, Binary UD encoding, an incomplete Eq. 8, power methodology | R4 |
| P4 | No latency/throughput/energy, no integration cost inside an attention pipeline | R2, R4 |
| P5 | No top-level block diagram; FP8/FP4 formats not considered | R1 |

**ISCAS has no author rebuttal phase.** Every objection has to be answered
inside the manuscript. That constraint shaped everything below.

---

## 2. The problem we are stuck on right now

**We have no access to the Genus machine, and four synthesis runs gate the
paper's central claim.**

Everything else is done. The specific dependency:

The paper's argument is that CORDIC beats a multiplier *at the precision the
accuracy data demands*. That rests on an area crossover we can only fit from
two measured word lengths:

```
A_mult  ≈ 381 + 19.4·W²      (from W=9: 1953 µm², W=14: 4185 µm²)
A_M-UD  ≈ 283 + 227·W        (from W=9: 2330 µm², W=14: 3467 µm²)
crossover → W ≈ 11.3
```

The measured precision requirement is W=13, which sits 1.7 bits above that
crossover. The linear model predicts 3240 µm² at W=13 against 3218 measured —
0.7% error on a point not used in the fit, which is a real independent check.

**But the crossover itself is interpolated between two points.** Runs 10 and 11
put the multiplier and LUT at W=12, directly on it. If the true crossover is
12.5 rather than 11.3, the margin halves and the paper's framing has to change.
Runs 1 and 2 separately decide whether merged UD or Binary UD leads, which
determines the abstract, contribution list and conclusion.

```bash
export SYN_LIBBASE=/path/to/gsclib045_all_v4.8
./SCRIPTS/run_all_synth.sh 1 2 10 11
python3 SCRIPTS/collect_results.py build
```

Nothing else in the project is waiting on anything.

---

## 3. What we did, and what went wrong doing it

### 3.1 The encoder was broken, and it invalidated the whole results section

**The finding.** A UD-CORDIC stage rotates by `arctan(2^-(i+1))`, not by
`2^-(i+1)`. Those weights are only approximately geometric — 0.927, 0.980,
0.995, 0.999 — so taking digits straight from the binary representation of θ,
which is what the UD formulation implies, mis-encodes the leading stages. The
error is *independent of pipeline depth*.

That is visible in the published Table I and nobody noticed: the error barely
moves with N. Binary UD 3.88° → 2.20° on doubling the stages; CSD 3.38° →
3.13°. A working datapath improves roughly 4× per doubling. The flat column was
the signature of an encoder that never converged.

**The fix.** The tail of the weight sequence is geometric to better than 0.13%,
so it can be read straight off the residual and only the two leading stages need
explicit resolution. The result is one adder, three constant comparators, a 4:1
constant mux and a subtractor — fully combinational, so the Z-path-free property
survives. `RTL/rope_angle_encoder.v`.

| Method | N | Published | Corrected | change |
|---|---|---|---|---|
| Binary UD | 5 | 3.88° | 2.004° | 2× |
| Binary UD | 10 | 2.20° | **0.0634°** | 35× |
| Merged UD | 5 | 3.38° | **0.0431°** | 78× |

The synthesisable encoder achieves **0.094°** at N=10 (the 0.0634° is the
algorithmic bound with an ideal encoder).

**Obstacle hit:** the first prefix-encoder search made P=3 *worse* than P=2 and
both worse than a plain affine fit, which made no sense. Cause: out-of-range
candidates were being discarded rather than clamped. Changing `continue` to a
clamp fixed it.

### 3.2 The comparison basis was wrong — and the user caught it

We had been comparing merged UD at N stages against standard CORDIC at N
stages, which hands merged UD twice the precision for free. The correct
comparison is N/2 merged against N binary. We had also mixed W=8 and W=9 numbers
across rows.

Corrected at matched precision (W=9): merged UD N=5 = 2330 µm², Binary UD N=10
= 3068, standard N=10 = 3292. This reopened the entire merged-UD verdict and
created two new tasks.

**This was caught by the user, not by us.** It is the single most important
correction in the project, because every area claim in the paper depended on it.

### 3.3 Fixed-point RoPE cannot hold real activations (S-14)

**The finding.** At F=14 — nearly full precision — perplexity came out at
27034 against a baseline of ~5.5, with a rotation error of only 0.00165. The
rotation was fine; something else was destroying the model.

Hooking Qwen2-0.5B showed why: |q| reaches 132 and |k| reaches 178, median ~20,
against the [−2, 2) representable range of Q(1,F). The datapath was saturating
on essentially every value.

**The consequence.** Block floating point — a shared exponent per (head, token),
barrel-shifted in and out — is a *functional requirement*, not an optimisation,
and it was absent from the published paper entirely. `RTL/rope_bfp_norm.v`.

This is architecture-neutral: the multiplier and LUT baselines need it too. It
does not shift the comparison, and the paper says so explicitly to avoid
double-counting.

**Obstacle hit:** the one's-complement magnitude estimate reports 2^k − 1 for
|v| = 2^k, over-shifting by a bit. The range check failed at exactly 2^(W−3).
Fixed with a single `+1` on the aggregate.

### 3.4 The optimal-precision claim was wrong by three bits

Published: "F=7 saturates, F=9 optimal." Measured:

| F | LLaMA-2-7B Δ | Qwen2-7B Δ |
|---|---|---|
| 11 | +0.005% | +0.018% |
| 10 | +0.020% | +0.103% |
| 9 | +0.078% | **+6.36%** |
| 8 | +0.318% | +131% |

The two models disagree by two bits, and the cause is **not** model scale —
both are 7B with the same head dimension. Qwen2 uses a RoPE base of 10⁶ against
LLaMA-2's 10⁴, so its Θᵢ spans a far wider dynamic range and the low-frequency
dimension pairs receive angles too small to resolve. Once an angle falls below
the datapath LSB, that pair **stops rotating entirely** and its positional
signal is discarded rather than degraded — which is why it is a cliff, not a
slope.

Recommendation: **F=11 (W=13)** for a general-purpose unit.

**Obstacles hit, in order:**

1. **Double shift.** Pre-shifted targets were passed to `labels=`, and the
   framework shifts internally — so we scored P(t+2|t). Baseline came out
   18738 instead of ~7. Fixed by computing loss explicitly. A tiny-random-model
   smoke test could not have caught this, because a uniform-output model is
   shift-invariant. Validated afterwards with GPT-2 → 32.2 at ctx 1024.
2. **A silent no-op that produced byte-identical results.** An experiment
   forcing different RoPE bases returned *identical* numbers for all three
   bases, including the fp16 baseline. Cause: `cfg.rope_theta` does not exist on
   LLaMA configs in transformers 5.x — the value lives in
   `cfg.rope_parameters["rope_theta"]`. The log said `rope_theta override: None
   -> 10000.0` and the `None` was missed. Fixed with a setter that writes every
   location, returns the sites written, **fails loudly if empty**, and asserts a
   readback.
3. **The re-run was confounded anyway.** After the fix, LLaMA-2 forced to base
   10⁶ degraded its *own* fp16 baseline 2.45×, so deltas were being measured
   against a broken model. The experiment was abandoned and replaced with an
   analytical derivation (`VERIFY/angle_loss.py`) computing the share of
   (position, dimension) pairs whose rotation quantises to zero. It crosses ~6%
   between F=10 and F=9 — exactly where Qwen2's measured cliff sits.
4. **A config shim that fixed one model and broke two others.** Clearing
   `rope_scaling` fixed Phi-3 but broke Falcon and Gemma-2, because the two
   fields are aliases in transformers 5.x. Made opt-in behind a flag.
5. **Gemma-2 needs bfloat16** — its fp16 baseline came out at 196.88. Caught
   automatically by a plausibility guard that had been added earlier. Dropped
   from the model set, with the reason recorded.

Final model set: **five** models (LLaMA-2 7B and 13B, Qwen2-7B, Mistral-7B,
Phi-3-3.8B), not the seven originally claimed.

### 3.5 Constant gain and stage merging are mutually exclusive (S-13)

**Contribution C1.** The CORDIC scale factor K normally costs a compensation
multiplier. In RoPE it costs nothing: q and k traverse the same rotator, so the
attention logit is scaled by exactly K², a constant that folds into the existing
1/√d_h. Measured on RTL: 1.164426 against 1.164435 predicted, spread ±0.0003.

**The impossibility.** This holds only for Binary UD. A merged radix-4 stage has
gain √(1 + v²4^−i), which depends on the digit magnitude. A digit-independent
gain requires all digits to share one magnitude — and a single-magnitude digit
set carries one bit per stage, which *is* Binary UD. Constant gain and radix-4
merging cannot be obtained together.

Uncompensated, merged UD costs +908% perplexity. Compensating the leading stage
alone (it accounts for 80.3% of the spread) with a three-constant shift-add
network holds it under 0.8%. `RTL/rope_gain_comp.v`.

**Obstacle hit:** the first gain-compensation implementation had 3e-3 error from
truncating each shift term independently — five truncations accumulating. Fixed
with a wide accumulator and a single round at the end.

### 3.6 The architecture is named after a digit set it does not implement

`csd_control.v` implements textbook radix-4 Booth, emitting digits {0, ±1, ±2}
**assuming weight 2**. But `csd_ud_stage.v` builds the magnitude-2 digit as
`x_s1 + x_s2` with SHIFT1 = 2i and SHIFT2 = 2i+1:

```
x·2^-2i + x·2^-(2i+1) = 1.5 · x · 2^-2i
```

**The digit labelled `+2` is physically a ×1.5.** A true ×2 would need the
second shift to be one place *less*, not one more. Control and datapath disagree
by a factor of 4/3 on the largest digit.

So the realised digit set is {0, ±1, ±3/2} — neither CSD (which is {0,±1} with
no adjacent non-zeros) nor Booth. The name was wrong, and the §II-D
justification built on CSD's non-adjacency property did not describe the
hardware. **Renamed to merged UD-CORDIC (M-UD).**

Worse, on regenerating the comparison the textbook ±2 set turns out to be
**better on both axes**: marginally more accurate (0.040° vs 0.043° at N=5) and
strictly cheaper, since ±2 is the single shift `x >> (2i−1)` and needs no adder
at all where ±3/2 needs one per stage. Its only deficit is a wider gain spread
(152% vs 93%), which matters solely because merged UD must carry compensation
hardware regardless.

The paper now states this plainly: we report the 3/2 set because it is what was
synthesised, not because it is preferable.

**This was found late**, while tracing where ±3/2 came from. It is the reason
merged UD's position in the paper is now uncertain — see §5.

### 3.7 Smaller corrections

| | |
|---|---|
| **S-17** | We had claimed the angle front-end is "shared across all d/2 lanes". Wrong — θᵢ = m·Θᵢ depends on i, so every lane needs its own angle. The real reuse is across **heads × layers** (1024× for LLaMA-2-7B), because the angle never depends on the data. Larger amortisation, different axis. |
| **S-6/7/8** | Library is **Cadence GPDK045**, not TSMC 45 nm. Corner is `fast_vdd1v2` at **1.32 V, 0 °C**, not "nominal 1.2 V". Power has no SAIF/VCD back-annotation. All three now stated, with the note that every design shares the corner so relative comparisons hold. |
| **Long context** | Contrary to intuition, rotation error does **not** compound with sequence length — degradation is flat or decreasing, because range reduction by truncation is exact. Measured at ctx 1024/2048/4096. |
| **Plan drift** | The plan's scoreboard was maintained by hand and went stale twice. `VERIFY/check_plan.py` now recounts the ledger and fails on disagreement. |
| **Credentials** | A live HF token was pasted into a notebook cell and shared in screenshots. Revoked; the value now lives only in Kaggle Secrets. **Git history still needs scrubbing** before the paper points readers at the repo. |

---

## 4. What exists now

### 4.1 Verification — `VERIFY/`, one command, currently 7 PASS / 0 FAIL

```bash
cd VERIFY && bash run_all.sh
```

24 scripts covering the encoder search, range checks, golden-vector generation,
five pair-module testbenches (2000 vectors, **mutation-verified**), the BFP
range check, block-granularity sweep, Table I regeneration, the analytical
angle-loss derivation, and a plan-consistency check.

### 4.2 RTL — `RTL/`, 14 modules

New this cycle: `rope_angle_encoder.v` (encoder + range reduce),
`rope_gain_comp.v` (H1/H2 compensation), `rope_bfp_norm.v` (normalise +
denormalise). All verified in Icarus Verilog. **None synthesised yet.**

### 4.3 Synthesis tooling — `SCRIPTS/`, 17 runs reduced to one command

`synth_generic.tcl` (env-driven, one script for all runs) · `set_params.py`
(rewrites parameter defaults into a per-run RTL copy; **aborts if a parameter
is not found**, rather than silently synthesising the default) ·
`run_all_synth.sh` (isolates each run in `build/NN_name/`) ·
`collect_results.py` (emits `run,design,area_um2,slack_ps,power_mW`).

### 4.4 Evaluation — `KAGGLE/`

A vectorised torch twin of the RTL plus the perplexity harness. Five models,
full WikiText-2, precision sweep F=14→3, long-context sweep, gain-compensation
sweep. All measured; nothing pending.

### 4.5 The paper — `PAPER/iscas2027_main.tex`

Complete and self-contained, rebuilt from scratch rather than patched. Four
tables, one figure wired in (`block_diagram.jpg`), a second staged as a comment
(`cordic_comparison.jpg`). Passes an IEEE template compliance audit. **Nine
`<<TBD>>` remain, all synthesis-dependent.**

Deleted from the submitted version: the old Table I (wrong numbers), Table II
(all rows at the wrong operating point), the 7×12 perplexity grid (168 numbers,
~150 identical), and the normalised-tradeoff figure (its "F≥7 safe" band is the
claim our own work contradicts).

---

## 5. The implementation plan from here

### Step 1 — the four critical runs *(blocked on machine access)*

```bash
tar xzf SIDDHANT_synth.tar.gz && cd SIDDHANT
export SYN_LIBBASE=/path/to/gsclib045_all_v4.8
./SCRIPTS/run_all_synth.sh 1          # validate the flow on one run first
./SCRIPTS/run_all_synth.sh 2 10 11
python3 SCRIPTS/collect_results.py build
```

**Runs 1–2** price the gain-compensation block. If it lands near ~150 µm²,
merged UD leads; near a multiplier (~570 µm²), Binary UD leads on the strength
of C1. **Runs 10–11** test the crossover directly.

### Step 2 — the architecture decision

This is a genuine fork, and the evidence has been accumulating against merged
UD:

| | Binary UD | Merged UD |
|---|---|---|
| Encoder in RTL | ✅ written, verified | ❌ Booth encoder mismatches its own datapath |
| Gain compensation | ✅ free (C1) | ❌ required block |
| Digit set | — | ❌ worse than textbook ±2 on accuracy *and* cost |
| Area at W=14 | 4346 µm² | 3467 µm² *(excludes its encoder)* |

Merged UD is smaller on paper but owes two unbuilt blocks. **My expectation is
that runs 1–2 push the paper toward leading with Binary UD**, with merged UD
reported as a secondary result and its caveats stated.

### Step 3 — fill nine `<<TBD>>` and write three sections

Abstract, contribution list in final form, and conclusion are all blocked on
Step 2 because they must name the leading architecture.

### Step 4 — compile and fit to four pages

Never compiled — there is no LaTeX toolchain on this machine. The estimate is
4.2–4.6 pages against a 4-page limit. Cut order if over: `tab:longctx` → two
sentences; the block-size paragraph in §III-B; the energy-per-token paragraph in
§IV-B; and Fig. 2, which is the cheapest cut in the paper since it illustrates
prior work rather than our contributions.

### Step 5 — repo release

Push the new RTL, scripts and results; write a real README; **scrub git history
for credentials** (`gitleaks`, or `git log -p | grep -iE 'hf_|token|api[_-]key'`)
before a published paper points readers at it.

---

## 6. Everything still pending

| | Item | Blocked by |
|---|---|---|
| **P0** | Runs 1, 2, 10, 11 | machine access |
| **P0** | Architecture decision: merged vs Binary UD | runs 1–2 |
| **P0** | Nine `<<TBD>>` | runs 1–2, 10–11, 15 |
| **P0** | Abstract, contribution list, conclusion | architecture decision |
| **P0** | First compile; fit to 4 pages | nothing — needs Overleaf |
| P1 | Remaining 13 runs (3–9, 12–17) | machine access |
| P1 | Fig. 2 final pass (two label fixes) or drop | nothing |
| P1 | Execute `RENAME_CHECKLIST.md`, including the paper title | nothing |
| P2 | Prior-work rows in `tab:baselines` — numbers from RoPIM and Li et al. | reading those papers |
| P2 | Re-cite the 13 dropped references in one sweep sentence | nothing |
| P2 | Polynomial baseline RTL + the `\todocite{poly}` citation | optional |
| P2 | Merged-UD encoder in RTL, if merged UD stays the headline | Step 2 |
| P3 | Repo push, README, **git history credential scrub** | nothing |

---

## 7. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **No Genus access before 2026-10-13** | Submission fails | Only four runs are strictly required; they are scripted and take under an hour |
| **Crossover lands at 12.5, not 11.3** | Central claim weakens to ~0.5 bit of margin | Runs 10–11 test it directly; fallback is to lead on energy and self-containment rather than area |
| Paper overruns 4 pages | Formatting reject | Cut order fixed in §5 Step 4 |
| Merged UD's unbuilt encoder is noticed by a reviewer | Credibility | Already stated in §II-B and §IV-B as a caveat against ourselves |
| Credentials in git history | Serious, and public | Scrub before the repo URL appears in a published paper |

---

## 8. What is actually new here

Worth stating plainly, because P1 (novelty) is what got the paper rejected.
Three results that are true for RoPE and false for generic CORDIC rotation:

1. **Free gain compensation.** K² folds into the attention scale at zero cost —
   and provably only without stage merging.
2. **Angle front-end co-design.** The digit string *is* the angle, so no sin/cos
   ROM is needed, and the encoder amortises 1024× across heads and layers
   because it never depends on the data.
3. **The precision requirement is set by the frequency schedule**, not model
   size — with the mechanism derived analytically and confirmed on five models.

Plus one finding that is not a contribution so much as a correction to the
field's assumption: **a fixed-point RoPE datapath is not deployable without
shared-exponent normalisation**, because real activations exceed its range by
two orders of magnitude.
