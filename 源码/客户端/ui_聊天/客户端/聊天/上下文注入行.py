from ....ui_基础界面组件.icons import 图标
from ....ui_对话.异常 import 标样式模块
from .上下文体 import 选择上下文体
from .用披露 import 注入聊天样式,画披露行,挂节点

__all__=['上下文注入行','上下文消息节点视图']

样式模块='context-injection'


def 恒等(键,参数=None):
    '没有文案表时返回键'
    return 键


class 上下文注入行:
    '按生产者角色和形态画折叠的上下文'
    def __init__(自身,属性=None):
        '记下内容和来源'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.打开=False
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '工具增减、召回和普通注入用不同标题'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'上下文注入行.module.css')
        翻译=属性.get('t') if callable(属性.get('t')) else 恒等
        内容=属性.get('content') if isinstance(属性.get('content'),list) else []
        来源=属性.get('source')
        生产者=属性.get('producer') if isinstance(属性.get('producer'),dict) else {}
        形态=属性.get('form')
        选择=选择上下文体(形态,文档,窗口,内容,来源,翻译)
        工具块=None
        if len(内容)>0:
            全是工具=True
            for 块 in 内容:
                if not isinstance(块,dict) or 块.get('type') not in ('tool-addition','tool-removal'):
                    全是工具=False
                    break
            if 全是工具:
                工具块=内容
        增加=[]
        移除=[]
        if 工具块 is not None:
            for 块 in 工具块:
                if 块.get('type')=='tool-addition':
                    增加.append(块.get('toolName'))
                elif 块.get('type')=='tool-removal':
                    移除.append(块.get('toolName'))
        单个=工具块[0] if 工具块 is not None and len(工具块)==1 else None
        工具摘要=None
        if 工具块 is not None and 单个 is None:
            if len(增加)>0 and len(移除)>0:
                工具摘要=翻译('message.toolsChanged',{'added':len(增加),'removed':len(移除)})
            elif len(增加)>0:
                工具摘要=翻译('message.toolsAddedCount',{'count':len(增加)})
            else:
                工具摘要=翻译('message.toolsRemovedCount',{'count':len(移除)})
        if 单个 is not None:
            键='message.toolAdded' if 单个.get('type')=='tool-addition' else 'message.toolRemoved'
            标题=翻译(键,{'name':单个.get('toolName')})
        elif 工具块 is not None:
            标题=翻译('message.toolsUpdated')
        elif 生产者.get('role')=='recall':
            标题=翻译('message.contextRecall')
        else:
            标题=翻译('message.contextInjection')
        if 工具块 is not None:
            图=图标('browse-16',{'window':窗口})
        elif 生产者.get('role')=='recall':
            图=文档.createElement('span')
            图.setAttribute('data-context-recall-icon','')
            图.textContent='session'
        else:
            图=图标('browse-16',{'window':窗口})
        折叠=None
        if 工具摘要 is not None:
            折叠=文档.createDocumentFragment()
            点=文档.createElement('span')
            点.className='sep'
            标样式模块(点,样式模块)
            点.setAttribute('aria-hidden','true')
            摘=文档.createElement('span')
            摘.className='summary'
            标样式模块(摘,样式模块)
            摘.textContent=工具摘要
            折叠.appendChild(点)
            折叠.appendChild(摘)
        elif 工具块 is None and 生产者.get('label') is not None:
            折叠=文档.createDocumentFragment()
            点=文档.createElement('span')
            点.className='sep'
            标样式模块(点,样式模块)
            点.setAttribute('aria-hidden','true')
            源=文档.createElement('span')
            源.className='source'
            标样式模块(源,样式模块)
            源.setAttribute('data-context-source','')
            源.textContent=str(生产者.get('label'))
            折叠.appendChild(点)
            折叠.appendChild(源)
            if 选择.get('summary') is not None:
                点2=文档.createElement('span')
                点2.className='sep'
                标样式模块(点2,样式模块)
                点2.setAttribute('aria-hidden','true')
                摘=文档.createElement('span')
                摘.className='summary'
                标样式模块(摘,样式模块)
                摘.setAttribute('data-context-summary','')
                摘.textContent=选择['summary']
                折叠.appendChild(点2)
                折叠.appendChild(摘)

        def 切换():
            '单个工具变更不能展开'
            if 单个 is not None:
                return
            自身.打开=not 自身.打开
            自身.渲染()

        体=文档.createElement('div')
        体.className='body'
        标样式模块(体,样式模块)
        体.setAttribute('data-context-injection-body','')
        if 选择.get('rendered') is not None:
            体.setAttribute('data-context-form',选择['rendered'])
        if 工具块 is None:
            挂节点(体,选择.get('body'))
        else:
            改=文档.createElement('div')
            改.className='toolChanges'
            标样式模块(改,样式模块)
            if len(增加)>0:
                行=文档.createElement('div')
                行.textContent=翻译('message.toolsAdded',{'names':', '.join(str(名) for 名 in 增加)})
                改.appendChild(行)
            if len(移除)>0:
                行=文档.createElement('div')
                行.textContent=翻译('message.toolsRemoved',{'names':', '.join(str(名) for 名 in 移除)})
                改.appendChild(行)
            体.appendChild(改)
        自身.根=画披露行(文档,{
            'window':窗口,
            'className':'root',
            '样式模块':样式模块,
            'icon':图,
            'chevronClassName':'chevron',
            'title':标题,
            'collapsedContent':折叠,
            'keepContentWhenOpen':True,
            'open':自身.打开 and 单个 is None,
            'expandable':单个 is None,
            'expandOnRowClick':True,
            'onToggle':切换,
            'children':体,
        })
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(自身.根)
        return 自身.根


class 上下文消息节点视图:
    '注入上下文这一键的渲染器'
    def __init__(自身,属性=None):
        '从节点拆出内容和生产者'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.行=None
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '交给上下文注入行'
        属性=自身.属性
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        行属性={
            'window':属性['window'],
            'content':数据.get('content'),
            'source':数据.get('source'),
            'producer':数据.get('producer'),
            'form':数据.get('form'),
            't':属性.get('t'),
            'parent':属性.get('parent'),
        }
        if 自身.行 is None:
            自身.行=上下文注入行(行属性)
        else:
            自身.行.更新(行属性)
            自身.行.渲染()
        自身.根=自身.行.根
        return 自身.根
