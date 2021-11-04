from xml_parser import XMLParser
import xml.etree.ElementTree as ET

'''
An example of how to use the XMLParser to append an element to a node in an XML tree.
'''
if __name__ == "__main__":
    # Instantiate the parser with and parse an xml file with its default namespace.
    parser = XMLParser("tableIndex.xml", namespace="http://www.sa.dk/xmlns/diark/1.0")

    # Find the tables node/element by searching for the namespace + tables.
    tables_node = parser.tree.find("{http://www.sa.dk/xmlns/diark/1.0}tables")

    # Parse the xml file that contains the element we want to append.
    table_to_add = ET.parse("table_index_parent_children.xml")
    table_element = table_to_add.getroot()

    # Add the element to the node in the tree.
    parser.add_element_to_node(tables_node, table_element)
    
    # Write the updated tree to an xml file.
    parser.write_tree("newTable.xml")
