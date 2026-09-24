"""工作区注册表归档准入的 job 族：会话尚未结算的后台任务，以及随工作归档时的终止。"""

def 安装任务归档准入(上下文,注册表):
    """用仍在运行或停止中的所属任务回答 workspace/session-activity，并用 kill 回答 workspace/session-stop。"""
    def 会话活动(载荷,下一步,*其余):
        """把本会话未结算任务并入活动列表。"""
        会话标识=载荷['sessionId']
        任务列表=运行中任务(注册表,会话标识)
        其余项=下一步()
        if len(任务列表)==0:
            return 其余项
        本项={'kind':'job','items':[{'id':任务['id'],'label':任务['label']} for 任务 in 任务列表]}
        return [本项]+list(其余项)

    def 会话停止(载荷,*其余):
        """归档时终止本会话仍活着的任务。"""
        会话标识=载荷['sessionId']
        for 任务 in 运行中任务(注册表,会话标识):
            try:
                注册表.终止(任务['id'],会话标识,'session archived')
            except (TypeError,KeyError,ValueError,OSError,RuntimeError) as 错误:
                上下文.日志.警告('jobs: killing "'+str(任务['id'])+'" for an archived Session failed: '+str(错误))

    上下文.监听('workspace/session-activity',会话活动)
    上下文.监听('workspace/session-stop',会话停止)

def 运行中任务(注册表,所有者):
    """该会话拥有且尚未结算的任务；同一次列举里无主任务不属于任何人。"""
    结果=[]
    for 任务 in 注册表.列出(所有者):
        if 任务.get('owner')==所有者 and (任务['status']=='running' or 任务['status']=='stopping'):
            结果.append(任务)
    return 结果
