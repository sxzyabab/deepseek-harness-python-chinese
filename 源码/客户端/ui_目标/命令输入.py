"""Goal 自有的人类命令输入投影。

对齐上游 `ui-goal/src/client/goal-command-input.ts`。公开面仅中文名。
独立于模型消息投影；通用命令节点定义仍保留结果行。
"""

__all__=['目标错误','目标命令文本','目标命令输入定义']#仅中文公开名

class 目标错误(Exception):
    """本包异常基类。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

def 目标命令文本(事件):#从 command/run 拼可见命令行
    """去掉解析器尾随空白后的命令文本。"""
    数据=事件['data'] if 'data' in 事件 and 事件['data'] is not None else {}#事件数据
    参数=数据['args'] if 'args' in 数据 and 数据['args'] is not None else ''#参数
    名=数据['name'] if 'name' in 数据 else None#命令名
    return f"/{名}{str(参数).rstrip()}"#斜杠+名+去尾空白参数

def 匹配(事件):#是否认作 /goal 的 command/run
    """对不上返回 None。"""
    if 事件['type']!='command/run':#非命令运行
        return None#忽略
    数据=事件['data'] if 'data' in 事件 and 事件['data'] is not None else {}#数据
    if ('name' not in 数据) or 数据['name']!='goal':#非 goal
        return None#忽略
    return {'id':str(数据['commandId']),'role':'start'}#开节点

def 起始(上下文,匹配结果):#用 command/run 建折叠状态
    """开节点必须是 command/run。"""
    事件=匹配结果['event'] if 'event' in 匹配结果 else None#事件
    if 事件 is None or 事件['type']!='command/run':#必须
        raise 目标错误('goal-command-input start requires command/run')#起始必须是 command/run
    数据=事件['data'] if 'data' in 事件 and 事件['data'] is not None else {}#数据
    return {#折叠状态
        'commandId':数据['commandId'] if 'commandId' in 数据 else None,#命令身份
        'seq':事件['seq'] if 'seq' in 事件 else None,#起始序号
        'time':事件['time'] if 'time' in 事件 else None,#时刻
        'text':目标命令文本(事件),#可见命令行
    }#状态结束

def 更新(上下文):#无后续事件
    """状态原样返回。"""
    return 上下文['state'] if 'state' in 上下文 else None#原样

def 建视图节点(上下文):#投影聊天节点
    """尚无状态则不发表。"""
    状态=上下文['state'] if 'state' in 上下文 else None#状态
    if 状态 is None:#无
        return None#不发表
    起始事件=上下文['start'] if 'start' in 上下文 else None#起始
    位置=起始事件['location'] if 起始事件 is not None and 'location' in 起始事件 else None#位置
    if 位置 is None:#未解析
        位置={'kind':'unresolved'}#缺省
    序号=状态['seq'] if 'seq' in 状态 else 0#序号
    return {#聊天节点
        'key':上下文['key'] if 'key' in 上下文 else None,#节点键
        'kind':'command-input',#种类
        'id':上下文['id'] if 'id' in 上下文 else None,#身份
        'target':'chat',#聊天面
        'anchorSeq':序号-0.1,#锚在 command/run 稍前
        'location':位置,#位置
        'visibility':'visible',#始终可见
        'data':{#视图载荷
            'commandId':状态['commandId'] if 'commandId' in 状态 else None,#命令身份
            'text':状态['text'] if 'text' in 状态 else None,#可见命令行
            'time':状态['time'] if 'time' in 状态 else None,#时刻
        },#data 结束
    }#节点结束

目标命令输入定义={#会话节点定义
    'kind':'goal-command-input',#本贡献 kind
    'target':'chat',#投到聊天面
    'match':匹配,#匹配
    'start':起始,#起始
    'update':更新,#更新
    'buildViewNode':建视图节点,#建视图
}#定义结束
