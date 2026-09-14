from ...模型后端.llm.助手流 import 拼接助手流文本#嵌入流文本拼接

class 助手输出折叠:
    """选取规则的增量折叠，供观察子体流式输出的后端使用：会话事件后端推送每条事件，没有会话事件的传输（ACP 内容块）用推送文本把原始文本送进同一流式回退。"""
    def __init__(自身):
        """初始无完整消息、无流式碎片。"""
        自身._消息=None#最后一条非空助手消息
        自身._碎片=[]#流式文本碎片

    def 推送(自身,事件):
        """折叠一条会话事件：非空助手消息成为候选最终答案，其内嵌流与任何仅日志的 attempt 扩展流式回退；其余事件不贡献。事件为 dict。"""
        类型=事件['type'] if 'type' in 事件 else None#事件类型
        if 类型=='assistant/message':#完整助手消息
            数据=事件['data'] if 'data' in 事件 else None#data
            消息=数据['message'] if isinstance(数据,dict) and 'message' in 数据 else None#message
            内容=消息['content'] if isinstance(消息,dict) and 'content' in 消息 else None#消息内容
            if 内容 is not None and len(内容)>0:#非空才成为候选
                自身._消息=内容#记下候选
        if 类型=='assistant/message' or 类型=='assistant/attempt':#消息或 attempt 带流
            数据=事件['data'] if 'data' in 事件 else None#data
            流=数据['stream'] if isinstance(数据,dict) and 'stream' in 数据 else []#嵌入流
            自身.推送文本(拼接助手流文本(流 or []))#拼接流文本并入回退

    def 推送文本(自身,文本):
        """用会话事件之外观察到的文本扩展流式回退。空段为空操作。"""
        if 文本 is not None and len(文本)>0:#非空才记下
            自身._碎片.append(文本)#记下碎片

    def 收集(自身):
        """选取目前已折叠的最终输出。最后一条非空助手消息，否则累计流式文本，子体两者都没产出时为 None。"""
        if 自身._消息 is not None:#优先完整消息
            return 自身._消息#完整消息
        文本=''.join(自身._碎片)#拼接流式碎片
        if len(文本)>0:#有文本
            return [{'type':'text','text':文本}]#包成块
        return None#两者都没产出

def 最终助手输出(事件列表):
    """对一份完整的子体自有事件后缀应用选取规则。"""
    折叠=助手输出折叠()#新建
    for 事件 in 事件列表:#逐条
        折叠.推送(事件)#折叠
    return 折叠.收集()#选取
