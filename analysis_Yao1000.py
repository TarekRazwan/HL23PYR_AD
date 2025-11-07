"""
analysis_Yao1000.py

Analysis script for Yao et al. 2022 network simulation results
Compares simulation output with published data

Usage:
    python analysis_Yao1000.py Yao1000.pkl
"""

import pickle
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

###############################################################################
# TARGET FIRING RATES (from Yao et al. 2022)
###############################################################################

# Published firing rates from in vivo recordings
TARGET_RATES = {
    'HL23PYR': 1.5,   # Hz (pyramidal neurons, sparse firing)
    'HL23SST': 5.0,   # Hz (SST interneurons, moderate activity)
    'HL23PV': 10.0,   # Hz (PV interneurons, high frequency)
    'HL23VIP': 8.0,   # Hz (VIP interneurons, moderate-high)
}

###############################################################################
# LOAD SIMULATION DATA
###############################################################################

if len(sys.argv) < 2:
    print("Usage: python analysis_Yao1000.py <simulation_file.pkl>")
    sys.exit(1)

sim_file = sys.argv[1]

if not os.path.exists(sim_file):
    print(f"Error: File {sim_file} not found")
    sys.exit(1)

print("=" * 80)
print(f"Loading simulation data from: {sim_file}")
print("=" * 80)

with open(sim_file, 'rb') as f:
    data = pickle.load(f)

# Extract spike data
spkt = np.array(data['simData']['spkt'])
spkid = np.array(data['simData']['spkid'])

# Extract population information
net = data['net']
pops = net['pops']

print(f"\nLoaded {len(spkt)} spikes from {len(spkid)} unique cells")

###############################################################################
# CALCULATE FIRING RATES
###############################################################################

# Analysis window (exclude initial 500ms transient)
tstart = 500  # ms
tstop = max(spkt) if len(spkt) > 0 else 4500
duration_s = (tstop - tstart) / 1000.0

print(f"\nAnalysis window: {tstart} - {tstop} ms ({duration_s:.2f} s)")
print("-" * 80)

# Calculate firing rates per population
results = {}

for pop_name, pop_data in pops.items():
    cell_gids = pop_data['cellGids']

    # Count spikes in analysis window for this population
    mask = np.isin(spkid, cell_gids) & (spkt >= tstart) & (spkt <= tstop)
    spikes_in_window = np.sum(mask)

    num_cells = len(cell_gids)
    if num_cells > 0 and duration_s > 0:
        avg_rate = spikes_in_window / (num_cells * duration_s)
    else:
        avg_rate = 0.0

    # Calculate per-cell statistics
    rates_per_cell = []
    for gid in cell_gids:
        cell_spikes = np.sum((spkid == gid) & (spkt >= tstart) & (spkt <= tstop))
        cell_rate = cell_spikes / duration_s
        rates_per_cell.append(cell_rate)

    results[pop_name] = {
        'avg_rate': avg_rate,
        'std_rate': np.std(rates_per_cell),
        'min_rate': np.min(rates_per_cell) if rates_per_cell else 0,
        'max_rate': np.max(rates_per_cell) if rates_per_cell else 0,
        'num_cells': num_cells,
        'total_spikes': spikes_in_window,
        'rates_per_cell': rates_per_cell,
    }

###############################################################################
# DISPLAY RESULTS
###############################################################################

print("\nFiring Rate Analysis:")
print("=" * 80)
print(f"{'Population':<15} {'Avg Rate':<12} {'Target':<12} {'Δ (%)':<12} {'Range':<20}")
print("-" * 80)

for pop_name in sorted(results.keys()):
    res = results[pop_name]
    target = TARGET_RATES.get(pop_name, None)

    if target is not None:
        delta_pct = ((res['avg_rate'] - target) / target) * 100
        delta_str = f"{delta_pct:+.1f}%"
    else:
        delta_str = "N/A"
        target = "N/A"

    range_str = f"{res['min_rate']:.2f} - {res['max_rate']:.2f} Hz"

    print(f"{pop_name:<15} {res['avg_rate']:>6.2f} Hz    {str(target):>6s} Hz    "
          f"{delta_str:>8s}    {range_str:<20}")

print("=" * 80)

###############################################################################
# PLOT RESULTS
###############################################################################

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Yao et al. 2022 Network Simulation Analysis', fontsize=16, fontweight='bold')

# 1. Raster plot
ax = axes[0, 0]
for pop_name in sorted(results.keys()):
    pop_data = pops[pop_name]
    cell_gids = pop_data['cellGids']

    # Get spikes for this population
    mask = np.isin(spkid, cell_gids) & (spkt >= tstart)
    pop_spkt = spkt[mask]
    pop_spkid = spkid[mask]

    ax.scatter(pop_spkt, pop_spkid, s=1, alpha=0.5, label=pop_name)

ax.set_xlabel('Time (ms)', fontsize=12)
ax.set_ylabel('Cell GID', fontsize=12)
ax.set_title('Network Raster Plot', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
ax.set_xlim([tstart, tstop])
ax.grid(alpha=0.3)

# 2. Firing rate comparison
ax = axes[0, 1]
pop_names = sorted(results.keys())
x_pos = np.arange(len(pop_names))

sim_rates = [results[pop]['avg_rate'] for pop in pop_names]
target_rates = [TARGET_RATES.get(pop, 0) for pop in pop_names]

width = 0.35
ax.bar(x_pos - width/2, sim_rates, width, label='Simulated', color='steelblue', alpha=0.8)
ax.bar(x_pos + width/2, target_rates, width, label='Target (Yao 2022)', color='coral', alpha=0.8)

ax.set_xlabel('Population', fontsize=12)
ax.set_ylabel('Firing Rate (Hz)', fontsize=12)
ax.set_title('Firing Rates: Simulated vs Target', fontsize=14, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels(pop_names, rotation=45, ha='right')
ax.legend()
ax.grid(axis='y', alpha=0.3)

# 3. Firing rate distribution (box plot)
ax = axes[1, 0]
rate_distributions = [results[pop]['rates_per_cell'] for pop in pop_names]
bp = ax.boxplot(rate_distributions, labels=pop_names, patch_artist=True)

# Color boxes
colors = ['steelblue', 'coral', 'mediumseagreen', 'orchid']
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.6)

ax.set_xlabel('Population', fontsize=12)
ax.set_ylabel('Firing Rate (Hz)', fontsize=12)
ax.set_title('Firing Rate Distribution per Population', fontsize=14, fontweight='bold')
ax.grid(axis='y', alpha=0.3)
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

# 4. Population spike histogram
ax = axes[1, 1]
bin_size = 50  # ms
bins = np.arange(tstart, tstop, bin_size)

for pop_name in sorted(results.keys()):
    pop_data = pops[pop_name]
    cell_gids = pop_data['cellGids']

    # Get spikes for this population
    mask = np.isin(spkid, cell_gids) & (spkt >= tstart) & (spkt <= tstop)
    pop_spkt = spkt[mask]

    hist, _ = np.histogram(pop_spkt, bins=bins)
    hist_rate = hist / (len(cell_gids) * (bin_size / 1000.0))  # Convert to Hz

    ax.plot(bins[:-1], hist_rate, label=pop_name, alpha=0.7, linewidth=2)

ax.set_xlabel('Time (ms)', fontsize=12)
ax.set_ylabel('Population Firing Rate (Hz)', fontsize=12)
ax.set_title('Population Activity Over Time', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
ax.grid(alpha=0.3)

plt.tight_layout()

# Save figure
output_file = sim_file.replace('.pkl', '_analysis.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n✓ Analysis figure saved to: {output_file}")

###############################################################################
# GENERATE SUMMARY REPORT
###############################################################################

report_file = sim_file.replace('.pkl', '_report.txt')

with open(report_file, 'w') as f:
    f.write("=" * 80 + "\n")
    f.write("Yao et al. 2022 Network Simulation - Analysis Report\n")
    f.write("=" * 80 + "\n\n")

    f.write(f"Simulation file: {sim_file}\n")
    f.write(f"Analysis window: {tstart} - {tstop} ms ({duration_s:.2f} s)\n")
    f.write(f"Total spikes recorded: {len(spkt)}\n\n")

    f.write("Firing Rate Summary:\n")
    f.write("-" * 80 + "\n")
    f.write(f"{'Population':<15} {'Cells':<8} {'Avg Rate':<12} {'Target':<12} "
            f"{'Δ (%)':<12} {'Std Dev':<10}\n")
    f.write("-" * 80 + "\n")

    for pop_name in sorted(results.keys()):
        res = results[pop_name]
        target = TARGET_RATES.get(pop_name, None)

        if target is not None:
            delta_pct = ((res['avg_rate'] - target) / target) * 100
            delta_str = f"{delta_pct:+.1f}%"
        else:
            delta_str = "N/A"
            target = "N/A"

        f.write(f"{pop_name:<15} {res['num_cells']:<8} {res['avg_rate']:>6.2f} Hz    "
                f"{str(target):>6s} Hz    {delta_str:>8s}    {res['std_rate']:>6.2f} Hz\n")

    f.write("=" * 80 + "\n\n")

    f.write("Model Validation:\n")
    f.write("-" * 80 + "\n")

    # Calculate overall match score
    total_error = 0
    valid_pops = 0

    for pop_name in sorted(results.keys()):
        if pop_name in TARGET_RATES:
            target = TARGET_RATES[pop_name]
            simulated = results[pop_name]['avg_rate']
            error = abs(simulated - target) / target
            total_error += error
            valid_pops += 1

            if error < 0.2:  # Within 20%
                status = "✓ EXCELLENT"
            elif error < 0.5:  # Within 50%
                status = "✓ GOOD"
            elif error < 1.0:  # Within 100%
                status = "⚠ ACCEPTABLE"
            else:
                status = "✗ NEEDS TUNING"

            f.write(f"{pop_name:<15} {status}\n")

    avg_error = (total_error / valid_pops) * 100 if valid_pops > 0 else 0

    f.write("-" * 80 + "\n")
    f.write(f"Average error: {avg_error:.1f}%\n")

    if avg_error < 20:
        f.write("Overall assessment: ✓✓ EXCELLENT MATCH\n")
    elif avg_error < 50:
        f.write("Overall assessment: ✓ GOOD MATCH\n")
    else:
        f.write("Overall assessment: ⚠ NEEDS PARAMETER TUNING\n")

    f.write("=" * 80 + "\n")

print(f"✓ Analysis report saved to: {report_file}")
print("=" * 80)
print("\n✓ Analysis complete!")

# Show plot
plt.show()
