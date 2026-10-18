'选中任务的已保存运行记录。卸下时丢掉还没回来的那一页'
import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.按钮 import 处理按钮
from ...ui_基础界面组件.状态点 import 处理状态点
from ...ui_基础界面组件.提示泡 import 处理提示泡
from ...ui_基础界面组件.icons import 图标警告16,图标信息描边常规
from .管理文案 import 管理中文
from .文案 import 套用
from .日程格式 import 格式化下次运行
from .任务管理图标 import 画时钟

__all__=['投递历史']

样式模块='task-manager-page'

def 确保样式(文档):
    '运行记录用任务管理页样式'
    注入模块样式文件(文档,'日程任务管理页样式',os.path.join(os.path.dirname(__file__),'任务管理页.module.css'),样式模块)

def 标(节点):
    '挂上样式模块'
    if 节点 is not None:
        标样式模块(节点,样式模块)
    return 节点

class 投递历史:
    '刷新会盖过还在进行的更早一页。卸下后晚到的结果不再写入'
    def __init__(自身,属性):
        '按任务和会话分页'
        自身.属性=属性
        自身.页=None
        自身.加载中=True
        自身.失败=None
        自身.保留开=False
        自身.纪元=0
        自身.进行中=False
        自身.根=None
        自身.已载=None

    def 加载(自身,之前=None):
        '一页 20 条。之前是更老一页的游标'
        if 自身.进行中:
            return
        自身.进行中=True
        自身.纪元=自身.纪元+1
        代=自身.纪元
        自身.加载中=True
        自身.失败=None
        请求={'id':自身.属性['id'],'sessionId':自身.属性['sessionId'],'limit':20}
        if 之前 is not None:
            请求['before']=之前
        try:
            结果=自身.属性['loadHistory'](请求)
        except Exception:
            if 代!=自身.纪元:
                return
            自身.进行中=False
            自身.加载中=False
            自身.失败={'key':'delivery.error','before':之前}
            自身.画出()
            return
        if 代!=自身.纪元:
            return
        自身.进行中=False
        自身.加载中=False
        if not isinstance(结果,dict) or not 结果.get('ok'):
            自身.失败={'key':'delivery.error','before':之前}
        elif isinstance(结果.get('value'),dict) and 'code' in 结果['value']:
            键='delivery.notFound' if 结果['value']['code']=='schedule_not_found' else 'delivery.cursorError'
            自身.失败={'key':键,'before':None}
        else:
            下一=结果['value']
            if 之前 is None or 自身.页 is None:
                自身.页=下一
            else:
                见过=set()
                记录=list(自身.页.get('records') or [])
                for 项 in 记录:
                    见过.add(项.get('messageId'))
                for 项 in 下一.get('records') or []:
                    if 项.get('messageId') not in 见过:
                        见过.add(项.get('messageId'))
                        记录.append(项)
                自身.页={**下一,'records':记录}
        自身.画出()

    def 画出(自身):
        '按当前页重画'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        确保样式(文档)
        if 自身.根 is None:
            自身.根=文档.createElement('div')
            自身.根.className='deliveryHistory'
            标(自身.根)
        根=自身.根
        while 根.firstChild is not None:
            根.removeChild(根.firstChild)
        根.setAttribute('aria-busy','true' if 自身.加载中 else 'false')
        滚=文档.createElement('div')
        滚.className='detailScroll'
        标(滚)
        有记录=自身.页 is not None and len(自身.页.get('records') or [])>0
        if 自身.加载中 and not 有记录:
            空=文档.createElement('div')
            空.className='empty'
            标(空)
            空.setAttribute('role','status')
            空.setAttribute('aria-label',管理中文['delivery.loading'])
            点=处理状态点(窗口,{'state':'ongoing'})
            if 点 is not None:
                空.appendChild(点)
            滚.appendChild(空)
        if 自身.失败 is not None:
            文=管理中文[自身.失败['key']]
            钮文=管理中文['delivery.refresh'] if 自身.失败['key']=='delivery.cursorError' else 管理中文['delivery.retry']
            def 再试(之前=自身.失败.get('before')):
                '按失败时的游标再读'
                自身.加载(之前)
            if 有记录:
                盒=文档.createElement('div')
                盒.className='notice'
                标(盒)
                段=文档.createElement('p')
                段.setAttribute('role','alert')
                段.textContent=文
                盒.appendChild(段)
                盒.appendChild(处理按钮(窗口,{'variant':'outline','size':'sm','children':钮文,'onClick':再试,'window':窗口}))
                滚.appendChild(盒)
            else:
                空=文档.createElement('div')
                空.className='empty'
                标(空)
                图=图标警告16({'window':窗口,'size':24,'className':'emptyGlyph'})
                if 图 is not None:
                    空.appendChild(图)
                段=文档.createElement('p')
                段.className='emptyTitle'
                标(段)
                段.setAttribute('role','alert')
                段.textContent=文
                空.appendChild(段)
                钮=处理按钮(窗口,{'variant':'outline','className':'emptyAction','children':钮文,'onClick':再试,'window':窗口})
                标(钮)
                空.appendChild(钮)
                滚.appendChild(空)
        if (not 自身.加载中) and 自身.失败 is None and 自身.页 is not None and len(自身.页.get('records') or [])==0:
            空=文档.createElement('div')
            空.className='empty'
            标(空)
            空.setAttribute('role','status')
            空.appendChild(画时钟(文档,24))
            题=文档.createElement('h3')
            题.textContent=管理中文['delivery.empty']
            空.appendChild(题)
            滚.appendChild(空)
        if 自身.页 is not None:
            for 记录 in 自身.页.get('records') or []:
                节=文档.createElement('section')
                节.className='delivery'
                标(节)
                节.setAttribute('aria-label',管理中文['delivery.label'])
                节.appendChild(画时钟(文档,16))
                体=文档.createElement('div')
                体.className='deliveryBody'
                标(体)
                头=文档.createElement('div')
                头.className='deliveryHead'
                标(头)
                时=文档.createElement('time')
                时.className='deliveryTime'
                标(时)
                时.setAttribute('dateTime',记录.get('scheduledAt') or '')
                时.textContent=格式化下次运行(记录.get('scheduledAt') or '',管理中文['time.locale'],属性.get('timeZone'))
                头.appendChild(时)
                体.appendChild(头)
                if 记录.get('prompt') is not None:
                    段=文档.createElement('p')
                    段.className='savedPrompt'
                    标(段)
                    段.textContent=记录['prompt']
                    体.appendChild(段)
                节.appendChild(体)
                滚.appendChild(节)
            if 自身.页.get('nextBefore') is not None and 自身.失败 is None:
                def 更多(游标=自身.页.get('nextBefore')):
                    '再读更早的一页'
                    自身.加载(游标)
                滚.appendChild(处理按钮(窗口,{
                    'variant':'outline','disabled':自身.加载中,
                    'children':管理中文['delivery.loadMore'],'onClick':更多,'window':窗口,
                }))
        根.appendChild(滚)
        页=自身.页
        if 有记录 and 页.get('earlierRecordsPruned') and 页.get('nextBefore') is None and not 自身.加载中 and 自身.失败 is None:
            脚=文档.createElement('footer')
            脚.className='retentionEnd'
            标(脚)
            行=文档.createElement('div')
            行.className='retentionLine'
            标(行)
            字=文档.createElement('span')
            字.textContent=管理中文['delivery.pruned']
            行.appendChild(字)
            信息=文档.createElement('button')
            信息.type='button'
            信息.className='retentionInfo'
            标(信息)
            信息.setAttribute('aria-label',管理中文['delivery.retention'])
            信息.setAttribute('aria-expanded','true' if 自身.保留开 else 'false')
            图=图标信息描边常规({'window':窗口,'size':14})
            if 图 is not None:
                信息.appendChild(图)
            def 切换(事件):
                '展开或收起保留规则'
                自身.保留开=not 自身.保留开
                自身.画出()
            信息.addEventListener('click',切换)
            处理提示泡(窗口,{'label':管理中文['delivery.retention'],'side':'top','portal':True,'children':信息,'window':窗口})
            行.appendChild(信息)
            脚.appendChild(行)
            if 自身.保留开:
                规则=文档.createElement('div')
                规则.className='retentionRule'
                标(规则)
                保留=页.get('retention') or {}
                上=文档.createElement('p')
                上.textContent=套用(管理中文['delivery.retentionBounds'],{'days':保留.get('days'),'records':保留.get('records')})
                下=文档.createElement('p')
                下.textContent=管理中文['delivery.retentionExplanation']
                规则.appendChild(上)
                规则.appendChild(下)
                脚.appendChild(规则)
            根.appendChild(脚)
        return 根

    def 确保加载(自身):
        '任务、会话或最新投递变了就重新拉第一页'
        键=(自身.属性.get('id'),自身.属性.get('sessionId'),自身.属性.get('latestMessageId'))
        if 自身.已载==键:
            return
        自身.已载=键
        自身.纪元=自身.纪元+1
        自身.进行中=False
        自身.页=None
        自身.加载()

    def 拆除(自身):
        '卸下后忽略晚到的结果'
        自身.纪元=自身.纪元+1
        自身.进行中=False

    def __call__(自身,属性=None):
        '换绑定后重画'
        if 属性 is not None:
            自身.属性=属性
        自身.确保加载()
        return 自身.画出()
