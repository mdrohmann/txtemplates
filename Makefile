.PHONY: test update_readme doc

all: update_readme

test:
	PYTHONPATH=$$PWD:$$PYTHONPATH py.test --junitxml=jUnittest.xml --cov-config .coveragerc  --twisted --cov-report html --cov voteapp tests/

vitest:
	py.test --twisted -x -s --tb=native tests/

%.html: %.rst
	@pandoc -s -c $(abspath ./)/kultiad-serif.css -f rst -t html5 $< > $@

update_readme: README.html

doc:
	make -C docs html
