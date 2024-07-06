from collections import defaultdict
from litellm import completion, stream_chunk_builder

def chatgpt(message, state=[], return_raw=False, stream=False):  
  return completion_fn("gpt-4o", message, state, return_raw, stream)

def sonnet(message, state=[], return_raw=False, stream=False):  
  return completion_fn("claude-3-5-sonnet-20240620", message, state, return_raw, stream)
  
def haiku(message, state=[], return_raw=False, stream=False):  
  return completion_fn("claude-3-haiku-20240307", message, state, return_raw, stream)

def completion_fn(model_id, 
                  message, 
                  state=[], return_raw=False, stream=False):  
  messages = [*state,
              {"role": "user", "content": message}]

  resp = completion(
              model=model_id, 
              messages=messages, stream=stream)
  
  if stream:
    parts = []
    for part in resp:
      parts.append(part)
      print(part.choices[0].delta.content or "", end='') # type: ignore
  
    full_resp = stream_chunk_builder(parts, messages=messages)
  else:
    full_resp = resp

  if return_raw:
    return full_resp
  else:
    return full_resp["choices"][0]["message"]["content"]   # type: ignore

def llm(message, state=[], return_raw=False, stream=False):
  return haiku(message, state, return_raw, stream)

def init_usage_stat():
  return {"prompt": 0, "completion": 0}
class Session:
  def __init__(self, system_prompt=None):

    if system_prompt:
      self.states = [{"role": "system", "content": system_prompt}]
    else:
      self.states = []
    self.usage_stat = defaultdict(init_usage_stat)

  def add_usage(self, model_key, used_token):
    stat = self.usage_stat[model_key]
    stat["prompt"] += used_token.prompt_tokens
    stat["completion"] += used_token.completion_tokens

  def usage(self):
    return self.usage
  
  def __call__(self, message, 
               llm_func=llm, stream=False):
    
    chat_history = [
      {"role": x["role"], "content": x["content"]}  
      for x in self.states
    ]
    
    resp = llm_func(message, chat_history, return_raw=True, stream=stream)
    resp_text = resp["choices"][0]["message"]["content"]
    used_token = resp["usage"]
    self.add_usage(llm_func.__name__, used_token)

    self.states.append({"role": "user", "content": message})    
    self.states.append({"role": "assistant", "content": resp_text, "model": llm_func.__name__})
    return resp_text