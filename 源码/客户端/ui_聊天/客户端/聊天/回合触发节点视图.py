from ....ui_基础界面组件.icons import 图标
from ....ui_对话.异常 import 标样式模块
from .上下文体 import 须知体
from .回合触发 import 回合触发详情
from .消息铬 import 格式化消息时钟
from .用披露 import 注入聊天样式

__all__=['回合触发节点视图']

样式模块='turn-trigger'
图标名={
    'request':'browse-16',
    'goal':'goal-16',
    'agent':'send-14',
    'team':'agent-preset-16',
    'subagent':'agent-preset-16',
    'github':'branch-16',
    'webhook':'globe-14',
    'schedule':'queue-14',
    'job':'queue-14',
    'plugin':'cordis-plugin-14',
}


class 回合触发节点视图:
    '非人类回合触发的可展开说明'
    def __init__(自身,属性=None):
        '记下触发节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.打开=False
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '标题、时间和说明。展开后是须知正文'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'回合触发节点视图.module.css')
        翻译=属性.get('t')
        if not callable(翻译):
            def 翻译(键,参数=None):
                '没有文案表时返回键'
                return 键
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        详情=回合触发详情(数据)
        根=文档.createElement('section')
        根.className='root'
        标样式模块(根,样式模块)
        根.setAttribute('data-turn-trigger','')
        体号='trigger-body-'+str(id(自身))
        头=文档.createElement('button')
        头.className='header'
        标样式模块(头,样式模块)
        头.type='button'
        头.setAttribute('aria-expanded','true' if 自身.打开 else 'false')
        头.setAttribute('aria-controls',体号)
        图盒=文档.createElement('span')
        图盒.className='icon'
        标样式模块(图盒,样式模块)
        图盒.setAttribute('aria-hidden','true')
        图=图标(图标名.get(详情.get('icon'),'browse-16'),{'window':窗口})
        if 图 is not None:
            图盒.appendChild(图)
        头.appendChild(图盒)
        题=文档.createElement('span')
        题.className='title'
        标样式模块(题,样式模块)
        题.textContent=翻译(详情.get('title'))
        头.appendChild(题)
        时=文档.createElement('time')
        时.className='time'
        标样式模块(时,样式模块)
        毫秒=数据.get('time') if isinstance(数据.get('time'),(int,float)) else 0
        try:
            from datetime import datetime as 日期时间,timezone as 时区
            时.setAttribute('dateTime',日期时间.fromtimestamp(毫秒/1000,时区.utc).isoformat())
        except (OverflowError,OSError,ValueError):
            时.setAttribute('dateTime','')
        时.textContent=格式化消息时钟(毫秒,翻译)
        头.appendChild(时)
        箭头=图标('chevron-down-14',{'window':窗口,'className':'openChevron' if 自身.打开 else 'chevron'})
        if 箭头 is not None:
            标样式模块(箭头,样式模块)
            头.appendChild(箭头)

        def 切换(事件=None):
            '翻转说明'
            自身.打开=not 自身.打开
            自身.渲染()

        头.addEventListener('click',切换)
        根.appendChild(头)
        if 自身.打开:
            体=文档.createElement('div')
            体.id=体号
            体.className='body'
            标样式模块(体,样式模块)
            释=文档.createElement('p')
            释.className='explanation'
            标样式模块(释,样式模块)
            释.textContent=翻译('message.trigger.explanation')
            体.appendChild(释)
            内容=文档.createElement('div')
            内容.className='content'
            标样式模块(内容,样式模块)
            须知=须知体(文档,窗口,数据.get('content'),翻译)
            if 须知 is not None:
                内容.appendChild(须知)
            体.appendChild(内容)
            根.appendChild(体)
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根
