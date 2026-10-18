'把 /goal 的 command/run 收成独立的聊天节点'

__all__=['目标命令','目标命令输入定义']

目标命令='goal'#这条投影认的命令名


def 匹配(事件):
    '只有 /goal 的 command/run 才开节点'
    if 事件['type']!='command/run':#不是命令运行
        return None#不认
    if 事件['data']['name']!=目标命令:#不是 goal
        return None#不认
    return {'id':str(事件['data']['commandId']),'role':'start'}#开节点


def 起始(上下文,匹配结果):
    '开节点必须是 command/run，可见文本去掉参数尾随空白'
    事件=匹配结果['event']#命中的事件
    if 事件['type']!='command/run':#不是命令运行
        raise Exception('goal-command-input start requires command/run')#起始类型不对
    数据=事件['data']#命令载荷
    参数=数据['args'] if 'args' in 数据 and 数据['args'] is not None else ''#缺省当空串
    return {#折叠状态
        'commandId':数据['commandId'],#命令身份
        'seq':事件['seq'],#起始序号
        'time':事件['time'],#时刻
        'text':'/'+数据['name']+参数.rstrip(),#斜杠、名字、去掉尾随空白的参数
    }#状态结束


def 更新(上下文):
    '没有后续折叠，状态原样留下'
    return 上下文['state']#原状态


def 建视图节点(上下文):
    '没有状态就不发表。位置缺了用 unresolved'
    状态=上下文['state']#折叠状态
    if 状态 is None:#还没有
        return None#不发表
    起始匹配=上下文['start'] if 'start' in 上下文 else None#起始匹配
    if 起始匹配 is None or 起始匹配.get('location') is None:#没有位置
        位置={'kind':'unresolved'}#未解析
    else:#有位置
        位置=起始匹配['location']#沿用
    return {#聊天节点
        'key':上下文['key'],#节点键
        'kind':'command-input',#命令输入
        'id':上下文['id'],#身份
        'target':'chat',#聊天面
        'anchorSeq':状态['seq']-0.1,#锚在 command/run 稍前
        'location':位置,#位置
        'visibility':'visible',#可见
        'data':{#视图载荷
            'commandId':状态['commandId'],#命令身份
            'text':状态['text'],#可见命令行
            'time':状态['time'],#时刻
        },#载荷结束
    }#节点结束


目标命令输入定义={#会话节点定义
    'kind':'goal-command-input',#本贡献 kind
    'target':'chat',#投到聊天面
    'match':匹配,#匹配
    'start':起始,#起始
    'update':更新,#更新
    'buildViewNode':建视图节点,#建视图
}#定义结束
