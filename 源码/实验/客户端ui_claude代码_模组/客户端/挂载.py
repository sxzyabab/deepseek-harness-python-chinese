'浏览器登记模组条带：Remote 流放进存储，停靠条目负责按下'
from functools import partial as 偏函数
from ....基础设施.通用工具 import 获取内部数据,启动守护线程
from .条带 import 条带
from .文案 import 命名空间,中文,英文

__all__=['依赖','挂载模组条带','登记界面']

依赖=['remote','slots','locale']

def 错误文本(错误):
    '异常取消息，其余转成字符串'
    if isinstance(错误,BaseException):
        return str(错误)
    return str(错误)

class 条带存储:
    '槽位渲染器当成 useBand 的最小可观察对象'
    def __init__(自身):
        '从空画面开始'
        自身.快照=None
        自身.监听=set()

    def getSnapshot(自身):
        '当前画面'
        return 自身.快照

    def subscribe(自身,监听):
        '订阅；返回退订'
        自身.监听.add(监听)
        def 退订():
            '去掉这一个'
            自身.监听.discard(监听)
        return 退订

    def 设置(自身,下一个):
        '替换画面并通知'
        自身.快照=下一个
        for 监听 in list(自身.监听):
            监听()

def 观看会话(上下文,会话号,结束时):
    '用宿主 watchBand 喂这一会话的存储，流结束就丢掉，下次再开'
    存储=条带存储()
    控制器={'aborted':False}
    def 中止():
        '标记取消'
        控制器['aborted']=True
    控制器['abort']=中止
    句柄=上下文.remote.claudeCodeMods.watchBand(会话号,控制器)
    def 消费():
        '快照写进存储；未取消的结束记一条警告'
        try:
            for 画面 in 句柄:
                存储.设置(画面)
        except Exception as 错误:
            if not 控制器['aborted']:
                上下文.日志.警告('claude-code-mods band: watch of '+str(会话号)+' ended: '+错误文本(错误))
        finally:
            结束时()
    启动守护线程(消费)
    def 拆除():
        '取消并拆句柄'
        中止()
        if hasattr(句柄,'dispose'):
            句柄.dispose()
    return {'store':存储,'dispose':拆除}

def 登记界面(上下文):
    '登记词典，并为每个会话保持一条条带流'
    def 卸词典():
        '登记条带文案'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(卸词典,'client-ui-claude-code-mods: dictionaries')
    观看表={}
    def 拆全部():
        '插件释放时拆掉全部观看'
        def 清理():
            '逐个拆除'
            for 项 in list(观看表.values()):
                项['dispose']()
            观看表.clear()
        return 清理
    上下文.副作用(拆全部,'client-ui-claude-code-mods: band watches')
    def 取观看(会话号):
        '没有就新开一条'
        已有=观看表.get(会话号)
        if 已有 is None:
            持有={'项':None}
            def 结束():
                '流结束且仍是这一条才删掉'
                if 观看表.get(会话号) is 持有['项']:
                    观看表.pop(会话号,None)
            持有['项']=观看会话(上下文,会话号,结束)
            观看表[会话号]=持有['项']
            已有=持有['项']
        return 已有
    def 注入(会话号):
        '这一会话的画面和按下'
        def 按下(代数,动作号):
            '按下后用返回的画面替换存储'
            结果=上下文.remote.claudeCodeMods.pressBand(会话号,代数,动作号)
            def 检查(值):
                '失败则抛 Remote 错误'
                if isinstance(值,dict) and 值.get('ok') is False:
                    raise 值['error']
                if isinstance(值,dict) and 'value' in 值:
                    取观看(会话号)['store'].设置(值['value'])
                return 值
            if hasattr(结果,'然后'):
                return 结果.然后(检查)
            return 检查(结果)
        return {'hooks':{'band':取观看(会话号)['store']},'press':按下}
    def 挂条带():
        '输入停靠上的条带'
        return 上下文.slots.register({
            'name':'conversation.input.dock',
            'id':'claude-code-mods',
            'order':20,
            'locale':命名空间,
            'inject':注入,
        },条带)
    上下文.slots.inject('conversation.input.dock',挂条带)

def 调用无参(函数,结果=None):
    '期约回调丢掉兑现值'
    return 函数()

def 抛出保留错误(错误,结果=None):
    '回滚完成后抛出原错误'
    raise 错误

def 卸界面与远程(界面,卸远程):
    '卸界面和 Remote'
    return 界面.dispose().然后(偏函数(调用无参,卸远程))

def 回滚界面(界面,卸远程,错误):
    '界面启动失败：卸掉后再抛原错误'
    return 界面.dispose().然后(偏函数(调用无参,卸远程)).然后(偏函数(抛出保留错误,错误))

def 交出卸除器(界面,卸远程,界面就绪值=None):
    '界面就绪后交出卸除函数'
    return 偏函数(卸界面与远程,界面,卸远程)

def 挂载模组条带(上下文,贡献):
    '挂上桥的 Remote 并登记条带。返回期约，兑现值是卸除函数'
    def 挂载界面(卸远程):
        'Remote 挂载完成后启动界面；失败则回滚 Remote'
        界面=上下文.依赖启动(['remote.claudeCodeMods','slots','locale'],登记界面)
        return 界面.等待().然后(偏函数(交出卸除器,界面,卸远程)).捕获(偏函数(回滚界面,界面,卸远程))
    return 获取内部数据(上下文.remote,'mount')(贡献).然后(挂载界面)
