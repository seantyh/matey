import json
from pathlib import Path
import numpy as np
from sklearn.neighbors import NearestNeighbors
from litellm import embedding
from .config_utils import get_config

def load_vecmat(fpath):
  if not Path(fpath).exists():
    return np.array([])
  return np.load(fpath)

def load_metadata(fpath):
  if not Path(fpath).exists():
    return []
  return json.loads(Path(fpath).read_text())

class VecDB:
  __inst = None

  def __init__(self, embmat, metadata,
               embmat_path, metadata_path):
    self.embmat = embmat
    self.metadata = metadata
    self.embmat_path = embmat_path
    self.metadata_path = metadata_path

  @classmethod
  def getInstance(cls, embmat_path=None, metadata_path=None):    
    if cls.__inst is None:
      vdb_prefix = get_config().get("vdb_prefix", "vdb")  # type: ignore
      if embmat_path is None:
        embmat_path =  vdb_prefix + ".npy"
      if metadata_path is None:
        metadata_path = vdb_prefix + ".json"
      embmat_path = embmat_path
      metadata_path = metadata_path
      embmat = load_vecmat(embmat_path)
      metadata = load_metadata(metadata_path)
      cls.__inst = VecDB(embmat, metadata, embmat_path, metadata_path)
    else:
      return cls.__inst
  
  def put(self, text_list, metadata=None):
    if isinstance(text_list, str):
      text_list = [text_list]
    if metadata is None:
      metadata = [{"text": x} for x in text_list]    
    if isinstance(metadata, dict):
      metadata = [metadata]
    assert isinstance(metadata, list), "metadata must be a list of dictionaries"
    assert isinstance(metadata[0], dict), "metadata must be a list of dictionaries"
    assert len(text_list) == len(metadata)

    # ensure there is a text field in metadata
    for txt, md in zip(text_list, metadata):
      if "text" not in md:
        md["text"] = txt

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
    self.save()
  
  def ls(self):
    def short(x):
      return x[:30] + ("..." if len(x) > 30 else "")
    
    for i, md in enumerate(self.metadata):
      print(i, short(md["text"]))
        
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