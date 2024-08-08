db_inst = None
chat_agent = None

def get_db():
    global db_inst
    if db_inst is None:
        from .doc_store import DocStore
        db_inst = DocStore()
    return db_inst

def get_chat_agent():
    global chat_agent
    if chat_agent is None:
        from .agent import ChatAgent
        chat_agent = ChatAgent()
    return chat_agent

def put(text):    
    db_inst = get_db()
    db_inst.put(text)

def ls():
    db_inst = get_db()
    db_inst.ls()

def load_nb(nb_path):
    from .notebook import Notebook
    return Notebook.load(nb_path)

def binder(nb_dir=None):
    from .nb_binder import NbBinder
    from pathlib import Path
    if nb_dir is None:
        nb_dir = Path.cwd()
    binder = NbBinder(nb_dir)
    binder.save()
    return binder

def recent_files(days=7):
    from .git_utils import recently_worked_on_files
    return recently_worked_on_files(days)

def chat(message):
    ca = get_chat_agent()
    return ca(message)

def chat_history():
    ca = get_chat_agent()
    return ca.history
