'检查活对象的 JSON，包括循环的 Location 存储'

import json
import weakref
from .格式 import 失败说明

__all__=['检查器json']

未定义=object()

class 检查器json写入器:
    '按祖先链标记循环，并把 Map/Set 收成对象或数组'
    def __init__(自身):
        '祖先栈和 Map/Set 的已渲染容器'
        自身._祖先=[]
        自身._容器={}
        自身._身份=[]

    def 写入(自身,值):
        '两空格缩进的 JSON；根为未定义时得到空串'
        if 值 is 未定义:
            return ''
        准备=自身._准备(值,object())
        if 准备 is 未定义:
            return ''
        return json.dumps(准备,indent=2,ensure_ascii=False)

    def _容器身份(自身,值):
        '同一 Map/Set 复用同一个容器对象'
        for 编号,已有 in enumerate(自身._身份):
            if 已有 is 值:
                return 自身._容器[编号]
        编号=len(自身._身份)
        自身._身份.append(值)
        if type(值).__name__ in ('Map','映射'):
            容器={}
            配对=值.items() if hasattr(值,'items') else 值
            for 键,项 in 配对:
                容器[str(键)]=项
        elif isinstance(值,(set,frozenset)) or type(值).__name__ in ('Set','集合'):
            容器=list(值)
        else:
            容器=值
        自身._容器[编号]=容器
        return 容器

    def _替换(自身,父,值):
        'bigint 变成带 n 的字符串；只有祖先才算循环'
        if type(值).__name__=='bigint':
            return f'{值}n'
        if 值 is None or isinstance(值,(str,int,float,bool)):
            return 值
        if callable(值):
            return 未定义
        while len(自身._祖先)>0 and 自身._祖先[-1] is not 父:
            自身._祖先.pop()
        渲染=值
        if type(值).__name__ in ('Map','映射','Set','集合') or isinstance(值,(set,frozenset)):
            渲染=自身._容器身份(值)
        for 祖先 in 自身._祖先:
            if 祖先 is 渲染:
                return '[Circular]'
        自身._祖先.append(渲染)
        return 渲染

    def _准备(自身,值,父):
        '先替换，再走进返回的对象或数组'
        替换=自身._替换(父,值)
        if 替换 is 未定义 or 替换 is None or isinstance(替换,(str,int,float,bool)):
            return 替换
        if isinstance(替换,list):
            return [None if 项 is 未定义 else 项 for 项 in (自身._准备(项,替换) for 项 in 替换)]
        if isinstance(替换,dict):
            输出={}
            for 键,项 in 替换.items():
                子=自身._准备(项,替换)
                if 子 is 未定义:
                    continue
                输出[str(键)]=子
            return 输出
        if isinstance(替换,tuple):
            return [自身._准备(项,替换) for 项 in 替换]
        return str(替换)

def 检查器json(值=未定义):
    '序列化原始详情；格式化失败不拆掉视图'
    try:
        return {'text':检查器json写入器().写入(值),'failed':False}
    except Exception as 错误:
        return {'text':失败说明(错误),'failed':True}
