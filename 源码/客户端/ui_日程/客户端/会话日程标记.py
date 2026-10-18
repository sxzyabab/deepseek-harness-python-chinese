'侧栏会话行前面的时钟。只在这一会话还有活动任务时出现'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from .文案 import 目录中文,套用
from .会话日程状态 import 用会话日程事实
from .任务管理图标 import 画时钟

__all__=['会话日程标记']

样式模块='session-schedule-mark'

def 确保样式(文档):
    '会话标记样式只插一次'
    注入模块样式文件(文档,'日程会话标记样式',os.path.join(os.path.dirname(__file__),'会话日程标记.module.css'),样式模块)

class 会话日程标记:
    '点标记不激活会话。数量只放在无障碍名字里'
    按会话={}

    def __new__(类,属性=None):
        '同一会话复用一份标记'
        键=属性.get('sessionId')
        已有=类.按会话.get(键)
        if 已有 is not None and 已有.根 is not None and getattr(已有.根,'isConnected',False):
            已有.属性=属性
            return 已有.渲染()
        自身=object.__new__(类)
        自身.属性=属性
        自身.根=None
        自身.已订=False
        类.按会话[键]=自身
        return 自身.渲染()

    def 渲染(自身):
        '没有活动任务就拿掉标记'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        if not 自身.已订 and callable(属性.get('useCatalog')) and hasattr(属性['useCatalog'],'_subscribe'):
            def 变更():
                '目录变了就重画'
                自身.渲染()
            属性['useCatalog']._subscribe(变更)
            自身.已订=True
        事实=用会话日程事实(属性['useCatalog'],属性['sessionId'])
        if not 事实['hasActive']:
            if 自身.根 is not None and 自身.根.parentNode is not None:
                自身.根.parentNode.removeChild(自身.根)
            自身.根=None
            return None
        if 自身.根 is None:
            根=文档.createElement('span')
            根.className='mark'
            根.setAttribute('data-dsh-css',样式模块)
            根.setAttribute('data-session-schedule-mark','')
            def 挡住(事件):
                '不把点击冒到会话行'
                事件.stopPropagation()
            根.addEventListener('click',挡住)
            根.appendChild(画时钟(文档,14))
            字=文档.createElement('span')
            字.className='visuallyHidden'
            字.setAttribute('data-dsh-css',样式模块)
            根.appendChild(字)
            自身.根=根
            自身.字=字
        自身.字.textContent=套用(目录中文['mark.aria'],{'count':len(事实['records'])})
        return 自身.根
