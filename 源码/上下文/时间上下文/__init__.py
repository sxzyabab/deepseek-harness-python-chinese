"""可选的请求时钟上下文。符合条件的步骤把带源归属的持久时间读数加进请求历史。"""
import json,time#JSON诊断与纪元毫秒
from zoneinfo import ZoneInfoNotFoundError as 时区未找到#时区解析失败
from ...依赖.schemastery import 字符串字段,数字字段
from ...模型后端.llm import 创建用户消息#导入用户消息构造
from .请求时区 import 推导浏览器时区上下文,渲染浏览器时区上下文#推导与渲染浏览器时区
from .时间戳 import 创建时间戳格式化器,格式化时间戳,时间戳错误#时间戳格式化与错误

__all__=['包名','名称','依赖','应用','默认','配置']

包名='@deepseek-ai/dsh-time-context'
名称='time-context'
依赖=['agents','sessionProjections']
安全整数上限=9007199254740991#外来 JSON Number.MAX_SAFE_INTEGER
配置={
    'timeZone':字符串字段(),#打开的回合没有唯一浏览器时区时的回退展示时区；省略则用进程时区
    'refreshIntervalMs':数字字段(),#同一会话两次持久注入之间的最小毫秒；省略或0则每个符合条件的步骤都注入
}

class 时间上下文错误(Exception):
    """时间上下文包的异常基类。"""

def 编码(值):
    """诊断用紧凑 JSON。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#JSON

def 取时间毫秒():
    """当前纪元毫秒。"""
    return int(time.time()*1000)#纪元毫秒

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位即中止

def 格式化时长(经过毫秒):
    """把非负经过毫秒格式化为紧凑的整秒单位。"""
    秒=int(max(0,经过毫秒)//1000)#先收成非负整秒
    天=秒//86400#整天
    秒%=86400#去掉天
    小时=秒//3600#整小时
    秒%=3600#去掉小时
    分钟=秒//60#整分钟
    秒%=60#剩余秒
    片段=[]#非零单位片段
    if 天>0:#有天才出天
        片段.append(str(天)+'d')#天
    if 小时>0:#有小时才出小时
        片段.append(str(小时)+'h')#小时
    if 分钟>0:#有分钟才出分钟
        片段.append(str(分钟)+'m')#分钟
    片段.append(str(秒)+'s')#秒始终出现
    return ' '.join(片段)#空格拼接

def 末次下标(序列,回合):
    """从后往前找本回合 turn/start 下标，没有则 -1。"""
    for 下标 in range(len(序列)-1,-1,-1):#从末尾往前
        事件=序列[下标]#当前事件
        数据=事件['data'] if 'data' in 事件 else {}#载荷
        if 事件['type']=='turn/start' and 数据['turn']==回合:#命中
            return 下标#下标
    return -1#未找到

def 收集请求消息(智能体,回合,拟议):
    """收集属于一轮打开回合的、已进入与拟议用户消息。"""
    事件列表=list(智能体.session.events)#会话事件
    起点=末次下标(事件列表,回合)#本回合开始
    if 起点<0:#没有回合开始
        已进入=[]#则没有已进入消息
    else:#有回合开始
        已进入=[]#收集已进入
        for 事件 in 事件列表[起点+1:]:#回合开始之后
            if 事件['type']=='user/message':#只收用户消息
                已进入.append(事件['data'])#收下
    return list(已进入)+list(拟议)#已进入加本步拟议

def 渲染文本(此刻,回合,步骤,先前,格式化器,时区,浏览器上下文):
    """持久读数文本。"""
    经过='unavailable' if 先前 is None else 格式化时长(此刻-先前)#没有基线则不可用
    基线='model-visible message' if 步骤==1 else 'step context'#首步用模型可见消息，其后用步骤上下文
    浏览器文本=渲染浏览器时区上下文(浏览器上下文)#时区策略行
    return ('Time sampled while preparing turn '+str(回合)+', step '+str(步骤)+': '+格式化时间戳(此刻,格式化器,时区)+'\n'
        +浏览器文本+'\n'
        +'Elapsed since the preceding '+基线+': '+经过+'.')#经过时长行

def 校验刷新间隔(刷新间隔毫秒):
    """拒绝无法表示精确经过毫秒差值的刷新间隔。"""
    if 刷新间隔毫秒 is None:#省略
        return#通过
    if isinstance(刷新间隔毫秒,bool):#布尔不是整数
        raise TypeError('time-context: refreshIntervalMs must be a non-negative safe integer, got '+str(刷新间隔毫秒))#加载失败
    if isinstance(刷新间隔毫秒,int):#整数
        合法=abs(刷新间隔毫秒)<=安全整数上限#外来安全范围
    elif isinstance(刷新间隔毫秒,float) and 刷新间隔毫秒.is_integer():#整值浮点
        合法=abs(刷新间隔毫秒)<=安全整数上限#外来安全范围
    else:#其它
        合法=False#非法
    if (not 合法) or 刷新间隔毫秒<0:#提供了间隔且非法
        raise TypeError('time-context: refreshIntervalMs must be a non-negative safe integer, got '+str(刷新间隔毫秒))#加载失败

def 应用(上下文,配置值):
    """在 ctx 的生命周期内注册一条前置的预步骤监听器。"""
    if 配置值 is None:#缺省空配置
        配置值={}#空配置
    时区=配置值['timeZone'] if 'timeZone' in 配置值 else None#可选回退时区
    刷新间隔毫秒=配置值['refreshIntervalMs'] if 'refreshIntervalMs' in 配置值 else None#可选刷新间隔
    校验刷新间隔(刷新间隔毫秒)#非法间隔在加载时失败
    try:#尝试按配置或进程时区创建
        回退格式化器=创建时间戳格式化器(时区)#None表示进程默认
    except (时区未找到,时间戳错误,ValueError,KeyError,OSError) as 错误:#无法解析
        if 时区 is None:#未配置则是系统时区失败
            消息='time-context: failed to resolve the system time zone'#系统时区
        else:#配置非法
            消息='time-context: invalid IANA timeZone '+编码(时区)#配置非法
        raise 时间上下文错误(消息) from 错误#包装并挂cause
    回退时区=回退格式化器.解析选项().timeZone#解析出的规范回退时区
    格式化器表={回退时区:回退格式化器}#按时区缓存格式化器

    def 取格式化器(选中时区):
        """解析并缓存一个请求本地的时间戳格式化器。"""
        if 选中时区 in 格式化器表:#缓存命中
            return 格式化器表[选中时区]#直接用
        新建=创建时间戳格式化器(选中时区)#新建
        格式化器表[选中时区]=新建#写入缓存
        return 新建#返回

    def 初始状态(头=None):
        """投影初始读数。"""
        return {'lastMessageTime':None,'lastInjectionTime':None,'lastTurnInjectionTime':None}

    def 折叠状态(状态,事件):
        """按事件推进时钟投影。"""
        种类=事件['type']
        if 种类=='turn/start' or 种类=='turn/end':
            if 状态['lastTurnInjectionTime'] is None:
                return 状态
            下一=dict(状态)
            下一['lastTurnInjectionTime']=None
            return 下一
        if 种类=='user/message':
            出处=事件['data']['source'] if 'source' in 事件['data'] else None
            本插件=isinstance(出处,dict) and 出处['kind']==名称
            下一=状态 if 状态['lastMessageTime']==事件['time'] else dict(状态,lastMessageTime=事件['time'])
            if not 本插件:
                return 下一
            下一=dict(下一)
            下一['lastInjectionTime']=事件['time']
            下一['lastTurnInjectionTime']=事件['time']
            return 下一
        if 种类=='assistant/message' or 种类=='tool/result':
            if 状态['lastMessageTime']==事件['time']:
                return 状态
            return dict(状态,lastMessageTime=事件['time'])
        return 状态

    上下文.sessionProjections.登记({
        'key':'timeContext',
        'stateVersion':2,
        'init':初始状态,
        'apply':折叠状态,
    })

    def 预步骤监听(载荷,下一步,*剩余):
        """先让后续监听器决定；进入且未取消时追加时钟读数。"""
        决策=下一步()#先让后续监听器决定
        信号=载荷['signal'] if 'signal' in 载荷 else None#取消信号
        if 决策['kind']=='reject' or 已中止(信号):#拒绝或已取消则不注入
            return 决策#原样返回
        此刻=取时间毫秒()#采样时刻
        智能体=载荷['agent']#智能体
        状态=上下文.sessionProjections.状态(智能体.session,'timeContext')
        if 状态 is None:
            状态=初始状态()
        if 刷新间隔毫秒 is not None and 刷新间隔毫秒>0:#启用了正间隔
            上次注入=状态['lastInjectionTime']
            if (上次注入 is not None
                and 此刻>=上次注入
                and 此刻-上次注入<刷新间隔毫秒):#间隔未到则跳过
                return 决策#跳过
        步骤=载荷['step']#步骤号
        回合=载荷['turn']#回合号
        if 步骤==1:#首步
            先前=状态['lastMessageTime']
        else:#后续步
            先前=状态['lastTurnInjectionTime']
        拟议=决策['messages'] if 'messages' in 决策 and 决策['messages'] is not None else []#拟议
        消息列表=收集请求消息(智能体,回合,拟议)#本回合用户消息
        浏览器=推导浏览器时区上下文(消息列表)#推导浏览器时区
        if 浏览器['kind']=='resolved':#唯一浏览器时区优先
            选中时区=浏览器['timeZone']#浏览器时区
        else:#否则回退
            选中时区=回退时区#回退时区
        文本=渲染文本(此刻,回合,步骤,先前,取格式化器(选中时区),选中时区,浏览器)#渲染读数
        消息列表=list(拟议)#原消息
        消息列表.append(创建用户消息({
            'content':[{'type':'text','text':文本}],#读数文本
            'source':{'kind':名称,'form':'snapshot','sections':[{'name':名称,'text':文本}]},#快照形态，不含请求权威
        }))#追加结束
        return {'kind':'enter','messages':消息列表}#进入并追加读数

    上下文.监听('agent/pre-step',预步骤监听,{'前置':True})#前置，以便后续监听器看见已追加的读数

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
