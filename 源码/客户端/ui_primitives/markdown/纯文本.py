"""Markdown 到纯文本的投影，用于紧凑摘要与标签。

对齐上游 `ui-primitives/src/markdown/plain-text.ts`。公开面仅中文名。
解析与渲染器共用流式 GFM 语法，因此投影剥掉的正是渲染器会画出的标记；
原始 HTML 保持字面量，链接保留标签，图片保留 alt，代码保留源文本。
"""
from .解析 import 解析GFM#流式 GFM 解析

__all__=['抽取Markdown纯文本','内联文本','块文本']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 内联文本(节点):#内联节点抽成纯文本
    """链接取标签、图片取 alt、代码取源。"""
    类型=取字段(节点,'type')#类型
    if 类型 in ('text','inlineCode','code'):#字面
        return 取字段(节点,'value') or ''#值
    if 类型 in ('image','imageReference'):#图
        return 取字段(节点,'alt') or ''#alt
    if 类型=='break':#硬换行
        return '\n'#换行
    if 类型=='html':#原始 HTML
        return 取字段(节点,'value') or ''#字面
    子=取字段(节点,'children') or []#子
    return ''.join(内联文本(子项) for 子项 in 子)#拼接

def 压紧内联(文本):#空白压成单空格并去首尾
    """连续空白→单空格，再 trim。"""
    出=[]#段
    空白=False#是否在空白
    for 字 in 文本:#逐字
        if 字.isspace():#空白
            空白=True#记
        else:#非空白
            if 空白 and 出:#需要空格
                出.append(' ')#单空格
            空白=False#清
            出.append(字)#字
    return ''.join(出).strip()#去首尾

def 块文本(节点):#块级节点抽成纯文本
    """块之间空行、列表项换行、表单元格制表符。"""
    类型=取字段(节点,'type')#类型
    子=取字段(节点,'children') or []#子
    if 类型 in ('root','blockquote'):#根/引用
        return '\n\n'.join(段 for 段 in (块文本(子项) for 子项 in 子) if 段)#空行
    if 类型 in ('paragraph','heading'):#段/标题
        return 压紧内联(内联文本(节点))#一行
    if 类型=='code':#围栏
        值=取字段(节点,'value') or ''#源
        return 值.strip()#去首尾
    if 类型=='list':#列表
        return '\n'.join(段 for 段 in (块文本(子项) for 子项 in 子) if 段)#换行
    if 类型=='listItem':#列表项
        return ' '.join(段 for 段 in (块文本(子项) for 子项 in 子) if 段)#空格
    if 类型=='table':#表
        return '\n'.join(段 for 段 in (块文本(子项) for 子项 in 子) if 段)#行
    if 类型=='tableRow':#表行
        return '\t'.join(块文本(子项) for 子项 in 子)#制表
    if 类型=='tableCell':#单元格
        return 压紧内联(内联文本(节点))#一行
    if 类型=='html':#块 HTML
        return 取字段(节点,'value') or ''#字面
    if 类型 in ('thematicBreak','definition'):#分隔/定义
        return ''#无可见
    return 压紧内联(内联文本(节点))#当内联

def 找首段(节点):#深度优先找首个非空段落
    """返回压紧文本或 None。"""
    if 取字段(节点,'type')=='paragraph':#本节点段落
        文=压紧内联(内联文本(节点))#压紧
        if 文!='':#非空
            return 文#首段
    for 子 in 取字段(节点,'children') or []:#子树
        文=找首段(子)#递归
        if 文 is not None:#找到
            return 文#返回
    return None#没有

def 整篇文本(根):#整篇纯文本
    """去行首尾空白、连续空行压成一段、再 trim。"""
    行们=[行.strip() for 行 in 块文本(根).split('\n')]#去行空白
    拼='\n'.join(行们)#拼回
    while '\n\n\n' in 拼:#连续空行
        拼=拼.replace('\n\n\n','\n\n')#压成一段
    return 拼.strip()#去首尾

def 抽取Markdown纯文本(源文,选项=None):#把 GFM 投影成纯文本
    """整篇、首条可见行、或首个语义段落。"""
    选项=选项 or {}#选项
    模式=选项.get('mode','all') if isinstance(选项,dict) else getattr(选项,'mode','all')#边界
    根=解析GFM(源文)#流式树
    全部=整篇文本(根)#整篇
    if 模式=='all':#整篇
        return 全部#完整
    if 模式=='first-line':#首行
        for 行 in 全部.split('\n'):#找非空
            if 行!='':#非空
                return 行#首行
        return ''#全空
    if 模式=='first-paragraph':#首段
        段=找首段(根)#段落
        if 段 is not None:#有
            return 段#段
        for 行 in 全部.split('\n'):#回退首行
            if 行!='':#非空
                return 行#行
        return ''#空
    return 全部#未知模式当整篇
