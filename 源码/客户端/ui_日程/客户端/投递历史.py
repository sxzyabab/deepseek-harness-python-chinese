'某一任务已保存的投递记录'
from nicegui import ui as 界面
from ..异常 import 页面失败文案
from ...ui_基础界面组件.状态点 import 状态点
from .日程格式 import 格式化绝对时刻

__all__=['投递历史']

class 投递历史:
    '父组件调用渲染。按任务加载一页，可再取更早的'
    def __init__(自身,属性=None):
        '只记 props'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.页=None
        自身.加载中=False
        自身.失败=None
        自身.展开={}
        自身.保留打开=False

    def 更新(自身,属性):
        '换任务时清空已加载页'
        新=属性 if isinstance(属性,dict) else {}
        旧标识=(自身.属性.get('id'),自身.属性.get('sessionId'))
        自身.属性=新
        if (新.get('id'),新.get('sessionId'))!=旧标识:
            自身.页=None
            自身.失败=None
        自身.加载中=False

    def 渲染(自身):
        '先画壳再读第一页'
        if getattr(自身,'_壳',None) is None:
            自身._壳=界面.column().classes('schedule-history')
        if 自身.页 is None and 自身.加载中 is False and 自身.失败 is None:
            自身.加载()
        自身.重画()

    def 加载(自身,之前=None):
        'loadHistory；同步结果或 thenable'
        回调=自身.属性['loadHistory'] if 'loadHistory' in 自身.属性 else None
        if not callable(回调):
            自身.失败='delivery.error'
            自身.加载中=False
            return
        请求={'id':自身.属性['id'] if 'id' in 自身.属性 else None,'sessionId':自身.属性['sessionId'] if 'sessionId' in 自身.属性 else None,'limit':20}
        if 之前 is not None:
            请求['before']=之前
        自身.加载中=True
        自身.失败=None
        try:
            结果=回调(请求)
        except Exception:
            自身.加载中=False
            自身.失败='delivery.error'
            自身.重画()
            return
        def 应用(值,游标=之前):
            '合并更早的一页'
            自身.加载中=False
            if not isinstance(值,dict) or ('ok' in 值 and 值['ok'] is False):
                自身.失败='delivery.error'
            elif isinstance(值,dict) and 'value' in 值 and isinstance(值['value'],dict) and 'code' in 值['value']:
                码=值['value']['code']
                自身.失败='delivery.notFound' if 码=='schedule_not_found' else 'delivery.cursorError'
            elif isinstance(值,dict) and 'value' in 值 and isinstance(值['value'],dict) and 'records' in 值['value']:
                自身._并入(值['value'],游标)
                自身.失败=None
            elif isinstance(值,dict) and 'records' in 值:
                自身._并入(值,游标)
                自身.失败=None
            else:
                自身.失败='delivery.error'
            if getattr(自身,'_壳',None) is not None:
                自身.重画()
        if hasattr(结果,'then') and callable(结果.then):
            结果.then(lambda 值:应用(值), lambda _错误:应用({'ok':False}))
            return
        应用(结果)

    def _并入(自身,页,之前):
        '第一页替换，更早的页接在后面'
        if 之前 is None or 自身.页 is None:
            自身.页=页
            return
        已见={项['messageId'] for 项 in 自身.页['records'] if isinstance(项,dict) and 'messageId' in 项}
        记录=list(自身.页['records']) if 'records' in 自身.页 else []
        for 项 in 页['records'] if 'records' in 页 else []:
            if isinstance(项,dict) and 项.get('messageId') not in 已见:
                记录.append(项)
                已见.add(项.get('messageId'))
        自身.页={**页,'records':记录}

    def 重画(自身):
        '加载、失败、空、记录和加载更多'
        壳=getattr(自身,'_壳',None)
        if 壳 is None:
            return
        壳.clear()
        属性=自身.属性
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else (lambda 键,_参数=None:键)
        时区=属性['timeZone'] if 'timeZone' in 属性 else None
        页=自身.页 if isinstance(自身.页,dict) else None
        记录=页['records'] if 页 is not None and 'records' in 页 and isinstance(页['records'],list) else []
        有记录=len(记录)>0
        with 壳:
            if 自身.加载中 and 有记录 is False:
                with 界面.row():
                    状态点({'state':'ongoing'}).渲染()
                    界面.label(翻译('delivery.loading'))
            if 自身.失败 is not None:
                键=自身.失败
                界面.label(翻译(键))
                再试键='delivery.refresh' if 键=='delivery.cursorError' else 'delivery.retry'
                界面.button(翻译(再试键), on_click=lambda:自身.加载()).props('outline')
            if 自身.加载中 is False and 自身.失败 is None and 页 is not None and len(记录)==0:
                界面.icon('schedule', size='24px')
                界面.label(翻译('delivery.empty'))
            for 项 in 记录:
                if not isinstance(项,dict):
                    continue
                标识=项['messageId'] if 'messageId' in 项 else id(项)
                时刻=格式化绝对时刻(项['scheduledAt'] if 'scheduledAt' in 项 else '',翻译('time.locale'))
                界面.label(时刻)
                提示=项['prompt'] if 'prompt' in 项 and isinstance(项['prompt'],str) else ''
                if 提示!='':
                    开=自身.展开.get(标识) is True
                    界面.label(提示 if 开 or len(提示)<=160 else 提示[:160]+'…')
                    if len(提示)>160:
                        def 切换(当前=标识):
                            '展开或收起这条提示'
                            自身.展开[当前]=自身.展开.get(当前) is not True
                            自身.重画()
                        界面.button(翻译('delivery.collapse' if 开 else 'delivery.expand'), on_click=切换).props('flat')
            if 页 is not None and 'nextBefore' in 页 and 页['nextBefore'] is not None and 自身.失败 is None:
                游标=页['nextBefore']
                界面.button(翻译('delivery.loadMore'), on_click=lambda 游标=游标:自身.加载(游标)).props('outline')
            if 有记录 and 页 is not None and 页.get('earlierRecordsPruned') is True and 页.get('nextBefore') is None and 自身.加载中 is False and 自身.失败 is None:
                界面.label(翻译('delivery.pruned'))
                def 切换保留():
                    '展开保留规则'
                    自身.保留打开=not 自身.保留打开
                    自身.重画()
                界面.button(翻译('delivery.retention'), on_click=切换保留).props('flat')
                if 自身.保留打开:
                    保留=页['retention'] if 'retention' in 页 and isinstance(页['retention'],dict) else {}
                    天数=保留['days'] if 'days' in 保留 else 0
                    条数=保留['records'] if 'records' in 保留 else 0
                    界面.label(翻译('delivery.retentionBounds',{'days':天数,'records':条数}))
                    界面.label(翻译('delivery.retentionExplanation'))
