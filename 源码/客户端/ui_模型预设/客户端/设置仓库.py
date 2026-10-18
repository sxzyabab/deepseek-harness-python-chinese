from ...存储 import 创建快照存储
from .呈现 import 展示权限预设

__all__=['权限设置命名空间','权限默认于','权限预设设置控制器']

权限设置命名空间='permission'

def 权限默认于(视图,目录):
    '从权限目录取出新会话当前默认和可选标签'
    值体=视图['value']
    if isinstance(值体,dict):
        预设=值体['defaultPreset'] if 'defaultPreset' in 值体 else None
    else:
        预设=值体['defaultPreset']
    当前值=目录['defaultPreset'] if 预设 is None else 预设
    选项=[]
    for 项 in 目录['defaultOptions']:
        选项.append({'id':项['value'],'label':展示权限预设(项['value'],项['name'])})
    命中=False
    for 项 in 选项:
        if 项['id']==当前值:
            命中=True
            break
    if 命中 is not True:
        raise Exception('permission catalog does not advertise its current default')
    return {'currentValue':当前值,'options':选项}

class 权限预设设置控制器:
    '从共享设置镜像和权限目录推出设置行，并把默认预设写回去'
    def __init__(自身,描述面,上下文,目录):
        '记下镜像、远程上下文和目录。第一次加载才开始跟随'
        自身.描述面=描述面
        自身.上下文=上下文
        自身.目录=目录
        自身.存储=创建快照存储({
            'status':'idle',
            'error':None,
            'writable':False,
            'currentValue':'',
            'options':[],
            'revision':0,
        })
        自身.跟随=None
        自身.跟随目录=None
        自身.保存中=False
        自身.已拆除=False

    def 加载(自身):
        '开始跟随镜像和目录，并把快照落到当前答案'
        if 自身.已拆除:
            return
        if 自身.跟随 is None:
            def 镜像变了(*位置参数):
                '镜像发布后重算这一行'
                自身.推导()
            自身.跟随=自身.描述面.subscribe(镜像变了)
        if 自身.跟随目录 is None:
            def 目录变了(*位置参数):
                '目录发布后重算这一行'
                自身.推导()
            自身.跟随目录=自身.目录.存储.subscribe(目录变了)
        def 写入加载(状态):
            '进入加载，清掉旧错误'
            状态['status']='loading'
            状态['error']=None
        自身.存储.update(写入加载)
        自身.描述面.确保()
        try:
            自身.目录.加载()
        except Exception as 错误:
            自身.失败(错误)
            return
        自身.推导()

    def 选定(自身,预设):
        '把一个已公布预设写成以后新建会话的默认。保存途中的再次提交丢掉'
        状态=自身.存储.getSnapshot()
        镜像=自身.描述面.getSnapshot()
        视图=None
        空间=[]
        if 镜像['view'] is not None:
            空间=镜像['view']['namespaces']
        for 行 in 空间:
            if 行['ns']==权限设置命名空间:
                视图=行
                break
        if 视图 is None or 状态['writable'] is not True or 自身.保存中 is True:
            return
        自身.保存中=True
        def 写入保存(草稿):
            '保存中，清掉旧错误'
            草稿['status']='saving'
            草稿['error']=None
        自身.存储.update(写入保存)
        try:
            应答=自身.上下文.remote.settings.mutate(权限设置命名空间,[{'op':'set','path':['defaultPreset'],'value':预设}],视图['revision'])
        finally:
            自身.保存中=False
        if 自身.已拆除:
            return
        if 应答['ok'] is not True:
            自身.失败(应答['error'])
            return
        自身.描述面.接纳视图(应答['value'])

    def 拆除(自身):
        '停止跟随。之后的发布不再改快照'
        自身.已拆除=True
        if 自身.跟随 is not None:
            自身.跟随()
            自身.跟随=None
        if 自身.跟随目录 is not None:
            自身.跟随目录()
            自身.跟随目录=None

    def 推导(自身):
        '从镜像和目录快照写这一行。保存途中不覆盖'
        if 自身.已拆除 or 自身.保存中:
            return
        镜像=自身.描述面.getSnapshot()
        if 镜像['view'] is None:
            if 镜像['error'] is not None:
                自身.失败(Exception(镜像['error']))
            return
        视图=None
        for 行 in 镜像['view']['namespaces']:
            if 行['ns']==权限设置命名空间:
                视图=行
                break
        if 视图 is None:
            def 写入不可用(状态):
                '宿主没有权限设置'
                状态['status']='unavailable'
                状态['writable']=False
                状态['currentValue']=''
                状态['options']=[]
            自身.存储.update(写入不可用)
            return
        try:
            目录值=自身.目录.存储.getSnapshot()['value']
            if 目录值 is None:
                return
            解析=权限默认于(视图,目录值)
            可写=镜像['view']['writable']
            修订=视图['revision']
            def 写入就绪(状态):
                '行可以显示并选择'
                状态['status']='ready'
                状态['error']=None
                状态['writable']=可写
                状态['currentValue']=解析['currentValue']
                状态['options']=解析['options']
                状态['revision']=修订
            自身.存储.update(写入就绪)
        except Exception as 错误:
            自身.失败(错误)

    def 失败(自身,错误):
        '把失败写进行快照。异常取消息，远程信封取 message'
        if isinstance(错误,BaseException):
            文案=str(错误)
        elif isinstance(错误,dict) and 'message' in 错误:
            文案=str(错误['message'])
        else:
            文案=str(错误)
        def 写入(状态):
            '错误态'
            状态['status']='error'
            状态['error']=文案
        自身.存储.update(写入)
