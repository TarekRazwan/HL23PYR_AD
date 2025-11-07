"""
netParams_Yao1000.py

NetPyNE network parameters for 1000-cell human L2/3 cortical microcircuit
Replicating: Yao et al. (2022) Cell Reports
"Reduced inhibition in depression impairs stimulus processing in human cortical microcircuits"

Network composition:
- 800 HL23PYR (Pyramidal, excitatory)
- 50 HL23SST (Somatostatin interneurons)
- 70 HL23PV (Parvalbumin interneurons)
- 80 HL23VIP (VIP interneurons)

Volume: 500x500x950 μm³ (L2/3, 250-1200 μm below pia)
"""

from netpyne import specs
import numpy as np

netParams = specs.NetParams()

###############################################################################
# NETWORK PARAMETERS
###############################################################################

# Spatial parameters (cylindrical distribution)
netParams.sizeX = 500.0  # μm
netParams.sizeY = 950.0  # μm (depth: 250-1200 μm below pia)
netParams.sizeZ = 500.0  # μm

# Conversion factor for determining network volume
netParams.shape = 'cylinder'  # cylindrical column
netParams.radius = 250.0  # μm (500 μm diameter)

###############################################################################
# CELL PARAMETERS
###############################################################################

# Import existing cell rules from cellwrapper
import sys
import os
cellwrapper_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, cellwrapper_path)

# Define cell types with their proportions
cellTypes = {
    'HL23PYR': {'numCells': 800, 'fracE': 1.0},  # Excitatory
    'HL23SST': {'numCells': 50, 'fracE': 0.0},   # Inhibitory
    'HL23PV': {'numCells': 70, 'fracE': 0.0},    # Inhibitory
    'HL23VIP': {'numCells': 80, 'fracE': 0.0}    # Inhibitory
}

# Define cell parameters using .hoc templates
# NetPyNE will load these via NEURON's template system
for cellType in cellTypes.keys():
    morphpath = os.path.join(cellwrapper_path, 'morphologies', cellType + '.swc')
    templatepath = os.path.join(cellwrapper_path, 'models', 'NeuronTemplate_' + cellType + '.hoc')

    netParams.cellParams[cellType + '_rule'] = {
        'conds': {'cellType': cellType},
        'secs': {},  # Will be imported from HOC template
        'secLists': {},
    }

###############################################################################
# POPULATION PARAMETERS
###############################################################################

# Spatial distribution: cylindrical column in L2/3
# Y-axis is depth (vertical), centered around -725 μm (midpoint of 250-1200)
yMin = -1200  # μm below pia
yMax = -250   # μm below pia
yCenter = (yMin + yMax) / 2.0  # -725 μm

for cellType, params in cellTypes.items():
    netParams.popParams[cellType] = {
        'cellType': cellType,
        'numCells': params['numCells'],
        'cellModel': 'HH_full',
        'xRange': [-250, 250],  # Centered at 0, radius 250
        'yRange': [yMin, yMax],
        'zRange': [-250, 250],
        'xnormRange': [0.0, 1.0],
        'ynormRange': [0.0, 1.0],
        'znormRange': [0.0, 1.0],
    }

###############################################################################
# SYNAPTIC MECHANISMS
###############################################################################

# AMPA/NMDA synapses (excitatory)
netParams.synMechParams['AMPA'] = {
    'mod': 'Exp2Syn',
    'tau1': 0.3,   # rise time (ms)
    'tau2': 3.0,   # decay time (ms)
    'e': 0         # reversal potential (mV)
}

netParams.synMechParams['NMDA'] = {
    'mod': 'Exp2Syn',
    'tau1': 2.0,   # rise time (ms)
    'tau2': 65.0,  # decay time (ms)
    'e': 0         # reversal potential (mV)
}

# GABA synapses (inhibitory)
netParams.synMechParams['GABA'] = {
    'mod': 'Exp2Syn',
    'tau1': 1.0,   # rise time (ms)
    'tau2': 10.0,  # decay time (ms)
    'e': -80       # reversal potential (mV)
}

###############################################################################
# CONNECTIVITY PARAMETERS
###############################################################################

# Connection probability matrix (16 connections)
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

    ('HL23VIP', 'HL23PYR'): 0.000,  # No VIP → PYR connections
    ('HL23VIP', 'HL23SST'): 0.350,
    ('HL23VIP', 'HL23PV'):  0.100,
    ('HL23VIP', 'HL23VIP'): 0.050,
}

# Synaptic conductances (S) - peak conductance values
synConds = {
    ('HL23PYR', 'HL23PYR'): 0.000248,
    ('HL23PYR', 'HL23SST'): 0.000380,
    ('HL23PYR', 'HL23PV'):  0.000337,
    ('HL23PYR', 'HL23VIP'): 0.000310,

    ('HL23SST', 'HL23PYR'): 0.001240,
    ('HL23SST', 'HL23SST'): 0.000340,
    ('HL23SST', 'HL23PV'):  0.000330,
    ('HL23SST', 'HL23VIP'): 0.000460,

    ('HL23PV', 'HL23PYR'):  0.002910,
    ('HL23PV', 'HL23SST'):  0.000330,
    ('HL23PV', 'HL23PV'):   0.000330,
    ('HL23PV', 'HL23VIP'):  0.000340,

    ('HL23VIP', 'HL23PYR'): 0.000000,
    ('HL23VIP', 'HL23SST'): 0.000360,
    ('HL23VIP', 'HL23PV'):  0.000340,
    ('HL23VIP', 'HL23VIP'): 0.000340,
}

# Number of synaptic contacts per connection
numContacts = {
    ('HL23PYR', 'HL23PYR'): 3,
    ('HL23PYR', 'HL23SST'): 8,
    ('HL23PYR', 'HL23PV'):  8,
    ('HL23PYR', 'HL23VIP'): 4,

    ('HL23SST', 'HL23PYR'): 12,
    ('HL23SST', 'HL23SST'): 12,
    ('HL23SST', 'HL23PV'):  13,
    ('HL23SST', 'HL23VIP'): 5,

    ('HL23PV', 'HL23PYR'):  17,
    ('HL23PV', 'HL23SST'):  16,
    ('HL23PV', 'HL23PV'):   15,
    ('HL23PV', 'HL23VIP'):  7,

    ('HL23VIP', 'HL23PYR'): 0,
    ('HL23VIP', 'HL23SST'): 9,
    ('HL23VIP', 'HL23PV'):  11,
    ('HL23VIP', 'HL23VIP'): 7,
}

# Short-term plasticity: Depression time constant (ms)
Depression = {
    ('HL23PYR', 'HL23PYR'): 670,
    ('HL23PYR', 'HL23SST'): 140,
    ('HL23PYR', 'HL23PV'):  510,
    ('HL23PYR', 'HL23VIP'): 670,

    ('HL23SST', 'HL23PYR'): 1300,
    ('HL23SST', 'HL23SST'): 720,
    ('HL23SST', 'HL23PV'):  710,
    ('HL23SST', 'HL23VIP'): 890,

    ('HL23PV', 'HL23PYR'):  710,
    ('HL23PV', 'HL23SST'):  700,
    ('HL23PV', 'HL23PV'):   710,
    ('HL23PV', 'HL23VIP'):  720,

    ('HL23VIP', 'HL23PYR'): 300,
    ('HL23VIP', 'HL23SST'): 760,
    ('HL23VIP', 'HL23PV'):  720,
    ('HL23VIP', 'HL23VIP'): 720,
}

# Short-term plasticity: Facilitation (not used in Yao model, set to large values)
Facilitation = {
    ('HL23PYR', 'HL23PYR'): 17,
    ('HL23PYR', 'HL23SST'): 670,
    ('HL23PYR', 'HL23PV'):  326,
    ('HL23PYR', 'HL23VIP'): 329,

    ('HL23SST', 'HL23PYR'): 1100,
    ('HL23SST', 'HL23SST'): 1000,
    ('HL23SST', 'HL23PV'):  1000,
    ('HL23SST', 'HL23VIP'): 1000,

    ('HL23PV', 'HL23PYR'):  1000,
    ('HL23PV', 'HL23SST'):  1000,
    ('HL23PV', 'HL23PV'):   1000,
    ('HL23PV', 'HL23VIP'):  1000,

    ('HL23VIP', 'HL23PYR'): 1000,
    ('HL23VIP', 'HL23SST'): 1000,
    ('HL23VIP', 'HL23PV'):  1000,
    ('HL23VIP', 'HL23VIP'): 1000,
}

# Short-term plasticity: Use parameter (release probability)
Use = {
    ('HL23PYR', 'HL23PYR'): 0.46,
    ('HL23PYR', 'HL23SST'): 0.09,
    ('HL23PYR', 'HL23PV'):  0.88,
    ('HL23PYR', 'HL23VIP'): 0.50,

    ('HL23SST', 'HL23PYR'): 0.30,
    ('HL23SST', 'HL23SST'): 0.25,
    ('HL23SST', 'HL23PV'):  0.25,
    ('HL23SST', 'HL23VIP'): 0.31,

    ('HL23PV', 'HL23PYR'):  0.08,
    ('HL23PV', 'HL23SST'):  0.25,
    ('HL23PV', 'HL23PV'):   0.25,
    ('HL23PV', 'HL23VIP'):  0.26,

    ('HL23VIP', 'HL23PYR'): 0.23,
    ('HL23VIP', 'HL23SST'): 0.27,
    ('HL23VIP', 'HL23PV'):  0.25,
    ('HL23VIP', 'HL23VIP'): 0.26,
}

###############################################################################
# CONNECTIVITY RULES
###############################################################################

# Define all 16 connection types
preCellTypes = ['HL23PYR', 'HL23SST', 'HL23PV', 'HL23VIP']
postCellTypes = ['HL23PYR', 'HL23SST', 'HL23PV', 'HL23VIP']

for prePop in preCellTypes:
    for postPop in postCellTypes:

        connKey = (prePop, postPop)
        prob = connProbs[connKey]

        if prob == 0.0:
            continue  # Skip connections with zero probability

        # Determine synapse type based on presynaptic cell
        if 'PYR' in prePop:
            synMech = 'AMPA'  # Excitatory connections use AMPA
            synMechFraction = {'AMPA': 0.8, 'NMDA': 0.2}  # AMPA:NMDA ratio
        else:
            synMech = 'GABA'  # Inhibitory connections
            synMechFraction = {'GABA': 1.0}

        # Connection rule name
        connLabel = f'{prePop}_to_{postPop}'

        # Weight (convert conductance to NetPyNE weight)
        # NetPyNE weight = conductance (μS) * 1000 for conversion
        weight = synConds[connKey] * 1e6  # Convert S to μS

        # Create connectivity rule
        if 'PYR' in prePop:
            # Excitatory connections: use both AMPA and NMDA
            netParams.connParams[connLabel + '_AMPA'] = {
                'preConds': {'pop': prePop},
                'postConds': {'pop': postPop},
                'probability': prob,
                'weight': weight * 0.8,  # 80% AMPA
                'delay': 2.0,  # ms (axonal + synaptic delay)
                'synMech': 'AMPA',
                'sec': 'soma',  # Will be distributed properly in detailed model
                'loc': 0.5,
            }

            netParams.connParams[connLabel + '_NMDA'] = {
                'preConds': {'pop': prePop},
                'postConds': {'pop': postPop},
                'probability': prob,
                'weight': weight * 0.2,  # 20% NMDA
                'delay': 2.0,
                'synMech': 'NMDA',
                'sec': 'soma',
                'loc': 0.5,
            }
        else:
            # Inhibitory connections: use GABA only
            netParams.connParams[connLabel] = {
                'preConds': {'pop': prePop},
                'postConds': {'pop': postPop},
                'probability': prob,
                'weight': weight,
                'delay': 1.0,  # ms (faster inhibitory transmission)
                'synMech': 'GABA',
                'sec': 'soma',
                'loc': 0.5,
            }

###############################################################################
# BACKGROUND STIMULATION
###############################################################################

# Background excitatory input (tonic drive simulating cortical/thalamic input)
# From Yao model: different cell types receive different numbers of background inputs

bgStim = {
    'HL23PYR': {'numStims': 55, 'weight': 0.004, 'rate': 10.0},
    'HL23PV':  {'numStims': 35, 'weight': 0.002, 'rate': 10.0},
    'HL23VIP': {'numStims': 65, 'weight': 0.0022, 'rate': 10.0},
    'HL23SST': {'numStims': 40, 'weight': 0.003, 'rate': 10.0},  # Estimated
}

for cellType, params in bgStim.items():

    # Create NetStim for background input
    netParams.stimSourceParams[f'bkg_{cellType}'] = {
        'type': 'NetStim',
        'rate': params['rate'],  # Hz
        'noise': 1.0,  # Poisson noise (fully random)
        'start': 0,
        'number': 1e9,  # Effectively continuous
    }

    # Connect background stimulus to population
    netParams.stimTargetParams[f'bkg_{cellType}_stim'] = {
        'source': f'bkg_{cellType}',
        'conds': {'pop': cellType},
        'weight': params['weight'] * 1e6,  # Convert to μS
        'delay': 0,
        'synMech': 'AMPA',
        'sec': 'soma',
        'loc': 0.5,
    }

###############################################################################
# SIMULATION CONFIGURATION
###############################################################################

netParams.defaultThreshold = -20.0  # mV (spike detection threshold)

# Biophysical parameters
netParams.defaultTemp = 34.0  # Celsius (body temperature)
netParams.defaultV = -80.0    # mV (initial membrane potential)

print("=" * 80)
print("NetPyNE Network Parameters: Yao et al. 2022 (1000 cells)")
print("=" * 80)
print(f"Total cells: {sum([p['numCells'] for p in cellTypes.values()])}")
print(f"  - HL23PYR: {cellTypes['HL23PYR']['numCells']}")
print(f"  - HL23SST: {cellTypes['HL23SST']['numCells']}")
print(f"  - HL23PV: {cellTypes['HL23PV']['numCells']}")
print(f"  - HL23VIP: {cellTypes['HL23VIP']['numCells']}")
print(f"Connection types: {len([k for k in connProbs.keys() if connProbs[k] > 0])}")
print(f"Network volume: {netParams.sizeX}x{netParams.sizeY}x{netParams.sizeZ} μm³")
print("=" * 80)
