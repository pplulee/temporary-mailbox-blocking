import json

import requests

block_url = "https://raw.githubusercontent.com/amieiro/disposable-email-domains/master/denyDomains.json"
allow_url = "https://raw.githubusercontent.com/amieiro/disposable-email-domains/master/allowDomains.json"
response = requests.get(block_url)
if response.status_code == 200:
    block_json_data = response.json()
else:
    print("获取封禁数据失败")
    exit()
response = requests.get(allow_url)
if response.status_code == 200:
    allow_json_data = response.json()
else:
    print("获取允许数据失败")
    exit()
block_manual = open('block_manual.json', 'r', encoding='utf-8')
block_manual_json_data = json.load(block_manual)
block_manual.close()
block_json_data.extend(block_manual_json_data)
output = open('rule.txt', 'w', encoding='utf-8')
print(f"共有{len(block_json_data)}条封禁数据")
print(f"共有{len(block_manual_json_data)}条手动封禁数据")
for item in block_json_data:
    if item != "" and "#" not in item:
        output.write(f"||{item}^\n")
print(f"共有{len(allow_json_data)}条允许数据")
for item in allow_json_data:
    if item != "" and "#" not in item:
        output.write(f"@@||{item}^\n")
output.close()
print("转换完成")
