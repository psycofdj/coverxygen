# -*- mode: python; coding: utf-8 -*-
#------------------------------------------------------------------------------

from __future__ import print_function

import sys
import argparse
from argparse import RawTextHelpFormatter

import coverxygen

#------------------------------------------------------------------------------

def main():
  l_parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter, prog="coverxygen", add_help=False)
  l_requiredArgs = l_parser.add_argument_group("required arguments")
  l_optionalArgs = l_parser.add_argument_group("optional arguments")

  l_optionalArgs.add_argument("-h", "--help",
                              action="help",
                              help="show this help message and exit")
  l_optionalArgs.add_argument("--version",
                              action="version",
                              help ="print version and exit",
                              version=coverxygen.__version__)
  l_optionalArgs.add_argument("--verbose",
                              action="store_true",
                              help ="enabled verbose output",
                              default=False)
  l_optionalArgs.add_argument("--json",
                              action="store_true",
                              help="(deprecated) same as --format json-legacy",
                              default=None)
  l_optionalArgs.add_argument("--format",
                              action="store",
                              help="output file format :\n"
                              "lcov         : lcov compatible format (default)\n"
                              "json-v3      : json format which includes summary information\n"
                              "json-v2      : simpler json format\n"
                              "json-v1      : legacy json format\n"
                              "json         : (deprecated) same as json-v2\n"
                              "json-legacy  : (deprecated) same as json-v1\n"
                              "json-summary : summary in json format\n"
                              "summary      : textual summary table format\n",
                              default="lcov")
  l_optionalArgs.add_argument("--prefix",
                              action="store",
                              help ="keep only file matching given path prefix",
                              default=None)
  l_optionalArgs.add_argument("--exclude",
                              action="append",
                              help="exclude files whose absolute path matches the given regular expression <EXLUDE>;\n"
                              "this option can be given multiple times",
                              default=[])
  l_optionalArgs.add_argument("--include",
                              action="append",
                              help="include files whose absolute path matches the given regular expression <INCLUDE>\n"
                              "even if they also match an exclude filter (see --exclude) or if they\n"
                              "are not matching the patch prefix (see --prefix);\n"
                              "this option can be given multiple times",
                              default=[])
  l_optionalArgs.add_argument("--scope",
                              action="store",
                              help="comma-separated list of item scopes to include :\n"
                              " - public    : public member and global elements\n"
                              " - protected : protected member elements\n"
                              " - private   : private member elements\n"
                              " - all       : all above\n",
                              default="all")
  l_optionalArgs.add_argument("--kind",
                              action="store",
                              help="comma-separated list of item types to include : \n"
                              " - enum      : enum definitions\n"
                              " - enumvalue : enum value definitions\n"
                              "               Note: a single undocumented enum value will mark\n"
                              "               the containing enum as undocumented\n"
                              " - friend    : friend declarations\n"
                              " - typedef   : type definitions\n"
                              " - variable  : variable definitions\n"
                              " - function  : function definitions\n"
                              " - signal    : Qt signal definitions\n"
                              " - slot      : Qt slot definitions\n"
                              " - class     : class definitions\n"
                              " - struct    : struct definitions\n"
                              " - union     : union definitions\n"
                              " - define    : define definitions\n"
                              " - file      : files\n"
                              " - namespace : namespace definitions\n"
                              " - page      : documentation pages\n"
                              " - all       : all above\n",
                              default="all")

  l_requiredArgs.add_argument("--xml-dir",
                              action="store",
                              help ="path to generated doxygen XML directory",
                              required=True)
  l_requiredArgs.add_argument("--output",
                              action="store",
                              help ="destination output file (- for stdout)",
                              required=True)
  l_requiredArgs.add_argument("--src-dir",
                              action="store",
                              help ="root source directory used to match prefix for "
                              "relative path generated files",
                              required=True)

  l_result = l_parser.parse_args()

  if l_result.scope == "all":
    l_result.scope = "public,protected,private"
  if l_result.kind == "all":
    l_result.kind = "enum,enumvalue,friend,typedef,variable,function,signal,slot,class,struct,union,define,file,namespace,page"

  l_formatMapping = {
    "json"       : "json-v2",
    "json-legacy": "json-v1"
  }
  if l_result.format in l_formatMapping:
    l_result.format = l_formatMapping[l_result.format]

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
                                l_format,
                                l_result.src_dir,
                                l_result.prefix,
                                l_result.verbose,
                                l_result.exclude,
                                l_result.include)
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
