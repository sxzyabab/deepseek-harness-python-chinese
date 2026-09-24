import re
from .markdown.高亮 import 高亮分行,语法加载计数

__all__=['代码高亮扩展名','路径语言','使用代码高亮器']

语言扩展名={
    'typescript':('ts','tsx','mts','cts'),
    'javascript':('js','jsx','mjs','cjs'),
    'shellscript':('sh','bash','zsh'),
    'json':('json','jsonc','jsonl','ndjson'),
    'python':('py','pyw','pyi'),
    'ruby':('rb','rake','gemspec'),
    'go':('go',),
    'rust':('rs',),
    'java':('java',),
    'c':('c','h'),
    'cpp':('cc','cpp','cxx','hh','hpp','hxx'),
    'csharp':('cs',),
    'kotlin':('kt','kts'),
    'swift':('swift',),
    'php':('php',),
    'yaml':('yaml','yml'),
    'toml':('toml',),
    'ini':('ini',),
    'markdown':('md','markdown'),
    'mdx':('mdx',),
    'html':('html','htm','xhtml'),
    'css':('css',),
    'scss':('scss',),
    'less':('less',),
    'sql':('sql',),
    'xml':('xml','xsd','xsl','xslt'),
    'lua':('lua',),
}

_扩展语言={}
for 语言,扩展表 in 语言扩展名.items():
    for 扩展 in 扩展表:
        _扩展语言[扩展]=语言

代码高亮扩展名=tuple(_扩展语言.keys())

_后缀=re.compile(r'\.([^./]+)\Z',re.ASCII)

def 路径语言(路径):
    """按文件名后缀选共享语法；未登记则 None。"""
    命中=_后缀.search(路径.replace('\\','/'))
    if 命中 is None:
        return None
    return _扩展语言.get(命中.group(1).lower())

def 使用代码高亮器(语言):
    """绑到一份语法；未就绪时高亮返回 None。"""
    语法加载计数()
    def 高亮(代码):
        return 高亮分行(代码,语言)
    return 高亮
