from pathlib import Path

def from_text(fpath):
  return Path(fpath).read_text()

def from_pdf(fpath):
  from pypdf import PdfReader

  reader = PdfReader("example.pdf")    
  text = "\n".join(page.extract_text() for page in reader.pages)
  return text

def chunk(text, chunk_size=1000):
  chunks = []
  for i in range(0, len(text), chunk_size):
    chunks.append(text[i:i+chunk_size])
  return chunks
  