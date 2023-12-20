import json
import threading
import time

import requests


def process_line(line):
    line = line.strip()
    if line == "" or "#" in line:
        return None
    else:
        return line


def get_rule_from_url(session, url):
    try:
        response = session.get(url)
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
        with open(filename, 'r', encoding='utf-8') as file:
            print(f"Reading {filename}...")
            return file.read().splitlines()
    except FileNotFoundError:
        print(f"{filename} not found")
        return None


def process_rule_source(session, source, rule_type, lists):
    if source.startswith('http'):
        result = get_rule_from_url(session, source)
    else:
        result = get_rule_from_file(source)
    if result is not None:
        for line in result:
            c_line = process_line(line)
            if c_line:
                lists[rule_type].add(c_line)


def process_rules(session, rule_sources, rule_type, lists):
    threads = []
    for source in rule_sources:
        thread = threading.Thread(target=process_rule_source, args=(session, source, rule_type, lists))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    print("Start generating rules...\n\n")
    start_time = time.time()
    try:
        with open('config.json', 'r', encoding='utf-8') as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        print("config.json not found")
        exit()

    allow_list = set()
    deny_list = set()
    lists = {"allow": allow_list, "deny": deny_list}

    session = requests.Session()

    process_rules(session, config["allowURL"] + config["allowFile"], "allow", lists)
    process_rules(session, config["denyURL"] + config["denyFile"], "deny", lists)

    # Print stat
    print(f"{len(allow_list)} allow rules")
    print(f"{len(deny_list)} deny rules")

    # Output to file
    if "outputTXT" in config.keys():
        with open(config["outputTXT"]["allow"], 'w', encoding='utf-8') as allow_file, \
                open(config["outputTXT"]["deny"], 'w', encoding='utf-8') as deny_file:
            print(f"Output allow list to {config['outputTXT']['allow']}")
            print(f"Output deny list to {config['outputTXT']['deny']}")
            for line in allow_list:
                allow_file.write(line + '\n')
            for line in deny_list:
                deny_file.write(line + '\n')

    if "outputJson" in config.keys():
        with open(config["outputJson"]["allow"], 'w', encoding='utf-8') as allow_file, \
                open(config["outputJson"]["deny"], 'w', encoding='utf-8') as deny_file:
            print(f"Output allow list to {config['outputJson']['allow']}")
            print(f"Output deny list to {config['outputJson']['deny']}")
            json.dump(list(allow_list), allow_file)
            json.dump(list(deny_list), deny_file)

    if "outputAdGuard" in config.keys():
        with open(config["outputAdGuard"], 'w', encoding='utf-8') as output_file:
            print(f"Output AdGuard rules to {config['outputAdGuard']}")
            for line in allow_list:
                output_file.write(f"@@||{line}^\n")
            for line in deny_list:
                output_file.write(f"||{line}^\n")

    end_time = time.time()
    print("\n\nDone")
    print(f"Time used: {end_time - start_time}s")
