from pathlib import Path
from datetime import datetime, timedelta
import hashlib
from .llm_api import Session
from .ipynb_api import to_rag, load_notebook
from .db import db_put, db_get, db_query
class Agent:
  def __init__(self, prefix=""):
    system_prompt = (Path(__file__).parent / "prompts/system_prompt.txt").read_text()
    self.session = Session(system_prompt)
    self.prefix = prefix

  def __call__(self, message):
    return self.session(message)
  
  def load_state(self, days=7):
    docs = db_query([
      ("type", "==", "agent_state"),
      ("prefix", "==", self.prefix),
      ("timestamp", ">", datetime.now() - timedelta(days=days))              
    ])
    
    return [doc["state"] for doc in docs if doc]

  def save_state(self, offset=-1):
    state = self.session.states[offset]
    state_hash = hashlib.sha1(str(state).encode()).hexdigest()
    doc_key = f"mateyAgent-{state_hash}"
    db_put(doc_key, {
      "type": "agent_state",
      "prefix": self.prefix,
      "state": state["content"],
      "timestamp": datetime.now()})
  
class NotebookAgent:
  def __init__(self, repo_id):        
    self.agent_prefix = "NAgent-00a"
    self.repo_id = repo_id

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
                              "repo": self.repo_id,
                              "summary": summary, 
                              "filepath": str(nb_path), 
                              "filehash": nb.filehash, 
                              "timestamp": datetime.now()})
      return summary
    
  def summarize(self, nb):
    rag_text = to_rag(nb.cells)
    session = Session()
    prompt = (Path(__file__).parent / "prompts/notebook_prompt.txt").read_text()
    prompt = prompt.format(filename=nb.filename, rag_text=rag_text)
    summary = session(prompt)
    return summary
