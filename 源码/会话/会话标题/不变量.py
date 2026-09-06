"""@deepseek-ai/dsh-session-title 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-session-title'#包名
名称='session-title-invariant'#插件名
注入=['invariants','sessions']#依赖

__all__=['包名','名称','注入','安装','应用']#公开面

def 安装(子上下文=None,失败=None):
    """校验 session/title 的 messageSeqs 与 source.kind 关系。"""
    def 收到派发(模式,事件名,参数):
        """拦截即将提交的 session/title。"""
        if 事件名!='session/event':
            return#放过
        if len(参数)<2:
            return#放过
        事件=参数[1]#事件
        if 事件['type']!='session/title':
            return#放过
        数据=事件['data']#载荷
        来源=数据['source']#来源
        序列列表=数据['messageSeqs'] if 'messageSeqs' in 数据 and 数据['messageSeqs'] is not None else []#序列
        需要空=来源['kind']=='user'#用户重命名
        if (len(序列列表)==0)!=需要空:
            要求='cite no message seqs' if 需要空 else 'cite at least one message seq'#要求
            失败('session/title event '+str(事件['seq'])+' with source "'+str(来源['kind'])+'" must '+要求+'; got '+str(len(序列列表)))#失败
    子上下文.监听('internal/dispatch',收到派发,{'全局':True})#全局拦截

def 应用(上下文对象):
    """注册不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#登记

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
default=应用#Cordis 默认导出槽
