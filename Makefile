.PHONY: install test run webhook

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

run:
	python scheduler.py

webhook:
	python webhook.py
