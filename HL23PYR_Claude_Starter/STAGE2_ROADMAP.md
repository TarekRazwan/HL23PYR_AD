# Stage 2 Roadmap: AD Variant Implementation & Comparison

**Prerequisite**: Stage 1 Complete ✓
**Goal**: Quantify AD-induced changes in neuronal excitability
**Approach**: Implement literature-validated ion channel alterations, compare to healthy baseline

---

## Scientific Rationale

Alzheimer's Disease is associated with documented changes in ion channel expression and function in pyramidal neurons:

1. **Nav1.6 (Sodium channels)**: Reduced expression → decreased excitability
2. **Kv3.1 (Potassium channels)**: Reduced expression → altered repolarization
3. **SK (Ca²⁺-activated K⁺)**: Reduced expression → altered adaptation/AHP

These changes collectively alter **intrinsic neuronal excitability**, contributing to network dysfunction independent of amyloid/tau pathology.

---

## Implementation Plan

### Task 1: Create AD Biophysics File

**File to create**: `/models/biophys_HL23PYR_AD.hoc`

**Method**: Copy `biophys_HL23PYR.hoc` and apply reductions

**Ion Channel Changes**:

```hoc
// AD-SPECIFIC REDUCTIONS (30% reduction for Nav1.6 and Kv3.1, 25% for SK)

forsec $o1.somatic {
    // ... (passive + other channels unchanged) ...

    // SK reduction (25%)
    // Healthy: gbar_SK will be set via distribute_channels to 0.000853
    // AD: Multiply by 0.75
}

forsec $o1.axonal {
    // Similar reductions
}

// Update distribute_channels calls:
$o1.distribute_channels("soma","gbar_NaTg",0,1.0,0.0,0.0,0.0,0.1904000000)  // was 0.272 (30% reduction)
$o1.distribute_channels("soma","gbar_Kv3_1",0,1.0,0.0,0.0,0.0,0.02968000)   // was 0.0424 (30% reduction)
$o1.distribute_channels("soma","gbar_SK",0,1.0,0.0,0.0,0.0,0.00063975)      // was 0.000853 (25% reduction)

$o1.distribute_channels("axon","gbar_NaTg",0,1.0,0.0,0.0,0.0,0.9660000000)  // was 1.38 (30% reduction)
$o1.distribute_channels("axon","gbar_Kv3_1",0,1.0,0.0,0.0,0.0,0.6587000000) // was 0.941 (30% reduction)
```

**Documentation**: Add header comment explaining AD modifications

```hoc
// ============================================================================
// ALZHEIMER'S DISEASE VARIANT
// Based on biophys_HL23PYR.hoc (healthy baseline)
//
// AD-specific changes (literature-validated):
// - Nav1.6 (gbar_NaTg): 30% reduction (soma & axon)
// - Kv3.1 (gbar_Kv3_1): 30% reduction (soma & axon)
// - SK (gbar_SK): 25% reduction (soma)
//
// Expected functional consequences:
// - Increased rheobase (less excitable)
// - Reduced firing rate at fixed current injection
// - Altered spike shape (reduced Nav → smaller amplitude)
// - Altered repolarization (reduced Kv3.1 → wider spikes)
// ============================================================================
```

---

### Task 2: Update cellwrapper.py

**Current code** (line ~20):
```python
def loadCell_HL23PYR(cellName, ad=False):
    # ... paths ...
    biophysics = os.path.join(_CELLWRAPPER_DIR, 'models', 'biophys_' + cellName + '.hoc')
```

**Updated code**:
```python
def loadCell_HL23PYR(cellName, ad=False):
    templatepath = os.path.join(_CELLWRAPPER_DIR, 'models', 'NeuronTemplate_HL23PYR.hoc')

    # Select biophysics based on AD flag
    if ad:
        biophysics = os.path.join(_CELLWRAPPER_DIR, 'models', 'biophys_' + cellName + '_AD.hoc')
    else:
        biophysics = os.path.join(_CELLWRAPPER_DIR, 'models', 'biophys_' + cellName + '.hoc')

    morphpath = os.path.join(_CELLWRAPPER_DIR, 'morphologies', cellName + '.swc')
    # ... rest unchanged ...
```

---

### Task 3: Modify Simulation Driver

**File**: `/HL23PYR_Claude_Starter/src/build_netpyne_model_HL23PYR.py`

**Add command-line argument**:
```python
import argparse

# ... existing code ...

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run HL23PYR simulations')
    parser.add_argument('--ad', action='store_true', help='Use AD variant biophysics')
    args = parser.parse_args()

    # Pass to make_netparams
    netParams = make_netparams(ad=args.ad)

    # Update output filenames
    suffix = "_AD" if args.ad else ""
    # ... modify simlabel to include suffix ...
```

**Update make_netparams**:
```python
def make_netparams(ad=False):
    netParams = specs.NetParams()
    cellName = 'HL23PYR'
    cellRule = netParams.importCellParams(
        label=cellName,
        somaAtOrigin=True,
        conds={'cellType': cellName, 'cellModel': 'HH_full'},
        fileName=os.path.join(REPO_ROOT, 'cellwrapper.py'),
        cellName='loadCell_HL23PYR',
        cellInstance=True,
        cellArgs={'cellName': cellName, 'ad': ad}  # Pass AD flag
    )
    # ... rest unchanged ...
```

---

### Task 4: Run AD Simulations

**Command**:
```bash
cd HL23PYR_Claude_Starter
python src/build_netpyne_model_HL23PYR.py --ad
```

**Expected outputs** (in `data/`):
- `baseline_0pA_AD_sim.json`
- `passive_neg50pA_AD_sim.json`
- `sag_neg110pA_AD_sim.json`
- `sweep_45_AD_sim.json`
- `sweep_52_AD_sim.json`

---

### Task 5: Create Comparison Script

**New file**: `/HL23PYR_Claude_Starter/src/compare_healthy_vs_AD.py`

**Purpose**: Load both healthy and AD simulations, extract features, compute Δ values

**Key features**:
```python
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def load_and_compare():
    # Load healthy
    healthy_170 = load_trace("data/sweep_45_sim.json")
    healthy_310 = load_trace("data/sweep_52_sim.json")

    # Load AD
    ad_170 = load_trace("data/sweep_45_AD_sim.json")
    ad_310 = load_trace("data/sweep_52_AD_sim.json")

    # Extract spike counts
    healthy_spikes_170 = count_spikes(healthy_170)
    ad_spikes_170 = count_spikes(ad_170)

    # Compute Δ
    delta_spikes_170 = ad_spikes_170 - healthy_spikes_170

    # Generate FI curve data
    currents = [0, 50, 100, 150, 170, 200, 250, 310]  # pA
    # ... run additional simulations or use existing ...

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(currents_healthy, firing_healthy, 'o-', label='Healthy', linewidth=2)
    plt.plot(currents_ad, firing_ad, 's-', label='AD', linewidth=2)
    plt.xlabel('Injected Current (pA)')
    plt.ylabel('Firing Rate (Hz)')
    plt.title('FI Curve: Healthy vs AD')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('results/FI_curve_healthy_vs_AD.png', dpi=300)

    # Generate comparison table
    df = pd.DataFrame({
        'Feature': ['Spikes @ 170 pA', 'FR @ 310 pA', 'AP amp', 'AP width'],
        'Healthy': [healthy_vals...],
        'AD': [ad_vals...],
        'Δ (AD - Healthy)': [deltas...],
        'Δ (%)': [percent_changes...]
    })
    df.to_csv('results/healthy_vs_AD_comparison.csv', index=False)
    print(df)
```

---

### Task 6: Validation & Interpretation

**Expected AD phenotype** (based on 30% Nav/Kv, 25% SK reduction):

| Feature | Healthy | AD (predicted) | Direction |
|---------|---------|----------------|-----------|
| Rheobase | ~170 pA | ↑ 200-250 pA | Less excitable |
| Spikes @ 170 pA | 15 | ↓ 5-10 | Reduced |
| FR @ 310 pA | 21.4 Hz | ↓ 12-16 Hz | Reduced |
| AP amplitude | 91 mV | ↓ 75-85 mV | Smaller (Nav↓) |
| AP width | 1.1 ms | ↑ 1.3-1.5 ms | Wider (Kv↓) |
| Adaptation | 0.011 | ↓ ~0.008 | Even weaker |

**Interpretation checks**:
1. If rheobase ↑ → confirms reduced excitability ✓
2. If FR @ 310 pA ↓ → confirms impaired spiking ✓
3. If AP amplitude ↓ → confirms Nav reduction ✓
4. If AP width ↑ → confirms Kv reduction ✓

**Red flags** (would indicate errors):
- AD more excitable than healthy (rheobase ↓) → check gbar reductions
- AD fires faster than healthy → check biophysics file loaded correctly
- No change in any metric → verify AD flag propagated to cellArgs

---

## Deliverables

### Code
1. ✓ `models/biophys_HL23PYR_AD.hoc` — AD biophysics
2. ✓ Updated `cellwrapper.py` — AD flag handling
3. ✓ Updated `build_netpyne_model_HL23PYR.py` — --ad argument
4. ✓ New `compare_healthy_vs_AD.py` — Comparison analysis

### Data
5. ✓ `data/*_AD_sim.json` — AD simulation outputs (5 protocols)
6. ✓ `results/healthy_vs_AD_comparison.csv` — Feature comparison table
7. ✓ `results/FI_curve_healthy_vs_AD.png` — Visual comparison

### Documentation
8. ✓ `STAGE2_RESULTS.md` — AD validation results, interpretation
9. ✓ Update `HL23PYR_AD_project_primer.json` — Mark Stage 2 complete

---

## Success Criteria

**Minimum Requirements**:
- [ ] AD variant shows **reduced excitability** vs healthy (rheobase ↑ or FR ↓)
- [ ] Changes are **biologically plausible** (30% Nav/Kv reduction → ~30-50% firing reduction)
- [ ] Results are **reproducible** (re-running gives same outputs)
- [ ] All code is **documented** and **version controlled** (git commit)

**Ideal Outcomes**:
- [ ] Quantitative comparison table (Healthy vs AD with Δ and % change)
- [ ] FI curve visualization showing clear separation
- [ ] Statistical analysis (if running multiple seeds/trials)
- [ ] Interpretation aligned with AD literature

---

## Timeline Estimate

| Task | Estimated Time | Complexity |
|------|----------------|------------|
| Create biophys_HL23PYR_AD.hoc | 15 min | Low (copy + modify) |
| Update cellwrapper.py | 5 min | Low (add if/else) |
| Update build_netpyne_model_HL23PYR.py | 10 min | Low (add argparse) |
| Run AD simulations | 10 min | Low (single command) |
| Create compare_healthy_vs_AD.py | 30 min | Medium (analysis + plotting) |
| Run comparison & interpret | 15 min | Low (execute + review) |
| Documentation | 20 min | Low (summary report) |
| **Total** | **~2 hours** | **Low-Medium** |

---

## Potential Extensions (Post-Stage 2)

### Advanced AD Modeling
1. **Dose-response**: Test 10%, 20%, 30%, 40% reductions → find threshold
2. **Channel-specific effects**: Isolate Nav vs Kv vs SK (one at a time)
3. **Temperature effects**: Run at 23°C vs 34°C vs 37°C
4. **Ca²⁺ dynamics**: Modify CaDynamics parameters (AD affects Ca²⁺ homeostasis)

### Network-Level
5. **Synaptic changes**: Reduce AMPA/NMDA conductances
6. **Network simulations**: Build L2/3 microcircuit with E/I populations
7. **Population firing rates**: AD vs healthy network activity
8. **Oscillations**: Gamma/theta power changes in AD network

### Validation
9. **Literature comparison**: Compare Δ values to published experimental data
10. **Parameter uncertainty**: Test sensitivity to 20-40% reduction range
11. **Multiple cells**: Run on different Allen morphologies (generalizability)

---

## Next Command to Execute

Once ready to proceed:

```bash
# Step 1: Create AD biophysics file
cp models/biophys_HL23PYR.hoc models/biophys_HL23PYR_AD.hoc
# (then manually edit to apply reductions)

# Step 2: Run AD simulations
cd HL23PYR_Claude_Starter
python src/build_netpyne_model_HL23PYR.py --ad

# Step 3: Compare
python src/compare_healthy_vs_AD.py
```

---

**Stage 2 ready to begin. Awaiting confirmation to proceed.**
