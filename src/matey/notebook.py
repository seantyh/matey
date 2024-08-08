import re
import json
from pathlib import Path
from io import StringIO
import hashlib
import nbformat
from .agent import DataIOAgent, NotebookAgent

from .ipynb_types import NotebookCell, CellOutput

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
        
        filehash = hashlib.sha1(nb_path.read_bytes()).hexdigest()
        cells = [NotebookCell(
                    c["cell_type"],
                    c["source"],            
                    [CellOutput(**o) for o in c.get("outputs", [])],
                    c.get("metadata", {}))
                 for c in nb["cells"]]

        notebook = Notebook(nb_path.stem, filehash, cells)

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
        
    def locate_cell(self, *, 
                    cell_type=None, 
                    source=None, 
                    tag=None) -> tuple[int, NotebookCell] | None:
        assert cell_type or source or tag, "Must provide cell_type or keyword"

        hit_cell = None
        if source:
            pat = re.compile(source, re.IGNORECASE)
        else:
            pat = re.compile("")

        if tag:
            tag_pat = re.compile(tag, re.IGNORECASE)
        else:
            tag_pat = re.compile("")
        
        hit_cell = None
        for cidx, c in enumerate(self.cells):
            metadata_tags = ",".join(c.metadata.get("tags", []))

            if tag and tag_pat.search(metadata_tags) is None:
                continue            
            if cell_type and c.cell_type != cell_type:
                continue            
            if source and pat.search(c.source.lower()) is None:
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
        loc_cell = self.locate_cell(tag="indata")
        if loc_cell is None:
            loc_cell = self.locate_cell(cell_type="markdown", source="Data dependencies")

        # Do the actual processing    
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
        loc_cell = self.locate_cell(tag="outdata")
        if loc_cell is None:
            loc_cell = self.locate_cell(cell_type="markdown", source="Export Art[ie]facts?")
        
        # Do the actual processing
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

    def get_data_io(self):
        if self.locate_cell(tag=r"no[_\-. ]?in(puts?|data)") is not None:
            input_files = []
        else:
            input_files = self.input_files()
        
        if self.locate_cell(tag=r"no[_\-. ]?out(puts?|data)") is not None:
            output_files = []
        else:
            output_files = self.output_files()

        if input_files is None or output_files is None:                                
            io_agent = DataIOAgent()
            hash_cells = self.search("[a-z0-9]{40}")
            cell_rags = "\n".join(str(cell_x) for cell_x in hash_cells)
            io_resp = io_agent(cell_rags)
            try:
                io_resp = json.loads(io_resp)
            except json.JSONDecodeError:
                io_resp = {}

            if input_files is None:
              input_files = io_resp.get("inputs", [])
            
            if output_files is None:
              output_files = io_resp.get("outputs", [])

        return {"inputs": input_files, "outputs": output_files}

    def summarize(self, use_cache=True):
        nb_agent = NotebookAgent()        
        summary = nb_agent(self, use_cache=use_cache)
        return summary
    
    def get_yaml(self):
        cell = self.locate_cell(tag="yaml")
        if cell is not None:
            return cell[1].source
        return ""