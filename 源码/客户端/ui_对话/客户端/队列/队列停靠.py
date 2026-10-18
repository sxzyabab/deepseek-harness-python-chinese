import os
from ....ui_基础界面组件.icons import 图标上chevron14,图标下chevron14,图标勾14,图标关闭填14,图标编辑16,图标垃圾桶16,图标发送16,图标队列14
from ....ui_基础界面组件.文件大小 import 文件大小文本
from ....ui_基础界面组件.文件类型图标 import 处理文件类型图标
from ....ui_基础界面组件.提示泡 import 处理提示泡
from ....ui_基础界面组件.内联编辑器 import 内联编辑器
from ...异常 import 注入模块样式文件,标样式模块,挂上,对话错误
from ..文案 import 中文,填入,命名空间

__all__=['队列停靠','队列停靠条目']

样式模块='queue-dock'

def 纯文本(内容):
    '全是文本块才可编辑'
    if not isinstance(内容,list):
        return None
    for 块 in 内容:
        if not isinstance(块,dict) or 块.get('type')!='text':
            return None
    return ''.join(块.get('text') or '' for 块 in 内容)

def 队列附件(内容):
    '带引用的图片和文件。没有引用的图片块跳过'
    出=[]
    if not isinstance(内容,list):
        return 出
    for 块 in 内容:
        if not isinstance(块,dict):
            continue
        if 块.get('type')=='image' and isinstance(块.get('attachment'),dict):
            出.append({'type':'image','attachment':块['attachment']})
        if 块.get('type')=='file' and isinstance(块.get('attachment'),dict):
            出.append({'type':'file','attachment':块['attachment']})
    return 出

class 队列停靠:
    '一条直接展开。多条默认收成计数。空队列不画'
    def __init__(自身,属性):
        '默认收起，没有正在编辑的行'
        自身.属性=属性
        自身.根=None
        自身.收起=True
        自身.编辑=None
        自身.忙=None
        自身.已订=False
        自身.渲染()

    def 渲染(自身):
        '收件箱 next-turn 去掉已经进转录的提交'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        收件=属性['useProjection']('inbox')
        待定提交=属性['useSession'](lambda 快照:快照.get('pendingSubmissions') or [])
        行表=[]
        if isinstance(收件,dict):
            行表=list(收件.get('next-turn') or [])
        已进=set()
        for 项 in 待定提交:
            if 项.get('placement')=='transcript':
                已进.add(项.get('requestId'))
        if len(已进)>0:
            留下=[]
            for 行 in 行表:
                源=行.get('source') or {}
                if 源.get('kind')=='user' and 源.get('rpcId') in 已进:
                    continue
                留下.append(行)
            行表=留下
        已收=set()
        for 行 in 行表:
            源=行.get('source') or {}
            if 源.get('kind')=='user' and 源.get('rpcId') is not None:
                已收.add(源['rpcId'])
        待发=[项 for 项 in 待定提交 if 项.get('placement')=='queued' and 项.get('requestId') not in 已收]
        行数=len(行表)+len(待发)
        if 行数==0:
            if 自身.根 is not None:
                自身.根.remove()
                自身.根=None
            return None
        if 自身.编辑 is not None and not any(行.get('id')==自身.编辑['id'] for 行 in 行表):
            自身.编辑=None
        运行=属性['useSession'](lambda 快照:快照.get('running'))
        可改=属性['useSession'](lambda 快照:快照.get('subagent') is None or (isinstance(快照.get('subagent'),dict) and 快照['subagent'].get('address',{}).get('mode')=='continuable'))
        展开=(not 自身.收起) or 自身.编辑 is not None or 自身.忙 is not None
        列表可见=行数==1 or 展开
        注入模块样式文件(文档,'队列停靠样式',os.path.join(os.path.dirname(__file__),'队列停靠.module.css'),样式模块)
        父=None
        if 自身.根 is not None:
            父=自身.根.parentNode
            自身.根.remove()
        elif 'parent' in 属性:
            父=属性['parent']
        停靠=文档.createElement('div')
        停靠.className='dock'
        标样式模块(停靠,样式模块)
        停靠.setAttribute('data-queue-dock','')
        面板=文档.createElement('div')
        面板.className='panel'
        标样式模块(面板,样式模块)
        if 行数>1:
            头=文档.createElement('button')
            头.type='button'
            头.className='header'
            标样式模块(头,样式模块)
            头.setAttribute('aria-expanded','true' if 展开 else 'false')
            if 自身.编辑 is not None or 自身.忙 is not None:
                头.disabled=True
            def 切换(事件):
                '展开或收起多条队列'
                自身.收起=not 自身.收起
                自身.渲染()
            头.addEventListener('click',切换)
            前=文档.createElement('span')
            前.className='lead'
            标样式模块(前,样式模块)
            前.setAttribute('aria-hidden','true')
            前.appendChild(图标队列14({'window':窗口}))
            头.appendChild(前)
            计数=文档.createElement('span')
            计数.className='count'
            标样式模块(计数,样式模块)
            计数.textContent=填入(中文['queue.count'],{'n':行数})
            头.appendChild(计数)
            if (not 列表可见) and len(待发)>0:
                状态=文档.createElement('span')
                状态.className='status'
                标样式模块(状态,样式模块)
                状态.setAttribute('role','status')
                状态.textContent='发送中…'
                头.appendChild(状态)
            箭=文档.createElement('span')
            箭.className='chevron'
            标样式模块(箭,样式模块)
            箭.setAttribute('aria-hidden','true')
            箭.appendChild(图标下chevron14({'window':窗口}) if 展开 else 图标上chevron14({'window':窗口}))
            头.appendChild(箭)
            面板.appendChild(头)
        列=文档.createElement('ul')
        列.className='list'
        标样式模块(列,样式模块)
        if not 列表可见:
            列.hidden=True
        if 列表可见:
            for 行 in 行表:
                列.appendChild(自身.画行(文档,窗口,行,行数,可改,运行))
            for 提交 in 待发:
                列.appendChild(自身.画待发(文档,窗口,提交,行数,可改))
        面板.appendChild(列)
        停靠.appendChild(面板)
        自身.根=停靠
        if 父 is not None:
            父.appendChild(自身.根)
        if not 自身.已订:
            def 变更():
                '收件箱或会话变了就重画'
                if 自身.根 is not None and 自身.根.parentNode is not None:
                    自身.渲染()
            for 名 in ('useProjection','useSession'):
                钩=属性.get(名)
                if 钩 is not None and hasattr(钩,'_subscribe'):
                    钩._subscribe(变更)
            自身.已订=True
        return 自身.根

    def 画行(自身,文档,窗口,行,行数,可改,运行):
        '一条已入队的消息'
        项=文档.createElement('li')
        项.className='row'
        标样式模块(项,样式模块)
        if 行数==1:
            前=文档.createElement('span')
            前.className='lead'
            标样式模块(前,样式模块)
            前.setAttribute('aria-hidden','true')
            前.appendChild(图标队列14({'window':窗口}))
            项.appendChild(前)
        文本=纯文本(行.get('content'))
        if 自身.编辑 is not None and 自身.编辑['id']==行.get('id'):
            编辑=内联编辑器({
                'window':窗口,
                'value':自身.编辑['text'],
                'label':'编辑排队消息',
                'onChange':lambda 文,标识=行.get('id'): 自身.改文(标识,文),
                'onSave':自身.保存,
                'onCancel':自身.取消编辑,
            })
            项.appendChild(编辑.渲染())
        else:
            附件=队列附件(行.get('content'))
            if len(附件)>0:
                盒=文档.createElement('span')
                盒.className='attachments'
                标样式模块(盒,样式模块)
                for 片 in 附件:
                    if 片['type']=='image':
                        图=文档.createElement('span')
                        图.className='thumb'
                        标样式模块(图,样式模块)
                        图.setAttribute('aria-hidden','true')
                        盒.appendChild(图)
                    else:
                        盒.appendChild(自身.文件片(文档,窗口,片['attachment'],填入(中文['queue.file'],{'name':片['attachment'].get('name')})))
                项.appendChild(盒)
            预览=文档.createElement('span')
            预览.className='preview'
            标样式模块(预览,样式模块)
            原文=''.join(块.get('text') or '' for 块 in (行.get('content') or []) if isinstance(块,dict) and 块.get('type')=='text')
            挂上(预览,自身.属性['renderFactorySlot']('conversation.user.text',{
                'text':原文,
                'facts':{'collapseWhitespace':True,'trimWhitespace':True},
                'interactive':False,
                'ellipsis':True,
                'window':窗口,
            }))
            项.appendChild(预览)
        if 可改:
            项.appendChild(自身.动作(文档,窗口,行,文本,运行))
        return 项

    def 文件片(自身,文档,窗口,附件,标签):
        '文件名和大小'
        片=文档.createElement('span')
        片.className='file'
        标样式模块(片,样式模块)
        片.setAttribute('aria-label',标签)
        片.setAttribute('title',附件.get('name') or '')
        标=文档.createElement('span')
        标.className='fileIcon'
        标样式模块(标,样式模块)
        标.setAttribute('aria-hidden','true')
        标.appendChild(处理文件类型图标(窗口,{'path':附件.get('name') or '','size':16}))
        片.appendChild(标)
        名=文档.createElement('span')
        名.className='fileName'
        标样式模块(名,样式模块)
        名.textContent=附件.get('name') or ''
        片.appendChild(名)
        大小=文档.createElement('span')
        大小.className='fileSize'
        标样式模块(大小,样式模块)
        大小.textContent=文件大小文本(附件.get('bytes') or 0)
        片.appendChild(大小)
        return 片

    def 动作(自身,文档,窗口,行,文本,运行):
        '编辑、删除、插话'
        盒=文档.createElement('div')
        盒.className='actions'
        标样式模块(盒,样式模块)
        if 自身.编辑 is not None and 自身.编辑['id']==行.get('id'):
            盒.appendChild(自身.图标钮(文档,窗口,'保存排队消息',图标勾14,自身.保存,自身.忙 is not None or 自身.编辑['text'].strip()==''))
            盒.appendChild(自身.图标钮(文档,窗口,'取消编辑',图标关闭填14,自身.取消编辑,自身.忙 is not None))
        else:
            def 开始编辑(事件,行=行,文本=文本):
                '纯文本才进入编辑'
                if 文本 is not None:
                    自身.编辑={'id':行.get('id'),'text':文本}
                    自身.渲染()
            编辑钮=自身.图标钮(文档,窗口,'编辑排队消息',图标编辑16,开始编辑,自身.忙 is not None or 文本 is None)
            if 文本 is None:
                编辑钮.setAttribute('title','包含非文本内容，暂不支持编辑')
            盒.appendChild(编辑钮)
            def 删除(事件,行=行):
                '删掉这条排队消息'
                自身.执行(行.get('id'),{'kind':'remove'},'删除失败：这条消息可能已经开始发送。')
            盒.appendChild(自身.图标钮(文档,窗口,'删除排队消息',图标垃圾桶16,删除,自身.忙 is not None))
            def 插话(事件,行=行):
                '运行中才插话发送'
                自身.执行(行.get('id'),{'kind':'steer'},'插话发送失败，请重试。')
            插话钮=自身.图标钮(文档,窗口,'插话发送',图标发送16,插话,自身.忙 is not None or not 运行)
            if not 运行:
                插话钮.setAttribute('title','仅运行中可插话发送')
            盒.appendChild(插话钮)
        return 盒

    def 图标钮(自身,文档,窗口,标签,图标,点击,禁用):
        '带提示的圆形动作'
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='action'
        标样式模块(钮,样式模块)
        钮.setAttribute('aria-label',标签)
        钮.disabled=禁用
        钮.appendChild(图标({'window':窗口,'size':14}))
        钮.addEventListener('click',点击)
        return 处理提示泡(窗口,{'label':标签,'side':'bottom','delayMs':500,'portal':True,'disabled':禁用,'children':钮,'window':窗口})

    def 画待发(自身,文档,窗口,提交,行数,可改):
        '本地回声，动作先禁用'
        项=文档.createElement('li')
        项.className='row pendingRow'
        标样式模块(项,样式模块)
        项.setAttribute('data-submission-echo','')
        if 行数==1:
            前=文档.createElement('span')
            前.className='lead'
            标样式模块(前,样式模块)
            前.appendChild(图标队列14({'window':窗口}))
            项.appendChild(前)
        预览=文档.createElement('span')
        预览.className='preview'
        标样式模块(预览,样式模块)
        挂上(预览,自身.属性['renderFactorySlot']('conversation.user.text',{
            'text':提交.get('text') or '',
            'facts':{'collapseWhitespace':True,'trimWhitespace':True},
            'interactive':False,
            'ellipsis':True,
            'window':窗口,
        }))
        项.appendChild(预览)
        状态=文档.createElement('span')
        状态.className='status'
        标样式模块(状态,样式模块)
        状态.setAttribute('role','status')
        状态.textContent='发送中…'
        项.appendChild(状态)
        if 可改:
            盒=文档.createElement('div')
            盒.className='actions'
            标样式模块(盒,样式模块)
            for 标签,图标 in (('编辑排队消息',图标编辑16),('删除排队消息',图标垃圾桶16),('插话发送',图标发送16)):
                钮=文档.createElement('button')
                钮.type='button'
                钮.className='action'
                标样式模块(钮,样式模块)
                钮.setAttribute('aria-label',标签)
                钮.setAttribute('title','发送中…')
                钮.disabled=True
                钮.appendChild(图标({'window':窗口,'size':14}))
                盒.appendChild(钮)
            项.appendChild(盒)
        return 项

    def 改文(自身,标识,文):
        '编辑框里的草稿'
        自身.编辑={'id':标识,'text':文}

    def 取消编辑(自身,事件=None):
        '丢掉这次编辑'
        自身.编辑=None
        自身.渲染()

    def 保存(自身,事件=None):
        '把纯文本写回队列'
        if 自身.编辑 is None or 自身.编辑['text'].strip()=='':
            return
        if 自身.执行(自身.编辑['id'],{'kind':'edit','content':[{'type':'text','text':自身.编辑['text']}]},'编辑失败：这条消息可能已经开始发送。'):
            自身.编辑=None
            自身.渲染()

    def 执行(自身,项标识,动作,失败文):
        '更新队列。失败用中文通知'
        自身.忙=项标识
        try:
            结果=自身.属性['updateQueue'](项标识,动作)
            if hasattr(结果,'等待'):
                结果.等待()
            自身.忙=None
            return True
        except Exception:
            自身.属性['notify']('error',失败文)
            自身.忙=None
            自身.渲染()
            return False

def 应用队列(上下文):
    '登记队列停靠。动作走会话作用域里的 conversation'
    def 登记():
        '等输入停靠洞'
        def 注入(会话标识):
            '更新队列、通知和读图'
            作用域=上下文.sessions.scope(会话标识)
            if 作用域 is None:
                raise 对话错误('queue dock: session "'+str(会话标识)+'" resolved no scope')
            会话=作用域.get('conversation')
            if 会话 is None:
                raise 对话错误('queue dock: conversation service unavailable')
            def 通知(级别,文本):
                '写到这份输入壳'
                面=会话.input
                if hasattr(面,'供'):
                    面.供(作用域).notify(级别,文本)
                elif hasattr(面,'for_'):
                    面.for_(作用域).notify(级别,文本)
            return {
                'updateQueue':lambda 项标识,动作:会话.updateQueue(项标识,动作),
                'notify':通知,
                'loadImage':lambda 附件:上下文.uiConversation.imageUrl(会话标识,附件),
            }
        return 上下文.slots.inject('conversation.input.dock',lambda: 上下文.slots.register({
            'name':'conversation.input.dock',
            'id':'queue',
            'order':20,
            'locale':命名空间,
            'inject':注入,
        },队列停靠))
    return 登记()

队列停靠条目={
    'name':'conversation-queue-dock',
    'inject':['slots','conversation','sessions','uiConversation'],
    'apply':应用队列,
}
