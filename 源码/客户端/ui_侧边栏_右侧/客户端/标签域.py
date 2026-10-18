'一张签在布局之外还带着导航、中止和自己能做的动作'
import threading
from uuid import uuid4 as 随机标识
from ...存储 import 创建快照存储
from ...ui_停靠套件.引擎.树 import 查找标签窗格
from ..异常 import 右侧侧栏错误

__all__=['标签域','中止信号']


class 中止信号(threading.Event):
    '一次出现的寿命。资源钉住认 is_set 和 wait，正文认 aborted 和 abort 监听'

    def __init__(自身):
        '还没中止'
        super().__init__()
        自身._监听=[]

    @property
    def aborted(自身):
        '已经中止'
        return 自身.is_set()

    def abort(自身):
        '中止并通知监听。再调一次没有事'
        if 自身.is_set():
            return
        副本=list(自身._监听)
        自身._监听.clear()
        自身.set()
        for 回调 in 副本:
            回调()

    def addEventListener(自身,类型,回调,选项=None):
        '只听 abort。已经中止就立刻回调'
        if 类型!='abort':
            return
        if 自身.is_set():
            回调()
            return
        自身._监听.append(回调)

    def removeEventListener(自身,类型,回调):
        '摘掉这个 abort 监听'
        if 类型!='abort':
            return
        if 回调 in 自身._监听:
            自身._监听.remove(回调)


class 标签域:
    '按会话和签标识持有出现次。布局里消失的签会被中止'

    def __init__(自身,导航器,钉住):
        '导航器负责再打开和关闭。钉住在第一次同步时叫一次'
        自身.导航器=导航器
        自身.钉住=钉住
        自身.按会话={}

    def 同步(自身,会话标识,布局):
        '对照这份已提交布局：消失的中止，新的钉住'
        持有=自身._会话(会话标识)
        for 标签标识,出现 in list(持有.items()):
            if 标签标识 in 布局['tabs']:
                continue
            del 持有[标签标识]
            出现['controller'].abort()
        for 签 in 布局['tabs'].values():
            出现=持有.get(签['id'])
            if 出现 is None:
                出现=自身._持有(会话标识,签['id'],{'address':签['contentId'],'params':None,'revision':0})
            窗=查找标签窗格(布局,签['id'])
            出现['paneId']=窗['id'] if 窗['host']=='dock' else None
            if 出现['pinned']:
                continue
            出现['pinned']=True
            自身.钉住(出现['navigation'].getSnapshot()['address'],出现['signal'])

    def 出现(自身,会话标识,标签):
        '读已经调和过的出现次'
        表=自身.按会话.get(会话标识)
        出现=None if 表 is None else 表.get(标签['id'])
        if 出现 is None:
            raise 右侧侧栏错误('sidebarRight: tab "'+str(标签['id'])+'" has no committed occurrence in session "'+str(会话标识)+'"')
        return 出现

    def 导航(自身,会话标识,标签标识,目标):
        '记下这次打开落在哪张签上'
        已有=自身._会话(会话标识).get(标签标识)
        if 已有 is None:
            自身._持有(会话标识,标签标识,{'address':目标['address'],'params':目标.get('params'),'revision':1})
            return
        修订=已有['navigation'].getSnapshot()['revision']+1
        已有['navigation'].set({'address':目标['address'],'params':目标.get('params'),'revision':修订})

    def 拆除(自身):
        '卸载时中止全部出现次'
        for 持有 in 自身.按会话.values():
            for 出现 in 持有.values():
                出现['controller'].abort()
        自身.按会话.clear()

    def _会话(自身,会话标识):
        '取或建这个会话的桶'
        持有=自身.按会话.get(会话标识)
        if 持有 is None:
            持有={}
            自身.按会话[会话标识]=持有
        return 持有

    def _持有(自身,会话标识,标签标识,导航):
        '建一次出现'
        控制器=中止信号()
        导航器=自身.导航器
        出现盒={}

        def 放置(选项):
            '没点名的窗用这张签现在所在的停靠窗'
            结果={}
            if 选项.get('replaceTab') is True:
                结果['replaceTab']=标签标识
            elif 出现盒.get('paneId') is not None:
                结果['paneId']=出现盒['paneId']
            if 选项.get('paneId') is not None:
                结果['paneId']=选项['paneId']
            if 'preferNewPane' in 选项:
                结果['preferNewPane']=选项['preferNewPane']
            if 'revealIfOpened' in 选项:
                结果['revealIfOpened']=选项['revealIfOpened']
            return 结果

        def 绑定命令(命令):
            '后来的正文不会被先来的拆除摘掉'
            if 控制器.aborted:
                def 空拆():
                    '已经中止，没有可摘的'
                    return None
                return 空拆
            出现盒['commands']=命令

            def 释放():
                '只摘自己这份命令'
                if 出现盒.get('commands') is 命令:
                    出现盒['commands']={}
                控制器.removeEventListener('abort',释放)

            控制器.addEventListener('abort',释放,{'once':True})
            return 释放

        def 打开资源(地址,选项=None):
            '从这张签再开一个资源'
            用=选项 if 选项 is not None else {}
            放置结果=放置(用)
            if 'params' in 用:
                放置结果['params']=用['params']
            导航器.在会话打开资源(会话标识,地址,放置结果)

        def 打开标签(种类,选项=None):
            '从这张签再开一个页面种类'
            用=选项 if 选项 is not None else {}
            放置结果=放置(用)
            if 'params' in 用:
                放置结果['params']=用['params']
            导航器.在会话打开标签(会话标识,种类,放置结果)

        def 关闭():
            '关掉这张签'
            导航器.在会话关闭(会话标识,标签标识)

        出现={
            'id':str(随机标识()),
            'sessionId':会话标识,
            'tabId':标签标识,
            'controller':控制器,
            'commands':{},
            'signal':控制器,
            'navigation':创建快照存储(导航),
            'paneId':None,
            'pinned':False,
            'tabActions':{
                'bindCommands':绑定命令,
                'openResource':打开资源,
                'openTab':打开标签,
                'close':关闭,
            },
        }
        出现盒.update(出现)
        自身._会话(会话标识)[标签标识]=出现盒
        return 出现盒
