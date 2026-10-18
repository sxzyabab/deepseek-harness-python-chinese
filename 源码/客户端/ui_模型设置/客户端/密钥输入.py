from ...模块.客户端.通告 import 取握手窗口
from .文案 import 中文
from .编辑器页脚 import 建,清空子,采集焦点,还原焦点

__all__=['密钥输入']

眼睛轮廓='M1.5 8C2.9 5.25 5.25 3.5 8 3.5C10.75 3.5 13.1 5.25 14.5 8C13.1 10.75 10.75 12.5 8 12.5C5.25 12.5 2.9 10.75 1.5 8Z'
眼睛开=眼睛轮廓+'M10 8C10 9.1 9.1 10 8 10C6.9 10 6 9.1 6 8C6 6.9 6.9 6 8 6C9.1 6 10 6.9 10 8Z'
眼睛关=眼睛轮廓+'M2.5 2.5L13.5 13.5'
图形命名空间='http://www.w3.org/2000/svg'

class 密钥输入:
    '只写的密钥框。非空草稿才能点开明文，换了内容就重新遮住'
    def __init__(自身,属性):
        '记下草稿。明文对照从空开始'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.明文=None
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props。明文对照留着'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '密码框。有内容时旁边是显示或隐藏'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        值=属性.get('value')
        if isinstance(值,str) is False:
            值=''
        快照=None
        if 自身.根 is None:
            自身.根=建(文档,'div','keyInput')
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            快照=采集焦点(文档,自身.根)
            清空子(自身.根)
        揭开=len(值)>0 and 自身.明文==值
        类名='input'
        if len(值)>0:
            类名=类名+' keyInputFilled'
        框=建(文档,'input',类名)
        框.type='text' if 揭开 else 'password'
        框.autocomplete='new-password'
        框.value=值
        if 属性.get('placeholder') is not None:
            框.placeholder=属性['placeholder']
        if 属性.get('aria-label') is not None:
            框.setAttribute('aria-label',属性['aria-label'])
        if 属性.get('aria-invalid') is True:
            框.setAttribute('aria-invalid','true')
        if 属性.get('aria-describedby') is not None:
            框.setAttribute('aria-describedby',属性['aria-describedby'])
        if 属性.get('required') is True:
            框.required=True
        if 属性.get('focusKey') is not None:
            框.setAttribute('data-dsh-focus',属性['focusKey'])
        框.disabled=属性.get('disabled') is True
        if 属性.get('autoFocus') is True:
            框.autofocus=True
        def 改(事件):
            '换内容就重新遮住，再把这次读到的值交给卡片'
            自身.明文=None
            改写=属性.get('onChange')
            if 改写 is not None:
                改写(事件)
        框.addEventListener('input',改)
        自身.根.appendChild(框)
        if len(值)>0:
            钮=建(文档,'button','keyToggle')
            钮.type='button'
            钮.setAttribute('aria-label',中文['keyHide'] if 揭开 else 中文['keyReveal'])
            钮.setAttribute('aria-pressed','true' if 揭开 else 'false')
            钮.disabled=属性.get('disabled') is True
            图=文档.createElementNS(图形命名空间,'svg')
            图.setAttribute('width','16')
            图.setAttribute('height','16')
            图.setAttribute('viewBox','0 0 16 16')
            图.setAttribute('fill','none')
            图.setAttribute('stroke','currentColor')
            图.setAttribute('stroke-width','1.3')
            图.setAttribute('stroke-linecap','round')
            图.setAttribute('aria-hidden','true')
            路=文档.createElementNS(图形命名空间,'path')
            路.setAttribute('d',眼睛关 if 揭开 else 眼睛开)
            图.appendChild(路)
            钮.appendChild(图)
            def 切换(事件):
                '在这份草稿上打开或关掉明文'
                if 揭开:
                    自身.明文=None
                else:
                    自身.明文=值
                自身.渲染()
            钮.addEventListener('click',切换)
            自身.根.appendChild(钮)
        还原焦点(文档,快照)
        if 属性.get('autoFocus') is True and 快照 is None:
            框.focus()
        return 自身.根
