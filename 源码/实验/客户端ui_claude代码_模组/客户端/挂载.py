'浏览器登记模组条带：Remote 流放进存储，停靠条目负责按下'
from ....客户端.模块.客户端.通告 import 取握手窗口
import threading#观看流在线程里读，不挡住登记
from . import 条带 as 条带模块#条带界面类
from .文案 import 命名空间,中文,英文#登记用的中英文案表

__all__=['依赖','登记界面']

依赖=['remote','slots','locale']#浏览器要的服务
线程类=threading.Thread#观看线程
锁类=threading.Lock#观看表


class 条带存储:
    '槽位渲染器当成 useBand 的最小可观察对象'
    def __init__(自身):
        '从空画面开始'
        自身.快照=None#还没有画面
        自身.监听=set()#订阅者
        自身.锁=锁类()#观看线程和页面都会碰

    def getSnapshot(自身):
        '当前画面'
        with 自身.锁:#和设置互斥
            return 自身.快照

    def subscribe(自身,监听):
        '订阅。返回退订'
        with 自身.锁:#和通知互斥
            自身.监听.add(监听)#记下
        def 退订():
            '去掉这一个'
            with 自身.锁:
                自身.监听.discard(监听)#退订
        return 退订

    def 设置(自身,下一个):
        '替换画面并通知。先抄一份监听再叫，避免订阅里改集合'
        with 自身.锁:#抄监听
            自身.快照=下一个#新画面
            副本=list(自身.监听)#副本
        for 监听 in 副本:#锁外通知
            监听()


def 登记界面(上下文):
    '登记词典，并为每个会话保持一条条带流'
    def 登记词典():
        '登记条带中英文案表。页面显示不走英文表'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(登记词典,'client-ui-claude-code-mods: dictionaries')#卸插件时卸词典
    观看表={}#会话号到观看
    观看锁=锁类()#流结束和打开会同时碰
    def 提供清理():
        '插件释放时拆掉全部观看'
        def 清理():
            '先摘掉表，再逐个取消'
            with 观看锁:
                待拆=list(观看表.values())#抄一份
                观看表.clear()#表先空
            for 项 in 待拆:#锁外拆除
                项['拆除']()
        return 清理
    上下文.副作用(提供清理,'client-ui-claude-code-mods: band watches')#卸插件时停流
    def 取观看(会话号):
        '没有就新开一条。流结束就丢掉，下次再开'
        with 观看锁:#打开和结束互斥
            已有=观看表.get(会话号)#可能已经有
            if 已有 is not None:#复用
                return 已有
            存储=条带存储()#这一会话的画面
            控制器=取握手窗口().AbortController()#取消用页面信号
            句柄=上下文.remote.claudeCodeMods.watchBand(会话号,控制器.signal)#宿主画面流
            已开={'存储':存储}#先占住，线程结束时按这份认
            def 结束():
                '流结束且仍是这一条才删掉'
                with 观看锁:
                    if 观看表.get(会话号) is 已开:#还是这一条
                        del 观看表[会话号]#下次重新开
            def 消费():
                '快照写进存储。未取消的结束记一条警告'
                try:
                    for 画面 in 句柄:#上游读到的快照
                        存储.设置(画面)#通知条带
                except Exception as 错误:#流失败
                    if not 控制器.signal.aborted:#不是拆除引起的
                        原文=getattr(错误,'message',None)#页面错误常有 message
                        if not isinstance(原文,str):#没有消息就转成字符串
                            原文=str(错误)
                        上下文.日志.警告(
                            f'claude-code-mods band: watch of {会话号} ended: {原文}'
                        )#原文警告
                finally:
                    结束()#丢掉这一条
            def 拆除():
                '取消并拆句柄'
                控制器.abort()#信号中止
                句柄.dispose()#拆流
            已开['拆除']=拆除#留给卸载
            观看表[会话号]=已开#先入表再启动
            线程=线程类(target=消费,daemon=True)#不挡住登记
            线程.start()#开始读
            return 已开
    def 注入(会话号):
        '这一会话的画面和按下'
        观看=取观看(会话号)#复用或新开
        def 按下(代数,动作号):
            '按下后用返回的画面替换存储。失败则抛出'
            结果=上下文.remote.claudeCodeMods.pressBand(会话号,代数,动作号)#同步等宿主
            if not 结果['ok']:#失败
                错误值=结果['error']#宿主错误
                if isinstance(错误值,BaseException):#原样抛
                    raise 错误值
                raise RuntimeError(str(错误值))#不是异常就收成错误
            取观看(会话号)['存储'].设置(结果['value'])#换成新画面
        return {'hooks':{'band':观看['存储']},'press':按下}#槽位注入面
    def 挂条带():
        '输入停靠上的条带'
        return 上下文.slots.register({
            'name':'conversation.input.dock',#槽名
            'id':'claude-code-mods',#条目
            'order':20,#顺序
            'locale':命名空间,#文案命名空间
            'inject':注入,#按会话注入
        },条带模块.条带)#界面类
    上下文.slots.inject('conversation.input.dock',挂条带)#声明出现后登记
