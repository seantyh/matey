from pathlib import Path
from datetime import datetime
from .llm_api import Session
from .ipynb_api import to_rag, load_notebook
from .db import db_put, db_get, db_delete
class Agent:
  def __init__(self):
    system_prompt = (Path(__file__).parent / "prompts/system_prompt.txt").read_text()
    self.session = Session(system_prompt)

  def __call__(self, message):
    return self.session(message)
  
class NotebookAgent:
  def __init__(self):        
    self.agent_prefix = "NotebookAgent-0.1.0"

  def __call__(self, nb_path, use_cache=True):
    nb_path = Path(nb_path)
    if not nb_path.exists():
      raise FileNotFoundError(f"Notebook file not found: {nb_path}")
    nb = load_notebook(nb_path)
    nb_fingerprint = f"{self.agent_prefix}-{nb.filename}-{nb.filehash}"

    doc = db_get(nb_fingerprint)
    if doc and use_cache and "summary" in doc:
      return doc["summary"]
    else:
      summary = self.summarize(nb)
      db_put(nb_fingerprint, {"type": "notebook_summary",
                              "summary": summary, 
                              "filepath": str(nb_path), 
                              "filehash": nb.filehash, 
                              "timestamp": datetime.now().isoformat()})
      return summary
    
  def summarize(self, nb):
    rag_text = to_rag(nb.cells)
    session = Session()
    prompt = (Path(__file__).parent / "prompts/notebook_prompt.txt").read_text()
    prompt = prompt.format(filename=nb.filename, rag_text=rag_text)
    summary = session(prompt)
    return summary
