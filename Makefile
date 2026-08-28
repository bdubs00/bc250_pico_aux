MPREMOTE ?= mpremote
SRC := src/config.py src/power_button.py src/psu.py src/main.py

.PHONY: deploy monitor

deploy:
	$(MPREMOTE) cp $(SRC) :/
	$(MPREMOTE) reset

monitor:
	$(MPREMOTE) repl
