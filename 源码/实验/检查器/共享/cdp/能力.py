"""每个检查器界域显式公布的操作支持。

对齐上游 `shared/cdp/capabilities.ts`。公开面仅中文名。
"""
__all__=[#仅中文公开名
    '运行时操作','控制台操作','源操作','调试器操作','检查器领域能力',
]#公开面结束

运行时操作=(#Runtime操作名
    'evaluate','get-properties','call-function','await-promise',#求值属性函数
    'release-object','release-object-group','global-lexical-scope-names',#释放与词法
)#运行时结束

控制台操作=('events','exceptions','clear')#Console操作名

源操作=('catalog','content','source-map')#源操作名

调试器操作=('breakpoint','pause','resume','step','call-frame')#调试器操作名

class 检查器领域能力:#界域能力
    """一个被检查界域的完整能力声明。"""
    def __init__(自身,运行时,控制台,源,调试器):#构造
        """保存四类操作列表。"""
        自身.runtime=tuple(运行时)#Runtime操作
        自身.console=tuple(控制台)#Console操作
        自身.sources=tuple(源)#源操作
        自身.debugger=tuple(调试器)#调试器操作
