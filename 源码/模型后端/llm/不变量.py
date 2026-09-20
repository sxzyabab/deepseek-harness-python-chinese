"""校验 LLM 流协议块下标、增量与整段流。"""
import math
from .错误 import 装备错误

__all__=('包名','名称','依赖','校验下标','校验增量','校验流','安装','应用')

包名='@deepseek-ai/dsh-llm'
名称='llm-invariant'#配套不变量插件名（字面量不译）
依赖=['invariants']

def 校验下标(下标,失败):
    """要求块下标为非负安全整数。外来 JSON 入口。"""
    是整数=isinstance(下标,int) and not isinstance(下标,bool)#先排除 bool
    if not 是整数:#可能是整值浮点
        是整数=isinstance(下标,float) and math.isfinite(下标) and 下标==int(下标)
    if (not 是整数) or 下标<0 or abs(下标)>9007199254740991:
        失败('LLM stream block index must be a non-negative safe integer, got '+str(下标))

def 校验增量(打开,下标,期望,失败):
    """要求增量块指向已打开且类型匹配的块。"""
    校验下标(下标,失败)
    if 下标 not in 打开 or 打开[下标]!=期望:
        实际=打开[下标] if 下标 in 打开 else None
        失败(期望+' delta at index '+str(下标)+' requires an open '+期望+' block, got '+str(实际))

def 校验流(源,失败):
    """包装一条提供方流，在消费块时强制其语法。源是同步可迭代。"""
    打开={}
    已见用量=False
    已结束=False
    for 块 in 源:
        if 已结束:
            失败('LLM stream emitted '+块['type']+' after terminal finish')
        类型=块['type']
        if 类型=='block-start':
            校验下标(块['index'],失败)
            if 块['index'] in 打开:
                失败('LLM stream repeated block-start index '+str(块['index']))
            打开[块['index']]=块['blockType']
        elif 类型=='text-delta':
            校验增量(打开,块['index'],'text',失败)
        elif 类型=='reasoning-delta':
            校验增量(打开,块['index'],'reasoning',失败)
        elif 类型=='tool-call-delta':
            校验增量(打开,块['index'],'tool-call',失败)
        elif 类型=='block-end':
            校验下标(块['index'],失败)
            if 块['index'] not in 打开:
                失败('LLM stream block-end index '+str(块['index'])+' has no open block')
            块类型=打开[块['index']]
            if 块['block']['type']!=块类型:
                失败('LLM stream block-end index '+str(块['index'])+' closes '+块['block']['type']+', expected '+块类型)
            打开.pop(块['index'],None)
        elif 类型=='usage':
            if 已见用量:
                失败('LLM stream emitted usage more than once')
            已见用量=True
        elif 类型=='finish':
            原因种类=块['reason']['kind']
            if len(打开)>0 and 原因种类!='error' and 原因种类!='aborted':
                失败('LLM stream finished with '+str(len(打开))+' open block(s)')
            已结束=True
        yield 块
    if not 已结束:
        失败('LLM stream ended without a terminal finish chunk')

def 安装(上下文,失败):
    """给每条提供方流套上校验，并在适配器更新后核对注册表可读。"""
    def 包装流(选项,下一步):
        """在全局最前包装每条流。"""
        return 校验流(下一步(),失败)
    上下文.监听('llm/stream',包装流,{'全局':True,'前置':True})
    def 核对注册表():
        """适配器更新后核对注册表可读。"""
        运行时=上下文.获取服务('llm')
        if 运行时 is None:
            return
        for 提供方 in 运行时.列出提供方():
            try:
                运行时.提供方重试政策(提供方['id'])
            except 装备错误:
                失败('llm/adapters-updated fired while provider "'+提供方['id']+'" has no readable registration')
    上下文.监听('llm/adapters-updated',核对注册表,{'全局':True})

def 应用(上下文):
    """注册 LLM 不变量配套。"""
    return 上下文.invariants.register(包名,安装)

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
