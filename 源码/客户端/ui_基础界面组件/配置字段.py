from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['配置字段']

样式模块='config-field'
序号=0

class 配置字段:
    '受控配置输入。有选项用下拉，密钥用密码框，否则用文本区'
    def __init__(自身,属性=None):
        '记下字段状态'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '画出标签、复位、控件和校验句'
        global 序号
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(文档,'配置字段样式',os.path.join(os.path.dirname(__file__),'配置字段.module.css'),样式模块)
        序号=序号+1
        标识='config-field-'+str(序号)
        标签=属性.get('labels') if isinstance(属性.get('labels'),dict) else {}
        根=文档.createElement('div')
        根.className='field'
        标样式模块(根,样式模块)
        头=文档.createElement('div')
        头.className='head'
        标样式模块(头,样式模块)
        题=文档.createElement('label')
        题.htmlFor=标识
        题.textContent='' if 属性.get('label') is None else str(属性['label'])
        头.appendChild(题)
        if 属性.get('overridden') is True:
            复位=文档.createElement('button')
            复位.type='button'
            复位.disabled=属性.get('disabled') is True
            复位.textContent='' if 标签.get('reset') is None else str(标签['reset'])
            def 点复位(事件):
                '去掉覆盖'
                回=属性.get('onReset')
                if 回 is not None:
                    回()
            复位.addEventListener('click',点复位)
            头.appendChild(复位)
        根.appendChild(头)
        值='' if 属性.get('value') is None else str(属性['value'])
        选项=属性['choices'] if isinstance(属性.get('choices'),(list,tuple)) else []
        def 变更(事件):
            '空选项当复位，其余交给 onChange'
            文=事件.target.value
            if len(选项)>0 and 文=='':
                回=属性.get('onReset')
                if 回 is not None:
                    回()
                return
            改=属性.get('onChange')
            if 改 is not None:
                改(文)
        if len(选项)>0:
            控=文档.createElement('select')
            空项=文档.createElement('option')
            空项.value=''
            空项.textContent='' if 标签.get('inherited') is None else str(标签['inherited'])
            控.appendChild(空项)
            for 项 in 选项:
                选=文档.createElement('option')
                选.value=str(项)
                选.textContent=str(项)
                控.appendChild(选)
            控.value=值
        elif 属性.get('secret') is True:
            控=文档.createElement('input')
            控.type='password'
            控.autocomplete='new-password'
            控.value=值
        else:
            控=文档.createElement('textarea')
            行数=值.count('\n')+1
            if 行数<1:
                行数=1
            if 行数>8:
                行数=8
            控.rows=行数
            控.value=值
        控.id=标识
        控.disabled=属性.get('disabled') is True
        if 属性.get('invalid') is True:
            控.setAttribute('aria-invalid','true')
        控.addEventListener('change',变更)
        控.addEventListener('input',变更)
        根.appendChild(控)
        if 属性.get('invalid') is True:
            句=文档.createElement('p')
            句.setAttribute('role','status')
            句.textContent='' if 标签.get('invalid') is None else str(标签['invalid'])
            根.appendChild(句)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 根
