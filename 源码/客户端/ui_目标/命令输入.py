"""Goal 自有的人类命令输入投影。



对齐上游 `ui-goal/src/client/goal-command-input.ts`。公开面仅中文名。

独立于模型消息投影；通用命令节点定义仍保留结果行。

"""



__all__=['目标命令文本','目标命令输入定义']#仅中文公开名



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺省#缺席

    return getattr(对象,键,缺省)#属性



def 目标命令文本(事件):#从 command/run 拼可见命令行

    """去掉解析器尾随空白后的命令文本。"""

    数据=取字段(事件,'data') or {}#事件数据

    参数=取字段(数据,'args') or ''#参数

    return f"/{取字段(数据,'name')}{str(参数).rstrip()}"#斜杠+名+去尾空白参数



def 匹配(事件):#是否认作 /goal 的 command/run

    """对不上返回 None。"""

    if 取字段(事件,'type')!='command/run':#非命令运行

        return None#忽略

    数据=取字段(事件,'data') or {}#数据

    if 取字段(数据,'name')!='goal':#非 goal

        return None#忽略

    return {'id':str(取字段(数据,'commandId')),'role':'start'}#开节点



def 起始(上下文,匹配结果):#用 command/run 建折叠状态

    """开节点必须是 command/run。"""

    事件=取字段(匹配结果,'event')#事件

    if 取字段(事件,'type')!='command/run':#必须

        raise Exception('goal-command-input start requires command/run')#起始必须是 command/run

    数据=取字段(事件,'data') or {}#数据

    return {#折叠状态

        'commandId':取字段(数据,'commandId'),#命令身份

        'seq':取字段(事件,'seq'),#起始序号

        'time':取字段(事件,'time'),#时刻

        'text':目标命令文本(事件),#可见命令行

    }#状态结束



def 更新(上下文):#无后续事件

    """状态原样返回。"""

    return 取字段(上下文,'state')#原样



def 建视图节点(上下文):#投影聊天节点

    """尚无状态则不发表。"""

    状态=取字段(上下文,'state')#状态

    if 状态 is None:#无

        return None#不发表

    起始事件=取字段(上下文,'start')#起始

    位置=取字段(起始事件,'location') if 起始事件 is not None else None#位置

    if 位置 is None:#未解析

        位置={'kind':'unresolved'}#缺省

    return {#聊天节点

        'key':取字段(上下文,'key'),#节点键

        'kind':'command-input',#种类

        'id':取字段(上下文,'id'),#身份

        'target':'chat',#聊天面

        'anchorSeq':取字段(状态,'seq')-0.1,#锚在 command/run 稍前

        'location':位置,#位置

        'visibility':'visible',#始终可见

        'data':{#视图载荷

            'commandId':取字段(状态,'commandId'),#命令身份

            'text':取字段(状态,'text'),#可见命令行

            'time':取字段(状态,'time'),#时刻

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


