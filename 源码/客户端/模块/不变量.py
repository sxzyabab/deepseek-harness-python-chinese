包名='@deepseek-ai/dsh-client-modules'#本包的不变量所有权名
名称='client-modules-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 安装(上下文对象,失败):
    """每次扫描触发都检查 graph 与 clientPath 自洽。"""
    def 内部插件(_光纤=None):
        """核对图行路径。"""
        宿主=上下文对象.获取服务('clientModules')#可选客户端模块宿主
        if 宿主 is None:
            return#无物可审计
        图=宿主.graph()#当前图
        行列表=图['entries'] if 'entries' in 图 else []#图行
        for 行 in 行列表:
            标识=行['id']#行 id
            if 宿主.clientPath(标识) is None:
                网址=行['url'] if 'url' in 行 else None#广告 URL
                失败('web plugin graph row "'+str(标识)+'" advertises '+str(网址)+' but resolves no client bundle path — the served __DSH_BOOT__ would 404 on fetch')#报告图自洽失败
    上下文对象.监听('internal/plugin',内部插件,{'global':True})#全局监听

def 应用(上下文对象):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#同步登记

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
