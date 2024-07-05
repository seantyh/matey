
# %%
import re
import json
import base64
import hashlib
from io import BytesIO, StringIO
from pathlib import Path
import nbformat
from PIL import Image
from dataclasses import dataclass

from .agent import DataIOAgent, SummaryAgent

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



def decode_image(b64_image:str):
    img_bytes = base64.b64decode(b64_image)
    img = Image.open(BytesIO(img_bytes))
    return img