'列表、详情和任务页共用的加载与失败状态'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.按钮 import 处理按钮
from ...ui_基础界面组件.状态点 import 处理状态点
from ...ui_基础界面组件.icons import 图标警告16
from .管理文案 import 管理中文

__all__=['目录反馈']

样式模块='task-manager-page'

def 确保样式(文档):
    '任务管理页样式只插一次'
    注入模块样式文件(文档,'日程任务管理页样式',os.path.join(os.path.dirname(__file__),'任务管理页.module.css'),样式模块)

def 标(节点):
    '挂上任务管理页样式模块'
    if 节点 is not None:
        标样式模块(节点,样式模块)
    return 节点

class 目录反馈:
    '空面板居中。已经有内容时，失败用紧凑提示，刷新中的加载不挡行'
    def __new__(类,属性=None):
        '画出当前该出现的状态'
        窗口=属性['window'] if isinstance(属性,dict) and 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        状态=属性.get('status')
        有内容=属性.get('populated') is True
        重试=属性.get('onRetry')
        片段=文档.createDocumentFragment()
        if 状态=='loading' and not 有内容:
            空=文档.createElement('div')
            空.className='empty'
            标(空)
            空.setAttribute('role','status')
            空.setAttribute('aria-label',管理中文['list.loading'])
            点=处理状态点(窗口,{'state':'ongoing'})
            if 点 is not None:
                空.appendChild(点)
            片段.appendChild(空)
        if 状态=='error':
            if 有内容:
                盒=文档.createElement('div')
                盒.className='notice'
                标(盒)
                段=文档.createElement('p')
                段.setAttribute('role','alert')
                段.textContent=管理中文['list.error']
                盒.appendChild(段)
                钮=处理按钮(窗口,{'variant':'outline','size':'sm','children':管理中文['list.retry'],'onClick':重试,'window':窗口})
                盒.appendChild(钮)
                片段.appendChild(盒)
            else:
                空=文档.createElement('div')
                空.className='empty'
                标(空)
                图=图标警告16({'window':窗口,'size':24,'className':'emptyGlyph'})
                if 图 is not None:
                    标(图)
                    空.appendChild(图)
                段=文档.createElement('p')
                段.setAttribute('role','alert')
                段.className='emptyTitle'
                标(段)
                段.textContent=管理中文['list.error']
                空.appendChild(段)
                钮=处理按钮(窗口,{'variant':'outline','className':'emptyAction','children':管理中文['list.retry'],'onClick':重试,'window':窗口})
                标(钮)
                空.appendChild(钮)
                片段.appendChild(空)
        return 片段
