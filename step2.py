import requests

url = "https://image-upload-autohdr-j.s3-accelerate.amazonaws.com/83b93a60-aef6-409a-9f0d-7c1683c06e3f/raw/anh-dep-1.jpg?AWSAccessKeyId=AKIA4ZPZU4K2DBM7KGHU&Signature=%2Fxmc97Euc03G7aB70Xh88cSSrow%3D&content-type=application%2Foctet-stream&x-amz-acl=private&content-md5=&Expires=1775020016"

payload = "<file contents here>"
headers = {
  'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0',
  'Accept': '*/*',
  'Accept-Language': 'en-US,en;q=0.9',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Content-Type': 'application/octet-stream',
  'x-amz-acl': 'private',
  'Origin': 'https://www.autohdr.com',
  'Connection': 'keep-alive',
  'Referer': 'https://www.autohdr.com/',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'cross-site'
}

response = requests.request("PUT", url, headers=headers, data=payload)

print(response.text)

import requests

url = "https://image-upload-autohdr-j.s3-accelerate.amazonaws.com/83b93a60-aef6-409a-9f0d-7c1683c06e3f/raw/anh-dep-1.jpg?AWSAccessKeyId=AKIA4ZPZU4K2DBM7KGHU&Signature=%2Fxmc97Euc03G7aB70Xh88cSSrow%3D&content-type=application%2Foctet-stream&x-amz-acl=private&content-md5=&Expires=1775020016"

payload = {}
headers = {
  'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:148.0) Gecko/20100101 Firefox/148.0',
  'Accept': '*/*',
  'Accept-Language': 'en-US,en;q=0.9',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Access-Control-Request-Method': 'PUT',
  'Access-Control-Request-Headers': 'content-type,x-amz-acl',
  'Referer': 'https://www.autohdr.com/',
  'Origin': 'https://www.autohdr.com',
  'Connection': 'keep-alive',
  'Sec-Fetch-Dest': 'empty',
  'Sec-Fetch-Mode': 'cors',
  'Sec-Fetch-Site': 'cross-site',
  'Priority': 'u=4'
}

response = requests.request("OPTIONS", url, headers=headers, data=payload)

print(response.text)
