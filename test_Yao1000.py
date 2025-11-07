"""
test_Yao1000.py

Quick test script to validate the Yao 1000-cell network setup
Tests with a small 20-cell network before running full simulation
"""

import sys
import os

# Ensure mechanisms are compiled
print("=" * 80)
print("QUICK TEST: Yao et al. 2022 Network")
print("=" * 80)

print("\n1. Checking NEURON mechanisms...")
try:
    from neuron import h
    h.load_file('stdrun.hoc')

    # Try to load mechanisms
    mech_dir = os.path.join(os.path.dirname(__file__), 'mod')
    from neuron import load_mechanisms
    load_mechanisms(mech_dir)
    print("   ✓ Mechanisms loaded")
except Exception as e:
    print(f"   ✗ Error loading mechanisms: {e}")
    print("   Run 'nrnivmodl mod/' to compile mechanisms")
    sys.exit(1)

print("\n2. Testing cell loading...")
try:
    import cellwrapper

    # Test loading one cell of each type
    for cellType in ['HL23PYR', 'HL23PV', 'HL23SST', 'HL23VIP']:
        print(f"   Loading {cellType}...", end=" ")
        if cellType == 'HL23PYR':
            cell = cellwrapper.loadCell_HL23PYR(cellType)
        elif cellType == 'HL23PV':
            cell = cellwrapper.loadCell_HL23PV(cellType)
        elif cellType == 'HL23SST':
            cell = cellwrapper.loadCell_HL23SST(cellType)
        elif cellType == 'HL23VIP':
            cell = cellwrapper.loadCell_HL23VIP(cellType)

        nsecs = len([sec for sec in cell.all])
        print(f"✓ ({nsecs} sections)")

except Exception as e:
    print(f"\n   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Testing NetPyNE imports...")
try:
    from netpyne import specs, sim
    print("   ✓ NetPyNE imported")
except Exception as e:
    print(f"   ✗ Error: {e}")
    print("   Install NetPyNE: pip install netpyne")
    sys.exit(1)

print("\n4. Loading network parameters...")
try:
    from netParams_Yao1000 import netParams, cellTypes
    print(f"   ✓ Network parameters loaded")
    print(f"   ✓ {len(cellTypes)} cell types defined")
    print(f"   ✓ {len(netParams.popParams)} populations")
    print(f"   ✓ {len(netParams.synMechParams)} synapse types")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n5. Creating mini test network (20 cells)...")
try:
    # Scale down to 20 cells for quick test
    scale_factor = 20.0 / 1000.0

    for cellType in cellTypes.keys():
        original = netParams.popParams[cellType]['numCells']
        scaled = max(1, int(original * scale_factor))
        netParams.popParams[cellType]['numCells'] = scaled
        print(f"   {cellType:12s}: {scaled:3d} cells")

    print("\n   Initializing network...")
    simConfig = specs.SimConfig()
    simConfig.duration = 500  # ms (short test)
    simConfig.dt = 0.025
    simConfig.verbose = False
    simConfig.recordCellsSpikes = -1
    simConfig.hParams = {'celsius': 34.0, 'v_init': -80.0}
    simConfig.filename = 'test_Yao1000'
    simConfig.savePickle = False
    simConfig.printRunTime = 0.5

    print("   ✓ Config created")

except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n6. Running 500ms test simulation...")
print("-" * 80)

try:
    # Create network
    sim.initialize(netParams, simConfig)

    # Network statistics
    total_cells = sum([len(pop.cellGids) for pop in sim.net.pops.values()])
    print(f"\n   Network created: {total_cells} cells")

    for popLabel, pop in sim.net.pops.items():
        print(f"      {popLabel:12s}: {len(pop.cellGids):3d} cells")

    # Run simulation
    print("\n   Running simulation...")
    sim.setupRecording()
    sim.runSim()

    # Analyze spikes
    spkts = sim.allSimData['spkt']
    spkids = sim.allSimData['spkid']

    print(f"\n   ✓ Simulation complete!")
    print(f"   ✓ Total spikes recorded: {len(spkts)}")

    if len(spkts) > 0:
        # Calculate firing rates
        duration_s = simConfig.duration / 1000.0
        print(f"\n   Firing rates:")

        for popLabel, pop in sim.net.pops.items():
            cell_gids = pop.cellGids
            spikes_in_pop = sum([1 for gid in spkids if gid in cell_gids])
            num_cells = len(cell_gids)

            if num_cells > 0:
                avg_rate = spikes_in_pop / (num_cells * duration_s)
                print(f"      {popLabel:12s}: {avg_rate:6.2f} Hz")
    else:
        print("\n   ⚠ Warning: No spikes detected")
        print("      This may be normal for a short test simulation")

except Exception as e:
    print(f"\n   ✗ Simulation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("TEST COMPLETE - NETWORK READY!")
print("=" * 80)
print("\nNext steps:")
print("  1. Run full simulation:")
print("     python init_Yao1000.py")
print("\n  2. Run test mode (100 cells):")
print("     python init_Yao1000.py --test")
print("\n  3. Analyze results:")
print("     python analysis_Yao1000.py Yao1000.pkl")
print("=" * 80)
