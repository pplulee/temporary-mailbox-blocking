import json

block_file = open('block.json', 'r', encoding='utf-8')
block_json_data = json.load(block_file)
block_file.close()
output = open('rule.txt', 'w', encoding='utf-8')
print(f"共有{len(block_json_data)}条封禁数据")
for item in block_json_data:
    if item!="" and "#" not in item:
        output.write(f"||{item}^\n")

allow_file = open('allow.json', 'r', encoding='utf-8')
allow_json_data = json.load(allow_file)
allow_file.close()
print(f"共有{len(allow_json_data)}条允许数据")
for item in allow_json_data:
    if item!="" and "#" not in item:
        output.write(f"@@||{item}^\n")
output.close()
print("转换完成")