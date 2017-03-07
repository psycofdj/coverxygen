# -*- mode: python; coding: utf-8 -*-
#------------------------------------------------------------------------------

from __future__ import print_function

import sys
import argparse
from argparse import RawTextHelpFormatter

import coverxygen

#------------------------------------------------------------------------------

def main():
  if "--version" in sys.argv:
    print(coverxygen.__version__)
    sys.exit(0)

  l_parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, prog="coverxygen")
  l_parser.add_argument("--version",
                        action="store_true",
                        help ="prints version",
                        default=False)
  l_parser.add_argument("--verbose",
                        action="store_true",
                        help ="enabled verbose output",
                        default=False)
  l_parser.add_argument("--json",
                        action="store_true",
                        help="(deprecated) same as --format json-legacy",
                        default=None)
  l_parser.add_argument("--format",
                        action="store",
                        help="output file format : \n"
                        "lcov        : lcov compatible format (default)\n"
                        "json-legacy : legacy json format\n"
                        "lcov        : simpler json format\n",
                        default="lcov")
  l_parser.add_argument("--xml-dir",
                        action="store",
                        help ="path to generated doxygen XML directory",
                        required=True)
  l_parser.add_argument("--output",
                        action="store",
                        help ="destination output file (- for stdout)",
                        required=True)
  l_parser.add_argument("--src-dir",
                        action="store",
                        help ="root source directory used to match prefix for"
                        "relative path generated files",
                        required=True)
  l_parser.add_argument("--prefix",
                        action="store",
                        help ="keep only file matching given path prefix",
                        default="/")
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

  if l_result.scope == "all":
    l_result.scope = "public,protected,private"
  if l_result.kind == "all":
    l_result.kind = "enum,typedef,variable,function,class,struct,define,file,namespace,page"

  l_result.scope = l_result.scope.split(",")
  l_result.kind  = l_result.kind.split(",")

  if not l_result:
    sys.stderr.write("error: couldn't parse parameters\n")
    sys.exit(1)

  l_format = l_result.format
  if l_result.json:
    l_format = "json-legacy"
  l_obj = coverxygen.Coverxygen(l_result.xml_dir,
                                l_result.output,
                                l_result.scope,
                                l_result.kind,
                                l_result.prefix,
                                l_format,
                                l_result.src_dir,
                                l_result.verbose)
  try:
    l_obj.process()
  except RuntimeError as l_error:
    sys.stderr.write("error: %s\n" % str(l_error))
    sys.exit(1)

if __name__ == "__main__":
  main()

# Local Variables:
# ispell-local-dictionary: "american"
# End:
