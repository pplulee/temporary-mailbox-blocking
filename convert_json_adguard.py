import json
import time

file = open('input.json', 'r', encoding='utf-8')
json_data = json.load(file)
file.close()
output = open('tmp-mail.txt', 'w', encoding='utf-8')
print(f"共有{len(json_data)}条数据")

domain_cache = []
domain_list = []
special_domain = []


class Domain:
    def __init__(self, name, suffix):
        self.name = name
        self.suffix = suffix

    def set_wildcard_suffix(self):
        self.suffix = "*"


start_time = time.time()
for item in json_data:
    if item.count('.') == 1:
        domain, suffix = item.split('.')
        if domain not in domain_cache:
            domain_cache.append(domain)
            domain_list.append(Domain(domain, suffix))
        else:
            domain_list[domain_cache.index(domain)].set_wildcard_suffix()
    else:
        # 特殊域名，跳过
        special_domain.append(item)
end_time = time.time()
print(f"处理完成，耗时{end_time - start_time}秒")
for item in domain_list:
    output.write(f"||{item.name}.{item.suffix}^\n")
for item in special_domain:
    output.write(f"||{item}^\n")
output.close()
print("转换完成")
