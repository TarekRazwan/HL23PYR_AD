"""
Systematic Grid Search for Passive Properties
Explores g_pas × soma_Ih parameter space to find optimal fit to targets:
- Resting Vm: -75.8 mV
- Rin: 100 MΩ
- τ: 17.8 ms
"""
import os, sys, json
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from datetime import datetime

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)

from netpyne import specs, sim
from neuron import h

# Load mechanisms
dll_path = os.path.join(REPO_ROOT, "x86_64", "libnrnmech.dylib")
if os.path.exists(dll_path):
    h.nrn_load_dll(dll_path)
    print(f"[INFO] Loaded mechanisms from {dll_path}")
else:
    raise FileNotFoundError(f"Mechanisms not found: {dll_path}")

# Targets
TARGETS = {
    'vm': -75.8,      # mV
    'rin': 100.0,     # MΩ
    'tau': 17.8,      # ms
}

# Parameter grid (scientifically motivated ranges)
GPAS_RANGE = [0.00007, 0.00008, 0.00009, 0.0000954, 0.00010, 0.00011]  # 6 values
IH_SOMA_RANGE = [0.00008, 0.0001, 0.00012, 0.000148, 0.00018]  # 5 values
# Total: 6 × 5 = 30 simulations

def create_model(g_pas_val, ih_soma_val):
    """Create model with specified parameters"""
    netParams = specs.NetParams()

    # Import cell, but we'll override biophysics
    cellName = 'HL23PYR'
    cellRule = netParams.importCellParams(
        label=cellName,
        somaAtOrigin=True,
        conds={'cellType': cellName, 'cellModel': 'HH_full'},
        fileName=os.path.join(REPO_ROOT, 'cellwrapper.py'),
        cellName='loadCell_HL23PYR',
        cellInstance=True,
        cellArgs={'cellName': cellName, 'ad': False}
    )

    # Override passive parameters in all sections
    for secName in cellRule['secs']:
        if 'mechs' not in cellRule['secs'][secName]:
            cellRule['secs'][secName]['mechs'] = {}
        if 'pas' in cellRule['secs'][secName]['mechs']:
            cellRule['secs'][secName]['mechs']['pas']['g'] = g_pas_val

    # Override somatic Ih
    if 'soma_0' in cellRule['secs']:
        if 'Ih' in cellRule['secs']['soma_0']['mechs']:
            cellRule['secs']['soma_0']['mechs']['Ih']['gbar'] = ih_soma_val

    netParams.popParams['pyr'] = {
        'cellType': cellName,
        'cellModel': 'HH_full',
        'numCells': 1
    }

    return netParams

def run_passive_protocol(g_pas_val, ih_soma_val):
    """Run -50 pA protocol and extract features"""
    netParams = create_model(g_pas_val, ih_soma_val)

    cfg = specs.SimConfig()
    cfg.duration = 1200
    cfg.dt = 0.025
    cfg.hParams = {'celsius': 34, 'v_init': -80}
    cfg.verbose = False
    cfg.recordCells = [0]
    cfg.recordTraces = {'V_soma': {'sec': 'soma_0', 'loc': 0.5, 'var': 'v'}}
    cfg.recordStep = 0.1
    cfg.recordStim = True
    cfg.recordTime = True

    # -50 pA stimulus
    netParams.stimSourceParams['IClamp1'] = {
        'type': 'IClamp',
        'delay': 100,
        'dur': 1000,
        'amp': -0.05  # nA
    }
    netParams.stimTargetParams['IClamp1->pyr'] = {
        'source': 'IClamp1',
        'conds': {'pop': 'pyr'},
        'sec': 'soma_0',
        'loc': 0.5
    }

    # Run
    sim.createSimulate(netParams=netParams, simConfig=cfg, output=False)
    sim.gatherData()

    # Extract data
    t = np.array(sim.simData['t'])
    v = np.array(sim.simData['V_soma']['cell_0'])

    # Measure features
    features = measure_passive_features(t, v, stim_start=100, stim_end=1100, i_pA=-50)

    # Cleanup
    sim.clearAll()

    return features

def measure_passive_features(t, v, stim_start=100, stim_end=1100, i_pA=-50):
    """Extract Vm, Rin, tau from voltage trace"""
    # Baseline
    pre_idx = (t >= 50) & (t < stim_start)
    v_base = np.mean(v[pre_idx])

    # Steady-state
    ss_idx = (t >= stim_end - 200) & (t <= stim_end)
    v_ss = np.mean(v[ss_idx])

    # Rin
    delta_v = v_ss - v_base
    rin = abs(delta_v / (i_pA / 1000.0))

    # Tau (exponential fit)
    fit_idx = (t >= stim_start) & (t <= stim_start + 100)
    t_fit = t[fit_idx] - stim_start
    v_fit = v[fit_idx]

    def exp_model(t, tau):
        return v_ss + (v_base - v_ss) * np.exp(-t / tau)

    try:
        popt, _ = curve_fit(exp_model, t_fit, v_fit, p0=[15], bounds=(0.5, 50))
        tau = popt[0]
    except:
        tau = np.nan

    return {
        'vm': v_base,
        'rin': rin,
        'tau': tau,
        'v_ss': v_ss,
        'delta_v': delta_v
    }

def compute_error(features, targets):
    """Compute normalized composite error"""
    # Normalize each error by target value to make them comparable
    vm_error = (features['vm'] - targets['vm']) / abs(targets['vm'])
    rin_error = (features['rin'] - targets['rin']) / targets['rin']
    tau_error = (features['tau'] - targets['tau']) / targets['tau'] if not np.isnan(features['tau']) else 10.0

    # Composite error (Euclidean distance in normalized space)
    error = np.sqrt(vm_error**2 + rin_error**2 + tau_error**2)

    return error, {
        'vm_error': vm_error,
        'rin_error': rin_error,
        'tau_error': tau_error
    }

def main():
    print("="*80)
    print("SYSTEMATIC PASSIVE PARAMETER GRID SEARCH")
    print("="*80)
    print(f"g_pas range: {GPAS_RANGE}")
    print(f"Ih_soma range: {IH_SOMA_RANGE}")
    print(f"Total simulations: {len(GPAS_RANGE) * len(IH_SOMA_RANGE)}")
    print()

    results = []

    for i, g_pas in enumerate(GPAS_RANGE):
        for j, ih_soma in enumerate(IH_SOMA_RANGE):
            idx = i * len(IH_SOMA_RANGE) + j + 1
            total = len(GPAS_RANGE) * len(IH_SOMA_RANGE)

            print(f"[{idx}/{total}] g_pas={g_pas:.2e}, Ih_soma={ih_soma:.2e}...", end=" ")

            try:
                features = run_passive_protocol(g_pas, ih_soma)
                error, error_components = compute_error(features, TARGETS)

                results.append({
                    'g_pas': g_pas,
                    'ih_soma': ih_soma,
                    'vm_meas': features['vm'],
                    'rin_meas': features['rin'],
                    'tau_meas': features['tau'],
                    'error_total': error,
                    'error_vm': error_components['vm_error'],
                    'error_rin': error_components['rin_error'],
                    'error_tau': error_components['tau_error']
                })

                print(f"Vm={features['vm']:.2f}, Rin={features['rin']:.1f}, τ={features['tau']:.2f}, Error={error:.3f}")

            except Exception as e:
                print(f"FAILED: {e}")
                continue

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Find optimal parameters
    best_idx = df['error_total'].idxmin()
    best = df.loc[best_idx]

    print()
    print("="*80)
    print("OPTIMAL PARAMETERS")
    print("="*80)
    print(f"g_pas:      {best['g_pas']:.2e} S/cm²")
    print(f"Ih_soma:    {best['ih_soma']:.2e} S/cm²")
    print()
    print("RESULTING FEATURES:")
    print(f"  Resting Vm: {best['vm_meas']:.2f} mV (target: {TARGETS['vm']:.2f} mV)")
    print(f"  Rin:        {best['rin_meas']:.1f} MΩ (target: {TARGETS['rin']:.1f} MΩ)")
    print(f"  τ:          {best['tau_meas']:.2f} ms (target: {TARGETS['tau']:.2f} ms)")
    print()
    print(f"Total Error: {best['error_total']:.3f}")
    print("="*80)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(os.path.dirname(__file__), "..", "results", f"grid_search_{timestamp}.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"\n[SAVED] {csv_path}")

    return df, best

if __name__ == "__main__":
    df, best_params = main()
