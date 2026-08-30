"""shell / agent-loop / web-search 三张出厂卡片控制器。

对齐上游 bash/agent-loop/web-search-card-controller.ts。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
from .卡片表单 import 卡片表单,数字字段,文本字段#表单

__all__=[#仅中文公开名
    '终端命名空间','智能体循环命名空间','网页搜索命名空间',
    '终端卡片控制器','智能体循环卡片控制器','网页搜索卡片控制器',
]#公开面结束

终端命名空间='shell'#shell 命名空间字面量
智能体循环命名空间='agent-loop'#agent-loop 命名空间
网页搜索命名空间='web-search-deepseek'#DeepSeek 搜索命名空间
默认密钥引用='DEEPSEEK_API_KEY'#默认凭证引用
密钥字段='apiKey'#凭证暂存字段名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

class 终端卡片控制器:#bash 卡片暂存表单
    """把 bash 作用域接到 shell 卡片。"""
    def __init__(自身,作用域):#绑定 bash 命名空间
        """数字字段：超时与每路输出上限。"""
        自身.表单=卡片表单(作用域,[数字字段('timeoutMs'),数字字段('maxOutputBytes')])#表单
        自身.store=自身.表单.bind(自身.投影)#投影仓库

    def 投影(自身):#卡片渲染状态
        """外壳加两字段。"""
        壳=自身.表单.shell()#外壳
        return {**壳,'timeoutMs':自身.表单.field('timeoutMs'),'maxOutputBytes':自身.表单.field('maxOutputBytes')}#投影

    def inject(自身):#槽位注入面孔
        """快照钩子并摊开表单动作。"""
        return {'hooks':{'bashCard':自身.store},**自身.表单.actions()}#面孔

class 智能体循环卡片控制器:#agent-loop 卡片暂存表单
    """把 agent-loop 作用域接到卡片。"""
    def __init__(自身,作用域):#绑定命名空间
        """并行工具调用上限。"""
        自身.表单=卡片表单(作用域,[数字字段('maxParallelToolCalls')])#表单
        自身.store=自身.表单.bind(自身.投影)#投影仓库

    def 投影(自身):#卡片渲染状态
        """外壳加并行上限。"""
        return {**自身.表单.shell(),'maxParallelToolCalls':自身.表单.field('maxParallelToolCalls')}#投影

    def inject(自身):#槽位注入面孔
        """快照钩子并摊开表单动作。"""
        return {'hooks':{'agentLoopCard':自身.store},**自身.表单.actions()}#面孔

def 引用于(快照):#分区点名或默认引用
    """有非空 apiKeyEnv 则用，否则默认。"""
    值=取字段(快照,'value')#有效层
    声明=取字段(值,'apiKeyEnv') if isinstance(值,dict) else None#声明
    return 声明 if isinstance(声明,str) and len(声明)>0 else 默认密钥引用#引用

class 网页搜索卡片控制器:#web-search 卡片
    """作用域与凭证域接到卡片。"""
    def __init__(自身,作用域,接口):#绑定命名空间与凭证线面
        """端点、次数上限与凭证。"""
        自身.作用域=作用域#作用域
        自身.接口=接口#credentials 面
        自身.凭证={'ref':'','configured':False,'writable':True}#最近凭证报告
        自身.表单=卡片表单(作用域,[文本字段('baseURL'),数字字段('maxUses')],[{'field':密钥字段,'write':自身.写密钥}])#表单
        自身.store=自身.表单.bind(自身.投影)#投影
        作用域.subscribe(lambda:自身.读凭证())#作用域变化重读
        自身.读凭证()#构造时读一次

    def 投影(自身):#卡片渲染状态
        """外壳加字段与凭证徽章。"""
        return {#投影
            **自身.表单.shell(),#外壳
            'baseURL':自身.表单.field('baseURL'),#端点
            'maxUses':自身.表单.field('maxUses'),#次数
            'apiKey':自身.表单.field(密钥字段),#暂存密钥
            'apiKeyConfigured':自身.凭证['configured'],#已配置
            'apiKeyWritable':自身.凭证['writable'],#可写
        }#投影结束

    def 读凭证(自身):#向凭证域询问当前引用
        """过期引用答案丢弃。"""
        引用=引用于(自身.作用域.getSnapshot())#当前引用
        if 引用!=自身.凭证['ref']:#引用已换
            自身.凭证={'ref':引用,'configured':False,'writable':True}#清空
            自身.store.set(自身.投影())#立刻投影
        try:#describe
            应答=解开(自身.接口.credentials.describe({'refs':[引用]}))#描述
        except Exception:#读取失败不让卡片不可用
            return#保留上次
        结果=取字段(应答,'result')#业务结果
        if not 取字段(结果,'ok') or 引用!=引用于(自身.作用域.getSnapshot()):#失败或引用已变
            return#丢弃
        视图=取字段(取字段(结果,'value'),'credentials') or {}#凭证图
        项=视图.get(引用) if isinstance(视图,dict) else 取字段(视图,引用)#该项
        下一={'ref':引用,'configured':bool(取字段(项,'configured',False)),'writable':bool(取字段(项,'writable',True))}#新状态
        if 下一['configured']==自身.凭证['configured'] and 下一['writable']==自身.凭证['writable']:#无变化
            return#不投影
        自身.凭证=下一#采纳
        自身.store.set(自身.投影())#发布

    def refreshCredential(自身,引用):#Host 报告监视引用有变时重读
        """不是本卡片监视的引用则忽略。"""
        if 引用!=自身.凭证['ref']:#无关
            return#忽略
        自身.读凭证()#重问

    def inject(自身):#槽位注入面孔
        """快照钩子并摊开表单动作。"""
        return {'hooks':{'webSearchCard':自身.store},**自身.表单.actions()}#面孔

    def 写密钥(自身,值):#写出暂存密钥并重读
        """Host 是密钥是否存在的唯一权威。"""
        try:#set
            解开(自身.接口.credentials.set({'ref':引用于(自身.作用域.getSnapshot()),'value':值}))#写入
        except Exception:#拒绝经重读浮出
            pass#重读
        自身.读凭证()#重问
        return 自身.凭证['configured']#是否已配置
