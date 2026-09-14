from .控制器 import 消息反馈控制器,描述失败#消息层
from .对话框 import 反馈对话框控制器#对话框

__all__=['反馈表面']#仅中文公开名

class 反馈表面:#按会话成对体
    """支撑一个会话每个入口。"""
    def __init__(自身,上下文,会话标识):
        """注入浏览器插件上下文与会话身份。"""
        自身._上下文=上下文#上下文
        自身._会话标识=会话标识#会话
        自身.反馈=消息反馈控制器(上下文.remote.messageFeedback,会话标识)#消息层
        def 路由(目标,条目):#按目标路由提交
            """消息目标走所选评分；会话目标走 sessionFeedback。"""
            if 'kind' in 目标 and 目标['kind']=='message':#消息
                return 自身.反馈.rate(目标['messageId'],目标['rating'],条目)#所选评判
            return 自身._记录会话(条目)#会话级
        自身.对话框=反馈对话框控制器(路由)#对话框

    def _记录会话(自身,条目):#记录会话反馈
        """经 sessionFeedback Remote 记录。条目为 dict。"""
        请求={'sessionId':自身._会话标识}#请求
        请求.update(条目)#展开条目
        载体=自身._上下文.remote.sessionFeedback.record(请求)#远程
        if 'ok' not in 载体 or not 载体['ok']:#载体失败
            错误=载体['error'] if 'error' in 载体 else {}#错误
            return {'ok':False,'error':{'code':错误['code'] if 'code' in 错误 else None,'message':错误['message'] if 'message' in 错误 else None}}#失败
        值=载体['value'] if 'value' in 载体 else {}#业务
        if 'ok' in 值 and 值['ok']:#成功
            return {'ok':True}#成功
        业务错=值['error'] if 'error' in 值 else {}#业务错
        码=业务错['code'] if 'code' in 业务错 else None#码
        return {'ok':False,'error':{'code':码,'message':描述失败(码)}}#业务失败

    def 拆除(自身):#拆除
        """丢掉两个控制器。"""
        自身.反馈.dispose()#消息层
        自身.对话框.拆除()#对话框
