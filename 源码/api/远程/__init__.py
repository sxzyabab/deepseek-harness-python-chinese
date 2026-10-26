'远程贡献组装的宿主入口：把选定的 Cordis 事件交给网关转发'
import os,json,threading
from collections import deque#事件帧缓冲
from ...内核.作用域 import 获取载体键#瀑布 this 上的智能体
from ...类型化远程调用.协议 import 是否远程json值#emit 参数必须是无损 JSON
from ...基础设施.js特性 import PromiseEX as 期约#瀑布结算
from ..网关.流协议 import 已中止#事件源寿命
from .远程事件 import 远程转发事件#白名单
from .类型 import 远程转发事件名#事件名投影
from . import (
    远程事件,#白名单模块
    类型,#选择席位
    异常,#本包没有异常类
    客户端,#客户端组装，不在这里启动
)#同目录模块。导入时执行它们的顶层

__all__=[#包根导出同目录模块和宿主入口，不转发客户端里的名字
    '远程转发事件','远程转发事件名',
    '远程事件','类型','异常','客户端',
    '依赖','应用',
]#公开面结束

依赖=['typertGateway']#网关拥有物理 Remote 流

def 远程事件源结束原因(信号):
    '源关闭原因。取消时用信号上的原因，否则是意外结束'
    if 信号.aborted:#调用方取消
        return 信号.reason#取消原因
    return Exception('api-remotes: 转发的 Remote 事件源已结束')#意外结束

class 远程事件队列:
    '把同步 Cordis 监听接到可拉取迭代'
    def __init__(自身):
        '构造空队列'
        自身.缓冲=deque()#尚未被拉取的帧
        自身.等待事件=threading.Event()#有帧或结束时放开
        自身.已结束=False#结束后不再接收

    def 推入帧(自身,帧):
        '入队一帧。已经结束则拒绝，返回是否收下'
        if 自身.已结束:#源已关
            return False#没收下
        自身.缓冲.append(帧)#放进缓冲
        自身.等待事件.set()#叫醒拉取
        return True#已收下

    def 结束(自身,原因):
        '结束并拒绝还挂着的瀑布。重复调用无事'
        if 自身.已结束:#已经结束
            return#停
        自身.已结束=True#不再接收
        while len(自身.缓冲)>0:#还没被拉取的帧
            派发=自身.缓冲.popleft()#取出
            if isinstance(派发,dict) and 'context' in 派发:#挂起的瀑布
                派发['reject'](原因)#拒绝
        自身.等待事件.set()#叫醒拉取，让迭代退出

    def 迭代(自身,信号,清理):
        '拉取直至中止或结束。离开时结束队列并拆除监听'
        def 中止():
            '信号取消时结束队列'
            自身.结束(远程事件源结束原因(信号))#用取消原因
        信号.addEventListener('abort',中止,{'once':True})#只接一次
        try:#无论生成怎样停都要清理
            while True:#没有自然结束，载体来关
                if 自身.已结束 or 已中止(信号):#已经停
                    return#结束生成
                while len(自身.缓冲)>0:#先交已有的帧
                    yield 自身.缓冲.popleft()#一帧
                if 自身.已结束 or 已中止(信号):#交完时已经停
                    return#结束生成
                自身.等待事件.clear()#准备等下一帧
                while not 自身.已结束 and not 已中止(信号) and len(自身.缓冲)==0:#还没有帧
                    自身.等待事件.wait(0.05)#短等，取消也能退出
        finally:#生成结束
            信号.removeEventListener('abort',中止)#摘掉
            自身.结束(远程事件源结束原因(信号))#拒绝剩余瀑布
            清理()#拆除监听

def 应用(上下文):
    '登记本应用选定的 Cordis 事件源'
    def 登记():
        '把事件源交给网关，返回拆除器'
        def 打开(信号):
            '挂上白名单监听并交出迭代器'
            队列=远程事件队列()#这一次源的唯一队列
            拆除表=[]#监听拆除器
            for 条目 in 远程转发事件:#白名单
                事件=条目['event']#线名
                if 条目['mode']=='emit':#通知
                    资源=条目['resources'] if 'resources' in 条目 else None#资源读取器，没有则不带
                    def 发射(*位置参数,事件名=事件,目标=队列,资源表=资源):
                        '把 emit 参数推进队列。参数必须是无损 JSON'
                        参数=list(位置参数)#按到达顺序
                        for 下标,参数值 in enumerate(参数):#逐个
                            if not 是否远程json值(参数值):#不能无损过线
                                raise Exception('转发的宿主事件 "'+事件名+'" 第 '+str(下标)+' 个参数不是无损 JSON 数据')#拒绝
                        帧={'event':事件名,'args':参数}#事件与参数
                        if 资源表 is not None:#声明了资源
                            帧['resources']=资源表#原样交给网关
                        目标.推入帧(帧)#入队
                    拆除表.append(上下文.监听(事件,发射))#登记
                else:#瀑布
                    def 瀑布(*位置参数,事件名=事件,目标=队列):
                        '把作用域瀑布交给网关。返回期约，解决值是客户端结果或下一环的结果'
                        if len(位置参数)>=3:#派发对象被绑成第一个参数
                            载体,请求,下一步=位置参数[0],位置参数[1],位置参数[2]#this、请求、续体
                        else:#没有派发对象
                            载体,请求,下一步=None,位置参数[0],位置参数[1]#请求、续体
                        载体智能体=获取载体键(载体)#this 上的智能体
                        if 载体智能体 is None:#没有作用域载体
                            return 下一步()#继续原来的瀑布
                        if isinstance(请求,dict) and 'agent' in 请求:#请求是字典
                            智能体=请求['agent']#直接携带的智能体
                        else:#请求是对象
                            智能体=getattr(请求,'agent',None)#属性上的智能体
                        if 智能体 is None or 智能体 is not 载体智能体:#没带上这个载体
                            raise TypeError('转发的作用域事件 '+json.dumps(事件名)+' 必须直接携带其智能体')#拒绝
                        任务=期约()#本次瀑布的结算点
                        def 解决结局(结局):
                            '客户端给出结果，或把这一环交给下一个监听'
                            if isinstance(结局,dict) and 结局.get('kind')=='result':#客户端有结果
                                任务.解决(结局.get('value'))#采用这个结果
                                return#停
                            try:#没有客户端结果
                                任务.解决(下一步())#走下一环
                            except BaseException as 错误:#下一环失败
                                任务.拒绝(错误)#交给调用方
                        派发={#挂起事件
                            'event':事件名,'request':请求,
                            'context':{'value':智能体.ctx,'subject':智能体,'agentId':智能体.id},
                            'resolve':解决结局,'reject':任务.拒绝,
                        }#派发结束
                        if not 目标.推入帧(派发):#队列已经结束
                            try:#直接走下一环
                                任务.解决(下一步())#下一环的结果
                            except BaseException as 错误:#下一环失败
                                任务.拒绝(错误)#交给调用方
                        return 任务#调用方对期约链接
                    拆除表.append(上下文.监听(事件,瀑布))#登记
            def 清理():
                '拆除这一次源挂上的监听'
                for 拆除 in 拆除表:#逐个
                    拆除()#拆除
            return 队列.迭代(信号,清理)#交给网关拉取
        return 上下文.typertGateway.登记远程事件(打开,{'home':os.path.expanduser('~')})#家目录随事件源登记
    上下文.副作用(登记,'api-remotes: forwarded Cordis event source')#随纤程拆除

inject=依赖#框架槽
apply=应用#框架槽
