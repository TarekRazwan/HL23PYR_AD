# HL23PYR Stage 1 — Iterations 1-3 Final Summary & Recommendation

**Date:** 2025-11-01
**Status:** ❌ Passive tuning unsuccessful via current approach

---

## Summary of All Iterations

| Iteration | Changes | Resting Vm | Δ from Target | Firing @ 170 pA | Firing @ 310 pA |
|-----------|---------|------------|---------------|-----------------|-----------------|
| **Baseline** | None | −73.61 mV | +2.2 mV | 14 spikes, 15 Hz | 20 spikes, 21 Hz ✓ |
| **1** | Eh: −45→−37 mV<br>g_pas: 0.0000954→0.0000562 | −70.40 mV | **+5.4 mV** | 17 spikes, 16 Hz | 23 spikes, 23 Hz |
| **2** | + soma Ih: 0.000148→0.0001 | −67.95 mV | **+7.9 mV** | 17 spikes, 14 Hz | 23 spikes, 19 Hz |
| **Target** | - | −75.8 mV | 0 mV | Near threshold | ~20 Hz |

**Direction:** ❌ Each iteration made resting Vm **MORE depolarized**

---

## Root Cause: Apical Ih Gradient Dominates

The problem is **NOT** somatic Ih. The problem is the **apical dendritic Ih gradient**, which reaches very high values distally (up to ~0.015 S/cm² in apic_20-28).

When we reduced g_pas (to fix τ), we weakened the leak conductance that was "fighting" against this strong apical Ih. The apical Ih then dominated, pulling the cell toward Eh (−37 mV) despite our efforts.

**Reducing somatic Ih had minimal effect** because:
- Somatic Ih gbar = 0.0001 S/cm²
- Apical Ih gbar (distal) = ~0.015 S/cm² (**150× stronger**)
- The apical tree has much larger surface area than soma

---

## Recommended Fix: Revert to Near-Baseline Parameters

### Option A (SIMPLEST — Recommended)

**Revert all changes except Eh:**
1. Set g_pas = **0.0000954** (original)
2. Keep Eh = **−37 mV** (improved from −45 mV)
3. Set soma Ih gbar = **0.000148** (original)

**Expected outcome:**
- Resting Vm: ~−74.5 mV (within ±2 mV of target ✓)
- τ: ~10.5 ms (sub-optimal but acceptable)
- Rheobase: closer to 170 pA
- FI @ 310 pA: ~21 Hz ✓

**Rationale:**
- The Eh fix alone should hyperpolarize Vm by ~1 mV
- This gets us close enough to the target
- We accept a slightly fast τ as a trade-off
- All other features should fall into place

---

### Option B (More Complex)

**Keep τ fix, reduce apical Ih:**
1. Keep g_pas = 0.0000562
2. Keep Eh = −37 mV
3. Revert soma Ih gbar = 0.000148
4. **Reduce apical Ih gradient scaling factor** in line 37 of biophys_HL23PYR.hoc:
   ```hoc
   $o1.distribute_channels("apic","gbar_Ih",2,-0.8696,3.6161,0.0,2.0870,$o1.soma.gbar_Ih)
   ```
   Change the last parameter (soma.gbar_Ih scaling) from 2.087 to **1.5** (−28%)

**Expected outcome:**
- Resting Vm: ~−75 mV ✓
- τ: ~17.8 ms ✓
- Sag ratio: may decrease (needs validation)
- Rheobase: closer to 170 pA

**Risk:** May reduce sag ratio below acceptable range (0.10–0.20)

---

## Detailed Parameter Changes for Option A

### File: [mod/Ih.mod](../mod/Ih.mod)
```mod
ehcn = -37.0 (mV)  // KEEP THIS
```

### File: [models/biophys_HL23PYR.hoc](../models/biophys_HL23PYR.hoc)
```hoc
// Line 8: REVERT g_pas
g_pas = 0.0000954

// Line 27: REVERT soma Ih
gbar_Ih = 0.000148
```

---

## Shell Commands for Option A

```bash
cd /Users/tarek/Desktop/HL23PYR_AD-main

# 1. Edit biophys_HL23PYR.hoc line 8
#    Change: g_pas = 0.0000562 → 0.0000954

# 2. Edit biophys_HL23PYR.hoc line 27
#    Change: gbar_Ih = 0.0001 → 0.000148

# 3. No need to recompile (only .hoc changed, Eh already correct in compiled dll)

# 4. Re-run simulations
cd HL23PYR_Claude_Starter
python src/build_netpyne_model_HL23PYR.py

# 5. Validate
python src/run_validation_HL23PYR.py
```

---

## Key Lessons Learned

1. **Passive parameter coupling is complex:**
   - g_pas affects both τ (via Rm) and resting Vm (via leak strength)
   - Can't optimize both independently without considering Ih

2. **Ih spatial distribution matters:**
   - Apical Ih gradient dominates over somatic Ih
   - Must consider total membrane area × gbar, not just gbar alone

3. **Parameter order matters:**
   - Should have tested Eh fix ALONE before changing g_pas
   - Then could have seen that Eh fix alone might have been sufficient

4. **When to stop:**
   - Resting Vm within ±2 mV is acceptable
   - Don't over-optimize at the expense of other features (FI slope, etc.)

---

## Next Steps After Applying Option A

1. **Run simulations and check:**
   - Resting Vm (expect ~−74.5 mV)
   - Rheobase (expect closer to 170 pA)
   - FI @ 310 pA (expect ~21 Hz, maintain)

2. **If Vm is within ±2 mV of target:**
   - Proceed to Stage 2 spontaneous firing diagnosis
   - Document all parameter values in a final config file

3. **If Vm is still > +2 mV off:**
   - Try Option B (reduce apical Ih gradient)
   - OR accept current state and document as "best achievable with current model"

---

## Files to Preserve

Before making changes, save current state:
```bash
cp models/biophys_HL23PYR.hoc models/biophys_HL23PYR_iter3.hoc
cp mod/Ih.mod mod/Ih_iter3.mod
```

---

**End of Iterations Summary**
