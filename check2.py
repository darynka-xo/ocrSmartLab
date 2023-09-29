import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import camelot
import time
import os

os.environ['TESSDATA_PREFIX'] = '/usr/share/tesseract-ocr/4.00/tessdata/'



def extract_tables_from_pdf(pdf_path):
    tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
    return tables


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


def save_text_to_file(text, output_path):
    with open(output_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)


def main(pdf_path):
    start_time = time.time()

    extracted_tables = extract_tables_from_pdf(pdf_path)
    extracted_text = extract_text_from_pdf(pdf_path)

    # Process extracted tables
    for table_num, table in enumerate(extracted_tables):
        table_data = table.df
        extracted_text += f"\nTable {table_num + 1}:\n{table_data}\n"

    output_path = pdf_path.replace('.pdf', '.txt')
    save_text_to_file(extracted_text, output_path)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Text and table data extracted and saved to: {output_path}")
    print(f"Elapsed time: {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    pdf_path = "1st.pdf"
    main(pdf_path)
