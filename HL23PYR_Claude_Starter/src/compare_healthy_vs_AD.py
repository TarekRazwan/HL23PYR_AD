"""
Compare Healthy vs AD Variant: Feature Extraction & Analysis
Quantifies AD-induced changes in neuronal excitability
"""
import json
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

def load_trace(json_file):
    """Load voltage trace from NetPyNE JSON output"""
    with open(json_file) as f:
        d = json.load(f)
    t = np.array(d['simData']['t'])
    v = np.array(d['simData']['v_soma']['cell_0'])
    return t, v

def count_spikes(t, v, stim_start=100, stim_end=1100, threshold=-20):
    """Count action potentials during stimulus period"""
    stim_idx = (t >= stim_start) & (t <= stim_end)
    v_stim = v[stim_idx]
    t_stim = t[stim_idx]

    # Find peaks above threshold
    crossings = np.where(np.diff((v_stim > threshold).astype(int)) == 1)[0]
    spike_times = t_stim[crossings]

    # Filter out close peaks (within 2 ms = refractory period)
    if len(spike_times) > 0:
        filtered_spikes = [spike_times[0]]
        for spike in spike_times[1:]:
            if spike - filtered_spikes[-1] > 2.0:
                filtered_spikes.append(spike)
        return len(filtered_spikes)
    return 0

def measure_ap_properties(t, v, stim_start=100, threshold=-20):
    """Measure AP amplitude and width from first spike"""
    # Find first spike after stim_start
    post_stim_idx = t >= stim_start
    v_post = v[post_stim_idx]
    t_post = t[post_stim_idx]

    crossings = np.where(np.diff((v_post > threshold).astype(int)) == 1)[0]
    if len(crossings) == 0:
        return None, None

    # Get first spike
    spike_idx = crossings[0]
    spike_window = slice(max(0, spike_idx - 50), min(len(v_post), spike_idx + 100))
    v_spike = v_post[spike_window]
    t_spike = t_post[spike_window]

    # AP amplitude (peak - baseline)
    baseline = np.mean(v_spike[:20])
    peak = np.max(v_spike)
    amplitude = peak - baseline

    # AP width at half-max
    half_max = baseline + amplitude / 2
    above_half = v_spike > half_max
    if np.any(above_half):
        indices = np.where(above_half)[0]
        if len(indices) > 1:
            width = t_spike[indices[-1]] - t_spike[indices[0]]
        else:
            width = np.nan
    else:
        width = np.nan

    return amplitude, width

def measure_passive(t, v, i_pA, stim_start=100, stim_end=1100):
    """Measure Rin and tau from passive response"""
    pre_idx = (t >= 50) & (t < stim_start)
    v_base = np.mean(v[pre_idx])

    ss_idx = (t >= stim_end - 200) & (t <= stim_end)
    v_ss = np.mean(v[ss_idx])

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

    return {'v_base': v_base, 'rin': rin, 'tau': tau}

print("="*80)
print("HEALTHY vs AD VARIANT COMPARISON")
print("="*80)

# ============================================================================
# PASSIVE PROPERTIES
# ============================================================================
print("\n[1/4] PASSIVE PROPERTIES")
print("-"*80)

# -50 pA protocol
t_h, v_h = load_trace("data/passive_neg50pA_sim.json")
t_ad, v_ad = load_trace("data/passive_neg50pA_AD_sim.json")

passive_h = measure_passive(t_h, v_h, -50)
passive_ad = measure_passive(t_ad, v_ad, -50)

print(f"\nResting Vm:")
print(f"  Healthy: {passive_h['v_base']:.2f} mV")
print(f"  AD:      {passive_ad['v_base']:.2f} mV")
print(f"  Δ (AD - Healthy): {passive_ad['v_base'] - passive_h['v_base']:+.2f} mV")

print(f"\nInput Resistance (Rin):")
print(f"  Healthy: {passive_h['rin']:.1f} MΩ")
print(f"  AD:      {passive_ad['rin']:.1f} MΩ")
print(f"  Δ (AD - Healthy): {passive_ad['rin'] - passive_h['rin']:+.1f} MΩ ({100*(passive_ad['rin']/passive_h['rin']-1):+.1f}%)")

print(f"\nMembrane Time Constant (τ):")
print(f"  Healthy: {passive_h['tau']:.2f} ms")
print(f"  AD:      {passive_ad['tau']:.2f} ms")
print(f"  Δ (AD - Healthy): {passive_ad['tau'] - passive_h['tau']:+.2f} ms ({100*(passive_ad['tau']/passive_h['tau']-1):+.1f}%)")

# ============================================================================
# RHEOBASE CHECK (170 pA)
# ============================================================================
print("\n[2/4] RHEOBASE CHECK @ 170 pA")
print("-"*80)

t_h, v_h = load_trace("data/sweep_45_sim.json")
t_ad, v_ad = load_trace("data/sweep_45_AD_sim.json")

spikes_h_170 = count_spikes(t_h, v_h)
spikes_ad_170 = count_spikes(t_ad, v_ad)

print(f"\nSpike Count:")
print(f"  Healthy: {spikes_h_170} spikes")
print(f"  AD:      {spikes_ad_170} spikes")
print(f"  Δ (AD - Healthy): {spikes_ad_170 - spikes_h_170:+d} spikes ({100*(spikes_ad_170/spikes_h_170-1):+.1f}%)")

# AP properties from first spike
amp_h, width_h = measure_ap_properties(t_h, v_h)
amp_ad, width_ad = measure_ap_properties(t_ad, v_ad)

if amp_h is not None and amp_ad is not None:
    print(f"\nAP Amplitude:")
    print(f"  Healthy: {amp_h:.1f} mV")
    print(f"  AD:      {amp_ad:.1f} mV")
    print(f"  Δ (AD - Healthy): {amp_ad - amp_h:+.1f} mV ({100*(amp_ad/amp_h-1):+.1f}%)")

if width_h is not None and width_ad is not None and not np.isnan(width_h) and not np.isnan(width_ad):
    print(f"\nAP Width:")
    print(f"  Healthy: {width_h:.2f} ms")
    print(f"  AD:      {width_ad:.2f} ms")
    print(f"  Δ (AD - Healthy): {width_ad - width_h:+.2f} ms ({100*(width_ad/width_h-1):+.1f}%)")

# ============================================================================
# HIGH CURRENT (310 pA)
# ============================================================================
print("\n[3/4] HIGH CURRENT FIRING @ 310 pA")
print("-"*80)

t_h, v_h = load_trace("data/sweep_52_sim.json")
t_ad, v_ad = load_trace("data/sweep_52_AD_sim.json")

spikes_h_310 = count_spikes(t_h, v_h)
spikes_ad_310 = count_spikes(t_ad, v_ad)

freq_h = spikes_h_310 / 1.0  # Hz (1 second stim)
freq_ad = spikes_ad_310 / 1.0

print(f"\nSpike Count:")
print(f"  Healthy: {spikes_h_310} spikes")
print(f"  AD:      {spikes_ad_310} spikes")
print(f"  Δ (AD - Healthy): {spikes_ad_310 - spikes_h_310:+d} spikes")

print(f"\nFiring Rate:")
print(f"  Healthy: {freq_h:.2f} Hz")
print(f"  AD:      {freq_ad:.2f} Hz")
if freq_h > 0:
    print(f"  Δ (AD - Healthy): {freq_ad - freq_h:+.2f} Hz ({100*(freq_ad/freq_h-1):+.1f}%)")
else:
    print(f"  Δ (AD - Healthy): N/A (healthy = 0)")

# AP properties from first spike (if any)
amp_h, width_h = measure_ap_properties(t_h, v_h)
amp_ad, width_ad = measure_ap_properties(t_ad, v_ad)

if amp_ad is not None:
    print(f"\nAP Amplitude (first spike):")
    if amp_h is not None:
        print(f"  Healthy: {amp_h:.1f} mV")
    print(f"  AD:      {amp_ad:.1f} mV")
    if amp_h is not None:
        print(f"  Δ (AD - Healthy): {amp_ad - amp_h:+.1f} mV ({100*(amp_ad/amp_h-1):+.1f}%)")

# ============================================================================
# SUMMARY TABLE
# ============================================================================
print("\n[4/4] SUMMARY TABLE")
print("="*80)

summary = pd.DataFrame({
    'Feature': [
        'Resting Vm (mV)',
        'Rin (MΩ)',
        'τ (ms)',
        'Spikes @ 170 pA',
        'Spikes @ 310 pA',
        'Firing Rate @ 310 pA (Hz)',
        'AP Amplitude (mV)',
        'AP Width (ms)'
    ],
    'Healthy': [
        f"{passive_h['v_base']:.2f}",
        f"{passive_h['rin']:.1f}",
        f"{passive_h['tau']:.2f}",
        f"{spikes_h_170}",
        f"{spikes_h_310}",
        f"{freq_h:.2f}",
        f"{amp_h:.1f}" if amp_h is not None else "N/A",
        f"{width_h:.2f}" if width_h is not None and not np.isnan(width_h) else "N/A"
    ],
    'AD': [
        f"{passive_ad['v_base']:.2f}",
        f"{passive_ad['rin']:.1f}",
        f"{passive_ad['tau']:.2f}",
        f"{spikes_ad_170}",
        f"{spikes_ad_310}",
        f"{freq_ad:.2f}",
        f"{amp_ad:.1f}" if amp_ad is not None else "N/A",
        f"{width_ad:.2f}" if width_ad is not None and not np.isnan(width_ad) else "N/A"
    ],
    'Δ (AD - Healthy)': [
        f"{passive_ad['v_base'] - passive_h['v_base']:+.2f}",
        f"{passive_ad['rin'] - passive_h['rin']:+.1f}",
        f"{passive_ad['tau'] - passive_h['tau']:+.2f}",
        f"{spikes_ad_170 - spikes_h_170:+d}",
        f"{spikes_ad_310 - spikes_h_310:+d}",
        f"{freq_ad - freq_h:+.2f}",
        f"{amp_ad - amp_h:+.1f}" if amp_h is not None and amp_ad is not None else "N/A",
        f"{width_ad - width_h:+.2f}" if width_h is not None and width_ad is not None and not np.isnan(width_h) and not np.isnan(width_ad) else "N/A"
    ],
    'Δ (%)': [
        f"{100*(passive_ad['v_base']/passive_h['v_base']-1):+.1f}%",
        f"{100*(passive_ad['rin']/passive_h['rin']-1):+.1f}%",
        f"{100*(passive_ad['tau']/passive_h['tau']-1):+.1f}%",
        f"{100*(spikes_ad_170/spikes_h_170-1):+.1f}%",
        f"{100*(spikes_ad_310/spikes_h_310-1) if spikes_h_310 > 0 else 0:+.1f}%" if spikes_h_310 > 0 else "N/A",
        f"{100*(freq_ad/freq_h-1):+.1f}%" if freq_h > 0 else "N/A",
        f"{100*(amp_ad/amp_h-1):+.1f}%" if amp_h is not None and amp_ad is not None else "N/A",
        f"{100*(width_ad/width_h-1):+.1f}%" if width_h is not None and width_ad is not None and not np.isnan(width_h) and not np.isnan(width_ad) else "N/A"
    ]
})

print(summary.to_string(index=False))

# Save to CSV
output_path = "results/healthy_vs_AD_comparison.csv"
summary.to_csv(output_path, index=False)
print(f"\n[SAVED] {output_path}")

print("\n" + "="*80)
print("INTERPRETATION")
print("="*80)
print("\nAD-induced changes (30% Nav/Kv, 25% SK reduction):")
if spikes_ad_310 < spikes_h_310:
    print("  ✓ REDUCED EXCITABILITY: AD variant fires fewer spikes")
    if freq_h > 0:
        reduction = 100 * (freq_h - freq_ad) / freq_h
        print(f"  ✓ FIRING RATE REDUCTION: {reduction:.1f}% decrease @ 310 pA")
else:
    print("  ✗ UNEXPECTED: AD variant fires more than healthy (check biophysics)")

if amp_ad is not None and amp_h is not None and amp_ad < amp_h:
    print(f"  ✓ SMALLER AP AMPLITUDE: Consistent with Nav reduction")

if width_ad is not None and width_h is not None and not np.isnan(width_ad) and not np.isnan(width_h):
    if width_ad > width_h:
        print(f"  ✓ WIDER AP: Consistent with Kv reduction (slower repolarization)")

print("\n" + "="*80)
