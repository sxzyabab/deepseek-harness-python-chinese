'宿主上比较公开 npm 源的应答。客户端自己决定最初选哪一个'
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse,urlunparse
from ...依赖.schemastery import 布尔字段,正整数字段,自然数字段
from ...工具.超时 import 定时器延迟上限毫秒
from ...类型化远程调用.协议 import 远程,远程服务
from . import 客户端

__all__=['客户端','插件注册表探测','配置']

配置={
    'registryProbeEnabled':布尔字段(默认值=True),
    'registryProbeTimeoutMs':正整数字段(默认值=1500,最小=1,最大=定时器延迟上限毫秒),
    'registryProbeCacheTtlMs':自然数字段(默认值=300000),
}
Config=配置

探测端点=(
    'https://registry.npmjs.org/-/ping',
    'https://registry.npmmirror.com/-/ping',
)

class 拒绝重定向(urllib.request.HTTPRedirectHandler):
    '重定向即失败，对齐 fetch 的 redirect error'
    def redirect_request(自身,请求,响应,码,消息,头,新址):
        '不跟随重定向'
        raise urllib.error.HTTPError(请求.full_url,码,消息,头,None)

打开器=urllib.request.build_opener(拒绝重定向())

def 取配置(配置值,键,缺省):
    '配置缺席时用模式里的缺省'
    if not isinstance(配置值,dict) or 键 not in 配置值:
        return 缺省
    return 配置值[键]

def 根网址(端点):
    'ping 地址对应的注册表根'
    解析=urlparse(端点)
    return urlunparse((解析.scheme,解析.netloc,'/','','',''))

class 插件注册表探测(远程服务):
    '在宿主上比公开注册表的 HTTPS 应答。客户端拥有最初的选择'
    Config=配置
    def __init__(自身,上下文,配置值=None):
        '记下期限和缓存，卸载时中止还在飞的探测'
        super().__init__(上下文,'pluginRegistryProbe')
        自身.启用=取配置(配置值,'registryProbeEnabled',True) is not False
        自身.超时毫秒=取配置(配置值,'registryProbeTimeoutMs',1500)
        自身.缓存毫秒=取配置(配置值,'registryProbeCacheTtlMs',300000)
        自身.已中止=False
        自身.进行中=None
        自身.缓存=None
        自身.锁=threading.Lock()
        def 登记寿命():
            '卸载时中止，并等这次探测结束'
            def 清理():
                '中止寿命，并等共享的那次探测'
                自身.已中止=True
                进行=自身.进行中
                if 进行 is not None:
                    进行['事件'].wait()
            return 清理
        上下文.副作用(登记寿命)

    @远程('fastest')
    def 最快(自身):
        '并行探测 npm 与 npmmirror。并发读者共用一次探测。已卸载则拒绝'
        if 自身.已中止:
            raise RuntimeError('The operation was aborted')
        if 自身.启用 is not True:
            return None
        现在=time.time()*1000
        if 自身.缓存 is not None and 自身.缓存['expiresAt']>现在:
            return 自身.缓存['registry']
        with 自身.锁:
            if 自身.进行中 is None:
                盒={'事件':threading.Event(),'结果':None,'错误':None}
                自身.进行中=盒
                启动=True
            else:
                盒=自身.进行中
                启动=False
        if 启动:
            try:
                盒['结果']=自身.探测()
            except Exception as 错误:
                盒['错误']=错误
            finally:
                with 自身.锁:
                    自身.进行中=None
                盒['事件'].set()
        else:
            盒['事件'].wait()
        if 盒['错误'] is not None:
            raise 盒['错误']
        return 盒['结果']

    def 探测(自身):
        '谁先成功用谁。另一个请求结束后关掉响应体'
        完成=threading.Event()
        盒={'注册表':None,'锁':threading.Lock()}
        超时秒=自身.超时毫秒/1000
        def 探(端点):
            '请求一个 ping。成功则记下注册表根'
            if 自身.已中止 or 完成.is_set():
                return
            try:
                请求=urllib.request.Request(端点,method='GET')
                响应=打开器.open(请求,timeout=超时秒)
            except Exception:
                return
            try:
                状态=响应.status
                if 状态>=200 and 状态<300:
                    with 盒['锁']:
                        if 盒['注册表'] is None:
                            盒['注册表']=根网址(端点)
                            完成.set()
            finally:
                响应.close()
        线程=[]
        for 端点 in 探测端点:
            线=threading.Thread(target=探,args=(端点,))
            线.start()
            线程.append(线)
        完成.wait(超时秒)
        完成.set()
        for 线 in 线程:
            线.join()
        if 自身.已中止 is not True:
            自身.缓存={'registry':盒['注册表'],'expiresAt':time.time()*1000+自身.缓存毫秒}
        return 盒['注册表']
