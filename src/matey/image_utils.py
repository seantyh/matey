
def get_image_base64(fpath):
  from PIL import Image, ImageGrab
  from io import BytesIO
  import base64

  if fpath == ":clipboard:":
    img = ImageGrab.grabclipboard()  
  else:
    img = Image.open(fpath)  

  if img is not None:
    img.thumbnail((1000, 1000))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode()
  else:
    return None
  
def get_clipboard_image():
  from PIL import ImageGrab
  img = ImageGrab.grabclipboard()  
  return img