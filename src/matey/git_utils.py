from dataclasses import dataclass
from datetime import datetime
import subprocess
import os

@dataclass
class Commit:
  hash: str
  date: datetime
  message: str

  def __repr__(self):
    return f"<Commit: {self.date} [{self.hash}] {self.message}>"

def get_git_commits():
  
  out = subprocess.run(["git", "log", '--pretty=%h,%ci,%s'], 
                       capture_output=True, text=True).stdout.strip()
  commits = []
  for ln_x in out.splitlines():        
    hash, date, message = ln_x.split(",", 2)
    date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S %z")
    commits.append(Commit(hash, date, message))
  return commits

def get_file_history(file_path):
  if not os.path.exists(file_path):
    raise FileNotFoundError(f"File not found: {file_path}")
  out = subprocess.run(["git", "log", '--pretty=%h,%ci,%s', '--follow', "--", file_path], 
                       capture_output=True, text=True).stdout.strip()
  commits = []
  for ln_x in out.splitlines():        
    hash, date, message = ln_x.split(",", 2)
    date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S %z")
    commits.append(Commit(hash, date, message))
  return commits

def recently_worked_on_files(days=7):
  out = subprocess.run(["git", "diff", '--name-only', f'@{{{days} days ago}}', 'HEAD'], 
                       capture_output=True, text=True).stdout.strip()
  files = out.splitlines()  
  return files