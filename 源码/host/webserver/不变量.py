"""`@deepseek-ai/dsh-host-webserver` 的本包拥有不变量配套。

对齐上游 `webserver/src/invariant.ts`。公开面仅中文名。
HTTP 与 upgrade 路由登记及其 disposer 必须对称。
"""
from cordis.工具 import 已兑现#立刻兑现

包名='@deepseek-ai/dsh-host-webserver'#本包所有权名
名称='host-webserver-invariant'#配套插件名
注入=['invariants']#依赖 invariants

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):#挂到每次插件拆除
    """每次 fiber 拆除时探测登记/拆除是否对称。"""
    def 探测(*剩余):#fiber 拆除时探测
        """在保留路径上做登记/拆除探测。"""
        服务器=上下文对象.get('webServer') if hasattr(上下文对象,'get') else getattr(上下文对象,'webServer',None)#可能未挂
        if 服务器 is None:#本组合没有 webserver
            return#放过
        探测路由={'kind':'exact','path':'/__dsh_invariant_probe__','handler':lambda 请求,响应:None}#HTTP 探测
        try:#两轮登记+立刻 dispose
            服务器.register(探测路由)()#第一轮
            服务器.register(探测路由)()#第二轮；残留则抛
            升级探测={'path':'/__dsh_invariant_upgrade_probe__','handler':lambda 请求,套接字,头:None}#upgrade 探测
            服务器.registerUpgrade(升级探测)()#第一轮
            服务器.registerUpgrade(升级探测)()#第二轮
        except BaseException:#dispose 没清掉
            失败('webServer route disposer left a route registered — route tables and fiber lifecycles diverged')#报不对称
    上下文对象.on('internal/plugin',探测,{'global':True})#全局监听拆除

安装.inject=['webServer']#安装时还要 webServer——探测时再 get

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记
