'回合里一张 schedule_create 卡片'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.按钮 import 处理按钮
from .管理文案 import 管理中文
from .文案 import 套用
from .日程格式 import 任务名,格式化日程频率
from .日程创建模型 import 日程创建卡模型
from .任务管理图标 import 画时钟

__all__=['日程创建卡']

样式模块='schedule-create-card'

def 确保样式(文档):
    '创建卡样式只插一次'
    注入模块样式文件(文档,'日程创建卡样式',os.path.join(os.path.dirname(__file__),'日程创建卡.module.css'),样式模块)

def 标(节点):
    '挂上创建卡样式模块'
    if 节点 is not None:
        标样式模块(节点,样式模块)
    return 节点

class 日程创建卡:
    '能打开的卡有整行热区和打开按钮。读不出任务就只留标题和原文'
    def __new__(类,属性=None):
        '按这次的块重画'
        窗口=属性['window'] if isinstance(属性,dict) and 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        模型=日程创建卡模型(属性.get('block') or {},属性.get('toolName') or '')
        有当前='currentTask' in 属性
        当前=属性.get('currentTask')
        已删=有当前 and 当前 is None
        if (not 有当前) or 当前 is None:
            任务=模型['task']
            标题=模型['title']
        else:
            任务=当前
            标题=任务名(当前)
        可开=任务 is not None and not 已删
        根=文档.createElement('div')
        根.className='card'
        标(根)
        根.setAttribute('data-tool','schedule_create')
        if 可开:
            热区=文档.createElement('button')
            热区.type='button'
            热区.className='cardOpen'
            标(热区)
            热区.setAttribute('aria-label',套用(管理中文['card.openLabel'],{'title':标题}))
            def 打开(事件,标识=任务['id']):
                '整行打开详情'
                属性['openTaskDetail'](标识)
            热区.addEventListener('click',打开)
            根.appendChild(热区)
        行=文档.createElement('div')
        行.className='row'
        标(行)
        前=文档.createElement('span')
        前.className='leading'
        标(前)
        前.appendChild(画时钟(文档,18))
        行.appendChild(前)
        体=文档.createElement('span')
        体.className='body'
        标(体)
        名=文档.createElement('span')
        名.className='title'
        标(名)
        名.textContent=标题
        体.appendChild(名)
        if 任务 is not None or 已删:
            频=文档.createElement('span')
            频.className='frequency'
            标(频)
            频.textContent=管理中文['card.deleted'] if 已删 else 格式化日程频率(任务,管理中文)
            体.appendChild(频)
        行.appendChild(体)
        if 可开:
            def 点开(标识=任务['id']):
                '打开按钮进详情'
                属性['openTaskDetail'](标识)
            钮=处理按钮(窗口,{
                'variant':'outline','size':'sm','className':'openButton',
                'children':管理中文['card.open'],
                'onClick':点开,
                'window':窗口,
            })
            标(钮)
            行.appendChild(钮)
        根.appendChild(行)
        if 任务 is None and 模型['output'] is not None:
            预=文档.createElement('pre')
            预.className='fallback'
            标(预)
            预.textContent=模型['output']
            根.appendChild(预)
        return 根
