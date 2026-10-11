'可在本地调整高度的原始数据面板；指针捕获拥有拖动寿命'

__all__=['检查器详情']

def 夹百分比(值):
    '高度限制在 15% 到 80%'
    return max(15,min(80,值))

def 矩形高(矩形):
    'DOMRect 或字典上的高度'
    if 矩形 is None:
        return 0
    if isinstance(矩形,dict):
        return 矩形.get('height',0)
    return 矩形.height

class 检查器详情:
    '从上沿调整原始数据区，同时保持表格可见'
    def __init__(自身,属性):
        '记下原文、关闭回调和初始 40% 高度'
        自身.属性=属性
        自身.百分比=40
        自身.拖动=None
        自身.面板=None
        自身.标识=f'details-{id(自身)}'

    def 更新(自身,属性):
        '刷新 props；高度留在这一次挂载上'
        自身.属性=属性

    def _调整(自身,事件):
        '按指针位移改高度'
        当前=自身.拖动
        if 当前 is None or 当前['pointerId']!=事件.pointerId:
            return
        自身.百分比=夹百分比((当前['height']+当前['y']-事件.clientY)/当前['available']*100)

    def _停止(自身,事件):
        '松开或取消时释放指针捕获'
        if 自身.拖动 is None or 自身.拖动['pointerId']!=事件.pointerId:
            return
        自身.拖动=None
        if 事件.currentTarget.hasPointerCapture(事件.pointerId):
            事件.currentTarget.releasePointerCapture(事件.pointerId)

    def _按下(自身,事件):
        '主键开始拖动'
        if 事件.button!=0 or 自身.拖动 is not None:
            return
        元素=自身.面板
        父=None if 元素 is None else 元素.parentElement
        可用=0 if 父 is None else 矩形高(父.getBoundingClientRect())
        if 元素 is None or 可用==0:
            return
        事件.preventDefault()
        高度=矩形高(元素.getBoundingClientRect())
        自身.拖动={'pointerId':事件.pointerId,'y':事件.clientY,'height':高度,'available':可用}
        事件.currentTarget.setPointerCapture(事件.pointerId)

    def _松开(自身,事件):
        '移动结束时再记一次高度并停止'
        自身._调整(事件)
        自身._停止(事件)

    def _丢失捕获(自身,事件=None):
        '捕获丢失则放弃拖动'
        自身.拖动=None

    def _按键(自身,事件):
        '上下方向键和 Home/End 调整高度'
        键=事件.key
        if 键=='ArrowUp':
            自身.百分比=夹百分比(自身.百分比+5)
        elif 键=='ArrowDown':
            自身.百分比=夹百分比(自身.百分比-5)
        elif 键=='Home':
            自身.百分比=15
        elif 键=='End':
            自身.百分比=80
        else:
            return
        事件.preventDefault()

    def 渲染(自身):
        '分隔条、标题和原文或子内容'
        属性=自身.属性
        翻译=属性['t']
        子=属性.get('children')
        体={'type':'pre','role':'alert' if 属性.get('failed') else None,'text':属性.get('text','')}
        if 子 is not None:
            体={'type':'div','className':'objectDetails','children':子}
        return {
            'type':'div',
            'id':自身.标识,
            'className':'details',
            'ref':自身._记面板,
            'style':{'flexBasis':f'{自身.百分比}%'},
            'separator':{
                'role':'separator',
                'tabIndex':0,
                'aria-orientation':'horizontal',
                'aria-controls':自身.标识,
                'aria-label':翻译('table.resizeDetails'),
                'aria-valuemin':15,
                'aria-valuemax':80,
                'aria-valuenow':round(自身.百分比),
                'className':'detailsResize',
                'onPointerDown':自身._按下,
                'onPointerMove':自身._调整,
                'onPointerUp':自身._松开,
                'onPointerCancel':自身._停止,
                'onLostPointerCapture':自身._丢失捕获,
                'onKeyDown':自身._按键,
            },
            'toolbar':{
                'className':'toolbar',
                'title':翻译('table.raw'),
                'close':翻译('table.close'),
                'onClose':属性['close'],
            },
            'body':体,
        }

    def _记面板(自身,元素):
        '挂上面板元素，供拖动测量'
        自身.面板=元素

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
