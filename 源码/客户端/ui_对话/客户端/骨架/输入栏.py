import os
from ....ui_基础界面组件.icons import 图标加号16,图标警告16
from ....ui_基础界面组件.提示泡 import 处理提示泡
from ....ui_基础界面组件.吐司 import 处理吐司
from ...异常 import 注入模块样式文件,标样式模块,挂上,接上
from ..文案 import 中文,填入
from ..图像标签 import 图像大小文本,附件错误文本
from ..服务 import 是图片媒体类型
from ..输入.提交策略 import 解析提交方式
from .上下文仪表 import 上下文仪表
from .控件行布局 import 观察控件行

__all__=['输入栏']

样式模块='input-bar'
发送箭头='M8.3125 0.980183C8.66767 1.0531 8.97902 1.20418 9.2627 1.43233C9.48724 1.61297 9.73029 1.85793 9.97949 2.10714L14.707 6.83468L13.293 8.24874L9 3.95577V15.0417H7V3.95577L2.70703 8.24874L1.29297 6.83468L6.02051 2.10714C6.26971 1.85793 6.51277 1.61297 6.7373 1.43233C6.97662 1.23986 7.28445 1.04402 7.6875 0.980183C7.8973 0.947006 8.1031 0.95516 8.3125 0.980183Z'

def 发送标记(文档,停止):
    '圆钮里是箭头或方块，文字只放在无障碍名称上'
    图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
    图.setAttribute('viewBox','0 0 16 16')
    图.setAttribute('width','16')
    图.setAttribute('height','16')
    图.setAttribute('aria-hidden','true')
    if 停止:
        形=文档.createElementNS('http://www.w3.org/2000/svg','rect')
        形.setAttribute('x','3')
        形.setAttribute('y','3')
        形.setAttribute('width','10')
        形.setAttribute('height','10')
        形.setAttribute('rx','3')
    else:
        形=文档.createElementNS('http://www.w3.org/2000/svg','path')
        形.setAttribute('d',发送箭头)
    形.setAttribute('fill','currentColor')
    图.appendChild(形)
    return 图

class 输入栏:
    '撰写器栏。没有会话时同一棵树变成工作区触发器'
    def __init__(自身,属性):
        '吐司序号和活动席'
        自身.属性=属性
        自身.根=None
        自身.活动=False
        自身.吐司序号=0
        自身.吐司=None
        自身.已订=False
        自身.拆行=None
        自身.上次会话=None
        自身.本地稿=''
        自身.渲染()

    def 渲染(自身):
        '占位、发送、停止和子槽都按当前快照重画'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(文档,'输入栏样式',os.path.join(os.path.dirname(__file__),'输入栏.module.css'),样式模块)
        会话标识=属性.get('sessionId')
        if 自身.上次会话!=会话标识:
            自身.活动=False
            自身.上次会话=会话标识
        输入=属性['useInput'](lambda 快照:快照) if 属性.get('useInput') is not None else None
        通知=属性['useNotices'](lambda 快照:快照) if 属性.get('useNotices') is not None else None
        忙碌=属性['useBusyEnter'](lambda 值:值) if 属性.get('useBusyEnter') is not None else 'queue'
        停止键=属性['useStopShortcut'](lambda 键:键) if 属性.get('useStopShortcut') is not None else []
        if 属性.get('useLexicon') is not None:
            属性['useLexicon'](lambda 值:值)
        命令开=False
        if 属性.get('useMenuLauncher') is not None:
            命令开=属性['useMenuLauncher'](lambda 源:源=='command') is True
        会话=属性['useSession'](lambda 快照:快照) if 属性.get('useSession') is not None else None
        提示错=None if 会话 is None else 会话.get('promptError')
        运行中=False if 会话 is None else 会话.get('running') is True
        子=None if 会话 is None else 会话.get('subagent')
        已移除=False if 会话 is None else 会话.get('removed') is True
        计划=False
        if 属性.get('useProjection') is not None:
            计划值=属性['useProjection']('plan')
            if isinstance(计划值,dict):
                if 计划值.get('pending'):
                    计划=not 计划值.get('active')
                else:
                    计划=计划值.get('active') is True
        键盘=属性.get('keyboard')
        动作=属性.get('inputActions')
        活=输入 is not None and 键盘 is not None and 动作 is not None
        草稿=自身.本地稿 if 输入 is None else 输入.get('draft') or ''
        附件=[]
        if 输入 is not None and 属性.get('resolveDraftAttachments') is not None:
            附件=属性['resolveDraftAttachments'](输入.get('attachmentIds') or []) or []
        空=草稿.strip()=='' and len(附件)==0
        上传=属性['useFileUploads'](lambda 快照:快照) if 属性.get('useFileUploads') is not None else {}
        上传中=False
        for 项 in 附件:
            if 项.get('kind')=='file' and (not isinstance(上传,dict) or 上传.get(项.get('id'),{}).get('status')!='ready'):
                上传中=True
        if isinstance(提示错,dict):
            错误=提示错.get('error') or {}
            if 错误.get('code')=='session/writer-held':
                自身.显示吐司('当前会话已被占用，可能是其他正在运行的 DSH 导致的（如其他 dsh web、桌面端），请退出其他正在运行的 DSH 后重试。')
            elif 错误.get('code') in ('session/attachment-invalid','subagent/attachment-invalid'):
                限额=属性['useProjection']('imageLimits') if 属性.get('useProjection') is not None else None
                原因=''
                if isinstance(错误.get('details'),dict):
                    原因=错误['details'].get('reason') or ''
                自身.显示吐司(附件错误文本(原因,限额))
            else:
                自身.显示吐司(str(错误.get('message') or '')+' ('+str(错误.get('code') or '')+')')
        if isinstance(通知,dict) and 通知.get('level')=='error':
            自身.显示吐司(通知.get('text') or '')
        可继续=isinstance(子,dict) and 子.get('address',{}).get('mode')=='continuable'
        父离线=可继续 and 子.get('parentAvailable') is not True
        惰性=属性.get('disabled') is True
        被挡=属性.get('blocked')
        禁用=已移除 or 惰性 or (not 活) or 被挡 is not None or 父离线
        机器忙=输入 is not None and 输入.get('phase') in ('adjudicating','submitting')
        工作区触发=惰性 and (not 已移除) and 属性.get('onRequestWorkspace') is not None
        可编辑=(活 and (not 禁用) and (not 机器忙)) or (输入 is None and (not 已移除) and 被挡 is None and 属性.get('disabled') is not True)
        可插话=子 is None or 可继续
        可插话队列=(not 禁用) and (not 机器忙) and (not 命令开) and 空 and 运行中 and 可插话 and 输入 is not None and len(输入.get('queue') or [])>0
        主停止=运行中 and 子 is None and (空 or 被挡 is not None)
        主方式=解析提交方式(忙碌,运行中,'enter',可插话)
        普通稿=(not 空) and 输入 is not None and 输入.get('phase')=='plain' and not 草稿.lstrip().startswith('/')
        if 主停止:
            主标签='停止生成'
        elif 运行中 and 可插话 and (not 禁用) and (not 上传中) and 普通稿:
            主标签='插话发送' if 主方式=='steer' else '排队发送'
        else:
            主标签='发送消息'
        主禁用=属性.get('stop') is None if 主停止 else (空 or 禁用 or 机器忙 or 上传中)
        if 属性.get('placeholder') is not None:
            占位=属性['placeholder']
        elif 父离线:
            占位='父会话已离线，无法继续发送；仍可停止当前运行'
        elif 禁用:
            占位='会话不可用'
        elif 可插话队列:
            占位='Cmd/Ctrl+Enter 插话发送全部排队消息'
        elif 计划:
            占位='描述你的任务以生成计划'
        else:
            占位='发消息或创建任务, / 调用指令, @ 文件或对话'
        旧=自身.根
        父=旧.parentNode if 旧 is not None else (属性['parent'] if 'parent' in 属性 else None)
        if 自身.拆行 is not None:
            自身.拆行()
            自身.拆行=None
        根=文档.createElement('div')
        根.className='root hero' if 属性.get('variant')=='hero' else 'root'
        标样式模块(根,样式模块)
        if 自身.吐司 is not None:
            根.appendChild(处理吐司(窗口,{'text':自身.吐司['text'],'icon':图标警告16({'window':窗口}),'onDone':自身.关掉吐司,'window':窗口}))
        if isinstance(通知,dict) and 通知.get('level')=='info':
            条=文档.createElement('div')
            条.className='notice'
            标样式模块(条,样式模块)
            条.setAttribute('role','status')
            条.textContent=通知.get('text') or ''
            根.appendChild(条)
        卡=文档.createElement('div')
        卡.className='card cardWorkspaceTrigger' if 工作区触发 else 'card'
        标样式模块(卡,样式模块)
        卡.setAttribute('data-composer-card','')
        if 工作区触发:
            def 点卡(事件):
                '整张卡打开工作区选择'
                属性['onRequestWorkspace']()
            卡.addEventListener('click',点卡)
        if 会话标识 is not None:
            叠=文档.createElement('div')
            叠.className='overlayAnchor'
            标样式模块(叠,样式模块)
            叠.setAttribute('data-composer-overlay','')
            挂上(叠,属性['renderSlot']('conversation.input.overlay',{'window':窗口}))
            卡.appendChild(叠)
        if 属性.get('accessory') is not None:
            配=文档.createElement('div')
            配.className='accessory'
            标样式模块(配,样式模块)
            挂上(配,属性['accessory'])
            卡.appendChild(配)
        限额=属性['useProjection']('imageLimits') if 属性.get('useProjection') is not None else None
        放下=None
        if 限额 is not None:
            放下={'count':限额.get('maxImagesPerMessage'),'size':图像大小文本(限额.get('maxImageBytes') or 0)}
        可丢=(子 is None or 可继续) and (not 禁用) and (not 机器忙) and 属性.get('addFiles') is not None
        挂上(卡,属性['renderSlot']('conversation.input.attachments',{
            'attachments':附件,
            'canAcceptDrop':可丢,
            'onAddFiles':lambda 文件列,目录=None: 自身.纳入(文件列,目录),
            'onRemoveAttachment':lambda 标识: 属性['removeAttachment'](标识) if 属性.get('removeAttachment') is not None else None,
            'uploads':上传,
            'onRetryFile':lambda 标识: 属性['retryFileUpload'](标识) if 属性.get('retryFileUpload') is not None else None,
            'dropLimits':放下,
            'window':窗口,
        }))
        滚动=文档.createElement('div')
        滚动.className='scroll'
        标样式模块(滚动,样式模块)
        滚动.setAttribute('data-input-scroll','')
        长=文档.createElement('div')
        长.className='grow'
        标样式模块(长,样式模块)
        框=文档.createElement('div')
        框.className='input'
        标样式模块(框,样式模块)
        框.setAttribute('contenteditable','true' if 可编辑 else 'false')
        框.setAttribute('role','textbox')
        框.setAttribute('aria-label','选择工作区' if 工作区触发 else 占位)
        if 键盘 is not None and hasattr(键盘,'绑定编辑器'):
            键盘.绑定编辑器(框)
        if 草稿!='':
            框.textContent=草稿
        elif not (输入 is not None and 输入.get('phase') in ('claimed','submitting') and isinstance(输入.get('claim'),dict) and 草稿.startswith(输入['claim'].get('token') or '')):
            位=文档.createElement('div')
            位.className='placeholder'
            标样式模块(位,样式模块)
            位.textContent=占位
            长.appendChild(位)
        def 输入了(事件):
            '把可编辑区的文字写回壳。还没有会话时先留在这一栏'
            文=框.textContent or ''
            if 键盘 is not None and hasattr(键盘,'setDraft'):
                键盘.setDraft(文)
                return
            自身.本地稿=文
            主.disabled=文.strip()==''
        框.addEventListener('input',输入了)
        长.appendChild(框)
        滚动.appendChild(长)
        卡.appendChild(滚动)
        行=文档.createElement('div')
        行.className='row'
        标样式模块(行,样式模块)
        工具=文档.createElement('div')
        工具.className='tools'
        标样式模块(工具,样式模块)
        if 自身.活动:
            工具.hidden=True
        加=文档.createElement('button')
        加.type='button'
        加.className='add'
        标样式模块(加,样式模块)
        加.setAttribute('aria-label','添加文件或调用指令')
        加.setAttribute('aria-haspopup','listbox')
        加.setAttribute('aria-expanded','true' if 命令开 else 'false')
        加.disabled=禁用 or 属性.get('toggleCommandMenu') is None
        加.appendChild(图标加号16({'window':窗口,'size':14}))
        def 切菜单(事件):
            '先把焦点交回编辑器再打开命令菜单'
            if 属性.get('toggleCommandMenu') is not None and 键盘 is not None:
                属性['toggleCommandMenu'](键盘.caretSpan() if hasattr(键盘,'caretSpan') else {'start':0,'end':0})
        加.addEventListener('click',切菜单)
        工具.appendChild(处理提示泡(窗口,{'label':'添加文件或调用指令','side':'top','delayMs':500,'children':加,'window':窗口}))
        文件=文档.createElement('input')
        文件.type='file'
        文件.multiple=True
        文件.hidden=True
        文件.disabled=子 is not None
        def 选了(事件):
            '选完就清空，同一文件可以再选'
            列表=list(事件.target.files or [])
            事件.target.value=''
            if len(列表)>0:
                自身.纳入(列表,None)
        文件.addEventListener('change',选了)
        工具.appendChild(文件)
        模式=文档.createElement('div')
        模式.className='modes'
        标样式模块(模式,样式模块)
        if 会话标识 is not None:
            挂上(模式,属性['renderSlot']('conversation.input.permission',{'locked':禁用,'window':窗口}))
            挂上(模式,属性['renderSlot']('conversation.input.plan',{'locked':禁用,'window':窗口}))
        工具.appendChild(模式)
        if 输入 is not None and 会话标识 is not None:
            挂上(工具,属性['renderSlot']('conversation.input.left',{'window':窗口}))
        行.appendChild(工具)
        尾=文档.createElement('div')
        尾.className='trailing trailingActive' if 自身.活动 else 'trailing'
        标样式模块(尾,样式模块)
        标准=文档.createElement('div')
        标准.className='standardControls'
        标样式模块(标准,样式模块)
        if 自身.活动:
            标准.hidden=True
        if 输入 is not None and 会话标识 is not None:
            挂上(标准,属性['renderSlot']('conversation.input.right',{'window':窗口}))
        if 会话标识 is not None:
            挂上(标准,属性['renderSlot']('conversation.input.model',{'locked':已移除 or 惰性 or (not 活),'window':窗口}))
        尾.appendChild(标准)
        if 输入 is not None and 会话标识 is not None:
            def 活动变了(开):
                '活动席展开时收起标准控件'
                自身.活动=开 is True
                自身.渲染()
            挂上(尾,属性['renderSlot']('conversation.input.activity',{'locked':禁用,'onActiveChange':活动变了,'window':窗口}))
        def 主点(事件):
            '停止或按忙碌回车的方式发送。还没有会话时把这句话留在对话区'
            if 主停止:
                if 属性.get('stop') is not None:
                    属性['stop']()
                return
            if 键盘 is not None and hasattr(键盘,'submit') and (not 空) and (not 禁用) and (not 机器忙) and (not 上传中):
                键盘.submit(主方式,'click')
                return
            文=(自身.本地稿 or '').strip()
            if 文=='':
                return
            节点=框
            滚动区=None
            while 节点 is not None:
                if 节点.hasAttribute('data-conversation-scroll'):
                    滚动区=节点
                    break
                节点=节点.parentElement
            if 滚动区 is not None:
                条=文档.createElement('div')
                条.textContent=文
                座位=滚动区.querySelector('[data-composer-seat]')
                if 座位 is not None:
                    滚动区.insertBefore(条,座位)
                else:
                    滚动区.appendChild(条)
            自身.本地稿=''
            框.textContent=''
            主.disabled=True
        主=文档.createElement('button')
        主.type='button'
        主.className='primary'
        标样式模块(主,样式模块)
        主.setAttribute('aria-label',主标签)
        主.disabled=主禁用
        主.appendChild(发送标记(文档,主停止))
        主.addEventListener('click',主点)
        尾.appendChild(处理提示泡(窗口,{
            'label':'停止生成' if 主停止 else 主标签,
            'shortcutKeys':停止键 if 主停止 else None,
            'side':'top',
            'delayMs':500,
            'disabled':主禁用,
            'children':主,
            'window':窗口,
        }))
        行.appendChild(尾)
        卡.appendChild(行)
        根.appendChild(卡)
        坞=文档.createElement('div')
        坞.className='dock'
        标样式模块(坞,样式模块)
        坞.setAttribute('data-composer-dock','')
        if 属性.get('variant')=='composer' and 输入 is not None and 会话标识 is not None:
            挂上(坞,属性['renderSlot']('conversation.composer.dock',{'window':窗口}))
        if not 自身.活动 and 属性.get('useProjection') is not None:
            表=上下文仪表({'useProjection':属性['useProjection'],'window':窗口})
            if 表.根 is not None:
                坞.appendChild(表.根)
        根.appendChild(坞)
        自身.根=接上(旧,根,父)
        自身.拆行=观察控件行(行)
        if not 自身.已订:
            def 变更():
                '输入或会话变了就重画'
                if 自身.根 is not None and 自身.根.parentNode is not None:
                    自身.渲染()
            for 名 in ('useInput','useSession','useNotices','useBusyEnter','useFileUploads','useMenuLauncher','useStopShortcut','useProjection'):
                钩=属性.get(名)
                if 钩 is not None and hasattr(钩,'_subscribe'):
                    钩._subscribe(变更)
            自身.已订=True
        return 自身.根

    def 纳入(自身,文件列,目录):
        '整批检查图片限额。拒绝就吐司，不进轨'
        属性=自身.属性
        if 属性.get('addFiles') is None or len(文件列)==0:
            return
        if 目录 is None:
            目录=set()
        限额=属性['useProjection']('imageLimits') if 属性.get('useProjection') is not None else None
        子=None
        会话=属性['useSession'](lambda 快照:快照) if 属性.get('useSession') is not None else None
        if isinstance(会话,dict):
            子=会话.get('subagent')
        可继续=isinstance(子,dict) and 子.get('address',{}).get('mode')=='continuable'
        if 可继续 and any((文件 in 目录) or (not 是图片媒体类型(getattr(文件,'type',''))) for 文件 in 文件列):
            自身.显示吐司('仅支持 PNG、JPG、WebP、GIF 格式的图片')
            自身.渲染()
            return
        if 限额 is not None:
            类型=限额.get('mediaTypes') or []
            图片=[文件 for 文件 in 文件列 if getattr(文件,'type','') in 类型]
            if len(图片)>限额.get('maxImagesPerMessage',0):
                自身.显示吐司(填入(中文['image.tooMany'],{'count':限额.get('maxImagesPerMessage')}))
                自身.渲染()
                return
        拒绝=属性['addFiles'](文件列,目录)
        if 拒绝 is not None:
            自身.显示吐司(拒绝)
            自身.渲染()

    def 显示吐司(自身,文):
        '相同句子再来也换序号，重新计时'
        自身.吐司序号+=1
        自身.吐司={'seq':自身.吐司序号,'text':文}

    def 关掉吐司(自身):
        '时间到了拿掉'
        自身.吐司=None
        自身.渲染()
