from pathlib import Path
from .llm_api import Session

class Agent:
  def __init__(self):
    system_prompt = (Path(__file__).parent / "prompts/system_prompt.txt").read_text()
    self.session = Session(system_prompt)

  def __call__(self, message):
    return self.session(message)