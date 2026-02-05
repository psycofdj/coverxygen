# -*- coding: utf-8
#------------------------------------------------------------------#

__author__    = "Xavier MARCELET <xavier@marcelet.com>"

#------------------------------------------------------------------#

import os
import json
import tempfile
import xml.etree.ElementTree as ET
import unittest
from io import StringIO
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
      <node6 prot="s1" kind="friend">
        <type>friend class</type>
      </node6>
      <node7 prot="s1" kind="friend">
        <type>friend class</type>
        <initializer>{
	public:
		Foo() {}
	}</initializer>
      </node7>
    </data>
    """
    l_doc    = ET.fromstring(l_xml)
    l_scopes = ["s1", "s2"]
    l_kinds  = ["k1", "k2", "friend"]
    l_obj = Coverxygen(None, None, l_scopes, l_kinds, None, None, "/p")
    self.assertFalse(l_obj.should_filter_out(l_doc.find("./node1"), os.path.abspath("/p/file.hh"),     1))
    self.assertFalse(l_obj.should_filter_out(l_doc.find("./node2"), os.path.abspath("/p/file.hh"),     1))
    self.assertTrue( l_obj.should_filter_out(l_doc.find("./node3"), os.path.abspath("/p/file.hh"),     1))
    self.assertTrue( l_obj.should_filter_out(l_doc.find("./node4"), os.path.abspath("/p/file.hh"),     1))
    self.assertTrue( l_obj.should_filter_out(l_doc.find("./node5"), os.path.abspath("/p/file.hh"),     1))
    self.assertTrue( l_obj.should_filter_out(l_doc.find("./node1"), os.path.abspath("/other/file.hh"), 1))
    self.assertFalse(l_obj.should_filter_out(l_doc.find("./node6"), os.path.abspath("/p/file.hh"),     1))
    self.assertTrue( l_obj.should_filter_out(l_doc.find("./node7"), os.path.abspath("/p/file.hh"),     1))

  def test_file_filter(self):
    l_xml = """
    <data>
      <node1 prot="s1" kind="k1"/>
    </data>
    """
    l_doc = ET.fromstring(l_xml)
    l_dummyNode = l_doc.find("./node1")
    l_excludes = [".*[\\\\/]test[\\\\/].*", ".*\\.ctt$"]
    l_includes = [".*[\\\\/]special\\.ctt$"]
    l_obj = Coverxygen(None, None, ["s1"], ["k1"], None, None, p_prefix="/src", p_includes=l_includes, p_excludes=l_excludes)
    self.assertFalse(l_obj.should_filter_out(l_dummyNode, os.path.abspath("/src/file.cpp"), 1))
    self.assertTrue(l_obj.should_filter_out(l_dummyNode, os.path.abspath("/src/file.ctt"), 1))
    self.assertTrue(l_obj.should_filter_out(l_dummyNode, os.path.abspath("/src/test/file.cpp"), 1))
    self.assertFalse(l_obj.should_filter_out(l_dummyNode, os.path.abspath("/src/test/special.ctt"), 1))
    self.assertFalse(l_obj.should_filter_out(l_dummyNode, os.path.abspath("/other/special.ctt"), 1))

  def test_process_symbol(self):
    l_classDoc = ET.parse(self.get_data_path("class.xml"))
    l_scopes   = ["private",  "protected", "public"]
    l_kinds    = ["function", "class", "enum", "namespace"]

    l_node   = l_classDoc.find("./compounddef//memberdef[@id='classxtd_1_1Application_1a672c075ed901e463609077d571a714c7']")
    l_obj    = Coverxygen(None, None, l_scopes, l_kinds, None, "/opt", "/opt")
    l_data   = l_obj.process_symbol(l_node, "/opt/file.hh")
    l_expect = [{'documented': True, 'line': 102, 'kind': 'enum', 'symbol': 'argument', 'file': os.path.abspath('/opt/src/Application.hh')}]
    self.assertEqual(l_expect, l_data)

    l_node     = l_classDoc.find("./compounddef//memberdef[@id='classxtd_1_1Application_1a907b6fe8247636495890e668530863d6']")
    l_data     = l_obj.process_symbol(l_node, "/opt/file.hh")
    l_expect   = []
    self.assertEqual(l_expect, l_data)

    l_namesapceDoc = ET.parse(self.get_data_path("namespace.xml"))
    l_node         = l_namesapceDoc.find("./compounddef[@id='namespace_my_namespace']")
    l_obj          = Coverxygen(None, None, l_scopes, l_kinds, None, "/opt", "/opt")
    l_data         = l_obj.process_symbol(l_node, "/opt/file.hh")
    l_expect       = [{'documented': True, 'line': 5, 'kind': 'namespace', 'symbol': 'MyNamespace', 'file': os.path.abspath('/opt/src/MyNamespace.hh')}]
    self.assertEqual(l_expect, l_data)

    l_enumDoc = ET.parse(self.get_data_path("enum.xml"))
    l_node    = l_enumDoc.find("./compounddef//memberdef[@id='class_my_enum_class_1a4bffd5affc2abeba8ed3af3c2fd81ff4']")
    l_obj     = Coverxygen(None, None, l_scopes, ["enum", "enumvalue"], None, "/opt", "/opt")
    l_data    = l_obj.process_symbol(l_node, "/opt/file.hh")
    l_expect  = [{'documented': True, 'line': 466, 'kind': 'enum', 'symbol': 'MyEnum', 'file': os.path.abspath('/opt/MyEnumClass.hpp')},
                 {'documented': True, 'line': 466, 'kind': 'enumvalue', 'symbol': 'Enum_Value_1', 'file': os.path.abspath('/opt/MyEnumClass.hpp')},
                 {'documented': False, 'line': 466, 'kind': 'enumvalue', 'symbol': 'Enum_Value_2', 'file': os.path.abspath('/opt/MyEnumClass.hpp')}]
    self.assertEqual(l_expect, l_data)


  def test_group_symbols_by_file(self):
    l_syms   = [{ "file" : "a", "key1" : 1 }]
    l_expect = { "a" : [ { "file" : "a", "key1" : 1 } ] }
    l_res = Coverxygen.group_symbols_by_file(l_syms)
    self.assertDictEqual(l_expect, l_res)

    l_syms   = [
      { "file" : "a", "key1" : 1 },
      { "file" : "a", "key2" : 2 }
    ]
    l_expect = {
      "a" : [
        { "file" : "a", "key1" : 1 },
        { "file" : "a", "key2" : 2 }
      ]
    }
    l_res = Coverxygen.group_symbols_by_file(l_syms)
    self.assertDictEqual(l_expect, l_res)

    l_syms   = [
      { "file" : "b", "key1" : 1 },
      { "file" : "c", "key2" : 2 }
    ]
    l_expect = {
      "b" : [{ "file" : "b", "key1" : 1 }],
      "c" : [{ "file" : "c", "key2" : 2 }]
    }
    l_res = Coverxygen.group_symbols_by_file(l_syms)
    self.assertDictEqual(l_expect, l_res)

    l_syms   = [
      { "file" : "b", "key1" : 1 },
      { "file" : "c", "key2" : 2 },
      { "file" : "b", "key0" : 0 }
    ]
    l_expect = {
      "b" : [{ "file" : "b", "key1" : 1 }, { "file" : "b", "key0" : 0 }],
      "c" : [{ "file" : "c", "key2" : 2 }]
    }
    l_res = Coverxygen.group_symbols_by_file(l_syms)
    self.assertDictEqual(l_expect, l_res)

    l_syms   = [
      { "file" : "b", "key0" : 0 }
    ]
    l_expect = {
      "b" : [{ "file" : "b", "key0" : 0 }],
    }
    l_res = Coverxygen.group_symbols_by_file(l_syms)
    self.assertDictEqual(l_expect, l_res)


  def test_process_file(self):
    l_testDataFile   = self.get_data_path("class.xml")
    l_scopes = ["private",  "protected", "public"]
    l_kinds  = ["enum"]
    l_obj    = Coverxygen(None, None, l_scopes, l_kinds, None, "/opt", "/opt")
    l_file   = os.path.abspath("/opt/src/Application.hh")
    l_symbols = l_obj.process_file(l_testDataFile)
    self.assertEqual(2, len(l_symbols))
    self.assertEqual(2, len([x for x in l_symbols if x['file'] == l_file]))
    self.assertEqual(2, len([x for x in l_symbols if x['documented']]))

    l_testDataFile   = self.get_data_path("class.xml")
    l_scopes = ["private",  "protected", "public"]
    l_kinds  = ["class"]
    l_obj    = Coverxygen(None, None, l_scopes, l_kinds, None, "/opt", "/opt")
    l_file   = os.path.abspath("/opt/src/Application.hh")
    l_symbols = l_obj.process_file(l_testDataFile)
    self.assertEqual(1, len(l_symbols))
    self.assertEqual(1, len([x for x in l_symbols if x['file'] == l_file]))
    self.assertEqual(1, len([x for x in l_symbols if x['documented']]))


  def test_output_print_lvoc(self):
    l_obj = Coverxygen(None, None, [], [], None, None)
    l_stream = StringIO()
    l_symbols = [{'documented': True,  'line': 466, 'symbol': 'MyEnum', 'file': os.path.abspath('/opt/MyEnumClass.hpp')},
                 {'documented': False, 'line': 466, 'symbol': 'Enum_Value_1', 'file': os.path.abspath('/opt/MyEnumClass.hpp')},
                 {'documented': True,  'line': 466, 'symbol': 'Enum_Value_2', 'file': os.path.abspath('/opt/MyEnumClass.hpp')},
                 {'documented': True,  'line': 17,  'symbol': 'MyOtherEnum', 'file': os.path.abspath('/opt/MyOtherEnumClass.hpp')},
                 {'documented': True,  'line': 17,  'symbol': 'OtherEnum_Value_1', 'file': os.path.abspath('/opt/MyOtherEnumClass.hpp')},
                 {'documented': True,  'line': 17,  'symbol': 'OtherEnum_Value_2', 'file': os.path.abspath('/opt/MyOtherEnumClass.hpp')}]
    l_symbolsByFile = l_obj.group_symbols_by_file(l_symbols)
    l_obj.output_print_lcov(l_stream, l_symbolsByFile)
    l_outputResult = l_stream.getvalue()
    l_stream.close()

    self.assertIn("DA:466,0", l_outputResult)
    self.assertNotIn("DA:466,1", l_outputResult)
    self.assertNotIn("DA:17,0", l_outputResult)
    self.assertIn("DA:17,1", l_outputResult)

  def test_output_print_json_v2_v3_summary(self):
    l_obj = Coverxygen(None, None, [], [], None, None)

    l_myEnumClassFile      = os.path.abspath('/opt/MyEnumClass.hpp')
    l_myOtherEnumClassFile = os.path.abspath('/opt/MyOtherEnumClass.hpp')
    l_myClassFile          = os.path.abspath('/opt/MyClass.hpp')
    l_myEnumSymbol      = {'documented': True,  'line': 466, 'kind': 'enum', 'symbol': 'MyEnum', 'file': l_myEnumClassFile}
    l_myClassSymbol     = {'documented': True,  'line': 10,  'kind': 'class', 'symbol': 'MyClass', 'file': l_myClassFile}
    l_enumValue1Symbol  = {'documented': False, 'line': 466, 'kind': 'enumvalue', 'symbol': 'Enum_Value_1', 'file': l_myEnumClassFile}
    l_symbols = [l_myEnumSymbol,
                 l_enumValue1Symbol,
                 {'documented': True,  'line': 466, 'kind': 'enumvalue', 'symbol': 'Enum_Value_2', 'file': l_myEnumClassFile},
                 {'documented': True,  'line': 17,  'kind': 'enum', 'symbol': 'MyOtherEnum', 'file': l_myOtherEnumClassFile},
                 {'documented': True,  'line': 17,  'kind': 'enumvalue', 'symbol': 'OtherEnum_Value_1', 'file': l_myOtherEnumClassFile},
                 {'documented': True,  'line': 17,  'kind': 'enumvalue', 'symbol': 'OtherEnum_Value_2', 'file': l_myOtherEnumClassFile},
                 l_myClassSymbol,
                 {'documented': False,  'line': 20,  'kind': 'function', 'symbol': 'MyClass::foo', 'file': l_myClassFile}]

    # json-summary
    l_stream = StringIO()
    l_obj.output_print_json_summary(l_stream, l_symbols)
    l_jsonSummaryResult = l_stream.getvalue()
    l_stream.close()
    l_decodedJsonSummaryResult = json.loads(l_jsonSummaryResult)
    self.assertIn("total", l_decodedJsonSummaryResult)
    self.assertEqual(0.75, l_decodedJsonSummaryResult["total"]["coverage_rate"])
    self.assertEqual(8, l_decodedJsonSummaryResult["total"]["symbol_count"])
    self.assertEqual(6, l_decodedJsonSummaryResult["total"]["documented_symbol_count"])
    self.assertIn("kinds", l_decodedJsonSummaryResult)
    self.assertIn("class", l_decodedJsonSummaryResult["kinds"])
    self.assertEqual(1.0, l_decodedJsonSummaryResult["kinds"]["class"]["coverage_rate"])
    self.assertEqual(1, l_decodedJsonSummaryResult["kinds"]["class"]["symbol_count"])
    self.assertEqual(1, l_decodedJsonSummaryResult["kinds"]["class"]["documented_symbol_count"])
    self.assertIn("function", l_decodedJsonSummaryResult["kinds"])
    self.assertEqual(0.0, l_decodedJsonSummaryResult["kinds"]["function"]["coverage_rate"])
    self.assertEqual(1, l_decodedJsonSummaryResult["kinds"]["function"]["symbol_count"])
    self.assertEqual(0, l_decodedJsonSummaryResult["kinds"]["function"]["documented_symbol_count"])
    self.assertNotIn("friend", l_decodedJsonSummaryResult["kinds"])
    self.assertNotIn("files", l_decodedJsonSummaryResult)

    # json-v2
    l_stream = StringIO()
    l_symbolsByFile = l_obj.group_symbols_by_file(l_symbols)
    l_obj.output_print_json_v2(l_stream, l_symbolsByFile)
    l_jsonV2Result = l_stream.getvalue()
    l_stream.close()
    l_decodedJsonV2Result = json.loads(l_jsonV2Result)
    self.assertIn(l_myEnumClassFile, l_decodedJsonV2Result)
    self.assertIn(l_myClassFile, l_decodedJsonV2Result)
    self.assertIn(l_myEnumSymbol, l_decodedJsonV2Result[l_myEnumClassFile])
    self.assertIn(l_enumValue1Symbol, l_decodedJsonV2Result[l_myEnumClassFile])
    self.assertIn(l_myClassSymbol, l_decodedJsonV2Result[l_myClassFile])

    # json-v3
    l_stream = StringIO()
    l_obj.output_print_json_v3(l_stream, l_symbols, l_symbolsByFile)
    l_jsonV3Result = l_stream.getvalue()
    l_stream.close()
    l_decodedJsonV3Result = json.loads(l_jsonV3Result)
    self.assertIn("total", l_decodedJsonV3Result)
    self.assertIn("kinds", l_decodedJsonV3Result)
    self.assertIn("files", l_decodedJsonV3Result)
    self.assertEqual(l_decodedJsonSummaryResult, {"total": l_decodedJsonV3Result["total"], "kinds": l_decodedJsonV3Result["kinds"]})
    self.assertEqual(l_decodedJsonV2Result, l_decodedJsonV3Result["files"])


  def test_output_print_summary(self):
    l_obj = Coverxygen(None, None, [], [], None, None)
    l_stream = StringIO()
    l_symbols = [{'documented': True,  'line': 466, 'kind': 'enum', 'symbol': 'MyEnum', 'file': os.path.abspath('/opt/MyEnumClass.hpp')},
                 {'documented': False, 'line': 466, 'kind': 'enumvalue', 'symbol': 'Enum_Value_1', 'file': os.path.abspath('/opt/MyEnumClass.hpp')},
                 {'documented': True,  'line': 466, 'kind': 'enumvalue', 'symbol': 'Enum_Value_2', 'file': os.path.abspath('/opt/MyEnumClass.hpp')},
                 {'documented': True,  'line': 17,  'kind': 'enum', 'symbol': 'MyOtherEnum', 'file': os.path.abspath('/opt/MyOtherEnumClass.hpp')},
                 {'documented': True,  'line': 17,  'kind': 'enumvalue', 'symbol': 'OtherEnum_Value_1', 'file': os.path.abspath('/opt/MyOtherEnumClass.hpp')},
                 {'documented': True,  'line': 17,  'kind': 'enumvalue', 'symbol': 'OtherEnum_Value_2', 'file': os.path.abspath('/opt/MyOtherEnumClass.hpp')}]
    l_obj.output_print_summary(l_stream, l_symbols)
    l_outputResult = l_stream.getvalue()
    l_stream.close()

    self.assertRegex(l_outputResult, r".*Enums\s*:\s+100\.0% \(2/2\).*")
    self.assertRegex(l_outputResult, r".*Enum Values\s*:\s+75\.0% \(3/4\).*")
    self.assertRegex(l_outputResult, r".*Total\s*:\s+83\.3% \(5/6\).*")
