"""
init_Yao1000.py

NetPyNE simulation initialization for Yao et al. 2022 model
1000-cell human L2/3 cortical microcircuit

Usage:
    python init_Yao1000.py                    # Full 1000-cell simulation
    python init_Yao1000.py --test             # Test with 100 cells
    python init_Yao1000.py --duration 1000    # Custom duration (ms)
    python init_Yao1000.py --record           # Record detailed variables
"""

from netpyne import sim
import numpy as np
import sys
import os
import argparse

###############################################################################
# PARSE COMMAND LINE ARGUMENTS
###############################################################################

parser = argparse.ArgumentParser(description='Run Yao 1000-cell network simulation')
parser.add_argument('--test', action='store_true', help='Run test with 100 cells')
parser.add_argument('--duration', type=float, default=4500, help='Simulation duration (ms)')
parser.add_argument('--dt', type=float, default=0.025, help='Time step (ms)')
parser.add_argument('--record', action='store_true', help='Record detailed traces')
parser.add_argument('--no-gui', action='store_true', help='Run without GUI')
parser.add_argument('--save', type=str, default='Yao1000', help='Save file prefix')
parser.add_argument('--seed', type=int, default=42, help='Random seed')

args = parser.parse_args()

###############################################################################
# IMPORT NETWORK PARAMETERS
###############################################################################

from netParams_Yao1000 import netParams, cellTypes

# Modify for test run
if args.test:
    print("=" * 80)
    print("RUNNING TEST MODE: Scaling network to 100 cells")
    print("=" * 80)
    scale_factor = 100.0 / 1000.0
    for cellType in cellTypes.keys():
        original = netParams.popParams[cellType]['numCells']
        scaled = max(1, int(original * scale_factor))
        netParams.popParams[cellType]['numCells'] = scaled
        print(f"  {cellType}: {original} → {scaled}")

###############################################################################
# SIMULATION CONFIGURATION
###############################################################################

simConfig = sim.specs.SimConfig()

# Simulation parameters
simConfig.duration = args.duration  # ms
simConfig.dt = args.dt  # ms
simConfig.verbose = False
simConfig.recordTraces = {}
simConfig.recordStep = 0.1  # ms (record at 10 kHz)
simConfig.filename = args.save
simConfig.savePickle = True
simConfig.saveJson = False
simConfig.saveDat = False
simConfig.printRunTime = 0.1  # print run time every 0.1 fraction
simConfig.seeds = {'conn': args.seed, 'stim': args.seed, 'loc': args.seed}

# Recording configuration
simConfig.recordStim = False
simConfig.recordLFP = False  # LFP recording (can be enabled later)

# Record spikes from all cells
simConfig.recordCells = []  # Record from all cells
simConfig.recordTraces = {}

if args.record:
    # Record detailed traces from sample cells
    simConfig.recordTraces = {
        'V_soma': {'sec': 'soma', 'loc': 0.5, 'var': 'v'},
    }
    # Record from 10 cells of each type
    simConfig.recordCellsSpikes = -1  # all cells
else:
    simConfig.recordCellsSpikes = -1  # Record spikes from all cells

# Analysis and plotting
simConfig.analysis = {
    'plotRaster': {
        'orderBy': 'pop',
        'timeRange': [500, args.duration],  # Exclude initial transient
        'figSize': (12, 8),
        'saveFig': args.save + '_raster.png',
        'showFig': False
    },
    'plotSpikeHist': {
        'include': ['all'],
        'timeRange': [500, args.duration],
        'binSize': 50,
        'graphType': 'bar',
        'figSize': (10, 6),
        'saveFig': args.save + '_spikehist.png',
        'showFig': False
    },
    'plotRatePSD': {
        'include': ['allCells'],
        'timeRange': [500, args.duration],
        'Fs': 200,  # sampling frequency
        'smooth': 5,
        'saveFig': args.save + '_ratePSD.png',
        'showFig': False
    },
}

# Parallel processing
simConfig.hParams = {
    'celsius': 34.0,
    'v_init': -80.0,
}

# MPI configuration (if running in parallel)
try:
    from mpi4py import MPI
    simConfig.timing = True
    print(f"Running with MPI: {MPI.COMM_WORLD.Get_size()} processes")
except:
    print("Running without MPI (single process)")

###############################################################################
# CREATE AND RUN NETWORK
###############################################################################

print("=" * 80)
print("INITIALIZING NETWORK")
print("=" * 80)
print(f"Duration: {simConfig.duration} ms")
print(f"Time step: {simConfig.dt} ms")
print(f"Temperature: {simConfig.hParams['celsius']} °C")
print(f"Random seed: {args.seed}")
print("=" * 80)

# Create network
sim.initialize(netParams, simConfig)

# Print network statistics
print("\nNetwork Statistics:")
print("-" * 80)
for popLabel, pop in sim.net.pops.items():
    print(f"{popLabel:15s}: {len(pop.cellGids):5d} cells")

print(f"\nTotal cells: {sum([len(pop.cellGids) for pop in sim.net.pops.values()])}")
print(f"Total connections: {len(sim.net.params.connParams)} connection types")
print("=" * 80)

# Set up recording
sim.setupRecording()

# Run simulation
print("\nSTARTING SIMULATION...")
print("=" * 80)

sim.runSim()

print("=" * 80)
print("SIMULATION COMPLETE")
print("=" * 80)

###############################################################################
# SAVE AND ANALYZE RESULTS
###############################################################################

# Save simulation data
print("\nSaving data...")
sim.saveData()

# Calculate firing rates for each population
print("\nFiring Rate Analysis:")
print("-" * 80)

spkts = sim.allSimData['spkt']
spkids = sim.allSimData['spkid']

# Analysis window (exclude initial transient)
tstart = 500  # ms
tstop = simConfig.duration  # ms
duration_s = (tstop - tstart) / 1000.0  # Convert to seconds

# Calculate firing rates per population
for popLabel, pop in sim.net.pops.items():
    cellGids = pop.cellGids

    # Count spikes in analysis window
    spikes_in_window = [spkts[i] for i, gid in enumerate(spkids)
                        if gid in cellGids and tstart <= spkts[i] <= tstop]

    total_spikes = len(spikes_in_window)
    num_cells = len(cellGids)

    if num_cells > 0 and duration_s > 0:
        avg_rate = total_spikes / (num_cells * duration_s)
    else:
        avg_rate = 0.0

    print(f"{popLabel:15s}: {avg_rate:6.2f} Hz (total spikes: {total_spikes})")

print("=" * 80)

# Generate plots
if not args.no_gui:
    print("\nGenerating plots...")
    sim.analysis.plotData()

print("\n✓ Simulation complete!")
print(f"✓ Data saved to: {args.save}.pkl")
print(f"✓ Figures saved with prefix: {args.save}_")
print("=" * 80)
