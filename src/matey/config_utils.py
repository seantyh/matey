from pathlib import Path
from omegaconf import OmegaConf

def find_config_file():
  cwd = Path.cwd()
  prev_parent = None
  while True:
    config_file = cwd / "config.yaml"
    if config_file.exists():
      return config_file
    prev_parent = cwd
    cwd = cwd.parent
    if cwd == prev_parent:
      break
  return None

_config = None

def get_config():
  global _config
  if _config is not None:
    return _config
  
  config_path = find_config_file()  
  if config_path:
    config = OmegaConf.load(config_path)
    print(f"Loaded config from {config_path}")
  else:
    config = OmegaConf.create({"repo_id": "matey"})
  _config = config

  return _config

  