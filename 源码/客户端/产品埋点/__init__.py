'仅桌面的埋点远程调用与实时压缩采集'
import threading
from ...基础设施.通用工具.时间工具 import 当前毫秒
from ...类型化远程调用.协议 import 远程,远程服务
from ...依赖.schemastery import 布尔字段,字符串字段

__all__=['依赖','配置','应用','产品埋点','远程贡献']

依赖=['deepseekAccount','productTelemetry']

配置={
    'enabled':布尔字段(默认值=True),
    'appVersion':字符串字段(可空=True),
}

def 读易失(字段):
    '字典、列表和字符串本身就是值；只有其余对象的 get 才是易失读取'
    if isinstance(字段,(dict,list,str,bytes,bytearray,bool,int,float)) or 字段 is None:
        return 字段
    取值=getattr(字段,'get',None)
    if callable(取值):
        return 取值()
    return 字段

def 取配置(配置值,键,缺省):
    '配置缺席用缺省'
    if not isinstance(配置值,dict) or 键 not in 配置值:
        return 缺省
    return 配置值[键]

class 产品埋点(远程服务):
    '已认证的事件入口；关闭后不读身份，也不收新事件'
    def __init__(自身,上下文,配置值=None):
        '登记 productAnalytics，关掉设置自动写入，并采集压缩开始'
        super().__init__(上下文,'productAnalytics')
        自身.上下文=上下文
        自身.配置值={} if 配置值 is None else 配置值
        自身.活动中=True
        自身._更新=threading.Event()

        def 拆除效果():
            '卸载后停收，并叫醒策略流'
            def 清理():
                '标停并通知订阅'
                自身.活动中=False
                自身._更新.set()
            return 清理
        上下文.副作用(拆除效果)

        def 易失更新(*参数):
            '实时配置变更后重发策略'
            自身._更新.set()
        上下文.监听('loader/volatile-update',易失更新)

        def 接线(子上下文):
            '有 settings 才关掉自动呈现'
            def 挂():
                'auto:false 绑到本纤程'
                return 子上下文.settings.configure({'auto':False},上下文.纤程)
            子上下文.副作用(挂)
        上下文.依赖启动(['settings'],接线)

        def 会话事件(会话,事件):
            '只上报压缩开始，不重放历史'
            if not isinstance(事件,dict) or 事件.get('type')!='compaction/start':
                return
            数据=事件.get('data') if isinstance(事件.get('data'),dict) else {}
            自身.report({
                'eventName':'context_compression',
                'timestamp':当前毫秒(),
                'attributes':{
                    'session_id':会话.id,
                    'trigger_type':'manual' if 数据.get('turn') is None else 'auto',
                },
            })
        上下文.监听('session/event',会话事件)

    def 已启用(自身):
        '当前宿主是否接受桌面埋点'
        return 自身.活动中 and bool(读易失(取配置(自身.配置值,'enabled',True)))

    @远程
    def enabled(自身):
        '读采集策略'
        return 自身.已启用()

    @远程({'mode':'stream'})
    def watchPolicy(自身,signal):
        '先给当前策略，实时配置变更后再给，直到取消或服务拆除'
        while 自身.活动中 and not getattr(signal,'aborted',False):
            yield 自身.enabled()
            自身._更新.clear()
            if getattr(signal,'aborted',False) or not 自身.活动中:
                return
            自身._更新.wait()

    @远程
    def report(自身,事件):
        '提交选定桌面字段；缺身份就省略，不新造。本地提交后即返回，不等送达'
        if not 自身.已启用():
            return
        try:
            try:
                身份=自身.上下文.deepseekAccount.获取设备身份()
            except Exception:
                身份=None
            if hasattr(身份,'然后'):
                def 送出(值):
                    '身份兑现后再看策略'
                    自身._发出(事件,值)
                def 丢掉(错误):
                    '读身份失败就当没有身份'
                    自身._发出(事件,None)
                return 身份.然后(送出).捕获(丢掉)
            自身._发出(事件,身份)
        except Exception as 错误:
            自身.上下文.日志.警告('Product analytics submission failed',错误)

    def _发出(自身,事件,身份):
        '策略仍开时补身份字段并交给产品遥测'
        if not 自身.已启用():
            return
        属性=dict(事件.get('attributes') or {})
        if isinstance(身份,dict):
            if 身份.get('deviceId') is not None:
                属性['device_id']=身份['deviceId']
            if 身份.get('userId') is not None:
                属性['user_id']=身份['userId']
            属性['os_version']=身份.get('osVersion')
        版本=取配置(自身.配置值,'appVersion',None)
        版本=读易失(版本)
        if 版本 is not None:
            属性['app_version']=版本
        自身.上下文.productTelemetry.发出({
            'eventName':事件['eventName'],
            'body':事件['eventName'],
            'timestamp':事件['timestamp'],
            'attributes':属性,
        })

远程贡献={
    'package':'@deepseek-ai/dsh-client-product-analytics',
    'namespace':'productAnalytics',
}

def 应用(上下文,配置值=None):
    '挂上桌面埋点入口'
    return 产品埋点(上下文,配置值)

name='productAnalytics'
inject=依赖
apply=应用
Config=配置
default=产品埋点
