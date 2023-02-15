import json

file = open('input.json', 'r', encoding='utf-8')
json_data = json.load(file)
file.close()
output = open('tmp-mail.txt', 'w', encoding='utf-8')
print(f"共有{len(json_data)}条数据")
for item in json_data:
    output.write(f"||{item}^\n")
output.close()
print("转换完成")