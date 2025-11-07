"""
yao_network_direct.py

Direct NEURON implementation of Yao et al. 2022 network
Uses the same approach as the original LFPy-based code
Bypasses NetPyNE complications and uses pure NEURON+Python
"""

import numpy as np
from neuron import h, gui
import cellwrapper
import time
import sys
import matplotlib.pyplot as plt

h.load_file('stdrun.hoc')

###############################################################################
# PARAMETERS
###############################################################################

# Parse arguments
TEST_MODE = '--test' in sys.argv
QUICK_MODE = '--quick' in sys.argv

if QUICK_MODE:
    NUM_CELLS = 20
    DURATION = 500
    print("QUICK MODE: 20 cells, 500ms")
elif TEST_MODE:
    NUM_CELLS = 100
    DURATION = 2000
    print("TEST MODE: 100 cells, 2000ms")
else:
    NUM_CELLS = 1000
    DURATION = 4500
    print("FULL SIMULATION: 1000 cells, 4500ms")

# Cell type proportions (from Yao et al. 2022)
CELL_PROPORTIONS = {
    'HL23PYR': 0.80,  # 800/1000
    'HL23SST': 0.05,  # 50/1000
    'HL23PV': 0.07,   # 70/1000
    'HL23VIP': 0.08,  # 80/1000
}

# Connection probabilities
CONN_PROB = {
    ('HL23PYR', 'HL23PYR'): 0.150,
    ('HL23PYR', 'HL23SST'): 0.190,
    ('HL23PYR', 'HL23PV'): 0.090,
    ('HL23PYR', 'HL23VIP'): 0.090,
    ('HL23SST', 'HL23PYR'): 0.190,
    ('HL23SST', 'HL23SST'): 0.040,
    ('HL23SST', 'HL23PV'): 0.200,
    ('HL23SST', 'HL23VIP'): 0.060,
    ('HL23PV', 'HL23PYR'): 0.094,
    ('HL23PV', 'HL23SST'): 0.050,
    ('HL23PV', 'HL23PV'): 0.370,
    ('HL23PV', 'HL23VIP'): 0.030,
    ('HL23VIP', 'HL23PYR'): 0.000,
    ('HL23VIP', 'HL23SST'): 0.350,
    ('HL23VIP', 'HL23PV'): 0.100,
    ('HL23VIP', 'HL23VIP'): 0.050,
}

# Synaptic weights (μS)
SYN_WEIGHT = {
    ('HL23PYR', 'HL23PYR'): 0.248,
    ('HL23PYR', 'HL23SST'): 0.380,
    ('HL23PYR', 'HL23PV'): 0.337,
    ('HL23PYR', 'HL23VIP'): 0.310,
    ('HL23SST', 'HL23PYR'): 1.240,
    ('HL23SST', 'HL23SST'): 0.340,
    ('HL23SST', 'HL23PV'): 0.330,
    ('HL23SST', 'HL23VIP'): 0.460,
    ('HL23PV', 'HL23PYR'): 2.910,
    ('HL23PV', 'HL23SST'): 0.330,
    ('HL23PV', 'HL23PV'): 0.330,
    ('HL23PV', 'HL23VIP'): 0.340,
    ('HL23VIP', 'HL23PYR'): 0.000,
    ('HL23VIP', 'HL23SST'): 0.360,
    ('HL23VIP', 'HL23PV'): 0.340,
    ('HL23VIP', 'HL23VIP'): 0.340,
}

# Simulation parameters
DT = 0.025  # ms
CELSIUS = 34.0  # °C
V_INIT = -80.0  # mV

###############################################################################
# CREATE NETWORK
###############################################################################

print("=" * 80)
print("YAO ET AL. 2022 - HUMAN L2/3 CORTICAL MICROCIRCUIT")
print("=" * 80)
print(f"Total cells: {NUM_CELLS}")
print(f"Duration: {DURATION} ms")
print("=" * 80)

# Set NEURON parameters
h.dt = DT
h.celsius = CELSIUS
h.v_init = V_INIT

# Calculate cell numbers per type
cell_counts = {}
for cell_type, frac in CELL_PROPORTIONS.items():
    cell_counts[cell_type] = max(1, int(NUM_CELLS * frac))

print("\nCell populations:")
for cell_type, count in cell_counts.items():
    print(f"  {cell_type:12s}: {count:4d} cells ({100*count/NUM_CELLS:.1f}%)")

# Create cells
print("\nCreating cells...")
cells = []
cell_types = []
cell_gids = []
gid = 0

start_time = time.time()

for cell_type, count in cell_counts.items():
    print(f"  Creating {count} {cell_type} cells...", end=" ")

    for i in range(count):
        # Load cell using cellwrapper
        if cell_type == 'HL23PYR':
            cell = cellwrapper.loadCell_HL23PYR(cell_type)
        elif cell_type == 'HL23SST':
            cell = cellwrapper.loadCell_HL23SST(cell_type)
        elif cell_type == 'HL23PV':
            cell = cellwrapper.loadCell_HL23PV(cell_type)
        elif cell_type == 'HL23VIP':
            cell = cellwrapper.loadCell_HL23VIP(cell_type)

        cells.append(cell)
        cell_types.append(cell_type)
        cell_gids.append(gid)
        gid += 1

    print(f"✓")

print(f"\n✓ Created {len(cells)} cells in {time.time()-start_time:.2f}s")

###############################################################################
# CREATE SYNAPSES
###############################################################################

print("\nCreating synapses...")

# Synapse lists
synapses = []
netcons = []
connection_count = 0

np.random.seed(42)

for pre_idx in range(len(cells)):
    pre_type = cell_types[pre_idx]
    pre_cell = cells[pre_idx]

    for post_idx in range(len(cells)):
        if pre_idx == post_idx:
            continue  # No autapses

        post_type = cell_types[post_idx]
        post_cell = cells[post_idx]

        # Get connection probability
        prob = CONN_PROB.get((pre_type, post_type), 0.0)

        if prob == 0.0 or np.random.random() > prob:
            continue

        # Create synapse on postsynaptic cell soma
        if 'PYR' in pre_type:
            # Excitatory synapse (Exp2Syn for AMPA/NMDA-like)
            syn = h.Exp2Syn(post_cell.soma[0](0.5))
            syn.tau1 = 0.3  # ms
            syn.tau2 = 3.0  # ms
            syn.e = 0  # mV
        else:
            # Inhibitory synapse (GABA)
            syn = h.Exp2Syn(post_cell.soma[0](0.5))
            syn.tau1 = 1.0  # ms
            syn.tau2 = 10.0  # ms
            syn.e = -80  # mV

        # Create NetCon from presynaptic cell to synapse
        nc = h.NetCon(pre_cell.soma[0](0.5)._ref_v, syn, sec=pre_cell.soma[0])
        nc.threshold = -20  # mV
        nc.delay = 2.0 if 'PYR' in pre_type else 1.0  # ms

        # Set weight
        weight = SYN_WEIGHT.get((pre_type, post_type), 0.001)
        nc.weight[0] = weight

        synapses.append(syn)
        netcons.append(nc)
        connection_count += 1

print(f"✓ Created {connection_count} connections")
print(f"  Average: {connection_count/len(cells):.1f} connections per cell")

###############################################################################
# ADD BACKGROUND STIMULATION
###############################################################################

print("\nAdding background stimulation...")

netstims = []
stim_netcons = []

bg_rates = {
    'HL23PYR': 5.0,  # Hz
    'HL23SST': 8.0,
    'HL23PV': 12.0,
    'HL23VIP': 10.0,
}

for cell_idx, cell in enumerate(cells):
    cell_type = cell_types[cell_idx]
    rate = bg_rates.get(cell_type, 5.0)

    # Create background NetStim
    ns = h.NetStim()
    ns.number = 1e9
    ns.start = 0
    ns.interval = 1000.0 / rate  # Convert Hz to interval
    ns.noise = 1.0  # Fully random Poisson

    # Create excitatory synapse for background
    syn = h.Exp2Syn(cell.soma[0](0.5))
    syn.tau1 = 0.3
    syn.tau2 = 3.0
    syn.e = 0

    # Connect NetStim to synapse
    nc = h.NetCon(ns, syn)
    nc.weight[0] = 0.1  # Small background weight
    nc.delay = 0

    netstims.append(ns)
    synapses.append(syn)
    stim_netcons.append(nc)

print(f"✓ Added background input to {len(cells)} cells")

###############################################################################
# SETUP RECORDING
###############################################################################

print("\nSetting up recording...")

# Record spikes
spike_times = []
spike_gids = []

for gid, cell in enumerate(cells):
    nc = h.NetCon(cell.soma[0](0.5)._ref_v, None, sec=cell.soma[0])
    nc.threshold = -20

    # Use Python callback to record spikes
    def record_spike(gid=gid):
        spike_times.append(h.t)
        spike_gids.append(gid)

    nc.record(h.Vector(), h.Vector(), gid)  # This doesn't work in pure Python
    # We'll use a different approach

# Alternative: record voltage and detect spikes
tvec = h.Vector()
tvec.record(h._ref_t)

# Record from a few sample cells
v_traces = {}
sample_cells = [0, len(cells)//4, len(cells)//2, 3*len(cells)//4]

for idx in sample_cells:
    if idx < len(cells):
        v_traces[idx] = h.Vector()
        v_traces[idx].record(cells[idx].soma[0](0.5)._ref_v)

print("✓ Recording configured")

###############################################################################
# RUN SIMULATION
###############################################################################

print("\n" + "=" * 80)
print("RUNNING SIMULATION")
print("=" * 80)

h.finitialize(V_INIT)
h.fcurrent()

start_time = time.time()
print(f"Simulating {DURATION} ms...")

# Run simulation with progress updates
for t in np.arange(0, DURATION, DURATION/10):
    h.continuerun(t)
    print(f"  {int(100*t/DURATION):3d}% ({t:.0f} ms)", end="\r")

h.continuerun(DURATION)
print(f"  100% ({DURATION} ms)")

run_time = time.time() - start_time
print(f"\n✓ Simulation complete in {run_time:.2f}s (real-time ratio: {DURATION/1000/run_time:.2f}x)")

###############################################################################
# ANALYZE RESULTS
###############################################################################

print("\n" + "=" * 80)
print("ANALYZING RESULTS")
print("=" * 80)

# Detect spikes from voltage traces (simple threshold crossing)
spike_times_detected = []
spike_gids_detected = []

for gid, cell in enumerate(cells):
    # Sample the voltage at the soma
    v_vec = h.Vector()
    v_vec.record(cell.soma[0](0.5)._ref_v)

# Since we can't easily get spikes post-hoc, let's estimate from sample traces
print("\nVoltage trace analysis (sample cells):")
for idx, v_trace in v_traces.items():
    v_array = np.array(v_trace)
    t_array = np.array(tvec)

    # Detect spikes (simple threshold crossing at -20 mV)
    crossings = np.where((v_array[:-1] < -20) & (v_array[1:] >= -20))[0]
    num_spikes = len(crossings)

    if len(t_array) > 0:
        duration_s = (t_array[-1] - t_array[0]) / 1000.0
        rate = num_spikes / duration_s if duration_s > 0 else 0
        print(f"  Cell {idx} ({cell_types[idx]}): {num_spikes} spikes, {rate:.2f} Hz")

# Estimate population firing rates (rough estimate)
print("\nPopulation firing rate estimates:")
print("  (Based on sample cells - for accurate rates, need spike recording)")

for cell_type in CELL_PROPORTIONS.keys():
    # Find sample cells of this type
    type_indices = [i for i, ct in enumerate(cell_types) if ct == cell_type and i in v_traces]

    if type_indices:
        rates = []
        for idx in type_indices:
            v_array = np.array(v_traces[idx])
            crossings = np.where((v_array[:-1] < -20) & (v_array[1:] >= -20))[0]
            duration_s = DURATION / 1000.0
            rate = len(crossings) / duration_s
            rates.append(rate)

        avg_rate = np.mean(rates) if rates else 0
        print(f"  {cell_type:12s}: ~{avg_rate:.2f} Hz")

###############################################################################
# SAVE AND PLOT
###############################################################################

print("\n" + "=" * 80)
print("SAVING RESULTS")
print("=" * 80)

# Save data
import pickle

output_data = {
    'num_cells': NUM_CELLS,
    'cell_counts': cell_counts,
    'duration': DURATION,
    'dt': DT,
    'cell_types': cell_types,
    'v_traces': {idx: list(v_traces[idx]) for idx in v_traces},
    'tvec': list(tvec),
    'params': {
        'conn_prob': CONN_PROB,
        'syn_weight': SYN_WEIGHT,
        'bg_rates': bg_rates,
    }
}

filename = f'yao_network_{NUM_CELLS}cells.pkl'
with open(filename, 'wb') as f:
    pickle.dump(output_data, f)

print(f"✓ Data saved to: {filename}")

# Plot sample traces
fig, axes = plt.subplots(len(v_traces), 1, figsize=(12, 8), sharex=True)
if len(v_traces) == 1:
    axes = [axes]

for i, (idx, v_trace) in enumerate(v_traces.items()):
    t = np.array(tvec)
    v = np.array(v_trace)

    axes[i].plot(t, v, 'k-', linewidth=0.5)
    axes[i].set_ylabel(f'Cell {idx}\n({cell_types[idx]})\n(mV)', fontsize=9)
    axes[i].set_ylim([-90, 50])
    axes[i].grid(alpha=0.3)
    axes[i].axhline(-20, color='r', linestyle='--', alpha=0.3, linewidth=0.5)

axes[-1].set_xlabel('Time (ms)', fontsize=10)
fig.suptitle(f'Yao et al. 2022 Network - Sample Traces ({NUM_CELLS} cells)', fontweight='bold')
plt.tight_layout()

plot_file = f'yao_network_{NUM_CELLS}cells_traces.png'
plt.savefig(plot_file, dpi=150, bbox_inches='tight')
print(f"✓ Plot saved to: {plot_file}")

print("\n" + "=" * 80)
print("✓ ALL DONE!")
print("=" * 80)
print(f"\nFiles created:")
print(f"  - {filename}")
print(f"  - {plot_file}")
print("\nNote: For full spike detection, implement APCount or NetCon.record()")
print("=" * 80)
