"""`@deepseek-ai/dsh-client-modules` 的本包拥有不变量配套。

对齐上游 `modules/src/invariant.ts`。公开面仅中文名。
拥有关系：节点半边的启动条目图必须自洽。
"""
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-client-modules'#本包的不变量所有权名
名称='client-modules-invariant'#配套不变量插件名（字面量）
注入=['invariants']#依赖 invariants 服务

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 安装(上下文对象,失败):#安装图行必须能解析打包路径的检查
    """每次扫描触发都检查 graph 与 clientPath 自洽。"""
    def 内部插件(_光纤=None):#每次插件光纤构造或拆除
        """核对图行路径。"""
        宿主=上下文对象.get('clientModules')#可选客户端模块宿主
        if 宿主 is None:#浏览器半边 / 没有节点半边
            return#无物可审计
        图=宿主.graph()#当前图
        for 行 in 取字段(图,'entries',[]):#逐行核对
            标识=取字段(行,'id')#行 id
            if 宿主.clientPath(标识) is None:#广告了 URL 却解析不出路径
                失败('web plugin graph row "'+str(标识)+'" advertises '+str(取字段(行,'url'))+' but resolves no client bundle path — the served __DSH_BOOT__ would 404 on fetch')#报告图自洽失败
    上下文对象.on('internal/plugin',内部插件,{'global':True})#全局监听

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺
