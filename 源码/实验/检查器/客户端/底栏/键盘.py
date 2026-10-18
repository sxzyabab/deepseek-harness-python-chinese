'把检查器文档里匹配到的按键转发到父级 iframe，不替换父窗口的命令仲裁'
from .....客户端.模块.客户端.通告 import 取握手窗口

__all__=['绑定检查器键盘']


def 绑定检查器键盘(框,读绑定):
    '按当前有效绑定安装转发，并返回拆除函数'
    释放箱={'函数':None}

    def 装上(事件=None):
        'iframe 加载后在内部文档上监听 keydown'
        if 释放箱['函数'] is not None:
            释放箱['函数']()
            释放箱['函数']=None
        文档=框.contentDocument
        if 文档 is None:
            return

        def 按下(键盘事件):
            '匹配当前绑定后，在父 iframe 上重发 keydown'
            if 键盘事件.defaultPrevented or 键盘事件.isComposing or 键盘事件.getModifierState('AltGraph'):
                return
            绑定=读绑定()
            if 绑定 is None or 绑定.get('secondCode') is not None or 绑定.get('code')!=键盘事件.code:
                return
            标志=[键盘事件.ctrlKey,键盘事件.altKey,键盘事件.shiftKey,键盘事件.metaKey]
            名称=('control','alt','shift','meta')
            修饰=绑定.get('modifiers') or []
            for 序号 in range(4):
                if (名称[序号] in 修饰)!=bool(标志[序号]):
                    return
            转发=取握手窗口().KeyboardEvent('keydown',{
                'key':键盘事件.key,
                'code':键盘事件.code,
                'ctrlKey':键盘事件.ctrlKey,
                'altKey':键盘事件.altKey,
                'shiftKey':键盘事件.shiftKey,
                'metaKey':键盘事件.metaKey,
                'repeat':键盘事件.repeat,
                'bubbles':True,
                'cancelable':True,
                'composed':True,
            })
            if not 框.dispatchEvent(转发):
                键盘事件.preventDefault()

        文档.addEventListener('keydown',按下)

        def 卸文档():
            '去掉内部文档上的 keydown'
            文档.removeEventListener('keydown',按下)

        释放箱['函数']=卸文档

    框.addEventListener('load',装上)
    装上()

    def 释放():
        '去掉 load 与 keydown'
        框.removeEventListener('load',装上)
        if 释放箱['函数'] is not None:
            释放箱['函数']()
            释放箱['函数']=None

    return 释放
