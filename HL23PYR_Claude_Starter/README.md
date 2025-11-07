# HL23PYR (Cell 531526539) — Claude-Ready Starter Kit

This repo scaffolds a **seamless workflow** to build, validate, and iterate a human L2/3 pyramidal neuron model (HL23PYR) in **NEURON/NetPyNE**, tuned to **Allen Cell Types** targets and ready for **Alzheimer's (AD) perturbations**.

## Quickstart

```bash
# 1) Setup
bash setup_neuron.sh
conda activate hl23pyr  # or ensure pip installs succeeded

# 2) Parse Allen XML (optional sanity check)
python src/extract_allen_features.py --xml data/PYR_531526539.xml

# 3) Run base protocols (sweeps 45 & 52 equivalents)
python src/build_netpyne_model.py

# 4) Validate against targets
python src/run_validation.py
```

## Project Structure

- `data/`
  - `PYR_531526539.xml` — Allen export for the cell (provided).
  - `*_sim.json` — NetPyNE outputs per protocol.
- `src/`
  - `protocols.json` — target step-current protocols (170 pA, 310 pA).
  - `targets.json` — Allen features to match.
  - `build_netpyne_model.py` — minimal runnable model; replace with detailed mech/morph.
  - `apply_ad_changes.py` — hooks for AD channel changes.
  - `extract_allen_features.py` — XML parser to count spikes per sweep (adjust XPaths as needed).
  - `run_validation.py` — eFEL-based feature comparison.
- `prompts/`
  - `claude_system_prompt.md` — role & rules.
  - `claude_task_prompt.md` — concrete tasks for iterative development.
- `checklists/`
  - `modeling_checklist.md` — step-by-step runbook.
- `environment.yml` / `requirements.txt` — dependencies.
- `notebooks/` — placeholders for morph viz & protocol runs.

## Modeling Targets (Allen)

See `src/targets.json`. Start with:
- Resting Vm: −75.8 mV
- Rheobase: 170 pA
- Input Resistance: 100 MΩ
- Membrane Tau: 17.8 ms
- Adaptation Index: 0.075
- Upstroke:Downstroke: 2.89
- Firing Rate ~20 Hz @ 310 pA (sweep 52)
- FI Slope: 0.14 spikes/pA

## Notes

- Replace the toy single-compartment model with your detailed template
  (hoc or section-based Python) and mechanisms (.mod files).
- Keep protocol timing consistent: start=100 ms, dur=1000 ms for comparability.
- Use `apply_ad_changes.py` after the healthy model is validated.
- All paths are **project-root relative** for tool compatibility.

## CHANGELOG
- v0.1: Initial scaffold, protocols, targets, parsing/validation templates.