'悬停卡里最多两条活动任务。时间在挂上时取一次，指针停着不走'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件
from .文案 import 目录中文,套用
from .会话日程状态 import 用会话日程事实
from .日程格式 import 任务名,格式化日程频率,下次运行两段,排序日程记录
from .任务管理图标 import 画时钟
from .相对时钟 import 现在毫秒

__all__=['会话日程悬停','悬停任务上限']

样式模块='session-schedule-mark'
悬停任务上限=2

def 确保样式(文档):
    '和行标记共用一份样式'
    注入模块样式文件(文档,'日程会话标记样式',os.path.join(os.path.dirname(__file__),'会话日程标记.module.css'),样式模块)

class 会话日程悬停:
    '逾期在前。超出两条写另有多少个'
    按会话={}

    def __new__(类,属性=None):
        '卡片还挂着就复用；卸掉后再挂重新取时间'
        键=属性.get('sessionId')
        已有=类.按会话.get(键)
        if 已有 is not None and 已有.根 is not None and getattr(已有.根,'isConnected',False):
            已有.属性=属性
            return 已有.渲染()
        自身=object.__new__(类)
        自身.属性=属性
        自身.根=None
        自身.现在=现在毫秒()
        自身.已订=False
        类.按会话[键]=自身
        return 自身.渲染()

    def 渲染(自身):
        '没有活动任务就什么都不画'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        if not 自身.已订 and callable(属性.get('useCatalog')) and hasattr(属性['useCatalog'],'_subscribe'):
            def 变更():
                '目录变了就重画，时间仍是挂上时那一次'
                自身.渲染()
            属性['useCatalog']._subscribe(变更)
            自身.已订=True
        事实=用会话日程事实(属性['useCatalog'],属性['sessionId'])
        if not 事实['hasActive']:
            return None
        根=文档.createElement('div')
        根.className='tasks'
        根.setAttribute('data-dsh-css',样式模块)
        根.setAttribute('data-session-schedule-tasks','')
        有序=排序日程记录(事实['records'],自身.现在)
        显示=有序[:悬停任务上限]
        省略=len(有序)-len(显示)
        for 记录 in 显示:
            两段=下次运行两段(记录['scheduledAt'],目录中文['time.locale'],自身.现在,目录中文)
            行=文档.createElement('div')
            行.className='task'
            行.setAttribute('data-dsh-css',样式模块)
            行.setAttribute('data-session-schedule-task','')
            图标盒=文档.createElement('span')
            图标盒.className='taskIcon'
            图标盒.setAttribute('data-dsh-css',样式模块)
            图标盒.setAttribute('aria-hidden','true')
            图标盒.appendChild(画时钟(文档,12))
            行.appendChild(图标盒)
            体=文档.createElement('span')
            体.className='taskBody'
            体.setAttribute('data-dsh-css',样式模块)
            名=文档.createElement('span')
            名.className='taskName'
            名.setAttribute('data-dsh-css',样式模块)
            名.textContent=任务名(记录)
            体.appendChild(名)
            时=文档.createElement('span')
            时.className='taskTiming'
            时.setAttribute('data-dsh-css',样式模块)
            时.appendChild(文档.createTextNode(格式化日程频率(记录,目录中文)+' · '))
            戳=文档.createElement('time')
            戳.setAttribute('dateTime',记录['scheduledAt'])
            戳.textContent=两段['absolute']
            时.appendChild(戳)
            时.appendChild(文档.createTextNode(' '))
            相对=文档.createElement('span')
            相对.className='taskRelative'
            相对.setAttribute('data-dsh-css',样式模块)
            相对.textContent=两段['relative']
            时.appendChild(相对)
            体.appendChild(时)
            行.appendChild(体)
            根.appendChild(行)
        if 省略>0:
            余=文档.createElement('div')
            余.className='omitted'
            余.setAttribute('data-dsh-css',样式模块)
            余.textContent=套用(目录中文['hover.more'],{'count':省略})
            根.appendChild(余)
        自身.根=根
        return 根
