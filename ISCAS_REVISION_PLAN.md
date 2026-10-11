# UD-CORDIC RoPE Accelerator — Revision Plan (APCCAS 2026 reject → ISCAS 2027)

**Status:** living document. §0.6 is the single source of truth for status; §8 is the append-only historical record.
**Last updated:** 2026-10-05

---

> **2026-10-05 — ALL 17 SYNTHESIS RUNS COMPLETE, 0 FAILURES.**
> Architecture decided: **Binary UD leads.** Merged UD reported as the
> energy-optimal variant. Zero `<<TBD>>` remain in the manuscript.
>
> | Headline (W=14, complete units) | |
> |---|---|
> | Binary UD vs Std CORDIC | **19.2% area, 42.7% power** |
> | Binary UD vs LUT (only self-contained baseline) | **19.1% area, 38% energy** |
> | Angle front-end (encoder + range reduce) | 458 µm², shared 1024× |
> | H1 gain compensation | 1032 µm² — **merging does not pay for itself** |
> | H2 compensation | 1819 µm² — strictly dominated by Binary UD |
> | BFP normalise + denormalise | 824 µm²/lane, **use D=8 not D=64** |
>
> Two findings that changed the paper: the fitted W≈11.3 crossover was
> datapath-only and does not survive compensation (real crossover vs the *bare*
> multiplier is W≈15) — but the LUT row **is** the completed multiplier design,
> and CORDIC beats it at every width. And runs 16–17 show finer BFP blocks are
> cheaper, more accurate *and* better for timing, reversing the paper's prior
> recommendation.
>
> **Remaining: compile in Overleaf and fit to 4 pages.** Nothing else blocks.

---

## 0. Logistics

| Item | Value |
|---|---|
| Prior submission | APCCAS 2026, paper #2130 — **rejected** |
| Target venue | **ISCAS 2027** — https://2027.ieee-iscas.org/ |
| Submission deadline | **2026-10-13** |
| Time remaining | **26 days** |
| Page limit | 4 pages + 1 references page (ISCAS standard — **still to confirm on the 2027 CFP**) |
| Repo | `Pratham007000/A-Uniformly-Distributed-CORDIC-Based-RoPE-Hardware-Accelerator-for-LLMs` |
| HF tokens | All revoked; a fresh read-only token lives in Kaggle Secrets as `HF_TOKEN` |

**ISCAS has no author rebuttal phase.** Every reviewer objection must be answered *inside the manuscript*, which is why §0.6 distinguishes "we measured it" from "it is on the page".

**Naming decision (T1.3, 2026-09-14):** the design formerly called *CSD UD-CORDIC* is renamed **merged UD-CORDIC (M-UD)**. Its digit set is {0, ±1, ±3/2}, which is neither canonical signed digit nor Booth, so the old name was wrong and the §II-D justification built on CSD's non-adjacency property did not describe the hardware. Tables below use the new name. `PAPER/RENAME_CHECKLIST.md` lists every site still to change, including the paper title.

---

## 0.5 Status at a glance — 2026-09-17

**Experiments are essentially complete. Ten paper sections are drafted. The blocker is one synthesis session.**

### Closed
| | |
|---|---|
| T1.1 / T1.2 | Merged-UD datapath verified sound; the *encoder* was the defect, not the ±3/2 digit |
| T1.5 | RTL ≡ torch model, bit-exact (485/485 vectors; 0.002° end-to-end agreement) |
| T1.6 | Five pair-module testbenches, 2000 vectors, 0 mismatches, **mutation-verified** |
| T1.7 | **Angle encoder written** (`rope_angle_encoder.v`) — 0.094° RMS, 23× better than published, no Z-path |
| T1.8 | Table I regenerated; full WikiText-2 perplexity on **five** models |
| T1.9 | Merged-UD encoder investigated; gain/merging incompatibility characterised |
| T2.2 | Latency / throughput / energy, incl. pJ/rotation and nJ/token |
| T2.3 | Attention-pipeline integration: cycle budget and MAC share |
| T2.5–2.8 | Synthesis methodology corrected and disclosed; FP8/FP4 answered with data |
| T2.10 | BFP normaliser RTL written and verified (synthesis pending) |
| T2.11 | Block-granularity sweep on real activations |
| T3.1–3.5 | Methodology table, precision claim, long context, Qwen2 mechanism, gain compensation |
| T4.1–4.6 | Block diagram, contributions, related work, §II rewrite, gain derivation |

### The five findings that reshape the paper
1. **S-1** — the published angle encoder never converged. Table I's plateau was a defect presented as a feature.
2. **S-14** — Q1.F saturates on real activations (|q|=132, |k|=178). Block-floating-point normalisation is a *functional requirement* and was absent from the paper entirely.
3. **The optimal-F claim was wrong by 3 bits, and the requirement is model-dependent.** Published: "F=7 saturates, F=9 optimal". Measured: base-10⁴ models tolerate F=8; Qwen2 (base 10⁶) needs F=10. **Recommend F=11.** Mechanism derived analytically.
4. **S-13** — constant gain and radix-4 merging are mutually exclusive, so C1 is Binary-UD-only. Merged UD needs compensation, which H1 supplies at <0.8% perplexity for an estimated ~150 µm².
5. **The corrected operating point is what makes the architecture win.** At W=9 a plain multiplier beats every CORDIC variant; at W=12–14 — the precision the accuracy data actually supports — merged UD is smallest and lowest-energy. The accuracy result and the hardware result reinforce each other.

### Single blocker
**Synthesis runs 1–2** (`rope_gain_comp`, H1 at W=12/14). They decide merged-UD vs Binary-UD, which in turn determines the abstract, contribution list and conclusion — the three unwritten sections. Everything is scripted: `SCRIPTS/run_all_synth.sh`.

### Not started
Abstract, contribution list rewrite in final form, conclusion, T5 repo release, and the prior-work numbers in `tab:baselines`.

---

## 0.6 Issue ledger — the single place to check status

| mark | meaning |
|---|---|
| `OPEN` | nothing done yet |
| `DATA` | the measurement or artifact exists; only the write-up remains |
| `PART` | partly addressed, a named gap remains |
| `DONE` | closed **and visible in the manuscript** (or, for self-found issues, fixed in the artifact) |

For reviewer issues `DONE` requires text on the page. Task checkboxes in §4 track *work*; this ledger tracks *closure*.

### Reviewer issues

| ID | status | what remains |
|---|---|---|
| R1-1 terminology | OPEN | T4.4; trivial, but touches the title |
| R1-2 block diagram | DATA | `fig_architecture.tex` — TikZ, **never compiled**, needs one pass |
| R1-3 non-CORDIC baselines | DATA | LUT + mult synthesised; needs W=12 runs (10–11) then write-up |
| R1-4 FP8/FP4 | DATA | `number_formats.tex` — answered with the measured sweep, not deflected |
| R2-1 related work | DATA | `related_work.tex` drafted; one `\todocite{poly}` unresolved |
| R2-2 LUT/poly/RoPE-specific | PART | LUT + mult done; polynomial (T2.4) and prior-accelerator rows missing |
| R2-3 latency + integration | DATA | `performance.tex` + `integration.tex`; one `<<TBD>>` (area vs ITA) |
| R2-4 soften optimal-F | DATA | `evaluation.tex` §IV-C; single-optimum claim removed, F=11 recommended |
| **R3-1 novelty** | DATA | C1, T3.4 mechanism and S-13 all drafted in `contributions.tex`, `gain_compensation.tex`, `evaluation.tex`. **Final form waits on the architecture decision** |
| R4-1 hw details | DATA | encoder, range-reduce and BFP normaliser all written and verified; `background_ud.tex` + Fig. 1 drafted |
| R4-2 open source | PART | testbenches + one-command regression done; repo push, README, history scrub open |
| R4-3 angle range | DONE | `rope_range_reduce`; ±54.9° vs 360° quantified |
| R4-4 gain compensation | DATA | `gain_compensation.tex`; K=1.164435 measured, spread ±0.0003 |
| R4-5 Binary UD encoding | DATA | `background_ud.tex` §II-C — bit→digit table and convergence range |
| R4-6 Eq. 8 incomplete | DATA | corrected as `eq:merged` in `background_ud.tex` |
| R4-7 power methodology | DATA | `synthesis_method.tex`; library, corner and activity source stated and verified against the scripts |
| R4-8 throughput/energy | DATA | `performance.tex`; one `<<TBD>>` pending run 15 |
| R4-9 full baseline set | PART | LUT/mult/std done; polynomial + PIM rows missing |
| R4-10 perplexity detail | DATA | `tab:method` covers every item R4 listed |
| R4-11 long context | DATA | `evaluation.tex` §IV-D; error does not compound, with the mechanism |

### Self-found issues

| ID | status | note |
|---|---|---|
| S-1 encoder never converged | DONE | encoder written (T1.7); datapath was always sound |
| S-2 ±3/2 digit | DONE | not a bug — marginally *better* than ±2; documented as a deliberate digit set |
| S-3 Booth vs CSD naming | DATA | Option A taken: renamed to merged UD. §II drafted; `RENAME_CHECKLIST.md` tracks the remaining sites |
| S-4 mult beats us at W=9 | DATA | resolved by the corrected operating point — see §2.2 |
| S-5 RTL ≢ Python | DONE | confirmed, then replaced by a bit-exact verified model |
| S-6 TSMC vs GPDK045 | DATA | corrected in `synthesis_method.tex` |
| S-7 fast corner vs 1.2 V | DATA | **decision: keep `fast_vdd1v2` and disclose it** — all designs share it, so relative claims hold |
| S-8 power estimation | DATA | disclosed as default-toggle, with the bias direction noted |
| S-9 anonymised repo URL | OPEN | T4.7 |
| S-10 no range reduction | DONE | `rope_range_reduce` |
| S-11 merged-UD gain | DONE | superseded by S-13 |
| S-12 reachable range | DONE | ±54.9° / ±84.0° quantified |
| **S-13 gain vs merging** | DATA | characterised and measured; **architecture decision gated on runs 1–2** |
| **S-14 datapath saturation** | DATA | RTL written and verified; synthesis pending (runs 7–9) |
| S-15 stale Table IV models | DONE | all five models re-measured with the corrected harness |
| S-16 Gemma-2 needs bf16 | DATA | caught by the plausibility guard; Gemma-2 dropped from the model set |
| **S-17 front-end amortisation** | DONE | corrected 2026-09-16: the front-end is **not** shared across lanes; reuse is across heads × layers (1024×) |

**Scoreboard: 9 DONE · 23 DATA · 3 PART · 2 OPEN** (37 tracked issues).

The shape of the remaining work: 19 `DATA` rows are sections awaiting assembly, not questions awaiting answers. The experiments are finished. What is left is one synthesis session, then writing.

---

## 1. What the reviewers actually said (deduplicated)

Four reviewers, five distinct problems, ranked by reject risk.

### P1 — Novelty is not established *(R3, echoed by R2)* — **EXISTENTIAL**
> "The key CORDIC concepts, including Z-path removal and CSD-based stage merging, seem to come from prior UD-CORDIC work rather than this manuscript."

R3 was correct about the submitted text: §II-C/II-D read as a tutorial on Garrido et al., and §III added pipelining. **Status: three RoPE-specific results now exist** — free gain compensation (C1), the frequency-schedule precision mechanism (T3.4), and the gain/merging impossibility (S-13). All are drafted; the final framing waits on the architecture decision.

### P2 — Missing baselines *(all four reviewers)* — **LARGELY CLOSED**
LUT, multiplier and standard CORDIC are implemented and synthesised under one flow. Outstanding: the polynomial baseline (T2.4, optional) and normalised rows for RoPIM and Li et al., whose numbers must be read out of those papers.

### P3 — Metrics are incomplete *(R2, R4)* — **CLOSED**
`performance.tex` and `integration.tex` add F_max, latency, throughput, pJ/rotation, nJ/token, cycle budget and MAC share.

### P4 — Perplexity methodology is unreproducible *(R4)* — **CLOSED**
`tab:method` covers every item R4 listed. Long context measured at 1k/2k/4k on two models.

### P5 — Hardware description has real gaps *(R1, R4)* — **CLOSED IN DRAFT**
Block diagram, angle-range handling, gain derivation, Binary UD encoding table, corrected Eq. 8, power methodology and terminology all drafted.

---

## 2. Synthesis data in hand

Cadence Genus 21.10, GPDK045 (`gsclib045` + hvt/lvt), `fast_vdd1v2` @ PVT_1P32V_0C, 2.0 ns / 500 MHz. Two baseline modules written for this revision:

- `RTL/rope_lut_pair.v` — 128-entry quarter-wave sin ROM + quadrant decode + 4 multipliers. **Self-contained**: generates its own sin/cos.
- `RTL/rope_mult_pair.v` — 4 multipliers + 2 adders. **Takes sin/cos as inputs** — does not pay to produce them, so it is not a complete RoPE unit.

Modules written since: `rope_angle_encoder.v` (+ `rope_range_reduce`), `rope_gain_comp.v`, `rope_bfp_norm.v` (+ denorm). All verified in iverilog; none yet synthesised.

### 2.1 Extracted dataset (post-`syn_opt`)

*"Merged UD" was labelled "CSD UD" in the submitted paper — same RTL, corrected name.*

| Design | Config | Area (µm²) | Power (mW) | Slack (ps) |
|---|---|---|---|---|
| **Word-length sweep** ||||
| Mult RoPE | W=8 | 1471 | 0.660 | 1148 |
| Mult RoPE | W=9 | 1953 | 0.810 | 1086 |
| Mult RoPE | W=14 | 4185 | 2.092 | 600 |
| Mult RoPE | W=16 | 5415 | 2.672 | 473 |
| Mult RoPE | W=32 | 20375 | 12.686 | **0** |
| LUT RoPE | W=8 | 1841 | 1.028 | 743 |
| LUT RoPE | W=9 | 2339 | 1.770 | 536 |
| LUT RoPE | W=14 | 5375 | 4.544 | 26 |
| LUT RoPE | W=16 | 6841 | 5.785 | 30 |
| LUT RoPE | W=32 | 13181 | 7.691 | **0** |
| Std CORDIC | W=8, N=10 | 2800 | 2.615 | 1468 |
| Std CORDIC | W=9, N=10 | 3292 | 3.062 | 1381 |
| Std CORDIC | W=16, N=10 | 5865 | 5.017 | 1215 |
| Std CORDIC | W=32, N=10 | 10508 | 10.044 | 709 |
| Binary UD | W=8, N=10 | 2728 | 1.790 | 1611 |
| Binary UD | W=16, N=10 | 4947 | 3.181 | 1261 |
| Binary UD | W=32, N=10 | 9771 | 6.408 | 764 |
| Merged UD | W=9, N=5 | 2330 | 1.117 | 1347 |
| Merged UD | W=16, N=5 | 4025 | 2.110 | 1046 |
| Merged UD | W=32, N=5 | 8123 | 6.828 | 386 |
| **Merged UD word-length sweep (N=5)** ||||
| Merged UD | W=6 (F=4) | 1539 | 0.656 | 1459 |
| Merged UD | W=7 (F=5) | 1797 | 0.802 | 1429 |
| Merged UD | W=8 (F=6) | 2051 | 0.940 | 1365 |
| Merged UD | W=9 (F=7) | 2330 | 1.117 | 1347 |
| Merged UD | W=10 (F=8) | 2605 | 1.245 | 1312 |
| Merged UD | W=11 (F=9) | 2734 | 2.146 | 1234 |
| Merged UD | W=12 (F=10) | 2942 | 1.470 | 1182 |
| Merged UD | W=13 (F=11) | 3218 | 1.645 | 1126 |
| Merged UD | W=14 (F=12) | 3467 | 1.765 | 1105 |
| **Merged UD stage sweep @ W=9** ||||
| Merged UD | N=4 | 1903 | 0.928 | 1355 |
| Merged UD | N=5 | 2330 | 1.117 | 1347 |
| Merged UD | N=6 | 2779 | 1.300 | 1353 |
| Merged UD | N=8 | 3769 | 2.640 | 1331 |
| Merged UD | N=10 | 4820 | 3.226 | 1352 |
| Merged UD | N=12 | 5970 | 3.859 | 1313 |
| **Std CORDIC stage sweep @ W=9** ||||
| Std CORDIC | N=8 | 2773 | 2.464 | 1381 |
| Std CORDIC | N=10 | 3292 | 3.062 | 1381 |
| Std CORDIC | N=12 | 3813 | 3.663 | 1360 |

These reconcile exactly with the submitted Tables II and III, so old and new sit on one measurement basis.

**Missing at the corrected operating point:** no multiplier or LUT run at W=12 at all, and no Binary UD at W=12/14 from this campaign. Runs 10–15 fill that gap; until then the headline comparison cannot be made where the accuracy data puts it.

### 2.2 The operating point, the crossover, and why it settles S-4

**Correction 2026-09-24.** An earlier version of this section labelled the W=14
column "measured requirement". That was wrong and it propagated into downstream
drafting. The measured requirement is **F=11, i.e. W=13** (`evaluation.tex`
§IV-C: Qwen2-7B is +0.018% at F=11, +0.103% at F=10 and +6.36% at F=9; F=11 is
one bit of margin above the cliff). **W=14 is where synthesis data happens to
exist**, and it is also where FP16/BF16 datapath matching lands — but it is not
what the accuracy data demands. Both facts are useful; conflating them is not.

Equally: the mechanism is the **frequency schedule** (base 10⁶ vs 10⁴ leaves
low-frequency dimension pairs with angles below the datapath LSB, so they stop
rotating altogether). It is **not** "trigonometric fidelity" or "sin/cos
accuracy" — no such experiment was run and none should be claimed.

#### The crossover is the argument, not the operating point

Fitting the two measured word lengths:

- Multiplier, quadratic: 1953 µm² @ W=9, 4185 @ W=14 → **A ≈ 22·W²**
- Merged UD, linear: 2330 µm² @ W=9, 3467 @ W=14 → **A ≈ 287 + 227·W**

Setting them equal: 22W² − 227W − 287 = 0 → **W ≈ 11.5**.

| | W=9 (paper's old claim) | W=13 (**measured requirement**) | W=14 (synthesised; FP16 match) |
|---|---|---|---|
| Mult RoPE† | **1953 µm², 1.62 pJ** | ~3700 µm² (interpolated) | 4185 µm², 4.18 pJ |
| LUT RoPE | 2339 µm², 3.54 pJ | — | 5375 µm², 9.09 pJ |
| Merged UD | 2330 µm², 2.23 pJ | **3218 µm²** | **3467 µm², 3.53 pJ** |

† consumes sin/cos it does not generate.

At W=9 the multiplier wins on area, power and latency, and no architectural
argument changes that — we concede it in the text. The crossover sits at
**W ≈ 11.5**, and the measured requirement is **1.5 bits above it**. That is
the whole case, and it is quantitative rather than rhetorical.

**This is an interpolation between two points.** Runs 10–11 (multiplier and LUT
at W=12) sit almost exactly on the fitted crossover and are the direct test. If
the true crossover lands at 12.5 instead of 11.5, the margin halves and the
framing weakens substantially. Runs 10–11 are therefore **critical path**, not
priority 3 — see `SYNTHESIS_RUN_LIST.md`.

#### The framing that follows

1. **Lead with the crossover**, not with "cheapest at W=9" — a claim we lose.
2. **Against the only self-contained baseline (LUT), merged UD wins at every
   width** — at W=14, 36% smaller, 2.6× lower energy, and the LUT closes with
   26 ps of slack against merged UD's 1105 ps.
3. **The multiplier comparison must carry angle generation** (T2.1, runs 5–6),
   or it compares a complete design against a partial one.
4. **Two independent legs, in this order**: (a) measured — a general-purpose
   accelerator must provision for the widest RoPE base in circulation, giving
   W=13; (b) system — FP16/BF16 datapaths put the unit at W=16 regardless.
5. **Do not double-count BFP.** The F=11 figure is measured *with* shared-exponent
   normalisation (`tab:method`). BFP is a functional requirement for both the
   CORDIC and the multiplier datapath, so it is architecture-neutral and does
   not independently justify a wider W.

#### Claims that must not appear

| Claim | Why not |
|---|---|
| "Trigonometric fidelity requires F=12" | Never measured; invents a metric |
| "Long context degrades at low F" | **Contradicts `tab:longctx`** — error is flat or decreasing with context, because range reduction by truncation is exact |
| "sin(100000) impossible at 7 frac bits" | Angle is reduced mod 2π *before* encoding; the relevant width is PW=16 in `rope_range_reduce`, a different parameter from W |
| "~80% of deployments are FP16" | Unsourced |
| "GPTQ/AWQ keep RoPE at higher precision" | Both are weight-only; they do not quantise activations, so the claim is vacuous |
| "Cheapest at W=9" | False, and reviewers will check |


---

## 3. Strategy

### 3.1 Positioning — the answer to Reviewer 3

Three contributions, each true for RoPE and false for generic CORDIC rotation.

- **C1 — Free gain compensation.** K = ∏√(1+2^−2(i+1)) normally costs a compensation multiplier. In RoPE it is free: **q** and **k** traverse the same rotator, so the logit ⟨q,k⟩ is scaled by exactly K², a constant that folds into the existing 1/√d_h scale. **Binary UD only** — S-13 shows merged UD's gain is angle-dependent. Measured on RTL: 1.164426 against 1.164435 predicted, spread ±0.0003. Drafted in `gain_compensation.tex`.
- **C2 — Angle front-end co-design.** The digit string *is* the angle, so no sin/cos ROM and no per-dimension angle table are needed. **Corrected 2026-09-16:** the front-end is *not* shared across the d/2 lanes — θᵢ = m·Θᵢ depends on i, so each lane needs its own angle. It is shared across **heads, layers and batch** (1024× for LLaMA-2-7B), because the angle never depends on the data. Larger amortisation, different axis.
- **C3 — Hardware–accuracy characterisation.** Five models, 3.8B–13B, with the precision requirement traced to the frequency schedule and derived analytically. The weakest of the three as novelty, but it is what the artifact delivers and it subsumes the old "seven models" claim with better controls.

### 3.2 What to cut to make room

Four pages must absorb a block diagram, a unified baseline table, a performance table and a methodology table. Cut:
- §II-B standard CORDIC tutorial → three sentences plus citation (`background_ud.tex` already does this).
- Old Table I → keep the regenerated version at two stage counts only.
- Perplexity table → five models × F ∈ {14, 12, 11, 10, 9, 8, 7, 6}; say the rest are unchanged.
- The introduction's second and third paragraphs, which restate each other.
- Fig. `fig:tradeoff` (the old normalised-metric plot) — its data is superseded and its "F=7–9 optimal" band is wrong. Replace with nothing; Table `tab:fsweep` carries it.

---

## 4. Task list

`[ ]` todo · `[~]` in progress · `[x]` done · **P0** = blocks submission

### T1 — Verification *(complete)*
- [x] **T1.1 / T1.2** — merged-UD datapath sound; encoder was the defect; ±3/2 digit harmless.
- [x] **T1.3** — naming resolved: Option A, renamed to merged UD-CORDIC.
- [x] **T1.4** — Eq. 8 corrected as `eq:merged` in `background_ud.tex`.
- [x] **T1.5** — RTL ≡ torch model, bit-exact; C1 confirmed on RTL.
- [x] **T1.6** — five pair testbenches, 2000 vectors, mutation-verified.
- [x] **T1.7** — `rope_angle_encoder.v` written and verified; 0.094° RMS.
- [x] **T1.8** — Table I regenerated; full perplexity on five models.
- [~] **T1.9** — merged-UD encoder: achievable (0.073° RMS, 64-entry ROM head) but two caveats recorded; **not worth further work** unless the gain verdict is overturned.

### T2 — Hardware
- [ ] **T2.1 · P0** — synthesise the angle front-end (runs 5–6) and report it per lane, so the multiplier baseline is not compared against a partial design. Closes R4-3's hardware half.
- [x] **T2.2** — `performance.tex`; one `<<TBD>>` pending run 15.
- [x] **T2.3** — `integration.tex`; one `<<TBD>>` (area vs ITA).
- [ ] **T2.4** — polynomial baseline. Optional; if skipped, `related_work.tex` still needs a real citation for `\todocite{poly}`.
- [x] **T2.5 / T2.6 / T2.7** — `synthesis_method.tex`. Corner kept and disclosed.
- [x] **T2.8** — `number_formats.tex`.
- [ ] **T2.9 · P0 · CRITICAL PATH** — synthesise `rope_gain_comp` (runs 1–4). Decides the headline architecture. Estimated ~150 µm²; **must be measured**.
- [~] **T2.10 · P0** — BFP normaliser RTL written and verified; synthesis pending (runs 7–9).
- [x] **T2.11** — block-granularity sweep on real activations.
- [ ] **T2.12** — fill the W=12/14 comparison gaps (runs 10–15).

### T3 — LLM evaluation *(complete)*
- [x] **T3.1** — methodology table (`tab:method`).
- [x] **T3.2** — optimal-F claim replaced with a recommended range.
- [x] **T3.3** — long context at 1k/2k/4k; error does not compound.
- [x] **T3.4** — Qwen2 mechanism: frequency schedule, derived analytically in `VERIFY/angle_loss.py`.
- [x] **T3.5** — gain compensation: H1 <0.8% on both models.
- [x] **T3.6** — controlled base override attempted; **confounded and abandoned** (overriding the base breaks an un-retrained model). Superseded by the analytical derivation.

### T4 — Writing
- [x] **T4.1** — `fig_architecture.tex`. **Never compiled** — needs one pass.
- [x] **T4.2** — `contributions.tex`.
- [x] **T4.3** — `related_work.tex`; `\todocite{poly}` and the prior-work rows outstanding.
- [ ] **T4.4** — terminology: *Rotary Position Embedding* throughout; title "Rope" → "RoPE".
- [x] **T4.5** — §II-C rewritten with the bit→digit table.
- [x] **T4.6** — `gain_compensation.tex`.
- [ ] **T4.7** — update reference [1] to the real repo URL.
- [ ] **T4.8 · P0** — rewrite the abstract. **Waits on runs 1–2.**
- [x] **T4.9** — non-standard digit set documented in `background_ud.tex`.
- [ ] **T4.11 · P0** — rewrite the conclusion. **Waits on runs 1–2.**
- [ ] **T4.12** — execute `PAPER/RENAME_CHECKLIST.md`, including the title.

### T5 — Open-source release
- [ ] **T5.1** — push new RTL (baselines, encoder, gain comp, BFP normaliser).
- [ ] **T5.2** — push synthesis scripts, SDC, results CSV. Not the multi-GB `RUN/` blobs.
- [ ] **T5.3** — write a real README (current one is two lines).
- [ ] **T5.4** — scrub git history for credentials before a paper points at the repo.
- [x] **T5.5** — testbenches and one-command regression (`VERIFY/run_all.sh`, `run_pair_tb.sh`).

---

## 5. Where each issue lands in the manuscript

§0.6 holds the status; this table holds only the *location*, so the two cannot drift. ISCAS has no rebuttal, so an objection is answered only where a reviewer will see it.

| ID | Reviewer's complaint (short) | Section / artifact |
|---|---|---|
| R1-1 | "Encoding" vs "Embedding" inconsistent | Title, abstract, §I |
| R1-2 | Top-level block diagram "highly desirable" | Fig. 1, top of §III |
| R1-3 | Compare against non-CORDIC architectures | `tab:baselines` (§I-A), `tab:perf` (§IV-A) |
| R1-4 | FP8/FP4 not considered | §III-E `number_formats.tex` |
| R2-1 | Related-work survey thin on RoPE hardware | §I-A `related_work.tex` |
| R2-2 | LUT / polynomial / prior RoPE accelerators | `tab:baselines` |
| R2-3 | Latency and attention-pipeline integration | §IV-A `performance.tex`, §IV-E `integration.tex` |
| R2-4 | Soften the optimal-precision claim | §IV-C, abstract, conclusion |
| **R3-1** | **Novelty comes from prior UD-CORDIC work** | §I contributions, §III-B gain derivation, §IV-C mechanism |
| R4-1 | More hardware implementation detail | §II-C, §III-A, Fig. 1 |
| R4-2 | Open-source the code | Reference [1] + reproducibility note in §III-C |
| R4-3 | RoPE angle-range handling missing | §III-A + Fig. 1 |
| R4-4 | Explain gain/scaling compensation | §III-B `gain_compensation.tex` |
| R4-5 | Binary UD encoding unclear | §II-C, Table `tab:bitmap` |
| R4-6 | Equation 8 incomplete | `eq:merged`, §II-D |
| R4-7 | ASIC power methodology | §III-C `synthesis_method.tex` |
| R4-8 | Throughput / latency / energy | `tab:perf`, §IV-A |
| R4-9 | Full baseline set incl. PIM | `tab:baselines` |
| R4-10 | Perplexity methodology detail | `tab:method`, §IV-B |
| R4-11 | Long-context evaluation | `tab:longctx`, §IV-D |

**Drafted section files** (`PAPER/`): `contributions.tex`, `background_ud.tex`, `fig_architecture.tex`, `gain_compensation.tex`, `synthesis_method.tex`, `number_formats.tex`, `performance.tex`, `evaluation.tex`, `integration.tex`, `related_work.tex`, plus `RENAME_CHECKLIST.md`.

**Outstanding placeholders:** `<<TBD>>` × 17 (mostly synthesis numbers), `\todocite{poly}`, and the prior-work rows in `tab:baselines`.

---

## 6. Schedule — 26 days

| Window | Focus | Gate |
|---|---|---|
| **Sep 17 – Sep 21** | Synthesis runs 1–9 (gain comp, front-end, BFP) | **Architecture decided.** Abstract and conclusion unblocked |
| **Sep 21 – Sep 25** | Runs 10–15; fill every `<<TBD>>`; compile Fig. 1 | All numbers final; no placeholders left |
| **Sep 25 – Oct 1** | Assemble the manuscript from `PAPER/*.tex`; abstract, conclusion, rename checklist | Full draft, inside the page limit |
| **Oct 1 – Oct 6** | T5 repo release; prior-work rows; polynomial baseline if time | Artifact live; coauthor review |
| **Oct 6 – Oct 11** | Coauthor revisions, trim, formatting | Sign-off |
| **Oct 11 – Oct 13** | Buffer and submission | Submitted |

**Gate at Sep 21:** if runs 1–2 show the compensation block costs near a multiplier (~570 µm²) rather than ~150 µm², merged UD loses its advantage and the paper leads with Binary UD instead. Either outcome is publishable, but the abstract, contribution order and conclusion all change, so this cannot slip.

The binding constraint is no longer experiments — it is assembling ten drafted sections into four pages.

---

## 7. Risk register

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| R8 | **Compensation block costs more than estimated** (S-13) | Flips the headline architecture | Runs 1–2, first thing. Fallback is comfortable: Binary UD has a verified encoder and carries C1 cleanly |
| R5 | **Ten drafted sections do not fit four pages** | Formatting scramble in the last week | Cut list in §3.2 is pre-agreed. Fig. `fig:tradeoff` already deleted. Assemble early (Sep 25) so the trim is deliberate |
| R9 | **Fig. 1 has never been compiled** | A broken figure discovered late | One `pdflatex` pass, day one of the Sep 21–25 window |
| R10 | **Prior-work comparison rows stay empty** | R2-2/R4-9 remain half-answered | Numbers must be read out of RoPIM and Li et al. Budget an hour; an honest "not directly comparable" row beats a fabricated conversion |
| R3 | Reviewer 3's novelty objection repeats | Reject | Three RoPE-specific results now drafted. The risk is presentation, not substance — make C1 and the impossibility argument prominent in the abstract |
| R11 | **Harness bugs found late** | Invalidates accuracy results again | Three silent failures already found (double shift, saturation, no-op override). `VERIFY/run_all.sh` is the regression; the plausibility guard catches broken baselines automatically |
| R4 | Long-context result reads as unremarkable | Weakens R4-11's answer | It is a positive finding with a mechanism (exact range reduction). State the mechanism, not just the numbers |

**Retired:** R1 (CSD convergence bug — datapath was sound), R2 (multiplier beats us — resolved by the corrected operating point, §2.2), R6 (RTL ≢ Python — replaced by a verified model), R7 (encoder critical path — written and verified).

## 8. Findings log

Append dated entries as work lands. Newest first.

### 2026-09-17 — synthesis tooling: 17 runs reduced to one command

Hand-editing `parameter` defaults 17 times is where a sweep goes wrong, so the
per-design scripts are replaced by four files in `SCRIPTS/`:

| file | role |
|---|---|
| `synth_generic.tcl` | one Genus script for every run, driven by environment variables. Same library, corner, flow and effort as the earlier campaign, so new numbers stay comparable |
| `set_params.py` | copies the RTL per run and rewrites parameter defaults in the copy. **Aborts if a parameter is not found**, rather than silently synthesising the default |
| `run_all_synth.sh` | all 17 configs; accepts run numbers for a subset; isolates each run in `build/NN_name/` so one failure costs one run |
| `collect_results.py` | parses every run's reports into a `run,design,area_um2,slack_ps,power_mW` CSV |

Verified locally: substitutions correct across all parameter spellings in the
tree (`W    = 12`, `W = 8`, `WIDTH  = 9`), multi-module files (`rope_bfp_norm.v`
— both modules), multi-file designs (standard CORDIC — W in three files,
STAGES in two), the abort path, and that a parameterised copy still elaborates
in iverilog.

Usage on the Genus machine:

```
export SYN_LIBBASE=/path/to/gsclib045_all_v4.8
./SCRIPTS/run_all_synth.sh            # or: ./SCRIPTS/run_all_synth.sh 1 2 5 6 7 8 15
python3 SCRIPTS/collect_results.py build
```

Combinational blocks use `original_rope.sdc` (max-delay only); the pair modules
use `rope.sdc` (clocked).

### 2026-09-16 — T2.11: block granularity measured

Swept the shared-exponent block size over **real** Qwen2 query activations
(synthetic data would have assumed the answer, since the question is precisely
how much dynamic range sits inside one block).

| F | D=1 | D=2 | D=4 | D=8 | D=16 | D=64 |
|---|---|---|---|---|---|---|
| 14 | 0.00034 | 0.00036 | 0.00038 | 0.00042 | 0.00048 | 0.00057 |
| 12 | 0.00053 | 0.00067 | 0.00090 | 0.00120 | 0.00158 | 0.00204 |
| 11 | 0.00088 | 0.00126 | 0.00186 | 0.00258 | 0.00341 | 0.00445 |
| 10 | 0.00178 | 0.00279 | 0.00397 | 0.00558 | 0.00750 | 0.00993 |

Two results. A **per-element exponent is worth about two bits of mantissa**
(3.8× error reduction from D=64 to D=1) — so the coarse block is not free, and
saying so is more honest than the earlier "buys no additional range" claim.
And **past D=16 there is no gain whatsoever**: the exponent is a power of two,
so two blocks only differ when their maxima fall in different octaves, which
at this width they rarely do.

This makes the FP8/FP4 answer quantitative: a per-element float format buys
two bits here and costs an exponent field, alignment and normalisation on
every lane instead of one reduction tree per 64. Folded into
`number_formats.tex` as `tab:blocksize`. The cost half of the trade needs
synthesis runs 7 (D=64), 16 (D=8) and 17 (D=16).

### 2026-09-16 — correction: the front-end does not amortise across lanes

Found while working out T2.3. Two already-drafted files claimed the angle
front-end is "shared across all $d/2$ lanes". **That is wrong.** Since
θ_i = m·Θ_i depends on i, every lane needs its own angle and its own
encoder — there is nothing to share across lanes.

What is true, and stronger: the angle depends only on (m, i) and **never on the
data**, so the digit string for a given (m, i) is identical in every head,
every layer and every batch element. For LLaMA-2-7B that is 32 × 32 = **1024
reuses**, against the 64 I incorrectly claimed. The amortisation is larger, on
a different axis.

Corrected in `contributions.tex` and `fig_architecture.tex` (caption and the
figure's own annotation). The lesson: the claim survived three drafts because
it sounded plausible and nobody had yet had to say *which* signal was shared.

### 2026-09-15 — T3.6 re-run works, but the experiment is confounded. Mechanism proved analytically instead.

Override now verified live (`via rope_parameters['rope_theta']`, baselines differ). Result:

| base | fp16 baseline | vs native | F=9 | F=8 | F=7 | F=6 |
|---|---|---|---|---|---|---|
| 10⁴ (native) | 5.5314 | 1.00× | +0.075% | +0.303% | +1.44% | +11.3% |
| 10⁵ | 6.8515 | 1.24× | +0.046% | +0.141% | +0.95% | +8.05% |
| 10⁶ | 13.5410 | **2.45×** | −0.324% | −0.581% | −1.33% | +9.06% |

**The cliff does not migrate, and the experiment cannot be used.** LLaMA-2 was *trained* at base 10⁴; forcing 10⁶ at inference degrades the un-approximated model 2.45× before any hardware is involved. The deltas are therefore measured against an already-broken baseline, and the negative deltas at 10⁶ — approximation apparently *improving* perplexity — are the signature of that. Overriding the base is not equivalent to training with it.

**T3.6 as designed is abandoned.** Two better routes:

1. **Analytical (done, no GPU needed).** For a small residual angle the rotation is x′ ≈ x − θy; with the input block-normalised to |y|≈1 that perturbation is representable only if θ > 2^−F. Below it the pair does not rotate at all — the positional signal is discarded, not degraded, which is why the failure is a cliff rather than a slope. Share of (position, dimension) pairs whose rotation quantises to zero:

| F | LSB | b=10⁴ | b=10⁵ | b=10⁶ |
|---|---|---|---|---|
| 12 | 0.00024 | 0.07% | 0.23% | 0.95% |
| 10 | 0.00098 | 0.20% | 0.57% | 3.26% |
| 9 | 0.00195 | 0.28% | 0.98% | **6.43%** |
| 8 | 0.00391 | 0.43% | 1.79% | **11.40%** |
| 7 | 0.00781 | 0.71% | 3.38% | 16.49% |

At base 10⁶ the loss rate crosses ~6% between F=10 and F=9 — exactly where Qwen2's measured cliff sits (+0.103% → +6.36%). This is a property of the frequency schedule alone, derived without reference to any model, and it is a **stronger** argument than the override experiment would have been.

2. **Better controlled model pair (optional, ~1 GPU hour).** CodeLlama-7B is the LLaMA-2 architecture *retrained* at base 10⁶. Comparing it against LLaMA-2-7B holds architecture and size fixed with a base the model was actually trained for. Worth running if GPU time allows; the analytical argument stands without it. **→ T3.7.**

Reproduce the analysis: `VERIFY/angle_loss.py`.

### 2026-09-15 — T3.6 first attempt was a silent no-op. Invalid; re-run required.

All three rope-base runs returned **byte-identical results**, fp16 baseline included (5.5314 at every base). Identical baselines are the proof: changing the frequency schedule must change the unpatched model's perplexity, so if the baseline doesn't move, the override never reached the model.

Cause: `cfg.rope_theta` does not exist on a LLaMA config in transformers 5.x — the value lives in `cfg.rope_parameters["rope_theta"]`. Assigning the bare attribute created a new one the model never reads. The log said so plainly (`rope_theta override: None -> 10000.0`, `base_orig = None`) and I did not check it.

Fixed: `_set_rope_base` now writes every location the base can live in (including nested `text_config`), returns the list of sites written, **fails loudly if that list is empty**, and asserts a readback match before loading. Verified on Mistral: 10⁴ → writes `rope_parameters['rope_theta']` → reads back 10⁶.

**Methodological note worth carrying into the paper's reproducibility discussion:** this is the third silent failure in this harness (double-shift, datapath saturation, now a no-op override), and in each case the giveaway was a number that should have moved and didn't, or moved implausibly. The plausibility guard on the baseline caught Gemma-2 automatically; this one needed the three-identical-outputs observation. Any config override that cannot be read back should be treated as not having happened.

**Delete the three `results_ropebase_*.json` before re-running** — the skip-if-exists check will otherwise preserve the invalid files.

### 2026-09-15 (later) — Phi-3 lands; five models measured. Recommend stopping here.

Phi-3-mini (3.8B, RoPE base 10⁴): baseline 6.0059, then +0.021% (F=10), +0.071% (F=9), +0.337% (F=8), +1.617% (F=7), +9.916% (F=6) — squarely in line with the other base-10⁴ models.

**Table IV model set, all re-measured with the corrected harness:**

| model | params | RoPE base | F=10 | F=9 | F=8 | F=7 |
|---|---|---|---|---|---|---|
| Phi-3-mini | 3.8B | 10⁴ | +0.021% | +0.071% | +0.337% | +1.62% |
| Mistral-7B | 7B | 10⁴ | +0.012% | +0.036% | +0.131% | +0.57% |
| LLaMA-2-7B | 7B | 10⁴ | +0.020% | +0.078% | +0.318% | +1.50% |
| LLaMA-2-13B | 13B | 10⁴ | +0.020% | +0.063% | +0.233% | +1.13% |
| **Qwen2-7B** | 7B | **10⁶** | **+0.103%** | **+6.36%** | **+131%** | **+8075%** |

Four models spanning **3.8B to 13B** — a 3.4× parameter range — agree to within a factor of ~3 at every precision. The one model with a different frequency schedule diverges by four orders of magnitude. This is a stronger evidence structure than the submitted paper's seven models, all of which shared base 10⁴ and therefore could not have revealed the effect at all.

**Recommendation: stop adding models.** Falcon-7B and Gemma-2-9B are both base 10⁴ and would add two more confirmatory points to a trend already established across a 3.4× size range. T3.6 (explicit base override on a fixed model) is worth more than either.

**Self-inflicted bug, now fixed.** The `rope_scaling` shim that rescued Phi-3 broke Falcon and Gemma-2: in transformers 5.x `rope_scaling` and `rope_parameters` are aliases, so clearing the field makes native model code fail on `rope_parameters["rope_type"]`. Repo-hosted code needs it cleared; native code needs it intact. The shim is now opt-in behind `--fix_rope_scaling`. General lesson worth keeping: a compatibility shim applied unconditionally is itself a portability bug.

### 2026-09-15 — five-model re-run: 3 of 5 landed, and T3.4 is now near-controlled

**LLaMA-2-13B is the important one.** Same RoPE base as LLaMA-2-7B (10⁴), nearly double the parameters, and the precision curve is almost identical:

| $\Delta$ ppl | F=10 | F=9 | F=8 | F=7 | F=6 |
|---|---|---|---|---|---|
| LLaMA-2-7B | +0.020% | +0.078% | +0.318% | +1.495% | +11.53% |
| **LLaMA-2-13B** | **+0.020%** | **+0.063%** | **+0.233%** | **+1.130%** | **+10.45%** |
| Mistral-7B | +0.012% | +0.036% | +0.131% | +0.567% | +3.04% |
| **Qwen2-7B** | **+0.103%** | **+6.355%** | **+131%** | **+8075%** | **+47621%** |

Baselines: 4.8800 / 5.4680 / 5.2491 / 7.1405.

**Model scale is now controlled.** Three base-10⁴ models spanning 7B–13B all degrade gracefully and land within a factor of ~2 of each other at every F; the single base-10⁶ model diverges by four orders of magnitude at F=8. Doubling parameters changes nothing; changing the frequency schedule changes everything. T3.4 has gone from "correlation across two families" to "controlled for size across four models" — T3.6 (explicit base override) would close it completely, but the claim is already defensible.

**Gemma-2-9B rejected by the guard.** fp16 baseline came out at 196.88, and the plausibility check fired. This is the known Gemma-2 fp16 overflow — the model is bf16-trained and its logit softcapping overflows in fp16. Re-run with `--dtype bfloat16`. **The guard added after the first harness bug did exactly its job**: a plausible-looking monotone curve on a broken baseline would otherwise have gone straight into Table IV.

**Falcon-7B** failed in `patch_model`: its legacy repo code has no `apply_rotary_pos_emb`. The native transformers implementation does — fixed with a new `--no_remote_code` flag.

**Phi-3** failed differently this time: my first shim mirrored `rope_type="default"` into `type`, and Phi-3's code rejects `default` as an unknown scaling mode. Corrected — an unscaled config is now *cleared* rather than translated.

Also fixed: `rope_theta` was recording 0.0 in the metadata. `_find_rope_base` now searches the nested locations transformers 5.x uses (verified: Mistral 10⁴, Qwen2 10⁶). This matters because the RoPE base is now load-bearing for the paper's central claim and belongs in the results table.

### 2026-09-14 (later) — gap-filling run: R4-11 answered, and it is good news

**Precision sweep completed** (F=13 and F=11 added). Full picture, full test split, ctx 2048:

| F | LLaMA-2-7B | Qwen2-7B |
|---|---|---|
| 14 | +0.001% | −0.000% |
| 13 | +0.001% | −0.002% |
| 12 | +0.003% | +0.005% |
| 11 | +0.005% | +0.018% |
| **10** | **+0.020%** | **+0.103%** |
| 9 | +0.078% | **+6.355%** |
| 8 | +0.318% | +131.5% |

Qwen2's cliff is sharp and sits between F=10 and F=9 — two orders of magnitude across one bit. **F=11 is the defensible recommendation** (+0.005% / +0.018%, one bit of margin above the cliff); F=10 is the aggressive choice.

**Long context (R4-11) — answered, and the answer is favourable.**

| | ctx 1024 | 2048 | 4096 |
|---|---|---|---|
| LLaMA-2 F=10 | +0.026% | +0.020% | +0.020% |
| LLaMA-2 F=9 | +0.098% | +0.078% | +0.086% |
| Qwen2 F=10 | +0.146% | +0.103% | **+0.080%** |
| Qwen2 F=9 | +3.047% | +6.355% | +4.392% |

**At adequate precision the relative degradation does not compound with sequence position — it is flat or mildly decreasing.** This is the substantive answer to R4-11 and it is a positive result: despite θ = m·Θᵢ growing without bound, range reduction is exact (mod 2π is free in a phase accumulator), so error does not accumulate with position. Qwen2 F=9 is non-monotonic (3.0 → 6.4 → 4.4) but that is an already-broken operating point and should not be over-read.

**Phi-3-mini failed to load**, both runs: `KeyError: 'type'` in its remote `modeling_phi3.py` `_init_rope`, which reads `rope_scaling["type"]` while the current config ships `rope_type`. A model/transformers incompatibility in Microsoft's code, not ours. Compat shim added (mirrors `rope_type` → `type`, clears malformed entries).

**New capability — controlled test of the T3.4 hypothesis.** `--rope_base` now overrides `config.rope_theta`. The frequency-schedule explanation is currently supported by a *correlation across two model families*; overriding the base on a single fixed model converts it into a controlled experiment. Proposed: LLaMA-2-7B at rope_theta ∈ {10⁴ (shipped), 10⁵, 10⁶} against the F sweep. If its precision requirement migrates toward Qwen2's as the base rises, the mechanism is demonstrated rather than inferred — a materially stronger claim for R3-1. **→ T3.6.**

### 2026-09-14 — Kaggle results in: full WikiText-2, Qwen2-7B + LLaMA-2-7B. T3.5 settled; T3.4 explained.

Full test split (298931 tok Qwen2, 341302 tok LLaMA-2), ctx 2048, fp16, corrected harness.

**Precision sweep — the requirement is model-dependent, which is the real story.**

| F | LLaMA-2-7B | Qwen2-7B |
|---|---|---|
| baseline | 5.4680 | 7.1405 |
| 14 | +0.001% | −0.000% |
| 12 | +0.003% | +0.005% |
| **10** | **+0.020%** | **+0.103%** |
| 9 | +0.078% | **+6.355%** |
| 8 | +0.318% | +131.5% |
| 7 | +1.495% | +8074.7% |
| 6 | +11.53% | +47621% |

**T3.4 explained.** The Qwen2 outlier the old paper reported but never accounted for is the RoPE base: Qwen2 uses θ_base = 10⁶ against LLaMA-2's 10⁴. The larger base spreads Θᵢ over a far wider dynamic range, so low-frequency dimensions carry very small angles that need more fractional bits to resolve. LLaMA-2 tolerates F=8 (+0.32%); Qwen2 needs F=10. Same architecture, same hardware, a 2-bit difference driven purely by the frequency schedule — a genuinely RoPE-specific result that no prior CORDIC paper could have found.

**Recommended operating point: F=10 (W=12)** covers both models (+0.02% / +0.10%); F=12 is the conservative choice. The published "F=7 saturates, F=9 optimal" is wrong by 3 bits on Qwen2.

**T3.5 SETTLED — CSD is viable, and cheap compensation suffices.**

| config | LLaMA-2-7B | Qwen2-7B |
|---|---|---|
| no compensation | +908.3% | +76.2% |
| **H1 (3 constants)** | **+0.617%** | **+0.767%** |
| H2 (9 constants) | +0.005% | +0.008% |

S-13 confirmed on real models — uncompensated CSD is unusable. But H1, the ~100–150 µm² muxed shift-add block, lands under 0.8% on both, and H2 is essentially free. **The architecture question now turns entirely on T2.9.**

Provisional area picture at the corrected operating point, W=14, from §2.1:

| design | area | note |
|---|---|---|
| **CSD UD N=5 + H1 comp** | **~3617 µm²** | 3467 measured + ~150 estimated |
| Binary UD N=10 | 4346 µm² | carries C1, no comp needed |
| Mult RoPE | 4185 µm² | **does not generate sin/cos** |
| LUT RoPE | 5375 µm² | complete baseline |

If T2.9 confirms the compensation cost, **CSD+H1 leads**: −16% vs Binary UD, −33% vs the complete LUT baseline. Note Binary UD at 4346 is slightly *larger* than the incomplete multiplier baseline at 4185 — another reason T2.1 (fair front-end accounting) is not optional.

**Long context (R4-11) — direction depends on precision.**

| | ctx 1024 | 2048 | 4096 |
|---|---|---|---|
| LLaMA-2 F=7 | +1.572% | +1.495% | +1.489% |
| Qwen2 F=7 | +3635% | +8075% | +11911% |
| both F=14 | ~0% | ~0% | ~0% |

At a precision the model tolerates, error is **flat or slightly improving** with context — worth stating plainly. Where precision is already insufficient (Qwen2 F=7) error **compounds with position**, consistent with θ = m·Θᵢ growing without bound. Caveat: F=7 is a regime nobody would deploy, so this must be re-run at F=10 before it can be claimed.

**Gaps from this run — all cheap to close:**
1. **F=11 and F=13 missing** — root cause found 2026-09-14: two later notebook cells re-ran `cp` from `/kaggle/input` *after* the patch cell, restoring the pristine file and silently reverting the edit. Fix is ordering — nothing may copy from the dataset after the patch. Re-run `sweep_F` for a tighter boundary around F=10–12.
2. **Phi-3-mini produced no output** — job appears to have failed; check the batch log.
3. **ctx 8192 returned nan / 0 tokens** on Qwen2 — almost certainly OOM on T4.
4. **Long context at F=10 never measured** — only F=7 (broken) and F=14 (perfect). This is the run that actually answers R4-11.

### 2026-09-13 — S-14: the datapath saturates on real LLM activations. Two headline claims change.

Two bugs found while bringing the perplexity harness up, the second of which is a real architectural finding.

**Bug 1 (harness, mine): double shift.** Pre-shifted targets were passed to `labels=`, which HF shifts again — scoring P(t+2 | t). Fixed by computing the loss explicitly. Validated: GPT-2 on WikiText-2 gives 32.2 at ctx 1024, textbook range. The earlier tiny-random-model smoke test could not catch this, since a uniform-output model is shift-invariant.

**Bug 2 — S-14, and this one is about the architecture.** Q1.(W−2) represents [−2, +2). Measured on Qwen2, real activations reach **|q| = 132, |k| = 178** (median ~20). Essentially every value saturated at the clamp. **A bare fixed-point RoPE datapath cannot hold LLM query/key activations** — normalization before the rotator is mandatory, and the paper never mentions it. That the published perplexity numbers show no such effect is further evidence for S-5 (the Python model and the RTL are different designs).

Fix modelled: **block floating point**, one shared exponent per (head, token), scaled so |x| < 1 with headroom for the CORDIC gain 1.164. In hardware this is a barrel shift in and out with the exponent carried alongside — cheap, and it is exactly the integration detail R4-1 asked for. **New RTL block to design and synthesize → T2.10.**

**Validated end to end on Qwen2-0.5B** (real weights, real RoPE, WikiText-2, 12k tokens, ctx 1024, fp32):

| config | ppl | delta vs baseline |
|---|---|---|
| fp32 baseline | 15.6181 | — |
| Binary UD N=10, F=14 | 15.6208 | +0.017% |
| Binary UD N=10, F=9 | 17.0691 | **+9.29%** |
| Binary UD N=10, F=7 | 53.1645 | **+240%** |
| Binary UD N=10, F=5 | 2037.75 | +12947% |
| CSD N=5, no comp | 238.34 | +1426% |
| **CSD N=5, H1** | **15.9685** | **+2.24%** |
| CSD N=5, H2 | 15.6197 | +0.010% |

**Consequence 1 — the "F=9 optimal / F=7 indistinguishable" claim is dead.** With a correctly saturating datapath F=9 costs 9.3% perplexity and F=7 is catastrophic. The published table showed F=7 as free because saturation was never modelled. The real optimum is higher, likely F=12–14, which *raises* the area and power of every proposed configuration and must be re-derived against the baselines in §2.1. **This is the single biggest change to the paper's results.**

**Consequence 2 — T3.5 answered, and CSD survives.** Uncompensated CSD is destroyed (+1426%), confirming S-13 on a real LLM rather than by argument. But the cheap 3-constant H1 shift-add compensation recovers to +2.24%, and H2 to +0.01%. So ~100–150 µm² of compensation is enough, and **T2.9 (synthesize it) now decides the headline architecture.**

Caveat on all of the above: 0.5B model, 12k tokens, fp32, one block-size choice. Indicative, not final — the 7B runs are the real numbers.

**New design knob (T2.11):** block granularity. One exponent per (head, token) is what was modelled; per-pair would be more accurate and more expensive. That tradeoff is a genuine RoPE-specific co-design result and feeds contribution C2.

### 2026-09-13 — T1.8 part A done (Table I regenerated); part B ready for Kaggle

**Table I regenerated** with the working encoders (`VERIFY/table1_regen.py`). Both families now converge at the expected rate instead of plateauing:

| Method | N | published | regenerated | gain spread |
|---|---|---|---|---|
| Binary UD | 5 | 3.88° | 2.004° | 0.00% |
| Binary UD | 10 | 2.20° | **0.063°** | 0.00% |
| CSD UD | 5 | 3.38° | **0.043°** | 93.4% |
| CSD UD | 8 | (3.13° @ N=10) | 0.006° | 93.0% |

The published column being flat in N was the encoder failing, not a precision limit. The N/2 equivalence claim is now genuinely supported — CSD N=5 (0.043°) does beat Binary N=10 (0.063°) on angle. The gain-spread column is new and is where the architectures actually differ.

**Perplexity harness built and locally validated** — `KAGGLE/rope_hw.py`, `KAGGLE/eval_perplexity.py`, `KAGGLE/validate_hw.py`, `KAGGLE/KAGGLE_INSTRUCTIONS.md`.

The torch model is a vectorized twin of the RTL, and `validate_hw.py` proves it:
- encoder vs the 485 iverilog golden vectors: **485/485 exact**
- end-to-end rotation RMS vs iverilog: 0.0891 vs 0.0899 (W=16), 0.1049 vs 0.1071 (W=12), 0.4532 vs 0.4536 (W=9) — agreement to 0.002°
- smoke-tested end to end on a real (tiny) LLaMA through the actual HF patch path

Key design points: only the **rotation** is approximated (weights/activations/Q/K stay fp16); digit tables depend only on (position, dim) so they are computed once and reused across every layer, head and batch element; angles are recovered as atan2(sin, cos) from the model's own tables, so the patch is model-family agnostic.

Every run prints a **self-test** giving the relative vector error per config, so a patch that fails to attach is caught before any GPU time is spent:

| config | rel err |
|---|---|
| binaryUD_N10_F14 | 0.0017 |
| binaryUD_N10_F9 | 0.0092 |
| binaryUD_N10_F7 | 0.0378 |
| csd_N5_nocomp | 0.2490 |
| csd_N5_H1 | 0.0253 |
| csd_N5_H2 | 0.0019 |

Three sweeps defined: `sweep_F` (replaces Table IV), `csd_gain` (settles **T3.5**), `longctx` (closes **R4-11**). The JSON `meta` block answers every item on Reviewer 4's methodology list. Two things stated rather than glossed: it is a custom harness, not lm-eval-harness, and `use_cache=False`.

**Blocked on:** Kaggle runs. Priority models are Qwen2-7B and LLaMA-2-7B — rope base 1e6 vs 1e4, which is the contrast that should explain the Table IV Qwen2 outlier (**T3.4**).

### 2026-09-13 — CORRECTION to the T1.9 verdict: CSD is not dead

The entry below compared **CSD UD (Ext.) at N stages against standard CORDIC at N stages**. That is not a meaningful comparison — CSD's premise is that N/2 CSD stages carry the precision of N binary stages, so matched *stage count* gives CSD twice the resolution. The correct basis is matched **precision**. Two corrections follow, and they change the recommendation.

**1. The N/2 equivalence is real** — now measured rather than asserted, using the T1.9 feed-forward encoder: Binary UD N=10 gives 0.063° angle RMS, CSD N=5 gives 0.043°. CSD N/2 matches (slightly beats) Binary N on angle.

**2. At matched precision CSD is genuinely smaller** (W=9, measured):

| architecture | area | power | vs Std | vs Binary |
|---|---|---|---|---|
| Std CORDIC N=10 | 3292 µm² | 3.06 mW | — | — |
| Binary UD N=10 | 3068 µm² | 2.00 mW | −6.8% | — |
| **CSD UD N=5** | **2330 µm²** | **1.12 mW** | **−29.2%** | **−24.1%** |

**3. My "compensation erases the advantage" claim was wrong twice over.** It compared CSD at W=9 (2330) against Binary UD at **W=8** (2728) — a word-length mix-up — and it assumed a full multiplier. Corrected: two W=9 multipliers cost ~1148 µm² (k ≈ 7.09 µm²/bit² from `mult_rope` W=8 vs W=9), which *would* put CSD at 3478 µm², 13.4% worse than Binary UD. **But compensation does not need a multiplier.** The head gains take only 3 distinct values at H=1 (1/K ∈ {0.5547, 0.7071, 1.0}) and 9 at H=2. Those are *constants* — a muxed shift-add network of order 100–150 µm², not 1148.

**Revised position.** CSD still cannot carry C1 — the angle-dependent gain (S-13) stands, and that remains a real RoPE-specific finding. But the architecture choice is now open, and it turns on two measurements neither of which exists yet:
- **Synthesize the compensation block** (muxed constant scalers, H=1 and H=2) and get its real area/power/timing.
- **Run H=1's 7.3% residual gain spread through the LLM eval.** If perplexity tolerates it, CSD keeps most of a 24% area and 44% power win. That is a perplexity question, not a hardware one.

→ New task **T2.9**; the headline-architecture decision is deferred until both land. Reproduce with `VERIFY/csd_fair.py`.

### 2026-09-13 — T1.9: CSD encoder investigated (verdict superseded by the correction above)

New file: `VERIFY/csd_encoder.py` (+ `csd_verdict.py`, `csd_rescue.py`, `csd_lut_enc.py`, `csd_booth_fix.py`).

**An encoder is achievable.** Feed-forward P=2 brute force reaches 0.043° RMS at N=5, 0.012° at N=6 — better than the sequential greedy oracle, which is myopic. Replacing the 25-way brute force with a 64-entry ROM head gives 0.073° at N=5 and 0.017° at N=6, at far lower cost. So angular accuracy was never the obstacle.

**But the gain is, and no encoder can fix it (S-13).** What RoPE consumes is the rotated vector, not the angle. Measuring RMS relative vector error after dividing out the best constant gain:

| architecture | angle RMS | gain spread | **vector error** |
|---|---|---|---|
| Binary UD N=10 | 0.063° | **0.000%** | **0.00111** |
| CSD as-built N=5 | 0.043° | 93.4% | 0.24860 |
| CSD Booth {0,±1,±2} N=5 | 0.040° | 152.1% | 0.33237 |

CSD's angle error is *better* than Binary UD's, and its vector error is **224× worse**. The reason is structural: stage gain is √(1+v²4^−i), which depends on digit *magnitude*. Any digit set with more than one magnitude has angle-dependent gain, and a fixed-magnitude set is one bit per stage — which is exactly Binary UD. **Constant gain and radix-4 stage merging are mutually exclusive.**

**The rescue attempt fails on cost.** Stages 0 and 1 cause ~87% of the spread, so a 25-entry ROM plus one multiplier brings CSD to 0.00186 vector error — comparable to Binary UD. But from the `mult_rope` synthesis data (1953 µm² for 4 multipliers at W=9, so ~400–450 µm² each), that puts corrected CSD at **~2750 µm² against Binary UD's measured 2728 µm²** — same area, plus a ROM and a multiplier in the critical path, to reach accuracy Binary UD gets for free via C1.

**Two honest caveats.** The demonstrated tail still contains a borrow chain, so a fully parallel CSD encoder is unproven; and a pure parallel-Booth tail gave ~5° and does not work as I constructed it. Neither is worth fixing given the verdict.

**Consequences for the paper.**
- **Binary UD becomes the headline architecture.** It has a verified encoder (T1.7), constant gain, and C1.
- **CSD becomes a characterized negative result** — and that is a genuine contribution, not a retreat. "Radix-4 merging cannot coexist with constant gain, so it is the wrong trade for RoPE specifically" is exactly the RoPE-specific analysis Reviewer 3 said the paper was missing. It also explains the Table II anomaly the paper never accounted for: **CSD UD (Ext.) at matched N is consistently *larger* than standard CORDIC** (3769 vs 2773 at N=8, 4820 vs 3292 at N=10, 5970 vs 3813 at N=12).
- Table I, Table II framing, and the abstract all need rewriting around Binary UD.

### 2026-09-13 — T1.7 complete (Binary UD): the encoder is written and verified

New files: `RTL/rope_angle_encoder.v` (+ `rope_range_reduce`), `VERIFY/encoder_design.py`, `VERIFY/encoder_hw.py`, `VERIFY/gen_golden.py`, `VERIFY/tb_angle_encoder.v`, `VERIFY/tb_e2e.v`, `VERIFY/run_all.sh`.

**The algorithm.** Rotations compose additively, so the achieved angle is exactly Σᵢdᵢaᵢ with aᵢ = arctan(2^−(i+1)). Substituting dᵢ = 2bᵢ−1 turns encoding into a subset-sum: S := (θ+A)/2 = Σᵢbᵢaᵢ. The weights are only *approximately* geometric — aᵢ/2^−(i+1) = 0.9273, 0.9799, 0.9948, 0.9987, 0.9997… The tail (i ≥ 2) is geometric to better than 0.13%, so its digits are literally the fixed-point bits of the residual. Only the head is non-geometric, and that is exactly what the paper's Eq. 5 gets wrong. So: **threshold-decode the 2 head stages against the four reachable head sums {0, a₁, a₀, a₀+a₁}, then bit-extract the tail.**

**Cost:** 1 adder, 3 constant comparators, one 4:1 constant mux, 1 subtractor. Fully combinational — **no Z-path**, so the architecture's central claim survives.

**Accuracy** (θ over ±45°, the residual after free quadrant folding):

| N | naive/affine | **proposed** | greedy oracle (sequential) |
|---|---|---|---|
| 6 | 1.174° | 1.006° | 0.512° |
| 8 | 1.083° | 0.255° | 0.129° |
| 10 | 1.079° | **0.063°** | 0.032° |
| 12 | 1.079° | 0.016° | 0.008° |

The affine encoder floors at ~1.08° no matter how deep the pipeline — that is the systematic non-geometry. The proposed encoder converges properly and tracks the sequential oracle within ~2×.

**Verification.**
- `tb_angle_encoder.v`: 485/485 vectors match the bit-exact model, boundaries included. **PASS.**
- `tb_e2e.v` (encoder → real `binary_ud_cordic_core`): 0.090° RMS at W=16, 0.107° at W=12, 0.454° at W=9 (datapath quantization dominates below W≈12).
- **Versus the paper's reported 2.20° for Binary UD N=10: 23× better at W=16, 4.9× better at the paper's own W=9.**
- **C1 confirmed on silicon-ready RTL:** measured gain 1.164426 against theoretical 1.164435, spread ±0.0003 across all angles at W=16. Angle-independent, exactly as the free-compensation argument requires.
- Full path including range reduction over [0, 2π): 0.107° RMS, 0.196° peak at N=10.

**Reproduce:** `cd VERIFY && ./run_all.sh` (needs python3 + iverilog).

**Still open:** the CSD encoder (**T1.9**). Its digit set {0,±1,±1.5}·2^−2i violates the CORDIC convergence condition, so the reachable set has holes (max gap 0.2239° at N=5). Oracle digits reach 0.0595° at N=5, so a good encoder exists — the open question is whether a feed-forward one does, and whether it costs less than it saves.

### 2026-09-13 — T1.1 / T1.2 complete: CSD datapath verified

Bit-accurate models in `VERIFY/` (`csd_verify.py`, `csd_search.py`, `csd_control_test.py`, `range_check.py`) mirror `csd_ud_stage.v`, `csd_ud_cordic_core.v`, `csd_control.v`.

**Verdict: the datapath is sound. The angle encoder is the defect.**

1. **Datapath converges properly (Control 2).** With oracle digit selection, RMS angular error over θ ∈ [0,1] rad falls 0.2376° (N=4) → 0.0595° (N=5) → 0.0148° (N=6) → 0.0009° (N=8) → 0.0001° (N=10) — about 4× per stage, exactly right for a radix-4 merged structure. **The architecture is not broken and the CSD area/power numbers remain meaningful.**
2. **The encoder never converges.** Exhaustive search over 16 conventions (Booth carry direction × digit-2 weight × shift order × bit order) gives 52–74° RMS error, **flat in N** in every case. `csd_control.v` applies radix-4 Booth in a weight direction inconsistent with the datapath's ascending shifts: Booth assigns digit *i* weight 4^(+i) while stage *i* applies 4^(−i).
3. **Same defect class in Binary UD.** Feeding the plain binary expansion — literally what paper Eq. 5 prescribes ("δᵢ extracted from the i-th bit of the binary-represented angle") — gives ~30° RMS, flat in N. With correct greedy encoding it converges: 2.21° (N=4) → 0.30° (N=10). **Eq. 5 as written does not describe a working encoder.**
4. **Table I's plateau is the encoder, not a feature.** Flat-in-N is the signature of both broken encoders. The paper's claim that N/2-stage CSD "captures the precision of N-stage Binary UD" is unsupported — both were simply failing to converge, at different plateaus.
5. **±2 = 1.5 is harmless (T1.2 closed).** Under oracle digits it beats textbook 2.0 slightly (0.0595° vs 0.0648° at N=5), with identical reachable granularity (max gap 0.2239°). Not the cause of anything. Downgraded to a documentation item (T4.9).
6. **S-11 — CSD gain is angle-dependent, K ∈ [1.00, 1.93].** Digit 0 gives gain 1.0, digit ±1.5 gives 1.803. Binary UD, with δ ∈ {−1,+1} always, has constant K = 1.164435. This **restricts contribution C1 to Binary UD** and means CSD needs real per-angle compensation.
7. **S-12 — reachable range** is ±54.9° (Binary UD, N≥8) and ±84.0° (CSD). RoPE spans 360°, so range reduction is mandatory for every variant.
8. **S-5 strengthened to near-certain.** A faithful model of the CSD RTL shows 52–74° angular error and up to 1.93× angle-dependent gain. Perplexity could not come out FP16-identical under those conditions. The Python evaluation model and the synthesized RTL are **different designs**. The paper's Table I values (3.88/2.20/3.38/3.13°) match neither the greedy model (~0.3–1.2°) nor the naive one (~30–60°), implying a third, undocumented implementation.

**Consequences:** area, power, and timing results are unaffected (they do not depend on digit values). Every *accuracy* result — Table I and all of Table IV — must be regenerated after T1.7. New critical path: **T1.7 (write the encoder) → T1.8 (regenerate accuracy)**.

**Silver lining for the R3 novelty problem:** "we identified that UD-CORDIC needs a non-trivial angle encoder for RoPE, and here is a cheap feed-forward one" is a genuine architectural contribution, and it pairs naturally with C1 and C2.

### 2026-09-13 — Venue confirmed
- Target confirmed as **ISCAS 2027**, deadline 2026-10-13. Added §5 traceability matrix: 17 reviewer issues + 10 self-found issues, each mapped to tasks, with a coverage check.

### 2026-09-13 — Initial audit
- Extracted the complete new synthesis dataset (§2.1); numbers reconcile with the submitted paper's Tables II/III, so old and new results share one basis.
- **Mult RoPE beats CSD UD at W=9** on area, power, and latency (§2.2). Requires reframing, not concealment.
- **No gain compensation exists in any RTL core.** Also the likely basis of contribution C1 — RoPE makes K² foldable into the attention scale for free.
- **`csd_control.v` is radix-4 modified Booth, not canonical signed digit.** The paper's non-adjacency justification for stage merging does not describe the synthesized RTL.
- **Suspected bug in `csd_ud_stage.v`:** the ±2 digit computes 1.5×2^-SHIFT1 instead of 2×2^-SHIFT1. Likely explanation for the CSD accuracy plateau in paper Table I.
- **Library is Cadence GPDK045, not TSMC 45 nm** as the paper states. Corner is `fast_vdd1v2` @ PVT_1P32V_0C (fast, 1.32 V), not the claimed 1.2 V nominal.
- Power is default-toggle estimation with no SAIF/VCD back-annotation.
- No angle range-reduction hardware exists; all four designs receive pre-computed angle representations from outside the synthesized boundary.
