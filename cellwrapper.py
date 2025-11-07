import sys
import os

# Get absolute path to the repo root (where this file lives)
_CELLWRAPPER_DIR = os.path.dirname(os.path.abspath(__file__))

# def loadCell_HL23PYR(cellName):

def loadCell_HL23PYR(cellName, ad=False, ad_stage=None):

    templatepath = os.path.join(_CELLWRAPPER_DIR, 'models', 'NeuronTemplate_HL23PYR.hoc')

    # Select biophysics file based on AD flag and stage
    if ad:
        if ad_stage == 1:
            biophysics = os.path.join(_CELLWRAPPER_DIR, 'models', 'biophys_' + cellName + '_AD_Stage1.hoc')
        elif ad_stage == 3:
            biophysics = os.path.join(_CELLWRAPPER_DIR, 'models', 'biophys_' + cellName + '_AD_Stage3.hoc')
        else:
            # Default to Stage 1 if ad=True but no stage specified
            biophysics = os.path.join(_CELLWRAPPER_DIR, 'models', 'biophys_' + cellName + '_AD_Stage1.hoc')
    else:
        biophysics = os.path.join(_CELLWRAPPER_DIR, 'models', 'biophys_' + cellName + '.hoc')

    morphpath = os.path.join(_CELLWRAPPER_DIR, 'morphologies', cellName + '.swc')

    from neuron import h
    h.load_file("stdrun.hoc")
    h.load_file('import3d.hoc')
    h.xopen(biophysics)

    try:
        h.xopen(templatepath)
    except:
        pass

    cell = getattr(h, 'NeuronTemplate_HL23PYR')(morphpath)
    h.biophys_HL23PYR(cell)  # This calls the proc from the loaded biophysics file

    print(cell)
    print("Kv3.1 gbar (soma):", cell.soma[0](0.5).gbar_Kv3_1)
    print("SK gbar (soma):", cell.soma[0](0.5).gbar_SK)
    print("NaTg gbar (axon):", cell.axon[0](0.5).gbar_NaTg)
    print("Nap gbar (axon):", cell.axon[0](0.5).gbar_Nap)

    return cell


# def apply_AD_changes(cell):
    # for sec in cell.axon:
    #     for seg in sec:
    #         if hasattr(seg, "vshiftm_NaTg"):
    #             seg.vshiftm_NaTg += 8
    #         if hasattr(seg, "vshifth_NaTg"):
    #             seg.vshifth_NaTg += 10
    #         if hasattr(seg, "slopem_NaTg"):
    #             seg.slopem_NaTg *= 1.2
    #         if hasattr(seg, "gbar_NaTg"):
    #             seg.gbar_NaTg *= 0.8

def apply_AD_changes(cell):
    # === NaTg (axon) ===
    for sec in getattr(cell, "axon", []):
        for seg in sec:
            if hasattr(seg, "gbar_NaTg"):
                original = seg.gbar_NaTg
                seg.gbar_NaTg *= 1.2
                print(f"{sec.name()}({seg.x:.2f}) gbar_NaTg: {original:.4f} → {seg.gbar_NaTg:.4f}")
            # if hasattr(seg, "vshiftm_NaTg"):
            #     original = seg.vshiftm_NaTg
            #     seg.vshiftm_NaTg += 2
            #     print(f"{sec.name()}({seg.x:.2f}) vshiftm_NaTg: {original:.1f} → {seg.vshiftm_NaTg:.1f}")
            # if hasattr(seg, "slopem_NaTg"):
            #     original = seg.slopem_NaTg
            #     seg.slopem_NaTg *= 1.2
            #     print(f"{sec.name()}({seg.x:.2f}) slopem_NaTg: {original:.1f} → {seg.slopem_NaTg:.1f}")

    # === Nap (axon) ===
    for sec in getattr(cell, "axon", []):
        for seg in sec:
            if hasattr(seg, "gbar_Nap"):
                original = seg.gbar_Nap
                seg.gbar_Nap *= 1.3
                print(f"{sec.name()}({seg.x:.2f}) gbar_Nap: {original:.5f} → {seg.gbar_Nap:.5f}")

    # === Kv3_1 (soma) ===
    for sec in getattr(cell, "soma", []):
        for seg in sec:
            if hasattr(seg, "gbar_Kv3_1"):
                original = seg.gbar_Kv3_1
                seg.gbar_Kv3_1 *= 0.5
                print(f"{sec.name()}({seg.x:.2f}) gbar_Kv3_1: {original:.4f} → {seg.gbar_Kv3_1:.4f}")

    # === SK (soma) ===
    for sec in getattr(cell, "soma", []):
        for seg in sec:
            if hasattr(seg, "gbar_SK"):
                original = seg.gbar_SK
                seg.gbar_SK *= 0.6
                print(f"{sec.name()}({seg.x:.2f}) gbar_SK: {original:.7f} → {seg.gbar_SK:.7f}")

    # === Ih (dendrites) ===
    for sec in getattr(cell, "dend", []):
        for seg in sec:
            if hasattr(seg, "gbar_Ih"):
                original = seg.gbar_Ih
                seg.gbar_Ih *= 0.7
                print(f"{sec.name()}({seg.x:.2f}) gbar_Ih: {original:.2e} → {seg.gbar_Ih:.2e}")


def loadCell_HL23VIP(cellName):

    templatepath = os.path.join(_CELLWRAPPER_DIR, 'models', 'NeuronTemplate_HL23VIP.hoc')
    biophysics = os.path.join(_CELLWRAPPER_DIR, 'models', 'biophys_' + cellName + '.hoc')
    morphpath = os.path.join(_CELLWRAPPER_DIR, 'morphologies', cellName + '.swc')

    from neuron import h

    h.load_file("stdrun.hoc")
    h.load_file('import3d.hoc')

    h.xopen(biophysics)
        
    try:
       h.xopen(templatepath)
    except:
        pass

    cell = getattr(h, 'NeuronTemplate_HL23VIP')(morphpath)
    
    print (cell)

    h.biophys_HL23VIP(cell)

    return cell


def loadCell_HL23PV(cellName):

    templatepath = os.path.join(_CELLWRAPPER_DIR, 'models', 'NeuronTemplate_HL23PV.hoc')
    biophysics = os.path.join(_CELLWRAPPER_DIR, 'models', 'biophys_' + cellName + '.hoc')
    morphpath = os.path.join(_CELLWRAPPER_DIR, 'morphologies', cellName + '.swc')

    from neuron import h

    h.load_file("stdrun.hoc")
    h.load_file('import3d.hoc')

    h.xopen(biophysics)
        
    try:
       h.xopen(templatepath)
    except:
        pass

    cell = getattr(h, 'NeuronTemplate_HL23PV')(morphpath)
    
    print (cell)

    h.biophys_HL23PV(cell)

    return cell


def loadCell_HL23SST(cellName):

    templatepath = os.path.join(_CELLWRAPPER_DIR, 'models', 'NeuronTemplate_HL23SST.hoc')
    biophysics = os.path.join(_CELLWRAPPER_DIR, 'models', 'biophys_' + cellName + '.hoc')
    morphpath = os.path.join(_CELLWRAPPER_DIR, 'morphologies', cellName + '.swc')

    from neuron import h

    h.load_file("stdrun.hoc")
    h.load_file('import3d.hoc')

    h.xopen(biophysics)
        
    try:
       h.xopen(templatepath)
    except:
        pass

    cell = getattr(h, 'NeuronTemplate_HL23SST')(morphpath)
    
    print (cell)

    h.biophys_HL23SST(cell)

    return cell