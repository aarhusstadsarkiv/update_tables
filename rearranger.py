import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Tuple
from sys import argv
from tiffprinter import stringToTiffPrinter
import xml.etree.ElementTree as ET


archive_suffixes = [".zip", ".tar", ".gz", ".7z", ".cab", ".rar"]


def is_archive(file_name: str) -> bool:
    """
    Description:
    ------------
    This function evaluates if the file with the name file_name
    is a compressed archive file, based on its suffix.
    This is an auxiliary function for rearrange_files
    and the result should not be interpreted as
    the ground truth. For a more extensive evaluation,
    use the sf_id function from sf_id.py,
    and evaluate the returned puid.

    Parameters:
    -----------
    file_name: str. The file name to evaluate.

    Returns:
    --------
    bool. If the file_name contains an archive file
    format suffix or not.
    """
    for suffix in archive_suffixes:
        if suffix in file_name:
            return True
    return False


def rearrange_files(
    extracted_folder: Path, new_doc_collection: Path, count: int
) -> Tuple[List[Dict], int]:
    """
    Description:
    -------------
    Recursively moves all files in extracted_folder
    to a subfolder in new_doc_collection.
    The subfolder is an incremented integer
    value representing the document id.

    Parameters:
    -----------
    extracted_folder: Path of the extracted archive.
    new_doc_collection: Path. Path of the new docCollection
    to place the files.

    Returns:
    --------
    doc_elements: List[Dict]. A list of document elements
    for indices/docIndex.xml file.
    count: int. The updated count variable.

    """
    doc_elements = []
    for path, subdirs, filenames in os.walk(extracted_folder):
        for filename in filenames:
            if not is_archive(filename):
                file_path = Path(os.path.join(path, filename))
                destination: Path = new_doc_collection / str(count) / filename
                destination.parent.mkdir()
                shutil.copy(file_path, destination)
                pid = extracted_folder.parent.name
                doc_element = {
                    "pID": pid,
                    "dID": count,
                    "mID": 1,
                    "dCf": new_doc_collection.name,
                    "oFn": filename,
                    "aFt": "tif",
                }
                doc_elements.append(doc_element)
                count += 1
    return doc_elements, count


def doc_elements_to_xml(doc_elements: List[Dict[str, Any]]) -> List[str]:
    """
    Description:
    ------------
    Converts a list of doc element dictionaries to a list of strings.
    Each string is an xml representation of a doc element.

    Parameters:
    -----------
    doc_elements: List[Dict[str, Any]]. The list of doc elements to process.

    Returns:
    --------
    xml_strings: List[str]. The doc_elements as a list of xml strings.
    """
    xml_strings = []
    for doc_element in doc_elements:
        xml_str = "<doc>\n"
        for key in doc_element.keys():
            xml_str += (
                "        <"
                + key
                + ">"
                + str(doc_element[key])
                + "</"
                + key
                + ">"
                + "\n"
            )
        xml_str += "    </doc>"
        xml_strings.append(xml_str)
    return xml_strings


def append_to_docIndex(docIndex: Path, xml_strings: List[str]) -> None:
    # Open the file in binary read/write mode.
    # "rb+" does not overwrite the file like wb+.
    with open(docIndex, "rb+") as docIndex_handle:
        # The </docIndex> tag is 11 ASCII chars
        # long plus a newline char.
        # This gives us 12 ASCII
        # since UTF-8 is ASCII compatible.
        # We thus go to 12 bytes before EOF.
        docIndex_handle.seek(-12, os.SEEK_END)
        docindex_tag = docIndex_handle.read(12)

        # print(docindex_tag)
        # Move the file pointer back after read of docIndex tag.
        docIndex_handle.seek(-12, os.SEEK_END)
        for xml_string in xml_strings:
            # Since we open the file in binary mode
            # We encode the xml_string to its
            # UTF-8 binary string.
            # We also append 4 spaces for indentation.
            xml_bytes_string = ("    " + xml_string).encode("UTF-8")
            # print(bytes_string)
            docIndex_handle.write(xml_bytes_string)
            docIndex_handle.write("\n".encode("UTF-8"))
        # After writing the xml strings to the file,
        # we add the docIndex tag that was overwritten
        # by the xml strings.
        docIndex_handle.write(docindex_tag)


def create_template_string(doc_elements: List[Dict], folder_name) -> str:
    template_string = (
        "This folder originally contained an archive file \n"
        "that has been recursively unpacked. \n"
        "The containing files have been moved to a new directory:\n \n"
    )
    for doc_element in doc_elements:
        doc_element_string = ""
        doc_element_string += "{}: {}\n".format(
            "Original filename", doc_element["oFn"]
        )
        doc_element_string += "{}: {} / {}\n \n".format(
            "Moved to", doc_element["dCf"], doc_element["dID"]
        )

        template_string += doc_element_string
    return template_string


def update_parent_child_table(doc_elements, root):
    """
    Updates the newly created table in the Tables folder
    with records on the form:
    <table some_namespaces>
        <row>
            <c1> parent id </c1>
            <c2> child id (new folder name)</c2>
            <c3> new docCollection </c3>
        </row>
    </table>
    where each row represents a document that was moved to a new docCollection.
    """
    colomn_keys = ["pID", "dID", "dCf"]
    for doc_element in doc_elements:
        row = ET.SubElement(root, "row")
        for colomn_count, colomn_key in enumerate(colomn_keys, start=1):
            ET.SubElement(
                row, (f"c{colomn_count}")
            ).text = f"{doc_element[colomn_key]}"


def create_new_table_index_element(
    table_index_path: Path, folder_name, row_count
):
    tree = ET.parse(table_index_path)
    root = tree.getroot()
    tables_element = root.find("{http://www.sa.dk/xmlns/diark/1.0}tables")
    table_root = ET.SubElement(tables_element, "table")
    description = (
        "Parent child relation table for"
        " moved files originally located in a container."
    )

    ET.SubElement(table_root, "name").text = "parentChildRelationTable"
    ET.SubElement(table_root, "folder").text = folder_name
    ET.SubElement(table_root, "description").text = description
    columns = ET.SubElement(table_root, "columns")

    column1 = ET.SubElement(columns, "column")
    ET.SubElement(column1, "name").text = "parentID"
    ET.SubElement(column1, "columnID").text = "c1"
    ET.SubElement(column1, "type").text = "INTEGER"
    ET.SubElement(column1, "typeOriginal").text = "INT UNSIGNED"
    ET.SubElement(column1, "nullable").text = "false"
    ET.SubElement(
        column1, "description"
    ).text = "Entydigt ID for dokumentets Parent mappe."
    ET.SubElement(
        column1, "functionalDescription"
    ).text = "parentDokumentIdentifikation"

    column2 = ET.SubElement(columns, "column")
    ET.SubElement(column2, "name").text = "childID"
    ET.SubElement(column2, "columnID").text = "c2"
    ET.SubElement(column2, "type").text = "INTEGER"
    ET.SubElement(column2, "typeOriginal").text = "INT UNSIGNED"
    ET.SubElement(column2, "nullable").text = "false"
    ET.SubElement(
        column2, "description"
    ).text = "Entydigt ID for dokumentets mappe."
    ET.SubElement(
        column2, "functionalDescription"
    ).text = "childDokumentIdentifikation"

    column3 = ET.SubElement(columns, "column")
    ET.SubElement(column3, "name").text = "childDocCollection"
    ET.SubElement(column3, "columnID").text = "c3"
    ET.SubElement(column3, "type").text = "CHARACTER VARYING(100)"
    ET.SubElement(column3, "typeOriginal").text = "VARCHAR"
    ET.SubElement(column3, "nullable").text = "false"
    ET.SubElement(
        column3, "description"
    ).text = (
        "Entydigt ID for den docCollection, som dokumentet er flyttet til."
    )
    ET.SubElement(
        column3, "functionalDescription"
    ).text = "childdokumentDocCollectionIdentifikation"

    primary_key = ET.SubElement(table_root, "primaryKey")
    ET.SubElement(primary_key, "name").text = "PK_parentChildRelationTable"
    ET.SubElement(primary_key, "column").text = "childID"

    row_count = ET.SubElement(table_root, "rows").text = f"{row_count}"

    tree = ET.ElementTree(root)
    tree.write(table_index_path)


def make_copy(path: Path):
    copy_destination = path.with_name(path.name + "Copy")
    shutil.copy(path, copy_destination)
    return copy_destination

if __name__ == "__main__":

    if argv[1] == "help":
        print(
            """
        Use as `python rearranger.py docCollection_dir
        newDocCollectionNumber, dIDCounter, newTableNumber`

        Argument 1 is the directory that contains the docCollections.
        Argument 2 is the new docCollection number.
        Argument 3 is the counter for the new dID, i.e. the last dID + 1.
        Argument 4 is the new table number for the parent child relation table.

        """
        )

    else:

        # Root is the directory that contains the docCollections.
        ET.register_namespace("", "http://www.sa.dk/xmlns/diark/1.0")
        root = Path(argv[1])
        new_docCollection = root / ("docCollection" + argv[2])
        new_docCollection.mkdir(exist_ok=True)
        doc_index_path = root.parent / "Indices" / "docIndex.xml"
        doc_index_copy = make_copy(doc_index_path)
        table_index_path = root.parent / "Indices" / "tableIndex.xml"
        table_folder_path = root.parent / "Tables" / ("table" + argv[4])
        table_folder_path.mkdir(exist_ok=True)
        table_xml_file = table_folder_path / f"table{argv[4]}.xml"
        parent_child_table_root = ET.Element("table")

        row_count = 0
        try:
            count = int(argv[3])
        except ValueError:
            print(f"Could not parse the string: {argv[3]} as an integer.")

        for docCollection in root.iterdir():
            print(f"Start processing of {docCollection.name}")
            extracted_folders = []
            for doc_folder in docCollection.iterdir():
                if doc_folder.is_dir():
                    for item in doc_folder.iterdir():
                        if item.suffix == ".extracted":
                            extracted_folders.append(item)

            for folder in extracted_folders:
                try:
                    doc_elements, count = rearrange_files(
                    folder, new_docCollection, count
                    )
                except FileExistsError as e:
                    print("Skipping file since it already exists.")
                    print(e)
                    count+=1

                
                try:
                    for element in doc_elements:
                        print(element["oFn"])
                except NameError:
                    continue
                # Add tiff template
                tiff_template_string = create_template_string(
                    doc_elements, folder.name
                )
                stringToTiffPrinter(
                    tiff_template_string, (folder.parent / "1.tiff")
                )

                # Convert the doc_elements to xml strings
                # and append them to docIndex.
                doc_element_xml_strings = doc_elements_to_xml(doc_elements)
                append_to_docIndex(doc_index_copy, doc_element_xml_strings)

                update_parent_child_table(
                    doc_elements, parent_child_table_root
                )
                row_count += len(doc_elements)

            parent_child_tree = ET.ElementTree(parent_child_table_root)
            #ET.indent(parent_child_tree, "    ", 0)
            parent_child_tree.write(table_xml_file)

            create_new_table_index_element(
                table_index_path, table_folder_path.name, row_count
            )
            print(f"Finished processing {docCollection.name}.")
