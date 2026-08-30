"""可选本地设置文档动作的状态所有者。

对齐上游 `ui-settings-general/src/client/settings-document-store.ts`。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
__all__=['快照仓库','设置文档仓库','已加载则刷新文档']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 错误文案(错误):#拒绝值收成可展示文案
    """Error 取其 message。"""
    return str(错误) if isinstance(错误,Exception) else str(错误)#文案

class 快照仓库:#简易快照仓库
    """标题栏动作共用的状态源。"""
    def __init__(自身,初值):#播种
        """记下初值。"""
        自身.状态=dict(初值)#状态
        自身.监听者=set()#订阅者

    def getSnapshot(自身):#读快照
        """返回当前状态。"""
        return 自身.状态#状态

    def subscribe(自身,回调):#订阅
        """登记变更回调。"""
        自身.监听者.add(回调)#加入
        def 退订():#退订
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def update(自身,变换):#就地变换并通知
        """调用变换(state)。"""
        变换(自身.状态)#变换
        for 回调 in list(自身.监听者):#通知
            回调()#触发

class 设置文档仓库:#设置文档状态所有者
    """加载本地文档是否可用，并调用无路径的宿主打开操作。"""
    def __init__(自身,接口):#注入 settings API
        """空闲快照。"""
        自身.接口=接口#settings 面
        自身.store=快照仓库({'status':'idle','opening':False,'error':None})#快照
        自身.世代=0#在飞请求世代

    def load(自身):#拉元数据并填仓库
        """最新请求胜出。"""
        自身.世代+=1#抬世代
        世代=自身.世代#本请求
        def 标加载(态):#loading
            """标 loading。"""
            态['status']='loading'#加载中
            态['error']=None#清错误
        自身.store.update(标加载)#写入
        try:#describe
            应答=解开(自身.接口.settings.describe({}))#描述
            if 世代!=自身.世代:#过期
                return#丢弃
            结果=取字段(应答,'result')#业务结果
            if not 取字段(结果,'ok'):#业务失败
                def 写成不可用(态):#不可用
                    """记下业务错误。"""
                    态['status']='unavailable'#不可用
                    态['error']=取字段(取字段(结果,'error'),'message')#错误
                自身.store.update(写成不可用)#写入
                return#结束
            有文档=bool(取字段(取字段(结果,'value'),'hasDocument'))#是否有文档
            def 写结果(态):#就绪或不可用
                """按是否有文档写入。"""
                态['status']='ready' if 有文档 else 'unavailable'#状态
                态['error']=None#清错误
            自身.store.update(写结果)#写入
        except Exception as 错误:#传输失败
            if 世代!=自身.世代:#过期
                return#丢弃
            def 写失败(态):#不可用
                """记下失败。"""
                态['status']='unavailable'#不可用
                态['error']=错误文案(错误)#文案
            自身.store.update(写失败)#写入

    def open(自身):#打开已加载文档
        """并发手势并入在飞。"""
        当前=自身.store.getSnapshot()#当前
        if 取字段(当前,'status')!='ready' or 取字段(当前,'opening'):#未就绪或已在打开
            return#忽略
        def 标打开(态):#opening
            """标 opening。"""
            态['opening']=True#打开中
            态['error']=None#清错误
        自身.store.update(标打开)#写入
        try:#openDocument
            应答=解开(自身.接口.settings.openDocument({}))#无路径打开
            结果=取字段(应答,'result')#业务结果
            if not 取字段(结果,'ok'):#业务失败
                raise Exception(取字段(取字段(结果,'error'),'message'))#抛
        except Exception as 错误:#打开失败
            def 写错(态):#记下失败
                """记下失败文案。"""
                态['error']=错误文案(错误)#文案
            自身.store.update(写错)#写入
        finally:#清 opening
            def 清打开(态):#清
                """打开不再在飞。"""
                态['opening']=False#结束
            自身.store.update(清打开)#写入

def 已加载则刷新文档(控制器):#已请求过才重拉
    """idle 则跳过。"""
    if 控制器 is None:#无
        return#跳过
    if 取字段(控制器.store.getSnapshot(),'status')=='idle':#尚未打开
        return#跳过
    控制器.load()#刷新
