from collections import defaultdict
from litellm import completion

def chatgpt(message, state=[], return_raw=False):  
  messages = [*state,
              {"role": "user", "content": message}]
  resp = completion(
              model="gpt-4o", 
              messages=messages)
  if return_raw:
    return resp
  else:
    return resp["choices"][0]["message"]["content"]

def sonnet(message, state=[], return_raw=False):  
  messages = [*state,
              {"role": "user", "content": message}]
  resp = completion(
              model="claude-3-5-sonnet-20240620", 
              messages=messages)
  if return_raw:
    return resp
  else:
    return resp["choices"][0]["message"]["content"]

def haiku(message, state=[], return_raw=False):  
  messages = [*state,
              {"role": "user", "content": message}]
  resp = completion(
              model="claude-3-haiku-20240307", 
              messages=messages)
  if return_raw:
    return resp
  else:
    return resp["choices"][0]["message"]["content"]

def llm(message, state=[]):
  return haiku(message, state)

class Session:
  def __init__(self):
    self.states = []
    self.usage_stat = defaultdict(lambda: {"prompt": 0, "completion": 0})

  def add_usage(self, model_key, used_token):
    stat = self.usage_stat[model_key]
    stat["prompt"] += used_token.get("prompt", 0)
    stat["completion"] += used_token.get("completion", 0)

  def usage(self):
    return self.usage
  
  def __call__(self, message, llm_func=llm):
    chat_history = [
      {"role": x["role"], "content": x["content"]}  
      for x in self.states
    ]
    resp = llm_func(message, chat_history, return_raw=True)
    resp_text = resp["choices"][0]["message"]["content"]
    used_token = resp["usage"]
    self.add_usage(llm_func.__name__, used_token)

    self.states.append({"role": "user", "content": message})    
    self.states.append({"role": "assistant", "content": resp_text, "model": llm_func.__name__})
    return resp_text