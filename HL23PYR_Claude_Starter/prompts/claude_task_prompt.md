Goal: Bring the model to within ±10% of Allen targets in src/targets.json for baseline (healthy) neuron,
using the XML in data/ for ground truth and NetPyNE/NEURON for simulation.

Deliverables for each iteration:
1) Proposed edits with rationale.
2) Updated code (diff or full file).
3) Commands to run.
4) Validation output vs targets.

Start by:
- Parsing data/PYR_531526539.xml to confirm spike counts for sweeps 45 (170 pA) and 52 (310 pA).
- Running src/build_netpyne_model.py to generate data/*_sim.json.
- Evaluating with src/run_validation.py and reporting gaps to targets.