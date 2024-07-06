import os

def jsonlink(url):
  import requests

  api_key = os.environ["JSONLINK_API_KEY"]

  params = {'url': url, 'api_key': api_key}
  response = requests.get('https://jsonlink.io/api/extract', params=params)

  if response.status_code == 200:
      data = response.json()
      return data
  else:
      print(f'Error: {response.status_code} - {response.text}')
      return None