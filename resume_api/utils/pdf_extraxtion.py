import fitz  # PyMuPDF

def extract_clean_text(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text_pages = []

    for page in doc:
        blocks = page.get_text("blocks")
        links = page.get_links()

        link_rects = [(fitz.Rect(link["from"]), link["uri"]) for link in links if "uri" in link]

        page_text_with_links = ""

        for block in blocks:
            block_rect = fitz.Rect(block[:4])
            block_text = block[4]

            appended_urls = []
            for rect, uri in link_rects:
                if rect.intersects(block_rect):
                    appended_urls.append(uri)

            combined = block_text
            for url in appended_urls:
                combined += " " + url  # <-- space added here

            page_text_with_links += combined

        full_text_pages.append(page_text_with_links)

    return "\n\n".join(full_text_pages)
