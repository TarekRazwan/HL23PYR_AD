"""
Parse Allen Cell Types XML to extract Long Square sweeps and basic spike counts.
Save per-sweep spike times and an overview CSV.
"""
import argparse, pandas as pd
from lxml import etree
from pathlib import Path

def parse_xml(xml_path: Path):
    root = etree.parse(str(xml_path))
    sweeps = []
    # Generic parser: looks for elements named sweep/Sweep and child spike/Spike nodes
    for sweep in root.xpath("//sweep|//Sweep"):
        sid = sweep.get("id") or sweep.get("index") or sweep.get("number")
        amp = sweep.get("stimulus_amplitude") or sweep.get("amplitude") or sweep.get("amp")
        stim = sweep.get("stimulus") or sweep.get("type")
        spike_times = []
        for sp in sweep.xpath(".//spike|.//Spike"):
            t = sp.get("time") or sp.get("t")
            if t is not None:
                try:
                    spike_times.append(float(t))
                except Exception:
                    pass
        sweeps.append({
            "sweep_id": sid,
            "stimulus": stim,
            "amplitude_pA": float(amp) if amp else None,
            "n_spikes": len(spike_times),
            "spike_times_ms": spike_times
        })
    return pd.DataFrame(sweeps)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml", type=str, default="data/PYR_531526539.xml")
    ap.add_argument("--out_csv", type=str, default="data/allen_sweeps_overview.csv")
    args = ap.parse_args()
    df = parse_xml(Path(args.xml))
    df.to_csv(args.out_csv, index=False)
    print(f"Saved: {args.out_csv}")
    if not df.empty:
        print(df.head())

if __name__ == "__main__":
    main()