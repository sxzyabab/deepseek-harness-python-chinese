"""会话检索消费方用的第一方语义文本抽取。对齐上游 `session-query/src/extraction.ts`。"""

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 抽取会话事件文本(事件):#按事件类型抽出可检索文本
    """从一条第一方会话事件抽出可检索的语义文本。"""
    类型=取字段(事件,'type')#判别标签
    if 类型=='user/message':#用户消息
        return 内容文本(取字段(取字段(事件,'data'),'content'))#内容块文本
    if 类型=='assistant/message':#助手消息
        return 内容文本(取字段(取字段(取字段(事件,'data'),'message'),'content'))#助手内容
    if 类型=='tool/call':#工具调用
        return 拼接文本([取字段(取字段(事件,'data'),'name'),取字段(取字段(事件,'data'),'arguments')])#名与参数
    if 类型=='tool/result':#工具结果
        错误=取字段(取字段(事件,'data'),'error')#可选错误
        return 拼接文本([
            内容文本(取字段(取字段(取字段(事件,'data'),'message'),'content')),
            取字段(错误,'name','') if 错误 is not None else '',
            取字段(错误,'code','') if 错误 is not None else '',
        ])#结果与错误标识
    if 类型=='todo/write':#待办写入
        片段=[]#状态与内容
        for 条 in 取字段(取字段(事件,'data'),'todos',[]):#逐条待办
            片段.append(取字段(条,'status'))#状态
            片段.append(取字段(条,'content'))#内容
        return 拼接文本(片段)#拼接
    if 类型=='turn/end':#回合结束
        return 回合结束文本(取字段(取字段(事件,'data'),'reason'))#按原因抽文本
    return ''#结构边界与未知类型不贡献文本

def 回合结束文本(原因):#按回合结束原因抽文本
    """按回合结束原因抽出可检索文本。"""
    if not isinstance(原因,dict):#必须是对象
        return ''#不贡献
    种类=取字段(原因,'kind')#原因标签
    if 种类=='error':#出错结束
        return 拼接文本(['error',取字段(取字段(原因,'error'),'message','')])#错误消息
    if 种类=='aborted':#中止
        return 'aborted'#固定文本
    if 种类 in ('max-tokens','interrupted'):#其他结构化结局
        return 种类#原因标签
    return ''#完成与未知不贡献

def 内容文本(内容):#把内容块列表收成可检索文本
    """把内容块列表收成换行拼接的语义文本。"""
    片段=[]#收集片段
    for 块 in 内容 or []:#逐块
        片段.extend(块文本(块))#展开块
    return 拼接文本(片段)#拼接

def 块文本(块):#从单块抽出可检索片段
    """从单块抽出可检索片段。"""
    if not isinstance(块,dict):#必须是对象
        return []#不贡献
    类型=取字段(块,'type')#块类型
    if 类型=='text':#普通文本
        return [取字段(块,'text','')]#文本
    if 类型=='tool-call':#块内工具调用
        return [取字段(块,'name',''),取字段(块,'arguments','')]#名与参数
    if 类型=='tool-result':#块内工具结果
        return 内容文本(取字段(块,'content',[]))#嵌套内容
    return []#推理与未知块不贡献

def 拼接文本(片段们):#把片段收成换行文本
    """去空白、丢掉空串、换行拼接。"""
    干净=[str(段).strip() for 段 in 片段们 if str(段).strip()!='']#修剪非空
    return '\n'.join(干净)#换行拼接
