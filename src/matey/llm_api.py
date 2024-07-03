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
    return resp["choices"][0]["message"]["content"]   # type: ignore

def sonnet(message, state=[], return_raw=False):  
  messages = [*state,
              {"role": "user", "content": message}]
  resp = completion(
              model="claude-3-5-sonnet-20240620", 
              messages=messages)
  if return_raw:
    return resp
  else:
    return resp["choices"][0]["message"]["content"]   # type: ignore

def haiku(message, state=[], return_raw=False):  
  messages = [*state,
              {"role": "user", "content": message}]
  resp = completion(
              model="claude-3-haiku-20240307", 
              messages=messages)
  if return_raw:
    return resp
  else:
    return resp["choices"][0]["message"]["content"]   # type: ignore

def llm(message, state=[], return_raw=False):
  return haiku(message, state, return_raw)

def init_usage_stat():
  return {"prompt": 0, "competion": 0}
class Session:
  def __init__(self, system_prompt):
    if system_prompt:
      self.states = [{"role": "system", "content": system_prompt}]
    self.usage_stat = defaultdict(init_usage_stat)

  def add_usage(self, model_key, used_token):
    stat = self.usage_stat[model_key]
    stat["prompt"] += used_token.prompt_tokens
    stat["completion"] += used_token.completion_tokens

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