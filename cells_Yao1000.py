"""
cells_Yao1000.py

Cell loader for NetPyNE Yao 1000-cell network
Interfaces with existing cellwrapper.py infrastructure
"""

import os
from neuron import h
import cellwrapper

# Get absolute path to this directory
BASEDIR = os.path.dirname(os.path.abspath(__file__))

def loadCell(cellName):
    """
    Load a cell using the cellwrapper infrastructure

    Args:
        cellName: 'HL23PYR', 'HL23SST', 'HL23PV', or 'HL23VIP'

    Returns:
        NEURON cell object
    """

    if cellName == 'HL23PYR':
        return cellwrapper.loadCell_HL23PYR(cellName)
    elif cellName == 'HL23SST':
        return cellwrapper.loadCell_HL23SST(cellName)
    elif cellName == 'HL23PV':
        return cellwrapper.loadCell_HL23PV(cellName)
    elif cellName == 'HL23VIP':
        return cellwrapper.loadCell_HL23VIP(cellName)
    else:
        raise ValueError(f"Unknown cell type: {cellName}")

def getCellRule(cellName):
    """
    Create NetPyNE cell rule dictionary for a given cell type

    Args:
        cellName: 'HL23PYR', 'HL23SST', 'HL23PV', or 'HL23VIP'

    Returns:
        Dictionary with cell rule parameters for NetPyNE
    """

    morphpath = os.path.join(BASEDIR, 'morphologies', cellName + '.swc')
    templatepath = os.path.join(BASEDIR, 'models', 'NeuronTemplate_' + cellName + '.hoc')
    biophyspath = os.path.join(BASEDIR, 'models', 'biophys_' + cellName + '.hoc')

    cellRule = {
        'conds': {'cellType': cellName},
        'secs': {},  # Will be imported from morphology
        'globals': {
            'morphology': morphpath,
            'template': templatepath,
            'biophysics': biophyspath,
        },
        'secLists': {
            'somatic': ['soma'],
            'apical': [],  # Will be populated from morphology
            'basal': [],
            'axonal': [],
        }
    }

    return cellRule

# Test function
if __name__ == '__main__':
    print("Testing cell loading...")

    for cellName in ['HL23PYR', 'HL23SST', 'HL23PV', 'HL23VIP']:
        print(f"\nLoading {cellName}...")
        try:
            cell = loadCell(cellName)
            print(f"✓ {cellName} loaded successfully")
            print(f"  Soma sections: {len([sec for sec in cell.soma])}")
            print(f"  Total sections: {len([sec for sec in cell.all])}")
        except Exception as e:
            print(f"✗ Error loading {cellName}: {e}")
