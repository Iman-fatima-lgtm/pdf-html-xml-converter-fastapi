import fitz  # PyMuPDF
import base64
import os

header_keywords = [
    "ZnO Nanoparticles Mitigate Cadmium Stress in Tomato",
    "Irfan et al.",
    "Intl J Agric Biol"
]

def process_pdf(pdf_path: str, file_id: str) -> str:
    doc = fitz.open(pdf_path)
    html_content = ["<html><body style='text-align:center;'>"]
    exclude_title_line = "Full Length Article"

    for page_num in range(len(doc)):
        page = doc[page_num]
        rect = page.rect
        page_text = page.get_text("dict")

        # Remove footers
        for block in page_text["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    x0, y0, x1, y1 = span["bbox"]

                    is_footer = y0 > rect.y1 - 100
                    is_page_number = (
                        text.lower().startswith("page") or
                        text.lower().startswith("p.") or
                        text.strip().isdigit()
                    )

                    if is_footer and is_page_number:
                        page.draw_rect(fitz.Rect(x0, y0, x1, y1), color=(1, 1, 1), fill=(1, 1, 1))

        # Header crop logic
        crop_top_y = rect.y0
        if page_num == 0:
            for block in page_text["blocks"]:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if exclude_title_line.lower() in span["text"].strip().lower():
                            crop_top_y = span["bbox"][3] + 5
                            break
        else:
            max_header_y = rect.y0
            for block in page_text["blocks"]:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        span_text = span["text"].strip()
                        if any(keyword in span_text for keyword in header_keywords):
                            span_y1 = span["bbox"][3]
                            max_header_y = max(max_header_y, span_y1 + 5)
            max_safe_crop = rect.y0 + (rect.y1 - rect.y0) * 0.3
            crop_top_y = min(max_header_y, max_safe_crop)

        crop_rect = fitz.Rect(rect.x0, crop_top_y, rect.x1, rect.y1)
        pix = page.get_pixmap(dpi=150, clip=crop_rect)

        img_bytes = pix.tobytes("png")
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        html_content.append(f'<img src="data:image/png;base64,{img_base64}" style="max-width:100%;"><br><br>')

    html_content.append("</body></html>")

    os.makedirs("output", exist_ok=True)
    html_path = f"output/{file_id}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_content))

    return html_path
