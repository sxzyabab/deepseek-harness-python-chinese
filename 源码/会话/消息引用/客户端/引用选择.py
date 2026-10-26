'选区上的引用按钮'
import os
from ....客户端.模块.客户端.通告 import 取握手窗口
from ....客户端.ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点

__all__=['引用选择动作']

样式模块='message-quote'


def 窗口于(属性):
    '宿主窗口。没有时用当前页'
    if isinstance(属性,dict) and 'window' in 属性:
        return 属性['window']
    return 取握手窗口()


def 确保样式(文档):
    '把引用按钮样式插进文档'
    注入模块样式文件(
        文档,
        '消息引用选择样式',
        os.path.join(os.path.dirname(__file__),'引用选择.module.css'),
        样式模块,
    )


def 换根(自身,新根):
    '已经在页面上就替换'
    旧=自身.根
    if 旧 is not None and 旧.parentNode is not None and 旧 is not 新根:
        旧.parentNode.replaceChild(新根,旧)
    自身.根=新根
    return 新根


def 可引用(会话):
    '没被移除。子会话必须还能继续，并且父会话还在'
    if not isinstance(会话,dict) or 会话.get('removed') is True:
        return False
    子=会话.get('subagent')
    if 子 is None:
        return True
    if not isinstance(子,dict):
        return False
    地址=子.get('address')
    if not isinstance(地址,dict):
        return False
    return 地址.get('mode')=='continuable' and 子.get('parentAvailable') is True


class 引用选择动作:
    '可写对话里，选中文字之后的引用按钮'
    def __init__(自身,属性=None):
        '记下选区份额'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.已收=False
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换选区份额'
        自身.属性=属性

    def 可点(自身):
        '会话钩子说这一会话还能引用'
        读=自身.属性.get('useSession')
        if not callable(读):
            return False
        return 读(可引用) is True

    def 按下(自身,事件=None):
        '按下时先保住选区'
        if 事件 is not None and callable(getattr(事件,'preventDefault',None)):
            事件.preventDefault()

    def 点击(自身,事件=None):
        '读出选中文字，插进输入框，然后清掉选区'
        读=自身.属性.get('readText')
        文本=None if not callable(读) else 读()
        if 文本 is None:
            关闭=自身.属性.get('dismiss')
            if callable(关闭):
                关闭()
            return
        输入=自身.属性.get('inputActions')
        插入=None if not isinstance(输入,dict) else 输入.get('insertQuote')
        if not callable(插入) or 插入(文本) is not True:
            return
        清除=自身.属性.get('clearSelection')
        if callable(清除):
            清除()
        关闭=自身.属性.get('dismiss')
        if callable(关闭):
            关闭()

    def 渲染(自身):
        '不能引用时收起。能引用就画按钮'
        属性=自身.属性
        if not 自身.可点():
            if 自身.已收 is not True:
                自身.已收=True
                关闭=属性.get('dismiss')
                if callable(关闭):
                    关闭()
            窗口=窗口于(属性)
            根=窗口.document.createElement('span')
            根.setAttribute('hidden','')
            return 换根(自身,根)
        自身.已收=False
        窗口=窗口于(属性)
        文档=窗口.document
        确保样式(文档)
        译=属性['t']
        根=模块节点(文档,'button',样式模块,'action')
        根.type='button'
        根.setAttribute('aria-label',译('quote.add'))
        根.textContent=译('quote.add')
        根.addEventListener('pointerdown',自身.按下)
        根.addEventListener('click',自身.点击)
        return 换根(自身,根)
