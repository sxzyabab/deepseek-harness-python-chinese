"""后台工作流运行的实时进度镜像：把引擎事件写入所属任务输出环。"""

def 创建工作流记录镜像(上下文):
    """订阅 workflow/* 进度事件，按运行号写入任务环。"""
    活跃={}

    def 阶段(信息,标题,*其余):
        """把阶段标题写入进度行与 log 通道。"""
        _=其余
        任务=活跃.get(信息['id'])
        if 任务 is None:
            return
        任务.updateProgress(标题)
        任务.append('▸ '+str(标题)+'\n',{'channel':'log'})

    def 日志(信息,消息,*其余):
        """把引擎日志写入 log 通道。"""
        _=其余
        任务=活跃.get(信息['id'])
        if 任务 is None:
            return
        任务.append(str(消息)+'\n',{'channel':'log'})

    def 智能体开始(信息,智能体,*其余):
        """成员开始叙述。"""
        _=其余
        任务=活跃.get(信息['id'])
        if 任务 is None:
            return
        任务.append('agent #'+str(智能体['seq'])+' '+str(智能体['label'])+' started\n',{'channel':'log'})

    def 智能体结束(信息,智能体,*其余):
        """成员结束叙述。"""
        _=其余
        任务=活跃.get(信息['id'])
        if 任务 is None:
            return
        任务.append('agent #'+str(智能体['seq'])+' '+str(智能体['outcome'])+'\n',{'channel':'log'})

    上下文.监听('workflow/phase',阶段)
    上下文.监听('workflow/log',日志)
    上下文.监听('workflow/agent-start',智能体开始)
    上下文.监听('workflow/agent-end',智能体结束)

    def 开始(运行号,任务):
        """把一次后台运行接到任务环。"""
        活跃[运行号]=任务

    def 停止(运行号):
        """停止路由；幂等。"""
        活跃.pop(运行号,None)

    return {'开始':开始,'停止':停止}

__all__=['创建工作流记录镜像']
