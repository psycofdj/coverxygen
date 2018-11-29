# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import os
import tempfile
import xml.etree.ElementTree as ET
import unittest2 as unittest
from coverxygen import Coverxygen

#------------------------------------------------------------------#

class CoverxygenTest(unittest.TestCase):
  def __init__(self, *p_args, **p_kwds):
    super(CoverxygenTest, self).__init__(*p_args, **p_kwds)
    l_path = os.path.realpath(os.path.dirname(__file__))
    self.m_dataRoot = os.path.join(l_path, "data")

  def get_data_path(self, p_file, p_assert=True):
    l_path = os.path.join(self.m_dataRoot, p_file)
    if p_assert:
      self.assertEqual(True, os.path.exists(l_path))
    return l_path

  def test_error(self):
    with self.assertRaisesRegex(RuntimeError, "message arg"):
      Coverxygen.error("message %s", "arg")
    l_expected = r"invalid message format 'message %s' with args '\(\)'"
    with self.assertRaisesRegex(RuntimeError, l_expected):
      Coverxygen.error("message %s")

  def test_get_index_path_from_root(self):
    with self.assertRaises(RuntimeError):
      Coverxygen.get_index_path_from_root(".")
    l_dir = tempfile.mkdtemp()
    l_path = os.path.join(l_dir, "index.xml")
    l_file = open(l_path, "w")
    l_file.close()
    self.assertEqual(l_path, Coverxygen.get_index_path_from_root(l_dir))
    os.unlink(l_path)
    os.removedirs(l_dir)

  def test_get_file_path_from_root(self):
    with self.assertRaises(RuntimeError):
      Coverxygen.get_file_path_from_root(".", "base")
    l_dir = tempfile.mkdtemp()
    l_path = os.path.join(l_dir, "base.xml")
    l_file = open(l_path, "w")
    l_file.close()
    self.assertEqual(l_path, Coverxygen.get_file_path_from_root(l_dir, "base"))
    os.unlink(l_path)
    os.removedirs(l_dir)

  def test_get_xmldoc_from_file(self):
    with self.assertRaises(RuntimeError):
      Coverxygen.get_xmldoc_from_file("invalid_path")
    l_regex = "invalid.xml : mismatched tag: line 667, column 2"
    with self.assertRaisesRegex(RuntimeError, l_regex):
      Coverxygen.get_xmldoc_from_file(self.get_data_path("invalid.xml"))
    Coverxygen.get_xmldoc_from_file(self.get_data_path("valid.xml"))

  def test_extract_name(self):
    l_data = """
<data>
  <node1 id="id1">
    <definition>def</definition>
    <name>name</name>
  </node1>
  <node2 id="id2">
    <name>name</name>
  </node2>
  <node3 id="id3"/>
  <node4 tag="mytag"/>
  <node5 id="id5">
    <compoundname>CompoundName</compoundname>
  </node5>
</data>
    """
    l_doc = ET.fromstring(l_data)
    self.assertEqual("def",          Coverxygen.extract_name(l_doc.find("./node1")))
    self.assertEqual("name",         Coverxygen.extract_name(l_doc.find("./node2")))
    self.assertEqual("id3",          Coverxygen.extract_name(l_doc.find("./node3")))
    self.assertEqual("CompoundName", Coverxygen.extract_name(l_doc.find("./node5")))
    with self.assertRaisesRegex(RuntimeError, "mytag"):
      Coverxygen.extract_name(l_doc.find("./node4"))

  def test_extract_documented(self):
    l_data = """
<data>
  <node1/>
  <node2>
    <briefdescription></briefdescription>
  </node2>
  <node3>
    <briefdescription>
    content
    </briefdescription>
  </node3>
  <node4>
    <detaileddescription>content</detaileddescription>
  </node4>
  <node5>
    <inbodydescription>content</inbodydescription>
  </node5>
</data>
    """
    l_doc = ET.fromstring(l_data)
    self.assertEqual(False,  Coverxygen.extract_documented(l_doc.find("./node1")))
    self.assertEqual(False,  Coverxygen.extract_documented(l_doc.find("./node2")))
    self.assertEqual(True,   Coverxygen.extract_documented(l_doc.find("./node3")))
    self.assertEqual(True,   Coverxygen.extract_documented(l_doc.find("./node4")))
    self.assertEqual(True,   Coverxygen.extract_documented(l_doc.find("./node5")))


  def test_extract_location(self):
    l_data = """
<data>
  <node1/>
  <node2>
    <location file="actual.hh" line="22"/>
  </node2>
  <node3>
    <location file="/opt/actual.hh" line="33"/>
  </node3>
  <error1>
    <location line="33"/>
  </error1>
  <error2>
    <location line="file.cc"/>
  </error2>
</data>
    """
    l_doc  = ET.fromstring(l_data)

    l_line = 1
    l_path = "file.xml"
    l_file = os.path.abspath(l_path)
    l_node = l_doc.find("./node1")
    self.assertEqual((l_file, l_line),  Coverxygen.extract_location(l_node, l_path, "/tmp"))

    l_line = 1
    l_path = "/root/file.xml"
    l_file = os.path.abspath(l_path)
    l_node = l_doc.find("./node1")
    self.assertEqual((l_file, l_line),  Coverxygen.extract_location(l_node, l_path, "/tmp"))

    l_line = 22
    l_path = "/root/file.xml"
    l_file = os.path.abspath("/tmp/actual.hh")
    l_node = l_doc.find("./node2")
    self.assertEqual((l_file, l_line),  Coverxygen.extract_location(l_node, l_path, "/tmp"))

    l_line = 33
    l_path = "/root/file.xml"
    l_file = os.path.abspath("/opt/actual.hh")
    l_node = l_doc.find("./node3")
    self.assertEqual((l_file, l_line),  Coverxygen.extract_location(l_node, l_path, "/tmp"))

    with self.assertRaises(RuntimeError):
      l_node = l_doc.find("./error1")
      Coverxygen.extract_location(l_node, l_path, "/tmp")

    with self.assertRaises(RuntimeError):
      l_node = l_doc.find("./error2")
      Coverxygen.extract_location(l_node, l_path, "/tmp")


  def test_get_absolute_path(self):
    self.assertEqual(os.path.abspath("/root/file.hh"), Coverxygen.get_absolute_path("file.hh",      "/root"))
    self.assertEqual(os.path.abspath("/root/file.hh"), Coverxygen.get_absolute_path("./file.hh",    "/root"))
    self.assertEqual(os.path.abspath("/tmp/file.hh"),  Coverxygen.get_absolute_path("/tmp/file.hh", "/root"))
    self.assertEqual(os.path.abspath("/file.hh"),      Coverxygen.get_absolute_path("../file.hh",   "/root"))
    self.assertEqual(os.path.abspath("/file.hh"),      Coverxygen.get_absolute_path("/../file.hh",  "/root"))

  def test_should_filter_out(self):
    l_xml = """
    <data>
      <node1 prot="s1" kind="k1"/>
      <node2 prot="s2" kind="k1"/>
      <node3 prot="s1" kind="k3"/>
      <node4 prot="s3" kind="k1"/>
      <node5 prot="s3" kind="k3"/>
    </data>
    """
    l_doc    = ET.fromstring(l_xml)
    l_scopes = ["s1", "s2"]
    l_kinds  = ["k1", "k2"]
    l_obj = Coverxygen(None, None, l_scopes, l_kinds, "/p", None, None, False)
    self.assertFalse(l_obj.should_filter_out(l_doc.find("./node1"), os.path.abspath("/p/file.hh"),     1))
    self.assertFalse(l_obj.should_filter_out(l_doc.find("./node2"), os.path.abspath("/p/file.hh"),     1))
    self.assertTrue(l_obj.should_filter_out(l_doc.find("./node3"), os.path.abspath("/p/file.hh"),     1))
    self.assertTrue(l_obj.should_filter_out(l_doc.find("./node4"), os.path.abspath("/p/file.hh"),     1))
    self.assertTrue(l_obj.should_filter_out(l_doc.find("./node5"), os.path.abspath("/p/file.hh"),     1))
    self.assertTrue(l_obj.should_filter_out(l_doc.find("./node1"), os.path.abspath("/other/file.hh"), 1))

  def test_process_symbol(self):
    l_classDoc = ET.parse(self.get_data_path("class.xml"))
    l_scopes   = ["private",  "protected", "public", "namespace"]
    l_kinds    = ["function", "class", "enum"]
    
    l_node   = l_classDoc.find("./compounddef//memberdef[@id='classxtd_1_1Application_1a672c075ed901e463609077d571a714c7']")
    l_obj    = Coverxygen(None, None, l_scopes, l_kinds, "/opt", None, "/opt", False)
    l_data   = l_obj.process_symbol(l_node, "/opt/file.hh")
    l_expect = {'documented': True, 'line': 102, 'symbol': 'argument', 'file': os.path.abspath('/opt/src/Application.hh')}
    self.assertDictEqual(l_expect, l_data)

	l_node   = l_classDoc.find("./compounddef//memberdef[@id='classxtd_1_1Application_1a907b6fe8247636495890e668530863d6']")
	l_data   = l_obj.process_symbol(l_node, "/opt/file.hh")
	l_expect = {}
	self.assertDictEqual(l_expect, l_data)

    l_namesapceDoc = ET.parse(self.get_data_path("namespace.xml"))
    l_node         = l_namesapceDoc.find("./compounddef[@id='namespace_my_namespace']")
    l_obj          = Coverxygen(None, None, l_scopes, l_kinds, "/opt", None, "/opt", False)
    l_data         = l_obj.process_symbol(l_node, "/opt/file.hh")
    l_expect       = {'documented': True, 'line': 5, 'symbol': 'MyNamespace', 'file': os.path.abspath('/opt/src/MyNamespace.hh')}
    self.assertDictEqual(l_expect, l_data)


  def test_merge_symbol(self):
    l_syms   = [{ "file" : "a", "key1" : 1}]
    l_res    = {}
    l_expect = { "a" : [ { "file" : "a", "key1" : 1} ] }
    Coverxygen.merge_symbols(l_res, l_syms)
    self.assertDictEqual(l_expect, l_res)

    l_syms   = [
      { "file" : "a", "key1" : 1},
      { "file" : "a", "key2" : 2}
    ]
    l_expect = {
      "a" : [
        { "file" : "a", "key1" : 1 },
        { "file" : "a", "key2" : 2 }
      ]
    }
    l_res = {}
    Coverxygen.merge_symbols(l_res, l_syms)
    self.assertDictEqual(l_expect, l_res)

    l_syms   = [
      { "file" : "b", "key1" : 1},
      { "file" : "c", "key2" : 2}
    ]
    l_expect = {
      "b" : [{ "file" : "b", "key1" : 1 }],
      "c" : [{ "file" : "c", "key2" : 2 }]
    }
    l_res = {}
    Coverxygen.merge_symbols(l_res, l_syms)
    self.assertDictEqual(l_expect, l_res)

    l_syms   = [
      { "file" : "b", "key1" : 1},
      { "file" : "c", "key2" : 2}
    ]
    l_expect = {
      "b" : [{ "file" : "b", "key0" : 0 }, { "file" : "b", "key1" : 1 }],
      "c" : [{ "file" : "c", "key2" : 2 }]
    }
    l_res = {
      "b" : [{ "file" : "b", "key0" : 0 }]
    }
    Coverxygen.merge_symbols(l_res, l_syms)
    self.assertDictEqual(l_expect, l_res)

    l_syms   = []
    l_expect = {
      "b" : [{ "file" : "b", "key0" : 0 }],
    }
    l_res = {
      "b" : [{ "file" : "b", "key0" : 0 }]
    }
    Coverxygen.merge_symbols(l_res, l_syms)
    self.assertDictEqual(l_expect, l_res)


  def test_process_file(self):
    l_file   = self.get_data_path("class.xml")
    l_scopes = ["private",  "protected", "public"]
    l_kinds  = ["enum"]
    l_obj    = Coverxygen(None, None, l_scopes, l_kinds, "/opt", None, "/opt", False)
    l_res    = {}
    l_name   = os.path.abspath("/opt/src/Application.hh")
    l_obj.process_file(l_file, l_res)
    self.assertEqual(1, len(l_res.keys()))
    self.assertIn(l_name, l_res)
    self.assertEqual(2, len(l_res[l_name]))
    self.assertEqual(2, len([x for x in l_res[l_name] if x['documented']]))

    l_file   = self.get_data_path("class.xml")
    l_scopes = ["private",  "protected", "public"]
    l_kinds  = ["class"]
    l_obj    = Coverxygen(None, None, l_scopes, l_kinds, "/opt", None, "/opt", False)
    l_res    = {}
    l_name   = os.path.abspath("/opt/src/Application.hh")
    l_obj.process_file(l_file, l_res)
    self.assertEqual(1, len(l_res.keys()))
    self.assertIn(l_name, l_res)
    self.assertEqual(1, len(l_res[l_name]))
    self.assertEqual(1, len([x for x in l_res[l_name] if x['documented']]))
