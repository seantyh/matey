
# %%
import base64
from io import BytesIO, StringIO
from pathlib import Path
import hashlib
import nbformat
from PIL import Image
from dataclasses import dataclass

class CellOutput:
    def __init__(self, **kwargs):
        self.output_type = kwargs.get("output_type", "")
        self.data = kwargs.get("data", {})
        self.metadata = kwargs.get("metadata", {})
        self.execution_count = kwargs.get("execution_count", 0)

    def get_data(self, mime_type: str|list[str]):
        if isinstance(mime_type, str):
            mime_type = [mime_type]
        return [self.data.get(m, "")
                for m in mime_type]

@dataclass
class NotebookCell:
    cell_type: str
    source: str
    outputs: list[CellOutput]    

    def __str__(self):
        out = StringIO()

        if self.cell_type == "markdown":
            out.write(self.source)
        if self.cell_type == "code":
            if self.source:
              out.write(f"```\n{self.source}\n```\n")            

        if self.outputs:
          out.write("Output:\n")
          for output_x in self.outputs:
            out.write(f"```\n{output_x.get_data('text/plain')}\n```\n")
        return out.getvalue()

@dataclass
class Notebook:
    filename: str
    filehash: str
    cells: list[NotebookCell]       

def load_notebook(nb_path):
    nb_path = Path(nb_path)
    with open(nb_path, 'r') as f:
        nb = nbformat.read(f, as_version=4)
    
    filename = nb_path.stem
    filehash = hashlib.sha1(nb_path.read_bytes()).hexdigest()
    cells = [NotebookCell(
        c["cell_type"],
        c["source"],
        [CellOutput(**o) for o in c.get("outputs", [])],
      ) for c in nb["cells"]]

    notebook = Notebook(filename, filehash, cells)

    return notebook

def to_rag(cells: list[NotebookCell]):
    buf = StringIO()
    for c in cells:        
        buf.write(str(c))
        buf.write("\n------\n")
    return buf.getvalue()

def decode_image(b64_image:str):
    img_bytes = base64.b64decode(b64_image)
    img = Image.open(BytesIO(img_bytes))
    return img