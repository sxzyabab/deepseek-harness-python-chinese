from ...模块.客户端.通告 import 取握手窗口
from ...ui_基础界面组件.吐司 import 吐司

__all__=['文件拖拽反馈']

class 文件拖拽反馈:
    '源面板卸掉之后，失败提示仍留在壳的覆盖层上'
    def __init__(自身,属性):
        '记下失败源和关掉动作，并画出'
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
        '没有失败就不留节点。序号变了才换一条吐司'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        def 取失败(值):
            '读当前失败'
            return 值
        失败=属性['useFailure'](取失败)
        if 自身.已订 is not True:
            def 重画():
                '失败变了就重画'
                自身.渲染()
            if hasattr(属性['useFailure'],'_subscribe'):
                属性['useFailure']._subscribe(重画)
            自身.已订=True
        if isinstance(失败,dict) and 自身.根 is not None and 自身.序号==失败.get('sequence'):
            return 自身.根
        旧=自身.根
        父=None
        if 旧 is not None:
            父=旧.parentNode
            旧.remove()
            自身.根=None
        if not isinstance(失败,dict):
            自身.序号=None
            return None
        自身.序号=失败.get('sequence')
        根=吐司({
            'window':窗口,
            'text':失败.get('text') or '',
            'onDone':属性.get('dismiss'),
        }).渲染()
        自身.根=根
        if 父 is None and 'parent' in 属性:
            父=属性['parent']
        if 父 is not None and 根 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根
