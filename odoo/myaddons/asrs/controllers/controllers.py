import requests
import json


headers = {
    "Content-Type": "application/json"
}
url = "http://localhost:8069/asrs/pack_number"
data = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "record_id": 1
    },
    "id": 1
}
cookies = {
    "frontend_lang": "en_US",
    "cids": "1",
    "tz": "Asia/Shanghai",
    "session_id": "reLj1krc7sIQS5GEbYqHZ7Sz7rJzG9dkgID0oKgyGYi1DTgJ-zfh_6TdPpmNHTDe17Lme8HzpJ7DOHK4jQW8"
}
data = json.dumps(data, separators=(',', ':'))
response = requests.post(url, headers=headers, data=data, cookies=cookies).json()


print(response)