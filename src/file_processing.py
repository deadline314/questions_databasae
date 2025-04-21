import os
import base64
import subprocess
from PyPDF2 import PdfReader, PdfWriter
import tempfile


def compress_pdf_with_gs(input_path, output_path, quality='ebook'):
    subprocess.run([
        'gs',
        '-sDEVICE=pdfwrite',
        '-dCompatibilityLevel=1.4',
        f'-dPDFSETTINGS=/{quality}',
        '-dNOPAUSE',
        '-dQUIET',
        '-dBATCH',
        f'-sOutputFile={output_path}',
        input_path
    ], check=True)

def split_pdf_to_bytes(filepath, max_parts=5, max_size_mb=4.5):
    max_bytes = int(max_size_mb * 1024 * 1024)
    reader = PdfReader(filepath)
    total_pages = len(reader.pages)
    pages_per_part = (total_pages + max_parts - 1) // max_parts

    byte_outputs = []

    for i in range(0, total_pages, pages_per_part):
        writer = PdfWriter()
        for j in range(i, min(i + pages_per_part, total_pages)):
            writer.add_page(reader.pages[j])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as raw_pdf:
            writer.write(raw_pdf)
            raw_pdf_path = raw_pdf.name

        with tempfile.NamedTemporaryFile(delete=False, suffix="_compressed.pdf") as compressed_pdf:
            compressed_pdf_path = compressed_pdf.name

        try:
            if os.path.getsize(raw_pdf_path) > max_bytes:
                compress_pdf_with_gs(raw_pdf_path, compressed_pdf_path)
                final_path = compressed_pdf_path
            else:
                final_path = raw_pdf_path

            with open(final_path, 'rb') as f:
                file_bytes = f.read()
                byte_outputs.append(file_bytes)

        finally:
            os.remove(raw_pdf_path)
            if os.path.exists(compressed_pdf_path):
                os.remove(compressed_pdf_path)

    return byte_outputs