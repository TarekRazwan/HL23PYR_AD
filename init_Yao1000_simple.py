"""
init_Yao1000_simple.py

Simple version using Izhikevich point neurons
Good for quick testing before moving to detailed morphologies
"""

from netpyne import sim
import sys

###############################################################################
# Parse arguments
###############################################################################

test_mode = '--test' in sys.argv
duration = 4500 if not test_mode else 1000

###############################################################################
# Import network
###############################################################################

from netParams_Yao1000_v2 import netParams, cellTypes

if test_mode:
    print("=" * 80)
    print("TEST MODE: Scaling to 100 cells")
    print("=" * 80)
    scale_factor = 100.0 / 1000.0
    for cellType in cellTypes.keys():
        original = netParams.popParams[cellType]['numCells']
        scaled = max(1, int(original * scale_factor))
        netParams.popParams[cellType]['numCells'] = scaled
        print(f"  {cellType}: {original} → {scaled}")

###############################################################################
# Simulation config
###############################################################################

simConfig = sim.specs.SimConfig()
simConfig.duration = duration
simConfig.dt = 0.025
simConfig.verbose = False
simConfig.recordCellsSpikes = -1
simConfig.recordStep = 0.1
simConfig.filename = 'Yao1000_simple_test' if test_mode else 'Yao1000_simple'
simConfig.savePickle = True
simConfig.printRunTime = 0.1
simConfig.seeds = {'conn': 42, 'stim': 42, 'loc': 42}

simConfig.analysis = {
    'plotRaster': {
        'orderBy': 'pop',
        'timeRange': [500, duration],
        'figSize': (12, 8),
        'saveFig': True,
        'showFig': False
    },
    'plotSpikeHist': {
        'include': ['all'],
        'timeRange': [500, duration],
        'binSize': 50,
        'saveFig': True,
        'showFig': False
    },
}

###############################################################################
# Run simulation
###############################################################################

print("=" * 80)
print("YAOET AL. 2022 NETWORK SIMULATION")
print("=" * 80)
print(f"Duration: {duration} ms")
print("=" * 80)

sim.initialize(netParams, simConfig)

print("\nNetwork Statistics:")
for popLabel, pop in sim.net.pops.items():
    print(f"{popLabel:15s}: {len(pop.cellGids):5d} cells")
print(f"Total: {sum([len(p.cellGids) for p in sim.net.pops.values()])} cells")

sim.setupRecording()
sim.runSim()
sim.saveData()

# Calculate firing rates
print("\n" + "=" * 80)
print("FIRING RATE ANALYSIS")
print("=" * 80)

spkts = sim.allSimData['spkt']
spkids = sim.allSimData['spkid']
tstart = 500
tstop = duration
duration_s = (tstop - tstart) / 1000.0

for popLabel, pop in sim.net.pops.items():
    cellGids = pop.cellGids
    spikes = [t for t, gid in zip(spkts, spkids) if gid in cellGids and tstart <= t <= tstop]
    if len(cellGids) > 0:
        rate = len(spikes) / (len(cellGids) * duration_s)
        print(f"{popLabel:15s}: {rate:6.2f} Hz")

print("=" * 80)
print("SIMULATION COMPLETE!")
print(f"Data saved to: {simConfig.filename}.pkl")
print("=" * 80)

sim.analysis.plotData()
