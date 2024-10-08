# 临时邮箱域名过滤

这个项目旨在收集并处理临时邮箱域名，以便开发人员和网站管理员使用这些规则来过滤掉来自临时邮箱的注册和访问请求。

# 为什么需要这个程序？

这个程序支持从在线URL和本地文件获取规则，对规则进行去重，并支持生成多重格式的规则。

**支持导出AdguardHome规则**

# 如何使用？

如果您没有特殊的需求，您可以直接使用我们提供的结果文件。如果不出意外，这些文件会在每天更新。

我们提供了多种格式的规则文件，您可以根据自己的需求选择使用。

# 如何自行部署？

自行部署并不困难，只需要克隆这个仓库，`config.json`的示例在这里：

```json
{
  "allowFile": [
    "local_allow1.txt",
    "local_allow2.txt"
  ],
  "allowURL": [
    "https://raw.githubusercontent.com/amieiro/disposable-email-domains/master/allowDomains.txt"
  ],
  "denyFile": [
    "local_block1.txt",
    "local_block2.txt"
  ],
  "denyURL": [
    "https://raw.githubusercontent.com/amieiro/disposable-email-domains/master/denyDomains.txt"
  ],
  "outputTXT": {
    "allow": "allow.txt",
    "deny": "deny.txt"
  },
  "outputJson": {
    "allow": "allow.json",
    "deny": "deny.json"
  },
  "outputAdGuard": "adguard.txt"
}
```

您只需要添加需要使用的URL或文件，设置输出文件名，并运行`python3 generate.py` 即可生成规则文件。

如果您不需要某种输出格式，可以直接删除相应的部分。例如，如果您不需要生成Json输出，则可以删除整个`outputJson`部分。

同样，如果您不需要使用某些URL或文件，不添加即可。

**请注意，程序只能识别纯文本格式，并不支持读取Json格式文件。**

# 贡献

如果您想添加新的规则，请修改`allow.txt`或`deny.txt`并提交Pull Request。

如果您有任何建议或疑问，请提交Issue。

# 规则来源

程序预设的规则来自以下仓库：

- [amieiro/disposable-email-domains](https://github.com/amieiro/disposable-email-domains) 


