SCRIPT_NAME=isa2w4m.py
REPOS_NAME=isa2w4m
TOOL_XML=isa2w4m.xml

all:

test:
	./test-isa2w4m

planemo-venv/bin/planemo: planemo-venv
	. planemo-venv/bin/activate && pip install --upgrade pip setuptools
	. planemo-venv/bin/activate && pip install planemo

planemo-venv:
	virtualenv -p python2.7 $@

plint: planemo-venv/bin/planemo
	. planemo-venv/bin/activate && planemo lint $(TOOL_XML)

ptest: planemo-venv/bin/planemo
	. planemo-venv/bin/activate && planemo test --conda_dependency_resolution --galaxy_branch release_19.01 $(TOOL_XML)

dist/$(REPOS_NAME)/:
	mkdir -p $@
	cp -Lr README.md $(SCRIPT_NAME) $(TOOL_XML) test-data $@

ptesttoolshed_diff: dist/$(REPOS_NAME)/ planemo-venv/bin/planemo
	. planemo-venv/bin/activate && cd $< && planemo shed_diff --shed_target testtoolshed

ptesttoolshed_update: dist/$(REPOS_NAME)/ planemo-venv/bin/planemo
	. planemo-venv/bin/activate && cd $< && planemo shed_update --check_diff --shed_target testtoolshed

ptoolshed_diff: dist/$(REPOS_NAME)/ planemo-venv/bin/planemo
	. planemo-venv/bin/activate && cd $< && planemo shed_diff --shed_target toolshed

ptoolshed_update: dist/$(REPOS_NAME)/ planemo-venv/bin/planemo
	. planemo-venv/bin/activate && cd $< && planemo shed_update --check_diff --shed_target toolshed

clean:
	$(RM) -r $(HOME)/.planemo
	$(RM) -r planemo-venv
	$(RM) tool_test_output.*
	$(RM) -r dist
	$(RM) -r MTBLS30

.PHONY:	all clean test plint ptest ptesttoolshed_diff ptesttoolshed_update ptoolshed_diff ptoolshed_update
