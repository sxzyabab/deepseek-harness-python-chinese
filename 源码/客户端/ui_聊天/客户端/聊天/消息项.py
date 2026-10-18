import time as 时间模块
from ....ui_基础界面组件.markdown.json块 import json块
from ....ui_基础界面组件.状态点 import 状态点
from ....ui_基础界面组件.文字闪烁 import 文字闪烁
from ....ui_对话.异常 import 标样式模块
from .压缩项 import 压缩项
from .上下文注入行 import 上下文消息节点视图
from .消息图标动作 import 消息图标动作
from .用披露 import 注入聊天样式,真属性,挂节点

__all__=[
    '待插话泡','待提交泡','用户消息节点视图','用户消息行',
    '上下文消息节点视图','压缩节点视图','重试节点视图','回合错误节点视图',
    '回合满令牌节点视图','未知节点视图',
]

样式模块='message-item'


def 恒等(键,参数=None):
    '没有文案表时返回键'
    return 键


def 内容拆分(内容):
    '文本拼起来。图片和文件进附件。其余留下'
    文本=[]
    附件=[]
    其余=[]
    for 块 in 内容 if isinstance(内容,list) else []:
        if not isinstance(块,dict):
            其余.append(块)
            continue
        if 块.get('type')=='text' and isinstance(块.get('text'),str):
            文本.append(块['text'])
        elif 块.get('type')=='image' and 块.get('attachment') is not None:
            附件.append({'type':'image','image':{'attachment':块.get('attachment')}})
        elif 块.get('type')=='file' and 块.get('attachment') is not None:
            附件.append({'type':'file','file':块.get('attachment')})
        else:
            其余.append(块)
    return {'text':''.join(文本),'attachments':附件,'rest':其余}


def 重试秒(毫秒):
    '至少一秒'
    return max(1,-(-int(毫秒)//1000))


def 失败文案(消息,代码,翻译):
    '已知失败码换成界面文案，其余保留原消息'
    if 代码=='ACCOUNT_SIGNED_OUT':
        return 翻译('message.failure.accountSignedOut')
    if 代码=='INTERRUPTED':
        return 翻译('message.failure.interrupted')
    if 代码=='ACCOUNT_SIGN_IN_REQUIRED':
        return 翻译('message.failure.accountSignInRequired')
    if 代码 in ('QUOTA','ACCOUNT_QUOTA'):
        return 翻译('message.failure.quota')
    if 代码=='AUTH':
        return 翻译('message.failure.auth')
    return 消息


class 用户风格泡:
    '用户和插话共用的右对齐气泡'
    def __init__(自身,属性=None):
        '记下内容和工厂槽'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '正文交给用户内容工厂。动作行收到拼好的文本'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'消息项.module.css')
        部分=内容拆分(属性.get('content'))
        附件=属性.get('previewAttachments')
        if 附件 is None:
            附件=部分['attachments']
        准备={'text':部分['text'],'attachments':附件,'extraBlocks':部分['rest']}
        if 属性.get('referenceLabels') is not None:
            准备['referenceLabels']=属性['referenceLabels']
        事实=dict(属性.get('facts') or {})
        if 属性.get('referenceLabels') is not None:
            事实['sessionLabels']=属性['referenceLabels']
        if 属性.get('skillNames') is not None:
            事实['skillNames']=属性['skillNames']
        根=文档.createElement('div')
        根.className='userRow'
        标样式模块(根,样式模块)
        真属性(根,'data-pending-steering',属性.get('pending') is True)
        真属性(根,'data-submission-echo',属性.get('echo') is True)
        工厂=属性.get('renderFactorySlot')
        载荷={
            'content':准备,
            'loadImage':属性.get('loadImage'),
            'facts':事实,
            'interactive':属性.get('interactive') is True,
            'window':窗口,
        }
        if callable(工厂):
            挂节点(根,工厂('conversation.chat.user.content',载荷))
        动作=属性.get('actions')
        if callable(动作):
            挂节点(根,动作(准备['text']))
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根


class 待插话泡:
    '宿主已经承认、还没落进转录的插话'
    def __init__(自身,属性=None):
        '记下待定内容'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.泡=None
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 渲染(自身):
        '用用户气泡，并带上还没有时间的动作行'
        属性=自身.属性
        窗口=属性['window']
        翻译=属性.get('t') if callable(属性.get('t')) else 恒等

        def 动作(文本):
            '复制行'
            return 消息图标动作({
                'window':窗口,'text':文本,'clock':'start','className':'actions','t':翻译,
            })

        自身.泡=用户风格泡({
            'window':窗口,
            'content':属性.get('content'),
            'renderFactorySlot':属性.get('renderFactorySlot'),
            'loadImage':属性.get('loadImage'),
            'pending':True,
            'actions':动作,
            'parent':属性.get('parent'),
        })
        自身.根=自身.泡.根
        return 自身.根


class 待提交泡:
    '提交后、耐久消息出现前的本地回显'
    def __init__(自身,属性=None):
        '记下待定提交'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 渲染(自身):
        '草稿文本加对象地址预览'
        属性=自身.属性
        窗口=属性['window']
        翻译=属性.get('t') if callable(属性.get('t')) else 恒等
        提交=属性.get('submission') if isinstance(属性.get('submission'),dict) else {}
        文本=提交.get('text') if isinstance(提交.get('text'),str) else ''
        内容=[] if 文本=='' else [{'type':'text','text':文本}]
        预览=[]
        for 附件 in 提交.get('attachments') or []:
            if not isinstance(附件,dict):
                continue
            值=附件.get('value') if isinstance(附件.get('value'),dict) else {}
            if 附件.get('type')=='image':
                图={'url':值.get('previewUrl')}
                if 值.get('name') is not None:
                    图['name']=值['name']
                if 值.get('width') is not None:
                    图['width']=值['width']
                if 值.get('height') is not None:
                    图['height']=值['height']
                预览.append({'type':'image','image':{'preview':图}})
            else:
                预览.append({'type':'file','file':值})

        def 动作(文):
            '带回显时间的复制行'
            return 消息图标动作({
                'window':窗口,'text':文,'time':提交.get('time'),'clock':'start','className':'actions','t':翻译,
            })

        泡=用户风格泡({
            'window':窗口,
            'content':内容,
            'previewAttachments':预览,
            'renderFactorySlot':属性.get('renderFactorySlot'),
            'loadImage':属性.get('loadImage'),
            'pending':提交.get('placement')=='steering',
            'echo':True,
            'actions':动作,
            'parent':属性.get('parent'),
        })
        自身.根=泡.根
        return 自身.根


class 用户消息节点视图:
    '用户消息和已接纳插话'
    def __init__(自身,属性=None):
        '记下消息节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '可交互，并带上消息时间'
        属性=自身.属性
        窗口=属性['window']
        翻译=属性.get('t') if callable(属性.get('t')) else 恒等
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}

        def 动作(文本):
            '复制行'
            return 消息图标动作({
                'window':窗口,'text':文本,'time':数据.get('time'),'clock':'start','className':'actions','t':翻译,
            })

        泡属性={
            'window':窗口,
            'content':数据.get('content'),
            'interactive':True,
            'renderFactorySlot':属性.get('renderFactorySlot'),
            'loadImage':属性.get('loadImage'),
            'actions':动作,
            'parent':属性.get('parent'),
        }
        if 数据.get('referenceLabels') is not None:
            泡属性['referenceLabels']=数据['referenceLabels']
        if 数据.get('skillNames') is not None:
            泡属性['skillNames']=数据['skillNames']
        泡=用户风格泡(泡属性)
        自身.根=泡.根
        return 自身.根


用户消息行=用户消息节点视图


class 模型重试行:
    '把宿主安排的延迟锚到这次渲染的时钟上'
    def __init__(自身,属性=None):
        '记下重试节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.定时=None
        自身.截止=None
        自身.剩余=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '活动中的重试每 250 毫秒减一次秒数'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'消息项.module.css')
        翻译=属性.get('t') if callable(属性.get('t')) else 恒等
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        活动=属性.get('active') is True
        if 自身.截止 is None:
            自身.截止=int(时间模块.time()*1000)+int(节点.get('delayMs') or 0)
            自身.剩余=重试秒(自身.截止-int(时间模块.time()*1000))
        计划秒=重试秒(节点.get('delayMs') or 0)
        上限='∞' if 节点.get('mode')!='normal' else 节点.get('maxRetries')
        秒=自身.剩余 if 活动 else 计划秒
        if 节点.get('retryState')=='cancelled':
            标签=翻译('message.retry.cancelled')
        elif 活动:
            标签=翻译('message.retry.active')
        elif 节点.get('retryState')=='started':
            标签=翻译('message.retry.started')
        else:
            标签=翻译('message.retry.scheduled')
        if 自身.根 is None:
            自身.根=文档.createElement('details')
            自身.根.className='retryRow'
            标样式模块(自身.根,样式模块)
        else:
            while 自身.根.firstChild is not None:
                自身.根.removeChild(自身.根.firstChild)
        真属性(自身.根,'data-active',活动)
        要=文档.createElement('summary')
        要.className='retrySummary'
        标样式模块(要,样式模块)
        文=文档.createElement('span')
        文.className='retryText'
        标样式模块(文,样式模块)
        文.setAttribute('role','status')
        挂节点(文,文字闪烁({
            'window':窗口,
            'active':活动,
            'children':翻译('message.retry.status',{'label':标签,'retry':节点.get('retry'),'maximum':上限,'seconds':秒}),
        }))
        要.appendChild(文)
        自身.根.appendChild(要)
        细=文档.createElement('div')
        细.className='retryDetails'
        标样式模块(细,样式模块)
        延迟=文档.createElement('div')
        延迟标=文档.createElement('span')
        延迟标.className='retryDetailLabel'
        标样式模块(延迟标,样式模块)
        延迟标.textContent=翻译('message.retry.delay')
        延迟.appendChild(延迟标)
        延迟.appendChild(文档.createTextNode(翻译('duration.milliseconds',{'milliseconds':round(节点.get('delayMs') or 0)})))
        失败=文档.createElement('div')
        失败标=文档.createElement('span')
        失败标.className='retryDetailLabel'
        标样式模块(失败标,样式模块)
        失败标.textContent=翻译('message.retry.failure')
        失败体=节点.get('failure') if isinstance(节点.get('failure'),dict) else {}
        失败.appendChild(失败标)
        失败.appendChild(文档.createTextNode(失败文案(失败体.get('message') or '',失败体.get('code'),翻译)))
        细.appendChild(延迟)
        细.appendChild(失败)
        自身.根.appendChild(细)
        if 自身.定时 is not None and hasattr(窗口,'clearInterval'):
            窗口.clearInterval(自身.定时)
            自身.定时=None
        if 活动 and 自身.剩余!=1 and hasattr(窗口,'setInterval'):
            def 减():
                '减到一秒就停'
                自身.剩余=重试秒(自身.截止-int(时间模块.time()*1000))
                if 自身.剩余==1 and 自身.定时 is not None:
                    窗口.clearInterval(自身.定时)
                    自身.定时=None
                自身.渲染()
            自身.定时=窗口.setInterval(减,250)
        if 属性.get('parent') is not None and 自身.根.parentNode is None:
            属性['parent'].appendChild(自身.根)
        return 自身.根


class 重试节点视图:
    '重试链'
    def __init__(自身,属性=None):
        '记下重试节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.行=None
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '只有还排着的重试才倒计时'
        属性=自身.属性
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        当前=数据.get('current') if isinstance(数据.get('current'),dict) else {}
        行属性={
            'window':属性['window'],
            'node':当前,
            'active':当前.get('retryState')=='scheduled',
            't':属性.get('t'),
            'parent':属性.get('parent'),
        }
        if 自身.行 is None:
            自身.行=模型重试行(行属性)
        else:
            自身.行.更新(行属性)
            自身.行.渲染()
        自身.根=自身.行.根
        return 自身.根


class 回合错误节点视图:
    '回合终态失败'
    def __init__(自身,属性=None):
        '记下错误节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '登出和中断用任务已停止，其余用回合错误'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'消息项.module.css')
        翻译=属性.get('t') if callable(属性.get('t')) else 恒等
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else 节点
        根=文档.createElement('div')
        根.className='turnErrorRow'
        标样式模块(根,样式模块)
        根.setAttribute('role','status')
        点=状态点({'window':窗口,'state':'error','className':'turnErrorDot'})
        画出=点.渲染()
        if 画出 is not None:
            标样式模块(画出,样式模块)
            根.appendChild(画出)
        文=文档.createElement('div')
        文.className='turnErrorCopy'
        标样式模块(文,样式模块)
        题=文档.createElement('span')
        题.className='turnErrorTitle'
        标样式模块(题,样式模块)
        代码=数据.get('code')
        题.textContent=翻译('message.taskStopped') if 代码 in ('ACCOUNT_SIGNED_OUT','INTERRUPTED') else 翻译('message.turnError')
        息=文档.createElement('span')
        息.className='turnErrorMessage'
        标样式模块(息,样式模块)
        息.textContent=失败文案(数据.get('message') or '',代码,翻译)
        文.appendChild(题)
        文.appendChild(息)
        根.appendChild(文)
        if 代码 is not None and 代码!='INTERRUPTED':
            码=文档.createElement('code')
            码.className='turnErrorCode'
            标样式模块(码,样式模块)
            码.textContent=str(代码)
            根.appendChild(码)
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根


class 回合满令牌节点视图:
    '输出令牌到顶'
    def __init__(自身,属性=None):
        '记下节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '警告点加提示'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'消息项.module.css')
        翻译=属性.get('t') if callable(属性.get('t')) else 恒等
        根=文档.createElement('div')
        根.className='turnErrorRow'
        标样式模块(根,样式模块)
        根.setAttribute('role','status')
        点=状态点({'window':窗口,'state':'warning','className':'turnErrorDot'})
        画出=点.渲染()
        if 画出 is not None:
            标样式模块(画出,样式模块)
            根.appendChild(画出)
        文=文档.createElement('div')
        文.className='turnErrorCopy'
        标样式模块(文,样式模块)
        题=文档.createElement('span')
        题.className='maxTokensTitle'
        标样式模块(题,样式模块)
        题.textContent=翻译('message.maxTokens')
        息=文档.createElement('span')
        息.className='turnErrorMessage'
        标样式模块(息,样式模块)
        息.textContent=翻译('message.maxTokens.hint')
        文.appendChild(题)
        文.appendChild(息)
        根.appendChild(文)
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根


class 压缩节点视图:
    '自动压缩标记'
    def __init__(自身,属性=None):
        '记下压缩节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.项=None
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '交给压缩项'
        属性=自身.属性
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        项属性={'window':属性['window'],'node':节点.get('data'),'t':属性.get('t'),'parent':属性.get('parent')}
        if 自身.项 is None:
            自身.项=压缩项(项属性)
        else:
            自身.项.更新(项属性)
            自身.项.渲染()
        自身.根=自身.项.根
        return 自身.根


class 未知节点视图:
    '不认识的表面'
    def __init__(自身,属性=None):
        '记下未知节点'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新属性'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '用 JSON 块留下原始数据'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入聊天样式(文档,样式模块,'消息项.module.css')
        翻译=属性.get('t') if callable(属性.get('t')) else 恒等
        节点=属性.get('node') if isinstance(属性.get('node'),dict) else {}
        数据=节点.get('data') if isinstance(节点.get('data'),dict) else {}
        根=文档.createElement('div')
        根.className='contextRow'
        标样式模块(根,样式模块)

        def 截断(总):
            '截断脚'
            return 翻译('json.truncated',{'total':总})

        块=json块({
            'window':窗口,
            'label':翻译('message.unknownSurface',{'type':数据.get('type')}),
            'payload':数据.get('data'),
            'truncatedLabel':截断,
        })
        画出=块.渲染()
        if 画出 is not None:
            根.appendChild(画出)
        自身.根=根
        if 属性.get('parent') is not None:
            属性['parent'].appendChild(根)
        return 根
