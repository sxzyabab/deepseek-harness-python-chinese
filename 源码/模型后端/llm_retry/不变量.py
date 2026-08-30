"""本包拥有的持久重试事件不变量。

对齐上游 `llm-retry/src/invariant.ts`。公开面仅中文名。
"""
import json#JSON序列化
from .. import llm#失败事实词表
from ...工具.超时 import 定时器延迟上限毫秒#导入定时器延迟上限
from ...依赖 import cordis#外部依赖胶水
from .历史 import 打开步提供方#导入打开步提供方
from .类型 import 取,试取,有键#读取字段

__all__=('包名','名称','注入','安装','应用')#仅中文公开名

编码=json.dumps#JSON序列化
是否整数=llm.类型.是否整数#对齐 Number.isInteger
是否安全整数=llm.类型.是否安全整数#对齐 Number.isSafeInteger
是否有限数=llm.类型.是否有限#对齐 Number.isFinite
包名='@deepseek-ai/dsh-llm-retry'#本包的不变量所有权名
名称='llm-retry-invariant'#配套不变量插件名
注入=['invariants']#依赖 invariants 服务

def 转JS字符串(值):#对齐 JS String()
    """对齐 JS String()，None 写成 undefined。"""
    if 值 is None:#缺席对齐undefined
        return 'undefined'#JS String(undefined)
    return str(值)#其余转字符串

def 校验失败载荷(值,失败):#校验提供方中立失败载荷
    """在持久边界校验完整的提供方中立失败载荷。"""
    if 值 is None or isinstance(值,(str,bytes,int,float,bool)) or callable(值):#不是对象
        失败('llm/retry failure must be an object')#必须是对象
    消息=试取(值,'message')#失败摘要
    if not isinstance(消息,str) or len(消息)==0:#消息非法
        失败('llm/retry failure.message must be a non-empty string')#消息必须非空
    失败码=试取(值,'code')#失败码
    if not isinstance(失败码,str) or len(失败码)==0:#code非法
        失败('llm/retry failure.code must be a non-empty string')#code必须非空
    if 有键(值,'status'):#有状态
        状态=取(值,'status')#可选HTTP状态
        if not 是否整数(状态) or 状态<100 or 状态>599:#不是合法HTTP码
            失败('llm/retry failure.status must be an integer from 100 through 599 when present')#状态越界
    if 有键(值,'providerRetryAfterMs'):#有提供方等待
        建议等待=取(值,'providerRetryAfterMs')#可选提供方等待
        if not 是否有限数(建议等待) or 建议等待<=0:#不是正有限数
            失败('llm/retry failure.providerRetryAfterMs must be a positive finite number when present')#等待非法
    if 有键(值,'requestId'):#有请求id
        请求号=取(值,'requestId')#可选请求id
        if not isinstance(请求号,str) or len(请求号)==0:#不是非空字符串
            失败('llm/retry failure.requestId must be a non-empty string when present')#请求id非法

def 从后找(事件们,判断):#对齐 Array.prototype.findLast
    """从后往前找出第一条命中的事件。"""
    下标=len(事件们)-1#最后一个下标
    while 下标>=0:#尚未到头
        事件=事件们[下标]#当前事件
        if 判断(事件):#命中
            return 事件#命中
        下标-=1#继续往前
    return None#没有命中

def 校验重试(历史,事件,失败):#校验 llm/retry
    """对照当前打开的请求步校验一条重试记录。"""
    载荷=试取(事件,'data')#本条重试载荷
    链身份=试取(载荷,'retryId')#重试链身份
    回合=试取(载荷,'turn')#回合
    步=试取(载荷,'step')#步
    提供方=试取(载荷,'provider')#提供方
    模式=试取(载荷,'mode')#普通或始终
    政策键=试取(载荷,'policyKey')#政策指纹
    序号=试取(载荷,'retry')#本次重试序号
    延迟毫秒=试取(载荷,'delayMs')#等待毫秒
    if not isinstance(链身份,str) or len(链身份)==0:#链身份非法
        失败('llm/retry retryId must be a non-empty string')#retryId必须非空
    失败事实=试取(载荷,'failure')#失败载荷
    校验失败载荷(失败事实,失败)#校验失败事实
    if not 是否安全整数(序号) or 序号<1:#序号非法
        失败('llm/retry retry must be a positive safe integer')#序号必须为正安全整数
    if not isinstance(提供方,str) or len(提供方)==0:#提供方非法
        失败('llm/retry provider must be a non-empty string')#提供方必须非空
    if not isinstance(政策键,str) or len(政策键)==0:#政策键非法
        失败('llm/retry policyKey must be a non-empty string')#政策键必须非空
    if 模式=='normal':#普通
        上限=试取(载荷,'maxRetries')#上限
        if not 是否安全整数(上限) or 上限<1 or 序号>上限:#上限非法或序号超出
            失败('llm/retry retry '+转JS字符串(序号)+' must not exceed a positive safe maxRetries '+转JS字符串(上限))#超出上限
    elif 模式=='always':#始终
        if 有键(载荷,'maxRetries'):#始终模式带了上限
            失败('llm/retry always mode must omit maxRetries')#始终模式不得带上限
    else:#未知模式
        失败('llm/retry mode must be normal or always, got '+转JS字符串(模式))#模式非法
    if isinstance(延迟毫秒,bool) or not isinstance(延迟毫秒,(int,float)) or not 是否有限数(延迟毫秒) or 延迟毫秒<0 or 延迟毫秒>定时器延迟上限毫秒:#延迟越界
        失败('llm/retry delayMs must be a finite number within 0..'+str(定时器延迟上限毫秒))#延迟越界
    def 是回合边界(先前):#回合开始或结束
        """回合开始或结束。"""
        类型=取(先前,'type')#事件类型
        return 类型=='turn/start' or 类型=='turn/end'#开始或结束
    回合边界=从后找(历史,是回合边界)#最近回合边界
    if 试取(回合边界,'type')!='turn/start':#不在打开回合内
        失败('llm/retry must be appended inside an open turn')#必须在打开回合
    打开回合=取(取(回合边界,'data'),'turn')#打开回合号
    if 回合!=打开回合:#点名的回合对不上
        失败('llm/retry names turn '+转JS字符串(回合)+', but the open turn is '+转JS字符串(打开回合))#回合不一致
    def 是步边界(先前):#步开始或结束
        """步开始或结束。"""
        类型=取(先前,'type')#事件类型
        return 类型=='step/start' or 类型=='step/end'#开始或结束
    步边界=从后找(历史,是步边界)#最近步边界
    if 试取(步边界,'type')!='step/start':#不在打开步内
        失败('llm/retry must be appended inside an open step')#必须在打开步
    步载荷=取(步边界,'data')#打开步载荷
    打开步=取(步载荷,'step')#打开步号
    打开步回合=取(步载荷,'turn')#打开步所属回合
    if 步!=打开步 or 回合!=打开步回合:#点名的步对不上
        失败('llm/retry names turn '+转JS字符串(回合)+'/step '+转JS字符串(步)+', but the open step is '+转JS字符串(打开步回合)+'/'+转JS字符串(打开步))#步不一致
    路由提供方=打开步提供方(历史,回合,步)#该步生效的提供方
    if 路由提供方!=提供方:#与失败请求提供方不一致
        失败('llm/retry provider '+转JS字符串(提供方)+' does not match the failed request provider '+转JS字符串(路由提供方))#提供方不匹配
    def 是同政策重试(先前):#同回合同一步同一提供方同一政策的重试
        """同回合同一步同一提供方同一政策的重试。"""
        if 取(先前,'type')!='llm/retry':#不是重试
            return False#不是重试
        先前载荷=取(先前,'data')#先前载荷
        return 取(先前载荷,'turn')==回合 and 取(先前载荷,'step')==步 and 取(先前载荷,'provider')==提供方 and 取(先前载荷,'policyKey')==政策键#同一政策
    先前政策重试=从后找(历史,是同政策重试)#同政策上一条
    上次序号=0 if 先前政策重试 is None else 取(取(先前政策重试,'data'),'retry')#上次序号
    期望序号=上次序号+1#期望序号
    if 序号!=期望序号:#序号不连续
        失败('llm/retry retry '+转JS字符串(序号)+' must equal provider policy retry '+转JS字符串(期望序号))#序号必须连续
    if 先前政策重试 is not None and 取(取(先前政策重试,'data'),'retryId')!=链身份:#链身份变了
        失败('llm/retry must preserve retryId across one provider-policy chain')#同一链必须保留retryId
    if 先前政策重试 is None:#新链
        def 占用链身份(先前):#已被别的链占用的 retryId
            """已被别的链占用的 retryId。"""
            类型=取(先前,'type')#事件类型
            if 类型!='llm/retry' and 类型!='llm/retry-started':#不是本包事件
                return False#不是本包事件
            return 取(取(先前,'data'),'retryId')==链身份#同一身份
        if 从后找(历史,占用链身份) is not None:#已被占用
            失败('llm/retry retryId '+编码(链身份,ensure_ascii=False)+' is already owned by another chain')#retryId冲突

def 校验已开始(历史,事件,失败):#校验 llm/retry-started
    """对照其已调度尝试校验一次等待完成过渡。"""
    载荷=试取(事件,'data')#本条过渡载荷
    链身份=试取(载荷,'retryId')#重试链身份
    回合=试取(载荷,'turn')#回合
    步=试取(载荷,'step')#步
    序号=试取(载荷,'retry')#本次重试序号
    if not isinstance(链身份,str) or len(链身份)==0:#链身份非法
        失败('llm/retry-started retryId must be a non-empty string')#retryId必须非空
    def 是配对调度(先前):#同链同序号的 llm/retry
        """同链同序号的 llm/retry。"""
        if 取(先前,'type')!='llm/retry':#不是调度
            return False#不是调度
        先前载荷=取(先前,'data')#先前载荷
        return 取(先前载荷,'retryId')==链身份 and 取(先前载荷,'retry')==序号#同链同序号
    已调度=从后找(历史,是配对调度)#配对的调度
    if 已调度 is None:#没有配对调度
        失败('llm/retry-started pairs no prior scheduled attempt')#没有配对调度
    调度载荷=取(已调度,'data')#调度载荷
    if 取(调度载荷,'turn')!=回合 or 取(调度载荷,'step')!=步:#回合/步对不上
        失败('llm/retry-started turn/step must match its scheduled attempt')#必须匹配调度
    def 是重复过渡(先前):#已经有同一次的过渡
        """已经有同一次的过渡。"""
        if 取(先前,'type')!='llm/retry-started':#不是过渡
            return False#不是过渡
        先前载荷=取(先前,'data')#先前载荷
        return 取(先前载荷,'retryId')==链身份 and 取(先前载荷,'retry')==序号#同链同序号
    if 从后找(历史,是重复过渡) is not None:#已经有同一次的过渡
        失败('llm/retry-started repeats one scheduled attempt')#不得重复

def 校验会话(会话,失败):#回放整份会话
    """校验一份已加载会话里已有的每条重试记录。"""
    事件们=会话.events#会话事件
    下标=0#当前下标
    for 事件 in 事件们:#按顺序回放
        类型=取(事件,'type')#事件类型
        if 类型=='llm/retry':#重试记录
            校验重试(事件们[:下标],事件,失败)#重试记录
        elif 类型=='llm/retry-started':#过渡记录
            校验已开始(事件们[:下标],事件,失败)#过渡记录
        下标+=1#前进

def 安装(上下文,失败):#给已加载与新追加的重试记录安装校验
    """给已加载与新追加的重试记录安装校验。"""
    for 会话 in 上下文.sessions.list():#回放已有会话
        校验会话(会话,失败)#回放
    def 新会话(会话):#新会话也回放
        """新会话也回放。"""
        校验会话(会话,失败)#回放
    上下文.on('session/created',新会话,{'global':True})#新会话也回放
    def 分派钩子(模式,事件名,参数列表,*其余):#新追加的会话事件
        """新追加的会话事件。"""
        if 事件名!='session/event':#只看会话事件
            return#只看会话事件
        会话=参数列表[0]#会话
        事件=参数列表[1]#事件
        类型=取(事件,'type')#事件类型
        if 类型=='llm/retry':#校验重试
            校验重试(会话.events,事件,失败)#校验重试
        elif 类型=='llm/retry-started':#校验过渡
            校验已开始(会话.events,事件,失败)#校验过渡
    上下文.on('internal/dispatch',分派钩子,{'global':True})#全局监听分派

安装.inject=['sessions']#还依赖sessions

def 应用(上下文):#注册 LLM 重试不变量配套
    """注册 LLM 重试不变量配套。

    参数：
    上下文:上下文
    返回：
    已兑现的释放器承诺
    """
    return 已兑现(上下文.invariants.register(包名,安装))#注册本包不变量并包成已决议承诺
