"""
netParams_Yao1000_v2.py

NetPyNE network parameters for 1000-cell human L2/3 cortical microcircuit
Replicating: Yao et al. (2022) Cell Reports

Simplified version using point neurons initially, can be upgraded to detailed morphologies
"""

from netpyne import specs
import numpy as np

netParams = specs.NetParams()

###############################################################################
# NETWORK PARAMETERS
###############################################################################

netParams.sizeX = 500.0  # μm
netParams.sizeY = 950.0  # μm depth
netParams.sizeZ = 500.0  # μm

###############################################################################
# CELL PARAMETERS (Point Neuron Models)
###############################################################################

# Cell type definitions
cellTypes = {
    'HL23PYR': {'numCells': 800, 'C': 1.0, 'k': 0.7, 'vr': -60, 'vt': -40, 'vpeak': 35, 'a': 0.03, 'b': -2, 'c': -50, 'd': 100},
    'HL23SST': {'numCells': 50, 'C': 0.8, 'k': 0.7, 'vr': -60, 'vt': -40, 'vpeak': 35, 'a': 0.1, 'b': 0.2, 'c': -60, 'd': 2},
    'HL23PV': {'numCells': 70, 'C': 0.5, 'k': 0.5, 'vr': -60, 'vt': -40, 'vpeak': 35, 'a': 0.2, 'b': 0.025, 'c': -55, 'd': 2},
    'HL23VIP': {'numCells': 80, 'C': 0.6, 'k': 0.6, 'vr': -60, 'vt': -40, 'vpeak': 35, 'a': 0.15, 'b': 0.1, 'c': -58, 'd': 2},
}

# Define cell rules using Izhikevich model
for cellType, params in cellTypes.items():
    netParams.cellParams[cellType + '_rule'] = {
        'conds': {'cellType': cellType},
        'secs': {
            'soma': {
                'geom': {'diam': 18.8, 'L': 18.8, 'Ra': 123.0},
                'mechs': {},
                'pointps': {
                    'Izhi': {
                        'mod': 'Izhi2007b',
                        'C': params['C'],
                        'k': params['k'],
                        'vr': params['vr'],
                        'vt': params['vt'],
                        'vpeak': params['vpeak'],
                        'a': params['a'],
                        'b': params['b'],
                        'c': params['c'],
                        'd': params['d'],
                        'celltype': 1 if 'PYR' in cellType else 2,
                    }
                }
            }
        }
    }

###############################################################################
# POPULATION PARAMETERS
###############################################################################

yMin = -1200
yMax = -250

for cellType, params in cellTypes.items():
    netParams.popParams[cellType] = {
        'cellType': cellType,
        'numCells': params['numCells'],
        'cellModel': 'Izhi2007b',
        'xRange': [-250, 250],
        'yRange': [yMin, yMax],
        'zRange': [-250, 250],
    }

###############################################################################
# SYNAPTIC MECHANISMS
###############################################################################

netParams.synMechParams['AMPA'] = {
    'mod': 'Exp2Syn',
    'tau1': 0.3,
    'tau2': 3.0,
    'e': 0
}

netParams.synMechParams['NMDA'] = {
    'mod': 'Exp2Syn',
    'tau1': 2.0,
    'tau2': 65.0,
    'e': 0
}

netParams.synMechParams['GABA'] = {
    'mod': 'Exp2Syn',
    'tau1': 1.0,
    'tau2': 10.0,
    'e': -80
}

###############################################################################
# CONNECTIVITY PARAMETERS
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

###############################################################################
# CONNECTIVITY RULES
###############################################################################

preCellTypes = ['HL23PYR', 'HL23SST', 'HL23PV', 'HL23VIP']
postCellTypes = ['HL23PYR', 'HL23SST', 'HL23PV', 'HL23VIP']

for prePop in preCellTypes:
    for postPop in postCellTypes:
        connKey = (prePop, postPop)
        prob = connProbs[connKey]

        if prob == 0.0:
            continue

        weight = synConds[connKey] * 1e6  # Convert S to μS

        connLabel = f'{prePop}_to_{postPop}'

        if 'PYR' in prePop:
            # Excitatory: AMPA + NMDA
            netParams.connParams[connLabel + '_AMPA'] = {
                'preConds': {'pop': prePop},
                'postConds': {'pop': postPop},
                'probability': prob,
                'weight': weight * 0.8,
                'delay': 2.0,
                'synMech': 'AMPA',
                'sec': 'soma',
                'loc': 0.5,
            }

            netParams.connParams[connLabel + '_NMDA'] = {
                'preConds': {'pop': prePop},
                'postConds': {'pop': postPop},
                'probability': prob,
                'weight': weight * 0.2,
                'delay': 2.0,
                'synMech': 'NMDA',
                'sec': 'soma',
                'loc': 0.5,
            }
        else:
            # Inhibitory: GABA
            netParams.connParams[connLabel] = {
                'preConds': {'pop': prePop},
                'postConds': {'pop': postPop},
                'probability': prob,
                'weight': weight,
                'delay': 1.0,
                'synMech': 'GABA',
                'sec': 'soma',
                'loc': 0.5,
            }

###############################################################################
# BACKGROUND STIMULATION
###############################################################################

bgStim = {
    'HL23PYR': {'rate': 10.0, 'weight': 0.004},
    'HL23PV':  {'rate': 10.0, 'weight': 0.002},
    'HL23VIP': {'rate': 10.0, 'weight': 0.0022},
    'HL23SST': {'rate': 10.0, 'weight': 0.003},
}

for cellType, params in bgStim.items():
    netParams.stimSourceParams[f'bkg_{cellType}'] = {
        'type': 'NetStim',
        'rate': params['rate'],
        'noise': 1.0,
        'start': 0,
        'number': 1e9,
    }

    netParams.stimTargetParams[f'bkg_{cellType}_stim'] = {
        'source': f'bkg_{cellType}',
        'conds': {'pop': cellType},
        'weight': params['weight'] * 1e6,
        'delay': 0,
        'synMech': 'AMPA',
        'sec': 'soma',
        'loc': 0.5,
    }

netParams.defaultThreshold = -20.0

print("=" * 80)
print("NetPyNE Network Parameters: Yao et al. 2022 (1000 cells - Point Neurons)")
print("=" * 80)
print(f"Total cells: {sum([p['numCells'] for p in cellTypes.values()])}")
for cellType, params in cellTypes.items():
    print(f"  - {cellType}: {params['numCells']}")
print(f"Connection types: {len([k for k in connProbs.keys() if connProbs[k] > 0])}")
print("=" * 80)
