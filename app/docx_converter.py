import os, base64, zipfile, mimetypes, shutil, uuid
from lxml import etree
from pdf2docx import Converter

def convert_pdf_to_word_xml(pdf_path: str, file_id: str) -> str:
    docx_filename = f"output/{file_id}.docx"
    unzip_dir = f"output/{file_id}_unzipped"
    output_xml_path = f"output/{file_id}.xml"

    # Convert PDF to DOCX
    cv = Converter(pdf_path)
    cv.convert(docx_filename)
    cv.close()

    # Unzip DOCX
    os.makedirs(unzip_dir, exist_ok=True)
    with zipfile.ZipFile(docx_filename, 'r') as zip_ref:
        zip_ref.extractall(unzip_dir)

    # Build Word-compatible XML
    pkg_package = build_pkg_package(unzip_dir)

    # Save XML
    xml_content = etree.tostring(pkg_package, pretty_print=True, encoding='utf-8')
    xml_declaration = b'<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
    processing_instruction = b'<?mso-application progid="Word.Document"?>\n'

    with open(output_xml_path, "wb") as f:
        f.write(xml_declaration + processing_instruction + xml_content)

    # Clean up intermediate files
    shutil.rmtree(unzip_dir)
    os.remove(docx_filename)

    return output_xml_path

def build_pkg_package(input_dir):
    NSMAP = {None: "http://schemas.microsoft.com/office/2006/xmlPackage"}
    pkg_package = etree.Element("{http://schemas.microsoft.com/office/2006/xmlPackage}package", nsmap=NSMAP)

    for root, _, files_in_dir in os.walk(input_dir):
        for file in files_in_dir:
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, input_dir).replace("\\", "/")
            with open(full_path, "rb") as f:
                content = f.read()

            content_type, _ = mimetypes.guess_type(file)
            if not content_type:
                content_type = "application/octet-stream"

            part_elem = etree.SubElement(pkg_package,
                                         "{http://schemas.microsoft.com/office/2006/xmlPackage}part",
                                         name=f"/{relative_path}",
                                         contentType=content_type,
                                         compression="store",
                                         padding="512")

            if file.endswith(".xml") or file.endswith(".rels"):
                try:
                    xml_tree = etree.fromstring(content)
                    xml_data_elem = etree.SubElement(part_elem, "{http://schemas.microsoft.com/office/2006/xmlPackage}xmlData")
                    xml_data_elem.append(xml_tree)
                except Exception:
                    binary_elem = etree.SubElement(part_elem, "{http://schemas.microsoft.com/office/2006/xmlPackage}binaryData")
                    binary_elem.text = base64.b64encode(content).decode('utf-8')
            else:
                binary_elem = etree.SubElement(part_elem, "{http://schemas.microsoft.com/office/2006/xmlPackage}binaryData")
                binary_elem.text = base64.b64encode(content).decode('utf-8')

    return pkg_package
