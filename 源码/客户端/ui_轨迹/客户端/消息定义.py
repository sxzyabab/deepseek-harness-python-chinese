"""轨迹拥有的收件箱分类与输入消息记录节点定义。

对齐上游 `ui-trajectory/src/client/trajectory-message-definitions.ts`。公开面仅中文名。
"""
from .定义公共 import 轨迹节点#包装轨迹贡献信封
from .轨迹记录 import 取字段#读字段

__all__=['登记轨迹消息定义']#仅中文公开名

def 应用拼接(上一,拼接):#把拼接应用到上一状态
    """更新后的收件箱状态。"""
    待处理=list(取字段(取字段(上一,'state'),'pending') if 上一 is not None else [])#复制待处理队列
    已认领=set(取字段(取字段(上一,'state'),'claimed') if 上一 is not None else [])#复制已认领集合
    起始=取字段(拼接,'start')#起始下标
    删除数=取字段(拼接,'removedCount') or 0#删除条数
    插入=list(取字段(拼接,'inserted') or [])#插入的身份列表
    删除=待处理[起始:起始+删除数]#将被删除的
    待处理[起始:起始+删除数]=插入#按起止删插
    for 身份 in 插入:#插入项从已认领中去掉
        已认领.discard(取字段(身份,'id'))#去掉
    if 取字段(拼接,'outcome')!='canceled':#非取消结果
        for 身份 in 删除:#删除项记入已认领
            已认领.add(取字段(身份,'id'))#记下
    return {'pending':待处理,'claimed':已认领}#新待处理与已认领

def 上下文出处(来源):#出处最小实现
    """运行时未迁完时的出处投影。"""
    return {'source':来源}#出处

def 上下文表单(来源):#表单最小实现
    """运行时未迁完时的表单投影。"""
    return 取字段(来源,'form')#表单字段

轨迹收件箱定义={#收件箱节点定义
    'kind':'trajectory-inbox-next-step',#定义种类
    'match':lambda 事件:({'id':str(取字段(事件,'seq')),'role':'start'} if 取字段(事件,'type')=='agent/inbox/spliced' and 取字段(取字段(事件,'data'),'target')=='next-step' else None),#收件箱拼接
    'start':lambda _上下文,匹配,读取器:(lambda:(_ for _ in ()).throw(Exception('trajectory-inbox-next-step start requires agent/inbox/spliced')) if 取字段(取字段(匹配,'event'),'type')!='agent/inbox/spliced' else 应用拼接(读取器.previous('trajectory-inbox-next-step'),取字段(取字段(匹配,'event'),'data')))(),#播种
    'update':lambda 上下文,_匹配:取字段(上下文,'state'),#单事件节点
    'publication':lambda _匹配:'none',#不发布到视图
}#定义结束

def 收件箱开始(上下文,匹配,读取器):#从拼接事件播种状态
    """起步必须是 inbox/spliced。"""
    事件=取字段(匹配,'event')#本条事件
    if 取字段(事件,'type')!='agent/inbox/spliced':#角色与类型不一致
        raise Exception('trajectory-inbox-next-step start requires agent/inbox/spliced')#起步必须是 inbox/spliced
    return 应用拼接(读取器.previous('trajectory-inbox-next-step'),取字段(事件,'data'))#把本条拼接叠到上一状态

轨迹收件箱定义['start']=收件箱开始#替换为具名函数

def 消息开始(_上下文,匹配,读取器):#从 user/message 播种消息节点
    """起步必须是 user/message。"""
    事件=取字段(匹配,'event')#本条用户消息事件
    if 取字段(事件,'type')!='user/message':#角色与类型不一致
        raise Exception('trajectory-input-message start requires user/message')#起步必须是 user/message
    数据=取字段(事件,'data')#消息载荷
    来源=取字段(数据,'source')#消息来源
    if 取字段(来源,'kind')!='user':#非用户来源，视为上下文
        return {'kind':'context','seq':取字段(事件,'seq'),'time':取字段(事件,'time'),'content':取字段(数据,'content'),'source':来源,'provenance':上下文出处(来源),'form':上下文表单(来源)}#上下文消息节点
    上一=读取器.previous('trajectory-inbox-next-step')#读上一收件箱
    已认领=上一 is not None and 取字段(取字段(上一,'state'),'claimed') is not None and str(取字段(数据,'id')) in 取字段(取字段(上一,'state'),'claimed')#该消息 id 是否已被认领
    if 已认领:#已认领则为转向
        return {'kind':'steering','messageId':取字段(数据,'id'),'seq':取字段(事件,'seq'),'time':取字段(事件,'time'),'content':取字段(数据,'content'),'source':来源}#转向消息节点
    return {'kind':'user','seq':取字段(事件,'seq'),'time':取字段(事件,'time'),'content':取字段(数据,'content'),'source':来源}#用户消息节点

def 消息匹配(事件):#只匹配用户消息
    """以序号为 id 起步。"""
    if 取字段(事件,'type')=='user/message':#用户消息事件
        return {'id':str(取字段(事件,'seq')),'role':'start'}#起步
    return None#不认其他事件

def 消息构建视图(上下文):#包进轨迹信封
    """无状态则不产出。"""
    状态=取字段(上下文,'state')#消息节点
    if 状态 is None:#无状态
        return None#不产出
    return 轨迹节点(上下文,取字段(状态,'seq'),{'kind':'node','node':状态})#包进轨迹信封

轨迹消息定义={#输入消息节点定义
    'kind':'trajectory-input-message',#定义种类
    'target':'trajectory',#投递到轨迹目标
    'match':消息匹配,#匹配
    'start':消息开始,#播种
    'update':lambda 上下文,_匹配:取字段(上下文,'state'),#单事件节点
    'buildViewNode':消息构建视图,#投影
}#定义结束

def 登记轨迹消息定义(上下文):#登记收件箱与输入消息定义
    """登记轨迹拥有的收件箱分类与消息记录。"""
    上下文.conversationEvents.register(轨迹收件箱定义)#登记收件箱定义
    上下文.conversationEvents.register(轨迹消息定义)#登记输入消息定义
