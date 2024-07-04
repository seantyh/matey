
# %%
import re
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
        text = kwargs.get("text", [])
        if text:
            self.data["text/plain"] = text
        self.metadata = kwargs.get("metadata", {})
        self.execution_count = kwargs.get("execution_count", 0)

    def get_data(self, mime_type: str):
        data = self.data.get(mime_type, "")
        if isinstance(data, list):
            data = "\n".join(data)
        return data
                    
    def __repr__(self):
        data_types = ", ".join(self.data.keys())
        return f"<CellOutput: {self.output_type}, {data_types}>"

@dataclass
class NotebookCell:
    cell_type: str
    source: str
    outputs: list[CellOutput]    
    metadata: dict

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

class Notebook:
    def __init__(self, filename, filehash, cells):
        self.filename: str = filename
        self.filehash: str = filehash
        self.cells: list[NotebookCell] = cells

    @staticmethod
    def load(nb_path):
        nb_path = Path(nb_path)
        with open(nb_path, 'r') as f:
            nb = nbformat.read(f, as_version=4)
        
        filename = nb_path.stem
        filehash = hashlib.sha1(nb_path.read_bytes()).hexdigest()
        cells = [NotebookCell(
                    c["cell_type"],
                    c["source"],            
                    [CellOutput(**o) for o in c.get("outputs", [])],
                    c.get("metadata", {}))
                 for c in nb["cells"]]

        notebook = Notebook(filename, filehash, cells)

        return notebook

    def to_rag(self):
        buf = StringIO()
        for c in self.cells:        
            buf.write(str(c))
            buf.write("\n------\n")
        return buf.getvalue()
    
    def search(self, pattern):
        hits = []
        pat = re.compile(pattern)
        for cidx, c in enumerate(self.cells):
            if pat.search(c.source):
                hits.append(c)
                continue

            for output_x in c.outputs:
                if pat.search(output_x.get_data("text/plain")):
                    hits.append(c)
                    continue
        return hits          
        
    def locate_cell(self, cell_type=None, keyword=None):
        assert cell_type or keyword, "Must provide cell_type or keyword"

        hit_cell = None
        if keyword:
            pat = re.compile(keyword, re.IGNORECASE)
        else:
            pat = re.compile("")

        for cidx, c in enumerate(self.cells):
            if cell_type and c.cell_type != cell_type:
                continue
            if keyword and pat.search(c.source.lower()) is None:
                continue

            hit_cell = (cidx, c)
            break
        return hit_cell     
    
    def parse_file_hashes(self, lines: list[str]):
        ## sanitize the output from R (remove the leading [1])
        lines = [x.removeprefix("[1] \"").rstrip("\"") for x in lines]                
        hash_pat = re.compile("[0-9a-f]{40}")
        ret = []
        for ln in lines:
            hash_mat = hash_pat.search(ln)
            if hash_mat is None: continue
            hash_str = hash_mat.group(0)
            filepath = ln.replace(hash_str, "").strip()
            ret.append({"filepath": filepath, "sha1": hash_str})

        return ret
    
    def input_files(self):
        loc_cell = self.locate_cell(cell_type="markdown", keyword="Data dependencies")
        if loc_cell is not None:
            tgt_cell_idx = loc_cell[0]+1
            tgt_cell = self.cells[tgt_cell_idx]
            hash_lines = [o.get_data("text/plain") for o in tgt_cell.outputs]
            if hash_lines:
                input_files = self.parse_file_hashes(hash_lines)
            else:
                input_files = None
            return input_files
        return None
    
    def output_files(self):
        loc_cell = self.locate_cell(cell_type="markdown", keyword="Export Art[ie]facts?")
        if loc_cell is not None:
            tgt_cell_idx = loc_cell[0]+1
            tgt_cell = self.cells[tgt_cell_idx]
            hash_lines = [o.get_data("text/plain") for o in tgt_cell.outputs]
            if hash_lines:
                output_files = self.parse_file_hashes(hash_lines)
            else:
                output_files = None
            return output_files
        
        return None

def decode_image(b64_image:str):
    img_bytes = base64.b64decode(b64_image)
    img = Image.open(BytesIO(img_bytes))
    return img