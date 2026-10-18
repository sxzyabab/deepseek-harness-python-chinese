from ...模块.客户端.通告 import 取握手窗口
import os
import weakref
from ...ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['设置表单']

样式模块='settings-form'

class 设置表单:
    '插件设置页的表单。离开时丢掉暂存。命名空间不在时只显示不可用'
    def __init__(自身,属性=None):
        '记下文案、状态和离开时的丢弃'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.盒={'丢':自身.属性.get('onDiscard')}
        def 离开(盒):
            '对象拆掉时丢掉暂存'
            回=盒.get('丢')
            if 回 is not None:
                回()
        自身.收尾=weakref.finalize(自身,离开,自身.盒)

    def 更新(自身,属性):
        '换成新的 props，并记住最新的丢弃回调'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.盒['丢']=自身.属性.get('onDiscard')

    def 拆除(自身):
        '离开页面时丢掉暂存'
        回=自身.盒.get('丢')
        自身.盒['丢']=None
        if 回 is not None:
            回()

    def 渲染(自身):
        '不可用只出一句。否则画出只读提示、控件和保存'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '设置表单样式',
            os.path.join(os.path.dirname(__file__),'设置表单.module.css'),
            样式模块,
        )
        状态=属性['state'] if isinstance(属性.get('state'),dict) else {}
        标签=属性['labels'] if isinstance(属性.get('labels'),dict) else {}
        if 状态.get('available') is not True:
            句=文档.createElement('p')
            句.className='unavailable'
            标样式模块(句,样式模块)
            句.setAttribute('role','status')
            句.textContent='' if 标签.get('unavailable') is None else str(标签['unavailable'])
            if 'parent' in 属性 and 属性['parent'] is not None:
                属性['parent'].appendChild(句)
            自身.根=句
            return 句
        根=文档.createElement('div')
        根.className='form'
        标样式模块(根,样式模块)
        if 状态.get('writable') is not True:
            只读=文档.createElement('p')
            只读.className='readOnly'
            标样式模块(只读,样式模块)
            只读.setAttribute('role','status')
            只读.textContent='' if 标签.get('readOnly') is None else str(标签['readOnly'])
            根.appendChild(只读)
        子=属性.get('children')
        if hasattr(子,'tagName'):
            根.appendChild(子)
        elif isinstance(子,(list,tuple)):
            for 项 in 子:
                if hasattr(项,'tagName'):
                    根.appendChild(项)
        脚=文档.createElement('div')
        脚.className='footer'
        标样式模块(脚,样式模块)
        if 状态.get('failed') is True:
            败=文档.createElement('p')
            败.className='failed'
            标样式模块(败,样式模块)
            败.setAttribute('role','status')
            败.textContent='' if 标签.get('saveFailed') is None else str(标签['saveFailed'])
            脚.appendChild(败)
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='save'
        标样式模块(钮,样式模块)
        挡住=状态.get('dirty') is not True or 状态.get('invalid') is True or 状态.get('saving') is True
        钮.disabled=挡住
        if 状态.get('saving') is True:
            钮.textContent='' if 标签.get('saving') is None else str(标签['saving'])
        else:
            钮.textContent='' if 标签.get('save') is None else str(标签['save'])
        def 点存(事件):
            '写入全部暂存'
            存=属性.get('onSave')
            if 存 is not None:
                存()
        钮.addEventListener('click',点存)
        脚.appendChild(钮)
        根.appendChild(脚)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 根
