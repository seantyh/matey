from pathlib import Path
from omegaconf import OmegaConf

def find_config_file():
  cwd = Path.cwd()
  prev_parent = None
  while True:
    config_file = cwd / "config.yaml"
    if config_file.exists():
      return config_file
    
    has_git_dir = (cwd / ".git").exists()
    prev_parent = cwd
    cwd = cwd.parent
    if cwd == prev_parent or has_git_dir:
      break

  home_config = Path.home() / ".matey/config.yaml"
  if home_config.exists():
    return home_config
  
  return None

_config = None

def set_config(**kwargs):
  global _config
  if _config is None:
    _config = get_config

  for k, v in kwargs.items():
    _config[k] = v # type: ignore

def get_config(verbose=False):
  global _config
  if _config is not None:
    return _config
  
  config_path = find_config_file()  
  if config_path:
    config = OmegaConf.load(config_path)
    if verbose:
      print(f"Loaded config from {config_path}")
  else:
    config = OmegaConf.create({"repo_id": "matey"})
  _config = config

  return _config

  