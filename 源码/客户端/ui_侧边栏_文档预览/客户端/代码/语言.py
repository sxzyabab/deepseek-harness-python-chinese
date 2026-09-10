"""映射到共享 CodeBlock 已支持文法的文件后缀。

对齐上游 `ui-sidebar-documentpreview/src/client/code/languages.ts`。公开面仅中文名。
"""

__all__=['代码扩展名','路径语言']#仅中文公开名

_语言扩展={#文法 → 后缀
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
}#语言扩展结束

_后缀表={}#后缀 → 文法
for _语言,_扩展 in _语言扩展.items():#展开
    for _扩 in _扩展:#各后缀
        _后缀表[_扩]=_语言#挂上

代码扩展名=tuple(_后缀表.keys())#识别后缀


def 路径语言(路径):
    """为文件名选择共享高亮器的文法；其它后缀为 None。"""
    归一=路径.replace('\\','/')#归一
    点=归一.rfind('.')#末点
    斜=归一.rfind('/')#末斜
    if 点<0 or 点<斜:#无扩展
        return None#无
    扩展=归一[点+1:].lower()#后缀
    return _后缀表[扩展] if 扩展 in _后缀表 else None#文法
