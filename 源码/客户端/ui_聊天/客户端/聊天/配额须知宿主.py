from ..文案 import 中文

__all__=['配额须知宿主']


def 原样(值):
    '整份快照'
    return 值


class 配额须知宿主:
    '全窗口只有一条额度须知。离开聊天面板也不丢掉'
    def __init__(自身,属性):
        '订须知并画出'
        自身.属性=属性
        自身.根=None
        自身.已订=False
        自身.渲染()

    def 渲染(自身):
        '没有须知就清空。有链上的认领就交给链，否则显示额度用尽'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        须知=属性['useNotice'](原样) if callable(属性.get('useNotice')) else None
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='quota-notice'
            if 属性.get('parent') is not None:
                属性['parent'].appendChild(自身.根)
        while 自身.根.firstChild is not None:
            自身.根.removeChild(自身.根.firstChild)
        if 须知 is None:
            return 自身.根
        业主={
            'code':须知.get('code') if isinstance(须知,dict) else None,
            'message':中文['message.failure.quota'],
            'dismiss':属性.get('dismissNotice'),
            'keepOpen':属性.get('keepNoticeOpen'),
            'window':窗口,
        }
        链=None
        if callable(属性.get('renderSlotChain')):
            链=属性['renderSlotChain']('shell.quota-notice',业主)
        if 链 is not None:
            自身.根.appendChild(链 if hasattr(链,'nodeType') else 文档.createTextNode(str(链)))
        else:
            条=文档.createElement('div')
            条.setAttribute('role','status')
            条.textContent=中文['message.failure.quota']
            if callable(属性.get('dismissNotice')):
                钮=文档.createElement('button')
                钮.setAttribute('type','button')
                钮.textContent='关闭'

                def 关掉(事件=None):
                    '关掉这条额度须知'
                    属性['dismissNotice']()

                钮.addEventListener('click',关掉)
                条.appendChild(钮)
            自身.根.appendChild(条)
        if not 自身.已订 and callable(getattr(属性.get('useNotice'),'_subscribe',None)):
            属性['useNotice']._subscribe(自身.渲染)
            自身.已订=True
        return 自身.根
