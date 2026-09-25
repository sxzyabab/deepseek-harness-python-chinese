import threading
from ....工具.超时 import 中止控制器
from .音频 import 录制错误,音频base64
from .波形图 import 波形图
from .语音输入安装对话框 import 语音输入安装对话框

__all__=['语音输入']

可用阶段=('ready','standby','waking')

def 读就绪(属性):
    """注入面 hooks.speechReadiness。"""
    钩=属性.get('hooks') or {}
    存储=钩.get('speechReadiness')
    if 存储 is not None:
        return 存储.getSnapshot()
    取=属性.get('useSpeechReadiness')
    if 取 is not None:
        def 全量(快照):
            """整份就绪快照。"""
            return 快照
        return 取(全量)
    return {'catalog':None,'connected':False,'error':None}

def 填(翻译,键,表=None):
    """词典插值。"""
    文=翻译(键)
    if 表 is None:
        return 文
    return 文.format(**表)

class 语音输入:
    """点按录音的输入栏活动；转写文字仍落在原会话草稿。"""
    def __init__(自身,属性):
        """记下 props。"""
        自身.属性=属性
        自身.阶段='idle'
        自身.消息=''
        自身.待插入=''
        自身.当前=None
        自身.代=0
        自身.波形=波形图()
        自身.上次会话=属性.get('sessionId')
        自身.引导开=False
        自身.对话框=语音输入安装对话框({
            'open':False,
            'needsInstallation':False,
            'onDismiss':自身.关引导,
            'onOpenDetails':自身.开详情,
            't':属性['t'],
        })

    def 关引导(自身):
        """关掉安装/不可用模态。"""
        自身.引导开=False

    def 开详情(自身):
        """关模态并打开语音 Bundle 详情。"""
        自身.引导开=False
        自身.属性['openSettings']()

    def 更新(自身,属性):
        """会话变了则作废在途采集。"""
        自身.属性=属性
        会话=属性.get('sessionId')
        if 会话!=自身.上次会话:
            自身.上次会话=会话
            自身.取消()

    def 可用(自身,就绪):
        """已连接且所选提供方处于可录阶段。"""
        目录=就绪.get('catalog')
        if not 就绪.get('connected') or 目录 is None:
            return False
        选=目录.get('selection') or {}
        提供方=None
        for 项 in 目录.get('providers') or []:
            if 项.get('id')==选.get('providerId'):
                提供方=项
                break
        if 提供方 is None:
            return False
        return (提供方.get('preparation') or {}).get('phase') in 可用阶段

    def 失败文(自身,失败):
        """录制错误走 kind 键，其余走 failed。"""
        翻译=自身.属性['t']
        if isinstance(失败,录制错误):
            return 翻译(失败.kind)
        消息=str(失败)
        if isinstance(失败,Exception):
            消息=str(失败)
        return 填(翻译,'failed',{'message':消息})

    def 反馈(自身,文本):
        """工具栏内提示。"""
        自身.消息=文本
        自身.阶段='feedback'

    def 拆录音(自身,采集):
        """关闭失败不得盖住结果。"""
        try:
            采集.拆除()
        except Exception:
            return

    def 取消(自身):
        """作废在途采集。"""
        自身.代+=1
        活动=自身.当前
        自身.当前=None
        if 活动 is not None:
            计时=活动.get('timer')
            if 计时 is not None:
                计时.cancel()
            活动['abort'].中止()
            自身.拆录音(活动['capture'])
        自身.待插入=''
        自身.消息=''
        自身.阶段='idle'
        自身.引导开=False

    def 点触发(自身):
        """可用则开录，否则开引导模态。"""
        就绪=读就绪(自身.属性)
        if 自身.可用(就绪):
            自身.开始()
        else:
            自身.引导开=True

    def 结束(自身):
        """停录并转写。"""
        活动=自身.当前
        if 活动 is None or 活动['phase']!='recording':
            return
        活动['phase']='transcribing'
        代=自身.代
        计时=活动.get('timer')
        if 计时 is not None:
            计时.cancel()
        自身.阶段='transcribing'
        try:
            音频=活动['capture'].stop(活动['maxDurationSeconds'])
            if 代!=自身.代:
                return
            if len(音频)>活动['maxAudioBytes']:
                自身.反馈(自身.属性['t']('tooLarge'))
                return
            请求={'audioBase64':音频base64(音频),**活动['selection']}
            结果=自身.属性['transcribe'](请求,活动['abort'].信号)
            if 代!=自身.代:
                return
            if not 结果['ok']:
                自身.反馈(填(自身.属性['t'],'failed',{'message':结果['error'].message}))
                return
            文本=结果['value']['text']
            if 文本=='':
                自身.反馈(自身.属性['t']('empty'))
                return
            if not 自身.属性['inputActions'].insertText(文本,活动['span']):
                自身.待插入=文本
                自身.反馈(自身.属性['t']('conflict'))
                return
            自身.阶段='idle'
        except Exception as 失败:
            自身.拆录音(活动['capture'])
            if 代==自身.代:
                自身.反馈(自身.失败文(失败))
        if 代==自身.代:
            自身.当前=None

    def 开始(自身):
        """取得麦克风并开始采集。"""
        就绪=读就绪(自身.属性)
        目录=就绪.get('catalog')
        if 目录 is None or not 自身.可用(就绪) or 自身.属性.get('locked') or 自身.当前 is not None:
            return
        自身.代+=1
        代=自身.代
        寿命=中止控制器()
        活动={
            'capture':自身.属性['createRecording'](),
            'abort':寿命,
            'span':自身.属性['inputActions'].captureInsertion(),
            'selection':目录['selection'],
            'maxDurationSeconds':目录['maxDurationSeconds'],
            'maxAudioBytes':目录['maxAudioBytes'],
            'phase':'requesting',
            'timer':None,
        }
        自身.当前=活动
        自身.消息=''
        自身.待插入=''
        自身.阶段='requesting'
        def 采集出错(失败):
            """采集中断立刻进反馈。"""
            if 代!=自身.代 or 自身.当前 is not 活动 or 活动['phase']=='transcribing':
                return
            自身.当前=None
            计时=活动.get('timer')
            if 计时 is not None:
                计时.cancel()
            寿命.中止()
            自身.反馈(自身.失败文(失败))
        try:
            活动['capture'].start(采集出错)
            if 代!=自身.代 or 自身.当前 is not 活动:
                return
            活动['phase']='recording'
            自身.阶段='recording'
            秒=活动['maxDurationSeconds']
            计时=threading.Timer(秒,自身.结束)
            计时.daemon=True
            活动['timer']=计时
            计时.start()
        except Exception as 失败:
            自身.拆录音(活动['capture'])
            if 代==自身.代:
                自身.当前=None
                自身.反馈(自身.失败文(失败))

    def 插入待定(自身):
        """草稿冲突后显式插入。"""
        动作=自身.属性['inputActions']
        if 动作.insertText(自身.待插入,动作.captureInsertion()):
            自身.待插入=''
            自身.阶段='idle'

    def 渲染(自身):
        """折叠麦克风或展开的采集行。"""
        翻译=自身.属性['t']
        就绪=读就绪(自身.属性)
        目录=就绪.get('catalog')
        提供方=None
        if 目录 is not None:
            选=目录.get('selection') or {}
            for 项 in 目录.get('providers') or []:
                if 项.get('id')==选.get('providerId'):
                    提供方=项
                    break
        可用=自身.可用(就绪)
        if 可用:
            自身.引导开=False
        锁定=bool(自身.属性.get('locked'))
        展开=自身.阶段!='idle'
        切活动=自身.属性.get('onActiveChange')
        if 切活动 is not None:
            切活动(展开)
        需安装=(就绪.get('connected') and 提供方 is not None
            and 提供方.get('location')=='host-local'
            and (提供方.get('preparation') or {}).get('phase')=='unprepared')
        if not 展开:
            return {
                'type':'voice-input',
                'mode':'trigger',
                'cssModule':'语音输入.module.css',
                'tooltip':翻译('dictate' if 可用 else 'prepareRequired'),
                'startLabel':翻译('start' if 可用 else 'setupPrompt.trigger'),
                'disabled':锁定,
                'hasPopup':None if 可用 else 'dialog',
                'onStart':自身.点触发,
                'setup':自身.对话框({
                    'open':自身.引导开 and not 可用,
                    'needsInstallation':需安装,
                    'onDismiss':自身.关引导,
                    'onOpenDetails':自身.开详情,
                    't':翻译,
                }),
            }
        准备=None if 提供方 is None else (提供方.get('preparation') or {}).get('phase')
        if 自身.阶段=='feedback':
            状态文=自身.消息
        elif 自身.阶段=='requesting':
            状态文=翻译('requesting')
        elif 准备=='waking':
            状态文=翻译('wakingShort')
        else:
            状态文=翻译('transcribingShort')
        波形=None
        if 自身.阶段=='recording':
            采集=None if 自身.当前 is None else 自身.当前.get('capture')
            波形=自身.波形({'recording':采集,'label':翻译('recording')})
        return {
            'type':'voice-input',
            'mode':'capture',
            'cssModule':'语音输入.module.css',
            'phase':自身.阶段,
            'cancelLabel':翻译('discard' if 自身.待插入 else 'cancel'),
            'onCancel':自身.取消,
            'waveform':波形,
            'status':None if 自身.阶段=='recording' else 状态文,
            'pending':自身.待插入,
            'stopLabel':翻译('stop'),
            'onStop':自身.结束 if 自身.阶段=='recording' else None,
            'insertLabel':翻译('insert'),
            'onInsert':自身.插入待定 if 自身.待插入 else None,
            'retryLabel':翻译('retryRecording'),
            'onRetry':自身.开始 if 自身.阶段=='feedback' and not 自身.待插入 else None,
            'retryDisabled':not 可用 or 锁定,
        }

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
