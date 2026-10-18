from ...模块.客户端.通告 import 取握手窗口
from ...ui_基础界面组件.复选框 import 复选框
from ...ui_对话.异常 import 挂上
from .文案 import 中文
from .编辑器页脚 import 建,清空子

__all__=['模型输入类型']

种类表=('text','image')

class 模型输入类型:
    '文本和图片两种输入。还没覆盖时先显示继承来的类型'
    def __init__(自身,属性):
        '记下这一行的模型和字段'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '一组复选框。只剩一种时不能再取消它'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        if 自身.根 is None:
            自身.根=建(文档,'fieldset','modelInputTypes')
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            清空子(自身.根)
        模型=属性.get('model')
        if isinstance(模型,dict) is False:
            模型={}
        字段=属性.get('field')
        现有=模型.get(字段)
        if isinstance(现有,list) and len(现有)>0:
            已选=现有
        else:
            回退=属性.get('fallback')
            已选=回退 if isinstance(回退,list) else ['text']
        位置=属性.get('position')
        自身.根.setAttribute('aria-label',中文['modelInputTypes']+' '+str(位置))
        题=建(文档,'legend','modelFieldLabel')
        题.textContent=中文['modelInputTypes']
        自身.根.appendChild(题)
        盒=建(文档,'div','modelInputChoices')
        禁用=属性.get('disabled') is True
        for 种类 in 种类表:
            文=中文['modelInputText'] if 种类=='text' else 中文['modelInputImage']
            勾着=种类 in 已选
            只剩=len(已选)==1 and 种类 in 已选
            def 改(勾,种类=种类):
                '按勾选重写这一行的输入类型。DeepSeek 去掉图片时丢掉图片限额'
                下一选=[]
                for 项 in 种类表:
                    if 项==种类:
                        if 勾:
                            下一选.append(项)
                    elif 项 in 已选:
                        下一选.append(项)
                下一=dict(模型)
                下一[字段]=下一选
                if 字段=='inputModalities' and 'image' not in 下一选:
                    if 'imagePixelBudget' in 下一:
                        del 下一['imagePixelBudget']
                    if 'imageMaxBytes' in 下一:
                        del 下一['imageMaxBytes']
                属性['onChange'](下一)
            挂上(盒,复选框({
                'window':窗口,
                'label':文,
                'checked':勾着,
                'disabled':禁用 or 只剩,
                'onChange':改,
            }))
        自身.根.appendChild(盒)
        return 自身.根
