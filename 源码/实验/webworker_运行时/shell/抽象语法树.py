"""本 shell 所命名的已解析命令行。

`@yarnpkg/parsers` 仅从包根再导出其文法类型图的一部分，且其 `exports`
字段禁止直接触达文法模块，因此三个缺失成员从已发布者推导。
`CommandChain` 是 `Command` 加上可选的管道链接，因而可在期望命令节点处使用。

对齐上游 `webworker-runtime/src/shell/ast.ts`。公开面仅中文名。
"""
__all__=['命令','值参数类型','重定向参数类型']#仅中文公开名

# 再导出面：ArgumentSegment/ArithmeticExpression/CommandChain/CommandLine/ShellLine
# 由 @yarnpkg/parsers 提供；此处仅命名别名。
命令='CommandChain'#命令节点别名
值参数类型='argument'#值参数 type 字段
重定向参数类型='redirection'#重定向参数 type 字段
