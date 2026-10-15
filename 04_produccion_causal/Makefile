PY ?= python

.PHONY: validate compile demo monitor
validate:
	$(PY) -m compileall -q src B1_servicio_dml B2_model_card_ci B3_servicio_policy B4_monitoreo_causal
compile:
	$(PY) scripts/build_runtime_bundles.py
