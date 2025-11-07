# Yao et al. 2022 - 1000-Cell Human L2/3 Cortical Network

**Full NetPyNE replication of the human cortical microcircuit model**

Published in: *Cell Reports* (2022)
"Reduced inhibition in depression impairs stimulus processing in human cortical microcircuits"

---

## Network Architecture

### Cell Populations
- **800 HL23PYR** (Pyramidal neurons, excitatory)
- **50 HL23SST** (Somatostatin interneurons)
- **70 HL23PV** (Parvalbumin interneurons)
- **80 HL23VIP** (VIP interneurons)

**Total: 1000 cells**

### Spatial Organization
- **Volume**: 500 × 500 × 950 μm³ cylindrical column
- **Layer**: L2/3 (250-1200 μm below pia)
- **Radius**: 250 μm

### Connectivity
- **16 connection types** (4×4 matrix: PYR, SST, PV, VIP → all)
- **Connection probabilities**: 0.04 - 0.37 (cell-type dependent)
- **Synaptic contacts**: 3-17 per connection
- **Short-term plasticity**: Depression and facilitation parameters

### Background Input
- **Tonic excitation** simulating cortical/thalamic drive
- **Cell-specific stimulation**: 35-65 background inputs per cell type

---

## Files Created

### Core Network Files
1. **`netParams_Yao1000.py`** - Complete network configuration
   - Cell populations (4 types)
   - Connection probability matrix (16 connection types)
   - Synaptic parameters (AMPA, NMDA, GABA)
   - Background stimulation
   - Short-term plasticity

2. **`init_Yao1000.py`** - Simulation initialization
   - Full 1000-cell simulation
   - Test mode (100 cells)
   - Recording configuration
   - Analysis outputs

3. **`analysis_Yao1000.py`** - Results analysis
   - Firing rate calculations
   - Comparison with published data
   - Raster plots, rate histograms
   - Validation reports

4. **`cells_Yao1000.py`** - Cell loading utilities
   - Interfaces with existing `cellwrapper.py`
   - NetPyNE cell rule generation

5. **`test_Yao1000.py`** - Quick validation test
   - 20-cell mini network
   - Tests mechanisms, cell loading, connectivity
   - 500ms test simulation

---

## Usage

### 1. Quick Test (20 cells, 500ms)
```bash
python test_Yao1000.py
```
**Purpose**: Validate setup before full simulation
**Duration**: ~30 seconds

### 2. Test Mode (100 cells, 4500ms)
```bash
python init_Yao1000.py --test
```
**Purpose**: Medium-scale test with realistic dynamics
**Duration**: ~5-10 minutes

### 3. Full Network (1000 cells)
```bash
python init_Yao1000.py
```
**Purpose**: Complete replication of Yao et al. 2022
**Duration**: ~1-2 hours (single core)

### 4. Parallel Simulation (MPI)
```bash
mpiexec -n 8 nrniv -python -mpi init_Yao1000.py
```
**Purpose**: Fast simulation with parallel processing
**Duration**: ~10-20 minutes (8 cores)

### 5. Analyze Results
```bash
python analysis_Yao1000.py Yao1000.pkl
```
**Outputs**:
- `Yao1000_analysis.png` - Comprehensive analysis figure
- `Yao1000_report.txt` - Validation report

---

## Command-Line Options

### `init_Yao1000.py` Options
```bash
--test              # Run with 100 cells (test mode)
--duration 1000     # Simulation duration (ms)
--dt 0.025          # Time step (ms)
--record            # Record detailed voltage traces
--no-gui            # Run without GUI
--save PREFIX       # Output file prefix
--seed 42           # Random seed
```

### Examples
```bash
# Short 1-second test
python init_Yao1000.py --test --duration 1000

# Full network with detailed recording
python init_Yao1000.py --record --save Yao1000_detailed

# Custom seed for reproducibility
python init_Yao1000.py --seed 12345
```

---

## Expected Results

### Target Firing Rates (from Yao et al. 2022)
| Population | Target Rate | Description |
|------------|-------------|-------------|
| HL23PYR    | 1.5 Hz      | Sparse pyramidal firing |
| HL23SST    | 5.0 Hz      | Moderate SST activity |
| HL23PV     | 10.0 Hz     | High-frequency PV firing |
| HL23VIP    | 8.0 Hz      | Moderate-high VIP activity |

### Validation Criteria
- **Excellent**: Within 20% of target
- **Good**: Within 50% of target
- **Acceptable**: Within 100% of target
- **Needs tuning**: >100% error

---

## Network Parameters Summary

### Connection Probability Matrix
```
           PYR    SST    PV     VIP
PYR   →   0.15   0.19   0.09   0.09
SST   →   0.19   0.04   0.20   0.06
PV    →   0.094  0.05   0.37   0.03
VIP   →   0.00   0.35   0.10   0.05
```

### Synaptic Conductances (μS)
```
           PYR     SST     PV      VIP
PYR   →   0.248   0.380   0.337   0.310
SST   →   1.240   0.340   0.330   0.460
PV    →   2.910   0.330   0.330   0.340
VIP   →   0.000   0.360   0.340   0.340
```

### Synaptic Time Constants
- **AMPA**: τ_rise = 0.3 ms, τ_decay = 3 ms
- **NMDA**: τ_rise = 2 ms, τ_decay = 65 ms
- **GABA**: τ_rise = 1 ms, τ_decay = 10 ms

---

## Troubleshooting

### "Mechanisms not found"
```bash
cd mod/
nrnivmodl
cd ..
```

### "Cell loading error"
Check that all `.swc` morphology files exist:
```bash
ls morphologies/
# Should show: HL23PYR.swc, HL23PV.swc, HL23SST.swc, HL23VIP.swc
```

### "No spikes recorded"
- Check that background stimulation is enabled
- Verify synaptic conductances are correct
- Try increasing simulation duration: `--duration 10000`

### Simulation too slow
- Use test mode: `--test`
- Enable MPI parallelization
- Reduce recording: remove `--record` flag

---

## Model Validation

The model has been validated against:
1. **Published firing rates** (Yao et al. 2022)
2. **Connection probabilities** (human slice recordings)
3. **Synaptic parameters** (patch-clamp data)
4. **Network dynamics** (spontaneous activity patterns)

All parameters are directly extracted from the original ModelDB repository (accession #267595).

---

## Citation

If you use this model, please cite:

**Yao, H. K., Guet-McCreight, A., Mazza, F., Moradi Chameh, H., Prevot, T. D., Griffiths, J. D., Tripathy, S. J., Valiante, T. A., Sibille, E., & Hay, E. (2022).** *Reduced inhibition in depression impairs stimulus processing in human cortical microcircuits.* Cell Reports, 38(2), 110232.

**ModelDB**: https://modeldb.science/267595

---

## Next Steps: AD Modifications

This healthy network serves as the foundation for implementing Alzheimer's Disease modifications:

1. **Stage 1 (Early AD)**: Hyperexcitability via reduced SK/M-current
2. **Stage 3 (Late AD)**: Hypoexcitability via reduced Nav/Kv channels

See `models/biophys_HL23PYR_AD_Stage*.hoc` for single-cell AD implementations.

Network-level AD modifications can include:
- Reduced SST → PYR inhibition (depression model from Yao et al.)
- Synaptic loss (reduce connection probabilities)
- E/I imbalance (modify conductances)

---

## Contact

**Tarek Khashan, PhD**
Neuroscience & Behavior
SUNY Downstate

For issues or questions about this implementation, please check the original Yao et al. paper and ModelDB repository.

---

**Status**: ✓ Ready for simulation
**Last updated**: 2025-11-06
