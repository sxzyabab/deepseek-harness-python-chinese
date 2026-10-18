from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ..标签 import 标签
from ..icons import 图标信息描边常规

__all__=['取值字段','密钥字段']

样式模块='settings-field'

def 确保样式(文档):
    '字段样式只插一次'
    注入模块样式文件(
        文档,
        '设置字段样式',
        os.path.join(os.path.dirname(__file__),'字段.module.css'),
        样式模块,
    )

class 取值字段:
    '暂存的普通值。数字只提示键盘，不改用户打的字'
    def __init__(自身,属性=None):
        '记下字段，帮助默认合上'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.帮助开=False
        自身.根=None

    def 渲染(自身):
        '画出标签、覆盖徽章、输入和说明'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        if 自身.根 is not None:
            自身.根.remove()
        标识='' if 属性.get('id') is None else str(属性['id'])
        根=文档.createElement('div')
        根.className='field'
        标样式模块(根,样式模块)
        头=文档.createElement('div')
        头.className='head'
        标样式模块(头,样式模块)
        组=文档.createElement('div')
        组.className='labelGroup'
        标样式模块(组,样式模块)
        题=文档.createElement('label')
        题.className='label'
        标样式模块(题,样式模块)
        题.htmlFor=标识
        题.textContent='' if 属性.get('label') is None else str(属性['label'])
        组.appendChild(题)
        帮助=属性.get('help') if isinstance(属性.get('help'),dict) else None
        帮助标识=标识+'-help'
        if 帮助 is not None:
            帮钮=文档.createElement('button')
            帮钮.type='button'
            帮钮.className='helpButton'
            标样式模块(帮钮,样式模块)
            帮钮.setAttribute('aria-label','' if 帮助.get('label') is None else str(帮助['label']))
            帮钮.setAttribute('aria-expanded','true' if 自身.帮助开 else 'false')
            帮钮.setAttribute('aria-controls',帮助标识)
            图=图标信息描边常规({'window':窗口,'size':12})
            if 图 is not None:
                帮钮.appendChild(图)
            def 点帮(事件):
                '展开或收起说明'
                自身.帮助开=自身.帮助开 is False
                自身.渲染()
            帮钮.addEventListener('click',点帮)
            组.appendChild(帮钮)
        头.appendChild(组)
        if 属性.get('overridden') is True:
            徽=文档.createElement('span')
            徽.className='badges'
            标样式模块(徽,样式模块)
            牌=标签({'window':窗口,'tone':'neutral','children':'' if 属性.get('overriddenLabel') is None else str(属性['overriddenLabel'])}).渲染()
            if 牌 is not None:
                徽.appendChild(牌)
            复位=文档.createElement('button')
            复位.type='button'
            复位.className='reset'
            标样式模块(复位,样式模块)
            复位.disabled=属性.get('disabled') is True
            复位.textContent='' if 属性.get('resetLabel') is None else str(属性['resetLabel'])
            def 点复(事件):
                '恢复继承'
                回=属性.get('onReset')
                if 回 is not None:
                    回()
            复位.addEventListener('click',点复)
            徽.appendChild(复位)
            头.appendChild(徽)
        根.appendChild(头)
        框=文档.createElement('input')
        框.id=标识
        框.className='input'
        标样式模块(框,样式模块)
        框.type='text'
        if 属性.get('numeric') is True:
            框.inputMode='numeric'
        if 属性.get('invalid') is True:
            框.setAttribute('aria-invalid','true')
        消息标识=标识+'-message'
        有消息=属性.get('invalid') is True or (属性.get('hint') not in (None,''))
        描述=[]
        if 有消息:
            描述.append(消息标识)
        if 自身.帮助开:
            描述.append(帮助标识)
        if len(描述)>0:
            框.setAttribute('aria-describedby',' '.join(描述))
        框.value='' if 属性.get('text') is None else str(属性['text'])
        框.placeholder='' if 属性.get('placeholder') is None else str(属性['placeholder'])
        框.disabled=属性.get('disabled') is True
        def 变更(事件):
            '把草稿交给 onEdit'
            改=属性.get('onEdit')
            if 改 is not None:
                改(事件.target.value)
        框.addEventListener('input',变更)
        根.appendChild(框)
        if 有消息:
            句=文档.createElement('p')
            句.id=消息标识
            if 属性.get('invalid') is True:
                句.className='invalid'
                句.textContent='' if 属性.get('invalidLabel') is None else str(属性['invalidLabel'])
            else:
                句.className='hint'
                句.textContent='' if 属性.get('hint') is None else str(属性['hint'])
            标样式模块(句,样式模块)
            根.appendChild(句)
        if 帮助 is not None and 自身.帮助开:
            区=文档.createElement('div')
            区.id=帮助标识
            区.className='help'
            标样式模块(区,样式模块)
            区.setAttribute('role','region')
            区.setAttribute('aria-label','' if 帮助.get('label') is None else str(帮助['label']))
            内容=帮助.get('content')
            if isinstance(内容,str):
                区.textContent=内容
            elif hasattr(内容,'tagName'):
                区.appendChild(内容)
            根.appendChild(区)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 根

class 密钥字段:
    '只写的密钥。空白草稿不写入，浏览器不要自动填登录密码'
    def __init__(自身,属性=None):
        '记下字段'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None

    def 渲染(自身):
        '画出标签、是否已配置，和空白密码框'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        if 自身.根 is not None:
            自身.根.remove()
        标识='' if 属性.get('id') is None else str(属性['id'])
        根=文档.createElement('div')
        根.className='field'
        标样式模块(根,样式模块)
        头=文档.createElement('div')
        头.className='head'
        标样式模块(头,样式模块)
        题=文档.createElement('label')
        题.className='label'
        标样式模块(题,样式模块)
        题.htmlFor=标识
        题.textContent='' if 属性.get('label') is None else str(属性['label'])
        头.appendChild(题)
        徽=文档.createElement('span')
        徽.className='badges'
        标样式模块(徽,样式模块)
        语气='neutral' if 属性.get('configured') is True else 'quiet'
        牌=标签({'window':窗口,'tone':语气,'children':'' if 属性.get('stateLabel') is None else str(属性['stateLabel'])}).渲染()
        if 牌 is not None:
            徽.appendChild(牌)
        头.appendChild(徽)
        根.appendChild(头)
        框=文档.createElement('input')
        框.id=标识
        框.className='input'
        标样式模块(框,样式模块)
        框.type='password'
        框.autocomplete='new-password'
        框.value='' if 属性.get('text') is None else str(属性['text'])
        框.disabled=属性.get('disabled') is True
        def 变更(事件):
            '把密钥草稿交给 onEdit'
            改=属性.get('onEdit')
            if 改 is not None:
                改(事件.target.value)
        框.addEventListener('input',变更)
        根.appendChild(框)
        句=文档.createElement('p')
        句.className='hint'
        标样式模块(句,样式模块)
        句.textContent='' if 属性.get('hint') is None else str(属性['hint'])
        根.appendChild(句)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        return 根
