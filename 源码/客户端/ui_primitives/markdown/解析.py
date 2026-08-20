"""Markdown 渲染器的两套 mdast 文法入口。

对齐上游 `ui-primitives/src/markdown/parse.ts`。公开面仅中文名。
流式臂：GFM + CJK 友好加粗（不含数学，避免流式闪 KaTeX 错）。
定稿臂：流式臂 + 兼容 TeX 定界符 + 数学。
micromark 扩展原文见同目录 `CJK友好加粗.上游.ts` / `数学兼容.上游.ts`。
Python 侧经装载注入与上游同构的可调用体；未装载则抛错，从不静默降级。
"""

__all__=['解析GFM','解析GFM含数学','装载流式解析','装载定稿解析']#仅中文公开名

_流式解析=None#流式臂后端
_定稿解析=None#定稿臂后端

def 装载流式解析(函数):#注入流式臂
    """供宿主挂上 fromMarkdown(GFM+CJK) 或等价实现。"""
    global _流式解析#写
    _流式解析=函数#记

def 装载定稿解析(函数):#注入定稿臂
    """供宿主挂上 fromMarkdown(GFM+CJK+兼容定界符+数学) 或等价实现。"""
    global _定稿解析#写
    _定稿解析=函数#记

def 解析GFM(文本):#按流式臂文法解析
    """不含数学；不完整 TeX 不会在流式过程中闪错。"""
    if _流式解析 is None:#未装
        raise Exception('ui-primitives: parseGfm backend not loaded')#失败
    return _流式解析(文本)#解析

def 解析GFM含数学(文本):#按定稿臂文法解析
    """GFM + 兼容定界符 + TeX 数学。"""
    if _定稿解析 is None:#未装
        raise Exception('ui-primitives: parseGfmWithMath backend not loaded')#失败
    return _定稿解析(文本)#解析
