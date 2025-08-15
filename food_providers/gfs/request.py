import requests

url = "https://order.gfs.com/api/v1/materials/543913/nutrition"

payload = {}
headers = {
  'accept': 'application/json, text/plain, */*',
  'accept-language': 'en-US,en;q=0.9',
  'dnt': '1',
  'priority': 'u=1, i',
  'referer': 'https://order.gfs.com/product/543913',
  'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"Linux"',
  'sec-fetch-dest': 'empty',
  'sec-fetch-mode': 'cors',
  'sec-fetch-site': 'same-origin',
  'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
  'Cookie': 'GCLB=CKLt1Mn576WjIRAD; EA_UID=c9727aed-fa47-4300-836b-b1e8350b7ae5; GOR=us-east1; XSRF-TOKEN=9c436546-d727-402c-8771-85017336959b; __Secure-GORDONORDERING2=MjNiN2MxNmItY2ZhMS00YWFiLTk2NzAtMjE1ZWMxNzJhNTA1; EA_SESSION_SAMPLED=true; EA_SID=8e945400-b985-4def-9ed6-7b1a527ea661; __Secure-GORDONORDERING2=M2E2NjZkYTAtZWU2MS00MmEzLWJjODktZDMwZjc4MDRmMDMz; GCLB=CJP2zOujmdCTqQEQAw; XSRF-TOKEN=c157d075-b971-4414-98e6-889f8db8fa92'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
