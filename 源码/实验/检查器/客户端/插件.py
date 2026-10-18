'把浏览器观察直接发到检查器 Worker 的 Client 插件'
import threading
from ..共享.网页 import 检查器引导路由
from ..共享.桥接.控制编解码 import 解析检查器客户端引导
from ..共享.服务 import 创建检查器服务
from ..共享.处置 import 处置检查器资源
from .检视.cordis import 发布cordis树
from .桥接.控制器 import 启动检查器客户端
from .底栏.页 import 登记检查器页

__all__=['应用','名称','依赖']

名称='experimental-inspector'
依赖=[]


def 取窗口(上下文):
    '这次握手传进来的窗口。文档在模块系统上，窗口是它的 defaultView'
    return 上下文.加载器.内部加载器.文档.defaultView


class 检查器客户端会话:
    '拥有当前源和树发布，直到换源或外层寿命拆除'
    def __init__(自身,上下文,窗口):
        '记下上下文和传进来的窗口。传输失败留给 connection/reset 重试'
        自身.上下文=上下文
        自身.窗口=窗口
        自身.寿命=窗口.AbortController()
        自身.锁=threading.Lock()
        自身.引导=None
        自身.释放=None

    def 刷新(自身):
        '重新读取引导并换源'
        with 自身.锁:
            自身.寿命.signal.throwIfAborted()
            自身._读引导()

    def 连接(自身,引导):
        '用已经解析的引导换源'
        with 自身.锁:
            自身.寿命.signal.throwIfAborted()
            自身._替换(引导)

    def _读引导(自身):
        '这个网页引擎不再通过浏览器读取引导'
        自身._连接失败(RuntimeError('这个网页引擎不再通过浏览器请求宿主 '+检查器引导路由))

    def _连接失败(自身,错误):
        '寿命已中止就不再记。否则警告，留给重连或刷新'
        if 自身.寿命.signal.aborted:
            return
        自身.上下文.日志.警告(
            'experimental-inspector: Client connection failed; reconnect or reload the page to retry',
            错误,
        )

    def _替换(自身,引导):
        '端点或协议变了才拆掉旧源并装上新源'
        自身.寿命.signal.throwIfAborted()
        已有=自身.引导
        if 已有 is not None and 已有.get('endpoint')==引导.get('endpoint') and 已有.get('protocol')==引导.get('protocol'):
            return
        if 自身.释放 is not None:
            自身.释放()
            自身.释放=None
        自身.引导=None
        try:
            源=启动检查器客户端(引导,自身.窗口)
        except Exception as 错误:
            自身._连接失败(错误)
            return
        清理列表=[]

        def 关闭源():
            '关闭这一份 Client 源'
            源.关闭()

        def 拆除():
            '反序拆除登记，再关闭源'
            处置检查器资源(清理列表,关闭源,'experimental-inspector: Client disposal failed')

        try:
            自身.寿命.signal.throwIfAborted()
            清理列表.append(发布cordis树(自身.上下文,源,{
                'maxNodes':引导['maxCordisNodes'],
                'maxBytes':引导['maxFrameBytes']-4096,
            }))
            清理列表.append(自身.上下文.提供服务('inspector',创建检查器服务(源)))

            def 等槽(槽上下文):
                '槽位、快捷键和文案就绪后再登记底栏'
                登记检查器页(槽上下文,源.领域源.sourceId)

            纤程=自身.上下文.依赖启动(['slots','shortcuts','locale'],等槽)

            def 拆底栏():
                '拆掉底栏登记'
                纤程.拆除()

            清理列表.append(拆底栏)
        except Exception as 错误:
            try:
                拆除()
            except Exception as 回滚错误:
                自身.上下文.日志.错误('experimental-inspector: Client initialization rollback failed',回滚错误)
            raise 错误
        自身.引导=引导
        自身.释放=拆除

    def 拆除(自身):
        '中止寿命，等当前替换结束，再拆源'
        自身.寿命.abort()
        with 自身.锁:
            if 自身.释放 is not None:
                自身.释放()
                自身.释放=None


def 应用(上下文,配置=None):
    '挂载 Client 源。页面已经加载后再激活也一样。不在这里调用别的包入口'
    窗口=取窗口(上下文)#这次握手的窗口
    会话=检查器客户端会话(上下文,窗口)

    def 寿命():
        '插件拆除时拆掉会话'
        def 卸():
            '拆会话'
            会话.拆除()
        return 卸

    上下文.副作用(寿命,'experimental-inspector: Client lifetime')

    def 重置():
        '连接重置后重读引导。失败只警告'
        try:
            会话.刷新()
        except Exception as 错误:
            上下文.日志.警告(
                'experimental-inspector: Client connection failed; reconnect or reload the page to retry',
                错误,
            )

    上下文.监听('connection/reset',重置)
    注入=getattr(窗口,'__DSH_INSPECTOR__',None)
    if 注入 is not None:#宿主已经把引导放进页面
        会话.连接(解析检查器客户端引导(注入))


name=名称
inject=依赖
apply=应用
