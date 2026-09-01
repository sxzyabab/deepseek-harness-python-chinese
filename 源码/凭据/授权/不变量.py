"""`@deepseek-ai/dsh-authorization` 的本包拥有不变量配套。"""
from ...依赖 import cordis#外部依赖胶水
包名='@deepseek-ai/dsh-authorization'#本包的不变量所有权名
名称='authorization-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 安装(上下文对象,失败):#安装单次飞行释放契约
    """settled 时键必须已释放，否则后续 begin 永远被拒绝。"""
    def 已结算(键,*_):#监听 settled
        """检查 inFlight 是否已清。"""
        授权=上下文对象.get('authorization') if hasattr(上下文对象,'get') else getattr(上下文对象,'authorization',None)#服务
        if 授权 is None:#服务已拆
            失败('authorization/settled for "'+str(键)+'" emitted without a live authorization service')#无服务
            return#结束
        条目=授权.描述(键)#查条目
        if 条目 is not None and 取字段(条目,'inFlight') is True:#仍占槽
            失败('authorization/settled for "'+str(键)+'" left the key in flight, wedging every later attempt')#卡死
    上下文对象.on('authorization/settled',已结算)#挂监听

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记
