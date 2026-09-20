"""向 invariants 登记客户端模块图自洽检查。"""
包名='@deepseek-ai/dsh-client-modules'
名称='client-modules-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用']

def 安装(上下文,失败):
    """每次扫描触发都检查 graph 与 clientPath 自洽。"""
    def 内部插件(_纤程=None):
        """核对图行是否都能解析到客户端 bundle 路径。"""
        宿主=上下文.获取服务('clientModules')
        if 宿主 is None:
            return
        图=宿主.graph()
        行列表=图['entries'] if 'entries' in 图 else []
        for 行 in 行列表:
            标识=行['id']
            if 宿主.clientPath(标识) is None:
                网址=行['url'] if 'url' in 行 else None
                失败('web 插件图行 "'+str(标识)+'" 广告了 '+str(网址)+' 却解析不到客户端 bundle 路径 — 下发的 __DSH_BOOT__ 拉取会 404')
    上下文.监听('internal/plugin',内部插件,{'global':True})

def 应用(上下文):
    """向 invariants 登记本包检查，返回拆除器。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
