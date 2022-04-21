SCRIPT_NAME=isa2w4m.py
REPOS_NAME=isa2w4m
TOOL_XML=isa2w4m.xml
PYVER=3.8.12
export PYENV_VERSION=$(PYVER)
PYENV:=$(shell which pyenv 2>/dev/null)
ifeq (,$(PYENV))
PYTHON=python3
else
PYTHON=pyenv exec python3
endif

ACTIVATE_VENV=. test-venv/bin/activate

all:

test: test-venv
	$(ACTIVATE_VENV) && tests/test-isa2w4m

pyver:
ifneq (,$(PYENV))
	pyenv install -s $(PYVER)
	pyenv local $(PYVER)
endif
	echo "Using $$($(PYTHON) --version)."

test-venv: pyver requirements.txt
	$(PYTHON) -m venv $@
	$(ACTIVATE_VENV) && python3 -m pip install --no-cache-dir --upgrade pip
	$(ACTIVATE_VENV) && python3 -m pip install --no-cache-dir -r requirements.txt
	$(ACTIVATE_VENV) && python3 -c 'import isatools'

test-venv/bin/planemo: test-venv
	$(ACTIVATE_VENV) && pip install planemo ; deactivate

plint: test-venv/bin/planemo
	$(ACTIVATE_VENV) && planemo lint $(TOOL_XML) ; deactivate

ptest: test-venv/bin/planemo
	$(ACTIVATE_VENV) && planemo test --conda_dependency_resolution --galaxy_branch release_20.09 $(TOOL_XML) ; deactivate

dist/$(REPOS_NAME)/:
	mkdir -p $@
	cp -Lr README.md $(SCRIPT_NAME) $(TOOL_XML) test-data $@

ptesttoolshed_diff: dist/$(REPOS_NAME)/ test-venv/bin/planemo
	$(ACTIVATE_VENV) && cd $< && planemo shed_diff --shed_target testtoolshed ; deactivate

ptesttoolshed_update: dist/$(REPOS_NAME)/ test-venv/bin/planemo
	$(ACTIVATE_VENV) && cd $< && planemo shed_update --check_diff --skip_metadata --shed_target testtoolshed ; deactivate

ptoolshed_diff: dist/$(REPOS_NAME)/ test-venv/bin/planemo
	$(ACTIVATE_VENV) && cd $< && planemo shed_diff --shed_target toolshed ; deactivate

ptoolshed_update: dist/$(REPOS_NAME)/ test-venv/bin/planemo
	$(ACTIVATE_VENV) && cd $< && planemo shed_update --check_diff --skip_metadata --shed_target toolshed ; deactivate

clean:
	$(RM) -r $(HOME)/.planemo
	$(RM) -r test-venv
	$(RM) tool_test_output.*
	$(RM) -r dist
	$(RM) -r tests/output
	$(RM) .python-version

.PHONY:	all clean test plint ptest ptesttoolshed_diff ptesttoolshed_update ptoolshed_diff ptoolshed_update
