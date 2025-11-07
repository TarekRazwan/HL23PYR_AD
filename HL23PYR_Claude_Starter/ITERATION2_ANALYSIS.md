# Iteration 2 Analysis — Unexpected Results

**Date:** 2025-11-01
**Changes Applied:**
1. ✅ Ih reversal (ehcn): −45 mV → −37 mV
2. ✅ g_pas: 0.0000954 → 0.0000562 S/cm²

---

## Critical Finding: Resting Vm Got WORSE

| Iteration | Resting Vm | Δ from Target | Firing @ 170 pA | Firing @ 310 pA |
|-----------|------------|---------------|-----------------|-----------------|
| **Baseline** | −73.61 mV | +2.2 mV | 14 spikes, 15 Hz | 20 spikes, 21 Hz ✓ |
| **Iter 2** | **−70.40 mV** | **+5.4 mV** | 17 spikes, 16 Hz | 23 spikes, 23 Hz |
| **Target** | −75.8 mV | 0 mV | Near threshold | 20 Hz |

**Direction:** ❌ **WORSE** — Vm became **3.2 mV MORE depolarized**

---

## Root Cause: Leak vs Ih Balance

### What Happened

Reducing g_pas had TWO competing effects:

1. **Intended effect:** Slower τ (more integration time)
2. **Unintended effect:** Weaker "pull" toward e_pas (−80 mV)

With weak leak conductance, **Ih now dominates the resting potential**. Even though we reduced Ih driving force (Eh: −45 → −37 mV), the reduction in leak conductance gave Ih more relative influence.

### The Math

**Current balance at rest:**
```
I_leak + I_h = 0  (no net current at steady state)
g_leak * (V_m - E_leak) + g_h * (V_m - E_h) = 0
```

Solving for V_m:
```
V_m = (g_leak * E_leak + g_h * E_h) / (g_leak + g_h)
```

**Iteration 1:**
- g_leak = 0.0000954
- E_leak = −80 mV
- E_h = −45 mV
- g_h ≈ small (various compartments)
- Result: V_m ≈ −73.6 mV (leak dominates slightly)

**Iteration 2:**
- g_leak = 0.0000562 (−41% reduction)
- E_leak = −80 mV
- E_h = −37 mV (+8 mV more hyperpolarized)
- g_h unchanged
- Result: V_m ≈ −70.4 mV (**Ih now dominates**)

The 41% reduction in g_leak gave Ih **much more relative weight**, overwhelming the 8 mV Eh shift.

---

## Revised Strategy

### Option A: Revert g_pas, Only Keep Eh Fix (Conservative)
- Set g_pas back to 0.0000954
- Keep Eh = −37 mV
- Accept τ ≈ 10.5 ms (sub-optimal but not critical)
- **Expected:** Vm ≈ −74.5 mV (closer to target)

### Option B: Reduce Somatic Ih gbar (Targeted)
- Keep g_pas = 0.0000562 (for correct τ)
- Keep Eh = −37 mV
- Reduce somatic Ih: gbar_Ih from 0.000148 → 0.0001 (−32%)
- **Expected:** Vm ≈ −75 mV, τ ≈ 17.8 ms ✓

### Option C: Adjust e_pas (Compensatory)
- Keep g_pas = 0.0000562
- Keep Eh = −37 mV
- Change e_pas: −80 mV → −77 mV (closer to target Vm)
- **Expected:** Vm ≈ −75 mV, but τ still correct

---

## Recommendation: Option B (Reduce Somatic Ih)

**Rationale:**
1. We want to keep the slower τ (17.8 ms target)
2. Reducing somatic Ih gbar will reduce depolarizing drive at rest
3. Apical Ih gradient can remain (needed for sag)
4. Most physiologically interpretable: "somatic Ih was too strong"

**Implementation:**
Edit [models/biophys_HL23PYR.hoc:27](../models/biophys_HL23PYR.hoc#L27):
```hoc
gbar_Ih = 0.0001  // was 0.000148
```

**Expected effects:**
- Resting Vm: −70.4 → ~−75 mV ✓
- τ: remains ~17.8 ms ✓
- Sag ratio: may decrease slightly (acceptable if still in 0.10–0.20 range)
- Rheobase: will increase toward 170 pA target ✓

---

## Alternative: If Sag Becomes Too Small

If reducing somatic Ih makes sag ratio drop below 0.10:
1. Slightly increase apical Ih scaling in the gradient
2. OR accept slightly larger somatic Ih (e.g., 0.00012 instead of 0.0001)

---

## Next Steps

1. **Apply Option B:** Reduce somatic Ih gbar to 0.0001
2. **Recompile:** Not needed (only .hoc changed)
3. **Re-run sims:** All 5 protocols
4. **Validate:** Check Vm, τ, Rin, sag, rheobase, FI slope
5. **If still off:** Fine-tune with smaller adjustments

---

**End of Iteration 2 Analysis**
