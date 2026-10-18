from ...模块.客户端.通告 import 取握手窗口
from ...ui_基础界面组件.icons import 图标警告16
from ...ui_基础界面组件.吐司 import 吐司
from .呈现 import 提示文案

__all__=['插件刷新浮动提示']

class 插件刷新浮动提示:
    '离开插件页之后仍显示刷新失败'
    def __init__(自身,属性):
        '记下共享提示和词典，并画出'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.序号=None
        自身.渲染()

    def __call__(自身,属性=None):
        '宿主再次渲染时重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '只有 refresh-failed 才画吐司，其余提示不在这里显示'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        def 取提示(状态):
            '读当前提示'
            return 状态.get('notice')
        提示=属性['usePluginManager'](取提示)
        if 自身.已订 is not True:
            def 重画():
                '提示变了就重画'
                自身.渲染()
            属性['usePluginManager']._subscribe(重画)
            自身.已订=True
        if 提示 is not None and 提示.get('kind')=='refresh-failed' and 自身.根 is not None and 自身.序号==提示.get('seq'):
            return 自身.根
        旧=自身.根
        父=None
        if 旧 is not None:
            父=旧.parentNode
            旧.remove()
            自身.根=None
        if 提示 is None or 提示.get('kind')!='refresh-failed':
            自身.序号=None
            return None
        自身.序号=提示.get('seq')
        根=吐司({
            'window':窗口,
            'text':提示文案(提示),
            'icon':图标警告16({'window':窗口}),
            'onDone':属性['dismissNotice'],
        }).渲染()
        自身.根=根
        if 父 is None and 'parent' in 属性:
            父=属性['parent']
        if 父 is not None and 根 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根
