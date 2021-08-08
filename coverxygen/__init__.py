# -*- mode: python; coding: utf-8 -*-
#------------------------------------------------------------------------------

import os
import sys
import json
import re
import xml.etree.ElementTree as ET
from functools import reduce

#------------------------------------------------------------------------------

__author__       = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__    = "Copyright (C) 2016 Xavier MARCELET"
__version__      = "1.6.0"
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
  def __init__(self, p_path, p_output, p_scope, p_kind, p_format, p_rootDir, p_prefix=None, p_verbose=False, p_excludes=[], p_includes=[]):
    self.m_root     = p_path
    self.m_output   = p_output
    self.m_scope    = p_scope
    self.m_kind     = p_kind
    self.m_prefix   = os.path.abspath(p_prefix) if p_prefix is not None else ""
    self.m_format   = p_format
    self.m_rootDir  = os.path.abspath(p_rootDir) if p_rootDir is not None else ""
    self.m_verbose  = p_verbose
    self.m_excludes = p_excludes
    self.m_includes = p_includes

  @staticmethod
  def error(p_format, *p_args):
    try:
      l_msg = p_format % p_args
    except TypeError:
      l_msg = "invalid message format '%s' with args '%s'" % (p_format, str(p_args))
    raise RuntimeError(l_msg)

  def verbose(self, p_fmt, *p_args):
    if self.m_verbose:
      l_msg = p_fmt % p_args
      sys.stderr.write(l_msg + "\n")

  @staticmethod
  def get_index_path_from_root(p_root):
    l_index = os.path.join(p_root, "index.xml")
    if not os.path.exists(l_index):
      Coverxygen.error("could not find root index.xml file %s", l_index)
    return l_index

  @staticmethod
  def get_file_path_from_root(p_root, p_name):
    l_fileName = "%s.xml" % p_name
    l_filePath = os.path.join(p_root, l_fileName)
    if not os.path.exists(l_filePath):
      Coverxygen.error("could not find indexed file %s", l_filePath)
    return l_filePath

  @staticmethod
  def get_xmldoc_from_file(p_file):
    try:
      l_doc = ET.parse(p_file)
    except BaseException as l_error:
      Coverxygen.error("error while parsing xml file %s : %s", p_file, str(l_error))
    return l_doc

  @staticmethod
  def extract_name(p_node):
    l_id       = p_node.get("id")
    l_def      = p_node.find("./definition")
    l_nam      = p_node.find("./name")
    l_compName = p_node.find("./compoundname")
    if l_def is not None:
      return l_def.text
    if l_nam is not None:
      return l_nam.text
    if l_compName is not None:
      return l_compName.text
    if l_id is not None :
      return l_id
    Coverxygen.error("unable to deduce name from node %s", ET.tostring(p_node))
    return None

  @staticmethod
  def extract_kind(p_node):
    l_kind = p_node.get("kind")

    if l_kind == 'friend':
      l_isDefinition = (p_node.get('inline') == 'yes' or p_node.find('initializer') is not None)
      if l_isDefinition:
        l_friendTypeNode = p_node.find('type')
        if l_friendTypeNode is not None:
          l_friendType = l_friendTypeNode.text
          if l_friendType == 'friend class':
            l_kind = 'class'
          elif l_friendType == 'friend struct':
            l_kind = 'struct'
          elif l_friendType == 'friend union':
            l_kind = 'union'
          else:
            l_kind = 'function'

    return l_kind

  @staticmethod
  def extract_documented(p_node):
    for c_key in ["briefdescription", "detaileddescription", "inbodydescription"]:
      l_node = p_node.find("./%s" % c_key)
      if l_node is not None:
        l_content = "".join(l_node.itertext()).strip()
        if l_content:
          return True
    return False

  @staticmethod
  def extract_location(p_node, p_file, p_rootDir):
    l_file = p_file
    l_line = 1
    l_loc  = p_node.find('./location')
    if l_loc is not None:
      l_file = l_loc.get("file")
      l_line = l_loc.get("line", 1)
      if (l_line is None) or (l_file is None):
        Coverxygen.error("unable to extract location from file %s, node : %s",
                         p_file, ET.tostring(p_node))
      l_line = int(l_line)
      l_file = Coverxygen.get_absolute_path(l_file, p_rootDir)
    else:
      l_file = os.path.abspath(l_file)
    return l_file, l_line

  @staticmethod
  def get_absolute_path(p_file, p_rootDir):
    l_path = p_file
    if not os.path.isabs(p_file):
      l_path = os.path.join(p_rootDir, p_file)
    return os.path.abspath(l_path)

  @staticmethod
  def matches_regex_list(p_string, p_regExList):
    for c_regExPattern in p_regExList:
      if re.match(c_regExPattern, p_string):
        return True
    return False

  def matches_include(self, p_file):
    return Coverxygen.matches_regex_list(p_file, self.m_includes)

  def matches_exclude(self, p_file):
    return Coverxygen.matches_regex_list(p_file, self.m_excludes)


  def should_filter_out(self, p_node, p_file, p_line):
    l_scope  = p_node.get('prot')
    l_kind   = self.extract_kind(p_node)

    if l_scope is None:
      l_scope = "public"

    if (not l_scope in self.m_scope) or (not l_kind in self.m_kind):
      return True

    if not self.matches_include(p_file):
      if not p_file.startswith(self.m_prefix):
        return True
      if self.matches_exclude(p_file):
        return True

    self.verbose("found symbol of type %s at %s:%d", l_kind, p_file, p_line)
    return False

  def process_enumValue(self, p_node, p_enum):
    l_name         = self.extract_name(p_node)
    l_isDocumented = self.extract_documented(p_node)
    l_enumValue = {
      "symbol"    : l_name,
      "documented": l_isDocumented,
      "kind"      : "enumvalue",
      # enum values do not have location information, so we use the location
      # of the surrounding enum
      "line"      : p_enum["line"],
      "file"      : p_enum["file"]
    }
    return l_enumValue

  def process_enum(self, p_node, p_enum):
    if not 'enumvalue' in self.m_kind:
      return []
    l_enumValueNodes = p_node.findall("./enumvalue")
    l_enumValues = []
    for c_enumValueNode in l_enumValueNodes:
      l_enumValues.append(self.process_enumValue(c_enumValueNode, p_enum))
    return l_enumValues

  def process_symbol(self, p_node, p_filePath):
    l_name         = self.extract_name(p_node)
    l_kind         = self.extract_kind(p_node)
    l_isDocumented = self.extract_documented(p_node)
    l_file, l_line = self.extract_location(p_node, p_filePath, self.m_rootDir)
    if self.should_filter_out(p_node, l_file, l_line):
      return []
    l_symbol = {
      "symbol"     : l_name,
      "documented" : l_isDocumented,
      "kind"       : l_kind,
      "line"       : l_line,
      "file"       : l_file
    }
    l_symbols = [l_symbol]
    if l_kind == 'enum':
      l_symbols.extend(self.process_enum(p_node, l_symbol))
    return l_symbols

  def process_file(self, p_filePath):
    self.verbose("processing file : %s", p_filePath)
    l_symbols   = []
    l_xmlDoc    = self.get_xmldoc_from_file(p_filePath)
    l_xmlNodes  = l_xmlDoc.findall("./compounddef//memberdef")
    l_xmlNodes += l_xmlDoc.findall("./compounddef")
    for c_def in l_xmlNodes:
      l_symbols.extend(self.process_symbol(c_def, p_filePath))
    return l_symbols

  def process_index(self, p_xmlDoc):
    l_symbols = []
    for c_entry in p_xmlDoc.findall('compound'):
      l_kind  = c_entry.get("kind")
      l_refid = c_entry.get("refid")
      if not l_kind:
        self.error("missing kind attribute on compound element : %s", str(c_entry))
      if not l_refid:
        self.error("missing refid attribute on compound element : %s", str(c_entry))
      if l_kind == "dir":
        continue
      l_filePath = self.get_file_path_from_root(self.m_root, l_refid)
      l_symbols.extend(self.process_file(l_filePath))
    return l_symbols

  @staticmethod
  def group_symbols_by_file(p_symbols):
    l_results = {}
    for c_symbol in p_symbols:
      if not c_symbol:
        continue
      l_file = c_symbol["file"]
      if not l_file in l_results:
        l_results[l_file] = []
      l_results[l_file].append(c_symbol)
    return l_results

  def output_results(self, p_symbols):
    l_outStream = self.output_get_stream(self.m_output)
    if self.m_format == "summary":
      self.output_print_summary(l_outStream, p_symbols)
    elif self.m_format == "json-summary":
      self.output_print_json_summary(l_outStream, p_symbols)
    else:
      l_symbolsByFile = Coverxygen.group_symbols_by_file(p_symbols)
      if self.m_format == "json-v3":
        self.output_print_json_v3(l_outStream, p_symbols, l_symbolsByFile)
      elif self.m_format == "json-v2":
        self.output_print_json_v2(l_outStream, l_symbolsByFile)
      elif self.m_format == "json-v1":
        self.output_print_json_v1(l_outStream, l_symbolsByFile)
      elif self.m_format == "lcov":
        self.output_print_lcov(l_outStream, l_symbolsByFile)
      else:
        self.error("invalid requested output format '%s'", self.m_format)

  def process(self):
    l_indexPath = self.get_index_path_from_root(self.m_root)
    l_xmlDoc    = self.get_xmldoc_from_file(l_indexPath)
    l_symbols   = self.process_index(l_xmlDoc)
    self.output_results(l_symbols)

  @staticmethod
  def count_symbols_by_kind(p_symbols):
    l_symbolCounts = {}
    for c_symbol in p_symbols:
      l_symbolKind = c_symbol["kind"]
      if not l_symbolKind in l_symbolCounts:
        l_symbolCounts[l_symbolKind] = {
          "documented_symbol_count": 0,
          "symbol_count"           : 0
        }
      if c_symbol["documented"]:
        l_symbolCounts[l_symbolKind]["documented_symbol_count"] += 1
      l_symbolCounts[l_symbolKind]["symbol_count"] += 1
    return l_symbolCounts

  @staticmethod
  def calculate_kind_coverage(p_symbolKindCounts):
    l_symbolKindCountsWithCoverage = p_symbolKindCounts
    for c_symbolKind, c_counts in p_symbolKindCounts.items():
      l_symbolKindCountsWithCoverage[c_symbolKind]["coverage_rate"] = c_counts["documented_symbol_count"]/c_counts["symbol_count"]
    return l_symbolKindCountsWithCoverage

  @staticmethod
  def calculate_totals(p_symbolKindCounts):
    l_totalDocumented = 0
    l_total = 0
    for c_counts in p_symbolKindCounts.values():
      l_totalDocumented += c_counts["documented_symbol_count"]
      l_total += c_counts["symbol_count"]
    return {
      "documented_symbol_count": l_totalDocumented,
      "symbol_count"           : l_total,
      "coverage_rate"          : 0 if l_total == 0 else l_totalDocumented / l_total
    }

  @staticmethod
  def create_summary(p_symbols):
    l_symbolKindCounts = Coverxygen.count_symbols_by_kind(p_symbols)
    l_totalCounts = Coverxygen.calculate_totals(l_symbolKindCounts)
    l_symbolKindCountsWithCoverage = Coverxygen.calculate_kind_coverage(l_symbolKindCounts)
    return {
      "total": l_totalCounts,
      "kinds": l_symbolKindCountsWithCoverage
    }

  @staticmethod
  def output_get_stream(p_output):
    if p_output == "-":
      return sys.stdout
    try:
      l_file = open(p_output, "w")
    except BaseException as l_error:
      Coverxygen.error("unable to write file %s : %s", p_output, str(l_error))
    return l_file

  @staticmethod
  def output_print_json_summary(p_stream, p_symbols):
    l_summary = Coverxygen.create_summary(p_symbols)
    p_stream.write(json.dumps(l_summary, indent=2))

  @staticmethod
  def output_print_json_v3(p_stream, p_symbols, p_symbolsByFile):
    l_data = Coverxygen.create_summary(p_symbols)
    l_data["files"] = p_symbolsByFile
    p_stream.write(json.dumps(l_data, indent=2))

  @staticmethod
  def output_print_json_v2(p_stream, p_symbolsByFile):
    p_stream.write(json.dumps(p_symbolsByFile, indent=2))

  @staticmethod
  def output_print_json_v1(p_stream, p_symbolsByFile):
    l_res = []
    for c_file, c_symbols in p_symbolsByFile.items():
      l_res.append({ c_file : c_symbols })
    p_stream.write(json.dumps(l_res, indent=2))

  @staticmethod
  def output_print_lcov(p_stream, p_results):
    for c_file, c_data in p_results.items():
      p_stream.write("SF:%s\n" % c_file)
      l_lines = {}
      for c_item in c_data:
        l_line = c_item["line"]
        if not c_item["documented"]:
          l_lines[l_line] = 0
        elif not l_line in l_lines:
          l_lines[l_line] = 1
      for c_line in l_lines:
        p_stream.write("DA:%d,%d\n" % (c_line, l_lines[c_line]))
      p_stream.write("end_of_record\n")

  @staticmethod
  def symbol_kind_to_string(p_kind):
    l_mapping = {
      "enum"     : "Enums",
      "enumvalue": "Enum Values",
      "friend"   : "Friends",
      "typedef"  : "Typedefs",
      "variable" : "Variables",
      "function" : "Functions",
      "signal"   : "Signals",
      "slot"     : "Slots",
      "class"    : "Classes",
      "struct"   : "Structs",
      "union"    : "Unions",
      "define"   : "Defines",
      "file"     : "Files",
      "namespace": "Namespaces",
      "page"     : "Pages"
    }
    return l_mapping[p_kind]

  @staticmethod
  def symbol_kind_counts_dict_to_list(p_symbolKindCountsDict):
    l_symbolCountsList = []
    for c_symbolKind, c_counts in p_symbolKindCountsDict.items():
      l_symbolCountsList.append({
        "kind": Coverxygen.symbol_kind_to_string(c_symbolKind),
        "documented_symbol_count": c_counts["documented_symbol_count"],
        "symbol_count": c_counts["symbol_count"]
      })
    return sorted(l_symbolCountsList, key=lambda obj: obj["kind"])

  @staticmethod
  def determine_first_column_width(p_symbolsKindCountsList):
    l_kindStringLengths = map(lambda c_symbolKindCount: len(c_symbolKindCount["kind"]), p_symbolsKindCountsList)
    l_longestKindStringLength = max(l_kindStringLengths, default=0)
    return l_longestKindStringLength

  @staticmethod
  def print_summary_line(p_stream, p_header, p_headerWidth, p_count, p_total):
    l_percentage = 0 if p_total == 0 else (p_count / p_total) * 100.0
    p_stream.write("%s: %5.1f%% (%d/%d)\n" % (("%%-%ds" % (p_headerWidth)) % p_header,
                                                l_percentage, p_count, p_total))

  @staticmethod
  def output_print_summary(p_stream, p_symbols):
    l_summary = Coverxygen.create_summary(p_symbols)
    l_symbolKindCountsList = Coverxygen.symbol_kind_counts_dict_to_list(l_summary["kinds"])
    l_totalCounts = l_summary["total"]
    l_firstColumnWidth = Coverxygen.determine_first_column_width(l_symbolKindCountsList)
    for c_symbolKindCount in l_symbolKindCountsList:
      Coverxygen.print_summary_line(p_stream, c_symbolKindCount["kind"], l_firstColumnWidth, c_symbolKindCount["documented_symbol_count"], c_symbolKindCount["symbol_count"])
    p_stream.write("%s\n" % ("-" * 35))
    Coverxygen.print_summary_line(p_stream, "Total", l_firstColumnWidth, l_totalCounts["documented_symbol_count"], l_totalCounts["symbol_count"])

# Local Variables:
# ispell-local-dictionary: "en"
# End:
