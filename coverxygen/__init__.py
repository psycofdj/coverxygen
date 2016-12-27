# -*- mode: python; coding: utf-8 -*-
#------------------------------------------------------------------------------

import os
import sys
import json
import xml.etree.ElementTree as ET

#------------------------------------------------------------------------------

__author__       = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__    = "Copyright (C) 2016 Xavier MARCELET"
__version__      = "1.1.0"
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

  @staticmethod
  def error(p_format, *p_args):
    l_message = p_format % p_args
    sys.stderr.write("error: %s" % l_message)
    sys.exit(1)


  @staticmethod
  def process_item(p_item, p_path, p_result, p_scope, p_kind, p_prefix):
    l_file   = p_path
    l_lineNo = 1
    l_name   = ""
    l_scope  = p_item.get('prot')
    l_kind   = p_item.get('kind')

    if l_scope and (not l_scope in p_scope):
      return
    if not l_kind in p_kind:
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

    if not l_file.startswith(p_prefix):
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

  def process_file(self, p_path, p_scope, p_kind, p_prefix):
    l_defs  = {}
    l_files = []
    try:
      l_tree = ET.parse(p_path)
    except ET.ParseError as l_error:
      print ("failed to parse ", p_path, l_error)
      sys.exit(1)

    for c_def in l_tree.findall("./compounddef//memberdef"):
      self.process_item(c_def, p_path, l_defs, p_scope, p_kind, p_prefix)
    for c_def in l_tree.findall("./compounddef"):
      self.process_item(c_def, p_path, l_defs, p_scope, p_kind, p_prefix)


    if len(l_defs):
      l_files.append(l_defs)
    return l_files

  def process(self, p_path, p_output, p_scope, p_kind, p_prefix, p_json):
    l_index = os.path.join(p_path, "index.xml")
    if not os.path.exists(l_index):
      self.error("could not find root index.xml file %s", l_index)
    l_tree = ET.parse(l_index)

    if p_output == "-":
      l_output = sys.stdout
    else:
      l_output = open(p_output, "w")

    l_result = []
    for c_entry in l_tree.findall('compound'):
      if c_entry.get('kind') in ['dir']:
        continue
      l_file = os.path.join (p_path, "%s.xml" % (c_entry.get('refid')))
      l_result += self.process_file(l_file, p_scope, p_kind, p_prefix)

    if not p_json:
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
