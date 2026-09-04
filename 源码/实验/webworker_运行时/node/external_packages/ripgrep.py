"""`@vscode/ripgrep` 桩。该包唯一导出是二进制路径，由搜索插件在模块作用域读取；
路径保持普通字符串以便构造成功，真正的大声失败来自 child_process 桩——
当有东西试图运行它时。

对齐上游 `webworker-runtime/src/node/external_packages/ripgrep.ts`。
"""
__all__=['rgPath','__esModule','default']#Node面

rgPath='/dsh/bin/rg'#假二进制路径；搜索插件本会 spawn
__esModule=True#CJS互操作

default={'rgPath':rgPath}#默认导出
