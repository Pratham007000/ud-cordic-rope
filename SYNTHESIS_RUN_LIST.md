# Synthesis runs needed — Genus machine

Updated **2026-09-24** — runs 10-11 promoted to critical path (see plan §2.2:
the multiplier/CORDIC crossover is fitted at W≈11.5 from two points, and runs
10-11 sit on it). Same flow as before (`gsclib045`, 2.0 ns / 500 MHz,
`rope.sdc`). **17 runs**, grouped by what they unblock.

**How to set parameters:** the flow has no parameter passing, so edit the
`parameter` defaults at the top of the module (as the earlier W sweeps were
done), then run the script. One directory per run so `OUTPUT/` does not clash.

**What to send back:** `OUTPUT/reports_*/<design>/opt/final.rpt` and
`.../opt/power.rpt` from each run. A zip of the `reports_*` trees is ideal —
skip the `outputs_*` trees, they are large and unnecessary.

---

## CRITICAL PATH — run these four first: **1, 2, 10, 11**

Two independent decisions, both of which the abstract, contribution list and
conclusion depend on:

* **Runs 1-2** price the gain-compensation block, deciding merged-UD vs Binary-UD.
* **Runs 10-11** put the multiplier and LUT at W=12, directly on the fitted
  crossover (W≈11.5). The paper's central claim is that the measured precision
  requirement (W=13) lies above the crossover. Right now that crossover is
  interpolated between W=9 and W=14. If the true value is 12.5 rather than 11.5
  the margin halves and the framing has to change — so this is a test we run
  before writing, not after.

```
./SCRIPTS/run_all_synth.sh 1 2 10 11
python3 SCRIPTS/collect_results.py build
```

## Priority 1 — decides the headline architecture (T2.9)

`RTL/rope_gain_comp.v`, script `SCRIPTS/rope_gain_comp.tcl`. Verified in
iverilog. If this lands near ~150 µm², merged UD leads at W=14; if it lands
near a multiplier (~570 µm²), Binary UD leads on the strength of C1.

| # | design | params | why |
|---|---|---|---|
| 1 | rope_gain_comp | MODE=1, W=12 | H1 at the aggressive operating point |
| 2 | rope_gain_comp | MODE=1, W=14 | H1 at the recommended point |
| 3 | rope_gain_comp | MODE=2, W=12 | H2, accuracy/area trade |
| 4 | rope_gain_comp | MODE=2, W=14 | H2 |

## Priority 2 — blocks the paper can no longer claim without (T2.1, T2.10)

Both are new RTL, both verified in iverilog, both referenced by the drafted
Sections III and IV. `rope_bfp_norm.v` contains **two** modules — synthesise
each by changing `set DESIGN`.

| # | design | params | why |
|---|---|---|---|
| 5 | rope_angle_encoder | N=10, FB=12 | cost currently unaccounted for in every comparison |
| 6 | rope_range_reduce | PW=16, FB=12 | mandatory; closes R4-3 |
| 7 | rope_bfp_norm | W=12, D=64, EW=6 | S-14 made this functional, not optional |
| 8 | rope_bfp_norm | W=14, D=64, EW=6 | at the recommended operating point |
| 9 | rope_bfp_denorm | W=14, D=64, EW=6 | the return path |

Blocks 5–9 are combinational, so expect them constrained against
`set_max_delay 2.0` rather than a clock. Area is what matters, plus whether
they fit the 2 ns budget alongside a rotator stage. **Report their area per
lane** (divide by D=64 for 7–9) — shared across the block is the whole point.

## Priority 3 — the comparison table (runs 10-11 are CRITICAL PATH, see above)

The paper's area claims were built at W=11. The measured requirement is
**F=11–12, i.e. W=13–14**, and there is no multiplier or LUT data at W=12 at
all, so the headline comparison cannot currently be made where the accuracy
data supports it.

| # | design | W | status |
|---|---|---|---|
| **10** | **rope_mult_pair** | **12** | **missing — CRITICAL PATH, tests the crossover** |
| **11** | **rope_lut_pair** | **12** | **missing — CRITICAL PATH, tests the crossover** |
| 12 | rope_cordic_pair (std, N=10) | 12 | missing |
| 13 | rope_cordic_pair (std, N=10) | 14 | missing |
| 14 | rope_binary_ud_pair (N=10) | 12 | missing |
| 15 | **rope_binary_ud_pair (N=10)** | **14** | **missing — fills the `<<TBD>>` in `performance.tex`** |
| — | rope_csd_pair (N=5) | 12, 14 | have 2942 / 3467 |
| — | rope_mult_pair / rope_lut_pair | 14 | have 4185 / 5375 |

## Priority 4 — optional, only if time allows

| # | design | params | why |
|---|---|---|---|
| 16 | rope_bfp_norm | W=14, D=8 | granularity sweep (T2.11), feeds C2 |
| 17 | rope_bfp_norm | W=14, D=16 | granularity sweep |

---

## If time is short

**Runs 1, 2, 10, 11, 5, 6, 7, 8, 15 — in that order.** The first four settle
both open decisions; 5-8 price the two mandatory new blocks; 15 fills the one
outstanding `<<TBD>>` in the performance table.

---

## Non-synthesis work outstanding

| item | what |
|---|---|
| T1.6 | Self-checking testbenches for the four `rope_*_pair` modules. The encoder, gain-comp and BFP blocks have them; the rotator pairs do not. Needed for the reproducibility claim R4-2 asks for. |
| T2.4 | Polynomial baseline RTL + synthesis (optional). R2 and R4 both named it. If skipped, `related_work.tex` still needs a real citation for the `\todocite{poly}`. |
| T2.3 | RoPE as a percentage of an ITA-class attention block — analysis, no tools needed. |
| T2.11 | Block-granularity accuracy sweep in the Python model, to pair with runs 16–17. |
| T5.1–5.5 | Push new RTL, scripts, results CSV; write a real README; scrub git history before pointing a paper at the repo. |
| — | Resolve `\todocite{poly}` and the prior-work rows in `tab:baselines` (numbers must come from the cited papers, normalised to 45 nm with the method stated). |

---

## Added 2026-10-16 — deadline moved to 22 Oct

### Runs 18–23: W=13, the recommended operating point

`tab:perf` currently shows W=12 and W=14 and concedes that the recommended
W=13 "lies between the two word lengths shown". A reviewer can reasonably ask
why the paper's own recommendation is the one point it does not measure.
Six runs close that.

```
./SCRIPTS/run_all_synth.sh 18 19 20 21 22 23
python3 SCRIPTS/collect_results.py build
```

| # | design | params | fills |
|---|---|---|---|
| 18 | rope_gain_comp | W=13 MODE=1 | H1 block for the merged row |
| 19 | rope_mult_pair | W=13 | multiplier row |
| 20 | rope_lut_pair | W=13 ADDR_W=7 | sin/cos LUT row |
| 21 | rope_cordic_pair | W=13 STAGES=10 | standard CORDIC row |
| 22 | rope_binary_ud_pair | W=13 STAGES=10 | **Binary UD row** |
| 23 | rope_csd_pair | WIDTH=13 STAGES=5 | merged datapath |

Merged UD row = run 23 area + run 18 area, as at the other two widths.

**`rope_csd_pair` parameterises on `WIDTH`, not `W`.** Every other design in
this file uses `W`. Passing `W=13` to it leaves WIDTH at its default of 9 and
the run completes, silently, at the wrong width.

### Runs 24–25: merged UD at W=12 and W=14 under this driver

The merged datapath areas in `tab:perf` (2942 at W=12, 3467 at W=14) come from
the earlier `RUN/csd_ud` campaign, not from `run_all_synth.sh`. Same library
and corner, so the numbers stand, but the paper says every design ran "the
same flow" and these two did not run *this* script. Cheap to remove the
discrepancy:

```
./SCRIPTS/run_all_synth.sh 24 25
```

Expect ~2942 and ~3467 µm². A material difference means the two campaigns
were not as identical as assumed, which matters more than the rerun cost.

### Optional: a second corner

`synth_generic.tcl` now reads `SYN_CORNER` (default `fast_vdd1v2`, so existing
results reproduce exactly). The fast corner at 1.32 V / 0 °C is the most
attackable choice in the evaluation. Repeating the five W=13 designs at the
nominal or slow corner would answer that directly:

```
ls $SYN_LIBBASE/gsclib045/timing/*.lib          # see which corners exist
SYN_CORNER=slow_vdd1v2 ./SCRIPTS/run_all_synth.sh 18 19 20 21 22 23
```

Build directories are named by run id, so run these into a separate tree or
rename `build/` first, or the fast-corner results are overwritten.
