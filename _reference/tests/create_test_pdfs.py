import os
from reportlab.pdfgen import canvas

def create_valid_pdf(filename, content):
    c = canvas.Canvas(filename)
    c.drawString(100, 750, content)
    c.save()

def create_corrupted_pdf(filename):
    with open(filename, 'wb') as f:
        f.write(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n' + os.urandom(1024))

if __name__ == "__main__":
    create_valid_pdf('valid1.pdf', 'This is a valid PDF 1.')
    create_valid_pdf('valid2.pdf', 'This is a valid PDF 2.')
    create_corrupted_pdf('corrupt.pdf')
    print("Created test files.")
