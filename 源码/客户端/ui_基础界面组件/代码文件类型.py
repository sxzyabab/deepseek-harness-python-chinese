
__all__=[#仅中文公开名
    '代码文件类型表',
    '是否代码文件类型',
    '是否链接代码扩展名',
    '分类代码文件类型',
]#公开面结束

代码文件类型表=(#代码文件类型元组
    'angular','c','clojure','cmake','cpp','csharp','css','dart','docker','elixir',
    'env','erlang','flutter','git','go','graphql','haskell','ini','java','javascript',
    'json','kotlin','lua','makefile','node','objective-c','perl','php','powershell',
    'protobuf','python','r','react','ruby','rust','scala','shell','solidity','sql',
    'svelte','swift','toml','typescript','vue','wasm','xml','yaml','zig',
)#类型表结束

_代码文件类型集=frozenset(代码文件类型表)#类型集合

_文件名类型={#整名 → 类型
    '.bash_profile':'shell','.bashrc':'shell','.env':'env',
    '.gitattributes':'git','.gitconfig':'git','.gitignore':'git','.gitmodules':'git',
    '.mailmap':'git','.profile':'shell','.zprofile':'shell','.zshrc':'shell',
    'bsdmakefile':'makefile','cmakelists.txt':'cmake','commit_editmsg':'git',
    'compose.yaml':'docker','compose.yml':'docker',
    'docker-compose.yaml':'docker','docker-compose.yml':'docker','dockerfile':'docker',
    'gemfile':'ruby','gnumakefile':'makefile','guardfile':'ruby','makefile':'makefile',
    'npm-shrinkwrap.json':'node','package-lock.json':'node','package.json':'node',
    'podfile':'ruby','rakefile':'ruby',
}#整名结束

_文件名前缀类型=(#前缀 → 类型
    ('dockerfile.','docker'),
    ('.env.','env'),
)#前缀结束

_文件名后缀类型=(#后缀 → 类型
    ('.component.ts','angular'),('.component.html','angular'),('.directive.ts','angular'),
    ('.service.ts','angular'),('.module.ts','angular'),('.pipe.ts','angular'),
    ('.guard.ts','angular'),('.interceptor.ts','angular'),('.dockerfile','docker'),
)#后缀结束

_扩展名类型={#扩展名 → 类型
    'bash':'shell','c':'c','c++':'cpp','cc':'cpp','cfg':'ini','cjs':'javascript',
    'clj':'clojure','cljc':'clojure','cljs':'clojure','cmake':'cmake','cpp':'cpp',
    'cs':'csharp','csh':'shell','css':'css','csx':'csharp','cts':'typescript','cxx':'cpp',
    'dart':'dart','dtd':'xml','edn':'clojure','env':'env','erl':'erlang','es6':'javascript',
    'escript':'erlang','ex':'elixir','exs':'elixir','fish':'shell','gemspec':'ruby',
    'go':'go','gql':'graphql','graphql':'graphql','h':'c','h++':'cpp','hh':'cpp',
    'hpp':'cpp','hrl':'erlang','hs':'haskell','hxx':'cpp','ini':'ini','ipp':'cpp',
    'java':'java','js':'javascript','json':'json','json5':'json','jsonc':'json',
    'jsx':'react','ksh':'shell','kt':'kotlin','kts':'kotlin','lhs':'haskell','lua':'lua',
    'm':'objective-c','mak':'makefile','mjs':'javascript','mk':'makefile','mm':'objective-c',
    'mts':'typescript','node':'node','pch':'objective-c','php':'php','php3':'php',
    'php4':'php','php5':'php','phps':'php','phtml':'php','pl':'perl','plist':'xml',
    'pm':'perl','pod':'perl','proto':'protobuf','ps1':'powershell','psd1':'powershell',
    'psm1':'powershell','py':'python','pyi':'python','pyw':'python','pyx':'python',
    'r':'r','rake':'ruby','rb':'ruby','rmd':'r','rs':'rust','sc':'scala','scala':'scala',
    'sh':'shell','sol':'solidity','sql':'sql','svelte':'svelte','swift':'swift','t':'perl',
    'tcsh':'shell','toml':'toml','tpp':'cpp','ts':'typescript','tsx':'react','vue':'vue',
    'wasm':'wasm','wast':'wasm','wat':'wasm','xml':'xml','xsd':'xml','xsl':'xml',
    'xslt':'xml','yaml':'yaml','yml':'yaml','zig':'zig','zsh':'shell',
}#扩展名结束

_链接代码扩展名=frozenset({#链接代码扩展名
    'ts','tsx','js','jsx','mjs','cjs','cts','mts','css','scss','sass','less','html','htm',
    'vue','svelte','astro','json','jsonc','json5','yaml','yml','toml','xml','ini','env',
    'sh','bash','zsh','fish','ps1','bat','cmd','py','pyi','rb','rs','go','java','kt','kts',
    'c','cc','cpp','cxx','h','hh','hpp','cs','php','swift','sql','csv','tsv','proto',
    'graphql','gql','lua','r','pl','scala','clj','cljs','ex','exs','erl','hs','dart',
})#链接扩展结束

def _路径末段(路径):#取路径末段
    """正斜杠或反斜杠分隔的末段。"""
    return 路径[max(路径.rfind('/'),路径.rfind('\\'))+1:]#末段

def 是否代码文件类型(类型):#是否细粒度代码类型
    """判定已解析文件类型是否使用全彩代码图标集。"""
    return 类型 in _代码文件类型集#集合判定

def 是否链接代码扩展名(扩展名):#是否链接代码扩展名
    """判定扩展名是否属于既有粗粒度链接代码类别。"""
    return 扩展名.lower() in _链接代码扩展名#小写后查表

def 分类代码文件类型(名,扩展名,上下文=None):#分类代码文件类型
    """按映射优先级解析最具体的代码/配置图标；传统分类器接管时返回 None。"""
    if 名 in _文件名类型:#整名优先
        return _文件名类型[名]#整名
    for 前缀,类型 in _文件名前缀类型:#前缀
        if 名.startswith(前缀):#命中
            return 类型#前缀类型
    for 后缀,类型 in _文件名后缀类型:#后缀
        if 名.endswith(后缀):#命中
            return 类型#后缀类型
    if 扩展名=='dart' and 上下文 is not None:#dart 上下文
        文件表=上下文['files'] if 'files' in 上下文 else {}#文件表
        规范=None#pubspec 文本
        for 路径,文本 in 文件表.items():#扫项目文件
            if _路径末段(路径).lower()=='pubspec.yaml':#命中
                规范=文本#记下
                break#结束
        if 规范 is not None and 'flutter:' in 规范:#含 flutter
            return 'flutter'#flutter
    if 扩展名 in _扩展名类型:#扩展名
        return _扩展名类型[扩展名]#类型
    return None#传统分类器接管
