from ..主题设置 import 字号最小,字号最大#字号边界

__all__=['字号行','样式表']

样式表='''
.row{display:flex;align-items:center;gap:8px;padding:16px 0;border-bottom:0.5px solid var(--dsw-alias-border-l2)}
.rowText{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;padding-right:48px}
.title{font-size:14px;font-weight:400;line-height:22px;color:var(--dsw-alias-label-primary)}
.desc{font-size:12px;font-weight:400;line-height:18px;color:var(--dsw-alias-label-tertiary)}
.control{display:inline-flex;align-items:center;gap:8px}
.stepper{position:relative;display:inline-flex;align-items:center;justify-content:center;min-width:72px;height:36px;border-radius:18px;background:var(--dsw-alias-bg-module-platform)}
.value{min-width:18px;text-align:center;font-size:14px;line-height:22px;font-variant-numeric:tabular-nums;color:var(--dsw-alias-label-primary)}
.unit{font-size:14px;line-height:22px;color:var(--dsw-alias-label-secondary)}
.arrows{position:absolute;right:8px;display:flex;flex-direction:column;gap:2px;opacity:0}
.stepper:hover .arrows,.stepper:focus-within .arrows{opacity:1}
.arrow{display:inline-flex;align-items:center;justify-content:center;width:17px;height:12px;padding:0;border:none;border-radius:3px;background:color-mix(in srgb,var(--dsw-alias-bg-layer-1) 75%,transparent);color:var(--dsw-alias-label-primary);cursor:pointer}
.arrow:hover:not(:disabled){background:var(--dsw-alias-bg-layer-1)}
.arrow:disabled{color:var(--dsw-alias-label-caption);cursor:default}
'''

class 字号行:
    """通用区字号行；显示已持久化字号。"""
    def __init__(自身,属性):
        """记下翻译、写字号与 store 钩。"""
        自身.属性=属性

    def 更新(自身,属性):
        """刷新合成 props。"""
        自身.属性=属性

    def 当前字号(自身):
        """从 useStore 选 fontSize。"""
        用存储=自身.属性['useStore']
        def 选字号(快照):
            """fontSize。"""
            return 快照['fontSize']
        return 用存储(选字号)

    def 渲染(自身):
        """与上游 JSX 同构。"""
        翻译=自身.属性['t']
        设字号=自身.属性['setFontSize']
        字号=自身.当前字号()
        def 增大():
            """加一。"""
            设字号(字号+1)
        def 减小():
            """减一。"""
            设字号(字号-1)
        return {
            'type':'font-size-row',
            'class':'row',
            'title':翻译('fontSize.title'),
            'description':翻译('fontSize.description'),
            'value':字号,
            'unit':翻译('fontSize.unit'),
            'increaseLabel':翻译('fontSize.increase'),
            'decreaseLabel':翻译('fontSize.decrease'),
            'increaseDisabled':字号>=字号最大,
            'decreaseDisabled':字号<=字号最小,
            'onIncrease':增大,
            'onDecrease':减小,
        }

    def __call__(自身,属性=None):
        """对齐 React 组件调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
