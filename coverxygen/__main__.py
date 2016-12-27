# -*- mode: python; coding: utf-8 -*-
#------------------------------------------------------------------------------

import sys
import argparse
import coverxygen
from argparse import RawTextHelpFormatter

#------------------------------------------------------------------------------

def main():
  if "--version" in sys.argv:
    print(coverxygen.__version__)
    sys.exit(0)

  l_parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, prog="coverxygen")
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
  l_obj = coverxygen.Coverxygen()
  l_obj.process(l_result.xml_dir, l_result.output, l_result.scope, l_result.kind, l_result.prefix, l_result.json)

if __name__ == "__main__":
  main()

# Local Variables:
# ispell-local-dictionary: "american"
# End:
