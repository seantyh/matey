from pathlib import Path
from datetime import datetime, timedelta
import hashlib
from .llm_api import Session
from .notebook import Notebook
from .db import db_put, db_get, db_query
from .config_utils import get_config
from .image_utils import get_image_base64

def get_repo_id(repo_id=None):
  if repo_id is None:
    config = get_config()
    repo_id = config.get("repo_id", "matey")  # type: ignore
  return repo_id
class DispatchAgent:
  def __init__(self, prefix=None):
    system_prompt = (Path(__file__).parent / "prompts/system_prompt.txt").read_text()
    self.session = Session(system_prompt)
    if prefix is None:      
      self.prefix = get_repo_id() + "-dispatch" # type: ignore
    else:
      self.prefix = prefix 

  def __call__(self, message):
    return self.session(message)
      
class ChatAgent:
  def __init__(self, prefix=None):    
    self.session = Session()
    if prefix is None:      
      self.prefix = get_repo_id() + "-chat" # type: ignore
    else:
      self.prefix = prefix

  def __call__(self, message):
    return self.session(message)
  
  def load_states(self, days=7):
    docs = db_query([
      ("type", "==", "agent_state"),
      ("prefix", "==", self.prefix),
      ("timestamp", ">", datetime.now() - timedelta(days=days))              
    ], return_docref=False)
    
    states_loaded = []
    for doc in docs:
      if not isinstance(doc, dict): continue
      doc_timestamp = doc["timestamp"].isoformat()
      state = {"role": "user", 
               "content": f"[{doc_timestamp}] " + doc["state"]}
      self.session.states.append(state)
      states_loaded.append(state)

    return states_loaded

  def save_state(self, offset=-1):
    state = [x for x in self.session.states if x["role"]=="user"][offset]
    state_hash = hashlib.sha1(str(state).encode()).hexdigest()
    doc_key = f"mateyAgent-{state_hash}"
    db_put(doc_key, {
      "type": "agent_state",
      "prefix": self.prefix,
      "state": state["content"],
      "timestamp": datetime.now()})
  
class NotebookAgent:
  def __init__(self, repo_id=None):        
    self.agent_prefix = "NAgent-00a"
    self.repo_id = get_repo_id(repo_id)

  def __call__(self, nb_path, use_cache=True):
    nb_path = Path(nb_path)
    if not nb_path.exists():
      raise FileNotFoundError(f"Notebook file not found: {nb_path}")
    nb = Notebook.load(nb_path)
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
    rag_text = nb.to_rag()
    session = Session()
    prompt = (Path(__file__).parent / "prompts/notebook_prompt.txt").read_text()
    prompt = prompt.format(filename=nb.filename, rag_text=rag_text)
    summary = session(prompt)
    return summary
  
class DataIOAgent:
  def __init__(self):    
    self.repo_id = get_repo_id()    
    self.session = Session()

  def __call__(self, context):
    prompt = (Path(__file__).parent / "prompts/dataio_prompt.txt").read_text()
    return self.session(prompt.replace("{context}", context))
    
class SummaryAgent:
  def __init__(self):    
    self.repo_id = get_repo_id()    
    self.session = Session()

  def __call__(self, context):
    prompt = "Summarize the following text: \n{context}\n\n## Summary\n\n"
    return self.session(prompt.replace("{context}", context))

class CaptionAgent:
  def __init__(self):
    self.repo_id = get_repo_id()    
    self.session = Session()
  
  def __call__(self, image_path, prompt=None):
    if prompt is None:
      prompt = "Describe this image"
    image_base64 = get_image_base64(image_path)
    if image_base64 is None:
      return "Error: Could not load image"
    message = [{"type": "text", "text": prompt}, 
               {"type": "image_url", "image_url": {"url": image_base64}}]
    return self.session(message)
  
    
