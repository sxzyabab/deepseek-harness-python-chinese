'工作区文件远程失败。消息原样过线，判别看 code'


class 远程错误(Exception):
    '一次远程调用失败。附加信息做成属性，消息不做删改'
    def __init__(自身,码,消息,详情,原因=None):
        '记下 code、message、details。原因只留在本进程'
        super().__init__(消息)#消息原样
        自身.name='RemoteError'#固定错误名
        自身.code=码#错误码
        自身.message=消息#过线说明
        自身.details=详情#结构化详情
        自身.isDSHRemoteError=True#跨模块识别标记
        if 原因 is not None:#原因链
            自身.__cause__=原因#只留本进程
