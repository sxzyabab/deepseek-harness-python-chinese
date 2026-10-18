'预览的读取面：分页、整文件、以及渲染器自己的加载'
from ...ui_侧边栏_右侧.客户端.标签域 import 中止信号
from .文档.资源组 import 资源组

__all__=['文本面']

def 已中止(信号):
    '信号是否已中止'
    if 信号 is None:
        return False
    if getattr(信号,'aborted',False):
        return True
    return False

def 文本面(读取,完整读取,资源):
    '把预览面绑到一份分页读、完整字节读与资源组。槽位上的会话标识不用，地址自带会话'
    def 工厂(会话标识,动作):
        '每个标签一份读取世代。第一次读取才挂上 abort，用来忘掉桶'
        标签表={}
        def 读取们(标签标识,信号):
            '没有就创建，并在标签结束时忘掉'
            已有=标签表.get(标签标识)
            if 已有 is not None:
                return 已有
            def 资源变了():
                '依赖变了'
                动作['resourceChanged'](标签标识)
            创建={
                'generation':0,
                'version':None,
                'mode':'text-pages',
                'group':资源组(资源,资源变了),
            }
            标签表[标签标识]=创建
            def 中止时():
                '忘掉桶和这份记账'
                控制器=创建.get('controller')
                if 控制器 is not None:
                    控制器.abort()
                创建['group'].关闭()
                if 标签标识 in 标签表:
                    del 标签表[标签标识]
                动作['forget'](标签标识)
            信号.addEventListener('abort',中止时,{'once':True})
            return 创建
        def 模式于(标签标识,信号,模式,渲染器标识=None):
            '模式或实现变了就作废在途读取并清空页'
            读取记录=读取们(标签标识,信号)
            原渲染器=读取记录.get('rendererId')
            if 读取记录['mode']!=模式 or 原渲染器!=渲染器标识:
                控制器=读取记录.get('controller')
                if 控制器 is not None:
                    控制器.abort()
                if 渲染器标识 is None:
                    if 'rendererId' in 读取记录:
                        del 读取记录['rendererId']
                else:
                    读取记录['rendererId']=渲染器标识
                读取记录['mode']=模式
                读取记录['generation']=读取记录['generation']+1
                读取记录['version']=None
                动作['reset'](标签标识)
            return 读取记录
        def 读页(标签标识,文件,偏移,信号,观察版本=None):
            '读一页进存储。较新版本出现在第一行之后就从头再走'
            if 已中止(信号):
                return
            读取记录=模式于(标签标识,信号,'text-pages')
            世代=读取记录['generation']
            动作['loading'](标签标识,'text-pages',观察版本)
            结果=读取(文件['sessionId'],文件['path'],偏移,信号).等待()
            if 已中止(信号) or 读取记录['generation']!=世代:
                return
            if not 结果['ok']:
                动作['failed'](标签标识,结果['error'])
                return
            值=结果['value']
            if 偏移!=1 and 读取记录['version'] is not None and 值['version']!=读取记录['version']:
                重开(标签标识,文件,信号,观察版本)
                return
            读取记录['version']=值['version']
            动作['page'](标签标识,值)
        def 读全部(标签标识,文件,信号,观察版本=None):
            '为整文件渲染器读完整字节'
            if 已中止(信号):
                return
            读取记录=模式于(标签标识,信号,'bytes-complete')
            旧控制器=读取记录.get('controller')
            if 旧控制器 is not None:
                旧控制器.abort()
            控制器=中止信号()
            读取记录['controller']=控制器
            def 父中止():
                '标签结束时一并中止这次整文件读取'
                控制器.abort()
            信号.addEventListener('abort',父中止,{'once':True})
            动作['loading'](标签标识,'bytes-complete',观察版本)
            try:
                结果=完整读取(文件,控制器).等待()
            except Exception as 错误:
                if 已中止(控制器):
                    return
                动作['failed'](标签标识,{
                    'name':'RemoteError',
                    'isDSHRemoteError':True,
                    'code':'gateway/internal',
                    'message':str(错误),
                    'details':{},
                })
                return
            if 已中止(控制器):
                return
            if not 结果['ok']:
                动作['failed'](标签标识,结果['error'])
                return
            文件结果=结果['value']
            读取记录['version']=文件结果['version']
            动作['complete'](标签标识,文件结果)
        def 重开(标签标识,文件,信号,观察版本=None,模式='text-pages'):
            '丢掉页并从第一行或整文件再读'
            if 已中止(信号):
                return
            读取记录=读取们(标签标识,信号)
            控制器=读取记录.get('controller')
            if 控制器 is not None:
                控制器.abort()
            读取记录['generation']=读取记录['generation']+1
            读取记录['version']=None
            动作['reset'](标签标识)
            if 模式=='text-pages':
                读页(标签标识,文件,1,信号,观察版本)
            else:
                读全部(标签标识,文件,信号,观察版本)
        def 加资源(标签标识,地址,信号):
            '观察一个渲染器依赖'
            if not 已中止(信号):
                读取们(标签标识,信号)['group'].添加(地址)
        def 设资源(标签标识,地址列表,信号):
            '换成这一组依赖'
            if not 已中止(信号):
                读取们(标签标识,信号)['group'].设置(地址列表)
        def 准备渲染器(标签标识,信号,渲染器标识,观察版本=None,重载=False):
            '渲染器自己加载，不读源字节'
            if 已中止(信号):
                return
            模式于(标签标识,信号,'renderer',渲染器标识)
            if 重载:
                动作['reset'](标签标识)
            动作['loading'](标签标识,'renderer',观察版本,渲染器标识)
        def 重载全部(标签标识,文件,信号,观察版本=None):
            '丢掉旧的完整结果再读'
            重开(标签标识,文件,信号,观察版本,'bytes-complete')
        return {
            'addResource':加资源,
            'setResources':设资源,
            'loadPage':读页,
            'reloadPages':重开,
            'loadAll':读全部,
            'prepareRenderer':准备渲染器,
            'reloadAll':重载全部,
        }
    return 工厂
