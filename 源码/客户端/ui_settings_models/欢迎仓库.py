"""欢迎提示状态；浏览器可用宿主设置时持久保存。

对齐上游 `ui-settings-models/src/client/welcome-store.ts`。公开面仅中文名。
"""
from cordis.工具 import 是否thenable#可等待判定
from .引导文案 import 欢迎通知设置命名空间,欢迎通知确认字段,欢迎通知版本#引导常量
from .仓库 import 快照仓库,错误文案#共用快照与文案

__all__=['欢迎通知仓库','已加载则刷新欢迎']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
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

def 确认值于(视图):#从命名空间视图取出确认值
    """字符串才算确认版本。"""
    值=取字段(视图,'value')#值
    if not isinstance(值,dict):#非对象
        return None#无
    确认=值.get(欢迎通知确认字段)#确认字段
    return 确认 if isinstance(确认,str) else None#版本

class 欢迎通知仓库:#欢迎提示状态所有者
    """协调持久的宿主确认，或远程浏览器的进程内回退。"""
    def __init__(自身,接口,持久化='host'):#注入 API 与持久化模式
        """空闲快照。"""
        自身.接口=接口#settings
        自身.持久化=持久化#host 或 memory
        自身.store=快照仓库({'status':'idle','acknowledged':False,'error':None})#快照
        自身.世代=0#在飞请求世代

    def load(自身):#拉确认并填仓库
        """内存模式直接就绪。"""
        自身.世代+=1#抬世代
        世代=自身.世代#本请求
        if 自身.持久化=='memory':#进程内
            def 写就绪(态):#就绪
                """保留确认。"""
                态['status']='ready'#就绪
                态['error']=None#清错误
            自身.store.update(写就绪)#写入
            return#结束
        def 标加载(态):#loading
            """标 loading。"""
            态['status']='loading'#加载中
            态['error']=None#清错误
        自身.store.update(标加载)#写入
        try:#describe
            应答=解开(自身.接口.settings.describe({}))#描述
            结果=取字段(应答,'result')#业务结果
            if not 取字段(结果,'ok'):#失败
                raise Exception(取字段(取字段(结果,'error'),'message'))#抛
            视图=None#欢迎 ns
            for 候选 in 取字段(取字段(结果,'value'),'namespaces') or []:#找
                if 取字段(候选,'ns')==欢迎通知设置命名空间:#命中
                    视图=候选#记下
                    break#找到
            if 视图 is None:#缺失
                raise Exception('welcome acknowledgement settings are unavailable')#抛
            if 世代!=自身.世代:#过期
                return#丢弃
            def 写结果(态):#就绪
                """确认值是否等于当前文案版本。"""
                态['status']='ready'#就绪
                态['acknowledged']=确认值于(视图)==欢迎通知版本#已确认
                态['error']=None#清错误
            自身.store.update(写结果)#写入
        except Exception as 错误:#失败
            if 世代!=自身.世代:#过期
                return#丢弃
            def 写失败(态):#错误
                """未确认。"""
                态['status']='error'#失败
                态['acknowledged']=False#未确认
                态['error']=错误文案(错误)#文案
            自身.store.update(写失败)#写入

    def acknowledge(自身):#写入确认或进程内推进
        """选定的持久化模式接受确认时为 True。"""
        自身.世代+=1#抬世代
        世代=自身.世代#本请求
        if 自身.持久化=='memory':#进程内
            def 写确认(态):#已确认
                """本进程已确认。"""
                态['status']='ready'#就绪
                态['acknowledged']=True#确认
                态['error']=None#清错误
            自身.store.update(写确认)#写入
            return True#接受
        def 标保存(态):#saving
            """标 saving。"""
            态['status']='saving'#保存中
            态['error']=None#清错误
        自身.store.update(标保存)#写入
        try:#mutate
            应答=解开(自身.接口.settings.mutate({#写入确认字段
                'ns':欢迎通知设置命名空间,#命名空间
                'ops':[{'op':'set','path':[欢迎通知确认字段],'value':欢迎通知版本}],#设版本
            }))#结束
            if not 取字段(取字段(应答,'result'),'ok'):#失败
                raise Exception(取字段(取字段(取字段(应答,'result'),'error'),'message'))#抛
            if 世代==自身.世代:#仍最新
                def 写成功(态):#已确认
                    """宿主接受。"""
                    态['status']='ready'#就绪
                    态['acknowledged']=True#确认
                    态['error']=None#清错误
                自身.store.update(写成功)#写入
            return True#接受
        except Exception as 错误:#失败
            if 世代==自身.世代:#仍最新
                def 写失败(态):#错误
                    """未确认。"""
                    态['status']='error'#失败
                    态['acknowledged']=False#未确认
                    态['error']=错误文案(错误)#文案
                自身.store.update(写失败)#写入
            return False#未接受

def 已加载则刷新欢迎(控制器):#已离开 idle 才重拉
    """idle 则跳过。"""
    if 取字段(控制器.store.getSnapshot(),'status')=='idle':#尚未打开
        return#跳过
    控制器.load()#刷新
