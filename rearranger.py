import os
from pathlib import Path
import shutil
from typing import Any, Dict, List
from sys import argv


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
) -> List[Dict]:
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
    new_doc_collection.mkdir()
    doc_elements = []
    for path, subdirs, filenames in os.walk(extracted_folder):
        for filename in filenames:
            if not is_archive(filename):
                file_path = Path(os.path.join(path, filename))
                destination: Path = new_doc_collection / str(count) / filename
                destination.parent.mkdir()
                shutil.copy(file_path, destination)
                pid = extracted_folder.name
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


if __name__ == "__main__":
    # Root is the directory that contains the docCollections.
    root = Path(argv[1])
    new_docCollection = root / ("docCollection" + argv[2])
    doc_index_path = root.parent / "Indices" / "docIndex.xml"

    try:
        count = int(argv[3])
    except ValueError:
        print(f"Could not parse the string: {argv[3]} as an integer.")

    for docCollection in root.iterdir():
        print(f"Start processing of {docCollection.name}")
        extracted_folders = []
        for doc_folder in docCollection.iterdir():
            for item in doc_folder.iterdir():
                if item.suffix == ".extracted":
                    extracted_folders.append(item)

        for folder in extracted_folders:
            doc_elements, count = rearrange_files(
                folder, new_docCollection, count
            )
            # Convert the doc_elements to xml strings
            # and append them to docIndex.
            doc_element_xml_strings = doc_elements_to_xml(doc_elements)
            append_to_docIndex(doc_index_path, doc_element_xml_strings)
        print(f"Finished processing {docCollection.name}.")
