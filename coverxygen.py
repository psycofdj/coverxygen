#!/usr/bin/env python
# -*- mode: python; coding: utf-8 -*-

__author__       = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__    = "Copyright (C) 2016 Xavier MARCELET"
__version__      = "0.1.2"
__description__  = "Generate doxygen's documentation coverage report"
__url__          = "https://github.com/psycofdj/coverxygen"
__download_url__ = "https://github.com/psycofdj/coverxygen/tarball/%s" % __version__
__keywords__     = ['doxygen', 'coverage', 'python']
__classifiers__  = [
  "Development Status :: 2 - Pre-Alpha",
  "Environment :: Console",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
  "Operating System :: Unix",
  "Programming Language :: Python :: 3 :: Only",
]

import os
import sys
import argparse
import xml.etree.ElementTree as ET
from argparse import RawTextHelpFormatter


def error(*objs):
    print("error: ", *objs, end='\n', file=sys.stderr)
    sys.exit(1)


def process_item(p_item, p_path, p_result, p_scope, p_kind):
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

def process_file(p_path, p_output, p_scope, p_kind):
  l_defs = {}

  try:
    l_tree = ET.parse(p_path)
  except ET.ParseError as l_error:
    print ("failed to parse ", fullpath, l_error)
    sys.exit(1)

  for c_def in l_tree.findall("./compounddef//memberdef"):
    process_item(c_def, p_path, l_defs, p_scope, p_kind)
  for c_def in l_tree.findall("./compounddef"):
    process_item(c_def, p_path, l_defs, p_scope, p_kind)

  for c_file, c_data in l_defs.items():
    p_output.write("SF:%s\n" % c_file)
    for c_item in c_data:
      l_value = 1
      if not c_item["documented"]:
        l_value = -1
      p_output.write("DA:%d,%d\n" % (c_item["line"], l_value))
    p_output.write("end_of_record\n")


def process(p_path, p_output, p_scope, p_kind):
  l_index = os.path.join(p_path, "index.xml")
  if not os.path.exists(l_index):
    error("could not find root index.xml file", l_index)
  l_tree = ET.parse(l_index)

  if "-" == p_output:
    l_output = sys.stdout
  else:
    l_output = open(p_output, "w")

  for entry in l_tree.findall('compound'):
    if entry.get('kind') in ('dir'):
      continue
    l_file = os.path.join (p_path, "%s.xml" %(entry.get('refid')))
    process_file(l_file, l_output, p_scope, p_kind)


def main():
  l_parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)
  l_parser.add_argument("--xml-dir", action="store", help ="path to generated doxygen XML directory", required=True)
  l_parser.add_argument("--output",  action="store", help ="destination output file (- for stdout)", required=True)
  l_parser.add_argument("--scope",
                        action="store",
                        help="comma-separated list of items's scope to include : \n"
                        " - public    : public member elements\n"
                        " - protected : protected member elements\n"
                        " - private   : private member elements\n"
                        " - all       : all above\n",
                        default="all")

  l_parser.add_argument("--kind",
                        action="store",
                        help="comma-separated list of items's type to include : \n"
                        " - enum      : enum definitions \n"
                        " - typedef   : typedef definitions\n"
                        " - variable  : variable definitions\n"
                        " - function  : function definitions\n"
                        " - class     : class definitions\n"
                        " - struct    : struct definitions\n"
                        " - define    : macro definitions\n"
                        " - file      : macro definitions\n"
                        " - namespace : macro definitions\n"
                        " - page      : macro definitions\n"
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
  process(l_result.xml_dir, l_result.output, l_result.scope, l_result.kind)

if __name__ == "__main__":
  main()
