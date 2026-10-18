import os
from ...异常 import 注入模块样式文件,标样式模块,挂上

__all__=['用户文本','纯文本','会话引用']

样式模块='user-text'

def 确保样式(文档):
    '用户文本样式只插一次'
    注入模块样式文件(
        文档,
        '用户文本样式',
        os.path.join(os.path.dirname(__file__),'用户文本.module.css'),
        样式模块,
    )

class 用户文本:
    '按规则把原文收成行内节点。失败时整段原文留下并上报'
    def __init__(自身,属性):
        '记下原文和事实'
        自身.属性=属性
        自身.根=None
        自身.求值器=None
        自身.渲染()

    def 渲染(自身):
        '节点槽按 id 挑选。没有登记就用回退文本'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        确保样式(文档)
        if 属性.get('useUserTextRevision') is not None:
            属性['useUserTextRevision'](lambda 修订:修订)
        if 自身.求值器 is None and 属性.get('createUserTextEvaluator') is not None:
            自身.求值器=属性['createUserTextEvaluator']()
        节点列=None
        错误=None
        try:
            if 自身.求值器 is not None:
                节点列=自身.求值器({'text':属性.get('text') or '','facts':属性.get('facts') or {}})
        except Exception as 原因:
            错误=原因
            节点列=None
        if 节点列 is None and 属性.get('reportTransformFailure') is not None:
            属性['reportTransformFailure'](错误)
        父=None
        if 自身.根 is not None:
            父=自身.根.parentNode
            自身.根.remove()
        elif 'parent' in 属性:
            父=属性['parent']
        根=文档.createElement('span')
        根.className='ellipsis' if 属性.get('ellipsis') is True else 'root'
        标样式模块(根,样式模块)
        文本=属性.get('text') or ''
        if 节点列 is None:
            根.textContent=文本
        else:
            for 节点 in 节点列:
                原文=文本[节点['start']:节点['end']]
                属主={'node':节点,'raw':原文,'interactive':属性.get('interactive') is True,'window':窗口}
                if 节点['id']=='text':
                    显示=节点['data'].get('display')
                    回退=原文 if 显示 is None else 显示
                else:
                    回退=原文
                回退节点=文档.createElement('span')
                回退节点.textContent=回退
                挂上(根,属性['renderSlot']('conversation.user.text.node',属主,{
                    'entryKey':节点['id'],
                    'fallback':回退节点,
                }))
        自身.根=根
        if 父 is not None:
            父.appendChild(自身.根)
        return 自身.根

class 纯文本:
    '没有业务解释的原文。display 缺席时用原文'
    def __init__(自身,属性):
        '画出这段文本'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        'display 为空串就什么都不显示'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        节点=属性['node']
        显示=节点['data'].get('display')
        文=节点['data']['text'] if 显示 is None else 显示
        根=文档.createElement('span')
        根.textContent=文
        自身.根=根
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        return 根

class 会话引用:
    '已确认的会话标签。不自己发明导航'
    def __init__(自身,属性):
        '画出不可点的会话芯片'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def 渲染(自身):
        '标签用节点数据，title 用原文'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        根=文档.createElement('span')
        根.textContent=属性['node']['data'].get('label') or ''
        根.setAttribute('data-appearance','session')
        if 属性.get('raw') is not None:
            根.setAttribute('title',属性['raw'])
        自身.根=根
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        return 根
