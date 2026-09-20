"""校验持久重试事件与失败事实（dict）。"""
import json,math
from ...工具.超时 import 定时器延迟上限毫秒
from .历史 import 打开步提供方

__all__=('包名','名称','依赖','安装','应用')

外来JSON上限=9007199254740991#持久事件整数字段校验点
包名='@deepseek-ai/dsh-llm-retry'
名称='llm-retry-invariant'
依赖=['invariants']

def 转JS字符串(值):
    """None 写成字面量 undefined，其余用 str()；供持久事件诊断串。"""
    if 值 is None:
        return 'undefined'
    return str(值)

def 校验失败载荷(值,失败):
    """在持久边界校验完整的提供方中立失败载荷。值为 dict。"""
    if 值 is None or not isinstance(值,dict):
        失败('llm/retry failure must be an object')
    if 'message' not in 值 or not isinstance(值['message'],str) or len(值['message'])==0:
        失败('llm/retry failure.message must be a non-empty string')
    if 'code' not in 值 or not isinstance(值['code'],str) or len(值['code'])==0:
        失败('llm/retry failure.code must be a non-empty string')
    if 'status' in 值:
        状态=值['status']
        if isinstance(状态,bool) or not isinstance(状态,int) or 状态<100 or 状态>599:
            失败('llm/retry failure.status must be an integer from 100 through 599 when present')
    if 'providerRetryAfterMs' in 值:
        建议等待=值['providerRetryAfterMs']
        if isinstance(建议等待,bool) or not isinstance(建议等待,(int,float)) or not math.isfinite(建议等待) or 建议等待<=0:
            失败('llm/retry failure.providerRetryAfterMs must be a positive finite number when present')
    if 'requestId' in 值:
        请求号=值['requestId']
        if not isinstance(请求号,str) or len(请求号)==0:
            失败('llm/retry failure.requestId must be a non-empty string when present')

def 从后找(事件列表,判断):
    """从后往前找出第一条命中的事件。"""
    下标=len(事件列表)-1
    while 下标>=0:
        事件=事件列表[下标]
        if 判断(事件):
            return 事件
        下标-=1
    return None

def 校验重试(历史,事件,失败):
    """对照当前打开的请求步校验一条重试记录。事件为 dict。"""
    载荷=事件['data']
    链身份=载荷['retryId'] if 'retryId' in 载荷 else None
    回合=载荷['turn'] if 'turn' in 载荷 else None
    步=载荷['step'] if 'step' in 载荷 else None
    提供方=载荷['provider'] if 'provider' in 载荷 else None
    模式=载荷['mode'] if 'mode' in 载荷 else None
    政策键=载荷['policyKey'] if 'policyKey' in 载荷 else None
    序号=载荷['retry'] if 'retry' in 载荷 else None
    延迟毫秒=载荷['delayMs'] if 'delayMs' in 载荷 else None
    if not isinstance(链身份,str) or len(链身份)==0:
        失败('llm/retry retryId must be a non-empty string')
    失败事实=载荷['failure'] if 'failure' in 载荷 else None
    校验失败载荷(失败事实,失败)
    if isinstance(序号,bool) or not isinstance(序号,int) or 序号<1 or 序号>外来JSON上限:
        失败('llm/retry retry must be a positive safe integer')
    if not isinstance(提供方,str) or len(提供方)==0:
        失败('llm/retry provider must be a non-empty string')
    if not isinstance(政策键,str) or len(政策键)==0:
        失败('llm/retry policyKey must be a non-empty string')
    if 模式=='normal':
        上限=载荷['maxRetries'] if 'maxRetries' in 载荷 else None
        if isinstance(上限,bool) or not isinstance(上限,int) or 上限<1 or 上限>外来JSON上限 or 序号>上限:
            失败('llm/retry retry '+转JS字符串(序号)+' must not exceed a positive safe maxRetries '+转JS字符串(上限))
    elif 模式=='always':
        if 'maxRetries' in 载荷:
            失败('llm/retry always mode must omit maxRetries')
    else:
        失败('llm/retry mode must be normal or always, got '+转JS字符串(模式))
    if isinstance(延迟毫秒,bool) or not isinstance(延迟毫秒,(int,float)) or not math.isfinite(延迟毫秒) or 延迟毫秒<0 or 延迟毫秒>定时器延迟上限毫秒:
        失败('llm/retry delayMs must be a finite number within 0..'+str(定时器延迟上限毫秒))
    def 是回合边界(先前):
        """回合开始或结束。"""
        类型=先前['type']
        return 类型=='turn/start' or 类型=='turn/end'
    回合边界=从后找(历史,是回合边界)
    if 回合边界 is None or 回合边界['type']!='turn/start':
        失败('llm/retry must be appended inside an open turn')
    打开回合=回合边界['data']['turn']
    if 回合!=打开回合:
        失败('llm/retry names turn '+转JS字符串(回合)+', but the open turn is '+转JS字符串(打开回合))
    def 是步边界(先前):
        """步开始或结束。"""
        类型=先前['type']
        return 类型=='step/start' or 类型=='step/end'
    步边界=从后找(历史,是步边界)
    if 步边界 is None or 步边界['type']!='step/start':
        失败('llm/retry must be appended inside an open step')
    步载荷=步边界['data']
    打开步=步载荷['step']
    打开步回合=步载荷['turn']
    if 步!=打开步 or 回合!=打开步回合:
        失败('llm/retry names turn '+转JS字符串(回合)+'/step '+转JS字符串(步)+', but the open step is '+转JS字符串(打开步回合)+'/'+转JS字符串(打开步))
    路由提供方=打开步提供方(历史,回合,步)
    if 路由提供方!=提供方:
        失败('llm/retry provider '+转JS字符串(提供方)+' does not match the failed request provider '+转JS字符串(路由提供方))
    def 是同政策重试(先前):
        """同回合同一步同一提供方同一政策的重试。"""
        if 先前['type']!='llm/retry':
            return False
        先前载荷=先前['data']
        return 先前载荷['turn']==回合 and 先前载荷['step']==步 and 先前载荷['provider']==提供方 and 先前载荷['policyKey']==政策键
    先前政策重试=从后找(历史,是同政策重试)
    上次序号=0 if 先前政策重试 is None else 先前政策重试['data']['retry']
    期望序号=上次序号+1
    if 序号!=期望序号:
        失败('llm/retry retry '+转JS字符串(序号)+' must equal provider policy retry '+转JS字符串(期望序号))
    if 先前政策重试 is not None and 先前政策重试['data']['retryId']!=链身份:
        失败('llm/retry must preserve retryId across one provider-policy chain')
    if 先前政策重试 is None:
        def 占用链身份(先前):
            """已被别的链占用的 retryId。"""
            类型=先前['type']
            if 类型!='llm/retry' and 类型!='llm/retry-started':
                return False
            return 先前['data']['retryId']==链身份
        if 从后找(历史,占用链身份) is not None:
            失败('llm/retry retryId '+json.dumps(链身份,ensure_ascii=False,separators=(',',':'),allow_nan=False)+' is already owned by another chain')

def 校验已开始(历史,事件,失败):
    """对照其已调度尝试校验一次等待完成过渡。事件为 dict。"""
    载荷=事件['data']
    链身份=载荷['retryId'] if 'retryId' in 载荷 else None
    回合=载荷['turn'] if 'turn' in 载荷 else None
    步=载荷['step'] if 'step' in 载荷 else None
    序号=载荷['retry'] if 'retry' in 载荷 else None
    if not isinstance(链身份,str) or len(链身份)==0:
        失败('llm/retry-started retryId must be a non-empty string')
    def 是配对调度(先前):
        """同链同序号的 llm/retry。"""
        if 先前['type']!='llm/retry':
            return False
        先前载荷=先前['data']
        return 先前载荷['retryId']==链身份 and 先前载荷['retry']==序号
    已调度=从后找(历史,是配对调度)
    if 已调度 is None:
        失败('llm/retry-started pairs no prior scheduled attempt')
    调度载荷=已调度['data']
    if 调度载荷['turn']!=回合 or 调度载荷['step']!=步:
        失败('llm/retry-started turn/step must match its scheduled attempt')
    def 是重复过渡(先前):
        """已经有同一次的过渡。"""
        if 先前['type']!='llm/retry-started':
            return False
        先前载荷=先前['data']
        return 先前载荷['retryId']==链身份 and 先前载荷['retry']==序号
    if 从后找(历史,是重复过渡) is not None:
        失败('llm/retry-started repeats one scheduled attempt')

def 校验会话(会话,失败):
    """校验一份已加载会话里已有的每条重试记录。会话为对象，事件为 dict。"""
    事件列表=会话.events
    下标=0
    for 事件 in 事件列表:
        类型=事件['type']
        if 类型=='llm/retry':
            校验重试(事件列表[:下标],事件,失败)
        elif 类型=='llm/retry-started':
            校验已开始(事件列表[:下标],事件,失败)
        下标+=1

def 安装(上下文,失败):
    """给已加载与新追加的重试记录安装校验。"""
    for 会话 in 上下文.sessions.列出():
        校验会话(会话,失败)
    def 新会话(会话):
        """新会话也回放。"""
        校验会话(会话,失败)
    上下文.监听('session/created',新会话,{'全局':True})
    def 分派钩子(模式,事件名,参数列表,*其余):
        """新追加的会话事件。"""
        if 事件名!='session/event':
            return
        会话=参数列表[0]
        事件=参数列表[1]
        类型=事件['type']
        if 类型=='llm/retry':
            校验重试(会话.events,事件,失败)
        elif 类型=='llm/retry-started':
            校验已开始(会话.events,事件,失败)
    上下文.监听('internal/dispatch',分派钩子,{'全局':True})

安装.inject=['sessions']

def 应用(上下文):
    """注册 LLM 重试不变量配套。"""
    return 上下文.invariants.register(包名,安装)

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
