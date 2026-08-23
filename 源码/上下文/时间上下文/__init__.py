"""可选的请求时钟上下文。符合条件的步骤把带源归属的持久时间读数加进请求历史。"""
import json,math,time#JSON诊断、安全整数与纪元毫秒
from ...依赖 import cordis,schemastery#外部依赖胶水
模式=schemastery.模式#导入配置校验
是否thenable=cordis.工具.是否thenable#可等待判定
from ..llm import 创建用户消息#导入用户消息构造
from .请求时区 import 推导浏览器时区上下文,渲染浏览器时区上下文#推导与渲染浏览器时区
from .时间戳 import 创建时间戳格式化器,格式化时间戳#时间戳格式化

__all__=['名称','注入','应用','配置','Config','name','inject']#公开面

名称='time-context'#插件名，来源记录共用
注入=['agents']#依赖agents服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
安全整数上限=9007199254740991#Number.MAX_SAFE_INTEGER
编码=json.dumps#JSON编码
配置=模式.对象({#请求准备阶段的时钟格式化与追加调度；非法值在插件加载时失败
    'timeZone':模式.字符串(),#打开的回合没有唯一浏览器时区时的回退展示时区；省略则用进程时区
    'refreshIntervalMs':模式.数字(),#同一会话两次持久注入之间的最小毫秒；省略或0则每个符合条件的步骤都注入
})#配置模式结束
Config=配置#Cordis配置模式

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 取时间毫秒():#对齐Date.now
    """当前纪元毫秒。"""
    return int(time.time()*1000)#纪元毫秒

def 是否安全整数(值):#对齐JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#在安全范围内
    if isinstance(值,float):#浮点
        if not math.isfinite(值) or not 值.is_integer():#非有限或非整
            return False#不是安全整数
        return abs(值)<=安全整数上限#在安全范围内
    return False#其它类型

def 格式化时长(经过毫秒):#格式化经过时长
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

def 前序消息时间(智能体):#上一条模型可见消息时间
    """找最新的模型可见事件，排除本插件待追加的那条。"""
    for 事件 in reversed(list(取字段(取字段(智能体,'session'),'events'))):#从新到旧
        种类=取字段(事件,'type')#事件类型
        if 种类=='user/message' or 种类=='assistant/message' or 种类=='tool/result':#这三类算模型可见
            return 取字段(事件,'time')#可见消息时间
        #可合并扩展的会话事件：非表面记录不是消息。
    return None#没有更早的可见消息

def 前序步骤上下文时间(智能体,回合):#本回合前一次时钟上下文时间
    """在打开的回合里找前一条 time-context 事件。"""
    for 事件 in reversed(list(取字段(取字段(智能体,'session'),'events'))):#从新到旧
        if 取字段(事件,'type')=='turn/start' and 取字段(取字段(事件,'data'),'turn')==回合:#碰到本回合开始则没有更早的本插件注入
            return None#本回合尚无注入
        来源=取字段(取字段(事件,'data'),'source')#消息来源
        if (取字段(事件,'type')=='user/message'#用户消息
            and 取字段(来源,'kind')=='plugin'#插件来源
            and 取字段(来源,'plugin')==名称):#本插件
            return 取字段(事件,'time')#前一次注入时间
    return None#本回合没有前一次注入

def 最新注入时间(智能体):#最新注入时间，用于刷新间隔
    """找本插件最新的持久注入，包括被表面遮蔽的事件。"""
    for 事件 in reversed(list(取字段(取字段(智能体,'session'),'events'))):#从新到旧扫原始事件
        来源=取字段(取字段(事件,'data'),'source')#消息来源
        if (取字段(事件,'type')=='user/message'#用户消息
            and 取字段(来源,'kind')=='plugin'#插件来源
            and 取字段(来源,'plugin')==名称):#本插件
            return 取字段(事件,'time')#最新一次
    return None#从未注入

def 末次下标(序列,回合):#对齐findLastIndex找本回合turn/start
    """从后往前找本回合 turn/start 下标，没有则 -1。"""
    for 下标 in range(len(序列)-1,-1,-1):#从末尾往前
        事件=序列[下标]#当前事件
        if 取字段(事件,'type')=='turn/start' and 取字段(取字段(事件,'data'),'turn')==回合:#命中
            return 下标#下标
    return -1#未找到

def 请求消息们(智能体,回合,拟议):#本回合用户消息
    """收集属于一轮打开回合的、已进入与拟议用户消息。"""
    事件们=list(取字段(取字段(智能体,'session'),'events'))#会话事件
    起点=末次下标(事件们,回合)#本回合开始
    if 起点<0:#没有回合开始
        已进入=[]#则没有已进入消息
    else:#有回合开始
        已进入=[]#收集已进入
        for 事件 in 事件们[起点+1:]:#回合开始之后
            if 取字段(事件,'type')=='user/message':#只收用户消息
                已进入.append(取字段(事件,'data'))#收下
    return list(已进入)+list(拟议)#已进入加本步拟议

def 渲染文本(此刻,回合,步骤,先前,格式化器,时区,浏览器上下文):#渲染一条时钟读数
    """持久读数文本。"""
    经过='unavailable' if 先前 is None else 格式化时长(此刻-先前)#没有基线则不可用
    基线='model-visible message' if 步骤==1 else 'step context'#首步用模型可见消息，其后用步骤上下文
    浏览器文本=渲染浏览器时区上下文(浏览器上下文)#时区策略行
    return ('Time sampled while preparing turn '+str(回合)+', step '+str(步骤)+': '+格式化时间戳(此刻,格式化器,时区)+'\n'#采样行
        +浏览器文本+'\n'#浏览器时区行
        +'Elapsed since the preceding '+基线+': '+经过+'.')#经过时长行

def 校验刷新间隔(刷新间隔毫秒):#校验刷新间隔
    """拒绝无法表示精确经过毫秒差值的刷新间隔。"""
    if 刷新间隔毫秒 is not None and ((not 是否安全整数(刷新间隔毫秒)) or 刷新间隔毫秒<0):#提供了间隔且非法
        raise TypeError('time-context: refreshIntervalMs must be a non-negative safe integer, got '+str(刷新间隔毫秒))#加载失败，诊断含原值

def 信号已中止(信号):#对齐signal.aborted
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if 取字段(信号,'aborted') is True:#英文
        return True#已中止
    if 取字段(信号,'已中止') is True:#中文
        return True#已中止
    return False#未中止

def 应用(上下文,配置值):#注册时钟上下文插件
    """在 ctx 的生命周期内注册一条前置的预步骤监听器。刷新间隔非法，或配置的/进程时区无法解析时抛错。"""
    if 配置值 is None:#缺省空配置
        配置值={}#空配置
    时区=取字段(配置值,'timeZone')#可选回退时区
    刷新间隔毫秒=取字段(配置值,'refreshIntervalMs')#可选刷新间隔
    校验刷新间隔(刷新间隔毫秒)#非法间隔在加载时失败
    try:#尝试按配置或进程时区创建
        回退格式化器=创建时间戳格式化器(时区)#None表示进程默认
    except Exception as 错误:#无法解析
        if 时区 is None:#未配置则是系统时区失败
            消息='time-context: failed to resolve the system time zone'#系统时区
        else:#配置非法
            消息='time-context: invalid IANA timeZone '+编码(时区,ensure_ascii=False)#配置非法
        raise Exception(消息) from 错误#包装并挂cause
    回退时区=回退格式化器.resolvedOptions().timeZone#解析出的规范回退时区
    格式化器表={回退时区:回退格式化器}#按时区缓存格式化器

    def 取格式化器(选中时区):#按选中时区取格式化器
        """解析并缓存一个请求本地的时间戳格式化器。"""
        已有=格式化器表.get(选中时区)#缓存命中
        if 已有 is not None:#命中
            return 已有#直接用
        新建=创建时间戳格式化器(选中时区)#新建
        格式化器表[选中时区]=新建#写入缓存
        return 新建#返回

    def 预步骤监听(载荷,下一步,*剩余):#前置预步骤：先委托再追加时钟读数
        """先让后续监听器决定；进入且未取消时追加时钟读数。"""
        决策=解开(下一步())#先让后续监听器决定
        if 取字段(决策,'kind')=='reject' or 信号已中止(取字段(载荷,'signal')):#拒绝或已取消则不注入
            return 决策#原样返回
        此刻=取时间毫秒()#采样时刻
        if 刷新间隔毫秒 is not None and 刷新间隔毫秒>0:#启用了正间隔
            上次注入=最新注入时间(取字段(载荷,'agent'))#上次注入
            if (上次注入 is not None#有过注入
                and 此刻>=上次注入#时钟未回拨
                and 此刻-上次注入<刷新间隔毫秒):#间隔未到则跳过
                return 决策#跳过
        步骤=取字段(载荷,'step')#步骤号
        回合=取字段(载荷,'turn')#回合号
        智能体=取字段(载荷,'agent')#智能体
        if 步骤==1:#首步
            先前=前序消息时间(智能体)#相对上一条模型可见消息
        else:#后续步
            先前=前序步骤上下文时间(智能体,回合)#相对本回合前一次时钟上下文
        消息们=请求消息们(智能体,回合,取字段(决策,'messages') or [])#本回合用户消息
        浏览器=推导浏览器时区上下文(消息们)#推导浏览器时区
        if 取字段(浏览器,'kind')=='resolved':#唯一浏览器时区优先
            选中时区=取字段(浏览器,'timeZone')#浏览器时区
        else:#否则回退
            选中时区=回退时区#回退时区
        文本=渲染文本(此刻,回合,步骤,先前,取格式化器(选中时区),选中时区,浏览器)#渲染读数
        消息列表=list(取字段(决策,'messages') or [])#原消息
        消息列表.append(创建用户消息({#时钟上下文
            'content':[{'type':'text','text':文本}],#读数文本
            'source':{'kind':'plugin','plugin':名称,'form':'snapshot','sections':[{'name':名称,'text':文本}]},#快照形态，不含请求权威
        }))#追加结束
        return {'kind':'enter','messages':消息列表}#进入并追加读数

    上下文.on('agent/pre-step',预步骤监听,{'prepend':True})#前置，以便后续监听器看见已追加的读数

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出