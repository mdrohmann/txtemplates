.PHONY: test update_readme doc

all: update_readme

test:
	py.test --junitxml=junit-build.xml --cov-config .coveragerc  --twisted --cov-report html --cov txtemplates tests/

vitest:
	py.test --twisted -x -s --tb=native tests/

%.html: %.rst
	@pandoc -s -c $(abspath ./)/kultiad-serif.css -f rst -t html5 $< > $@

update_readme: README.html

doc:
	make -C docs html
