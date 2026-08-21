
import sys; sys.path.append('src')
try:
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument('test_doc.pdf')
    for i in range(len(pdf)):
        page = pdf[i]
        image = page.render(scale=2).to_pil()
        print(f'Page {i} size:', image.size)
except Exception as e:
    print('Error:', e)

