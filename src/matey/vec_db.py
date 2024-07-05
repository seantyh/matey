import json
from pathlib import Path
import numpy as np
from sklearn.neighbors import NearestNeighbors
from litellm import embedding

def load_vecmat(fpath):
  if not Path(fpath).exists():
    return np.array([])
  return np.load(fpath)

def load_metadata(fpath):
  if not Path(fpath).exists():
    return []
  return json.loads(Path(fpath).read_text())

class VecDB:  
  def __init__(self, embmat_path="vdb.npy", metadata_path="vdb.json"):    
    self.embmat_path = embmat_path
    self.metadata_path = metadata_path
    self.embmat = load_vecmat(embmat_path)
    self.metadata = load_metadata(metadata_path)
  
  def store(self, text_list, metadata=None):
    if metadata is None:
      metadata = [{"text": x} for x in text_list]
    if isinstance(text_list, str):
      text_list = [text_list]
    if isinstance(metadata, str):
      metadata = [metadata]

    assert len(text_list) == len(metadata)

    emb_resp = embedding(
      model="text-embedding-3-small", 
      input=text_list
    )

    emb_list = np.array([emb["embedding"] for emb in emb_resp["data"]])
    emb_list = emb_list[:, :emb_list.shape[1]//2]
    if self.embmat.size == 0:
      self.embmat = emb_list      
    else:
      self.embmat = np.concatenate([self.embmat, emb_list], axis=0)
    self.metadata.extend(metadata)
    
  def query(self, query:str|list[str]):
    emb_resp = embedding(model="text-embedding-3-small", input=query)
    q_emb = np.array(emb_resp["data"][0]["embedding"])
    knn = NearestNeighbors(n_neighbors=min(5, self.embmat.shape[0]), metric="cosine")
    knn.fit(self.embmat)
    _, indices = knn.kneighbors(q_emb.reshape(1, -1))
    return [self.metadata[idx] for idx in indices[0]]
  
  def save(self):
    np.save(self.embmat_path, self.embmat)
    Path(self.metadata_path).write_text(json.dumps(self.metadata))