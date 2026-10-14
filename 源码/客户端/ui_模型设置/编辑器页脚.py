from nicegui import ui as 界面

__all__=['编辑器页脚','画输入类型']

def 画输入类型(界面,模型,字段,禁用,回退,翻译,变更):
    '文本与图片勾选；只剩一项时不可取消'
    模态=模型[字段] if isinstance(模型,dict) and 字段 in 模型 else None
    if isinstance(模态,list) and len(模态)>0:
        已选=list(模态)
    elif isinstance(回退,list) and len(回退)>0:
        已选=list(回退)
    else:
        已选=['text']
    界面.label(翻译('modelInputTypes'))
    for 种,键 in (('text','modelInputText'),('image','modelInputImage')):
        勾上=种 in 已选
        def 改(事件,本种=种,当前=tuple(已选)):
            '替换这一行的输入类型'
            下一=[值 for 值 in ('text','image') if (值==本种 and 事件.value is True) or (值!=本种 and 值 in 当前)]
            if 下一==list(当前):
                return
            补丁={字段:下一}
            if 字段=='inputModalities' and 'image' not in 下一:
                补丁['imagePixelBudget']=None
                补丁['imageMaxBytes']=None
            变更(补丁)
        框=界面.checkbox(翻译(键),value=勾上,on_change=改)
        if 禁用 or (len(已选)==1 and 勾上):
            框.disable()

class 编辑器页脚:
    'Cancel 只在提交飞行中拒绝输入，从不因只读而拒——只读卡仍须可关。父组件调用渲染，构造不画'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性

    def 更新(自身,属性):#刷新
        '记下最新 props'
        自身.属性=属性#最新

    def 渲染(自身):
        '画出取消与提交'
        翻译=自身.属性['t'] if 't' in 自身.属性 else None#翻译
        忙=bool(自身.属性['busy']) if 'busy' in 自身.属性 else False#飞行中
        提交禁用=bool(自身.属性['submitDisabled']) if 'submitDisabled' in 自身.属性 else False#提交门控
        提交闲=自身.属性['submitLabel'] if 'submitLabel' in 自身.属性 and 自身.属性['submitLabel'] else 'save'#闲时标签键
        提交忙=自身.属性['submitBusyLabel'] if 'submitBusyLabel' in 自身.属性 and 自身.属性['submitBusyLabel'] else 'saving'#忙时标签键
        取消键=自身.属性['cancelLabel'] if 'cancelLabel' in 自身.属性 and 自身.属性['cancelLabel'] else 'cancel'#取消键
        取消文=翻译(取消键) if 翻译 is not None else 取消键
        提交文=翻译(提交忙 if 忙 else 提交闲) if 翻译 is not None else (提交忙 if 忙 else 提交闲)
        def 点取消():
            '取消'
            回调=自身.属性['onCancel'] if 'onCancel' in 自身.属性 else None
            if 回调 is not None:
                回调()
        def 点提交():
            '提交'
            回调=自身.属性['onSubmit'] if 'onSubmit' in 自身.属性 else None
            if 回调 is not None:
                回调()
        with 界面.row().classes('editor-footer editorActions'):
            取消钮=界面.button(取消文, on_click=点取消)
            if 忙:
                取消钮.disable()
            提交钮=界面.button(提交文, on_click=点提交)
            if 提交禁用 or 忙:
                提交钮.disable()

    def __call__(自身,属性=None):#组件调用
        '对齐 React 组件调用'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
