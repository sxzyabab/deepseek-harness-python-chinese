"""盖在 ApiProxy 拥有的宿主端点上的 Web 会话日志下载命令。对齐上游 `@deepseek-ai/dsh-session-log-export`。"""
from ...依赖 import cordis#外部依赖胶水

名称='session-log-download'#Cordis插件名（字面量）
注入=['commands']#依赖命令注册表

已请求={'kind':'success','text':'Session log download requested.'}#浏览器插件观察的成功结算

__all__=['名称','注入','应用','apply']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否thenable(值):#判定可等待对象
    """判定值是否可等待。"""
    if 值 is None:#空不是
        return False#不是
    return callable(getattr(值,'wait',None)) or callable(getattr(值,'等待',None))#Future或thenable

def 已兑现(值=None):#立刻兑现的操作任务
    """把值包成立即兑现的 thenable。"""
    class _任务:#同步任务
        def wait(自身,超时=None):#阻塞等待
            return 值#原样返回
        def 等待(自身,超时=None):#中文别名
            return 值#原样返回
    return _任务()#已完成

def 应用(上下文):#登记/export命令
    """登记仅 Web 的 `/export` 命令，由浏览器下载插件观察。"""
    def 挂上():#以effect登记
        """登记 export 命令并在拆除时注销。"""
        def 处理(调用):#命令处理
            """无参数才请求下载。"""
            原始=取字段(调用,'rawInput','').strip()#原始输入
            if 原始=='':#无参数
                return 已兑现(已请求)#请求下载
            return 已兑现({'kind':'error','text':'The Web /export command does not accept a path.'})#拒绝路径
        释放=上下文.commands.register({'name':'export','description':'Download this Session log as a ZIP archive','handler':处理})#登记命令
        return 释放#拆除器
    上下文.effect(挂上,'session-log-download: command')#effect标签

apply=应用#Cordis插件入口
