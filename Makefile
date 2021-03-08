SCRIPT_NAME=isa2w4m.py
REPOS_NAME=isa2w4m
TOOL_XML=isa2w4m.xml
PYTHON_VERSION=3.6.10

all:

test: test-venv
	. test-venv/bin/activate && pip install isatools ; deactivate
	. test-venv/bin/activate && python -c 'import isatools' ; deactivate
	. test-venv/bin/activate && ./test-isa2w4m ; deactivate

install_python:
	pyenv install -s $(PYTHON_VERSION)

test-venv: install_python
	PYENV_VERSION=$(PYTHON_VERSION) python3 -m venv $@
	. $@/bin/activate && pip install --upgrade pip ; deactivate

test-venv/bin/planemo: test-venv
	. test-venv/bin/activate && pip install planemo ; deactivate

plint: test-venv/bin/planemo
	. test-venv/bin/activate && planemo lint $(TOOL_XML) ; deactivate

ptest: test-venv/bin/planemo
	. test-venv/bin/activate && planemo test --conda_dependency_resolution --galaxy_branch release_20.09 $(TOOL_XML) ; deactivate

dist/$(REPOS_NAME)/:
	mkdir -p $@
	cp -Lr README.md $(SCRIPT_NAME) $(TOOL_XML) test-data $@

ptesttoolshed_diff: dist/$(REPOS_NAME)/ test-venv/bin/planemo
	. test-venv/bin/activate && cd $< && planemo shed_diff --shed_target testtoolshed ; deactivate

ptesttoolshed_update: dist/$(REPOS_NAME)/ test-venv/bin/planemo
	. test-venv/bin/activate && cd $< && planemo shed_update --check_diff --skip_metadata --shed_target testtoolshed ; deactivate

ptoolshed_diff: dist/$(REPOS_NAME)/ test-venv/bin/planemo
	. test-venv/bin/activate && cd $< && planemo shed_diff --shed_target toolshed ; deactivate

ptoolshed_update: dist/$(REPOS_NAME)/ test-venv/bin/planemo
	. test-venv/bin/activate && cd $< && planemo shed_update --check_diff --skip_metadata --shed_target toolshed ; deactivate

clean:
	$(RM) -r $(HOME)/.planemo
	$(RM) -r test-venv
	$(RM) tool_test_output.*
	$(RM) -r dist
	$(RM) -r MTBLS30

.PHONY:	all clean test plint ptest ptesttoolshed_diff ptesttoolshed_update ptoolshed_diff ptoolshed_update
