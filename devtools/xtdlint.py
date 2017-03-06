#!/usr/bin/env python
# -*- mode:python -*-
# -*- coding:utf-8 -*-
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import os
import sys
import pylint
import json

from pylint.interfaces import IReporter
from pylint.reporters  import BaseReporter
from pylint.lint       import Run, PyLinter

#------------------------------------------------------------------#

def __sys_path():
  l_path = os.path.realpath(os.path.dirname(__file__))
  sys.path.insert(0, os.path.dirname(l_path))

__sys_path()

#------------------------------------------------------------------#

class JsonReporter(BaseReporter):
  """reports messages and layouts in plain text"""

  __implements__ = IReporter
  name = 'text'
  extension = 'txt'
  line_format = '{C}:{line:3d},{column:2d}: {msg} ({symbol})'

  def __init__(self, linter, output=None):
    BaseReporter.__init__(self, output)
    self.m_linter = linter
    self.m_data   = {}

  def handle_message(self, p_msg):
    if not p_msg.module in self.m_data:
      self.m_data[p_msg.module] = {
        "abspath"  : p_msg.abspath,
        "path"     : p_msg.path,
        "items"    : []
      }

    self.m_data[p_msg.module]["items"].append({
      "msg_id"   : p_msg.msg_id,
      "symbol"   : p_msg.symbol,
      "msg"      : p_msg.msg,
      "C"        : p_msg.C,
      "category" : p_msg.category,
      "obj"      : p_msg.obj,
      "line"     : p_msg.line,
      "column"   : p_msg.column
    })

  def _getStats(self):
    l_categories = {}
    l_messages = {}
    for c_module in self.m_data.values():
      for c_item in c_module["items"]:
        l_val = l_categories.get(c_item["category"], 0)
        l_categories[c_item["category"]] = (l_val + 1)
        l_val = l_messages.get(c_item["symbol"], 0)
        l_messages[c_item["symbol"]] = (l_val + 1)

    return {
      "by_cat"  : l_categories,
      "by_type" : l_messages
    }


  def _display(self, layout):
    print(json.dumps({
      "report"   : {
        "cloc" : {
          "total" : self.m_linter.stats['total_lines'],
          "code" : self.m_linter.stats['code_lines'],
          "empty" : self.m_linter.stats['empty_lines'],
          "comment" : self.m_linter.stats['comment_lines'],
          "docstring" : self.m_linter.stats['docstring_lines'],
          "duplicated" : self.m_linter.stats['nb_duplicated_lines'],
          "percent_duplicated" : self.m_linter.stats['percent_duplicated_lines'],
        },
        "statement" : {
          "total" : self.m_linter.stats['statement'],
          "class" : self.m_linter.stats['class'],
          "function" : self.m_linter.stats['function'],
          "module" : self.m_linter.stats['module'],
          "method" : self.m_linter.stats['method'],
        },
        "undoc" : {
         "module"   : self.m_linter.stats['undocumented_module'],
         "function" : self.m_linter.stats['undocumented_function'],
         "class"    : self.m_linter.stats['undocumented_class'],
         "method"   : self.m_linter.stats['undocumented_method'],
        },
        "score" : self.m_linter.stats['global_note'],
        "errors" : self._getStats()
      },
      "errors" : self.m_data
    }))


class XtdLint(PyLinter):
  def __init__(self, *p_args, **p_kwds):
    super(XtdLint, self).__init__(*p_args, **p_kwds)
    self.set_reporter(JsonReporter(self))

if __name__ == "__main__":
  Run.LinterClass = XtdLint
  Run(sys.argv[1:])
