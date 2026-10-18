'把日志坐标交给主对话去定位，不读另一个视图的模型'

def 会话日志聊天目标(锚):
    '用原始事件和可选增量描述一条日志在对话里的位置'
    事件=锚['event']#原始事件
    块=锚.get('chunk')#助手子行才有增量
    数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}#事件数据
    回合=数据.get('turn') if isinstance(数据.get('turn'),(int,float)) and not isinstance(数据.get('turn'),bool) else None#回合号
    步=数据.get('step') if isinstance(数据.get('step'),(int,float)) and not isinstance(数据.get('step'),bool) else None#步骤号
    类型=事件.get('type')#事件类型
    调用=None#工具调用身份
    if 类型=='tool/call':#调用本身
        调用=事件.get('data',{}).get('callId')#调用号
    elif 类型=='tool/result':#调用结果
        消息=事件.get('data',{}).get('message') if isinstance(事件.get('data'),dict) else None#结果消息
        来源=消息.get('source') if isinstance(消息,dict) else None#来源
        调用=来源.get('callId') if isinstance(来源,dict) else None#来源调用
    elif isinstance(数据.get('subCallId'),str):#子调用
        调用=数据.get('subCallId')#子调用号
    elif isinstance(块,dict) and 块.get('type')=='tool-call-delta':#增量里的调用
        调用=块.get('id')#增量调用号
    elif isinstance(块,dict) and 块.get('type')=='block-end' and isinstance(块.get('block'),dict) and 块['block'].get('type')=='tool-call':#工具块结束
        调用=块['block'].get('id')#块上的调用号
    根调用=数据.get('rootCallId') if isinstance(数据.get('rootCallId'),str) else 调用#没有根调用时用调用号
    部位=None#助手部位
    if isinstance(块,dict):#有增量才有部位
        if 块.get('type')=='reasoning-delta':#推理增量
            部位='reasoning'#推理
        elif 块.get('type')=='text-delta':#文本增量
            部位='response'#回复
        else:#块开始或结束
            块类型=None#块种类
            if 块.get('type')=='block-start':#开始
                块类型=块.get('blockType')#块类型
            elif 块.get('type')=='block-end' and isinstance(块.get('block'),dict):#结束
                块类型=块['block'].get('type')#块类型
            if 块类型=='reasoning':#推理块
                部位='reasoning'#推理
            elif 块类型=='text':#文本块
                部位='response'#回复
    目标={'anchorSeq':事件.get('seq')}#原始序号
    if 类型 in ('assistant/message','assistant/attempt','assistant/live-chunk'):#助手行
        目标['nodeKind']='assistant-step'#对话里的助手步骤
    if 回合 is not None:#有回合
        目标['turn']=回合#回合号
    if 步 is not None:#有步骤
        目标['step']=步#步骤号
    if 调用 is not None:#有调用
        目标['callId']=调用#调用号
    if 根调用 is not None and 根调用!=调用:#根调用和调用不同才单独写
        目标['rootCallId']=根调用#根调用
    if 部位 is not None:#有部位
        目标['groupPart']=部位#分组部位
    return 目标#坐标
