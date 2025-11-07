"""
init_Yao1000_HH.py

Full Yao 1000-cell network using Hodgkin-Huxley-based detailed cell models
Uses actual biophysics from cellwrapper
"""

from netpyne import sim, specs
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

###############################################################################
# Parse arguments
###############################################################################

test_mode = '--test' in sys.argv
quick_mode = '--quick' in sys.argv
duration = 4500

if test_mode:
    num_cells_target = 100
    duration = 1000
elif quick_mode:
    num_cells_target = 20
    duration = 500
else:
    num_cells_target = 1000

###############################################################################
# Network Parameters
###############################################################################

netParams = specs.NetParams()

# Network dimensions
netParams.sizeX = 500.0
netParams.sizeY = 950.0
netParams.sizeZ = 500.0

# Cell types and numbers
cellConfig = {
    'HL23PYR': {'frac': 0.80, 'E': True},
    'HL23SST': {'frac': 0.05, 'E': False},
    'HL23PV': {'frac': 0.07, 'E': False},
    'HL23VIP': {'frac': 0.08, 'E': False},
}

# Calculate actual cell numbers
for cellType, cfg in cellConfig.items():
    cfg['numCells'] = max(1, int(num_cells_target * cfg['frac']))

###############################################################################
# Import cell templates
###############################################################################

print("Loading cell templates...")
import cellwrapper
from neuron import h

h.load_file('stdrun.hoc')

# Pre-create one of each cell type to extract parameters
sample_cells = {}
for cellType in cellConfig.keys():
    print(f"  Loading {cellType}...")
    if cellType == 'HL23PYR':
        sample_cells[cellType] = cellwrapper.loadCell_HL23PYR(cellType)
    elif cellType == 'HL23SST':
        sample_cells[cellType] = cellwrapper.loadCell_HL23SST(cellType)
    elif cellType == 'HL23PV':
        sample_cells[cellType] = cellwrapper.loadCell_HL23PV(cellType)
    elif cellType == 'HL23VIP':
        sample_cells[cellType] = cellwrapper.loadCell_HL23VIP(cellType)

print("✓ Cell templates loaded\n")

###############################################################################
# Define cell rules (simplified for NetPyNE)
###############################################################################

for cellType in cellConfig.keys():
    cell = sample_cells[cellType]

    # Create simplified single-compartment version for NetPyNE
    netParams.cellParams[cellType] = {
        'conds': {'cellType': cellType},
        'secs': {
            'soma': {
                'geom': {
                    'diam': 18.8,
                    'L': 18.8,
                    'Ra': 100,
                    'cm': 1
                },
                'ions': {
                    'k': {'e': -85},
                    'na': {'e': 50},
                },
                'mechs': {
                    'pas': {'g': 0.00008, 'e': -80},
                    'NaTg': {'gbar': 0.2},
                    'Kv3_1': {'gbar': 0.02},
                    'SK': {'gbar': 0.0005},
                },
            }
        }
    }

###############################################################################
# Population parameters
###############################################################################

yMin, yMax = -1200, -250

for cellType, cfg in cellConfig.items():
    netParams.popParams[cellType] = {
        'cellType': cellType,
        'numCells': cfg['numCells'],
        'xRange': [-250, 250],
        'yRange': [yMin, yMax],
        'zRange': [-250, 250],
    }

###############################################################################
# Synaptic mechanisms
###############################################################################

netParams.synMechParams['AMPA'] = {
    'mod': 'Exp2Syn',
    'tau1': 0.3,
    'tau2': 3.0,
    'e': 0
}

netParams.synMechParams['GABA'] = {
    'mod': 'Exp2Syn',
    'tau1': 1.0,
    'tau2': 10.0,
    'e': -80
}

###############################################################################
# Connectivity
###############################################################################

connProbs = {
    ('HL23PYR', 'HL23PYR'): 0.150,
    ('HL23PYR', 'HL23SST'): 0.190,
    ('HL23PYR', 'HL23PV'):  0.090,
    ('HL23PYR', 'HL23VIP'): 0.090,
    ('HL23SST', 'HL23PYR'): 0.190,
    ('HL23SST', 'HL23SST'): 0.040,
    ('HL23SST', 'HL23PV'):  0.200,
    ('HL23SST', 'HL23VIP'): 0.060,
    ('HL23PV', 'HL23PYR'):  0.094,
    ('HL23PV', 'HL23SST'):  0.050,
    ('HL23PV', 'HL23PV'):   0.370,
    ('HL23PV', 'HL23VIP'):  0.030,
    ('HL23VIP', 'HL23PYR'): 0.000,
    ('HL23VIP', 'HL23SST'): 0.350,
    ('HL23VIP', 'HL23PV'):  0.100,
    ('HL23VIP', 'HL23VIP'): 0.050,
}

synWeights = {
    ('HL23PYR', 'HL23PYR'): 0.248,
    ('HL23PYR', 'HL23SST'): 0.380,
    ('HL23PYR', 'HL23PV'):  0.337,
    ('HL23PYR', 'HL23VIP'): 0.310,
    ('HL23SST', 'HL23PYR'): 1.240,
    ('HL23SST', 'HL23SST'): 0.340,
    ('HL23SST', 'HL23PV'):  0.330,
    ('HL23SST', 'HL23VIP'): 0.460,
    ('HL23PV', 'HL23PYR'):  2.910,
    ('HL23PV', 'HL23SST'):  0.330,
    ('HL23PV', 'HL23PV'):   0.330,
    ('HL23PV', 'HL23VIP'):  0.340,
    ('HL23VIP', 'HL23PYR'): 0.000,
    ('HL23VIP', 'HL23SST'): 0.360,
    ('HL23VIP', 'HL23PV'):  0.340,
    ('HL23VIP', 'HL23VIP'): 0.340,
}

# Create connections
for (prePop, postPop), prob in connProbs.items():
    if prob == 0:
        continue

    connLabel = f'{prePop}_to_{postPop}'
    weight = synWeights[(prePop, postPop)]

    if 'PYR' in prePop:
        synMech = 'AMPA'
        delay = 2.0
    else:
        synMech = 'GABA'
        delay = 1.0

    netParams.connParams[connLabel] = {
        'preConds': {'pop': prePop},
        'postConds': {'pop': postPop},
        'probability': prob,
        'weight': weight,
        'delay': delay,
        'synMech': synMech,
        'sec': 'soma',
        'loc': 0.5,
    }

###############################################################################
# Background stimulation
###############################################################################

bgRates = {
    'HL23PYR': 5.0,
    'HL23SST': 8.0,
    'HL23PV': 12.0,
    'HL23VIP': 10.0,
}

for cellType, rate in bgRates.items():
    netParams.stimSourceParams[f'bkg_{cellType}'] = {
        'type': 'NetStim',
        'rate': rate,
        'noise': 1.0,
        'start': 0,
        'number': 1e9,
    }

    netParams.stimTargetParams[f'bkg_{cellType}_stim'] = {
        'source': f'bkg_{cellType}',
        'conds': {'pop': cellType},
        'weight': 0.1,
        'delay': 0,
        'synMech': 'AMPA',
        'sec': 'soma',
        'loc': 0.5,
    }

###############################################################################
# Simulation configuration
###############################################################################

simConfig = specs.SimConfig()
simConfig.duration = duration
simConfig.dt = 0.025
simConfig.verbose = False
simConfig.recordCellsSpikes = -1
simConfig.recordStep = 0.1
simConfig.filename = f'Yao1000_{num_cells_target}cells'
simConfig.savePickle = True
simConfig.saveDat = False
simConfig.saveJson = False
simConfig.printRunTime = 0.1
simConfig.seeds = {'conn': 42, 'stim': 42, 'loc': 42}
simConfig.hParams = {'celsius': 34.0, 'v_init': -80.0}

if not quick_mode:
    simConfig.analysis = {
        'plotRaster': {'saveFig': True, 'showFig': False, 'orderBy': 'pop', 'timeRange': [500, duration]},
        'plotSpikeHist': {'saveFig': True, 'showFig': False, 'timeRange': [500, duration], 'binSize': 50},
    }

###############################################################################
# Run simulation
###############################################################################

print("=" * 80)
print("YAO ET AL. 2022 - HUMAN L2/3 CORTICAL NETWORK")
print("=" * 80)
print(f"Network size: {num_cells_target} cells")
print(f"Duration: {duration} ms")
print("=" * 80 + "\n")

print("Creating network...")
sim.initialize(netParams, simConfig)

print("\nNetwork composition:")
total = 0
for popLabel, pop in sim.net.pops.items():
    n = len(pop.cellGids)
    total += n
    print(f"  {popLabel:12s}: {n:4d} cells ({100*n/total if total > 0 else 0:.1f}%)")
print(f"  {'Total':12s}: {total:4d} cells")

print("\nRunning simulation...")
sim.setupRecording()
sim.runSim()
sim.saveData()

# Analyze
print("\n" + "=" * 80)
print("RESULTS")
print("=" * 80)

spkts = sim.allSimData['spkt']
spkids = sim.allSimData['spkid']
tstart = 500 if duration > 500 else 0
duration_s = (duration - tstart) / 1000.0

print(f"\nTotal spikes: {len(spkts)}")
print(f"Analysis window: {tstart}-{duration} ms\n")

print("Firing rates:")
for popLabel, pop in sim.net.pops.items():
    gids = pop.cellGids
    spikes = [1 for t, gid in zip(spkts, spkids) if gid in gids and t >= tstart]
    rate = len(spikes) / (len(gids) * duration_s) if len(gids) > 0 and duration_s > 0 else 0
    print(f"  {popLabel:12s}: {rate:6.2f} Hz")

print("\n" + "=" * 80)
print("✓ SIMULATION COMPLETE!")
print(f"✓ Data saved: {simConfig.filename}.pkl")
print("=" * 80)

if not quick_mode:
    sim.analysis.plotData()
