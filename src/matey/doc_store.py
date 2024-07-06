import hashlib
from datetime import datetime, timedelta
from .db import db_get, db_put, db_query, db_delete
from .config_utils import get_config

class DocStore:
  def __init__(self, repo_id=None):
    if repo_id is None:
      self.repo_id = get_config().get("repo_id", "matey")  # type: ignore
    else:
      self.repo_id = repo_id
    self.prefix = f"DocStore-00a"

  def store(self, text):
    text_hash = hashlib.sha1(text.encode()).hexdigest()[:10]
    doc_key = f"{self.prefix}-{text_hash}"
    db_put(doc_key, {
      "type": "doc_store",      
      "repo": self.repo_id,
      "text": text,
      "timestamp": datetime.now().astimezone()})
    
  def query(self, since_days: int|None=None):
    queries = [("type", "==", "doc_store"), 
               ("repo", "==", self.repo_id)]
    if since_days:
      queries = [("timestamp", ">", datetime.now().astimezone()-timedelta(days=since_days))]
    snapshots = db_query(queries, return_dict=False)
    return snapshots
  
  def docref(self, doc_id):
    doc = db_get(doc_id, return_ref=True)
    return doc

  def ls(self, since_days: int|None=None):
    docs = self.query(since_days)
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]  # type: ignore
  
  def delete(self, since_days: int|None=None):
    docs = self.query(since_days)
    for doc in docs:
      doc_ref = doc.reference # type: ignore
      doc_ref.delete()
