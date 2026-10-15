PY ?= python

.PHONY: validate demo monitor

validate:
	$(PY) -m compileall -q src B1_servicio_dml B2_model_card_ci B3_servicio_policy B4_monitoreo_causal

demo:
	PYTHONPATH=src $(PY) scripts/run_demo.py

monitor:
	$(PY) B4_monitoreo_causal/scripts/run_monitor.py
