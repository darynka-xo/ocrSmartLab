from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import camelot
import time

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_tables_from_pdf(pdf_path):
    tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
    return tables


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""

    for page_num in range(doc.page_count):
        page = doc[page_num]

        # Convert PDF page to an image
        img = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72))  # Adjust resolution as needed
        img_bytes = img.samples
        img_PIL = Image.frombytes("RGB", [img.width, img.height], img_bytes)

        # Perform OCR on the image
        ocr_text = pytesseract.image_to_string(img_PIL, lang='rus')
        text += ocr_text + "\n"

    doc.close()
    return text



def save_text_to_file(text, output_path):
    with open(output_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)

def insert_tables_into_text(text, tables):
    new_text = []

    for i, table in enumerate(tables):
        table_text = table.df.to_string(index=False)
        new_text.append(f"Table {i + 1}:")
        new_text.append(table_text)

    return '\n'.join(new_text)

@app.route('/', methods=['GET', 'POST'])
def index():
    download_link = None  # Initialize the download_link variable
    file_generated = False  # Track whether the text file has been generated

    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty part without a filename.
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # Save the uploaded PDF file
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)

            # Extract text and tables from PDF
            extracted_tables = extract_tables_from_pdf(filename)
            extracted_text = extract_text_from_pdf(filename)


            # Save extracted text to a TXT file
            txt_output_path = filename.replace('.pdf', '.txt')
            save_text_to_file(extracted_text        , txt_output_path)
            if os.path.exists(txt_output_path):
                download_link = url_for('download_txt_file', filename=os.path.basename(txt_output_path))
                file_generated = True
                return send_file(txt_output_path, as_attachment=True, download_name="{}".format(txt_output_path))
    return render_template('index.html', download_link=download_link, file_generated=file_generated)


@app.route('/download_txt/<filename>')
def download_txt_file(filename):
    txt_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Check if the file exists
    if os.path.exists(txt_file_path):
        return send_file(txt_file_path, as_attachment=True)
    else:
        return "File not found"


if __name__ == "__main__":
    app.run(debug=True)