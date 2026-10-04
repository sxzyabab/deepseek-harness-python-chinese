from ...模型后端.llm.异常 import 装备错误#Harness 错误基类

class 用户提问错误(装备错误):#用户提问失败的稳定错误分类
    '用户提问失败的稳定错误分类'
    def __init__(自身,消息,码,options=None):#构造带码错误
        '记下人类可读拒绝原因与稳定分类码'
        if options is None:#无额外选项
            装备错误.__init__(自身,消息,码)#交给装备错误
        else:#带 cause 等选项
            装备错误.__init__(自身,消息,码,options)#交给装备错误
        自身.name='UserQuestionError'#固定错误名
