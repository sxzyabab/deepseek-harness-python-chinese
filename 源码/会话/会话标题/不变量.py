"""向 invariants 登记本包；无独立运行时检查。"""
包名='@deepseek-ai/dsh-session-title'
名称='session-title-invariant'
依赖=['invariants','sessions']

__all__=['包名','名称','依赖','应用','默认']

def 安装(子上下文=None,失败=None):
    """校验 session/title 的 messageSeqs 与 source.kind 关系。"""
    def 收到派发(模式,事件名,参数):
        """拦截即将提交的 session/title。"""
        if 事件名!='session/event':
            return
        if len(参数)<2:
            return
        事件=参数[1]
        if 事件['type']!='session/title':
            return
        数据=事件['data']
        来源=数据['source']
        序列列表=数据['messageSeqs'] if 'messageSeqs' in 数据 and 数据['messageSeqs'] is not None else []
        需要空=来源['kind']=='user'
        if (len(序列列表)==0)!=需要空:
            要求='cite no message seqs' if 需要空 else 'cite at least one message seq'
            失败('session/title event '+str(事件['seq'])+' with source "'+str(来源['kind'])+'" must '+要求+'; got '+str(len(序列列表)))
    子上下文.监听('internal/dispatch',收到派发,{'全局':True})

def 应用(上下文):
    """注册不变量配套。"""
    return 上下文.invariants.register(包名,安装)

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
