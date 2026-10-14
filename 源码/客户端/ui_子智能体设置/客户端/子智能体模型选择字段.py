import json
import importlib.resources as 包资源
from nicegui import ui as 界面

__all__=['子智能体模型选择字段']

def _读样式():
    '读同目录样式并给类名加前缀。失败时异常文案只有样式读不到，不含路径'
    try:
        原文=包资源.files(__package__).joinpath('子智能体模型选择字段.module.css').read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None
    类名=(
        'catalogError','providerName','toggleLabel','modelGroup','modelName','permission',
        'toggleRow','selection','unavailable','conflict','models','notice','invalid','model','route','hint',
    )
    for 名 in sorted(类名, key=len, reverse=True):
        原文=原文.replace('.'+名,'.smodel-'+名)
    return 原文

界面.add_css(_读样式(),shared=True)

class 子智能体模型选择字段:
    '默认关闭的偏好与精确适配器路由'
    def __init__(自身,属性):
        '记下 props。父卡片会调用，构造时不画'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 更新(自身,属性):
        '刷新'
        自身.属性=属性

    def 画候选(自身,候选,禁用,翻译):
        '模型名、提供方路由，以及当前不可用标记'
        def 点模型(事件,键=候选['key'],已选=候选['selected']):
            '勾选或取消这一条精确路由'
            if 事件.value!=已选:
                自身.属性['toggleModel'](键)
        with 界面.row().classes('smodel-model'):
            框=界面.checkbox(value=候选['selected'], on_change=点模型)
            if 禁用:
                框.disable()
            with 界面.column().style('gap:0;min-width:0'):
                界面.label(候选['modelName']).classes('smodel-modelName')
                路由=候选['providerName']+' · '+候选['provider']+'/'+候选['model']
                界面.label(路由).classes('smodel-route')
            if 候选['available'] is not True:
                界面.label(翻译('subagentModelSelectionUnavailable')).classes('smodel-unavailable')

    def 渲染(自身):
        '偏好开关和已授权的精确路由；不画子会话目录'
        翻译=自身.属性['t']
        状态=自身.属性['state']
        可用分组=[]
        索引={}
        不可用=[]
        for 候选 in 状态['candidates']:
            if 候选['available'] is not True:
                不可用.append(候选)
                continue
            提供方=候选['provider']
            if 提供方 not in 索引:
                索引[提供方]=len(可用分组)
                可用分组.append({
                    'provider':提供方,
                    'providerName':候选['providerName'],
                    'candidates':[候选],
                })
            else:
                可用分组[索引[提供方]]['candidates'].append(候选)
        禁用=状态['writable'] is not True or 状态['saving'] is True
        def 点开关(事件):
            '翻转是否允许选模型'
            if 事件.value!=状态['enabled']:
                自身.属性['toggleEnabled']()
        with 界面.column().classes('smodel-permission'):
            with 界面.row().classes('smodel-toggleRow'):
                界面.label(翻译('subagentModelSelectionToggle')).classes('smodel-toggleLabel')
                开关=界面.switch(value=状态['enabled'], on_change=点开关)
                开关.props('aria-label='+json.dumps(翻译('subagentModelSelectionToggle'),ensure_ascii=False))
                if 禁用:
                    开关.disable()
            if 状态['enabled'] is True:
                提示键='subagentModelSelectionChoose'
            else:
                提示键='subagentModelSelectionOff'
            界面.label(翻译(提示键)).classes('smodel-hint')
        if 状态['enabled'] is True:
            with 界面.column().classes('smodel-selection'):
                if 状态['catalogStatus']=='loading':
                    界面.label(翻译('subagentModelSelectionLoading')).classes('smodel-notice')
                elif 状态['catalogStatus']=='error':
                    with 界面.row().classes('smodel-catalogError'):
                        界面.label(翻译('subagentModelSelectionLoadFailed'))
                        重试=界面.button(
                            翻译('subagentModelSelectionRetry'),
                            on_click=自身.属性['retryCatalog'],
                        ).props('flat no-caps')
                        if 状态['saving'] is True:
                            重试.disable()
                if 状态['catalogPartial'] is True:
                    界面.label(翻译('subagentModelSelectionPartial')).classes('smodel-notice')
                if len(状态['candidates'])>0:
                    with 界面.column().classes('smodel-models'):
                        界面.label(翻译('subagentModelSelectionAllowed')).classes('smodel-hint')
                        for 组 in 可用分组:
                            with 界面.column().classes('smodel-modelGroup'):
                                界面.label(组['providerName']).classes('smodel-providerName')
                                for 候选 in 组['candidates']:
                                    自身.画候选(候选,禁用,翻译)
                        if len(不可用)>0:
                            with 界面.column().classes('smodel-modelGroup'):
                                界面.label(翻译('subagentModelSelectionUnavailableGroup')).classes('smodel-providerName')
                                for 候选 in 不可用:
                                    自身.画候选(候选,禁用,翻译)
                elif 状态['catalogStatus']=='ready':
                    界面.label(翻译('subagentModelSelectionEmpty')).classes('smodel-notice')
                if 状态['invalid'] is True:
                    界面.label(翻译('subagentModelSelectionRequired')).classes('smodel-invalid')
        if 状态['conflicted'] is True:
            界面.label(翻译('subagentModelSelectionConflict')).classes('smodel-conflict')

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
