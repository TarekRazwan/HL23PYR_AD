"""
Load NetPyNE JSON traces and compute eFEL features; compare to targets.json.
"""
import json, glob, numpy as np
import efel

def load_trace(json_file):
    with open(json_file) as f:
        d = json.load(f)
    t = np.array(d['simData']['t'])
    v = np.array(d['simData']['v_soma']['cell_0'])
    return t, v

def to_efel(t, v, stim_start=100.0, stim_end=1100.0):
    return [{
        'T': t, 'V': v,
        'stim_start': [stim_start], 'stim_end': [stim_end]
    }]

def main():
    with open("src/targets.json") as f:
        targets = json.load(f)['features']
    for js in glob.glob("data/*_sim.json"):
        t, v = load_trace(js)
        traces = to_efel(t, v)
        features = ['Spikecount', 'mean_frequency']
        feats = efel.getFeatureValues(traces, features)[0]
        print(js, feats, "Targets:", {"FiringRate_Hz_at_310pA": targets["FiringRate_Hz_at_310pA"]})

if __name__ == "__main__":
    main()