SCRIPT_NAME=isa2w4m.py
REPOS_NAME=isa2w4m
TOOL_XML=isa2w4m.xml
PYVER38=3.8.12
PYVER39=3.9.9
PYVER=$(PYVER38) $(PYVER39)
PYENV:=$(shell command -v pyenv)
ifeq (,$(PYENV))
PYTHON=python3
else
PYTHON=$(PYENV) exec python3
endif
VM = isa2w4m-archlinux
CONDA_DIR=$(PWD)/conda

all:

test: test38 test39

testvm:
	teston -rD -f Makefile -f isa2w4m.py -f isa2w4m.xml -f requirements.txt -f tests/test-isa2w4m -f test-data -c gnumake -c pyenv -c unzip -c git -t test39 -O minimal archlinux/archlinux

define test_on_pyver
test$(1): PYENV_VERSION=$$(PYVER$(1))
test$(1): pyver requirements.txt
	$(PYTHON) -m venv test$(1)-venv
	. test$(1)-venv/bin/activate && python3 -m pip install --no-cache-dir --upgrade pip
	. test$(1)-venv/bin/activate && python3 -m pip install --no-cache-dir -r requirements.txt
	. test$(1)-venv/bin/activate && python3 -c 'import isatools'
	. test$(1)-venv/bin/activate && tests/test-isa2w4m
endef

$(foreach ver,38 39,$(eval $(call test_on_pyver,$(ver))))

pyver:
ifneq (,$(PYENV))
	for ver in $(PYVER) ; do pyenv install -s $$ver ; done
	pyenv local $(PYVER)
endif
	echo "Using $$($(PYTHON) --version)."

planemo-venv:
	python3 -m venv $@

planemo-venv/bin/planemo: planemo-venv
	. planemo-venv/bin/activate && python3 -m pip install planemo

plint: planemo-venv/bin/planemo
	. planemo-venv/bin/activate && planemo lint $(TOOL_XML)

$(CONDA_DIR): planemo-venv/bin/planemo 
	. planemo-venv/bin/activate && planemo conda_init --conda_prefix $(CONDA_DIR)

ptest: $(CONDA_DIR)
	. planemo-venv/bin/activate && planemo conda_install $(TOOL_XML)
	. planemo-venv/bin/activate && planemo test --conda_dependency_resolution --galaxy_branch release_21.09 $(TOOL_XML)

dist/$(REPOS_NAME)/:
	mkdir -p $@
	cp -Lr README.md $(SCRIPT_NAME) $(TOOL_XML) test-data $@

ptesttoolshed_diff: dist/$(REPOS_NAME)/ test-venv/bin/planemo
	. planemo-venv/bin/activate && cd $< && planemo shed_diff --shed_target testtoolshed

ptesttoolshed_update: dist/$(REPOS_NAME)/ test-venv/bin/planemo
	. planemo-venv/bin/activate && cd $< && planemo shed_update --check_diff --skip_metadata --shed_target testtoolshed

ptoolshed_diff: dist/$(REPOS_NAME)/ test-venv/bin/planemo
	. planemo-venv/bin/activate && cd $< && planemo shed_diff --shed_target toolshed

ptoolshed_update: dist/$(REPOS_NAME)/ test-venv/bin/planemo
	. planemo-venv/bin/activate && cd $< && planemo shed_update --check_diff --skip_metadata --shed_target toolshed

clean:
	$(RM) -r $(HOME)/.planemo
	$(RM) -r *-venv $(CONDA_DIR)
	$(RM) tool_test_output.*
	$(RM) -r dist
	$(RM) -r tests/output
	$(RM) .python-version

.PHONY: all clean test plint ptest ptesttoolshed_diff ptesttoolshed_update ptoolshed_diff ptoolshed_update
