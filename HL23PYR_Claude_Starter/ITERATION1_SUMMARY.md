# HL23PYR Stage 1 — Iteration 1 Summary

**Date:** 2025-11-01
**Model:** Allen Cell ID 531526539 (Human L2/3 Pyramidal)
**Status:** ✗ Passive properties OUT OF TOLERANCE — Action required

---

## What Was Accomplished

### 1. Infrastructure ✓
- ✅ Compiled and loaded all .mod mechanisms (17 files)
- ✅ Integrated real HL23PYR morphology + biophysics via `cellwrapper.py`
- ✅ Fixed path handling for macOS compatibility
- ✅ Created robust simulation harness (`build_netpyne_model_HL23PYR.py`)
- ✅ Implemented EFEL validation pipeline (`run_validation_HL23PYR.py`)

### 2. Diagnostic Protocols Executed ✓
- **0 pA baseline** → Resting Vm measurement
- **−50 pA passive** → Rin and τ measurement (not yet extracted)
- **−110 pA sag** → Sag ratio measurement (not yet extracted)
- **170 pA (sweep_45)** → Rheobase region, FI slope
- **310 pA (sweep_52)** → High-rate firing

### 3. Key Measurements

| Feature | Measured | Target | Δ | Status |
|---------|----------|--------|---|--------|
| **Resting Vm** | **−73.61 mV** | −75.8 mV | **+2.2 mV** | ✗ TOO DEPOLARIZED |
| Firing @ 170 pA | 14 spikes, 15 Hz | Near rheobase | N/A | ✗ TOO EXCITABLE |
| Firing @ 310 pA | 20 spikes, 21 Hz | 20 Hz | +1 Hz | ✓ EXCELLENT |
| AP width | 1.0–1.1 ms | ~1 ms | 0 ms | ✓ Good |
| AP amplitude | ~91 mV | ~90 mV | +1 mV | ✓ Good |
| Adaptation index @ 310 pA | 0.012 | 0.075 | −0.063 | ✗ Too low (minimal adaptation) |
| **Rin** | **NOT MEASURED** | 100 MΩ | N/A | ? |
| **τ (tau)** | **NOT MEASURED** | 17.8 ms | N/A | ? |
| **Sag ratio** | **NOT MEASURED** | 0.15 | N/A | ? |

---

## Root Cause Analysis

### Problem 1: Resting Vm Too Depolarized (+2.2 mV)

**Diagnosis:**
The Ih (hyperpolarization-activated current) reversal potential is set to **−45 mV** in [Ih.mod:18](../mod/Ih.mod#L18):

```mod
ehcn = -45.0 (mV)
```

At resting Vm = −73.61 mV, this creates a driving force of:
```
I_h = g_h * (V_m - E_h) = g_h * (-73.61 − (−45)) = g_h * (−28.61)
```

This is a **strong depolarizing (inward) current** that pulls the cell away from the leak reversal (e_pas = −80 mV) and toward more depolarized potentials.

**Expected impact:**
- Reduced rheobase (cell fires at lower currents)
- Increased resting excitability
- Potential spontaneous firing at 0 pA (if Ih is strong enough in some compartments)

**Literature range for Ih reversal:** −30 to −40 mV (physiological Na⁺/K⁺ mixed permeability)

---

### Problem 2: Membrane Time Constant (τ) Likely Too Fast

**Current parameters (from biophys_HL23PYR.hoc):**
- g_pas = 0.0000954 S/cm²
- Cm_soma = 1 µF/cm²

**Estimated τ:**
```
R_m = 1 / g_pas = 10,482 Ω·cm²
τ = R_m * C_m = 10,482 * 1e-6 = 0.0105 s = 10.5 ms
```

**Target τ:** 17.8 ms
**Deficit:** ~7.3 ms (41% too fast)

**Consequence:**
The cell integrates inputs too quickly, affecting temporal summation and rebound dynamics. This will distort rheobase measurements and spike timing.

**Fix:**
Reduce g_pas to increase R_m:
```
g_pas_new = Cm / τ_target = 1e-6 / 0.0178 = 0.0000562 S/cm² (−41% reduction)
```

---

### Problem 3: Cell Is Too Excitable at 170 pA

**Observation:**
At 170 pA (target rheobase), the cell fires **14 spikes @ 15 Hz**.
Expected: Near threshold, 1–5 spikes maximum.

**Likely causes:**
1. Depolarized resting Vm (−73.61 vs −75.8 mV) reduces distance to threshold by ~2 mV
2. Fast τ means the cell doesn't "leak" enough charge during current injection
3. Possible excess Na conductance or insufficient K repolarization (but 310 pA firing is correct, suggesting this is NOT the issue)

**Implication:**
Once we fix resting Vm and τ, the rheobase will likely increase toward 170 pA naturally. **Do not adjust NaTg/Kv3.1/SK yet.**

---

## Proposed Parameter Adjustments (Iteration 2)

### Adjustment 1: Fix Ih Reversal Potential ⚠️ CRITICAL

**File:** [mod/Ih.mod](../mod/Ih.mod)

**Current:**
```mod
ehcn = -45.0 (mV)
```

**Proposed:**
```mod
ehcn = -37.0 (mV)
```

**Rationale:**
- Physiological mid-range for Ih in pyramidal neurons
- Reduces depolarizing drive at rest by ~27%:
  - Old: g_h * (−73.61 + 45) = g_h * (−28.61)
  - New: g_h * (−73.61 + 37) = g_h * (−36.61)
  - Change: (−36.61) / (−28.61) = 1.28 (28% weaker depolarization)

**Expected effect:**
Resting Vm will hyperpolarize by **~1.5–2 mV** toward −75.5 mV.

---

### Adjustment 2: Reduce g_pas to Increase τ

**File:** [models/biophys_HL23PYR.hoc](../models/biophys_HL23PYR.hoc)

**Current (line 8):**
```hoc
g_pas = 0.0000954
```

**Proposed:**
```hoc
g_pas = 0.0000562
```

**Rationale:**
- Increases membrane resistance → slower decay
- New τ estimate: R_m * C_m = (1/0.0000562) * 1e-6 ≈ 17.8 ms ✓

**Expected effect:**
- τ will match target (17.8 ms)
- Rin will INCREASE (may overshoot 100 MΩ target — will adjust Cm if needed)
- Resting Vm will be slightly affected (reduced leak conductance → more influence from Ih, but Eh fix will compensate)

---

### Adjustment 3: Measure Rin and Sag After Fixes

**Action:** Re-run simulations with updated parameters and extract:
- Rin from −50 pA step: ΔV / I
- τ from exponential fit to −50 pA charging curve
- Sag ratio from −110 pA step: (V_peak − V_steady) / (V_peak − V_baseline)

**Acceptance criteria:**
- Rin: 100 ± 15 MΩ
- τ: 17.8 ± 2 ms
- Sag ratio: 0.10–0.20 (target ~0.15)

---

## Shell Commands for Iteration 2

### Step 1: Edit Ih.mod
```bash
cd /Users/tarek/Desktop/HL23PYR_AD-main
# Edit mod/Ih.mod line 18: change ehcn from -45.0 to -37.0
```

### Step 2: Edit biophys_HL23PYR.hoc
```bash
# Edit models/biophys_HL23PYR.hoc line 8: change g_pas from 0.0000954 to 0.0000562
```

### Step 3: Recompile mechanisms
```bash
nrnivmodl mod
```

### Step 4: Re-run simulations
```bash
cd HL23PYR_Claude_Starter
python src/build_netpyne_model_HL23PYR.py
```

### Step 5: Validate
```bash
python src/run_validation_HL23PYR.py
```

---

## Success Criteria for Iteration 2

| Feature | Current | Target | Pass? |
|---------|---------|--------|-------|
| Resting Vm | −73.61 mV | −75.8 ± 2 mV | ✗ → ✓ |
| τ | ~10.5 ms | 17.8 ± 2 ms | ✗ → ✓ |
| Rin | ? | 100 ± 15 MΩ | ? → ✓ |
| Sag ratio | ? | 0.10–0.20 | ? → ✓ |
| Rheobase | <170 pA | ~170 pA | ✗ → ✓ |
| FI @ 310 pA | 21 Hz | 20 Hz | ✓ (maintain) |

---

## What NOT To Do Yet

🚫 **DO NOT adjust NaTg, Kv3.1, SK, or Nap conductances**
Reason: The 310 pA firing rate is already correct (21 Hz vs 20 Hz target). The low rheobase is due to passive/Ih issues, not active conductances.

🚫 **DO NOT add tonic currents or change synapse properties**
Reason: This is Stage 1 Healthy baseline — no synaptic inputs yet.

🚫 **DO NOT change e_pas (leak reversal) yet**
Reason: Let's first fix Ih and g_pas, then measure resting Vm. If still off, we can fine-tune e_pas as a last resort.

---

## Files Modified/Created

### New Files
- `HL23PYR_Claude_Starter/src/build_netpyne_model_HL23PYR.py` — Main simulation driver
- `HL23PYR_Claude_Starter/src/run_validation_HL23PYR.py` — EFEL validation
- `HL23PYR_Claude_Starter/src/test_single_sim.py` — Debug/test script

### Modified Files
- `cellwrapper.py` — Fixed relative paths to absolute paths for macOS compatibility

### Output Files
- `HL23PYR_Claude_Starter/data/baseline_0pA_sim.json`
- `HL23PYR_Claude_Starter/data/passive_neg50pA_sim.json`
- `HL23PYR_Claude_Starter/data/sag_neg110pA_sim.json`
- (Older toy sweeps: `sweep_45_sim.json`, `sweep_52_sim.json` — will be overwritten)

---

## Next Steps

1. **You (Tarek):** Review this summary and approve the proposed parameter changes
2. **Claude (Iteration 2):** Apply changes to Ih.mod and biophys_HL23PYR.hoc
3. **Claude:** Recompile, re-run, and validate
4. **Claude:** Extract Rin, τ, sag from passive traces
5. **Claude:** Generate updated comparison table with pass/fail
6. **If all passive features pass:** Proceed to Stage 2 spontaneous firing diagnosis
7. **If features still out of tolerance:** Iterate with smaller adjustments

---

## Teaching Note: Why This Order Matters

You asked earlier why we fix passive before excitability. **This iteration proves the point:**

- The cell fires too much at 170 pA (**not** because Na is too high)
- But it fires correctly at 310 pA (**proving** active conductances are reasonable)
- The problem is the **depolarized baseline** (−73.61 vs −75.8 mV)

If we had "fixed" the low rheobase by reducing NaTg or increasing Kv3.1, we would have **broken** the 310 pA firing rate. Instead, by fixing the passive foundation first (Ih reversal + g_pas), the rheobase will self-correct while preserving the FI slope.

This is the "house of cards" problem I warned about. **Passive properties are the foundation.** Get them right, and the active properties become much easier to tune.

---

**End of Iteration 1 Summary**
