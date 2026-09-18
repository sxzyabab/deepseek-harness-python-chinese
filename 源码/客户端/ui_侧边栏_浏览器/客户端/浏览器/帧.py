from ....存储 import 创建快照存储#快照存储

__all__=['内嵌帧实现']#仅中文公开名

class 内嵌帧实现:#iframe 载体实现
    """独立于 URL 导航持有瞬时 iframe 与沙箱开关状态。"""
    def __init__(自身,沙箱变更,文档已加载):
        """沙箱变更把新策略应用到当前受控目标；文档已加载向导航状态机报告加载。"""
        自身.沙箱变更=沙箱变更#沙箱回调
        自身.文档已加载=文档已加载#加载回调
        自身.存储=创建快照存储({'document':None,'sandboxed':True,'loadFailed':False})#帧状态

    def 取快照(自身):
        """只读渲染快照。"""
        return 自身.存储.getSnapshot()#快照

    def 订阅(自身,监听):
        """订阅 iframe 或沙箱模式变更。"""
        return 自身.存储.subscribe(监听)#拆除器

    def 切换沙箱(自身):
        """切换本标签 occurrence 的沙箱强制。"""
        当前=自身.存储.getSnapshot()#当前
        沙箱=not 当前['sandboxed']#翻转
        自身.存储.set({**当前,'sandboxed':沙箱})#发布
        自身.沙箱变更(沙箱)#应用

    def 设文档(自身,文档):
        """发布控制器准备好的帧。"""
        自身.存储.set({**自身.存储.getSnapshot(),'document':文档,'loadFailed':False})#发布

    def 清文档(自身):
        """移除当前准备帧与瞬时加载失败。"""
        当前=自身.存储.getSnapshot()#当前
        if 当前['document'] is not None:#有文档
            自身.存储.set({**当前,'document':None,'loadFailed':False})#清空

    def 报告已加载(自身,修订):
        """载体报告已加载。"""
        自身.文档已加载(修订)#转发

    def 报告加载失败(自身,修订):
        """载体报告 error。"""
        当前=自身.存储.getSnapshot()#当前
        文档=当前['document']#文档
        if 文档 is None or 文档['revision']!=修订 or 当前['loadFailed']:#无关或已失败
            return#忽略
        自身.存储.set({**当前,'loadFailed':True})#失败

    getSnapshot=取快照#HostObservable 协议槽
    subscribe=订阅#HostObservable 协议槽
