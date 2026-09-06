"""轨迹拥有的收件箱分类与输入消息记录节点定义。

对齐上游 `ui-trajectory/src/client/trajectory-message-definitions.ts`。公开面仅中文名。
"""
from .轨迹节点 import 轨迹节点#包装轨迹贡献信封
from .轨迹记录 import 轨迹错误#本包异常

__all__=['登记轨迹消息定义']#仅中文公开名

def 应用拼接(上一,拼接):#把拼接应用到上一状态
    """更新后的收件箱状态。"""
    上态=上一['state'] if 上一 is not None and 'state' in 上一 else None#上一状态
    待处理=list(上态['pending'] if 上态 is not None and 'pending' in 上态 else [])#复制待处理队列
    已认领=set(上态['claimed'] if 上态 is not None and 'claimed' in 上态 else [])#复制已认领集合
    起始=拼接['start'] if 'start' in 拼接 else 0#起始下标
    删除数=拼接['removedCount'] if 'removedCount' in 拼接 and 拼接['removedCount'] is not None else 0#删除条数
    插入=list(拼接['inserted'] if 'inserted' in 拼接 and 拼接['inserted'] is not None else [])#插入的身份列表
    删除=待处理[起始:起始+删除数]#将被删除的
    待处理[起始:起始+删除数]=插入#按起止删插
    for 身份 in 插入:#插入项从已认领中去掉
        已认领.discard(身份['id'] if 'id' in 身份 else None)#去掉
    if ('outcome' not in 拼接) or 拼接['outcome']!='canceled':#非取消结果
        for 身份 in 删除:#删除项记入已认领
            已认领.add(身份['id'] if 'id' in 身份 else None)#记下
    return {'pending':待处理,'claimed':已认领}#新待处理与已认领

def 上下文出处(来源):#出处最小实现
    """运行时未迁完时的出处投影。"""
    return {'source':来源}#出处

def 上下文表单(来源):#表单最小实现
    """运行时未迁完时的表单投影。"""
    return 来源['form'] if 来源 is not None and 'form' in 来源 else None#表单字段

def 收件箱匹配(事件):#只匹配 next-step 收件箱拼接
    """以序号为 id 起步。"""
    if 事件['type']!='agent/inbox/spliced':#非拼接
        return None#忽略
    数据=事件['data'] if 'data' in 事件 else None#载荷
    if 数据 is None or ('target' not in 数据) or 数据['target']!='next-step':#非 next-step
        return None#忽略
    return {'id':str(事件['seq']),'role':'start'}#起步

def 收件箱开始(_上下文,匹配,读取器):#从拼接事件播种状态
    """起步必须是 inbox/spliced。"""
    事件=匹配['event'] if 'event' in 匹配 else None#本条事件
    if 事件 is None or 事件['type']!='agent/inbox/spliced':#角色与类型不一致
        raise 轨迹错误('trajectory-inbox-next-step start requires agent/inbox/spliced')#起步必须是 inbox/spliced
    return 应用拼接(读取器.previous('trajectory-inbox-next-step'),事件['data'] if 'data' in 事件 else None)#把本条拼接叠到上一状态

def 收件箱更新(上下文,_匹配):#单事件节点
    """状态原样。"""
    return 上下文['state'] if 'state' in 上下文 else None#原样

def 收件箱发布(_匹配):#不发布到视图
    """收件箱只作分类器。"""
    return 'none'#不发布

def 消息开始(_上下文,匹配,读取器):#从 user/message 播种消息节点
    """起步必须是 user/message。"""
    事件=匹配['event'] if 'event' in 匹配 else None#本条用户消息事件
    if 事件 is None or 事件['type']!='user/message':#角色与类型不一致
        raise 轨迹错误('trajectory-input-message start requires user/message')#起步必须是 user/message
    数据=事件['data'] if 'data' in 事件 else None#消息载荷
    来源=数据['source'] if 数据 is not None and 'source' in 数据 else None#消息来源
    if 来源 is None or ('kind' not in 来源) or 来源['kind']!='user':#非用户来源，视为上下文
        return {'kind':'context','seq':事件['seq'],'time':事件['time'],'content':数据['content'] if 数据 is not None and 'content' in 数据 else None,'source':来源,'provenance':上下文出处(来源),'form':上下文表单(来源)}#上下文消息节点
    上一=读取器.previous('trajectory-inbox-next-step')#读上一收件箱
    上态=上一['state'] if 上一 is not None and 'state' in 上一 else None#收件箱状态
    已认领集=上态['claimed'] if 上态 is not None and 'claimed' in 上态 else None#已认领
    消息标识=str(数据['id']) if 数据 is not None and 'id' in 数据 else None#消息 id
    已认领=已认领集 is not None and 消息标识 is not None and 消息标识 in 已认领集#该消息 id 是否已被认领
    if 已认领:#已认领则为转向
        return {'kind':'steering','messageId':数据['id'],'seq':事件['seq'],'time':事件['time'],'content':数据['content'] if 'content' in 数据 else None,'source':来源}#转向消息节点
    return {'kind':'user','seq':事件['seq'],'time':事件['time'],'content':数据['content'] if 'content' in 数据 else None,'source':来源}#用户消息节点

def 消息匹配(事件):#只匹配用户消息
    """以序号为 id 起步。"""
    if 事件['type']=='user/message':#用户消息事件
        return {'id':str(事件['seq']),'role':'start'}#起步
    return None#不认其他事件

def 消息更新(上下文,_匹配):#单事件节点
    """状态原样。"""
    return 上下文['state'] if 'state' in 上下文 else None#原样

def 消息构建视图(上下文):#包进轨迹信封
    """无状态则不产出。"""
    状态=上下文['state'] if 'state' in 上下文 else None#消息节点
    if 状态 is None:#无状态
        return None#不产出
    return 轨迹节点(上下文,状态['seq'] if 'seq' in 状态 else None,{'kind':'node','node':状态})#包进轨迹信封

轨迹收件箱定义={#收件箱节点定义
    'kind':'trajectory-inbox-next-step',#定义种类
    'match':收件箱匹配,#收件箱拼接
    'start':收件箱开始,#播种
    'update':收件箱更新,#单事件节点
    'publication':收件箱发布,#不发布到视图
}#定义结束

轨迹消息定义={#输入消息节点定义
    'kind':'trajectory-input-message',#定义种类
    'target':'trajectory',#投递到轨迹目标
    'match':消息匹配,#匹配
    'start':消息开始,#播种
    'update':消息更新,#单事件节点
    'buildViewNode':消息构建视图,#投影
}#定义结束

def 登记轨迹消息定义(上下文):#登记收件箱与输入消息定义
    """登记轨迹拥有的收件箱分类与消息记录。"""
    上下文.conversationEvents.register(轨迹收件箱定义)#登记收件箱定义
    上下文.conversationEvents.register(轨迹消息定义)#登记输入消息定义
