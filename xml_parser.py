import xml.etree.ElementTree as ET
from pathlib import Path

class XMLParser():
    def __init__(self, xml_file_path, namespace=None) -> None:
        if namespace is None:
            ET.register_namespace("", "http://www.sa.dk/xmlns/siard/1.0/schema0/table11.xsd")
        else:
            ET.register_namespace("", namespace)
        self.tree = ET.parse(xml_file_path)
        self.root_node = self.tree.getroot()

    def add_element_to_root(self, element_to_add: ET.Element) -> None:
        self.root_node.append(element_to_add)

    def add_document_to_node(self, node: ET.Element, document_to_add: str) -> None:
        tree = ET.parse(document_to_add)
        element_to_add = tree.getroot()
        node.append(element_to_add)

    def add_xml_string_to_node(self, node: ET.Element, xml_str_to_add: str)-> None:
        root_element = ET.fromstring(xml_str_to_add)
        node.append(root_element)

    def add_element_to_node(self, node: ET.Element, element_to_add: ET.Element) -> None:
        node.append(element_to_add)


    def write_tree(self, new_xml_file: str) -> None:    
        # ET.indent is only a part of python 3.9 and forward.
        ET.indent(self.tree, space="    ", level=0)
        self.tree.write(new_xml_file, encoding="UTF-8")

    