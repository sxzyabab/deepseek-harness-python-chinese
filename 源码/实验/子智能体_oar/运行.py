'一次性 OAR 执行、根答复选择，以及本运行拥有的会话释放'
import threading,uuid
from ...基础设施.js特性 import PromiseEX as 期约
from ...内核.会话 import 会话标识
from ...子智能体.子智能体 import 断言可用工作目录,结算运行结果,子进程运行句柄
from ...工具.值 import 断言永不
from .环境 import 环境覆盖

__all__=['运行规格','文本任务','启动运行']

失败建议={
    'installation':'Install and authenticate the selected runtime before retrying.',
    'startup':'Check the runtime installation, authentication, and launch settings.',
    'turn':'Check the selected runtime and its account before retrying.',
    'abort':'The runtime did not accept interruption; session disposal was requested.',
    'dispose':'The runtime may still be active; check it before starting another task.',
}

def 要求默认运行时(标识):
    '从 OAR 默认注册表取出运行时。中文树没有 @botiverse/oar'
    raise ModuleNotFoundError('@botiverse/oar')

def 等待回合结束(会话,序号,输入标识):
    '等到这次输入对应的回合结束。实现在 @botiverse/oar/observe'
    raise ModuleNotFoundError('@botiverse/oar/observe')

class 运行失败(Exception):
    '带阶段和类别的 OAR 失败。消息会进入父侧诊断，保持英文'
    def __init__(自身,阶段,类别,原因=None):
        '拼出阶段、类别和建议'
        super().__init__('OAR subagent failure (stage: '+阶段+'; category: '+类别+'). '+失败建议[阶段])
        自身.阶段=阶段
        自身.类别=类别
        自身.name='OarFailure'
        if 原因 is not None:
            自身.cause=原因
            自身.__cause__=原因

class 运行规格:
    '一个提供方实例拥有的已解析部署设置和运行时'
    def __init__(自身,运行时,环境,启动参数,模型=None,力度=None,超时毫秒=None,出错=None):
        '记下运行时、显式环境和可选时限'
        自身.运行时=运行时
        自身.模型=模型
        自身.力度=力度
        自身.环境=环境
        自身.启动参数=启动参数
        自身.超时毫秒=超时毫秒
        自身.出错=出错

def 文本任务(提示):
    '打开原生会话前校验这一次文本任务。按原顺序拼接，不插入分隔'
    if len(提示)==0:
        raise ValueError('subagent-oar: the one-shot task must contain only text blocks')
    文本=[]
    for 块 in 提示:
        if 块['type']!='text':
            raise ValueError('subagent-oar: the one-shot task must contain only text blocks')
        文本.append(块['text'])
    if all(len(项.strip())==0 for 项 in 文本):
        raise ValueError('subagent-oar: the one-shot task must not be empty')
    return ''.join(文本)

def 信号已中止(信号):
    '取消在原生启动和清理等待期间仍然有效'
    if 信号 is None:
        return False
    if hasattr(信号,'aborted'):
        return bool(信号.aborted)
    if hasattr(信号,'is_set'):
        return 信号.is_set()
    return False

def 取消失败():
    '启动阶段被取消'
    return 运行失败('startup','cancelled')

def 然后(期,成功,失败=None):
    '期约扩展用中文方法，原文期约用 then'
    if hasattr(期,'然后'):
        return 期.然后(成功,失败)
    return 期.then(成功,失败)

def 空操作():
    '没有可摘的监听'
    return None

def 监听中止(信号,回调):
    '中文中止信号是 Event，浏览器信号才有 addEventListener'
    if 信号 is None:
        return 空操作
    if hasattr(信号,'addEventListener'):
        信号.addEventListener('abort',回调,{'once':True})
        def 摘掉():
            '摘掉一次性监听'
            if hasattr(信号,'removeEventListener'):
                信号.removeEventListener('abort',回调)
        return 摘掉
    if hasattr(信号,'is_set'):
        if 信号.is_set():
            回调()
            return 空操作
        def 等待():
            '置位后回调一次'
            信号.wait()
            回调()
        threading.Thread(target=等待,daemon=True).start()
    return 空操作

def 报告失败(规格,错误):
    '诊断观察者不能替换运行结果'
    try:
        if 规格.出错 is not None:
            规格.出错(错误,'error')
    except Exception:
        return

def 释放会话(会话,规格):
    '释放失败改写成 dispose 阶段的运行失败'
    盒=期约()
    def 失败(错误):
        '记下并拒绝'
        失败对象=运行失败('dispose','unknown',错误)
        报告失败(规格,失败对象)
        盒.拒绝(失败对象)
    try:
        结果=会话.dispose()
    except Exception as 错误:
        失败(错误)
        return 盒
    if hasattr(结果,'然后') or hasattr(结果,'then'):
        然后(结果,盒.解决,失败)
    else:
        盒.解决(结果)
    return 盒

def 完成回合(结局,输出):
    '把 OAR 回合结局收成子智能体结果'
    种类=结局['kind'] if isinstance(结局,dict) else 结局.kind
    if 种类=='completed':
        return {'output':输出,'stopReason':'completed'}
    if 种类=='aborted':
        return {'output':输出,'stopReason':'aborted'}
    if 种类=='failed':
        失败类=结局['failure'] if isinstance(结局,dict) else 结局.failure
        return {'output':输出,'stopReason':'error','diagnostic':str(运行失败('turn',失败类))}
    return 断言永不(结局)

def 发布运行(会话,提示,请求,规格):
    '会话已经打开之后，发布一次性运行句柄'
    已停=期约()
    消息表={}
    状态={'流文本':'','阶段':'running','释放':None}
    def 收集输出():
        '有消息标识时取最后一条非空消息，否则用拼接的根文本'
        答复=状态['流文本']
        for 文本 in 消息表.values():
            if len(文本)>0:
                答复=文本
        if len(答复)==0:
            return []
        return [{'type':'text','text':答复}]
    def 释放():
        '同一份释放期约'
        if 状态['释放'] is None:
            状态['释放']=释放会话(会话,规格)
        return 状态['释放']
    def 中止会话():
        '中止失败只报告，不替换结果'
        盒=期约()
        def 失败(错误):
            'abort 阶段未知类别'
            报告失败(规格,运行失败('abort','unknown',错误))
            盒.解决(None)
        try:
            结果=会话.abort()
        except Exception as 错误:
            失败(错误)
            return 盒
        if hasattr(结果,'然后') or hasattr(结果,'then'):
            然后(结果,盒.解决,失败)
        else:
            盒.解决(结果)
        return 盒
    def 打断(原因):
        '取消或超时只结算一次'
        if 状态['阶段']!='running':
            return
        状态['阶段']=原因
        载荷={'output':收集输出(),'stopReason':'aborted' if 原因=='cancelled' else 'error'}
        if 原因=='timeout':
            载荷['diagnostic']='OAR subagent exceeded its execution timeout. Increase timeoutMs or use a smaller task.'
        已停.解决(载荷)
        中止会话()
        def 忽略释放失败(_错误):
            '取消结算期间观察释放拒绝'
            return None
        然后(释放(),lambda _值: None,忽略释放失败)
    def 当中止():
        '信号中止'
        打断('cancelled')
    def 收到事件(事件):
        '只累计根智能体的文本增量'
        会话标识值=事件['sessionId'] if isinstance(事件,dict) else 事件.sessionId
        路径=事件['agentPath'] if isinstance(事件,dict) else 事件.agentPath
        种类=事件['kind'] if isinstance(事件,dict) else 事件.kind
        if 会话标识值!=会话.id or len(路径)!=0 or 种类!='text_delta':
            return
        文本=事件['text'] if isinstance(事件,dict) else 事件.text
        状态['流文本']=状态['流文本']+文本
        消息标识=事件['messageId'] if isinstance(事件,dict) else getattr(事件,'messageId',None)
        if 消息标识 is not None:
            消息表[消息标识]=消息表.get(消息标识,'')+文本
    退订=会话.events(收到事件,{'cursor':{'sessionId':会话.id,'afterSeq':-1}})
    摘监听=监听中止(请求['signal'],当中止)
    if 信号已中止(请求['signal']):
        当中止()
    定时器=None
    if 规格.超时毫秒 is not None:
        def 到时():
            '时限到了就按超时打断'
            打断('timeout')
        定时器=threading.Timer(规格.超时毫秒/1000,到时)
        定时器.daemon=True
        定时器.start()
    def 跑回合():
        '提交提示并等到回合结束'
        盒=期约()
        输入标识=str(uuid.uuid4())
        def 已提交(接纳):
            '被拒绝则直接成为错误结果'
            种类=接纳['kind'] if isinstance(接纳,dict) else 接纳.kind
            if 种类=='rejected':
                码=接纳['code'] if isinstance(接纳,dict) else 接纳.code
                盒.解决({'output':收集输出(),'stopReason':'error','diagnostic':str(运行失败('turn',码))})
                return
            序号=接纳['seq'] if isinstance(接纳,dict) else 接纳.seq
            def 失败(错误):
                '观察失败'
                盒.拒绝(错误)
            try:
                然后(等待回合结束(会话,序号,输入标识),lambda 结局: 盒.解决(完成回合(结局,收集输出())),失败)
            except Exception as 错误:
                盒.拒绝(错误)
        def 提交失败(错误):
            '提交失败'
            盒.拒绝(错误)
        try:
            然后(会话.prompt(提示,{'inputId':输入标识}),已提交,提交失败)
        except Exception as 错误:
            盒.拒绝(错误)
        return 盒
    def 收集诊断():
        '失败且没有原生原因时的安全摘要'
        return str(运行失败('turn','unknown'))
    def 尝试():
        '已打断则跟随已停，否则与回合竞速'
        if 状态['阶段']!='running':
            return 已停
        盒=期约()
        def 成功(值):
            '竞速胜出'
            盒.解决(值)
        def 失败(错误):
            '收成回合阶段的未知失败'
            盒.拒绝(运行失败('turn','unknown',错误))
        try:
            然后(期约.竞速([跑回合(),已停]),成功,失败)
        except Exception as 错误:
            盒.拒绝(运行失败('turn','unknown',错误))
        return 盒
    def 收尾(_值=None):
        '摘掉定时器和事件订阅'
        if 定时器 is not None:
            定时器.cancel()
        if callable(退订):
            退订()
        if 状态['阶段']=='running':
            状态['阶段']='settled'
    结果=结算运行结果({
        'attempt':尝试,
        'collectOutput':收集输出,
        'collectDiagnostic':收集诊断,
        'cancelled':lambda: 状态['阶段']=='cancelled',
        'onError':规格.出错,
        'signal':请求['signal'],
        'onAbort':当中止,
    })
    然后(结果,收尾,收尾)
    def 拆除():
        '先释放会话，再等到结果期约'
        盒=期约()
        def 已释放(_值=None):
            '结果期约只兑现'
            然后(结果,盒.解决,盒.解决)
        然后(释放(),已释放,盒.拒绝)
        return 盒
    return 子进程运行句柄({
        'id':会话标识(str(uuid.uuid4())),
        'result':结果,
        'signal':请求['signal'],
        'onAbort':当中止,
        'requestCancel':当中止,
        'teardown':拆除,
    })

def 会话选项(规格,工作目录):
    '把部署设置收成 OAR 会话选项。线上键保持英文'
    选项={'cwd':工作目录,'env':环境覆盖(规格.环境),'launchArgs':list(规格.启动参数)}
    if 规格.模型 is not None:
        选项['model']=规格.模型
    if 规格.力度 is not None:
        选项['effort']=规格.力度
    return 选项

def 启动运行(请求,规格):
    '打开一个 OAR 会话并返回一次性运行。启动期间不能打断，取消会先释放再拒绝'
    盒=期约()
    try:
        提示=文本任务(请求['prompt'])
        if 信号已中止(请求['signal']):
            raise 取消失败()
        工作目录=断言可用工作目录('subagent-oar','child cwd',请求['cwd'])
    except Exception as 错误:
        盒.拒绝(错误)
        return 盒
    def 安装失败(错误):
        '安装探测失败'
        失败对象=运行失败('installation','unknown',错误)
        报告失败(规格,失败对象)
        盒.拒绝(失败对象)
    def 安装好了(安装):
        '不支持或找不到就按安装阶段拒绝'
        try:
            if 信号已中止(请求['signal']):
                raise 取消失败()
            if 安装 is None:
                raise 运行失败('installation','unsupported')
            种类=安装['kind'] if isinstance(安装,dict) else 安装.kind
            if 种类=='unsupported':
                raise 运行失败('installation','unsupported')
            if 种类=='not_found':
                raise 运行失败('installation','not-found')
        except Exception as 错误:
            盒.拒绝(错误)
            return
        def 会话好了(会话):
            '打开成功后再看取消'
            def 启动失败(错误):
                '发布失败时释放已打开的会话'
                失败对象=运行失败('startup','unknown',错误)
                报告失败(规格,失败对象)
                def 再抛(_值=None):
                    '释放结束后抛出启动失败'
                    盒.拒绝(失败对象)
                然后(释放会话(会话,规格),再抛,再抛)
            try:
                if 信号已中止(请求['signal']):
                    def 已释放(_值=None):
                        '迟到的会话先释放'
                        盒.拒绝(取消失败())
                    然后(释放会话(会话,规格),已释放,已释放)
                    return
                运行=发布运行(会话,提示,请求,规格)
            except Exception as 错误:
                启动失败(错误)
                return
            if 信号已中止(请求['signal']):
                def 已拆除(_值=None):
                    '发布后取消'
                    盒.拒绝(取消失败())
                拆=运行.销毁() if hasattr(运行,'销毁') else 运行.dispose()
                然后(拆,已拆除,已拆除)
                return
            盒.解决(运行)
        def 打开失败(错误):
            '打开失败。已经取消则改成取消'
            if 信号已中止(请求['signal']):
                盒.拒绝(取消失败())
                return
            失败对象=运行失败('startup','unknown',错误)
            报告失败(规格,失败对象)
            盒.拒绝(失败对象)
        try:
            然后(规格.运行时.session(安装,会话选项(规格,工作目录)),会话好了,打开失败)
        except Exception as 错误:
            打开失败(错误)
    探测=getattr(规格.运行时,'installation',None)
    if 探测 is None:
        安装好了(None)
        return 盒
    try:
        然后(探测({'env':环境覆盖(规格.环境)}),安装好了,安装失败)
    except Exception as 错误:
        安装失败(错误)
    return 盒
