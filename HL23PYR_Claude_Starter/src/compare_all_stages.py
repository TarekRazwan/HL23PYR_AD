"""
Compare Healthy vs Stage 1 vs Stage 3: Three-Condition Analysis
Demonstrates the "storm before the quiet" AD progression
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
print("THREE-STAGE COMPARISON: Healthy → Stage 1 (Early AD) → Stage 3 (Late AD)")
print("="*80)

# ============================================================================
# PASSIVE PROPERTIES
# ============================================================================
print("\n[1/3] PASSIVE PROPERTIES (from -50 pA protocol)")
print("-"*80)

# Load passive responses
t_h, v_h = load_trace("data/passive_neg50pA_sim.json")
t_s1, v_s1 = load_trace("data/passive_neg50pA_AD_Stage1_sim.json")
t_s3, v_s3 = load_trace("data/passive_neg50pA_AD_sim.json")

passive_h = measure_passive(t_h, v_h, -50)
passive_s1 = measure_passive(t_s1, v_s1, -50)
passive_s3 = measure_passive(t_s3, v_s3, -50)

print(f"\nResting Vm:")
print(f"  Healthy:   {passive_h['v_base']:7.2f} mV")
print(f"  Stage 1:   {passive_s1['v_base']:7.2f} mV  ({passive_s1['v_base'] - passive_h['v_base']:+.2f} mV)")
print(f"  Stage 3:   {passive_s3['v_base']:7.2f} mV  ({passive_s3['v_base'] - passive_h['v_base']:+.2f} mV)")

print(f"\nInput Resistance (Rin):")
print(f"  Healthy:   {passive_h['rin']:7.1f} MΩ")
print(f"  Stage 1:   {passive_s1['rin']:7.1f} MΩ  ({100*(passive_s1['rin']/passive_h['rin']-1):+.1f}%)")
print(f"  Stage 3:   {passive_s3['rin']:7.1f} MΩ  ({100*(passive_s3['rin']/passive_h['rin']-1):+.1f}%)")

print(f"\nMembrane Time Constant (τ):")
print(f"  Healthy:   {passive_h['tau']:7.2f} ms")
print(f"  Stage 1:   {passive_s1['tau']:7.2f} ms  ({100*(passive_s1['tau']/passive_h['tau']-1):+.1f}%)")
print(f"  Stage 3:   {passive_s3['tau']:7.2f} ms  ({100*(passive_s3['tau']/passive_h['tau']-1):+.1f}%)")

# ============================================================================
# 310 pA HIGH CURRENT (Key differentiator)
# ============================================================================
print("\n[2/3] HIGH CURRENT FIRING @ 310 pA")
print("-"*80)

t_h, v_h = load_trace("data/sweep_52_sim.json")
t_s1, v_s1 = load_trace("data/sweep_52_AD_Stage1_sim.json")
t_s3, v_s3 = load_trace("data/sweep_52_AD_sim.json")

spikes_h_310 = count_spikes(t_h, v_h)
spikes_s1_310 = count_spikes(t_s1, v_s1)
spikes_s3_310 = count_spikes(t_s3, v_s3)

freq_h = spikes_h_310 / 1.0
freq_s1 = spikes_s1_310 / 1.0
freq_s3 = spikes_s3_310 / 1.0

print(f"\nSpike Count (1000 ms stim):")
print(f"  Healthy:   {spikes_h_310:3d} spikes  ({freq_h:.2f} Hz)")
print(f"  Stage 1:   {spikes_s1_310:3d} spikes  ({freq_s1:.2f} Hz)  [{100*(freq_s1/freq_h-1):+.1f}%]")
print(f"  Stage 3:   {spikes_s3_310:3d} spikes  ({freq_s3:.2f} Hz)  [{100*(freq_s3/freq_h-1):+.1f}%]")

# AP properties
amp_h, width_h = measure_ap_properties(t_h, v_h)
amp_s1, width_s1 = measure_ap_properties(t_s1, v_s1)
amp_s3, width_s3 = measure_ap_properties(t_s3, v_s3)

if amp_h is not None:
    print(f"\nAP Amplitude (first spike):")
    print(f"  Healthy:   {amp_h:.1f} mV")
    if amp_s1 is not None:
        print(f"  Stage 1:   {amp_s1:.1f} mV  ({100*(amp_s1/amp_h-1):+.1f}%)")
    if amp_s3 is not None:
        print(f"  Stage 3:   {amp_s3:.1f} mV  ({100*(amp_s3/amp_h-1):+.1f}%)")

if width_h is not None and not np.isnan(width_h):
    print(f"\nAP Width (first spike):")
    print(f"  Healthy:   {width_h:.2f} ms")
    if width_s1 is not None and not np.isnan(width_s1):
        print(f"  Stage 1:   {width_s1:.2f} ms  ({100*(width_s1/width_h-1):+.1f}%)")
    if width_s3 is not None and not np.isnan(width_s3):
        print(f"  Stage 3:   {width_s3:.2f} ms  ({100*(width_s3/width_h-1):+.1f}%)")

# ============================================================================
# 170 pA RHEOBASE CHECK
# ============================================================================
print("\n[3/3] NEAR-RHEOBASE @ 170 pA")
print("-"*80)

t_h, v_h = load_trace("data/sweep_45_sim.json")
t_s1, v_s1 = load_trace("data/sweep_45_AD_Stage1_sim.json")
t_s3, v_s3 = load_trace("data/sweep_45_AD_sim.json")

spikes_h_170 = count_spikes(t_h, v_h)
spikes_s1_170 = count_spikes(t_s1, v_s1)
spikes_s3_170 = count_spikes(t_s3, v_s3)

print(f"\nSpike Count (1000 ms stim):")
print(f"  Healthy:   {spikes_h_170:3d} spikes")
print(f"  Stage 1:   {spikes_s1_170:3d} spikes  [{100*(spikes_s1_170/spikes_h_170-1):+.1f}%]")
print(f"  Stage 3:   {spikes_s3_170:3d} spikes  [{100*(spikes_s3_170/spikes_h_170-1):+.1f}%]")

# ============================================================================
# SUMMARY TABLE
# ============================================================================
print("\n" + "="*80)
print("SUMMARY TABLE")
print("="*80)

summary = pd.DataFrame({
    'Feature': [
        'Resting Vm (mV)',
        'Rin (MΩ)',
        'τ (ms)',
        'Spikes @ 170 pA',
        'Spikes @ 310 pA',
        'Firing Rate @ 310 pA (Hz)',
        'AP Amplitude @ 310 pA (mV)',
        'AP Width @ 310 pA (ms)'
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
    'Stage 1 (Early AD)': [
        f"{passive_s1['v_base']:.2f}",
        f"{passive_s1['rin']:.1f}",
        f"{passive_s1['tau']:.2f}",
        f"{spikes_s1_170}",
        f"{spikes_s1_310}",
        f"{freq_s1:.2f}",
        f"{amp_s1:.1f}" if amp_s1 is not None else "N/A",
        f"{width_s1:.2f}" if width_s1 is not None and not np.isnan(width_s1) else "N/A"
    ],
    'Δ Stage 1 (%)': [
        f"{100*(passive_s1['v_base']/passive_h['v_base']-1):+.1f}%",
        f"{100*(passive_s1['rin']/passive_h['rin']-1):+.1f}%",
        f"{100*(passive_s1['tau']/passive_h['tau']-1):+.1f}%",
        f"{100*(spikes_s1_170/spikes_h_170-1):+.1f}%",
        f"{100*(spikes_s1_310/spikes_h_310-1):+.1f}%",
        f"{100*(freq_s1/freq_h-1):+.1f}%",
        f"{100*(amp_s1/amp_h-1):+.1f}%" if amp_h is not None and amp_s1 is not None else "N/A",
        f"{100*(width_s1/width_h-1):+.1f}%" if width_h is not None and width_s1 is not None and not np.isnan(width_h) and not np.isnan(width_s1) else "N/A"
    ],
    'Stage 3 (Late AD)': [
        f"{passive_s3['v_base']:.2f}",
        f"{passive_s3['rin']:.1f}",
        f"{passive_s3['tau']:.2f}",
        f"{spikes_s3_170}",
        f"{spikes_s3_310}",
        f"{freq_s3:.2f}",
        f"{amp_s3:.1f}" if amp_s3 is not None else "N/A",
        f"{width_s3:.2f}" if width_s3 is not None and not np.isnan(width_s3) else "N/A"
    ],
    'Δ Stage 3 (%)': [
        f"{100*(passive_s3['v_base']/passive_h['v_base']-1):+.1f}%",
        f"{100*(passive_s3['rin']/passive_h['rin']-1):+.1f}%",
        f"{100*(passive_s3['tau']/passive_h['tau']-1):+.1f}%",
        f"{100*(spikes_s3_170/spikes_h_170-1):+.1f}%",
        f"{100*(spikes_s3_310/spikes_h_310-1):+.1f}%",
        f"{100*(freq_s3/freq_h-1):+.1f}%",
        f"{100*(amp_s3/amp_h-1):+.1f}%" if amp_h is not None and amp_s3 is not None else "N/A",
        f"{100*(width_s3/width_h-1):+.1f}%" if width_h is not None and width_s3 is not None and not np.isnan(width_h) and not np.isnan(width_s3) else "N/A"
    ]
})

print(summary.to_string(index=False))

# Save to CSV
output_path = "results/three_stage_comparison.csv"
summary.to_csv(output_path, index=False)
print(f"\n[SAVED] {output_path}")

# ============================================================================
# INTERPRETATION
# ============================================================================
print("\n" + "="*80)
print("INTERPRETATION: 'Storm Before the Quiet' Progression")
print("="*80)

print("\n[Stage 1 - Early AD Hyperexcitability (A+/T−/N−)]")
if freq_s1 > freq_h:
    increase = 100 * (freq_s1 - freq_h) / freq_h
    print(f"  ✓ HYPEREXCITABILITY: +{increase:.1f}% firing rate @ 310 pA")
    print(f"  → Mechanism: SK↓25%, M-current↓25%, Kv3.1↓10% (Nav unchanged)")
    print(f"  → Biological correlate: Reduced adaptation, lower rheobase")
else:
    print(f"  ⚠ EXPECTED HYPEREXCITABILITY: Got {100*(freq_s1/freq_h-1):+.1f}% change")
    print(f"  → May need stronger parameter changes or background drive")

print("\n[Stage 3 - Late AD Hypoexcitability (A+/T+/N+)]")
if freq_s3 < freq_h:
    reduction = 100 * (freq_h - freq_s3) / freq_h
    print(f"  ✓ SEVERE HYPOEXCITABILITY: -{reduction:.1f}% firing rate @ 310 pA")
    print(f"  → Mechanism: Nav↓30%, Kv↓30%, SK↓25%")
    print(f"  → Biological correlate: Channel dysfunction, synapse loss")

print("\n[Progression Pattern]")
print(f"  Healthy → Stage 1 → Stage 3")
print(f"  {freq_h:.0f} Hz → {freq_s1:.0f} Hz → {freq_s3:.0f} Hz @ 310 pA")

if freq_s1 > freq_h and freq_s3 < freq_h:
    print("  ✓ CORRECT 'STORM BEFORE QUIET' PATTERN")
elif freq_s1 <= freq_h:
    print("  ⚠ Stage 1 does not show clear hyperexcitability (may need tuning)")
    print("  → Consider: Further SK/M reduction, or add background depolarizing current")

print("\n" + "="*80)
