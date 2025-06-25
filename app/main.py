from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import os
from app.pdf_processor import process_pdf
from app.docx_converter import convert_pdf_to_word_xml

app = FastAPI()

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/upload-pdf-crop/")
async def upload_pdf_crop(id: str = Form(...), file: UploadFile = File(...)):
    pdf_path = os.path.join(OUTPUT_DIR, f"{id}.pdf")

    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    html_path = process_pdf(pdf_path, id)
    return FileResponse(html_path, media_type="text/html", filename="cropped_output.html")


@app.post("/upload-pdf-to-xml/")
async def upload_pdf_to_xml(id: str = Form(...), file: UploadFile = File(...)):
    pdf_path = os.path.join(OUTPUT_DIR, f"{id}.pdf")

    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    xml_path = convert_pdf_to_word_xml(pdf_path, id)
    return FileResponse(xml_path, media_type="application/xml", filename="word_compatible_output.xml")
