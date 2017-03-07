INPUT_SRC=$(shell find . -name '*.py' | grep -v test_)
INPUT_TEST=$(shell find . -name 'test_*.py')
PKG_NAME=coverxygen
PKG_VERSION=$(shell python3 -c 'import $(PKG_NAME); print($(PKG_NAME).__version__);')

all: dev

# dev tty

dev: dev-doc dev-check dev-pylint dev-coverage

dev-doc:
# 	@echo "---------------"
# 	@echo " Documentation "
# 	@echo "---------------"
# 	@make -C docs vhtml
# 	@echo ""

dev-check: $(SOURCES)
	@echo "-----------"
	@echo " Unittests "
	@echo "-----------"
	@./devtools/unittests.py -v
	@echo ""

dev-pylint:
	@echo "--------"
	@echo " PyLint "
	@echo "--------"
	@./devtools/xtdlint.py --rcfile=.pylintrc --reports=no -j4 coverxygen -f parseable || true
	@echo ""

dev-coverage:
	@echo "--------"
	@echo " Coverage "
	@echo "--------"
	@./devtools/coverage.sh python3
	@python3 -m coverage report
	@echo ""

# report

report: report-coverage report-doc report-pylint report-check

report-coverage: build/coverage/index.html
build/coverage/index.html: $(INPUT_SRC) $(INPUT_TEST) Makefile
	@echo "generating coverage report ..."
	@mkdir -p $(dir $@)
	@./devtools/coverage.sh python3 2> /dev/null
	@python3 -m coverage html -d $(dir $@)
	@echo "generating coverage report ... done"

report-pylint: build/pylint/index.html
build/pylint/index.html: $(INPUT_SRC) .pylintrc Makefile
	@echo "generating pylint report ..."
	@mkdir -p $(dir $@)
	@./devtools/xtdlint.py --rcfile=.pylintrc -j4 coverxygen -f html > $@ || true
	@echo "generating pylint report ... done"

report-doc: #build/docs/html/xtd.html
# build/docs/html/xtd.html:  $(INPUT_SRC) Makefile docs/conf.py
# 	@echo "generating documentation ..."
# 	@mkdir -p $(dir $@)
# 	@make -C docs -s html > /dev/null
# 	@echo "generating documentation ... done"

report-check: build/unittests/index.json
build/unittests/index.json:  $(INPUT_SRC) $(INPUT_TEST) Makefile
	@echo "generating unittests report ..."
	@mkdir -p $(dir $@)
	@./devtools/unittests.py --format json -v | json_pp > $@
	@echo "generating unittests report ... done"

# dist

dist: dist/$(PGK_NAME)-$(PKG_VERSION).tar.gz
dist/$(PGK_NAME)-$(PKG_VERSION).tar.gz: $(INPUT_SRC) setup.py setup.cfg
	@./setup.py sdist

# show

show: show-coverage show-doc show-check show-pylint
show-coverage: build/coverage/index.html
	@sensible-browser $< &
show-doc: #build/docs/html/xtd.html
# 	@sensible-browser $< &
show-check: build/unittests/index.json
	@sensible-browser $< &
show-pylint: build/pylint/index.html
	@sensible-browser $< &

# clean

clean: clean-doc clean-coverage clean-check clean-pylint clean-dist
# clean-doc:
# 	@rm -rf build/docs docs/xtd*.rst
clean-coverage:
	@rm -rf build/coverage
clean-check:
	@rm -rf build/unittests
clean-pylint:
	@rm -rf build/pylint
clean-dist:
	@rm -rf dist/ $(PKG_NAME).egg-info
