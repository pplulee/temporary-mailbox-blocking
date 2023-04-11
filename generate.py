import json
import time

import requests

print("Start generating rules...\n\n")


def process_line(line):
    line = line.strip()
    if line == "" or "#" in line:
        return None
    else:
        return line


def get_rule_from_url(url):
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        print(f"Failed to get {url}")
        return None
    if response.status_code != 200:
        print(f"Failed to get {url}")
        return None
    else:
        print(f"Reading {url}...")
        return response.text.splitlines()


def get_rule_from_file(filename):
    try:
        file = open(filename, 'r', encoding='utf-8')
    except FileNotFoundError:
        print(f"{filename} not found")
        return None
    else:
        print(f"Reading {filename}...")
        result = file.read().splitlines()
        file.close()
        return result


def insert(line, dest):
    global allow_list
    global deny_list
    if dest not in ["allow", "deny"]:
        return False
    if line[0] in eval(f"{dest}_list").keys():
        if line not in eval(f"{dest}_list")[line[0]]:
            eval(f"{dest}_list")[line[0]].append(line)
            return True
        else:
            return False
    else:
        eval(f"{dest}_list")[line[0]] = [line]
        return True


start_time = time.time()
try:
    config_file = open('config.json', 'r', encoding='utf-8')
except FileNotFoundError:
    print("config.json not found")
    exit()
else:
    config = json.load(config_file)
    config_file.close()

allow_list = {}
deny_list = {}

for url in config["allowURL"]:
    result = get_rule_from_url(url)
    if result is not None:
        for line in result:
            c_line = process_line(line)
            if not c_line:
                continue
            if insert(process_line(line), "allow"):
                continue
            else:
                print(f"Duplicate: {line}\nFile: {url}")

for file in config['allowFile']:
    result = get_rule_from_file(file)
    if result is not None:
        for line in result:
            c_line = process_line(line)
            if not c_line:
                continue
            if insert(process_line(line), "allow"):
                continue
            else:
                print(f"Duplicate: {line}\nFile: {file}")

for url in config["denyURL"]:
    result = get_rule_from_url(url)
    if result is not None:
        for line in result:
            c_line = process_line(line)
            if not c_line:
                continue
            if insert(process_line(line), "deny"):
                continue
            else:
                print(f"Duplicate: {line}\nFile: {url}")

for file in config['denyFile']:
    result = get_rule_from_file(file)
    if result is not None:
        for line in result:
            c_line = process_line(line)
            if not c_line:
                continue
            if insert(process_line(line), "deny"):
                continue
            else:
                print(f"Duplicate: {line}\nFile: {file}")

# Migrate dict data to list
allow_data = []
allow_list_keys = sorted(allow_list.keys())
deny_data = []
deny_list_keys = sorted(deny_list.keys())

for key in allow_list_keys:
    c_list = allow_list[key]
    c_list.sort()
    allow_data.extend(c_list)
for key in deny_list_keys:
    c_list = deny_list[key]
    c_list.sort()
    deny_data.extend(c_list)
del allow_list
del deny_list

# Print stat
print(f"{len(allow_data)} allow rules")
print(f"{len(deny_data)} deny rules")

# Output to file

if "outputTXT" in config.keys():
    allow_file = open(config["outputTXT"]["allow"], 'w', encoding='utf-8')
    deny_file = open(config["outputTXT"]["deny"], 'w', encoding='utf-8')
    print(f"Output allow list to {config['outputTXT']['allow']}")
    print(f"Output deny list to {config['outputTXT']['deny']}")
    for line in allow_data:
        allow_file.write(line + '\n')
    for line in deny_data:
        deny_file.write(line + '\n')
    allow_file.close()
    deny_file.close()
if "outputJson" in config.keys():
    allow_file = open(config["outputJson"]["allow"], 'w', encoding='utf-8')
    deny_file = open(config["outputJson"]["deny"], 'w', encoding='utf-8')
    print(f"Output allow list to {config['outputJson']['allow']}")
    print(f"Output deny list to {config['outputJson']['deny']}")
    json.dump(allow_data, allow_file)
    json.dump(deny_data, deny_file)
    allow_file.close()
    deny_file.close()
if "outputAdGuard" in config.keys():
    output_file = open(config["outputAdGuard"], 'w', encoding='utf-8')
    print(f"Output AdGuard rules to {config['outputAdGuard']}")
    for line in allow_data:
        output_file.write(f"@@||{line}^\n")
    for line in deny_data:
        output_file.write(f"||{line}^\n")
    output_file.close()
end_time = time.time()
print("\n\nDone")
print(f"Time used: {end_time - start_time}s")
