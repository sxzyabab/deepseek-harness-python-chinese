"""本包拥有的 LLM 流协议不变量。

对齐上游 `llm/src/invariant.ts`。公开面仅中文名；配套插件名 `llm-invariant` 字面量不译。
"""
import math#有限数判定
from .错误 import 装备错误#注册表查找失败

__all__=('包名','名称','注入','校验下标','校验增量','校验流','安装','应用')#仅中文公开名

包名='@deepseek-ai/dsh-llm'#本包的不变量所有权名
名称='llm-invariant'#配套不变量插件名（字面量不译）
注入=['invariants']#依赖 invariants 服务

def 校验下标(下标,失败):
    """要求块下标为非负安全整数。外来 JSON 入口。"""
    是整数=isinstance(下标,int) and not isinstance(下标,bool)#先排除 bool
    if not 是整数:#可能是整值浮点
        是整数=isinstance(下标,float) and math.isfinite(下标) and 下标==int(下标)#整值浮点
    if (not 是整数) or 下标<0 or abs(下标)>9007199254740991:#下标非法
        失败('LLM stream block index must be a non-negative safe integer, got '+str(下标))#下标非法则失败

def 校验增量(打开,下标,期望,失败):
    """要求增量块指向已打开且类型匹配的块。"""
    校验下标(下标,失败)#先校验下标
    if 下标 not in 打开 or 打开[下标]!=期望:#类型不匹配
        实际=打开[下标] if 下标 in 打开 else None#取出该下标当前打开的类型
        失败(期望+' delta at index '+str(下标)+' requires an open '+期望+' block, got '+str(实际))#类型不匹配则失败

def 校验流(源,失败):
    """包装一条提供方流，在消费块时强制其语法。源是同步可迭代。"""
    打开={}#仍打开的块下标到类型
    已见用量=False#是否已见过 usage 块
    已结束=False#是否已见过终止 finish
    for 块 in 源:#逐块校验
        if 已结束:#终止后仍有块
            失败('LLM stream emitted '+块['type']+' after terminal finish')#终止 finish 之后仍有块则失败
        类型=块['type']#按块类型分派
        if 类型=='block-start':#块开始
            校验下标(块['index'],失败)#校验下标
            if 块['index'] in 打开:#同一下标重复开始
                失败('LLM stream repeated block-start index '+str(块['index']))#同一下标重复开始则失败
            打开[块['index']]=块['blockType']#记下该下标打开的类型
        elif 类型=='text-delta':#文本增量
            校验增量(打开,块['index'],'text',失败)#必须对准已打开的 text 块
        elif 类型=='reasoning-delta':#推理增量
            校验增量(打开,块['index'],'reasoning',失败)#必须对准已打开的 reasoning 块
        elif 类型=='tool-call-delta':#工具调用增量
            校验增量(打开,块['index'],'tool-call',失败)#必须对准已打开的 tool-call 块
        elif 类型=='block-end':#块结束
            校验下标(块['index'],失败)#校验下标
            if 块['index'] not in 打开:#没有对应打开块
                失败('LLM stream block-end index '+str(块['index'])+' has no open block')#没有对应打开块则失败
            块类型=打开[块['index']]#取出该下标打开的类型
            if 块['block']['type']!=块类型:#关闭类型不匹配
                失败('LLM stream block-end index '+str(块['index'])+' closes '+块['block']['type']+', expected '+块类型)#关闭类型不匹配则失败
            打开.pop(块['index'],None)#从打开表里去掉
        elif 类型=='usage':#用量
            if 已见用量:#用量块只能出现一次
                失败('LLM stream emitted usage more than once')#用量块只能出现一次
            已见用量=True#记下已见过 usage
        elif 类型=='finish':#终止
            原因种类=块['reason']['kind']#结束种类
            if len(打开)>0 and 原因种类!='error' and 原因种类!='aborted':#带着打开块结束
                失败('LLM stream finished with '+str(len(打开))+' open block(s)')#带着打开块结束则失败
            已结束=True#记下已终止
        yield 块#把通过校验的块交给下游
    if not 已结束:#没有终止 finish
        失败('LLM stream ended without a terminal finish chunk')#没有终止 finish 则失败

def 安装(上下文对象,失败):
    """给每条提供方流套上校验，并在适配器更新后核对注册表可读。"""
    def 包装流(选项,下一步):
        """在全局最前包装每条流。"""
        return 校验流(下一步(),失败)#校验后逐块让出
    上下文对象.监听('llm/stream',包装流,{'全局':True,'前置':True})#在全局最前包装每条流
    def 核对注册表():
        """适配器更新后核对注册表可读。"""
        运行时=上下文对象.获取服务('llm')#尝试取出仍在场的 llm 服务
        if 运行时 is None:#服务已拆除
            return#服务已拆除则不再断言
        for 提供方 in 运行时.列出提供方():#逐个已注册提供方
            try:#通知承诺注册表可读
                运行时.提供方重试政策(提供方['id'])#查找应成功
            except 装备错误:#注册表不可读
                失败('llm/adapters-updated fired while provider "'+提供方['id']+'" has no readable registration')#注册表不可读则失败
    上下文对象.监听('llm/adapters-updated',核对注册表,{'全局':True})#全局监听适配器更新

def 应用(上下文对象):
    """注册 LLM 不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
