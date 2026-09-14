__all__=['基础界面错误','解析GFM','解析GFM含数学','装载流式解析','装载定稿解析']#仅中文公开名

class 基础界面错误(Exception):
    """本包异常基类。"""
    pass#无额外字段

_流式解析=None#流式臂后端
_定稿解析=None#定稿臂后端

def 装载流式解析(函数):
    """供宿主挂上 fromMarkdown(GFM+CJK) 或等价实现。"""
    global _流式解析#写
    _流式解析=函数#记

def 装载定稿解析(函数):
    """供宿主挂上 fromMarkdown(GFM+CJK+兼容定界符+数学) 或等价实现。"""
    global _定稿解析#写
    _定稿解析=函数#记

def 解析GFM(文本):
    """不含数学；不完整 TeX 不会在流式过程中闪错。"""
    if _流式解析 is None:#未装
        raise 基础界面错误('ui-primitives: parseGfm backend not loaded')#失败
    return _流式解析(文本)#解析

def 解析GFM含数学(文本):
    """GFM + 兼容定界符 + TeX 数学。"""
    if _定稿解析 is None:#未装
        raise 基础界面错误('ui-primitives: parseGfmWithMath backend not loaded')#失败
    return _定稿解析(文本)#解析
