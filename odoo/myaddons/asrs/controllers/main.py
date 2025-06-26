import requests
import json


headers = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Type": "application/json",
    "Origin": "http://127.0.0.1:8069",
    "Referer": "http://127.0.0.1:8069/odoo/action-680/1",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
cookies = {
    "frontend_lang": "en_US",
    "cids": "1",
    "session_id": "jCAn1cA7b02-zKN8E4InXGyWLSkONvwnROioeqput9pdn_xqTHzRHOvQJUh07Em1caXfUEOOXpS0QQPqdEUx"
}
url = "http://127.0.0.1:8069/web/dataset/call_kw/control.system.operate/web_save"
data = {
    "id": 5,
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "model": "control.system.operate",
        "method": "web_save",
        "args": [
            [
                1
            ],
            {
                "storage_location_number": 45
            }
        ],
        "kwargs": {
            "context": {
                "lang": "zh_CN",
                "tz": "Asia/Shanghai",
                "uid": 2,
                "allowed_company_ids": [
                    1
                ],
                "params": {
                    "resId": 1,
                    "action": 680,
                    "actionStack": [
                        {
                            "action": 680
                        },
                        {
                            "resId": 1,
                            "action": 680
                        }
                    ]
                }
            },
            "specification": {
                "status": {},
                "workshop": {},
                "line": {},
                "machine": {},
                "emergency_stop": {},
                "manual_control": {},
                "auto_control": {},
                "pack_number": {},
                "source_target": {},
                "new_target": {},
                "allow_outbound": {},
                "allow_return": {},
                "storage_goods_status": {},
                "storage_goods_cancel": {},
                "pc_start": {},
                "storage_pack_number": {},
                "storage_base_number": {},
                "storage_location_number": {},
                "storage_pack_barcode": {},
                "stacker_goods_status": {},
                "stacker_goods_cancel": {},
                "stacker_pack_number": {},
                "stacker_base_number": {},
                "stacker_location_number": {},
                "stacker_pack_barcode": {},
                "entrance1_goods_status": {},
                "entrance1_goods_cancel": {},
                "entrance1_pack_number": {},
                "entrance1_base_number": {},
                "entrance1_location_number": {},
                "entrance1_pack_barcode": {},
                "entrance2_goods_status": {},
                "entrance2_goods_cancel": {},
                "entrance2_pack_number": {},
                "entrance2_base_number": {},
                "entrance2_location_number": {},
                "entrance2_pack_barcode": {},
                "display_name": {}
            }
        }
    }
}
data = json.dumps(data, separators=(',', ':'))
response = requests.post(url, headers=headers, cookies=cookies, data=data)

print(response.text)
print(response)