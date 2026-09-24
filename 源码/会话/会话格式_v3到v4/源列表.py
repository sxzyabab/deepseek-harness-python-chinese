"""已发布 V3 插件来源转换与已声明消息遍历。"""
from ..会话格式 import 会话格式错误,是否会话格式json对象#从会话格式导入

def 映射事件消息(事件,变换):#映射事件消息
    """只走访第一方事件载荷携带的消息。"""
    数据=事件['data']#载荷
    if not 是否会话格式json对象(数据):#非对象
        return 事件#原样
    if 事件['type']=='user/message':#用户消息即载荷
        消息=变换(数据)#变换
        return 事件 if 消息 is 数据 else {**事件,'data':消息}#无变化则原样
    if 事件['type'] in ('developer/message','system/message','assistant/message','tool/result'):#嵌套消息
        if not 是否会话格式json对象(数据.get('message')):#须消息对象
            raise 会话格式错误(事件['type']+' requires a message')#错误
        消息=变换(数据['message'])#变换
        return 事件 if 消息 is 数据['message'] else {**事件,'data':{**数据,'message':消息}}#写回
    键='inserted' if 事件['type']=='agent/inbox/spliced' else ('messages' if 事件['type']=='session/title-llm-request' else None)#消息字段
    if 键 is None:#无消息槽
        return 事件#原样
    消息列表=数据.get(键)#消息列表
    if not isinstance(消息列表,list):#须数组
        raise 会话格式错误(事件['type']+' requires message array')#错误
    已改=[]#变换结果
    for 项 in 消息列表:#逐条
        if not 是否会话格式json对象(项):#须对象
            raise 会话格式错误(事件['type']+' requires message objects')#错误
        已改.append(变换(项))#变换
    if all(已改[下标] is 消息列表[下标] for 下标 in range(len(消息列表))):#无变化
        return 事件#原样
    return {**事件,'data':{**数据,键:已改}}#写回

#已发布 V3 插件名，其当前生产者种类不再是插件字符串本身。
已重命名生产者={#插件串到当前种类
    'compact':'compact-checkpoint',
    'tools-code-mode':'ptc-mode',
    'tools-ptc':'ptc-mode',
    'dsh-compaction-basic':'compact-basic',
    '@deepseek-ai/dsh-system-prompt':'runtime-context',
}#已重命名生产者结束

#第一方 V3 插件身份，有意保留当前种类名。
已发布同名生产者=frozenset([#同名生产者
    'agent-instructions','session-reference','team-message','goal',
    'skill-invocation','skill-catalog','coordinator','subagent-report',
    'subagent-settled','webhook','agent-message','model-selection',
    'plan-mode','time-context','tmux-context','user-approval',
    'repeat-tool-reminder','tool-cordis','cordis-host-runner','tool-goal',
    'tool-jobs','hooks-codex','hooks-claude-code','schedule',
    'dsh-session-title-llm',
])#已发布同名生产者结束

def 生产者种类(插件,角色):#解析生产者种类
    """解析一个已发布 V3 插件串的当前生产者种类。"""
    if 插件=='@deepseek-ai/dsh-system-prompt' and 角色=='system':#系统提示词
        return 'system-prompt'#系统提示词种类
    if 插件 in 已重命名生产者:#已重命名
        return 已重命名生产者[插件]#新种类
    if 插件 in 已发布同名生产者:#同名保留
        return 插件#原名
    return 'plugin:'+插件#扩展命名空间

def 改写插件来源(来源,序号,角色):#改写插件来源
    """把已发布 V3 插件来源提升为当前生产者自有形态。"""
    插件=来源.get('plugin')#插件串
    if not isinstance(插件,str):#须串
        raise 会话格式错误('plugin source at seq '+str(序号)+' is not canonical: plugin requires a string')#错误
    种类=生产者种类(插件,角色)#当前种类
    if len(来源)==2:#仅kind与plugin
        return {'kind':种类}#只保留kind
    return {键:(种类 if 键=='kind' else 项) for 键,项 in 来源.items() if 键!='plugin'}#丢掉plugin

def 改写v3消息来源(来源,序号,角色):#改写v3消息来源
    """转换已发布插件包装，保留每个直接来源种类及其元数据。"""
    种类=来源.get('kind')#种类
    if not isinstance(种类,str) or len(种类)==0:#须非空
        raise 会话格式错误('message source at seq '+str(序号)+' requires a nonempty kind')#错误
    if 种类=='plugin':#插件包装
        return 改写插件来源(来源,序号,角色)#提升
    return 来源#原样
