# -*- mode: python; coding: utf-8 -*-
#------------------------------------------------------------------------------

import os
import sys
import json
import xml.etree.ElementTree as ET

#------------------------------------------------------------------------------

__author__       = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__    = "Copyright (C) 2016 Xavier MARCELET"
__version__      = "1.2.0"
__description__  = "Generate doxygen's documentation coverage report"
__url__          = "https://github.com/psycofdj/coverxygen"
__download_url__ = "https://github.com/psycofdj/coverxygen/tarball/%s" % __version__
__keywords__     = ['doxygen', 'coverage', 'python']
__classifiers__  = [
  "Development Status :: 5 - Production/Stable",
  "Environment :: Console",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
  "Operating System :: Unix",
  "Programming Language :: Python :: 2",
  "Programming Language :: Python :: 3"
]

#------------------------------------------------------------------------------

class Coverxygen(object):
  def __init__(self, p_path, p_output, p_scope, p_kind, p_prefix, p_json, p_srcDir, p_verbose):
    self.m_path    = p_path
    self.m_output  = p_output
    self.m_scope   = p_scope
    self.m_kind    = p_kind
    self.m_prefix  = p_prefix
    self.m_json    = p_json
    self.m_srcDir  = p_srcDir
    self.m_verbose = p_verbose
   
  @staticmethod
  def error(p_format, *p_args):
    l_message = p_format % p_args
    sys.stderr.write("error: %s" % l_message)
    sys.exit(1)

  def verbose(self, p_fmt, *p_args):
    if self.m_verbose:
      l_msg = p_fmt % p_args
      sys.stderr.write(l_msg + "\n")


  def process_item(self, p_item, p_path, p_result):
    l_file   = p_path
    l_lineNo = 1
    l_name   = ""
    l_scope  = p_item.get('prot')
    l_kind   = p_item.get('kind')

    if l_scope and (not l_scope in self.m_scope):
      return
    if not l_kind in self.m_kind:
      return


    l_documented = False
    for c_key in ('briefdescription', 'detaileddescription', 'inbodydescription'):
      if p_item.findall("./%s/" % (c_key)):
        l_documented = True
        break

    l_def = p_item.find('./definition')
    l_nam = p_item.find('./name')
    l_loc = p_item.find('./location')

    if l_loc is not None:
      l_file   = l_loc.get('file')
      l_lineNo = l_loc.get('line')
      if l_lineNo is None:
        return
      l_lineNo = int(l_lineNo)

    self.verbose("processing item of type %s at %s:%d", l_kind, l_file, l_lineNo)

    if not l_file.startswith("/"):
      l_file = os.path.join(self.m_srcDir, l_file)

    if not l_file.startswith(self.m_prefix):
        return

    if l_def is not None:
      l_name = l_def.text
    elif l_nam is not None:
      l_name = l_nam.text
    else:
      l_name = p_item.get('id')

    if not l_file in p_result:
      p_result[l_file] = []

    p_result[l_file].append({
      "symbol" : l_name,
      "documented" : l_documented,
      "line" : l_lineNo,
      "file" : l_file
    })

  def process_file(self, p_path):
    self.verbose("processing file : %s", p_path)

    l_defs  = {}
    l_files = []
    try:
      l_tree = ET.parse(p_path)
    except ET.ParseError as l_error:
      self.error("failed to parse ", p_path, l_error)

    for c_def in l_tree.findall("./compounddef//memberdef"):
      self.process_item(c_def, p_path, l_defs)
    for c_def in l_tree.findall("./compounddef"):
      self.process_item(c_def, p_path, l_defs)

    if len(l_defs):
      l_files.append(l_defs)

    return l_files

  def process(self):
    l_index = os.path.join(self.m_path, "index.xml")
    if not os.path.exists(l_index):
      self.error("could not find root index.xml file %s", l_index)
    l_tree = ET.parse(l_index)

    if self.m_output == "-":
      l_output = sys.stdout
    else:
      l_output = open(self.m_output, "w")

    l_result = []
    for c_entry in l_tree.findall('compound'):
      if c_entry.get('kind') in ['dir']:
        continue
      l_file = os.path.join (self.m_path, "%s.xml" % (c_entry.get('refid')))
      l_result += self.process_file(l_file)

    if not self.m_json:
      for c_data in l_result:
        for c_file, c_data in c_data.items():
          l_output.write("SF:%s\n" % c_file)
          for c_item in c_data:
            l_value = 1
            if not c_item["documented"]:
              l_value = -1
            l_output.write("DA:%d,%d\n" % (c_item["line"], l_value))
          l_output.write("end_of_record\n")
    else:
      l_output.write(json.dumps(l_result, indent=2))

# Local Variables:
# ispell-local-dictionary: "american"
# End:
