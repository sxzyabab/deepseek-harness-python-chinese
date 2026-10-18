'右栏里一条任务的正文。导航丢了就用上次绑定'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from .管理文案 import 管理中文
from .目录反馈 import 目录反馈
from .任务详情 import 任务详情,任务详情控制器
from .任务标签目标 import 用任务标签目标
from .任务管理图标 import 画时钟

__all__=['日程任务标签']

样式模块='task-manager-page'

def 确保样式(文档):
    '任务页正文用任务管理页样式'
    注入模块样式文件(文档,'日程任务管理页样式',os.path.join(os.path.dirname(__file__),'任务管理页.module.css'),样式模块)

class 日程任务标签:
    '有任务就画详情。读完仍没有就说任务已不可用'
    按页={}

    def __new__(类,属性=None):
        '同一张右栏页复用一份'
        信息=属性['useTabInfo']()
        键=信息['tab']['id']
        已有=类.按页.get(键)
        if 已有 is not None and 已有.根 is not None and getattr(已有.根,'isConnected',False):
            已有.属性=属性
            return 已有.渲染()
        自身=object.__new__(类)
        自身.属性=属性
        自身.根=None
        自身.控制=任务详情控制器()
        自身.详情=None
        自身.基线=None
        自身.已订=False
        自身.已写=None
        类.按页[键]=自身
        return 自身.渲染()

    def 渲染(自身):
        '导航优先。恢复的页用绑定'
        属性=自身.属性
        窗口=属性.get('window') or 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        if not 自身.已订 and callable(属性.get('useCatalog')) and hasattr(属性['useCatalog'],'_subscribe'):
            def 变更():
                '目录变了就重画'
                自身.渲染()
            属性['useCatalog']._subscribe(变更)
            自身.已订=True
        信息=属性['useTabInfo']()
        页=信息['tab']
        解析=用任务标签目标(属性['sessionId'],页,属性['taskBindings'])
        def 取(快照):
            '整份目录'
            return 快照
        目录=属性['useCatalog'](取)
        修订=页.get('navigation',{}).get('revision') if 解析['navigated'] else None
        if 自身.基线 is None or 自身.基线.get('revision')!=修订:
            自身.基线={'revision':修订,'request':目录.get('readRequest',0)}
        已答=目录.get('settled') and 目录.get('readSettled',0)>自身.基线['request']
        参数=解析['params']
        快照=自身.控制.快照(属性,目录,None if 参数 is None else 参数.get('id'))
        任务=快照['task']
        if 任务 is None and not 已答:
            属性['onRetry'](自身.基线['request'])
        if 解析['navigation'] is not None and 自身.已写!=解析['navigation']:
            属性['taskBindings'].写入(属性['sessionId'],{'id':页['id'],'kind':页['kind'],'contentId':页['contentId']},解析['navigation'])
            自身.已写=解析['navigation']
        if 解析['recovered'] is not None and (not 解析['navigated']) and 已答 and 快照['record'] is None:
            属性['taskBindings'].忘记(属性['sessionId'],{'id':页['id'],'kind':页['kind'],'contentId':页['contentId']})
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='tabBody'
            标样式模块(自身.根,样式模块)
        while 自身.根.firstChild is not None:
            自身.根.removeChild(自身.根.firstChild)
        if 任务 is None:
            if 已答:
                空=文档.createElement('div')
                空.className='empty'
                标样式模块(空,样式模块)
                空.setAttribute('role','status')
                空.appendChild(画时钟(文档,24))
                题=文档.createElement('h3')
                题.textContent=管理中文['detail.missing']
                空.appendChild(题)
                自身.根.appendChild(空)
            else:
                待定=目录.get('status')=='ready' and not 已答
                反馈=目录反馈({'window':窗口,'status':'loading' if 待定 else 目录.get('status'),'populated':False,'onRetry':属性.get('onRetry')})
                if 反馈 is not None:
                    自身.根.appendChild(反馈)
            return 自身.根
        详情属性=dict(快照['props'])
        详情属性['window']=窗口
        详情属性['task']=任务
        详情属性['authoritative']=快照['record'] is not None
        def 关掉():
            '删掉之后关掉这一页'
            页['actions']['close']()
        详情属性['onDeleted']=关掉
        详情属性['withinSession']=属性.get('sessionId')
        if 自身.详情 is None:
            自身.详情=任务详情(详情属性)
        节点=自身.详情(详情属性)
        if 节点 is not None:
            自身.根.appendChild(节点)
        return 自身.根
