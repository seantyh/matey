from google.cloud import firestore


db_client = None
def get_db():
    return firestore.Client()

def db_put(key, value, collection="matey"):
    global db_client
    if db_client is None:
        db_client = get_db()
    coll = db_client.collection(collection) 
    coll.document(key).set(value)

def db_get(key, collection="matey", return_ref=False):
    global db_client
    if db_client is None:
        db_client = get_db()
    coll = db_client.collection(collection) 
    docref = coll.document(key)    
    doc = docref.get()
    if doc.exists:
        return docref if return_ref else doc.to_dict()
    else:
        return None

def db_delete(key, collection="matey"):
    global db_client
    if db_client is None:
        db_client = get_db()
    coll = db_client.collection(collection) 
    return coll.document(key).delete()

def db_query(queries, collection="matey", return_dict=True):
    global db_client
    if db_client is None:
        db_client = get_db()
    coll = db_client.collection(collection) 
    docs = coll
    for query_x in queries:
        docs = docs.where(filter=firestore.FieldFilter(*query_x))
        
    docs = docs.stream()
    if return_dict:
        return [doc.to_dict() for doc in docs]
    else:
        return docs