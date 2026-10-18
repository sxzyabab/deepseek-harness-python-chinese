from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['内联编辑器']

样式模块='inline-editor'

class 内联编辑器:
    '多行草稿。回车保存，Shift+回车换行，合成中的回车不动，Escape 取消'
    def __init__(自身,属性=None):
        '记下草稿和回调'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.拆除=None

    def 渲染(自身):
        '画出自动增高的 textarea，最多大约六行'
        if 自身.拆除 is not None:
            自身.拆除()
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(文档,'内联编辑器样式',os.path.join(os.path.dirname(__file__),'内联编辑器.module.css'),样式模块)
        if 自身.根 is None:
            框=文档.createElement('textarea')
            框.rows=1
            类名='editor'
            附加=属性.get('className')
            if isinstance(附加,str) and 附加!='':
                类名=类名+' '+附加
            框.className=类名
            标样式模块(框,样式模块)
            框.setAttribute('aria-label','' if 属性.get('label') is None else str(属性['label']))
            def 适配():
                '按内容增高，边框算进高度'
                框.style.height='auto'
                框.style.height=str(框.scrollHeight+框.offsetHeight-框.clientHeight)+'px'
            def 变更(事件):
                '把当前文字交给 onChange'
                改=属性.get('onChange')
                if 改 is not None:
                    改(事件.target.value)
            def 按键(事件):
                'Escape 取消。普通回车保存'
                if 事件.key=='Escape':
                    取消=属性.get('onCancel')
                    if 取消 is not None:
                        取消()
                    return
                合成=getattr(事件,'isComposing',False) is True or getattr(事件,'keyCode',None)==229
                if 事件.key!='Enter' or getattr(事件,'shiftKey',False) or 合成:
                    return
                事件.preventDefault()
                存=属性.get('onSave')
                if 存 is not None:
                    存()
            框.addEventListener('input',变更)
            框.addEventListener('keydown',按键)
            观察=None
            构造=getattr(窗口,'ResizeObserver',None)
            if 构造 is not None:
                观察=构造(适配)
                观察.observe(框)
            def 拆除():
                '卸掉尺寸观察'
                if 观察 is not None:
                    观察.disconnect()
            自身.拆除=拆除
            自身.根=框
            自身.适配=适配
            if 'parent' in 属性 and 属性['parent'] is not None:
                属性['parent'].appendChild(框)
            框.focus()
        框=自身.根
        文='' if 属性.get('value') is None else str(属性['value'])
        if 框.value!=文:
            框.value=文
        自身.适配()
        return 框
