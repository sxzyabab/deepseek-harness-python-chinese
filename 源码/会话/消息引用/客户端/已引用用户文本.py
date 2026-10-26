'引用节点按字面显示，不再解释'
from ....客户端.模块.客户端.通告 import 取握手窗口

__all__=['已引用用户文本']


def 窗口于(属性):
    '宿主窗口。没有时用当前页'
    if isinstance(属性,dict) and 'window' in 属性:
        return 属性['window']
    return 取握手窗口()


def 换根(自身,新根):
    '已经在页面上就替换'
    旧=自身.根
    if 旧 is not None and 旧.parentNode is not None and 旧 is not 新根:
        旧.parentNode.replaceChild(新根,旧)
    自身.根=新根
    return 新根


class 已引用用户文本:
    '解码后的引用原文。基础界面里还没有引用预览，这里只按字面画出'
    def __init__(自身,属性=None):
        '记下节点份额'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换节点份额'
        自身.属性=属性

    def 渲染(自身):
        '原文放进引用预览标记。悬停标题是全文'
        属性=自身.属性
        窗口=窗口于(属性)
        文档=窗口.document
        节点=属性.get('node')
        数据=None if not isinstance(节点,dict) else 节点.get('data')
        文本='' if not isinstance(数据,dict) or 数据.get('text') is None else str(数据.get('text'))
        根=文档.createElement('span')
        根.setAttribute('data-quote-preview','')
        根.textContent=文本
        根.title=文本
        return 换根(自身,根)
