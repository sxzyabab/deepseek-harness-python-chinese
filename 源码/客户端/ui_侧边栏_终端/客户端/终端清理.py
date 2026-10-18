from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,模块节点

__all__=['终端清理']

样式路径=os.path.join(os.path.dirname(__file__),'终端清理.module.css')
样式模块='TerminalCleanup'

class 终端清理:
    '失败清理可重试，不重建标签'
    def __init__(自身,属性=None):
        '记下份额并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.已订=False
        自身.渲染()
        用=自身.属性.get('useCloseFailures')
        if callable(getattr(用,'_subscribe',None)):
            def 变更(*参数):
                '失败列表变了就重画'
                自身.渲染()
            用._subscribe(变更)
            自身.已订=True

    def 更新(自身,属性):
        '换上一份份额'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '没有失败就不留节点'
        属性=自身.属性
        if isinstance(属性,dict) and 属性.get('window') is not None:
            窗=属性['window']
        else:
            窗=取握手窗口()
        文档=窗.document

        def 原样(值):
            '失败列表'
            return 值

        失败表=属性['useCloseFailures'](原样)
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        if not isinstance(失败表,(list,tuple)) or len(失败表)==0:
            return None
        注入模块样式文件(文档,'终端清理样式',样式路径,样式模块)
        根=模块节点(文档,'div',样式模块,'stack')
        for 失败 in 失败表:
            条=模块节点(文档,'div',样式模块,'notice')
            条.setAttribute('role','alert')
            字=文档.createElement('span')
            字.textContent='终端「'+str(失败['title'])+'」未能结束：'+str(失败['message'])
            钮=文档.createElement('button')
            钮.type='button'
            钮.textContent='重试'
            def 点(事件,标识=失败['id']):
                '再请求结束这一路'
                属性['retryClose'](标识)
            钮.addEventListener('click',点)
            条.appendChild(字)
            条.appendChild(钮)
            根.appendChild(条)
        自身.根=根
        父=属性.get('parent')
        if 父 is not None:
            父.appendChild(根)
        return 根

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
