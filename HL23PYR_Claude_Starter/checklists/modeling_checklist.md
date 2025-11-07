# HL23PYR Modeling Checklist (Fast Path)

- [ ] Create/activate env: `conda env create -f environment.yml && conda activate hl23pyr`
- [ ] Verify NEURON loads: `python -c "import neuron; print(neuron.__version__)"
- [ ] Parse Allen XML: `python src/extract_allen_features.py --xml data/PYR_531526539.xml`
- [ ] Run protocols: `python src/build_netpyne_model.py`
- [ ] Validate features: `python src/run_validation.py`
- [ ] Iterate parameters/mechanisms until within ±10% of targets
- [ ] Commit: `git add -A && git commit -m "Iter X: tweaks" && git push`