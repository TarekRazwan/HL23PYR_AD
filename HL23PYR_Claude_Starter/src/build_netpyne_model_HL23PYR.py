"""
NetPyNE HL23PYR (Allen Cell ID 531526539) — Stage 1/2 Simulations
- Loads full morphology (NeuronTemplate_HL23PYR.hoc) + biophysics
- Supports healthy baseline (default) or AD variant (--ad flag)
- Compiles/loads all .mod mechanisms (macOS-compatible)
- Runs diagnostic protocols: 0 pA (rest Vm), -50 pA (Rin/tau), -110 pA (sag), 170 pA, 310 pA
- Saves plain JSON traces for EFEL validation
"""
from netpyne import specs, sim
from neuron import h
import json, os, sys, numpy as np, argparse
from datetime import datetime

# Path setup relative to repo root
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MOD_DIR = os.path.join(REPO_ROOT, "mod")
MODELS_DIR = os.path.join(REPO_ROOT, "models")
MORPH_DIR = os.path.join(REPO_ROOT, "morphologies")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

sys.path.insert(0, REPO_ROOT)  # so we can import cellwrapper if needed

def compile_and_load_mechanisms():
    """
    Compile .mod files and load mechanisms (macOS-compatible).
    Uses nrnivmodl if available, otherwise tries h.nrn_load_dll.
    """
    import subprocess

    print(f"[INFO] Mechanism directory: {MOD_DIR}")

    # nrnivmodl creates x86_64/ in the current working directory (REPO_ROOT)
    # NOT inside MOD_DIR
    compiled_dir = os.path.join(REPO_ROOT, "x86_64")
    dll_path = os.path.join(compiled_dir, "libnrnmech.dylib")  # macOS

    if not os.path.exists(dll_path):
        print("[INFO] Mechanisms not compiled. Running nrnivmodl...")
        try:
            result = subprocess.run(
                ["nrnivmodl", "mod"],  # relative to REPO_ROOT
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout)
            if result.stderr:
                print("[WARN]", result.stderr)
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] nrnivmodl failed: {e.stderr}")
            raise
        except FileNotFoundError:
            print("[ERROR] nrnivmodl not found. Please ensure NEURON is installed.")
            raise

    # Load the compiled mechanisms
    if os.path.exists(dll_path):
        print(f"[INFO] Loading mechanisms from {dll_path}")
        h.nrn_load_dll(dll_path)
        print("[SUCCESS] Mechanisms loaded.")
    else:
        print("[ERROR] Could not find compiled mechanisms.")
        print(f"[DEBUG] Checked: {dll_path}")
        print(f"[DEBUG] REPO_ROOT contents: {os.listdir(REPO_ROOT)}")
        raise FileNotFoundError(f"Expected {dll_path}")


def make_netparams(ad=False, ad_stage=None):
    """
    Create NetPyNE network with real HL23PYR cell using importCellParams.

    Args:
        ad (bool): If True, use AD variant biophysics; if False, use healthy baseline
        ad_stage (int): AD stage (1=early hyperexcitability, 3=late hypoexcitability)
    """
    netParams = specs.NetParams()

    cellName = 'HL23PYR'

    # Import the detailed cell from cellwrapper.py
    # This loads NeuronTemplate_HL23PYR.hoc + biophys file (healthy or AD) + morphology
    cellRule = netParams.importCellParams(
        label=cellName,
        somaAtOrigin=True,
        conds={'cellType': cellName, 'cellModel': 'HH_full'},
        fileName=os.path.join(REPO_ROOT, 'cellwrapper.py'),
        cellName='loadCell_HL23PYR',
        cellInstance=True,
        cellArgs={'cellName': cellName, 'ad': ad, 'ad_stage': ad_stage}  # Pass AD flag and stage
    )

    # Create a single-cell population
    netParams.popParams['pyr'] = {
        'cellType': cellName,
        'cellModel': 'HH_full',
        'numCells': 1
    }

    return netParams


def make_simconfig(protocol_name="baseline", simlabel_suffix=""):
    """
    Create simulation config with recording setup.
    """
    cfg = specs.SimConfig()
    cfg.duration = 1200  # ms (100 pre + 1000 stim + 100 post)
    cfg.dt = 0.025
    cfg.hParams = {'celsius': 34, 'v_init': -80}
    cfg.verbose = False
    cfg.createNEURONObj = True
    cfg.createPyStruct = True
    cfg.cvode_active = False
    cfg.printRunTime = 0.1

    # Record from all cells in population 'pyr'
    # NetPyNE requires recordCells to be set for imported morphologies
    cfg.recordCells = [0]  # Cell GID 0 (first and only cell)
    cfg.recordTraces = {
        'V_soma': {'sec': 'soma_0', 'loc': 0.5, 'var': 'v'}
    }
    cfg.recordStep = 0.1
    cfg.recordStim = True
    cfg.recordTime = True

    # Unique label with timestamp
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    cfg.simLabel = f"Stage1_Healthy_{protocol_name}_{simlabel_suffix}_{ts}"
    cfg.saveFolder = DATA_DIR
    cfg.savePickle = False
    cfg.saveJson = False

    return cfg


def run_protocol(amplitude_pA=0, start_ms=100, duration_ms=1000, protocol_name="baseline", ad=False, ad_stage=None):
    """
    Run a single current-clamp protocol.

    Args:
        amplitude_pA: Current amplitude in pA
        start_ms: Stimulus start time in ms
        duration_ms: Stimulus duration in ms
        protocol_name: Descriptive name for this protocol
        ad: If True, use AD variant biophysics
        ad_stage: AD stage (1=early, 3=late)

    Returns:
        sim object with simData
    """
    netParams = make_netparams(ad=ad, ad_stage=ad_stage)
    cfg = make_simconfig(protocol_name, f"{int(amplitude_pA)}pA")

    # Add IClamp stimulus
    netParams.stimSourceParams['IClamp1'] = {
        'type': 'IClamp',
        'delay': start_ms,
        'dur': duration_ms,
        'amp': amplitude_pA / 1000.0  # pA -> nA
    }

    netParams.stimTargetParams['IClamp1->pyr'] = {
        'source': 'IClamp1',
        'conds': {'pop': 'pyr'},
        'sec': 'soma_0',
        'loc': 0.5
    }

    # Run simulation
    sim.createSimulate(netParams=netParams, simConfig=cfg, output=False)
    sim.gatherData()

    return sim


def save_plain_json(sim_obj, out_path):
    """
    Save simulation traces as plain JSON (no HocObjects).
    Format: {'simData': {'t': [...], 'v_soma': {'cell_0': [...]}}}
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Extract time and voltage traces
    t = np.asarray(sim_obj.simData['t']).tolist()

    # Handle different possible keys for voltage trace
    v_key_candidates = ['V_soma']
    v_data = None
    for key in v_key_candidates:
        if key in sim_obj.simData:
            v_dict = sim_obj.simData[key]
            # Get the first (and only) cell's data
            cell_key = list(v_dict.keys())[0]
            v_data = np.asarray(v_dict[cell_key]).tolist()
            break

    if v_data is None:
        raise ValueError(f"Could not find voltage trace in simData. Keys: {sim_obj.simData.keys()}")

    payload = {
        'simData': {
            't': t,
            'v_soma': {'cell_0': v_data}
        },
        'metadata': {
            'simLabel': sim_obj.cfg.simLabel if hasattr(sim_obj, 'cfg') else 'unknown',
            'duration': sim_obj.cfg.duration if hasattr(sim_obj, 'cfg') else len(t) * 0.1
        }
    }

    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[SAVED] {out_path}")


def load_protocols():
    """Load protocol definitions from protocols.json"""
    proto_file = os.path.join(os.path.dirname(__file__), "protocols.json")
    with open(proto_file) as f:
        return json.load(f)["protocols"]


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run HL23PYR simulations (Healthy or AD variant)')
    parser.add_argument('--ad', action='store_true', help='Use AD variant biophysics (default: healthy baseline)')
    parser.add_argument('--stage', type=int, choices=[1, 3], default=1, help='AD stage: 1=early hyperexcitability, 3=late hypoexcitability (default: 1)')
    args = parser.parse_args()

    if args.ad:
        if args.stage == 1:
            variant_name = "AD Stage 1 (Early Hyperexcitability)"
            stage_desc = "A+/T−/N−"
        else:  # stage == 3
            variant_name = "AD Stage 3 (Late Hypoexcitability)"
            stage_desc = "A+/T+/N+"
    else:
        variant_name = "Healthy Baseline"
        stage_desc = "A−/T−/N−"

    print("="*60)
    print(f"HL23PYR {variant_name} ({stage_desc})")
    print("="*60)

    # Step 1: Compile and load mechanisms
    compile_and_load_mechanisms()

    # Step 2: Define diagnostic protocols
    # These will measure passive properties BEFORE testing excitability
    diagnostic_protocols = [
        {"name": "baseline_0pA", "amplitude_pA": 0, "start_ms": 100, "duration_ms": 1000},
        {"name": "passive_neg50pA", "amplitude_pA": -50, "start_ms": 100, "duration_ms": 1000},
        {"name": "sag_neg110pA", "amplitude_pA": -110, "start_ms": 100, "duration_ms": 1000},
    ]

    # Add the standard Allen protocols (170 pA rheobase, 310 pA high rate)
    standard_protocols = load_protocols()

    all_protocols = diagnostic_protocols + [
        {"name": p["name"], "amplitude_pA": p["amplitude_pA"],
         "start_ms": p["start_ms"], "duration_ms": p["duration_ms"]}
        for p in standard_protocols
    ]

    # Step 3: Run all protocols
    if args.ad:
        suffix = f"_AD_Stage{args.stage}"
    else:
        suffix = ""

    for i, proto in enumerate(all_protocols):
        print(f"\n[{i+1}/{len(all_protocols)}] Running {proto['name']} @ {proto['amplitude_pA']} pA")

        try:
            sim_obj = run_protocol(
                amplitude_pA=proto['amplitude_pA'],
                start_ms=proto['start_ms'],
                duration_ms=proto['duration_ms'],
                protocol_name=proto['name'],
                ad=args.ad,  # Pass AD flag
                ad_stage=args.stage if args.ad else None  # Pass stage
            )

            # Add suffix to output filename for AD variant
            out_path = os.path.join(DATA_DIR, f"{proto['name']}{suffix}_sim.json")
            save_plain_json(sim_obj, out_path)

            # Clear NEURON state between runs
            sim.clearAll()

        except Exception as e:
            print(f"[ERROR] Protocol {proto['name']} failed: {e}")
            import traceback
            traceback.print_exc()
            continue

    print("\n" + "="*60)
    print(f"Simulation complete: {variant_name}")
    print(f"Saved to data/*{suffix}_sim.json")
    print("="*60)
