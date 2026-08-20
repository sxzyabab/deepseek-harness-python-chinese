"""TeX→视图树，复刻 rehype-katex 三臂错误链。

对齐上游 `ui-primitives/src/markdown/katex.tsx`。公开面仅中文名。
KaTeX 串行与 DOM 映射由宿主注入；未装载则抛错，从不静默降级。
"""

__all__=['渲染TeX到树','装载TeX渲染','样式对象']#仅中文公开名

_成串=None#宿主：TeX→HTML 字符串；(源文,展示模式,选项dict)→str
_HTML到树=None#宿主：HTML 字符串→子节点列表

def 装载TeX渲染(成串=None,HTML到树=None):#注入 KaTeX 与 DOM 映射
    """挂上 renderToString 与 DOMParser→树；两臂都要。"""
    global _成串,_HTML到树#写
    if 成串 is not None:#有
        _成串=成串#记
    if HTML到树 is not None:#有
        _HTML到树=HTML到树#记

def 样式对象(css文本):#内联 style 字符串→字典
    """KaTeX 只发 kebab-case；转 camelCase。"""
    样式={}#结果
    for 声明 in css文本.split(';'):#逐条
        冒号=声明.find(':')#分隔
        if 冒号==-1:#空
            continue#跳
        名=声明[:冒号].strip()#属性名
        键=''#camel
        跳大写=False#连字符后
        for 字 in 名:#逐字
            if 字=='-':#连字符
                跳大写=True#下字大写
            elif 跳大写:#转大写
                键+=字.upper()#大写
                跳大写=False#清
            else:#普通
                键+=字#追加
        样式[键]=声明[冒号+1:].strip()#值
    return 样式#样式字典

def 渲染TeX到树(源文,展示模式):#TeX→视图节点列表
    """三臂：严格→strict ignore→错误 span。"""
    if _成串 is None or _HTML到树 is None:#未装
        raise Exception('ui-primitives: katex backend not loaded')#失败
    首错=None#第一臂错误
    try:#严格
        html=_成串(源文,展示模式,{'throwOnError':True})#严格渲染
    except Exception as 错:#失败
        首错=错#记下
        try:#宽容
            html=_成串(源文,展示模式,{'strict':'ignore','throwOnError':False})#忽略严格
        except Exception:#内部错
            return [{#错误 span
                'type':'element','tag':'span',#元素
                'props':{#属性
                    'className':'katex-error',#类
                    'style':{'color':'#cc0000'},#色
                    'title':str(首错),#题注
                },#属性结束
                'children':[源文],#原文
            }]#列表
    return _HTML到树(html)#DOM→树
