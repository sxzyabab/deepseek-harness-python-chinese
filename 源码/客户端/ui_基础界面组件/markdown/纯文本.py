"""Markdown 到纯文本的投影，用于紧凑摘要与标签。

对齐上游 `ui-primitives/src/markdown/plain-text.ts`。公开面仅中文名。
mdast 节点与选项为 dict。
"""
from .解析 import 解析GFM#流式 GFM 解析

__all__=['抽取Markdown纯文本','内联文本','块文本']#仅中文公开名

def 节点值(节点):
    """value，缺则空串。"""
    return 节点['value'] if 'value' in 节点 and 节点['value'] is not None else ''#值

def 列出子节点(节点):
    """children，缺则空表。"""
    列=节点['children'] if 'children' in 节点 else None#子
    return 列 if 列 is not None else []#空则空表

def 内联文本(节点):
    """链接取标签、图片取 alt、代码取源。节点为 dict。"""
    类型=节点['type'] if 'type' in 节点 else None#类型
    if 类型 in ('text','inlineCode','code'):#字面
        return 节点值(节点)#值
    if 类型 in ('image','imageReference'):#图
        return 节点['alt'] if 'alt' in 节点 and 节点['alt'] is not None else ''#alt
    if 类型=='break':#硬换行
        return '\n'#换行
    if 类型=='html':#原始 HTML
        return 节点值(节点)#字面
    出=''#拼接
    for 子项 in 列出子节点(节点):#子
        出+=内联文本(子项)#拼
    return 出#拼接

def 压紧内联(文本):
    """连续空白→单空格，再 trim。"""
    出=[]#段
    空白=False#是否在空白
    for 字 in 文本:#逐字
        if 字.isspace():#空白（Unicode；原 TS 若走 \\s 则差 ASCII）
            空白=True#记
        else:#非空白
            if 空白 is True and len(出)>0:#需要空格；判 length
                出.append(' ')#单空格
            空白=False#清
            出.append(字)#字
    return ''.join(出).strip()#去首尾

def 块文本(节点):
    """块之间空行、列表项换行、表单元格制表符。"""
    类型=节点['type'] if 'type' in 节点 else None#类型
    子=列出子节点(节点)#子
    if 类型 in ('root','blockquote'):#根/引用
        段列表=[]#段
        for 子项 in 子:#子
            段=块文本(子项)#段
            if 段!='':#非空
                段列表.append(段)#入
        return '\n\n'.join(段列表)#空行
    if 类型 in ('paragraph','heading'):#段/标题
        return 压紧内联(内联文本(节点))#一行
    if 类型=='code':#围栏
        return 节点值(节点).strip()#去首尾
    if 类型=='list':#列表
        段列表=[]#段
        for 子项 in 子:#子
            段=块文本(子项)#段
            if 段!='':#非空
                段列表.append(段)#入
        return '\n'.join(段列表)#换行
    if 类型=='listItem':#列表项
        段列表=[]#段
        for 子项 in 子:#子
            段=块文本(子项)#段
            if 段!='':#非空
                段列表.append(段)#入
        return ' '.join(段列表)#空格
    if 类型=='table':#表
        段列表=[]#段
        for 子项 in 子:#子
            段=块文本(子项)#段
            if 段!='':#非空
                段列表.append(段)#入
        return '\n'.join(段列表)#行
    if 类型=='tableRow':#表行
        格=[]#格
        for 子项 in 子:#子
            格.append(块文本(子项))#格
        return '\t'.join(格)#制表
    if 类型=='tableCell':#单元格
        return 压紧内联(内联文本(节点))#一行
    if 类型=='html':#块 HTML
        return 节点值(节点)#字面
    if 类型 in ('thematicBreak','definition'):#分隔/定义
        return ''#无可见
    return 压紧内联(内联文本(节点))#当内联

def 找首段(节点):
    """深度优先找首个非空段落。"""
    if ('type' in 节点) and 节点['type']=='paragraph':#本节点段落
        文=压紧内联(内联文本(节点))#压紧
        if 文!='':#非空
            return 文#首段
    for 子 in 列出子节点(节点):#子树
        文=找首段(子)#递归
        if 文 is not None:#找到
            return 文#返回
    return None#没有

def 整篇文本(根):
    """去行首尾空白、连续空行压成一段、再 trim。"""
    行列表=[]#行
    for 行 in 块文本(根).split('\n'):#切
        行列表.append(行.strip())#去行空白
    拼='\n'.join(行列表)#拼回
    while '\n\n\n' in 拼:#连续空行
        拼=拼.replace('\n\n\n','\n\n')#压成一段
    return 拼.strip()#去首尾

def 抽取Markdown纯文本(源文,选项=None):
    """整篇、首条可见行、或首个语义段落。选项为 dict。"""
    选项=选项 if 选项 is not None else {}#选项
    模式=选项['mode'] if 'mode' in 选项 else 'all'#边界
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
