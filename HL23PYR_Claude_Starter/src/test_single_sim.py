"""
Quick test: run one simple simulation and inspect simData structure
"""
from netpyne import specs, sim
from neuron import h
import os, sys, json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)

# Load mechanisms
dll_path = os.path.join(REPO_ROOT, "x86_64", "libnrnmech.dylib")
if os.path.exists(dll_path):
    h.nrn_load_dll(dll_path)
    print(f"[INFO] Loaded mechanisms from {dll_path}")
else:
    print(f"[ERROR] Mechanisms not found at {dll_path}")
    exit(1)

# Create NetParams
netParams = specs.NetParams()

cellName = 'HL23PYR'
cellRule = netParams.importCellParams(
    label=cellName,
    somaAtOrigin=True,
    conds={'cellType': cellName, 'cellModel': 'HH_full'},
    fileName=os.path.join(REPO_ROOT, 'cellwrapper.py'),
    cellName='loadCell_HL23PYR',
    cellInstance=True,
    cellArgs={'cellName': cellName, 'ad': False}
)

netParams.popParams['pyr'] = {
    'cellType': cellName,
    'cellModel': 'HH_full',
    'numCells': 1
}

# Create SimConfig
cfg = specs.SimConfig()
cfg.duration = 1200
cfg.dt = 0.025
cfg.hParams = {'celsius': 34, 'v_init': -80}
cfg.verbose = False
cfg.recordCells = [0]  # Cell GID 0 (first and only cell)
cfg.recordTraces = {
    'V_soma': {'sec': 'soma_0', 'loc': 0.5, 'var': 'v'}
}
cfg.recordStep = 0.1
cfg.recordStim = True
cfg.recordTime = True

# Add 0 pA stimulus (baseline)
netParams.stimSourceParams['IClamp1'] = {
    'type': 'IClamp',
    'delay': 100,
    'dur': 1000,
    'amp': 0.0  # nA
}

netParams.stimTargetParams['IClamp1->pyr'] = {
    'source': 'IClamp1',
    'conds': {'pop': 'pyr'},
    'sec': 'soma_0',
    'loc': 0.5
}

# Run
print("Running simulation...")
sim.createSimulate(netParams=netParams, simConfig=cfg, output=False)
sim.gatherData()

# Inspect simData
print("\n[DEBUG] simData keys:", sim.simData.keys())
print("[DEBUG] 't' shape:", len(sim.simData['t']) if 't' in sim.simData else "N/A")

if 'V_soma' in sim.simData:
    print("[DEBUG] V_soma type:", type(sim.simData['V_soma']))
    print("[DEBUG] V_soma keys:", sim.simData['V_soma'].keys() if hasattr(sim.simData['V_soma'], 'keys') else "N/A")
    if hasattr(sim.simData['V_soma'], 'keys'):
        for key in sim.simData['V_soma'].keys():
            print(f"  [DEBUG] V_soma['{key}'] length:", len(sim.simData['V_soma'][key]))

print("\nDone.")
