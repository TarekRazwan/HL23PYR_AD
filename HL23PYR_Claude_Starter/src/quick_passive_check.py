"""
Quick check of passive features (Rin, tau, sag) from optimal parameters.
"""
import json
import numpy as np
from scipy.optimize import curve_fit

def load_trace(json_file):
    with open(json_file) as f:
        d = json.load(f)
    t = np.array(d['simData']['t'])
    v = np.array(d['simData']['v_soma']['cell_0'])
    return t, v

def measure_passive(t, v, i_pA, stim_start=100, stim_end=1100):
    """Measure Rin, tau from voltage response"""
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
        'v_base': v_base,
        'v_ss': v_ss,
        'delta_v': delta_v,
        'rin': rin,
        'tau': tau
    }

def measure_sag(t, v, stim_start=100, stim_end=1100):
    """Measure sag ratio"""
    # Baseline
    pre_idx = (t >= 50) & (t < stim_start)
    v_base = np.mean(v[pre_idx])

    # Peak deflection (minimum voltage during step)
    step_idx = (t >= stim_start) & (t <= stim_end)
    v_min = np.min(v[step_idx])

    # Steady-state
    ss_idx = (t >= stim_end - 200) & (t <= stim_end)
    v_ss = np.mean(v[ss_idx])

    # Sag ratio
    peak_deflection = v_base - v_min
    ss_deflection = v_base - v_ss
    sag_ratio = (peak_deflection - ss_deflection) / peak_deflection if peak_deflection != 0 else 0

    return {
        'v_base': v_base,
        'v_min': v_min,
        'v_ss': v_ss,
        'peak_deflection': peak_deflection,
        'ss_deflection': ss_deflection,
        'sag_ratio': sag_ratio
    }

print("="*70)
print("PASSIVE FEATURES: Optimal Parameters (g_pas=8e-05, Ih_soma=8e-05)")
print("="*70)

# -50 pA protocol
t, v = load_trace("data/passive_neg50pA_sim.json")
passive = measure_passive(t, v, -50)
print(f"\n-50 pA Protocol:")
print(f"  Resting Vm:  {passive['v_base']:.2f} mV")
print(f"  Rin:         {passive['rin']:.1f} MΩ")
print(f"  τ:           {passive['tau']:.2f} ms")

# -110 pA protocol
t, v = load_trace("data/sag_neg110pA_sim.json")
sag = measure_sag(t, v)
print(f"\n-110 pA Protocol:")
print(f"  Resting Vm:  {sag['v_base']:.2f} mV")
print(f"  Peak (min):  {sag['v_min']:.2f} mV")
print(f"  Steady:      {sag['v_ss']:.2f} mV")
print(f"  Sag ratio:   {sag['sag_ratio']:.3f}")

# Targets
print("\n" + "="*70)
print("COMPARISON TO TARGETS")
print("="*70)
targets = {
    'vm': -75.8,
    'rin': 100.0,
    'tau': 17.8,
    'sag': 0.15  # midpoint of 0.10-0.20 range
}

print(f"Vm:        {passive['v_base']:.2f} mV   (target: {targets['vm']:.2f} mV)   Δ = {passive['v_base'] - targets['vm']:+.2f} mV")
print(f"Rin:       {passive['rin']:.1f} MΩ   (target: {targets['rin']:.1f} MΩ)   Δ = {passive['rin'] - targets['rin']:+.1f} MΩ ({100*(passive['rin']/targets['rin']-1):+.1f}%)")
print(f"τ:         {passive['tau']:.2f} ms   (target: {targets['tau']:.2f} ms)   Δ = {passive['tau'] - targets['tau']:+.2f} ms ({100*(passive['tau']/targets['tau']-1):+.1f}%)")
print(f"Sag ratio: {sag['sag_ratio']:.3f}   (target: {targets['sag']:.3f})   Δ = {sag['sag_ratio'] - targets['sag']:+.3f}")

print("\n" + "="*70)
