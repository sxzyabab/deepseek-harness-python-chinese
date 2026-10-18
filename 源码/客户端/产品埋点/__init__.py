'仅桌面的埋点远程调用与实时压缩采集'
import threading#策略等待与共享采样
from ...类型化远程调用.协议 import 远程,远程服务#远程方法与服务基类
from ...基础设施.通用工具 import 启动守护线程#采样、身份和压缩上报
from ...基础设施.通用工具.时间工具 import 当前毫秒#发生时间
from ...基础设施.通用工具.数值判定 import 是否整值数#配置里的整数
from .环境 import 收集环境#静态环境，整次服务只采一次
from .环境查询 import 信号已中止#策略流的取消
from . import (
    事件,#事件名
    环境,#静态环境
    环境查询,#命令查询
    异常,#本包没有异常类
    客户端,#桌面发送器
)#同目录模块。导入时执行它们的顶层

__all__=['依赖','配置','产品埋点','客户端','事件','环境','环境查询','异常']#包根只导出客户端这个模块，不转发里面的类

整数上限=2147483647#有符号 32 位上界

def 取有界整数(数据,键,缺省):
    '缺席用缺省。写出的值必须是 1 到 2147483647 的整数'
    if 键 not in 数据:#没写
        值=缺省#缺省
    else:#写了
        值=数据[键]#原值
    if not 是否整值数(值) or 值<1 or 值>整数上限:#不是范围内的整数
        raise ValueError(键+' must be an integer from 1 to 2147483647')#加载时失败
    return int(值)#整数

class 易失格:
    '稳定引用。get 返回当前值，加载器可以改 当前'
    def __init__(自身,值):
        '记下初值'
        自身.当前=值#当前快照

    def get(自身):
        '当前快照'
        return 自身.当前#最新值

class 产品埋点配置:
    '应用自有的采集策略，没有用户设置页'
    @classmethod
    def 校验数据(类,数据=None):
        '补默认值。enabled 收成易失单元格，appVersion 可以不写'
        if 数据 is None:#没传配置
            数据={}#空配置
        if not isinstance(数据,dict):#必须是对象
            raise ValueError('product analytics config must be an object')#拒绝
        if 'enabled' in 数据:#写了开关
            启用=数据['enabled']#原值或单元格
        else:#没写
            启用=True#默认开
        已是单元格=not isinstance(启用,(dict,list,str,bytes,bytearray,bool,int,float,type(None))) and callable(getattr(启用,'get',None))#已有 get
        if isinstance(启用,bool):#普通布尔
            启用=易失格(启用)#收成单元格
        elif not 已是单元格:#既不是布尔也不是单元格
            raise ValueError('enabled must be a boolean')#拒绝
        if 'appVersion' in 数据:#写了版本
            版本=数据['appVersion']#原值
            if not isinstance(版本,str):#必须是字符串
                raise ValueError('appVersion must be a string')#拒绝
        else:#没写
            版本=None#不带 app_version
        return {#校验后的配置
            'enabled':启用,#易失开关
            'appVersion':版本,#可缺
            'environmentQueryTimeoutMillis':取有界整数(数据,'environmentQueryTimeoutMillis',5000),#单条查询截止
            'environmentQueryMaxOutputBytes':取有界整数(数据,'environmentQueryMaxOutputBytes',16384),#单路输出上限
        }#配置结束

class 产品埋点(远程服务):
    '已认证的事件入口。关闭后不读身份，也不收新事件'
    inject=['deepseekAccount','productTelemetry']#账号与产品遥测
    name='productAnalytics'#插件名
    Config=产品埋点配置#配置模式
    def __init__(自身,上下文,配置值):
        '登记 productAnalytics，关掉设置自动呈现，并在压缩开始时采集'
        super().__init__(上下文,'productAnalytics')#服务名
        自身.配置值=配置值#已校验配置
        自身.活动中=True#拆除前接受事件
        自身.环境寿命=threading.Event()#采样取消
        自身.环境锁=threading.Lock()#只启动一次采样
        自身.环境任务=None#尚未采样
        自身.监听器=set()#策略流
        def 拆除效果():
            '卸载后停收，取消采样，并等到采样结束'
            def 清理():
                '先停收再取消，避免迟到结果发出去'
                自身.活动中=False#不再接受
                for 监听 in list(自身.监听器):#叫醒策略流
                    监听()#各自的等待
                自身.环境寿命.set()#取消还在跑的命令
                if 自身.环境任务 is not None:#已经开始采样
                    自身.环境任务['完成'].wait()#等到采样返回
            return 清理#拆除器
        上下文.副作用(拆除效果)#随纤程拆除
        def 易失更新(*参数):
            '实时配置变更后重发策略。参数是变更路径，这里只重读开关'
            for 监听 in list(自身.监听器):#叫醒
                监听()#重读 enabled
        上下文.监听('loader/volatile-update',易失更新)#易失更新
        def 接线(子上下文):
            '有 settings 才关掉自动呈现'
            def 挂():
                'auto 为 false，绑到本纤程'
                return 子上下文.settings.configure({'auto':False},上下文.纤程)#呈现策略
            子上下文.副作用(挂)#随设置作用域拆除
        上下文.依赖启动(['settings'],接线)#等设置服务
        def 会话事件(会话,事件):
            '只上报压缩开始，不重放历史'
            if not isinstance(事件,dict) or 事件.get('type')!='compaction/start':#不是压缩开始
                return#忽略
            数据=事件['data']#载荷
            if 'turn' in 数据 and 数据['turn'] is None:#没有回合
                触发='manual'#手动
            else:#回合内或没有该键
                触发='auto'#自动
            def 上报():
                '不阻塞会话事件'
                自身.report({#选定字段
                    'eventName':'context_compression',#事件名
                    'timestamp':当前毫秒(),#现在
                    'attributes':{#属性
                        'session_id':会话.id,#会话
                        'trigger_type':触发,#手动或自动
                    },#属性结束
                })#上报结束
            启动守护线程(上报)#不等待
        上下文.监听('session/event',会话事件)#会话事件

    @远程
    def enabled(自身):
        '当前宿主是否接受桌面埋点'
        字段=自身.配置值['enabled']#开关或单元格
        if isinstance(字段,(dict,list,str,bytes,bytearray,bool,int,float)) or 字段 is None:#普通值
            当前=字段#本身
        else:#单元格
            取值=getattr(字段,'get',None)#get
            if callable(取值):#有 get
                当前=取值()#当前快照
            else:#没有 get
                当前=字段#本身
        return 自身.活动中 and 当前#拆除或关掉都不收

    @远程({'mode':'stream'})
    def watchPolicy(自身,信号):
        '先给当前策略，变更后再给，直到取消或服务拆除'
        更新=threading.Event()#下一次变更
        锁=threading.Lock()#代次与事件一起改
        代次={'n':0}#变更次数
        def 已变():
            '配置、拆除或取消时叫醒'
            with 锁:#代次和置位一起
                代次['n']=代次['n']+1#新的一代
                更新.set()#叫醒
        自身.监听器.add(已变)#登记
        已登记中止=False#是否用了 addEventListener
        if 信号 is not None and hasattr(信号,'addEventListener'):#浏览器取消
            信号.addEventListener('abort',已变,{'once':True})#取消时叫醒
            已登记中止=True#结束时摘掉
        elif 信号 is not None:#网关信号或 Event
            内部事件=getattr(信号,'_事件',None)#网关
            if 内部事件 is None and hasattr(信号,'wait'):#Event
                内部事件=信号#直接等
            if 内部事件 is not None:#有可等的事件
                def 等待中止():
                    '取消后叫醒策略流'
                    内部事件.wait()#阻塞到取消
                    已变()#叫醒
                启动守护线程(等待中止)#不阻塞这次调用
        try:#结束时一定摘掉监听
            while 自身.活动中 and not 信号已中止(信号):#还收，且没取消
                with 锁:#记下这一代
                    看到=代次['n']#当前代
                yield 自身.enabled()#当前策略
                while True:#等到新的一代
                    with 锁:#可能在交出之后已经变了
                        if 代次['n']!=看到:#已经变了
                            更新.clear()#清掉这一次
                            break#回去看是否还要继续
                    更新.wait()#等下一次
                    更新.clear()#消费掉
        finally:#取消或拆除
            自身.监听器.discard(已变)#摘掉
            if 已登记中止:#曾登记浏览器取消
                信号.removeEventListener('abort',已变)#摘掉

    @远程
    def report(自身,事件):
        '提交选定桌面字段。缺身份就省略。本地提交后返回，不等送达'
        if not 自身.enabled():#关闭后不读身份
            return#不采样
        try:#采样或遥测失败只记警告
            身份盒={'值':None}#身份
            身份完成=threading.Event()#身份读完
            def 读身份():
                '读失败就当没有身份，不让整次提交失败'
                try:#账号不可用
                    身份=自身.ctx.deepseekAccount.getDeviceIdentity()#不含凭据
                    if hasattr(身份,'等待'):#期约则等它落定
                        身份=身份.等待()#同步结果
                    身份盒['值']=身份#字典或对象
                except Exception as 读取错误:#读失败，不把账号错误写进事件
                    身份盒['值']=None#省略身份
                身份完成.set()#读完
            启动守护线程(读身份)#与环境采样同时
            with 自身.环境锁:#并发提交共用一次采样
                if 自身.环境任务 is None:#还没开始
                    盒子={'值':None,'错误':None,'完成':threading.Event()}#这一次的结果
                    def 采样():
                        '采完或失败都要放开等待'
                        try:#采样自己抛错则缓存这次失败
                            盒子['值']=收集环境({#界限与寿命
                                'timeoutMillis':自身.配置值['environmentQueryTimeoutMillis'],#截止
                                'maxOutputBytes':自身.配置值['environmentQueryMaxOutputBytes'],#输出上限
                                'signal':自身.环境寿命,#拆除时取消
                            })#采样结束
                        except Exception as 采样错误:#采样抛错
                            盒子['错误']=采样错误#后面的提交重放同一次失败
                        finally:#无论成败
                            盒子['完成'].set()#放开
                    自身.环境任务=盒子#先登记再启动，避免第二次又开
                    启动守护线程(采样)#开始
                盒子=自身.环境任务#这一次或已经在跑的那一次
            盒子['完成'].wait()#等到采样
            身份完成.wait()#等到身份
            if 盒子['错误'] is not None:#采样失败
                raise 盒子['错误']#记警告，不重试另一套
            if not 自身.enabled():#等待期间关掉了
                return#不发
            环境=盒子['值']#快照
            属性=dict(事件['attributes'])#事件自己的字段
            for 键,值 in 环境.items():#环境字段
                if 键!='missing_fields':#失败清单单独编码
                    属性[键]=值#盖到属性上
            缺失项=sorted(环境['missing_fields'].items())#按字段名排序
            if len(缺失项)>0:#有失败字段
                属性['missing_fields']=','.join(键+'='+原因 for 键,原因 in 缺失项)#标量
            未出现=object()#键不存在，和值为 null 分开
            def 读取身份字段(键):
                '键不存在就省略。值为 null 仍然写入'
                身份=身份盒['值']#这次读到的身份
                if 身份 is None:#没有身份
                    return 未出现#省略
                if isinstance(身份,dict):#字典
                    if 键 not in 身份:#没有这个键
                        return 未出现#省略
                    return 身份[键]#含 null
                if hasattr(身份,键):#对象字段
                    return getattr(身份,键)#含 null
                return 未出现#没有
            设备=读取身份字段('deviceId')#设备
            if 设备 is not 未出现:#写了，包括 null
                属性['device_id']=设备#只抄这一个
            用户=读取身份字段('userId')#用户
            if 用户 is not 未出现:#写了，包括 null
                属性['user_id']=用户#只抄这一个
            版本=自身.配置值['appVersion']#可缺
            if 版本 is not None:#写了版本
                属性['app_version']=版本#客户端版本
            记录=dict(事件)#保留事件上的其他键
            记录['body']=事件['eventName']#正文是事件名
            记录['attributes']=属性#合并后的属性
            自身.ctx.productTelemetry.发出(记录)#入队，不等网络
        except Exception as 错误:#不把遥测失败抛回调用方
            自身.ctx.日志.警告('Product analytics submission failed',错误)#原文警告

依赖=产品埋点.inject#与类上的依赖同一份
配置=产品埋点配置#配置模式
name=产品埋点.name#插件名
inject=依赖#模块依赖
Config=配置#模块配置槽
default=产品埋点#默认导出是宿主服务类
