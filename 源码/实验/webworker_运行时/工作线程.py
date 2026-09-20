from .node.未实现失败 import 运行时错误
from .工作线程宿主 import 创建工作线程宿主

__all__=['安装工作线程入口']

def 安装工作线程入口(
    创建内建=None,
    替换前缀=None,
    请求监听器=None,
    als因果=None,
    在异步上下文根运行=None,
    安装异步上下文钩子=None,
    安装定时器全局=None,
    安装crypto全局=None,
    安装process全局=None,
    是否shell启动帧=None,
    执行shell进程=None,
    自身=None,
):
    """安装消息入口：init 前排队，shell 角色分派，装配后根上下文派发。"""
    if 安装异步上下文钩子 is not None:#在timer全局之前
        安装异步上下文钩子()
    if 安装定时器全局 is not None:
        安装定时器全局()
    if 安装crypto全局 is not None:
        安装crypto全局()
    宿主=[None]
    shell角色=[False]
    排队=[]
    作用域=自身 if 自身 is not None else globals()

    def 收消息(事件):
        """按角色与 init 帧分派。"""
        数据=事件.data#MessageEvent 对象载荷
        if 宿主[0] is None and 是否shell启动帧 is not None and 是否shell启动帧(数据):
            shell角色[0]=True
            if 安装process全局 is not None:
                环境=数据['env'] if 'env' in 数据 else None
                工作目录=数据['cwd'] if 'cwd' in 数据 else None
                安装process全局({'cwd':工作目录,'env':环境})
            if 执行shell进程 is not None:
                执行shell进程(数据,作用域)
            return
        if 宿主[0] is None and isinstance(数据,dict) and 't' in 数据 and 数据['t']=='init':
            if 'image' not in 数据 or not isinstance(数据['image'],str):
                raise 运行时错误('webworker: init 帧需要字符串 image url')
            覆盖层=数据['overlays'] if 'overlays' in 数据 else None
            if not isinstance(覆盖层,list) or any(not isinstance(层,str) for 层 in 覆盖层):
                raise 运行时错误('webworker: init 帧需要字符串 overlay url 列表')
            创建=创建工作线程宿主({
                'staticModules':创建内建() if callable(创建内建) else {},
                'staticModulePrefixes':{} if 替换前缀 is None else 替换前缀,
                'requestListener':请求监听器,
                'alsCausality':als因果,
                'image':数据['image'],
                'overlays':覆盖层,
            })
            宿主[0]=创建
            for 已排 in 排队:
                def 冲刷已排(消=已排,主=创建):
                    """把排队消息交给宿主句柄。"""
                    主['handleMessage'](消)
                if callable(在异步上下文根运行):
                    在异步上下文根运行(冲刷已排)
                else:
                    冲刷已排()
            排队.clear()
            创建['start']()#失败由tunnel.fail报告
            return
        if 宿主[0] is None:
            if shell角色[0]:
                return
            排队.append(数据)
            return
        就绪=宿主[0]
        def 派发():
            """派发消息。"""
            就绪['handleMessage'](数据)
        if callable(在异步上下文根运行):
            在异步上下文根运行(派发)
        else:
            派发()

    加监听=作用域['addEventListener'] if 'addEventListener' in 作用域 else None
    if callable(加监听):
        加监听('message',收消息)
    return 收消息
