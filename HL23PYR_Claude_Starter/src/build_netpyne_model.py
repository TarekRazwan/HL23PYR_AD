"""
Minimal NetPyNE L2/3 PYR template with hooks for AD changes and Allen protocols.
- Runs long-square protocols (e.g., 170 pA, 310 pA) from src/protocols.json
- Saves plain-JSON traces (time, v_soma) that run_validation.py can read
- Stays intentionally simple so Claude can swap in your detailed HL23PYR model
"""
from netpyne import specs, sim
from neuron import h
import json, os, numpy as np
from datetime import datetime

THIS_DIR = os.path.dirname(__file__)

def load_protocols():
    with open(os.path.join(THIS_DIR, "protocols.json")) as f:
        return json.load(f)["protocols"]

def make_netparams():
    netParams = specs.NetParams()

    # --- PLACEHOLDER single-compartment cell ---
    # Replace this with your detailed HL23PYR morphology + mechanisms.
    soma = {
        'geom': {'diam': 20, 'L': 20, 'Ra': 100},
        'mechs': {'hh': {'gnabar': 0.12, 'gkbar': 0.036, 'gl': 0.0003, 'el': -70}}
    }
    netParams.cellParams['HL23PYR'] = {'secs': {'soma': soma}}
    netParams.popParams['pyr'] = {'cellType': 'HL23PYR', 'numCells': 1}

    return netParams

def make_simconfig(simlabel_suffix=""):
    cfg = specs.SimConfig()
    cfg.duration = 1200        # ms (100 ms pre + 1000 ms step + 100 ms post)
    cfg.dt = 0.025
    cfg.recordTraces = {'v_soma': {'sec': 'soma', 'loc': 0.5, 'var': 'v'}}
    cfg.recordStep = 0.1
    cfg.verbose = False
    cfg.analysis['plotTraces'] = {'include': [0]}  # will no-op headless

    # Optional: unique label so runs don’t overwrite if you later enable auto-saving
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    cfg.simLabel = f"HL23PYR_proto{('_' + simlabel_suffix) if simlabel_suffix else ''}_{ts}"

    return cfg

def run_protocol(amplitude_pA=170, start_ms=100, duration_ms=1000):
    netParams = make_netparams()
    cfg = make_simconfig(simlabel_suffix=f"{int(amplitude_pA)}pA")

    # Stimulus (IClamp in soma @ 0.5)
    cfg.addStim = True
    cfg.stims = [{
        'source': 'IClamp', 'sec': 'soma', 'loc': 0.5,
        'amp': amplitude_pA/1000.0,  # pA -> nA
        'delay': start_ms, 'dur': duration_ms
    }]

    sim.createSimulate(netParams=netParams, simConfig=cfg, output=False)
    sim.gatherData()
    return sim

def save_plain_json(sim_obj, out_path):
    """Write only plain Python lists (no HocObjects) so run_validation.py can load them."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Extract the minimal pieces used by run_validation.py
    t = np.asarray(sim_obj.simData['t']).tolist()
    v = np.asarray(sim_obj.simData['v_soma']['cell_0']).tolist()

    payload = {'simData': {'t': t, 'v_soma': {'cell_0': v}}}
    with open(out_path, "w") as f:
        json.dump(payload, f)

if __name__ == "__main__":
    for p in load_protocols():
        print(f"Running {p['name']} @ {p['amplitude_pA']} pA")
        sim_obj = run_protocol(p['amplitude_pA'], p['start_ms'], p['duration_ms'])

        out_path = os.path.join(THIS_DIR, "..", "data", f"{p['name']}_sim.json")
        save_plain_json(sim_obj, out_path)

        sim.clearAll()  # free NEURON/NetPyNE state between runs
