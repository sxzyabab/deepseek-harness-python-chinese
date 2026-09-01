"""@deepseek-ai/dsh-session-title 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-session-title'#包名
名称='session-title-invariant'#插件名
注入=['invariants','sessions']#依赖
name=名称#Cordis 插件名
inject=注入#Cordis 依赖
__all__=['包名','名称','注入','安装','应用']#公开面

def 安装(子上下文=None,失败=None):#安装不变量
    """校验 session/title 的 messageSeqs 与 source.kind 关系。"""
    def 收到派发(模式,事件名,参数):#internal/dispatch
        """拦截即将提交的 session/title。"""
        if 事件名!='session/event':#非会话事件
            return#放过
        if len(参数)<2:#参数不足
            return#放过
        事件=参数[1]#事件
        if 取字段(事件,'type')!='session/title':#非标题
            return#放过
        数据=取字段(事件,'data')#载荷
        来源=取字段(数据,'source')#来源
        序列们=取字段(数据,'messageSeqs') or []#序列
        需要空=取字段(来源,'kind')=='user'#用户重命名
        if (len(序列们)==0)!=需要空:#不一致
            要求='cite no message seqs' if 需要空 else 'cite at least one message seq'#要求
            失败('session/title event '+str(取字段(事件,'seq'))+' with source "'+str(取字段(来源,'kind'))+'" must '+要求+'; got '+str(len(序列们)))#失败
    子上下文.on('internal/dispatch',收到派发,{'global':True})#全局拦截

def 取字段(对象,键,缺省=None):#读字段
    """读映射或对象字段。"""
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#键
    return getattr(对象,键,缺省)#属性

def 应用(上下文对象):#登记不变量
    """注册不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记

apply=应用#Cordis 插件入口
