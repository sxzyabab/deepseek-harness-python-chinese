from ..ui_基础界面组件.设置表单 import 密钥字段,设置表单
from ..ui_基础界面组件.设置表单.字段 import 取值字段 as 基础取值字段

__all__=['取值字段','密钥字段','画出设置表单','跳过离开丢弃']

_离开表={}

class 取值字段(基础取值字段):
    '暂存值。说明按钮展开帮助。数字只提示键盘，不改写键入'
    def 渲染(自身):
        '画出字段。重画后仍挂回原处。帮助可以是一段文字、一个节点或多段节点'
        旧=自身.根
        父=None
        下一=None
        if 旧 is not None:
            父=旧.parentNode
            下一=旧.nextSibling
        根=基础取值字段.渲染(自身)
        if 根 is None:
            return None
        if 父 is not None and 根.parentNode is None:
            if 下一 is not None and 下一.parentNode is 父:
                父.insertBefore(根,下一)
            else:
                父.appendChild(根)
        属性=自身.属性 if isinstance(自身.属性,dict) else {}
        帮助=属性.get('help')
        if 自身.帮助开 is not True or not isinstance(帮助,dict):
            return 根
        内容=帮助.get('content')
        if not isinstance(内容,(list,tuple)):
            return 根
        区=根.lastElementChild
        if 区 is None or not str(区.id).endswith('-help'):
            return 根
        if 区.firstChild is not None:
            return 根
        for 项 in 内容:
            if hasattr(项,'tagName'):
                区.appendChild(项)
            elif isinstance(项,str) and 项!='':
                区.appendChild(根.ownerDocument.createTextNode(项))
        return 根

def 跳过离开丢弃(节点):
    '重画前拆掉旧根，不把这次删除当成离开页面'
    if 节点 is None:
        return
    记=_离开表.get(id(节点))
    if isinstance(记,dict):
        记['跳过']=True

def 画出设置表单(窗口,标签,状态,丢弃,保存,画控件):
    '各设置卡共用的表单。未提供命名空间时只留说明。离开页面丢掉暂存'
    子项=[]
    if isinstance(状态,dict) and 状态.get('available') is True:
        暂存=窗口.document.createElement('div')
        画控件(暂存)
        当前=暂存.firstChild
        while 当前 is not None:
            下一=当前.nextSibling
            子项.append(当前)
            当前=下一
    表单=设置表单({
        'window':窗口,
        'labels':标签,
        'state':状态 if isinstance(状态,dict) else {},
        'onSave':保存,
        'onDiscard':丢弃,
        'children':子项,
    })
    根=表单.渲染()
    if 表单.收尾.alive:
        表单.收尾.detach()
    _离开表[id(根)]={'丢弃':表单.拆除,'跳过':False,'表单':表单}
    原移除=根.remove
    def 移除():
        '删除节点时丢掉暂存。跳过标记表示这次只是重画'
        记下=_离开表.pop(id(根),None)
        if isinstance(记下,dict) and 记下['跳过'] is not True:
            记下['丢弃']()
        原移除()
    object.__setattr__(根,'remove',移除)
    return 根
