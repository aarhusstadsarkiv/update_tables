import xml.etree.ElementTree as ET

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

    def add_element_to_node(self, node: ET.Element, element_to_add: ET.Element,) -> None:
        node.append(element_to_add)


    def write_tree(self, new_xml_file: str) -> None:    
        # ET.indent is only a part of python 3.9 and forward.
        ET.indent(self.tree, space="    ", level=0)
        self.tree.write(new_xml_file, encoding="UTF-8")

    