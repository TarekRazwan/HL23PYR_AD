"""
EFEL validation for HL23PYR Stage 1 — Passive, Sag, and Excitability
Compares measured features to targets.json and outputs pass/fail table.
"""
import json, glob, os
import numpy as np
import pandas as pd
import efel
from datetime import datetime

THIS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(THIS_DIR, "..", "data")
RESULTS_DIR = os.path.join(THIS_DIR, "..", "results")

os.makedirs(RESULTS_DIR, exist_ok=True)


def load_trace(json_file):
    """Load time and voltage traces from JSON"""
    with open(json_file) as f:
        d = json.load(f)
    t = np.array(d['simData']['t'])
    v = np.array(d['simData']['v_soma']['cell_0'])
    return t, v


def to_efel_trace(t, v, stim_start=100.0, stim_end=1100.0):
    """Convert to EFEL trace format"""
    return {
        'T': t,
        'V': v,
        'stim_start': [stim_start],
        'stim_end': [stim_end]
    }


def compute_passive_features(t, v, stim_start=100.0, stim_end=1100.0):
    """
    Compute passive properties from subthreshold responses.

    For 0 pA: resting Vm
    For -50 pA: Rin, tau, voltage_base
    For -110 pA: sag_ratio2, sag_amplitude
    """
    trace = to_efel_trace(t, v, stim_start, stim_end)

    # EFEL features for passive/subthreshold
    feature_names = [
        'voltage_base',           # Resting Vm (mV)
        'steady_state_voltage',   # Steady-state voltage during step
        'voltage_deflection',     # ΔV from baseline
        'sag_amplitude',          # Sag magnitude (mV)
        'sag_ratio2',             # Sag ratio (0-1)
        'decay_time_constant_after_stim',  # Tau (ms)
        'ohmic_input_resistance',  # Rin (MΩ) — only for current steps
    ]

    result = efel.getFeatureValues([trace], feature_names)[0]

    # Clean up None values
    features = {}
    for key, val in result.items():
        if val is not None and len(val) > 0:
            features[key] = val[0] if isinstance(val, np.ndarray) else val
        else:
            features[key] = None

    return features


def compute_spiking_features(t, v, stim_start=100.0, stim_end=1100.0):
    """
    Compute spiking features from suprathreshold responses.

    Returns:
        dict with spike count, mean frequency, AP width, amplitude, etc.
    """
    trace = to_efel_trace(t, v, stim_start, stim_end)

    feature_names = [
        'Spikecount',
        'mean_frequency',
        'adaptation_index',
        'AP_amplitude',
        'AP_width',
        'AHP_depth',
        'AP_rise_rate',
        'AP_fall_rate',
    ]

    result = efel.getFeatureValues([trace], feature_names)[0]

    features = {}
    for key, val in result.items():
        if val is not None and len(val) > 0:
            features[key] = val[0] if isinstance(val, np.ndarray) else val
        else:
            features[key] = None

    return features


def manual_rin_tau(t, v, i_pA, stim_start=100.0, stim_end=1100.0):
    """
    Manually compute Rin and tau from voltage deflection.

    Rin = ΔV / I  (Ohm's law)
    Tau = fit exponential decay
    """
    # Get baseline voltage (pre-stim)
    pre_stim_idx = (t >= 0) & (t < stim_start)
    v_base = np.mean(v[pre_stim_idx])

    # Get steady-state voltage (last 200 ms of stim)
    steady_idx = (t >= stim_end - 200) & (t <= stim_end)
    v_steady = np.mean(v[steady_idx])

    # Voltage deflection
    delta_v = v_steady - v_base  # mV

    # Input resistance (Rin)
    if i_pA != 0:
        i_nA = i_pA / 1000.0  # convert to nA
        rin_MOhm = abs(delta_v / i_nA)  # MΩ
    else:
        rin_MOhm = None

    # Tau: fit exponential to the charging/discharging phase
    # For hyperpolarizing step: fit first 50 ms after stim onset
    fit_window_idx = (t >= stim_start) & (t <= stim_start + 50)
    t_fit = t[fit_window_idx] - stim_start
    v_fit = v[fit_window_idx]

    if len(t_fit) > 10:
        # Fit V(t) = v_steady + (v_base - v_steady) * exp(-t/tau)
        # Rearrange: log(|V(t) - v_steady|) = log(|v_base - v_steady|) - t/tau
        v_norm = v_fit - v_steady
        v_diff = v_base - v_steady

        if abs(v_diff) > 0.1:  # avoid division by small numbers
            # Use only points where voltage is still changing
            valid_idx = np.abs(v_norm) > 0.1 * abs(v_diff)
            if np.sum(valid_idx) > 5:
                t_valid = t_fit[valid_idx]
                v_valid = np.abs(v_norm[valid_idx])

                # Linear fit of log(v_valid) vs t
                log_v = np.log(v_valid)
                coeffs = np.polyfit(t_valid, log_v, 1)
                tau_ms = -1.0 / coeffs[0]  # ms
            else:
                tau_ms = None
        else:
            tau_ms = None
    else:
        tau_ms = None

    return {
        'v_base': v_base,
        'v_steady': v_steady,
        'delta_v': delta_v,
        'Rin_MOhm': rin_MOhm,
        'tau_ms': tau_ms
    }


def load_targets():
    """Load target features from targets.json"""
    targets_file = os.path.join(THIS_DIR, "targets.json")
    with open(targets_file) as f:
        return json.load(f)['features']


def check_tolerance(measured, target, tolerance_pct=10):
    """
    Check if measured value is within tolerance of target.

    Args:
        measured: measured value
        target: target value
        tolerance_pct: tolerance as percentage of target

    Returns:
        (pass, lower_bound, upper_bound)
    """
    if measured is None or target is None:
        return None, None, None

    tol = abs(target * tolerance_pct / 100.0)
    lower = target - tol
    upper = target + tol
    passed = lower <= measured <= upper

    return passed, lower, upper


def generate_report(features_by_protocol, targets):
    """
    Generate a comparison table: Measured vs Target with Pass/Fail.

    Args:
        features_by_protocol: dict mapping protocol name -> extracted features
        targets: target features from targets.json

    Returns:
        pandas DataFrame
    """
    rows = []

    # Define feature mappings: (protocol_name, feature_key, target_key, tolerance_pct)
    feature_map = [
        # Resting Vm (from 0 pA baseline)
        ("baseline_0pA", "v_base", "RestingVm_mV", 2.6),  # ±2 mV absolute -> ~2.6% of -75.8

        # Rin and Tau (from -50 pA passive step)
        ("passive_neg50pA", "Rin_MOhm", "InputResistance_MOhm", 15),
        ("passive_neg50pA", "tau_ms", "MembraneTau_ms", 11),  # ±2 ms of 17.8 -> ~11%

        # Sag ratio (from -110 pA)
        ("sag_neg110pA", "sag_ratio2", "SagRatio", 33),  # target ~0.15, allow 0.10-0.20

        # Rheobase and FI slope (requires multiple current steps — approximate from 170 pA)
        ("sweep_45", "Spikecount", "Rheobase_pA", None),  # qualitative: should spike at 170 pA

        # Firing rate at 310 pA
        ("sweep_52", "mean_frequency", "FiringRate_Hz_at_310pA", 15),

        # Adaptation index
        ("sweep_52", "adaptation_index", "AdaptationIndex", 30),

        # AP shape (from 170 pA or 310 pA)
        ("sweep_45", "AP_width", "AP_width_ms", 20),  # tolerance depends on target
    ]

    for proto_name, feat_key, target_key, tol_pct in feature_map:
        if proto_name not in features_by_protocol:
            continue

        feat_dict = features_by_protocol[proto_name]
        measured = feat_dict.get(feat_key)
        target = targets.get(target_key)

        if target is None:
            # Some features don't have explicit targets yet
            rows.append({
                "Feature": f"{feat_key} ({proto_name})",
                "Measured": f"{measured:.3f}" if measured is not None else "N/A",
                "Target": "N/A",
                "Tolerance": "N/A",
                "Pass": "?"
            })
            continue

        if tol_pct is not None and measured is not None:
            passed, lower, upper = check_tolerance(measured, target, tol_pct)
            pass_str = "✓" if passed else "✗"
            tol_str = f"{lower:.2f} – {upper:.2f}"
        else:
            pass_str = "?"
            tol_str = "N/A"

        rows.append({
            "Feature": f"{feat_key} ({proto_name})",
            "Measured": f"{measured:.3f}" if measured is not None else "N/A",
            "Target": f"{target:.3f}" if isinstance(target, (int, float)) else str(target),
            "Tolerance": tol_str,
            "Pass": pass_str
        })

    df = pd.DataFrame(rows)
    return df


def main():
    print("="*70)
    print("EFEL Validation: HL23PYR Stage 1 Healthy Baseline")
    print("="*70)

    # Load targets
    targets = load_targets()
    print(f"\nLoaded targets: {targets}\n")

    # Add SagRatio if not in targets (typical value for L2/3 PYR)
    if "SagRatio" not in targets:
        targets["SagRatio"] = 0.15  # midpoint of 0.10–0.20 range

    if "AP_width_ms" not in targets:
        targets["AP_width_ms"] = 1.0  # typical AP width ~1 ms (half-width)

    # Find all simulation output files
    sim_files = sorted(glob.glob(os.path.join(DATA_DIR, "*_sim.json")))

    if not sim_files:
        print(f"[ERROR] No simulation files found in {DATA_DIR}")
        print("Please run build_netpyne_model_HL23PYR.py first.")
        return

    features_by_protocol = {}

    # Extract features from each protocol
    for sim_file in sim_files:
        protocol_name = os.path.basename(sim_file).replace("_sim.json", "")
        print(f"\n{'='*70}")
        print(f"Protocol: {protocol_name}")
        print(f"{'='*70}")

        t, v = load_trace(sim_file)

        # Determine protocol type based on name
        if "0pA" in protocol_name or "baseline" in protocol_name:
            # Baseline: just measure resting Vm
            manual = manual_rin_tau(t, v, i_pA=0, stim_start=100, stim_end=1100)
            features = {**manual}
            print(f"  Resting Vm: {manual['v_base']:.2f} mV")

        elif "neg50pA" in protocol_name or "passive" in protocol_name:
            # Passive: Rin and tau
            manual = manual_rin_tau(t, v, i_pA=-50, stim_start=100, stim_end=1100)
            efel_feat = compute_passive_features(t, v, 100, 1100)
            features = {**manual, **efel_feat}

            print(f"  Resting Vm: {manual['v_base']:.2f} mV")
            print(f"  Steady-state Vm: {manual['v_steady']:.2f} mV")
            print(f"  ΔV: {manual['delta_v']:.2f} mV")
            print(f"  Rin: {manual['Rin_MOhm']:.1f} MΩ" if manual['Rin_MOhm'] else "  Rin: N/A")
            print(f"  Tau: {manual['tau_ms']:.2f} ms" if manual['tau_ms'] else "  Tau: N/A")

        elif "neg110pA" in protocol_name or "sag" in protocol_name:
            # Sag: measure sag ratio
            manual = manual_rin_tau(t, v, i_pA=-110, stim_start=100, stim_end=1100)
            efel_feat = compute_passive_features(t, v, 100, 1100)
            features = {**manual, **efel_feat}

            print(f"  Resting Vm: {manual['v_base']:.2f} mV")
            print(f"  Sag amplitude: {efel_feat.get('sag_amplitude', 'N/A')} mV")
            print(f"  Sag ratio: {efel_feat.get('sag_ratio2', 'N/A')}")

        elif "sweep" in protocol_name:
            # Spiking protocols
            spike_feat = compute_spiking_features(t, v, 100, 1100)
            features = {**spike_feat}

            print(f"  Spike count: {spike_feat.get('Spikecount', 0)}")
            print(f"  Mean frequency: {spike_feat.get('mean_frequency', 0):.2f} Hz")
            print(f"  Adaptation index: {spike_feat.get('adaptation_index', 'N/A')}")
            print(f"  AP amplitude: {spike_feat.get('AP_amplitude', 'N/A')} mV")
            print(f"  AP width: {spike_feat.get('AP_width', 'N/A')} ms")

        else:
            # Unknown protocol
            features = {}

        features_by_protocol[protocol_name] = features

    # Generate comparison report
    print("\n" + "="*70)
    print("SUMMARY: Measured vs Target")
    print("="*70)

    report_df = generate_report(features_by_protocol, targets)
    print(report_df.to_string(index=False))

    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = os.path.join(RESULTS_DIR, f"validation_Stage1_Healthy_{timestamp}.csv")
    report_df.to_csv(csv_path, index=False)
    print(f"\n[SAVED] {csv_path}")

    # Count passes and failures
    pass_count = (report_df['Pass'] == '✓').sum()
    fail_count = (report_df['Pass'] == '✗').sum()
    unknown_count = (report_df['Pass'] == '?').sum()

    print(f"\nResults: {pass_count} passed, {fail_count} failed, {unknown_count} N/A")

    if fail_count > 0:
        print("\n[ACTION REQUIRED] Some features are out of tolerance.")
        print("See proposed adjustments below.")
    else:
        print("\n[SUCCESS] All features within tolerance!")

    return features_by_protocol, targets, report_df


if __name__ == "__main__":
    features, targets, report = main()
