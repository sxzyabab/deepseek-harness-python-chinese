"""Client 代码界面与 Host read 卡片共享的扩展名→语法高亮语言表。"""
__all__=[
    '代码高亮扩展名列表',
    '按路径解析语言',
    '按路径解析读取语言提示',
]

#常量：规范化语言 id → 不含点的小写扩展名；id 是 grammar 名而非展示名
语言扩展名表={
    'typescript':('ts','tsx','mts','cts'),
    'javascript':('js','jsx','mjs','cjs'),
    'shellscript':('sh','bash','zsh'),
    'fish':('fish',),
    'json':('json','jsonc','jsonl','ndjson','ipynb'),
    'csv':('csv',),
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
    'ini':('ini','conf','cfg','properties'),
    'dotenv':('env',),
    'log':('log',),
    'diff':('diff','patch'),
    'http':('http',),
    'markdown':('md','markdown'),
    'mdx':('mdx',),
    'rst':('rst',),
    'latex':('tex','sty','cls'),
    'bibtex':('bib',),
    'asciidoc':('adoc',),
    'html':('html','htm','xhtml'),
    'css':('css',),
    'scss':('scss',),
    'less':('less',),
    'sql':('sql',),
    'xml':('xml','xsd','xsl','xslt','plist','svg'),
    'lua':('lua',),
    'bat':('bat','cmd'),
    'powershell':('ps1','psm1','psd1'),
    'r':('r',),
    'julia':('jl',),
    'dart':('dart',),
    'scala':('scala',),
    'clojure':('clj','cljs','edn'),
    'erlang':('erl','hrl'),
    'elixir':('ex','exs'),
    'haskell':('hs',),
    'fsharp':('fs','fsi','fsx'),
    'vb':('vb',),
    'perl':('pl','pm'),
    'verilog':('v',),
    'system-verilog':('sv','svh'),
    'graphql':('graphql','gql'),
    'proto':('proto',),
    'hcl':('tf','tfvars','hcl'),
    'nix':('nix',),
    'vue':('vue',),
    'svelte':('svelte',),
    'make':('makefile','mk'),
    'cmake':('cmake',),
    'groovy':('gradle','groovy'),
}

#扩展名→语言；显式键表，避免把 constructor 一类后缀当成内建属性
扩展名到语言={}
for 语言,扩展名列表 in 语言扩展名表.items():
    for 扩展名 in 扩展名列表:
        扩展名到语言[扩展名]=语言

代码高亮扩展名列表=tuple(扩展名到语言.keys())

#后缀自名比语言短名更适合持久化时的覆盖（tsx/tf/gradle 等）
按扩展名的读取语言={
    'tsx':'tsx','jsx':'jsx',
    'tf':'tf','tfvars':'tfvars','gradle':'gradle',
}

#规范语言 id → Host read 卡片短名；与上表互补
语言短名表={
    'typescript':'ts',
    'javascript':'js',
    'shellscript':'sh',
    'fish':'fish',
    'json':'json',
    'csv':'csv',
    'python':'py',
    'ruby':'rb',
    'go':'go',
    'rust':'rs',
    'java':'java',
    'c':'c',
    'cpp':'cpp',
    'csharp':'cs',
    'kotlin':'kotlin',
    'swift':'swift',
    'php':'php',
    'yaml':'yaml',
    'toml':'toml',
    'ini':'ini',
    'dotenv':'env',
    'log':'log',
    'diff':'diff',
    'http':'http',
    'markdown':'md',
    'mdx':'mdx',
    'rst':'rst',
    'latex':'tex',
    'bibtex':'bib',
    'asciidoc':'adoc',
    'html':'html',
    'css':'css',
    'scss':'scss',
    'less':'less',
    'sql':'sql',
    'xml':'xml',
    'lua':'lua',
    'bat':'bat',
    'powershell':'ps1',
    'r':'r',
    'julia':'jl',
    'dart':'dart',
    'scala':'scala',
    'clojure':'clj',
    'erlang':'erl',
    'elixir':'ex',
    'haskell':'hs',
    'fsharp':'fs',
    'vb':'vb',
    'perl':'pl',
    'verilog':'v',
    'system-verilog':'sv',
    'graphql':'graphql',
    'proto':'proto',
    'hcl':'hcl',
    'nix':'nix',
    'vue':'vue',
    'svelte':'svelte',
    'make':'make',
    'cmake':'cmake',
    'groovy':'groovy',
}

def 取路径扩展名(路径):
    """取最后路径段最后一个点之后的小写扩展名；无点则返回 None。"""
    斜杠=max(路径.rfind('/'),路径.rfind('\\'))
    基名=路径[斜杠+1:]
    点=基名.rfind('.')
    if 点<0:
        return None
    return 基名[点+1:].lower()

def 按路径解析语言(路径):
    """按文件名或路径解析规范化语法高亮语言 id；未识别返回 None。"""
    扩展名=取路径扩展名(路径)
    if 扩展名 is None:
        return None
    return 扩展名到语言.get(扩展名)

def 按路径解析读取语言提示(路径):
    """Host read 卡片持久化的短 lang；未识别返回 None。"""
    扩展名=取路径扩展名(路径)
    if 扩展名 is None:
        return None
    规范=扩展名到语言.get(扩展名)
    if 规范 is None:
        return None
    if 扩展名 in 按扩展名的读取语言:
        return 按扩展名的读取语言[扩展名]
    return 语言短名表[规范]
