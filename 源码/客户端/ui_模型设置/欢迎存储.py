"""欢迎提示状态；浏览器可用宿主设置时持久保存。

对齐上游 `ui-settings-models/src/client/welcome-store.ts`。公开面仅中文名。
"""
from .引导文案 import 欢迎通知设置命名空间,欢迎通知确认字段,欢迎通知版本#引导常量
from .存储 import 快照存储,错误文案,模型设置错误#共用快照与文案

__all__=['欢迎通知存储','已加载则刷新欢迎']#仅中文公开名

def 确认值于(视图):
    """字符串才算确认版本。"""
    值=视图['value'] if 'value' in 视图 else None#值
    if not isinstance(值,dict):#非对象
        return None#无
    确认=值[欢迎通知确认字段] if 欢迎通知确认字段 in 值 else None#确认字段
    return 确认 if isinstance(确认,str) else None#版本

class 欢迎通知存储:
    """协调持久的宿主确认，或远程浏览器的进程内回退。"""
    def __init__(自身,接口,持久化='host'):
        """空闲快照。"""
        自身.接口=接口#settings
        自身.持久化=持久化#host 或 memory
        自身.存储=快照存储({'status':'idle','acknowledged':False,'error':None})#快照
        自身.世代=0#在飞请求世代

    def load(自身):
        """内存模式直接就绪。"""
        自身.世代+=1#抬世代
        世代=自身.世代#本请求
        if 自身.持久化=='memory':#进程内
            def 写就绪(态):
                """保留确认。"""
                态['status']='ready'#就绪
                态['error']=None#清错误
            自身.存储.update(写就绪)#写入
            return#结束
        def 标加载(态):
            """标 loading。"""
            态['status']='loading'#加载中
            态['error']=None#清错误
        自身.存储.update(标加载)#写入
        try:#describe
            应答=自身.接口.settings.describe({}).等待()#描述
            结果=应答['result']#业务结果
            if not 结果['ok']:#失败
                错误体=结果['error'] if 'error' in 结果 else None#错误
                raise 模型设置错误(错误体['message'] if 错误体 is not None and 'message' in 错误体 else None)#抛
            值=结果['value'] if 'value' in 结果 else None#值
            视图表=值['namespaces'] if 值 is not None and 'namespaces' in 值 and 值['namespaces'] is not None else []#命名空间
            视图=None#欢迎 ns
            for 候选 in 视图表:#找
                if 'ns' in 候选 and 候选['ns']==欢迎通知设置命名空间:#命中
                    视图=候选#记下
                    break#找到
            if 视图 is None:#缺失
                raise 模型设置错误('welcome acknowledgement settings are unavailable')#抛
            if 世代!=自身.世代:#过期
                return#丢弃
            def 写结果(态):
                """确认值是否等于当前文案版本。"""
                态['status']='ready'#就绪
                态['acknowledged']=确认值于(视图)==欢迎通知版本#已确认
                态['error']=None#清错误
            自身.存储.update(写结果)#写入
        except Exception as 错误:#失败；RPC 异常契约未定
            if 世代!=自身.世代:#过期
                return#丢弃
            def 写失败(态):
                """未确认。"""
                态['status']='error'#失败
                态['acknowledged']=False#未确认
                态['error']=错误文案(错误)#文案
            自身.存储.update(写失败)#写入

    def acknowledge(自身):
        """选定的持久化模式接受确认时为 True。"""
        自身.世代+=1#抬世代
        世代=自身.世代#本请求
        if 自身.持久化=='memory':#进程内
            def 写确认(态):
                """本进程已确认。"""
                态['status']='ready'#就绪
                态['acknowledged']=True#确认
                态['error']=None#清错误
            自身.存储.update(写确认)#写入
            return True#接受
        def 标保存(态):
            """标 saving。"""
            态['status']='saving'#保存中
            态['error']=None#清错误
        自身.存储.update(标保存)#写入
        try:#mutate
            应答=自身.接口.settings.mutate({
                'ns':欢迎通知设置命名空间,#命名空间
                'ops':[{'op':'set','path':[欢迎通知确认字段],'value':欢迎通知版本}],#设版本
            }).等待()#结束
            结果=应答['result']#业务
            if not 结果['ok']:#失败
                错误体=结果['error'] if 'error' in 结果 else None#错误
                raise 模型设置错误(错误体['message'] if 错误体 is not None and 'message' in 错误体 else None)#抛
            if 世代==自身.世代:#仍最新
                def 写成功(态):
                    """宿主接受。"""
                    态['status']='ready'#就绪
                    态['acknowledged']=True#确认
                    态['error']=None#清错误
                自身.存储.update(写成功)#写入
            return True#接受
        except Exception as 错误:#失败；RPC 异常契约未定
            if 世代==自身.世代:#仍最新
                def 写失败(态):
                    """未确认。"""
                    态['status']='error'#失败
                    态['acknowledged']=False#未确认
                    态['error']=错误文案(错误)#文案
                自身.存储.update(写失败)#写入
            return False#未接受

def 已加载则刷新欢迎(控制器):
    """idle 则跳过。"""
    if 控制器.存储.getSnapshot()['status']=='idle':#尚未打开
        return#跳过
    控制器.load()#刷新
