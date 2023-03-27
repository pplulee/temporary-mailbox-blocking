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


start_time = time.time()
try:
    config_file = open('config.json', 'r', encoding='utf-8')
except FileNotFoundError:
    print("config.json not found")
    exit()
else:
    config = json.load(config_file)
    config_file.close()

allow_list = []
deny_list = []

for url in config["allowURL"]:
    result = get_rule_from_url(url)
    if result is not None:
        for line in result:
            line = process_line(line)
            if line and line not in allow_list:
                allow_list.append(line)

for file in config['allowFile']:
    result = get_rule_from_file(file)
    if result is not None:
        for line in result:
            line = process_line(line)
            if not line:
                continue
            if line not in allow_list:
                allow_list.append(line)
            else:
                print(f"Duplicate: {line}\nFile: {file}")

for url in config["denyURL"]:
    result = get_rule_from_url(url)
    if result is not None:
        for line in result:
            line = process_line(line)
            if line and line not in deny_list:
                deny_list.append(line)

for file in config['denyFile']:
    result = get_rule_from_file(file)
    if result is not None:
        for line in result:
            line = process_line(line)
            if not line:
                continue
            if line not in deny_list:
                deny_list.append(line)
            else:
                print(f"Duplicate: {line}\nFile: {file}")

# Sort
allow_list.sort()
deny_list.sort()

# Print stat
print(f"{len(allow_list)} allow rules")
print(f"{len(deny_list)} deny rules")

# Output to file

if "outputTXT" in config.keys():
    allow_file = open(config["outputTXT"]["allow"], 'w', encoding='utf-8')
    deny_file = open(config["outputTXT"]["deny"], 'w', encoding='utf-8')
    print(f"Output allow list to {config['outputTXT']['allow']}")
    print(f"Output deny list to {config['outputTXT']['deny']}")
    for line in allow_list:
        allow_file.write(line + '\n')
    for line in deny_list:
        deny_file.write(line + '\n')
    allow_file.close()
    deny_file.close()
if "outputJson" in config.keys():
    allow_file = open(config["outputJson"]["allow"], 'w', encoding='utf-8')
    deny_file = open(config["outputJson"]["deny"], 'w', encoding='utf-8')
    print(f"Output allow list to {config['outputJson']['allow']}")
    print(f"Output deny list to {config['outputJson']['deny']}")
    json.dump(allow_list, allow_file)
    json.dump(deny_list, deny_file)
    allow_file.close()
    deny_file.close()
if "outputAdGuard" in config.keys():
    output_file = open(config["outputAdGuard"], 'w', encoding='utf-8')
    print(f"Output AdGuard rules to {config['outputAdGuard']}")
    for line in allow_list:
        output_file.write(f"@@||{line}^\n")
    for line in deny_list:
        output_file.write(f"||{line}^\n")
    output_file.close()
end_time = time.time()
print("\n\nDone")
print(f"Time used: {end_time - start_time}s")
