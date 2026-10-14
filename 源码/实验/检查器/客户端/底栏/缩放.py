'拖拽和方向键把诊断底栏限制在视口高度的 20% 到 80%'
from nicegui import ui as 界面

__all__=['检查器缩放柄','最小高度','最大高度']

最小高度=20
最大高度=80

class 检查器缩放柄:
    '水平分隔条；高度是视口百分比，由面板记住'
    def __init__(自身,属性):
        '记下当前高度和回调'
        自身.属性=属性
        自身.高度=属性['height']
        自身.拖=None
        自身.柄=None

    def 调整(自身,值):
        '夹到允许区间后交给面板'
        次值=min(最大高度,max(最小高度,值))
        自身.高度=次值
        自身.属性['onResize'](次值)
        if 自身.柄 is not None:
            自身.柄.props(f'aria-valuenow={round(次值)}')

    def 事件(自身,事件):
        '指针拖拽按视口换算；方向键每次 5 个点'
        参数=事件.args if hasattr(事件,'args') else 事件
        if not isinstance(参数,dict):
            return
        种=参数.get('kind')
        if 种=='down':
            if 参数.get('button',0)!=0 or 自身.拖 is not None:
                return
            自身.拖={
                'pointerId':参数.get('pointerId'),
                'y':参数.get('y'),
                'height':自身.高度,
                'inner':参数.get('innerHeight') or 1,
            }
            return
        if 种 in ('move','up'):
            if 自身.拖 is None or 自身.拖['pointerId']!=参数.get('pointerId'):
                return
            内高=参数.get('innerHeight') or 自身.拖['inner'] or 1
            自身.调整(自身.拖['height']+(自身.拖['y']-参数.get('y',自身.拖['y']))/内高*100)
            if 种=='up':
                自身.拖=None
            return
        if 种=='step':
            自身.调整(自身.高度+参数.get('delta',0))
        elif 种=='set':
            自身.调整(参数.get('value',自身.高度))

    def 渲染(自身):
        '分隔条可指向、可键盘操作'
        柄=界面.element('div').classes('检查器缩放')
        柄.props(
            f'role=separator tabindex=0 aria-orientation=horizontal aria-controls={自身.属性["panelId"]} '
            f'aria-label="{自身.属性["label"]}" aria-valuemin={最小高度} aria-valuemax={最大高度} '
            f'aria-valuenow={round(自身.高度)}'
        )
        下脚本='''
(e)=>{
  if(e.button!==0) return;
  e.preventDefault();
  e.currentTarget.setPointerCapture(e.pointerId);
  emit({kind:"down",button:e.button,pointerId:e.pointerId,y:e.clientY,innerHeight:window.innerHeight});
}
'''
        移脚本='''
(e)=>{ emit({kind:"move",pointerId:e.pointerId,y:e.clientY,innerHeight:window.innerHeight}); }
'''
        起脚本='''
(e)=>{
  if(e.currentTarget.hasPointerCapture&&e.currentTarget.hasPointerCapture(e.pointerId)) e.currentTarget.releasePointerCapture(e.pointerId);
  emit({kind:"up",pointerId:e.pointerId,y:e.clientY,innerHeight:window.innerHeight});
}
'''
        键脚本='''
(e)=>{
  if(e.key==="ArrowUp"||e.key==="ArrowDown"){ e.preventDefault(); emit({kind:"step",delta:e.key==="ArrowUp"?5:-5}); }
  else if(e.key==="Home"){ e.preventDefault(); emit({kind:"set",value:20}); }
  else if(e.key==="End"){ e.preventDefault(); emit({kind:"set",value:80}); }
}
'''
        柄.on('pointerdown',自身.事件,js_handler=下脚本)
        柄.on('pointermove',自身.事件,js_handler=移脚本)
        柄.on('pointerup',自身.事件,js_handler=起脚本)
        柄.on('pointercancel',自身.事件,js_handler=起脚本)
        柄.on('keydown',自身.事件,js_handler=键脚本)
        自身.柄=柄
