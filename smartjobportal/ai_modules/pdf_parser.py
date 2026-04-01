import re

def extract_text_from_pdf(path: str) -> str:
    text = ''
    try:
        import fitz
        doc = fitz.open(path)
        for page in doc: text += page.get_text()
        doc.close()
        if text.strip(): return _clean(text)
    except Exception: pass
    try:
        import PyPDF2
        with open(path,'rb') as f:
            for page in PyPDF2.PdfReader(f).pages:
                text += page.extract_text() or ''
        if text.strip(): return _clean(text)
    except Exception: pass
    try:
        from pdfminer.high_level import extract_text as pm
        text = pm(path)
        if text.strip(): return _clean(text)
    except Exception: pass
    return text

def _clean(text: str) -> str:
    text = text.encode('utf-8','ignore').decode('utf-8')
    text = re.sub(r'[•◦▪▸►‣⁃◉○●■□]',' ',text)
    text = re.sub(r'https?://\S+|www\.\S+','',text)
    text = re.sub(r'\S+@\S+\.\S+','',text)
    text = re.sub(r'[\+]?[\d\s\-\(\)]{10,}','',text)
    text = re.sub(r'[ \t]+',' ',text)
    text = re.sub(r'\n{3,}','\n\n',text)
    lines = [l.strip() for l in text.split('\n') if len(re.findall(r'[a-zA-Z]',l)) >= 3]
    return '\n'.join(lines).strip()
