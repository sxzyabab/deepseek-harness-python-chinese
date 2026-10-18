from ....ui_对话.异常 import 标样式模块
from .压缩命令卡 import 压缩命令卡
from .泛型命令卡 import 泛型命令卡
from .用披露 import 注入聊天样式,挂节点

__all__=['命令节点视图','手动压缩节点视图']

样式模块='chat-view'


class 命令节点视图:
    '普通命令。有同名专用视图时让给槽位'
    def __init__(自身,属性=None):
        '记下命令节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '槽位回退到泛型命令卡'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'聊天视图.module.css')
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        命令=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        根=文档.createElement('div')
        根.className='callRow'
        标样式模块(根,样式模块)
        属主={'node':命令,'window':窗口,'t':属性.get('t')}
        槽=属性.get('renderSlot')
        画出=None
        if callable(槽):
            回退=泛型命令卡(dict(属主))
            画出=槽('conversation.chat.commandview',属主,{
                'entryKey':命令.get('name') or '',
                'fallback':回退,
                'window':窗口,
            })
            if 画出 is 回退 or 画出 is None:
                画出=回退.根 if getattr(回退,'根',None) is not None else 回退.渲染()
        else:
            回退=泛型命令卡(属主)
            画出=回退.根
        挂节点(根,画出)
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根


class 手动压缩节点视图:
    '手动压缩命令和它的检查点画在一起'
    def __init__(自身,属性=None):
        '记下手动压缩节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '有压缩结果就交给压缩命令卡'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'聊天视图.module.css')
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        根=文档.createElement('div')
        根.className='callRow'
        标样式模块(根,样式模块)
        卡属性={'window':窗口,'node':数据.get('command'),'t':属性.get('t')}
        if 数据.get('compaction') is not None:
            卡属性['compaction']=数据['compaction']
        卡=压缩命令卡(卡属性)
        挂节点(根,卡.根)
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根
