from celery import Celery
import camelot
from PIL import Image
import pytesseract
import fitz

celery = Celery(
    'app',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery.task
def process_pdf(pdf_path):
    def extract_tables_from_pdf(pdf_path):
        tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream', table_areas=['0,700,800,0'])
        return tables

    def insert_tables_into_text(text, tables):
        new_text = []

        for i, table in enumerate(tables):
            table_data = table.df
            new_text.append(f"\nTable {i + 1}:\n{table_data.to_csv(index=False)}\n")

        return '\n'.join(new_text)

    def extract_text_from_pdf(pdf_path):
        doc = fitz.open(pdf_path)
        text = ""

        for page_num in range(doc.page_count):
            page = doc[page_num]

            img = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72))
            img_bytes = img.samples
            img_PIL = Image.frombytes("RGB", [img.width, img.height], img_bytes)

            ocr_text = pytesseract.image_to_string(img_PIL, lang='rus')
            text += ocr_text + "\n"

        doc.close()
        return text
    extracted_tables = extract_tables_from_pdf(pdf_path)

    extracted_text = extract_text_from_pdf(pdf_path)

    extracted_text_with_tables = insert_tables_into_text(extracted_text, extracted_tables)

    return extracted_text_with_tables

if __name__ == '__main__':
    celery.start()
