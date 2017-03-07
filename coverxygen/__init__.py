# -*- mode: python; coding: utf-8 -*-
#------------------------------------------------------------------------------

import os
import sys
import json
import xml.etree.ElementTree as ET

#------------------------------------------------------------------------------

__author__       = "Xavier MARCELET <xavier@marcelet.com>"
__copyright__    = "Copyright (C) 2016 Xavier MARCELET"
__version__      = "1.3.0"
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
  def __init__(self, p_path, p_output, p_scope, p_kind, p_prefix, p_format, p_rootDir, p_verbose):
    self.m_root    = p_path
    self.m_output  = p_output
    self.m_scope   = p_scope
    self.m_kind    = p_kind
    self.m_prefix  = p_prefix
    self.m_format  = p_format
    self.m_rootDir = p_rootDir
    self.m_verbose = p_verbose

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
    l_id  = p_node.get("id")
    l_def = p_node.find("./definition")
    l_nam = p_node.find("./name")
    if l_def is not None:
      return l_def.text
    if l_nam is not None:
      return l_nam.text
    elif l_id is not None :
      return l_id
    Coverxygen.error("unable to deduce name from node %s", ET.tostring(p_node))

  @staticmethod
  def extract_documented(p_node):
    for c_key in ["briefdescription", "detaileddescription", "inbodydescription"]:
      l_node = p_node.find("./%s" % c_key)
      if l_node is not None:
        l_content = "".join(l_node.itertext()).strip()
        if len(l_content):
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
    return l_file, l_line

  @staticmethod
  def get_absolute_path(p_file, p_rootDir):
    l_path = p_file
    if not p_file.startswith("/"):
      l_path = os.path.join(p_rootDir, p_file)
    return os.path.abspath(l_path)

  def should_filter_out(self, p_node, p_file, p_line):
    l_scope  = p_node.get('prot')
    l_kind   = p_node.get('kind')
    if (not l_scope in self.m_scope) or (not l_kind in self.m_kind):
      return True
    if not p_file.startswith(self.m_prefix):
      return True
    self.verbose("found symbol of type %s at %s:%d", l_kind, p_file, p_line)
    return False

  def process_symbol(self, p_node, p_filePath):
    l_name         = self.extract_name(p_node)
    l_isDocumented = self.extract_documented(p_node)
    l_file, l_line = self.extract_location(p_node, p_filePath, self.m_rootDir)
    if self.should_filter_out(p_node, l_file, l_line):
      return {}
    return {
      "symbol"     : l_name,
      "documented" : l_isDocumented,
      "line"       : l_line,
      "file"       : l_file
    }

  @staticmethod
  def merge_symbols(p_results, p_symbols):
    for c_symbol in p_symbols:
      if not len(c_symbol):
        continue
      l_file = c_symbol["file"]
      if not l_file in p_results:
        p_results[l_file] = []
      p_results[l_file].append(c_symbol)

  def process_file(self, p_filePath, p_results):
    self.verbose("processing file : %s", p_filePath)
    l_symbols   = []
    l_xmlDoc    = self.get_xmldoc_from_file(p_filePath)
    l_xmlNodes  = l_xmlDoc.findall("./compounddef//memberdef")
    l_xmlNodes += l_xmlDoc.findall("./compounddef")
    for c_def in l_xmlNodes:
      l_symbol = self.process_symbol(c_def, p_filePath)
      l_symbols.append(l_symbol)
    self.merge_symbols(p_results, l_symbols)

  def process_index(self, p_xmlDoc):
    l_results = {}
    for c_entry in p_xmlDoc.findall('compound'):
      l_kind  = c_entry.get("kind")
      l_refid = c_entry.get("refid")
      if not l_kind:
        self.error("missing kind attribute on compound element : %s", str(c_entry))
      if not l_kind:
        self.error("missing refid attribute on compound element : %s", str(c_entry))
      if l_kind == "dir":
        continue
      l_filePath = self.get_file_path_from_root(self.m_root, l_refid)
      self.process_file(l_filePath, l_results)
    return l_results

  def output_results(self, p_results):
    l_outStream = self.output_get_stream(self.m_output)
    if self.m_format == "json":
      self.output_print_json(l_outStream, p_results)
    elif self.m_format == "json-legacy":
      self.output_print_json_legacy(l_outStream, p_results)
    elif self.m_format == "lcov":
      self.output_print_lcov(l_outStream, p_results)
    else:
      self.error("invalid requested output format '%s'", self.m_format)

  def process(self):
    l_indexPath = self.get_index_path_from_root(self.m_root)
    l_xmlDoc    = self.get_xmldoc_from_file(l_indexPath)
    l_results   = self.process_index(l_xmlDoc)
    self.output_results(l_results)

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
  def output_print_json(p_stream, p_results):
    p_stream.write(json.dumps(p_results, indent=2))

  @staticmethod
  def output_print_json_legacy(p_stream, p_results):
    l_res = []
    for c_file, c_symbols in p_results.items():
      l_res.append({ c_file : c_symbols })
    p_stream.write(json.dumps(l_res, indent=2))

  @staticmethod
  def output_print_lcov(p_stream, p_results):
    for c_file, c_data in p_results.items():
      p_stream.write("SF:%s\n" % c_file)
      for c_item in c_data:
        l_value = 1
        if not c_item["documented"]:
          l_value = -1
        p_stream.write("DA:%d,%d\n" % (c_item["line"], l_value))
      p_stream.write("end_of_record\n")

# Local Variables:
# ispell-local-dictionary: "en"
# End:
