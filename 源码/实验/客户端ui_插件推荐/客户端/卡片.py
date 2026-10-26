'enable_official_plugin 的正文：目录文本、详情、选择和结果'
import os
from ....客户端.模块.客户端.通告 import 取握手窗口
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ....客户端.ui_基础界面组件.按钮 import 按钮

__all__=['插件卡片正文']

样式模块='plugin-card'
开放阶段=('failed','unconfirmed')
原因键表=('unknown','unavailable','access-denied','not-live-root','closing')
编号={'n':0}


def 下一编号():
    '描述节点的标识'
    编号['n']=编号['n']+1
    return 'plugin-card-desc-'+str(编号['n'])


def 窗口于(属性):
    '宿主窗口。没有时用当前页'
    if isinstance(属性,dict) and 'window' in 属性:
        return 属性['window']
    return 取握手窗口()


def 确保样式(文档):
    '把插件卡片样式模块插进文档'
    注入模块样式文件(
        文档,
        '插件推荐卡片样式',
        os.path.join(os.path.dirname(__file__),'卡片.module.css'),
        样式模块,
    )


def 建(文档,标签名,类名):
    '造出带官方类名和样式模块标记的节点'
    return 模块节点(文档,标签名,样式模块,类名)


def 换根(自身,新根):
    '已经在页面上就替换'
    旧=自身.根
    if 旧 is not None and 旧.parentNode is not None and 旧 is not 新根:
        旧.parentNode.replaceChild(新根,旧)
    自身.根=新根
    return 新根


def 解析详情(值):
    '提案里必须有插件名'
    if not isinstance(值,dict) or not isinstance(值.get('name'),str):
        return None
    return 值


def 解析数据(值):
    '已记录的应用结果和错误码。坏数据当空'
    if not isinstance(值,dict):
        return {}
    if 'application' in 值 and 值['application'] is not None and 值['application']!='restart-required':
        return {}
    if 'errorCode' in 值 and 值['errorCode'] is not None and not isinstance(值['errorCode'],str):
        return {}
    return 值


def 原因键(原因):
    '没有专门文案的拒绝都读成不可用'
    if 原因 in 原因键表:
        return 原因
    return 'unavailable'


def 状态键(阶段,数据):
    '已启用时，要重启再收成重启文案'
    if 阶段 in ('dismissed','replaced','already-enabled','failed','unconfirmed'):
        return 阶段
    if 阶段=='enabled':
        if 数据.get('application')=='restart-required':
            return 'restart-required'
        return 'enabled'
    return None


class 插件卡片正文:
    '目录标题和描述、用户的选择，以及这次的结果'
    def __init__(自身,属性=None):
        '查询还没回来'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.查找=None
        自身.丢失=False
        自身.尝试=0
        自身.已查=None
        自身.待定=None
        自身.错误=None
        自身.根=None
        自身.描述标识=下一编号()
        自身.退订=None
        仓=自身.属性.get('catalog')
        if 仓 is not None and callable(getattr(仓,'subscribe',None)):
            def 变了():
                '记住的目录变了就重画'
                自身.渲染()
            自身.退订=仓.subscribe(变了)
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换框架份额。目录服务留在这一张上'
        旧=自身.属性
        自身.属性=属性
        for 键 in ('catalog','describe','openDetails','resolveText'):
            if 键 not in 属性 and 键 in 旧:
                自身.属性[键]=旧[键]

    def 拆除(自身):
        '卸掉目录监听'
        if callable(自身.退订):
            自身.退订()
        自身.退订=None

    def 插件名(自身):
        '提案详情里的包名。不合法就是 None'
        提案=自身.属性.get('proposal')
        if not isinstance(提案,dict):
            return None
        详情=解析详情(提案.get('details'))
        if 详情 is None:
            return None
        return 详情['name']

    def 确保查询(自身):
        '同一插件、会话、调用、阶段和尝试只查一次'
        名=自身.插件名()
        if 名 is None:
            return
        提案=自身.属性.get('proposal')
        决定=自身.属性.get('decision')
        阶段=None if not isinstance(决定,dict) else 决定.get('phase')
        标记=(名,自身.属性.get('sessionId'),None if not isinstance(提案,dict) else 提案.get('callId'),阶段,自身.尝试)
        if 自身.已查==标记:
            return
        自身.已查=标记
        描述=自身.属性.get('describe')
        if not callable(描述):
            return
        try:
            值=描述(自身.属性.get('sessionId'),提案.get('callId'))
        except Exception as 丢失:
            丢失=None
            if 自身.已查==标记:
                自身.丢失=True
                自身.查找=None
            return
        if 自身.已查!=标记:
            return
        if isinstance(值,dict) and 值.get('status')=='available':
            仓=自身.属性.get('catalog')
            if 仓 is not None:
                快照=dict(仓.getSnapshot())
                快照[名]=值
                仓.set(快照)
            自身.丢失=False
            自身.查找=值
        elif 值 is None:
            自身.丢失=True
            自身.查找=None
        else:
            自身.丢失=False
            自身.查找=值

    def 点重试查询(自身,事件=None):
        '丢掉这一次的查找，再查一次'
        自身.查找=None
        自身.丢失=False
        自身.尝试=自身.尝试+1
        自身.已查=None
        自身.渲染()

    def 点详情(自身,事件=None):
        '打开详情，不启用'
        名=自身.插件名()
        打开=自身.属性.get('openDetails')
        if 名 is not None and callable(打开):
            打开(名)

    def 跑(自身,动词):
        '操作可能已经写上。回复丢失仍可再试'
        自身.待定=动词
        自身.错误=None
        try:
            结果=自身.属性['act'](动词)
            if 结果 is None:
                自身.错误='transport'
            elif isinstance(结果,dict) and 结果.get('status') in ('refused','unconfirmed'):
                自身.错误=原因键(结果.get('reason'))
        except Exception as 丢失:
            丢失=None
            自身.错误='transport'
        自身.待定=None
        自身.渲染()

    def 点动词(自身,动词):
        '按钮点击入口'

        def 点(事件=None):
            '跑这一动词'
            自身.跑(动词)

        return 点

    def 渲染(自身):
        '名不合法时只留框架摘要。查询回来前用占位行'
        自身.确保查询()
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        确保样式(文档)
        译=属性['t']
        名=自身.插件名()
        根=建(文档,'div',None)
        if 名 is None:
            体=建(文档,'div','body')
            摘要=属性.get('summary')
            if hasattr(摘要,'tagName'):
                体.appendChild(摘要)
            elif isinstance(摘要,(list,tuple)):
                for 项 in 摘要:
                    if hasattr(项,'渲染'):
                        画出=项.渲染()
                        if 画出 is not None:
                            体.appendChild(画出)
                    elif hasattr(项,'tagName'):
                        体.appendChild(项)
            根.appendChild(体)
            return 换根(自身,根)
        仓=属性.get('catalog')
        缓存=None
        if 仓 is not None:
            表=仓.getSnapshot()
            if isinstance(表,dict) and 名 in 表:
                缓存=表[名]
        if 自身.丢失 or (isinstance(自身.查找,dict) and 自身.查找.get('status')=='refused'):
            当前=None if 自身.丢失 else 自身.查找
        else:
            当前=缓存 if 缓存 is not None else 自身.查找
        加载中=当前 is None and not 自身.丢失
        可用=当前 if isinstance(当前,dict) and 当前.get('status')=='available' else None
        决定=属性.get('decision') if isinstance(属性.get('decision'),dict) else None
        数据=解析数据({} if 决定 is None else 决定.get('data'))
        阶段=None if 决定 is None else 决定.get('phase')
        已结算=阶段 is not None and 阶段 not in 开放阶段
        状态=None
        if 阶段 is None:
            if isinstance(可用,dict) and 可用.get('enabled') is True:
                状态='already-enabled'
        else:
            状态=状态键(阶段,数据)
        提供=not 已结算 and not (isinstance(可用,dict) and 可用.get('enabled') is True)
        可启用=提供 and (可用 is not None or 加载中)
        查询问题=None
        if not 已结算 and not 加载中 and not (isinstance(当前,dict) and 当前.get('status')=='available'):
            if 自身.丢失 or 当前 is None:
                查询问题='lookup-failed'
            elif isinstance(当前,dict):
                查询问题=当前.get('reason')
        失败=None
        if 阶段=='failed' and isinstance(数据.get('errorCode'),str):
            失败='version-error' if 数据['errorCode']=='incompatible-version' else 'management-error'
        解析文本=属性.get('resolveText')
        提案=属性.get('proposal') if isinstance(属性.get('proposal'),dict) else {}
        if 可用 is None or not callable(解析文本):
            标题='' if 提案.get('title') is None else str(提案.get('title'))
        else:
            标题=解析文本(可用.get('title'))
        忙=自身.待定 is not None
        头=建(文档,'header','header')
        头.appendChild(文档.createTextNode(译('heading')))
        徽=建(文档,'span','badge')
        徽.textContent=译('official')
        头.appendChild(徽)
        根.appendChild(头)
        体=建(文档,'div','body')
        if 加载中:
            体.setAttribute('aria-busy','true')
        详情=建(文档,'button','details')
        详情.type='button'
        详情.addEventListener('click',自身.点详情)
        详情.setAttribute('aria-label',译('detailsFor',{'title':标题}))
        if 可用 is not None:
            详情.setAttribute('aria-describedby',自身.描述标识)
        强=建(文档,'strong','title')
        强.textContent=标题
        详情.appendChild(强)
        if 加载中 or 可用 is not None:
            描述=建(文档,'span','description')
            描述.id=自身.描述标识
            if 可用 is None:
                占位=建(文档,'span','placeholder')
                描述.appendChild(占位)
            else:
                描述.textContent=解析文本(可用.get('description'))
            详情.appendChild(描述)
        体.appendChild(详情)
        if 状态 is not None:
            状态行=建(文档,'p','status')
            状态行.setAttribute('role','status')
            状态行.textContent=译(状态)
            体.appendChild(状态行)
        if 失败 is not None:
            失败行=建(文档,'p','status')
            失败行.setAttribute('role','alert')
            失败行.textContent=译(失败)
            体.appendChild(失败行)
        if 查询问题 is not None:
            查询行=建(文档,'p','status')
            查询行.setAttribute('role','alert')
            查询行.textContent=译(查询问题)
            体.appendChild(查询行)
        if 提供 and 自身.错误 is not None:
            错误行=建(文档,'p','status')
            错误行.setAttribute('role','alert')
            错误行.textContent=译(自身.错误)
            体.appendChild(错误行)
        if 提供:
            脚=建(文档,'footer','footer')
            范围=建(文档,'span','scope')
            范围.textContent=译('scope')
            脚.appendChild(范围)
            动作=建(文档,'div','actions')
            if 查询问题 is not None:
                重试=按钮({
                    'window':窗口,'variant':'ghost','size':'sm','disabled':忙,
                    'children':译('retryLookup'),'onClick':自身.点重试查询,
                }).渲染()
                标样式模块(重试,样式模块)
                动作.appendChild(重试)
            忽略文='working' if 自身.待定=='dismiss' else 'dismiss'
            忽略=按钮({
                'window':窗口,'variant':'ghost','size':'sm','disabled':忙 or 加载中,
                'children':译(忽略文),'onClick':自身.点动词('dismiss'),
            }).渲染()
            标样式模块(忽略,样式模块)
            动作.appendChild(忽略)
            if 可启用:
                启用文='working' if 自身.待定=='enable' else ('enable' if 阶段 is None else 'retry')
                启用=按钮({
                    'window':窗口,'variant':'primary','size':'sm','disabled':忙 or 加载中,
                    'children':译(启用文),'onClick':自身.点动词('enable'),
                }).渲染()
                标样式模块(启用,样式模块)
                动作.appendChild(启用)
            脚.appendChild(动作)
            体.appendChild(脚)
        根.appendChild(体)
        return 换根(自身,根)
