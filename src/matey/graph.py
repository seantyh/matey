
def make_io_graph(io_data):
  import networkx as nx

  G = nx.DiGraph()
  for nb_key, io in io_data.items():
    indata = io["inputs"]
    outdata = io["outputs"]

    for in_file in indata:
      in_label = f"{in_file['sha1'][:6]}_{in_file['file_path']}"
      G.add_edge(in_label, nb_key)

    for out_file in outdata:
      out_label = f"{out_file['sha1'][:6]}_{out_file['file_path']}"
      G.add_edge(nb_key, out_label)
  
  return G
