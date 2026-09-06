"""已加载轮次投影为紧凑导航轨道项。

对齐上游 `ui-chat/src/client/conversation-nodes/turn-navigation.ts`。公开面仅中文名。
"""

__all__=['同回合导航项','回合导航项','提示预览上限','回复预览上限']#仅中文公开名

提示预览上限=50#提示词预览上限
回复预览上限=120#回复预览上限

def 预览(片段列表,上限):#有界预览文本
    """折叠空白；超限省略。展示宽度按码点，不是线协议字节预算。"""
    文=''#累计
    未读=False#未读
    for 片 in 片段列表:#遍历
        if len(文)>=上限*2:#够预算
            未读=True#未读
            break#停
        截=len(片)>上限*2#过长
        块=片[:上限*2] if 截 else 片#截
        文=块 if 文=='' else 文+' '+块#拼
        if 截:#截断
            未读=True#未读
            break#停
    规=' '.join(文.split()).strip()#折叠
    if len(规)>上限-1:#超限
        return 规[:上限-1].rstrip()+'…'#省略
    return 规+'…' if 未读 else 规#未读省略

def 提示文本(节点):#节点提示词预览
    """仅 user。"""
    if 节点['kind']!='user':#非
        return ''#空
    数据=节点['data'] if 'data' in 节点 else None#数据
    内容=数据['content'] if 数据 is not None and 'content' in 数据 else []#内容
    return 预览((块['text'] for 块 in 内容 if 'type' in 块 and 块['type']=='text' and 'text' in 块),提示预览上限)#预览

def 回复文本(节点):#节点回复预览
    """仅 assistant-step。"""
    if 节点['kind']!='assistant-step':#非
        return ''#空
    数据=节点['data'] if 'data' in 节点 else None#数据
    块列表=数据['blocks'] if 数据 is not None and 'blocks' in 数据 else []#块
    return 预览((块['text'] for 块 in 块列表 if 'kind' in 块 and 块['kind']=='text' and 'text' in 块),回复预览上限)#预览

def 同回合导航项(左,右):#导航项相等
    """双侧字段。"""
    if 左 is None or 右 is None:#单侧
        return 左 is 右#同缺席
    return (#字段
        左['turn']==右['turn']#轮次
        and 左['anchorKey']==右['anchorKey']#锚
        and 左['prompt']==右['prompt']#提示
        and 左['response']==右['response']#回复
    )#结束

def 回合导航项(回合,位置索引,节点表):#投影导航项
    """无可见节点则缺席。位置与仓为本包可变对象。"""
    键列表=位置索引.getTurn(回合)#轮内键
    已载=[]#可见
    for 键 in 键列表:#扫
        节=节点表.get(键)#节点
        if 节 is not None and 节['visibility']=='visible':#可见
            已载.append(节)#收
    用户=None#开场用户
    for 节 in 已载:#找
        if 节['kind']=='user':#用户
            用户=节#记下
            break#停
    锚=用户 if 用户 is not None else (已载[0] if len(已载)>0 else None)#锚点
    if 锚 is None:#无
        return None#缺席
    回复=None#末条回复
    for 节 in 已载:#从后找
        if 回复文本(节)!='':#非空
            回复=节#记下
    return {#导航项
        'turn':回合,#轮次
        'anchorKey':锚['key'],#锚键
        'prompt':'' if 用户 is None else 提示文本(用户),#提示
        'response':'' if 回复 is None else 回复文本(回复),#回复
    }#结束
