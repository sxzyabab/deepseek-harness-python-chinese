'当前会话页眉上的提醒入口。一条时直接打开，多条才展开'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.锚定位置 import 使用锚定位置
from ...ui_基础界面组件.点外关闭 import 点外关闭
from ...ui_基础界面组件.icons import 图标垃圾桶16
from .文案 import 目录中文,套用
from .日程格式 import 任务名,格式化日程频率,下次运行两段,排序日程记录
from .任务管理图标 import 画时钟
from .相对时钟 import 现在毫秒

__all__=['日程目录动作']

样式模块='schedule-catalog-action'

def 确保样式(文档):
    '页眉目录样式只插一次'
    注入模块样式文件(文档,'日程目录动作样式',os.path.join(os.path.dirname(__file__),'日程目录动作.module.css'),样式模块)

class 日程目录动作:
    '打开时每秒刷新相对时间。会话不在打开态就收起'
    按会话={}

    def __new__(类,属性=None):
        '同一会话复用入口'
        def 取开(快照):
            '会话是否打开'
            return 快照.get('openState') if isinstance(快照,dict) else None
        开=属性['useSession'](取开) if callable(属性.get('useSession')) else None
        键=属性.get('sessionId',开)
        已有=类.按会话.get(键)
        if 已有 is not None and 已有.根 is not None and getattr(已有.根,'isConnected',False):
            已有.属性=属性
            return 已有.渲染()
        自身=object.__new__(类)
        自身.属性=属性
        自身.根=None
        自身.打开=False
        自身.现在=现在毫秒()
        自身.定时=None
        自身.拆位置=None
        自身.拆外面=None
        自身.菜单=None
        自身.已订=False
        类.按会话[键]=自身
        return 自身.渲染()

    def 拆菜单(自身):
        '卸掉弹层、定位和秒表'
        if 自身.定时 is not None:
            取握手窗口().clearInterval(自身.定时)
            自身.定时=None
        if callable(自身.拆位置):
            自身.拆位置()
            自身.拆位置=None
        if callable(自身.拆外面):
            自身.拆外面()
            自身.拆外面=None
        if 自身.菜单 is not None and 自身.菜单.parentNode is not None:
            自身.菜单.parentNode.removeChild(自身.菜单)
        自身.菜单=None

    def 渲染(自身):
        '还没有记录且不是失败时不占页眉'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        确保样式(文档)
        if not 自身.已订:
            def 变更():
                '会话或目录变了就重画'
                自身.渲染()
            if callable(属性.get('useSession')) and hasattr(属性['useSession'],'_subscribe'):
                属性['useSession']._subscribe(变更)
            if callable(属性.get('useCatalog')) and hasattr(属性['useCatalog'],'_subscribe'):
                属性['useCatalog']._subscribe(变更)
            自身.已订=True
        def 取开(快照):
            '会话打开态'
            return 快照.get('openState') if isinstance(快照,dict) else None
        def 取目录(快照):
            '整份目录'
            return 快照
        开态=属性['useSession'](取开)
        目录=属性['useCatalog'](取目录)
        记录=目录.get('records') or []
        状态=目录.get('status')
        删除中=目录.get('deleting') or []
        if 开态!='open':
            自身.打开=False
            自身.拆菜单()
            return None
        if len(记录)==0 and 状态!='error':
            自身.拆菜单()
            return None
        if 自身.根 is None:
            根=文档.createElement('div')
            根.className='root'
            标样式模块(根,样式模块)
            def 按键(事件):
                'Escape 关掉并回到按钮'
                if 事件.key!='Escape' or not 自身.打开:
                    return
                事件.preventDefault()
                自身.打开=False
                自身.拆菜单()
                自身.渲染()
                if 自身.触发 is not None:
                    自身.触发.focus()
            根.addEventListener('keydown',按键)
            触发=文档.createElement('button')
            触发.type='button'
            触发.className='trigger'
            标样式模块(触发,样式模块)
            触发.setAttribute('data-schedule-reminder-entry','')
            触发.appendChild(画时钟(文档,16))
            def 点触发(事件):
                '一条且已就绪就直接打开，否则展开'
                自身.点触发()
            触发.addEventListener('click',点触发)
            根.appendChild(触发)
            自身.根=根
            自身.触发=触发
        已知=len(记录)
        if 已知==0:
            名字=目录中文['trigger.label']
        else:
            键='trigger.one' if 已知==1 else 'trigger.other'
            名字=套用(目录中文[键],{'count':已知})
        自身.触发.setAttribute('aria-label',名字)
        唯一=记录[0] if 状态=='ready' and len(记录)==1 else None
        可展开=唯一 is None or 自身.打开
        if 可展开:
            自身.触发.setAttribute('aria-expanded','true' if 自身.打开 else 'false')
        else:
            自身.触发.removeAttribute('aria-expanded')
        自身.唯一=唯一
        自身.记录=记录
        自身.状态=状态
        自身.删除中=删除中
        if 自身.打开:
            自身.挂菜单(文档,窗口)
        else:
            自身.拆菜单()
        return 自身.根

    def 点触发(自身):
        '刷新时钟。单条直接进详情'
        自身.现在=现在毫秒()
        if 自身.唯一 is not None and not 自身.打开:
            自身.属性['openTaskDetail'](自身.唯一['id'])
            return
        自身.打开=not 自身.打开
        if 自身.打开:
            窗口=取握手窗口()
            def 跳动():
                '打开期间每秒重画距离'
                自身.现在=现在毫秒()
                自身.渲染()
            自身.定时=窗口.setInterval(跳动,1000)
        自身.渲染()

    def 挂菜单(自身,文档,窗口):
        '固定在按钮下面'
        if 自身.菜单 is None:
            菜单=文档.createElement('ul')
            菜单.className='menu'
            标样式模块(菜单,样式模块)
            菜单.setAttribute('aria-label',目录中文['list.aria'])
            菜单.style.visibility='hidden'
            菜单.style.left='0px'
            菜单.style.top='0px'
            文档.body.appendChild(菜单)
            自身.菜单=菜单
            自身.拆位置=使用锚定位置({
                'open':True,'anchor':自身.触发,'panel':菜单,'window':窗口,
                'side':'bottom','gap':5,'margin':16,
            })
            def 置关(打开):
                '点外面关掉'
                if 打开 is False:
                    自身.打开=False
                    自身.渲染()
            自身.拆外面=点外关闭(自身.根,True,置关,菜单)
        while 自身.菜单.firstChild is not None:
            自身.菜单.removeChild(自身.菜单.firstChild)
        if 自身.状态=='loading':
            项=文档.createElement('li')
            项.className='row'
            标样式模块(项,样式模块)
            项.setAttribute('role','status')
            项.textContent=目录中文['list.loading']
            自身.菜单.appendChild(项)
        if 自身.状态=='error':
            项=文档.createElement('li')
            项.className='row'
            标样式模块(项,样式模块)
            警=文档.createElement('span')
            警.setAttribute('role','alert')
            警.textContent=目录中文['list.error']
            项.appendChild(警)
            重=文档.createElement('button')
            重.type='button'
            重.textContent=目录中文['list.retry']
            def 点重(事件):
                '再读目录'
                自身.属性['onRetry']()
            重.addEventListener('click',点重)
            项.appendChild(重)
            自身.菜单.appendChild(项)
        行=排序日程记录(自身.记录,自身.现在)
        for 记录 in 行:
            逾期=取握手窗口().Date.parse(记录['scheduledAt'])<=自身.现在
            两段=下次运行两段(记录['scheduledAt'],目录中文['time.locale'],自身.现在,目录中文)
            项=文档.createElement('li')
            项.className='row rowTask rowOverdue' if 逾期 else 'row rowTask'
            标样式模块(项,样式模块)
            体=文档.createElement('span')
            体.className='body'
            标样式模块(体,样式模块)
            开=文档.createElement('button')
            开.type='button'
            开.className='openButton'
            标样式模块(开,样式模块)
            开.setAttribute('aria-label',套用(目录中文['list.open'],{'title':任务名(记录)}))
            def 点开(事件,标识=记录['id']):
                '关掉菜单再打开详情'
                自身.打开=False
                自身.属性['openTaskDetail'](标识)
                自身.渲染()
            开.addEventListener('click',点开)
            题=文档.createElement('span')
            题.className='title'
            标样式模块(题,样式模块)
            题.textContent=任务名(记录)
            开.appendChild(题)
            体.appendChild(开)
            元=文档.createElement('span')
            元.className='metadata metadataOverdue' if 逾期 else 'metadata'
            标样式模块(元,样式模块)
            段=文档.createElement('span')
            段.textContent=格式化日程频率(记录,目录中文)
            元.appendChild(段)
            体.appendChild(元)
            下次=文档.createElement('span')
            下次.className='nextRun metadataOverdue' if 逾期 else 'nextRun'
            标样式模块(下次,样式模块)
            前=文档.createElement('span')
            前.textContent=目录中文['list.nextRun']+' '
            下次.appendChild(前)
            戳=文档.createElement('time')
            戳.setAttribute('dateTime',记录['scheduledAt'])
            戳.textContent=两段['absolute']
            下次.appendChild(戳)
            相对=文档.createElement('span')
            相对.className='nextRunRelative'
            标样式模块(相对,样式模块)
            相对.textContent=两段['relative']
            下次.appendChild(相对)
            体.appendChild(下次)
            项.appendChild(体)
            删=文档.createElement('button')
            删.type='button'
            删.className='deleteButton'
            标样式模块(删,样式模块)
            删.setAttribute('aria-label',套用(目录中文['delete.label'],{'title':任务名(记录)}))
            进行中=记录['id'] in 自身.删除中
            删.setAttribute('title',目录中文['delete.pending'] if 进行中 else 目录中文['delete.action'])
            删.disabled=进行中
            图=图标垃圾桶16({'window':窗口,'size':14})
            if 图 is not None:
                删.appendChild(图)
            def 点删(事件,标识=记录['id']):
                '删这一条'
                自身.属性['onDelete'](标识)
            删.addEventListener('click',点删)
            项.appendChild(删)
            自身.菜单.appendChild(项)
