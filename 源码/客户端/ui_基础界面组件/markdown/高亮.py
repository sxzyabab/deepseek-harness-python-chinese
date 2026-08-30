"""客户端语法高亮软面：别名表、惰性语法清单与订阅总线。

对齐上游 `ui-primitives/src/markdown/highlight.ts` 可 Python 化段。公开面仅中文名。
颜色只活在主题包 `--shiki-*`；本模块不写死色值。
实际分词由宿主 shiki/等价引擎经装载高亮器注入；未就绪语言返回 None（纯文本回退）。
"""

__all__=[#仅中文公开名
    '启动语法名','惰性语法名','语言别名','订阅语法已载','语法加载计数',
    '高亮成HTML','高亮分行','装载高亮器','确保语法',
]#公开面结束

启动语法名=('typescript','shellscript','json')#启动加载语法 id

惰性语法名=(#read 卡片扩展语法 id
    'python','ruby','go','rust','java','c','cpp','csharp','kotlin','swift',
    'php','yaml','toml','ini','markdown','mdx','html','css','scss','less','sql','xml','lua',
)#惰性结束

语言别名={#围栏/扩展名别名 → 语法 id
    'typescript':'typescript','ts':'typescript','tsx':'typescript',
    'javascript':'typescript','js':'typescript','jsx':'typescript',
    'shellscript':'shellscript','bash':'shellscript','sh':'shellscript',
    'shell':'shellscript','zsh':'shellscript',
    'json':'json','jsonc':'json',
    'py':'python','python':'python',
    'rb':'ruby','ruby':'ruby',
    'go':'go',
    'rs':'rust','rust':'rust',
    'java':'java','c':'c','cpp':'cpp',
    'cs':'csharp','csharp':'csharp',
    'kotlin':'kotlin','swift':'swift','php':'php',
    'yaml':'yaml','yml':'yaml','toml':'toml','ini':'ini',
    'md':'markdown','markdown':'markdown','mdx':'mdx',
    'html':'html','css':'css','scss':'scss','less':'less',
    'sql':'sql','xml':'xml','lua':'lua',
}#别名结束

_已请求=set()#已请求过的惰性语法 id
_监听们=set()#加载完成回调
_加载计数=0#惰性加载计数快照
_高亮成HTML=None#宿主 HTML 高亮
_高亮分行=None#宿主分行分词
_语法就绪=None#宿主：语法 id → 是否已注册
_请求惰性=None#宿主：发起惰性加载

def 装载高亮器(成HTML=None,分行=None,语法就绪=None,请求惰性=None):#注入宿主引擎
    """挂上实际分词实现；未挂则高亮接口返回 None。"""
    global _高亮成HTML,_高亮分行,_语法就绪,_请求惰性#写
    if 成HTML is not None:#有
        _高亮成HTML=成HTML#记
    if 分行 is not None:#有
        _高亮分行=分行#记
    if 语法就绪 is not None:#有
        _语法就绪=语法就绪#记
    if 请求惰性 is not None:#有
        _请求惰性=请求惰性#记

def 订阅语法已载(监听):#订阅惰性语法加载完成
    """返回取消订阅函数。"""
    _监听们.add(监听)#登记
    def 拆():#取消
        """移除。"""
        _监听们.discard(监听)#删
    return 拆#拆除器

def 语法加载计数():#useSyncExternalStore 快照
    """每次惰性加载递增。"""
    return _加载计数#计数

def 通知语法已载():#宿主加载完成后调用
    """递增快照并广播。"""
    global _加载计数#写
    _加载计数+=1#加
    for 听 in list(_监听们):#广播
        听()#回调

def 确保语法(已解析):#确保语法已注册或开始加载
    """启动语法始终就绪；惰性未载则请求一次并报未就绪。"""
    if 已解析 in 启动语法名:#启动
        return True#就绪
    if 已解析 not in 惰性语法名:#未知
        return True#无加载器路径由调用方判别名
    if _语法就绪 is not None and _语法就绪(已解析):#已注册
        return True#就绪
    if 已解析 not in _已请求:#尚未请求
        _已请求.add(已解析)#标记
        if _请求惰性 is not None:#有宿主
            _请求惰性(已解析,通知语法已载)#飞一次
    return False#本次未就绪

def 高亮成HTML(代码,语言):#高亮成 HTML
    """未知或尚未加载则 None。"""
    if 语言 is None:#缺
        return None#纯文本
    已解析=语言别名.get(str(语言).lower())#别名
    if 已解析 is None:#未知
        return None#纯文本
    if not 确保语法(已解析):#未就绪
        return None#回退
    if _高亮成HTML is None:#未装引擎
        return None#回退
    return _高亮成HTML(代码,已解析)#HTML

def 高亮分行(代码,语言):#按行分词成高亮 run
    """返回行→span 列表；未知或未加载则 None。"""
    if 语言 is None:#缺
        return None#纯文本
    已解析=语言别名.get(str(语言).lower())#别名
    if 已解析 is None:#未知
        return None#纯文本
    if not 确保语法(已解析):#未就绪
        return None#回退
    if _高亮分行 is None:#未装
        return None#回退
    return _高亮分行(代码,已解析)#分行
