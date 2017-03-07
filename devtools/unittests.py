#!/usr/bin/env python3
# -*- mode:python -*-
# -*- coding:utf-8 -*-
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import inspect
import unittest2 as unittest
import importlib
import os
import sys
import json

#------------------------------------------------------------------#

def __sys_path():
  # l_path = os.path.realpath(os.path.dirname(__file__))
  # os.chdir(os.path.dirname(l_path))
  sys.path.insert(0, ".")

__sys_path()

#------------------------------------------------------------------#

class JsonTestRunner(unittest.TextTestRunner):
  def __init__(self, *p_args, **p_kwds):
    self.m_origStream = p_kwds.get("stream", sys.stdout)
    p_kwds["stream"] = open("/dev/null", "w")
    super(JsonTestRunner, self).__init__(*p_args, **p_kwds)

  def _makeResult(self):
    l_res = super(JsonTestRunner, self)._makeResult()
    return l_res

  @staticmethod
  def _getTestInfo(p_test, p_message=None):
    l_file = inspect.getsourcefile(p_test.__class__)
    l_methodName = p_test._testMethodName
    l_method = getattr(p_test, l_methodName)
    l_data = {
      "file" : l_file,
      "line" : inspect.getsourcelines(l_method)[1],
      "class" : p_test.__class__.__name__,
      "method" : l_methodName
    }
    if p_message is not None:
      l_data["message"] = p_message
    return l_data


  def run(self, p_test):
    if self.verbosity > 1:
      l_allTests = []
      for c_item in p_test._tests:
        if hasattr(c_item, "_tests"):
          for c_test in c_item._tests:
            l_allTests.append(c_test)
        else:
          l_allTests.append(c_item)

    l_res  = super(JsonTestRunner, self).run(p_test)
    l_data = {
      "tests" : l_res.testsRun,
      "success" : l_res.testsRun - len(l_res.errors) - len(l_res.failures),
      "errors" : len(l_res.errors),
      "failures" : len(l_res.failures),
      "skipped" : len(l_res.skipped),
      "expectedFailures" : len(l_res.expectedFailures),
      "unexpectedSuccesses" : len(l_res.unexpectedSuccesses)
    }

    if self.verbosity > 1:
      l_errorTests  =  set([x for x in l_res.errors])
      l_errorTests  = l_errorTests | set([x[0] for x in l_res.failures])
      l_errorTests  = l_errorTests | set([x[0] for x in l_res.skipped])
      l_errorTests  = l_errorTests | set([x[0] for x in l_res.expectedFailures])
      l_errorTests  = l_errorTests | set([x    for x in l_res.unexpectedSuccesses])
      l_successTests = [ x for x in l_allTests if not x in l_errorTests ]
      l_data["details"] = {
        "success"             : [ self._getTestInfo(x)          for x in l_successTests         ],
        "errors"              : [ self._getTestInfo(x[0], x[1]) for x in l_res.errors           ],
        "failures"            : [ self._getTestInfo(x[0], x[1]) for x in l_res.failures         ],
        "skipped"             : [ self._getTestInfo(x[0], x[1]) for x in l_res.skipped          ],
        "expectedFailures"    : [ self._getTestInfo(x[0], x[1]) for x in l_res.expectedFailures ],
        "unexpectedSuccesses" : [ self._getTestInfo(x) for x in l_res.unexpectedSuccesses       ],
      }

    self.m_origStream.write(json.dumps(l_data))
    return l_res

class XtdTestProgram(unittest.TestProgram):
  def __init__(self, *p_args, **p_kwds):
    self.format = None
    super(XtdTestProgram, self).__init__(*p_args, **p_kwds)

  def _getParentArgParser(self):
    l_parser = super(XtdTestProgram, self)._getParentArgParser()
    l_parser.add_argument('--format', dest='format', action='store', help='Set output format : text or json')
    return l_parser

  def runTests(self):
    if self.format == "json":
      self.testRunner = JsonTestRunner
    l_parser = super(XtdTestProgram, self).runTests()

class XtdTestLoader(unittest.TestLoader):
  def __init__(self):
    super(XtdTestLoader, self).__init__()
    self.m_data = []
    self._loadTests()

  def _splitToPackage(self, p_file):
    if p_file.startswith("./"):
      p_file = p_file[2:]
    l_dir, l_name = os.path.split(p_file)
    l_module      = l_name.split(".")[0]
    l_package     = l_dir.replace("/", ".")
    return l_module, l_package

  def _loadTests(self):
    l_files = []
    for c_root, c_dirs, c_files in os.walk("."):
      l_files += [ os.path.join(c_root,x) for x in c_files
                   if x.startswith("test") and x.endswith(".py") ]

    for c_file in l_files:
      l_tests                 = []
      l_source                = c_file.replace("/test/", "/").replace("test_", "")
      l_testModule, l_testPkg = self._splitToPackage(c_file)
      l_srcModule, l_srcPkg   = self._splitToPackage(l_source)
      l_srcName               = "%s.%s" % (l_srcPkg,  l_srcModule)
      l_testName              = "%s.%s" % (l_testPkg, l_testModule)

      l_module = importlib.import_module(l_testName)
      for c_className in [ x for x in dir(l_module) if x.endswith("Test") ]:
        l_class    = getattr(l_module, c_className)
        l_testCase = self.loadTestsFromTestCase(l_class)
        self.m_data.append({
          "test_module"  : l_testName,
          "test_package" : l_testModule,
          "src_module"   : l_srcName,
          "src_package"  : l_srcModule,
          "test_class"   : c_className,
          "object"       : l_testCase,
          "cases"        : [ x for x in l_testCase ]
        })

  @staticmethod
  def _matchTest(p_name, p_item):
    if p_name == p_item["test_module"] or \
       p_name == p_item["test_package"] or \
       p_name == p_item["test_class"] or \
       p_name == p_item["src_module"] or \
       p_name == p_item["src_package"] or \
       p_name == "%s.%s" % (p_item["test_module"], p_item["test_class"]):
      return True

    for c_case in p_item["cases"]:
      l_name = c_case._testMethodName
      l_fullName = "%s.%s.%s" % (p_item["test_module"], p_item["test_class"], l_name)
      if p_name == l_name or p_name == l_fullName:
        return True

    return False

  def loadTestsFromName(self, p_name, p_module=None):
    l_suite = unittest.TestSuite()
    for c_item in self.m_data:
      if self._matchTest(p_name, c_item):
        l_suite.addTests(c_item["object"])
    return l_suite

  def loadTestsFromModule(self, p_module, p_useLoadTests=True):
    l_suite = unittest.TestSuite()
    for c_item in self.m_data:
      l_suite.addTests(c_item["object"])
    return l_suite

if __name__ == "__main__":
  l_loader = XtdTestLoader()
  l_main   = XtdTestProgram(testLoader=l_loader)
