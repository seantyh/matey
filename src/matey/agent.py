from pathlib import Path
from datetime import datetime, timedelta
import hashlib
from .llm_api import Session
from .db import db_put, db_get, db_query
from .config_utils import get_config
from .image_utils import get_image_base64

from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from .notebook import Notebook

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

  def __call__(self, message, context=None):
    if context is not None:
      message = "Here are some contexts for this conversation: \n" +\
                "## Context\n" + context + "\n\n" + message
    return self.session(message, stream=True)
  
  @property
  def history(self):        
    def short(x):      
      return x[:30] + ("..." if len(x) > 20 else "")
    return [(i, x["role"], short(x["content"])) for i, x in enumerate(self.session.states)]

  def get(self, idx):
    obj = self.session.states[idx]
    return obj["content"]
  
class NotebookAgent:
  def __init__(self, repo_id=None):        
    self.agent_prefix = "NAgent-00a"
    self.repo_id = get_repo_id(repo_id)

  def __call__(self, nb: "Notebook", use_cache=True):
    nb_fingerprint = f"{self.agent_prefix}-{nb.filename}-{nb.filehash}"

    doc = db_get(nb_fingerprint, return_ref=False)
    
    if doc and use_cache and "summary" in doc:  # type: ignore
      return doc["summary"]  # type: ignore
    else:
      summary = self.summarize(nb)
      db_put(nb_fingerprint, {"type": "notebook_summary",
                              "repo": self.repo_id,
                              "summary": summary, 
                              "filepath": str(nb.filename), 
                              "filehash": nb.filehash, 
                              "timestamp": datetime.now().astimezone()})
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
  
    
