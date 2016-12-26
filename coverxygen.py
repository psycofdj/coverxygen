#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

__author__       = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__    = "Copyright (C) 2016 Xavier MARCELET"
__version__      = "1.0.0"
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

import os
import sys
import argparse
import json
import xml.etree.ElementTree as ET
from argparse import RawTextHelpFormatter


def error(p_format, *p_args):
  l_message = p_format % p_args
  sys.stderr.write("error: %s" % l_message)
  sys.exit(1)


def process_item(p_item, p_path, p_result, p_scope, p_kind, p_prefix):
    l_file   = p_path
    l_lineNo = 1
    l_colNo  = 1
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

    d_def = p_item.find('./definition')
    d_nam = p_item.find('./name')
    d_loc = p_item.find('./location')

    if d_loc is not None:
      l_file   = d_loc.get('file')
      l_lineNo = d_loc.get('line')
      if l_lineNo is None:
        return
      l_lineNo = int(l_lineNo)

    if not l_file.startswith(p_prefix):
      return

    if d_def is not None:
      l_name = d_def.text
    elif d_nam is not None:
      l_name = d_nam.text
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

def process_file(p_path, p_output, p_scope, p_kind, p_prefix):
  l_defs  = {}
  l_files = []
  try:
    l_tree = ET.parse(p_path)
  except ET.ParseError as l_error:
    print ("failed to parse ", fullpath, l_error)
    sys.exit(1)

  for c_def in l_tree.findall("./compounddef//memberdef"):
    process_item(c_def, p_path, l_defs, p_scope, p_kind, p_prefix)
  for c_def in l_tree.findall("./compounddef"):
    process_item(c_def, p_path, l_defs, p_scope, p_kind, p_prefix)


  if len(l_defs):
    l_files.append(l_defs)
  return l_files

def process(p_path, p_output, p_scope, p_kind, p_prefix, p_json):
  l_index = os.path.join(p_path, "index.xml")
  if not os.path.exists(l_index):
    error("could not find root index.xml file %s", l_index)
  l_tree = ET.parse(l_index)

  if "-" == p_output:
    l_output = sys.stdout
  else:
    l_output = open(p_output, "w")

  l_result = []
  for entry in l_tree.findall('compound'):
    if entry.get('kind') in ('dir'):
      continue
    l_file = os.path.join (p_path, "%s.xml" %(entry.get('refid')))
    l_result += process_file(l_file, l_output, p_scope, p_kind, p_prefix)

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

def main():
  if "--version" in sys.argv:
    print(__version__)
    sys,exit(0)

  l_parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
  l_parser.add_argument("--version", action="store_true", help ="prints version",                          default=False)
  l_parser.add_argument("--json",    action="store_true", help ="output raw data as json file format",     default=False)
  l_parser.add_argument("--xml-dir", action="store",      help ="path to generated doxygen XML directory", required=True)
  l_parser.add_argument("--output",  action="store",      help ="destination output file (- for stdout)",  required=True)
  l_parser.add_argument("--prefix",  action="store",      help ="keep only file matching given prefix (default /)", default="/")
  l_parser.add_argument("--scope",
                        action="store",
                        help="comma-separated list of items' scope to include : \n"
                        " - public    : public member elements\n"
                        " - protected : protected member elements\n"
                        " - private   : private member elements\n"
                        " - all       : all above\n",
                        default="all")

  l_parser.add_argument("--kind",
                        action="store",
                        help="comma-separated list of items' type to include : \n"
                        " - enum      : enum definitions \n"
                        " - typedef   : typedef definitions\n"
                        " - variable  : variable definitions\n"
                        " - function  : function definitions\n"
                        " - class     : class definitions\n"
                        " - struct    : struct definitions\n"
                        " - define    : define definitions\n"
                        " - file      : file definitions\n"
                        " - namespace : namespace definitions\n"
                        " - page      : page definitions\n"
                        " - all       : all above\n",
                        default="all")
  l_result = l_parser.parse_args()

  if "all" == l_result.scope:
    l_result.scope = "public,protected,private"
  if "all" == l_result.kind:
    l_result.kind = "enum,typedef,variable,function,class,struct,define,file,namespace,page"

  l_result.scope = l_result.scope.split(",")
  l_result.kind = l_result.kind.split(",")

  if not l_result:
    error("couldn't parse parameters")
  process(l_result.xml_dir, l_result.output, l_result.scope, l_result.kind, l_result.prefix, l_result.json)

if __name__ == "__main__":
  main()

# Local Variables:
# ispell-local-dictionary: "american"
# End:
