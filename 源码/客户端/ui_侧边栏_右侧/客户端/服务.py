'别的插件能对右侧栏做的事：打开、关闭、分栏、浮动，以及现在屏幕上是哪个会话'
from ...模块.客户端.通告 import 取握手窗口
from uuid import uuid4 as 随机标识
from ...存储 import 创建快照存储
from ...ui_停靠套件.引擎.约束 import 可分割
from ...ui_停靠套件.引擎.树 import 取窗格,查找标签窗格,停靠窗格标识列表
from ...ui_停靠套件.引擎.规划 import 活动停靠窗格标识,查找内容标签,查找窗格内容标签
from ..异常 import 右侧侧栏错误,未登记种类,无人认领
from .约定.种子 import 页面地址
from .存储 import 可关闭标签
from .标签域 import 标签域
from .标签清单 import 侧栏标签清单
from .焦点 import 从元素取右侧侧栏目标

__all__=['创建右侧侧栏控制器','右侧侧栏控制器','资源方案前缀']

资源方案前缀='dsh-resource://'
_缺省=object()


def 创建右侧侧栏控制器(标签表,钉住,宿主):
    '控制器，加上认领存储、忘掉作用域、点名在屏会话、记下能不能分栏'
    已认={}
    房间={}
    在屏=创建快照存储(None)
    清单=侧栏标签清单()
    控制器=右侧侧栏控制器(标签表,钉住,宿主,{
        'adopted':已认,
        'rooms':房间,
        'onScreen':在屏,
        'openTabs':清单.源,
    })

    def 遗忘(会话标识):
        '清掉清单和房间规则'
        清单.移除(会话标识)
        if 会话标识 in 房间:
            del 房间[会话标识]

    def 显示(会话标识):
        '在屏会话变了才发布'
        if 在屏.getSnapshot() is not 会话标识:
            在屏.set(会话标识)

    def 测量(会话标识,能分):
        '记下这一格还能不能分成两半'
        房间[会话标识]=能分

    def 认领(会话标识,存储):
        '换上这份存储，先对齐一次，再跟随后续提交'
        旧=已认.get(会话标识)
        if 旧 is not None:
            旧['unsubscribe']()

        def 同步():
            '清单和出现次跟这份表面走'
            表面=存储.getSnapshot()['bySession'].get(会话标识)
            签表={} if 表面 is None else 表面['layout']['tabs']
            清单.更新(会话标识,list(签表.values()))
            if 表面 is not None:
                控制器.标签域.同步(会话标识,表面['layout'])

        认={'store':存储,'unsubscribe':存储.subscribe(同步)}
        已认[会话标识]=认
        同步()

        def 释放():
            '只摘掉还是这一次的认领'
            认['unsubscribe']()
            if 已认.get(会话标识) is 认:
                del 已认[会话标识]

        return 释放

    return {'controller':控制器,'adopt':认领,'forget':遗忘,'show':显示,'measure':测量}


class 右侧侧栏控制器:
    '在屏会话上的导航。签自己的动作走那张签所在的会话'

    def __init__(自身,标签表,钉住,宿主,会话):
        '标签域用控制器自己当导航器'
        自身.标签表=标签表
        自身.宿主=宿主
        自身.已认=会话['adopted']
        自身.房间=会话['rooms']
        自身.已挂载=会话['onScreen']
        自身.打开标签=会话['openTabs']
        自身.关闭钩表={}
        自身.标签域=标签域(自身,钉住)

    def 登记关闭钩(自身,种类,钩):
        '同一种类只能有一个。返回摘掉它的函数'
        if 种类 in 自身.关闭钩表:
            raise 右侧侧栏错误('sidebarRight: close handler already registered for '+种类)
        自身.关闭钩表[种类]=钩

        def 拆除():
            '只摘自己这份'
            if 自身.关闭钩表.get(种类) is 钩:
                del 自身.关闭钩表[种类]

        return 拆除

    def 会话内标签(自身,会话标识):
        '这份已认领布局里的签。还没认领就是空'
        认=自身.已认.get(会话标识)
        if 认 is None:
            return ()
        表面=认['store'].getSnapshot()['bySession'].get(会话标识)
        if 表面 is None:
            return ()
        return tuple(表面['layout']['tabs'].values())

    def 打开资源(自身,地址,选项=None):
        '在屏会话里打开资源'
        要求=自身._要求()
        自身._放置资源(要求['sessionId'],要求['actions'],地址,选项 if 选项 is not None else {})

    def 打开标签(自身,种类,选项=None):
        '在屏会话里按种类打开页面'
        要求=自身._要求()
        自身._放置标签(要求['sessionId'],要求['actions'],种类,选项 if 选项 is not None else {})

    def 在会话打开资源(自身,会话标识,地址,选项=None):
        '这张签所在的会话。存储没认领就什么都不做'
        动作=自身._动作于(会话标识)
        if 动作 is not None:
            自身._放置资源(会话标识,动作,地址,选项 if 选项 is not None else {})

    def 在会话打开标签(自身,会话标识,种类,选项=None):
        '这张签所在的会话。存储没认领就什么都不做'
        动作=自身._动作于(会话标识)
        if 动作 is not None:
            自身._放置标签(会话标识,动作,种类,选项 if 选项 is not None else {})

    def 在会话关闭(自身,会话标识,标签标识):
        '先跑清理钩，再关。独一停靠向导留着'
        动作=自身._动作于(会话标识)
        认=自身.已认.get(会话标识)
        表面=None if 认 is None else 认['store'].getSnapshot()['bySession'].get(会话标识)
        if 动作 is None or 表面 is None:
            return
        签=表面['layout']['tabs'].get(标签标识)
        if 签 is None or not 可关闭标签(表面,标签标识):
            return

        def 提交():
            '清理通过才关'
            动作['关闭标签'](会话标识,标签标识)

        自身._清理后移除(会话标识,签,提交)

    def _清理后移除(自身,会话标识,签,提交):
        '钩子抛了就不提交，签还在'
        钩=自身.关闭钩表.get(签['kind'])
        if 钩 is not None:
            钩(会话标识,签)
        提交()

    def _放置资源(自身,会话标识,动作,地址,选项):
        '不是资源地址，或没有类型认，就抛'
        if not str(地址).startswith(资源方案前缀):
            无人认领(地址)
        认领=自身.标签表.认领(地址,选项.get('kind'))
        自身._放置(会话标识,动作,认领,地址,选项,选项.get('params'))

    def _放置标签(自身,会话标识,动作,种类,选项):
        '允许多开的种类每次用新地址'
        定义=自身.标签表.取(种类)
        if 定义 is None:
            未登记种类(种类)
        if 定义.get('multiple') is True:
            地址=页面地址(种类)+'/'+str(随机标识())
        else:
            地址=页面地址(种类)
        认领={'kind':种类,'contentId':地址,'title':定义['title'](地址)}
        自身._放置(会话标识,动作,认领,地址,选项,选项.get('params'))

    def _放置(自身,会话标识,动作,认领,地址,放置,参数):
        '一次打开意图，并记下导航'
        认=自身.已认.get(会话标识)
        表面=None if 认 is None else 认['store'].getSnapshot()['bySession'].get(会话标识)
        目标窗=None
        if 表面 is not None:
            目标窗=放置.get('paneId')
            if 目标窗 is None:
                目标窗=活动停靠窗格标识(表面['layout'])
        目标=None if 目标窗 is None or 表面 is None else 表面['layout']['nodes'].get(目标窗)
        偏好新窗=放置.get('preferNewPane') is True and 放置.get('replaceTab') is None and 表面 is not None and 目标 is not None and 目标.get('kind')=='pane' and 目标.get('host')=='dock' and len(目标['tabs'])>0 and 可分割(表面['layout']) and len(停靠窗格标识列表(表面['layout']))<2 and 自身.已挂载.getSnapshot()==会话标识 and 自身._能分栏(会话标识,目标['id'])
        意图={
            'kind':认领['kind'],
            'contentId':认领['contentId'],
            'title':认领['title'],
        }
        if 放置.get('paneId') is not None:
            意图['paneId']=放置['paneId']
        if 偏好新窗:
            意图['preferNewPane']=True
        if 放置.get('replaceTab') is not None:
            意图['replaceTab']=放置['replaceTab']
        if 'revealIfOpened' in 放置:
            意图['revealIfOpened']=放置['revealIfOpened']

        def 提交():
            '落定回调里记下导航'
            def 落定(标签标识):
                '这次打开落在这张签'
                自身.标签域.导航(会话标识,标签标识,{'address':地址,'params':参数})
            动作['打开内容'](会话标识,意图,落定)

        布局=None if 表面 is None else 表面['layout']
        被替换=None
        if 放置.get('replaceTab') is not None and 布局 is not None:
            被替换=布局['tabs'].get(放置['replaceTab'])
        替换窗=None
        if 被替换 is not None and 布局 is not None:
            替换窗=查找标签窗格(布局,被替换['id'])
        if 布局 is None:
            揭示=None
        elif 认领['contentId']==页面地址(认领['kind']):
            if 替换窗 is not None and 替换窗.get('host')=='dock':
                找窗=替换窗['id']
            else:
                找窗=放置.get('paneId')
                if 找窗 is None:
                    找窗=活动停靠窗格标识(布局)
            揭示=查找窗格内容标签(布局,找窗,认领['contentId'],认领['kind'])
        elif 放置.get('revealIfOpened') is False:
            揭示=None
        else:
            揭示=查找内容标签(布局,认领['contentId'],认领['kind'])
        if 被替换 is None or 被替换['id']==揭示:
            提交()
            return
        自身._清理后移除(会话标识,被替换,提交)

    def 关闭(自身,标签标识):
        '关在屏会话里的这张签'
        自身.在会话关闭(自身._要求()['sessionId'],标签标识)

    def 活动(自身):
        '活动窗里的活动签'
        表面=自身._挂载表面()
        if 表面 is None:
            return None
        布局=表面['layout']
        窗=取窗格(布局,布局['activePaneId'])
        活动标识=窗.get('activeTabId')
        for 签 in 布局['tabs'].values():
            if 签['id']==活动标识:
                return 签
        return None

    def 是否展开(自身):
        '在屏表面展开着'
        表面=自身._挂载表面()
        if 表面 is None:
            return False
        return 表面['layout']['expanded'] is True

    def 切换展开(自身):
        '展开后聚焦活动停靠窗'
        要求=自身._要求()

        def 打开():
            '切换并返回要聚焦的窗'
            要求['actions']['切换展开'](要求['sessionId'])
            布局=None if 自身._挂载表面() is None else 自身._挂载表面()['layout']
            if 布局 is not None and 布局['expanded']:
                return 活动停靠窗格标识(布局)
            return None

        自身.宿主['openWithFocus'](要求['sessionId'],打开)

    def 聚焦(自身,标签标识):
        '没有这张签就不动'
        要求=自身._要求()
        表面=自身._挂载表面()
        if 表面 is None or 标签标识 not in 表面['layout']['tabs']:
            return
        要求['actions']['聚焦标签'](要求['sessionId'],标签标识)

    def 聚焦目标(自身,元素=_缺省):
        '从页面元素读当前页。不传就用文档焦点'
        if 元素 is _缺省:
            元素=取握手窗口().document.activeElement
        屏=自身._屏()
        if 屏 is None:
            return None
        return 从元素取右侧侧栏目标(元素,屏['sessionId'],屏['surface']['layout'],lambda 标签标识: 自身.标签域.出现(屏['sessionId'],{'id':标签标识}))

    def 命令目标(自身,元素=_缺省):
        '有焦点用焦点。点在侧栏外才回退到活动停靠窗'
        if 元素 is _缺省:
            元素=取握手窗口().document.activeElement
        已聚焦=自身.聚焦目标(元素)
        在侧栏=False
        if 元素 is not None:
            在侧栏=元素.closest('[data-sidebar-right-session]') is not None
        if 已聚焦 is not None or 在侧栏:
            return 已聚焦
        屏=自身._屏()
        if 屏 is None:
            return None
        布局=屏['surface']['layout']
        窗=取窗格(布局,活动停靠窗格标识(布局))
        标签标识=窗.get('activeTabId')
        持有=None if 标签标识 is None else 自身.标签域.出现(屏['sessionId'],{'id':标签标识})
        修订=None if 持有 is None else 持有['navigation'].getSnapshot()['revision']
        return {
            'sessionId':屏['sessionId'],
            'paneId':窗['id'],
            'host':窗['host'],
            'tabId':标签标识,
            'occurrence':持有,
            'navigationRevision':修订,
        }

    def 从目标打开标签(自身,种类,目标):
        '浮动里的同一页只展开并聚焦。向导会被替换'
        if not 自身.目标仍当前(目标):
            return
        要求=自身._要求()

        def 打开():
            '按宿主做完再返回活动窗'
            签=None
            if 目标.get('tabId') is not None and 自身._挂载表面() is not None:
                签=自身._挂载表面()['layout']['tabs'].get(目标['tabId'])
            定义=自身.标签表.取(种类)
            多个=定义 is not None and 定义.get('multiple') is True
            if 目标['host']=='float' and 签 is not None and 签['kind']==种类 and not 多个:
                要求['actions']['设展开'](要求['sessionId'],True)
                自身.聚焦(签['id'])
            else:
                选项={}
                if 目标['host']=='dock':
                    选项['paneId']=目标['paneId']
                if 签 is not None and 签['kind']=='guide':
                    选项['replaceTab']=签['id']
                自身.打开标签(种类,选项)
            表面=自身._挂载表面()
            if 表面 is None:
                return None
            return 表面['layout']['activePaneId']

        自身.宿主['openWithFocus'](要求['sessionId'],打开)

    def 可关闭目标(自身,目标):
        '还是这一页，并且捕获到了签'
        return 自身.目标仍当前(目标) and 目标.get('tabId') is not None

    def 关闭目标(自身,目标):
        '能关就关，独一停靠向导就收起。身份变了返回 stale'
        if not 自身.目标仍当前(目标):
            return 'stale'
        表面=自身._挂载表面()
        if 表面 is None or 目标.get('tabId') is None:
            return 'unavailable'
        标签标识=目标['tabId']
        要求=自身._要求()

        def 关闭():
            '清理抛了就留着这一页'
            if 可关闭标签(表面,标签标识):
                自身.关闭(标签标识)
            else:
                要求['actions']['设展开'](要求['sessionId'],False)

        自身.宿主['closeWithFocus'](要求['sessionId'],目标['paneId'],关闭)
        return 'closed'

    def 目标仍当前(自身,目标):
        '会话、窗、出现次和导航修订都还对得上'
        if 自身.已挂载.getSnapshot()!=目标['sessionId']:
            return False
        表面=自身._挂载表面()
        布局=None if 表面 is None else 表面['layout']
        窗=None if 布局 is None else 布局['nodes'].get(目标['paneId'])
        if 窗 is None or 窗.get('kind')!='pane' or 窗.get('host')!=目标['host']:
            return False
        if 目标.get('tabId') is None:
            return 窗.get('activeTabId') is None
        if 目标['tabId'] not in 窗['tabs'] or 目标['tabId'] not in 布局['tabs']:
            return False
        持有=自身.标签域.出现(目标['sessionId'],{'id':目标['tabId']})
        return 持有 is 目标.get('occurrence') and not 持有['signal'].aborted and 持有['navigation'].getSnapshot()['revision']==目标.get('navigationRevision')

    def 分栏阻断(自身,目标):
        '不能分栏时返回原因键，能分就没有'
        表面=自身._挂载表面()
        if 表面 is None or not 自身.目标仍当前(目标):
            return 'stale'
        布局=表面['layout']
        if 目标['host']=='float':
            return 'float'
        if not 布局['expanded']:
            return 'collapsed'
        if len(取窗格(布局,目标['paneId'])['tabs'])==0:
            return 'empty'
        if not 可分割(布局) or len(停靠窗格标识列表(布局))>=2:
            return 'budget'
        if not 自身._能分栏(目标['sessionId'],目标['paneId']):
            return 'width'
        return None

    def 切换全屏(自身,目标):
        '窄视口下的自动全屏改为收起，否则切换记录的模式'
        if not 自身.目标仍当前(目标) or 目标['host']=='float' or not 自身.是否展开():
            return
        要求=自身._要求()
        自动=自身.宿主['autoFullscreen']()
        表面=自身._挂载表面()
        全屏=自动 or (表面 is not None and 表面['layout']['mode']=='fullscreen')
        if 全屏 and 自动:
            要求['actions']['设展开'](要求['sessionId'],False)
        要求['actions']['设模式'](要求['sessionId'],'push' if 全屏 else 'fullscreen')

    def 分栏(自身,窗格标识=None):
        '预算和宽度都允许才分。返回新窗，没分成就没有'
        要求=自身._要求()
        表面=自身._挂载表面()
        if 表面 is None:
            return None
        布局=表面['layout']
        目标=窗格标识 if 窗格标识 is not None else 活动停靠窗格标识(布局)
        节点=布局['nodes'].get(目标)
        if 节点 is None or 节点.get('kind')!='pane' or 节点.get('host')!='dock':
            return None
        if not 可分割(布局) or len(停靠窗格标识列表(布局))>=2 or not 自身._能分栏(要求['sessionId'],目标):
            return None
        已建=[None]

        def 打开():
            '分完返回新窗'
            def 落定(标识):
                '新窗'
                已建[0]=标识
            要求['actions']['分窗格'](要求['sessionId'],目标,落定)
            return 已建[0]

        自身.宿主['openWithFocus'](要求['sessionId'],打开)
        return 已建[0]

    def 浮出(自身,标签标识,矩形=None):
        '已经在浮动里的签不动'
        要求=自身._要求()
        表面=自身._挂载表面()
        if 表面 is None or 标签标识 not in 表面['layout']['tabs']:
            return
        if 查找标签窗格(表面['layout'],标签标识)['host']!='dock':
            return
        要求['actions']['浮出标签'](要求['sessionId'],标签标识,矩形)

    def 收回(自身,窗格标识):
        '不是浮动窗就不动'
        要求=自身._要求()
        表面=自身._挂载表面()
        节点=None if 表面 is None else 表面['layout']['nodes'].get(窗格标识)
        if 节点 is None or 节点.get('kind')!='pane' or 节点.get('host')!='float':
            return
        要求['actions']['收回浮窗'](要求['sessionId'],窗格标识)

    def _撤销(自身):
        '退一条意图'
        要求=自身._要求()
        要求['actions']['撤销'](要求['sessionId'])

    def _重做(自身):
        '再做一条意图'
        要求=自身._要求()
        要求['actions']['重做'](要求['sessionId'])

    def _屏(自身):
        '在屏会话和它的表面'
        会话标识=自身.已挂载.getSnapshot()
        if 会话标识 is None:
            return None
        认=自身.已认.get(会话标识)
        if 认 is None:
            return None
        表面=认['store'].getSnapshot()['bySession'].get(会话标识)
        if 表面 is None:
            return None
        return {'sessionId':会话标识,'surface':表面}

    def _挂载表面(自身):
        '在屏表面'
        屏=自身._屏()
        if 屏 is None:
            return None
        return 屏['surface']

    def _能分栏(自身,会话标识,窗格标识):
        '没量过的窗当作放得下'
        规则=自身.房间.get(会话标识)
        if 规则 is None:
            return True
        return 规则(窗格标识) is not False

    def _动作于(自身,会话标识):
        '这份已认领存储的动作'
        认=自身.已认.get(会话标识)
        if 认 is None:
            return None
        return 认['store'].actions

    def _要求(自身):
        '没有在屏表面就不能写'
        会话标识=自身.已挂载.getSnapshot()
        动作=None if 会话标识 is None else 自身._动作于(会话标识)
        if 会话标识 is None or 动作 is None:
            raise 右侧侧栏错误('sidebarRight: no session surface is mounted')
        return {'sessionId':会话标识,'actions':动作}
