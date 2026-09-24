"""按 token 预算持留工具内容，文本可恢复、图像整块保留。执行后策略先于持留结算；规范程序值不动。缺少恢复存储或图像计价则留下原文并经日志报告原因。"""
import json
from ...依赖.schemastery import 数字字段
from .类型 import (
    溢出策略执行字段,
    溢出策略智能体字段,
    溢出策略会话字段,
    溢出策略会话头字段,
)
from .持留 import 持留内容
from .须知 import 格式化溢出须知,含溢出须知
from ...模型后端.token计数器.计价 import 计价内容
from ...模型后端.llm import 创建用户消息,解析图片附件访问

__all__=[
    '名称','依赖','配置模式','应用',
    '溢出策略执行字段','溢出策略智能体字段','溢出策略会话字段','溢出策略会话头字段',
    '溢出策略错误','持留内容','格式化溢出须知','含溢出须知',
]

名称='spill-policy'
依赖=['tools']
配置模式={'maxInlineTokens':数字字段()}
空隙={'type':'text','text':'\n\n[...]\n\n'}

class 溢出策略错误(Exception):
    """溢出策略加载或运行失败。"""
    def __init__(自身,消息):
        super().__init__(消息)

def 可持留(内容):
    """内容是否仅含可切文本与必须整块的图像。"""
    return all(块['type']=='text' or 块['type']=='image' for 块 in 内容)

def 应用(上下文,配置):
    """为已接受的工具结果与 PTC 日志副本挂 token 持留。"""
    if 'maxInlineTokens' not in 配置:
        return
    上限值=配置['maxInlineTokens']
    if isinstance(上限值,bool) or not isinstance(上限值,(int,float)) or 上限值!=int(上限值) or 上限值<0:
        raise 溢出策略错误('spill-policy: maxInlineTokens must be a non-negative integer (got '+str(上限值)+')')
    最大令牌=int(上限值)

    def 定价(执行,图像表):
        """给实际请求图像及其描述文本定价。"""
        成本表={}
        if len(图像表)>0:
            智能体=执行.agent
            路由=None
            if 智能体 is not None:
                头=智能体.session.requestHeader() if hasattr(智能体.session,'requestHeader') else None
                路由=None if 头 is None else (头.get('config') if isinstance(头,dict) else getattr(头,'config',None))
            提供方=None if 路由 is None else 路由.get('provider')
            if 提供方 is None and 智能体 is not None:
                提供方=智能体.options.get('provider') if isinstance(智能体.options,dict) else getattr(智能体.options,'provider',None)
            模型=None if 路由 is None else 路由.get('model')
            if 模型 is None and 智能体 is not None:
                模型=智能体.options.get('model') if isinstance(智能体.options,dict) else getattr(智能体.options,'model',None)
            llm=上下文.获取服务('llm',False)
            计算器=None if llm is None or 提供方 is None or 模型 is None else llm.图片请求定价(提供方,模型)
            if 计算器 is None:
                raise 溢出策略错误('the current model has no image token calculator')
            价格表=计算器.计价图片(图像表) if hasattr(计算器,'计价图片') else 计算器.priceImages(图像表)
            if len(价格表)!=len(图像表):
                raise 溢出策略错误('image token calculator returned an inconsistent occurrence count')
            下标=0
            for 图像 in 图像表:
                价格=价格表[下标]
                成本表[id(图像)]=价格['visualTokens']+计价内容([{'type':'text','text':价格['text']}])
                下标+=1
        def 一块(块):
            """一块可持留内容的价格。"""
            if 块['type']=='image':
                return 成本表[id(块)]
            return 计价内容([块])
        return 一块

    def 全文(内容):
        """按序全文，图像位置写入执行可读附件路径。"""
        段列表=[]
        for 块 in 内容:
            if 块['type']=='text':
                段列表.append(块['text'])
                continue
            附件=上下文.获取服务('attachments',False)
            文件系统=上下文.获取服务('fs',False)
            访问=None
            if 附件 is not None and 文件系统 is not None:
                映射=文件系统.processPathFromHostPath if hasattr(文件系统,'processPathFromHostPath') else 文件系统.从宿主路径到进程路径
                访问=解析图片附件访问(附件,映射,块['attachment'])
            if 访问 is None:
                raise 溢出策略错误('image '+str(块['attachment']['attachmentId'])+' has no readable attachment path')
            段列表.append('\n[Image: '+json.dumps(访问['readonlyPath'],ensure_ascii=False)+'; '+str(块['attachment']['mediaType'])+'; '+str(块['attachment']['width'])+'x'+str(块['attachment']['height'])+'. Use read_image to view it.]\n')
        return ''.join(段列表)

    def 约束(执行,内容,工具名,调用标识,标签):
        """可恢复地约束一份展示副本；失败则留下成功的工具内容。"""
        if not 可持留(内容):
            return None
        try:
            图像表=[块 for 块 in 内容 if 块['type']=='image']
            计价=定价(执行,图像表)
            合计=0
            for 块 in 内容:
                合计+=计价(块)
            if 合计<=最大令牌:
                return None
            所有者=None
            智能体=执行.agent
            if 智能体 is not None:
                头=智能体.session.header
                所有者=头['id'] if isinstance(头,dict) else getattr(头,'id',None)
            if 所有者 is None:
                raise 溢出策略错误('no session owner for '+工具名+' '+标签)
            溢出存储=上下文.获取服务('spillStore',False)
            if 溢出存储 is None:
                raise 溢出策略错误('no ctx.spillStore backend loaded')
            引用=溢出存储.保存文本({
                'owner':{'sessionId':所有者},
                'source':{'kind':'tool','toolName':工具名,'callId':调用标识,'label':标签},
                'suggestedName':工具名+'.txt',
                'content':全文(内容),
            })
            总字节=0
            for 块 in 内容:
                if 块['type']=='text':
                    总字节+=len(块['text'].encode('utf-8'))
            def 须知(字节数,计数):
                """须知文本块。"""
                return {'type':'text','text':格式化溢出须知({'kind':'exact','count':字节数},引用,计数)}
            最坏=须知(总字节,len(图像表))
            预留=计价(空隙)+计价({'type':'text','text':'\n\n'+最坏['text']})
            if 计价(最坏)>最大令牌:
                raise 溢出策略错误('spill notice for '+工具名+' exceeds maxInlineTokens')
            已持留=持留内容(内容,max(0,最大令牌-预留),计价)
            页脚=须知(已持留['omittedBytes'],已持留['omittedImages'])
            if len(已持留['head'])+len(已持留['tail'])==0:
                结果=[页脚]
            else:
                结果=list(已持留['head'])+[空隙]+list(已持留['tail'])+[{'type':'text','text':'\n\n'+页脚['text']}]
            合并=[]
            for 块 in 结果:
                if len(合并)>0 and 块['type']=='text' and 合并[-1]['type']=='text':
                    合并[-1]['text']+=块['text']
                elif 块['type']=='text':
                    合并.append(dict(块))
                else:
                    合并.append(块)
            return 合并
        except Exception as 错误:
            上下文.日志.警告('spill-policy: '+str(错误)+'; keeping the inline content')
            return None

    def 面向模型臂(执行,结果,下一步,*剩余):
        """先委托；约束已接受内容。"""
        _=剩余
        决策=下一步()
        if 决策['kind']!='accept' or 'value' in 决策 or 执行.name=='read':
            return 决策
        内容=决策['content'] if 'content' in 决策 else 结果['content']
        有图像=any(块['type']=='image' for 块 in 内容)
        if 执行.parent is not None and not 有图像:
            return 决策
        已持留=约束(执行,内容,执行.name,执行.callId,'result' if 执行.parent is None else 'dispatch')
        if 已持留 is None:
            return 决策
        附加=list(决策['additionalContexts']) if 'additionalContexts' in 决策 else []
        if 执行.parent is not None and not 结果.get('isError') and 有图像 and not any(块['type']=='image' for 块 in 已持留):
            附加.append(创建用户消息({'content':已持留,'source':{'kind':'ptc-mode'}}))
        接受={'kind':'accept','content':已持留}
        if len(附加)>0:
            接受['additionalContexts']=附加
        return 接受

    上下文.监听('tools/post-execute',面向模型臂,{'前置':True})

    def 派发日志臂(派发,下一步,*剩余):
        """约束 PTC 派发日志副本。"""
        _=剩余
        内容=下一步()
        return 约束(派发['exec'],内容,派发['name'],派发['subCallId'],'dispatch') or 内容

    上下文.监听('tools/ptc-dispatch-log',派发日志臂,{'前置':True})

name=名称
inject=依赖
Config=配置模式
apply=应用
default=应用
