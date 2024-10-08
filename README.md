<h3 align="center"><a href="README_zh_CN.md" style="text-decoration:none">中文文档</a> | English</h3>


# Temporary Email Domain Filtering Rules Project

This project aims to collect and process temporary email domains so that developers and website administrators can use
these rules to filter out registration and access requests from temporary emails.

# Why I need this program?

This program supports fetching rules from both an online URL and a local file, deduplicating them, and merging them
together. It also allows you to generate rules in multiple formats.

**Support for exporting files required by AdguardHome**

# How to use?

If nothing else, this project will be automatically updated once a day, based on the preset URL. This means you can
directly use the result file provided by us.

We provide a variety of formats, you just need to choose what you want.

# How to deploy it yourself?

If you want to deploy it yourself, it is not a difficult thing. Simply clone this repository and modify configuration.

Just add the URL or file that you wish to use, set the output file name, and then run `python3 generate.py` to generate
the file.

**Please note that the program can only recognize plain text format and does not support reading json**

# Contributing

If you want to add new rules, just modify `allow.txt` or `deny.txt` and submit a pull request.

If you have any suggestions or questions, please submit an issue.

# Source of rules

The rules preset by the program come from the following repositories:

- [amieiro/disposable-email-domains](https://github.com/amieiro/disposable-email-domains) 
