
import json
from pathlib import Path
from tqdm.auto import tqdm
from .notebook import Notebook

class NbBinder:
  def __init__(self, nb_base_dir):
    self.nb_base_dir = Path(nb_base_dir)    
    self.metadata = self.load_metadata()
    self.update_metadata()

  def load_metadata(self):
    metadata_path = self.nb_base_dir / "binder.json"
    if metadata_path.exists():
      with open(metadata_path, "r") as f:
        metadata = json.load(f)
    else:
      metadata = {}
    return metadata
  
  def update_metadata(self):
    nb_base_dir = self.nb_base_dir
    nb_files = list(nb_base_dir.glob("**/*.ipynb"))
    metadata = self.load_metadata()

    for nb_path_x in tqdm(nb_files):     
      nb_relpath = str(nb_path_x.relative_to(nb_base_dir))
      nb = Notebook.load(nb_path_x)

      # use cache if exists    
      if nb_relpath in metadata:
        cached_filehash = metadata[nb_relpath]["filehash"]
        if cached_filehash == nb.filehash:
          continue
      
      # write an updated entry
      metadata[nb_relpath] = {
        "filehash": nb.filehash,
        "filename": nb.filename,
        "dataio": nb.get_data_io(),
        "yaml": nb.get_yaml()
      }

    self.metadata = metadata

  def save(self):
    metadata_path = self.nb_base_dir / "binder.json"
    with open(metadata_path, "w", encoding="UTF-8") as f:
      json.dump(self.metadata, f, indent=2, ensure_ascii=False)