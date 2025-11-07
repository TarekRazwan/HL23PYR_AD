# AD Staging Framework: Evidence-Based Implementation

**Critical Correction**: The initial implementation modeled **hypoexcitability** (late-stage AD), but early AD is characterized by **hyperexcitability**. This document provides the corrected, staged approach.

---

## The "Storm Before the Quiet" Timeline

**Early AD (A+/T−/N−)**: Hyperexcitability, aberrant activity, seizure risk ↑
**Mid AD (A+/T+/N±)**: Mixed hyperexcitability + emerging hypoconnectivity
**Late AD (A+/T+/N+)**: Hypoactivity, synapse loss, network failure

---

## Stage 1: Preclinical Aβ+ Hyperexcitability (A+/T−/N−)

### Core Mechanisms

**Primary driver**: **Reduced inhibition** before major synapse loss
- PV-interneuron dysfunction → impaired gamma, E:I imbalance
- GABAergic clearance defects (↓GAT-1/3) → slower IPSC decay, spillover
- Neuronal hyperactivity clusters near plaques

### Single-Cell Implementation (HL23PYR)

Since we have a **single pyramidal neuron model** (no network), we implement hyperexcitability through:

#### Option A: Intrinsic Excitability Changes
```hoc
// biophys_HL23PYR_AD_Stage1.hoc

// 1. REDUCED SK (Ca²⁺-activated K⁺) → less adaptation, more sustained firing
//    Rationale: Early SK dysfunction allows "runaway" firing
gbar_SK (soma): 0.000853 → 0.000640 (-25%)  // ✓ Already implemented
gbar_SK (axon): 0.0145 → 0.010875 (-25%)    // ✓ Already implemented

// 2. SLIGHTLY INCREASED Nav1.6 (or unchanged) → NOT reduced
//    Rationale: Some studies show Nav hyperactivity, not hypoactivity in early AD
//    CORRECTION: Remove the 30% Nav reduction!
gbar_NaTg (soma): 0.272 → 0.272 (unchanged)  // ← FIX
gbar_NaTg (axon): 1.38 → 1.38 (unchanged)    // ← FIX

// 3. M-CURRENT (Kv7/KCNQ) REDUCTION → less spike frequency adaptation
//    Rationale: M-current reduction is a robust hyperexcitability mechanism
gbar_Im (soma): 0.000306 → 0.000230 (-25%)   // NEW

// 4. Kv3.1 UNCHANGED or slight reduction
//    Rationale: Kv3.1 dysfunction impairs fast-spiking in PV cells primarily
//    For PYR: keep or reduce slightly
gbar_Kv3_1 (soma): 0.0424 → 0.0382 (-10%)    // Modest reduction
```

#### Option B: Increased Background Drive (Network Compensation)
```python
# Add depolarizing background current to simulate:
# - Loss of tonic GABAergic inhibition
# - Increased glutamate spillover
# - Compensatory hyperactivity

# Add small depolarizing bias (0.01-0.02 nA = 10-20 pA)
netParams.stimSourceParams['BGDrive'] = {
    'type': 'IClamp',
    'delay': 0,
    'dur': 1200,
    'amp': 0.015  # 15 pA constant depolarization
}
```

### Expected Stage 1 Phenotype

| Feature | Healthy | Stage 1 (Early AD) | Direction |
|---------|---------|---------------------|-----------|
| **Resting Vm** | -73.1 mV | -70 to -72 mV | Slightly depolarized |
| **Rheobase** | ~170 pA | 140-160 pA | **↓ (more excitable)** |
| **Spikes @ 170 pA** | 15 | 18-22 | **↑ More spikes** |
| **Spikes @ 310 pA** | 21 | 25-30 | **↑ More spikes** |
| **Adaptation Index** | 0.011 | 0.005-0.008 | **↓ Less adaptation** |
| **Spontaneous @ 0 pA** | 0 | 0 (maybe 1-2) | Possible spontaneous |

**Key signature**: **Increased firing, reduced adaptation, lower rheobase**

---

## Stage 2: Early Symptomatic (MCI) (A+/T+/N±)

### Additional Mechanisms

**Synapse loss begins** (15-30% reduction in excitatory input)
**PV dysfunction worsens** (further reduce effective inhibition)
**SST vulnerability** (dendritic inhibition impaired)

### Single-Cell Implementation

```hoc
// From Stage 1 base, ADD:

// 1. Reduce excitatory drive to compensate for synapse loss
//    (In single-cell model: reduce injected current efficacy or add leak)
g_pas: 0.00008 → 0.00009 (+12.5%)  // Slightly more leak = less excitability

// 2. Further SK reduction
gbar_SK: 0.000640 → 0.000550 (-15% additional from Stage 1)

// 3. Begin Nav dysfunction (NOT full reduction yet)
gbar_NaTg: 0.272 → 0.245 (-10%)

// 4. Continue M-current reduction
gbar_Im: 0.000230 → 0.000200 (-13% additional)
```

### Expected Stage 2 Phenotype

**Mixed**: Some hyperexcitability remains, but beginning to fail under sustained input
- Firing rate @ 310 pA: 22-25 Hz (still elevated but less than Stage 1)
- Increased firing failures during long depolarizations
- Wider APs (beginning Kv dysfunction)

---

## Stage 3: Established Dementia (A+/T+/N+)

### Mechanisms

**Massive synapse loss** (30-50%)
**Nav/Kv dysfunction severe**
**Network hypoactivity**

### Single-Cell Implementation

```hoc
// This is what we ORIGINALLY implemented (by mistake)
gbar_NaTg: 0.272 → 0.190 (-30%)  // Now appropriate for LATE stage
gbar_Kv3_1: 0.0424 → 0.0297 (-30%)
gbar_SK: 0.000853 → 0.000640 (-25%)
```

### Expected Stage 3 Phenotype

**Hypoexcitability** (what we currently have):
- Firing @ 310 pA: 2-5 Hz (severe reduction)
- Wide APs, depolarization block risk
- This matches our current results!

---

## Corrected Implementation Strategy

### Immediate Action: Implement Stage 1 (Early AD Hyperexcitability)

**Create**: `biophys_HL23PYR_AD_Stage1.hoc`

**Changes from healthy baseline**:
1. ✓ **SK ↓25%** (keep current reduction)
2. ✗ **REMOVE Nav reduction** (was wrong!)
3. ✓ **M-current (Im) ↓25%** (new)
4. ✓ **Kv3.1 ↓10%** (reduce from 30% to 10%)
5. ± **Optional**: Add 10-15 pA background depolarizing current

**Expected outcome**: **Increased firing** compared to healthy (opposite of current results)

### Future: Implement Stage 3 (Late AD)

**Rename current AD model**: `biophys_HL23PYR_AD_Stage3.hoc`
- Keep Nav ↓30%, Kv ↓30%, SK ↓25%
- Relabel as "late-stage AD / neurodegeneration"
- Current results (90.5% firing reduction) are **correct for Stage 3**

---

## Literature Support

### Stage 1 Hyperexcitability

**Busche et al. (2008)**: Neuronal hyperactivity clusters near amyloid plaques
- Mechanism: Reduced inhibition (PV dysfunction, GABA clearance defects)
- Observation: 2-3× higher spontaneous Ca²⁺ transients

**Palop & Mucke (2016)**: Network abnormalities in AD
- Early: Aberrant hyperactivity, seizure susceptibility
- Late: Hypoactivity, synapse loss

**Kamenetz et al. (2003)**: Aβ increases neuronal activity
- Aβ oligomers → ↑ glutamate release, ↓ inhibition

### Ion Channel Changes

**SK channels**: Early dysfunction → reduced adaptation (Sun et al., 2018)
**M-current**: Reduction → hyperexcitability (Morse et al., 2019)
**Nav**: Mixed reports - some show hyperactivity (not reduction) in early stages
**Kv**: Dysfunction primarily in PV interneurons; PYR effects less clear early on

---

## Recommended Next Steps

1. **Create Stage 1 AD model** (hyperexcitability)
   - Remove Nav reduction
   - Keep SK reduction
   - Add M-current reduction
   - Reduce Kv3.1 reduction from 30% → 10%

2. **Run Stage 1 simulations**
   - Expect: ↑ firing @ 310 pA (25-30 Hz vs 21 Hz healthy)
   - Expect: ↓ rheobase (140-160 pA vs 170 pA healthy)

3. **Rename current model as Stage 3**
   - Current results (90.5% reduction) are appropriate for **late AD**

4. **Optional: Implement Stage 2** (mixed phenotype)

5. **Compare all three stages**:
   - Healthy baseline (21 Hz @ 310 pA)
   - Stage 1 Early AD (28-30 Hz @ 310 pA) ← HYPEREXCITABLE
   - Stage 3 Late AD (2 Hz @ 310 pA) ← HYPOEXCITABLE

This would demonstrate the **"storm before the quiet"** progression!

---

## Parameter Summary Table

| Channel | Healthy | Stage 1 (Early) | Stage 3 (Late) | Rationale |
|---------|---------|-----------------|----------------|-----------|
| **gbar_NaTg (soma)** | 0.272 | **0.272** | 0.190 | Nav: Unchanged early, ↓ late |
| **gbar_Kv3_1 (soma)** | 0.0424 | **0.0382** | 0.0297 | Kv: Mild ↓ early, severe late |
| **gbar_SK (soma)** | 0.000853 | **0.000640** | 0.000640 | SK: ↓ early (hyperexc) |
| **gbar_Im (soma)** | 0.000306 | **0.000230** | 0.000200 | M: ↓ early (hyperexc) |
| **Background drive** | 0 pA | **+10-15 pA** | 0 pA | Compensatory in early |

---

## Validation Targets (Stage 1)

**Must achieve**:
- ✓ Increased firing rate @ suprathreshold (25-30 Hz @ 310 pA)
- ✓ Reduced rheobase (140-160 pA)
- ✓ Reduced adaptation index (<0.008)
- ± Possible spontaneous firing @ 0 pA

**Red flags** (would indicate error):
- ✗ Decreased firing rate (that's Stage 3!)
- ✗ Increased rheobase (opposite of hyperexcitability)

---

**Action item**: Shall I implement the corrected Stage 1 (hyperexcitability) model now?
