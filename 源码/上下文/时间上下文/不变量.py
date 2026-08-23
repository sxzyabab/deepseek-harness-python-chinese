"""本包拥有的持久时钟上下文不变量。"""
import json,math,re#JSON片段、安全整数与读数格式
from datetime import datetime as 日期时间#解析渲染时间戳
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器
from .请求时区 import 推导浏览器时区上下文,渲染浏览器时区上下文#推导与渲染浏览器时区
from .时间戳 import 创建时间戳格式化器,格式化时间戳#时间戳格式化

__all__=['包名','名称','注入','安装','应用','name','inject']#公开面

包名='@deepseek-ai/dsh-time-context'#本包的不变量所有权名
来源名='time-context'#来源记录里的插件名
名称='time-context-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
安全整数上限=9007199254740991#Number.MAX_SAFE_INTEGER
编码=json.dumps#JSON编码
读数格式=re.compile(#持久读数的整段格式
    r'^Time sampled while preparing turn (\d+), step (\d+): '#回合与步骤
    +r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})\[[^\]]+\])\n'#形如ISO的时间戳
    +r'(Browser time zone for this request: .+)\n'#浏览器时区行
    +r'Elapsed since the preceding (model-visible message|step context): '#基线种类
    +r'(?:unavailable|(?:(?:\d+d )?(?:\d+h )?(?:\d+m )?\d+s))\.$'#不可用或紧凑时长
)#读数格式结束
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 有自有(对象,键):#对齐in / hasOwn
    """对齐字段是否自有。"""
    if 对象 is None:#空对象
        return False#没有
    if isinstance(对象,dict):#映射
        return 键 in 对象#映射键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:#没有字典
        return False#没有
    return 键 in 字典#自有

def 键数量(对象):#对齐Object.keys(对象).length
    """对象自有键数量。"""
    if 对象 is None:#空
        return 0#零
    if isinstance(对象,dict):#映射
        return len(对象)#键数
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:#没有
        return 0#零
    return len(字典)#键数

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

def 准备位置(历史,失败):#当前打开的回合与步骤
    """推导一条时钟上下文读数可以追加的打开步骤边界。"""
    打开回合=None#打开的回合号
    打开步骤=None#打开的步骤号
    请求已开始=False#是否已见到request/header
    for 事件 in 历史:#扫描到当前事件之前
        种类=取字段(事件,'type')#按事件类型更新边界
        if 种类=='turn/start':#回合开始
            打开回合=取字段(取字段(事件,'data'),'turn')#记下回合
            打开步骤=None#步骤尚未开始
            请求已开始=False#新回合尚未请求
        elif 种类=='step/start':#步骤开始
            打开步骤=取字段(取字段(事件,'data'),'step')#记下步骤
            请求已开始=False#本步尚未请求
        elif 种类=='request/header':#请求头已发出
            请求已开始=True#读数必须在此之前
        elif 种类=='step/end':#步骤结束
            打开步骤=None#不再有打开步骤
            请求已开始=False#复位
        elif 种类=='turn/end':#回合结束
            打开回合=None#不再有打开回合
            打开步骤=None#步骤一并关闭
            请求已开始=False#复位
        #其他事件不影响边界
    if 打开回合 is None:#必须在打开回合内
        失败('time-context reading must be appended inside an open turn')#失败
    if 打开步骤 is None:#必须在step/start之后
        失败('time-context reading must follow step/start')#失败
    if 请求已开始:#必须在request/header之前
        失败('time-context reading must precede request/header')#失败
    return {'turn':打开回合,'step':打开步骤}#返回打开边界

def 末次下标(历史,回合):#找本回合turn/start
    """从后往前找本回合 turn/start 下标，没有则 -1。"""
    for 下标 in range(len(历史)-1,-1,-1):#从末尾往前
        事件=历史[下标]#当前
        if 取字段(事件,'type')=='turn/start' and 取字段(取字段(事件,'data'),'turn')==回合:#命中
            return 下标#下标
    return -1#未找到

def 请求消息们(历史,回合):#本回合已进入的用户消息
    """收集属于一轮打开回合的已进入用户消息。"""
    起点=末次下标(历史,回合)#本回合开始下标
    结果=[]#收集
    for 事件 in 历史[起点+1:]:#开始之后
        if 取字段(事件,'type')=='user/message':#只收用户消息
            结果.append(取字段(事件,'data'))#收下
    return 结果#已进入用户消息

def 解析渲染时间(渲染):#去掉时区括号再解析为纪元毫秒
    """对齐 Date.parse(rendered.replace(/\\[[^\\]]+\\]$/, ''))。"""
    去掉括号=re.sub(r'\[[^\]]+\]$','',渲染)#去掉时区括号
    try:#解析ISO
        时刻=日期时间.fromisoformat(去掉括号.replace('Z','+00:00'))#Z写成偏移
    except Exception:#无法解析
        return float('nan')#非有限
    return int(时刻.timestamp()*1000)#纪元毫秒

def 校验读数(历史,事件,失败):#校验单条读数
    """按会话位置与时间戳校验一条带插件归属的时钟读数。"""
    内容=取字段(取字段(事件,'data'),'content')#内容块列表
    if not isinstance(内容,list):#必须是列表
        内容=[]#空
    块值=内容[0] if len(内容)>0 else None#第一块未知
    if isinstance(块值,dict) and 块值 is not None:#须为对象
        块=块值#收成记录
    else:#否则没有块
        块=None#没有块
    块文本=取字段(块,'text') if 块 is not None else None#可能的文本
    if (len(内容)!=1#必须恰好一块
        or 块 is None#必须是对象
        or 键数量(块)!=2#只有type与text
        or 取字段(块,'type')!='text'#必须是文本块
        or not isinstance(块文本,str)):#text必须是字符串
        失败('time-context messages must contain exactly one text block')#内容形态非法
    匹配=读数格式.match(块文本) if isinstance(块文本,str) else None#按持久格式匹配
    if 匹配 is None:#格式不对
        失败('time-context message does not match the durable reading format')#格式不对
        return#已失败
    回合=int(匹配.group(1))#捕获的回合
    步骤=int(匹配.group(2))#捕获的步骤
    if (not 是否安全整数(回合)) or 回合<1 or (not 是否安全整数(步骤)) or 步骤<1:#必须是正安全整数
        失败('time-context turn and step must be positive safe integers')#回合步骤非法
    期望=准备位置(历史,失败)#历史推导的打开边界
    if 回合!=取字段(期望,'turn') or 步骤!=取字段(期望,'step'):#读数自称的位置必须吻合
        失败('time-context reading names turn '+str(回合)+'/step '+str(步骤)+', expected turn '+str(取字段(期望,'turn'))+'/step '+str(取字段(期望,'step')))#位置不符
    来源=取字段(取字段(事件,'data'),'source')#消息来源
    if 取字段(来源,'kind')!='plugin' or 取字段(来源,'plugin')!=来源名:#必须保留本包所有权
        失败('time-context source must retain package ownership')#来源所有权丢失
    分段们=取字段(来源,'sections') if 有自有(来源,'sections') else None#快照分段
    段值=分段们[0] if isinstance(分段们,list) and len(分段们)>0 else None#第一段未知
    if isinstance(段值,dict) and 段值 is not None:#须为对象
        段=段值#收成记录
    else:#否则没有段
        段=None#没有段
    if (键数量(来源)!=4#来源只有kind/plugin/form/sections
        or 取字段(来源,'form')!='snapshot'#必须是快照形态
        or not isinstance(分段们,list)#sections必须是数组
        or len(分段们)!=1#恰好一段
        or 段 is None#第一段必须是对象
        or 键数量(段)!=2#只有name与text
        or 取字段(段,'name')!=来源名#段名必须是本插件
        or 取字段(段,'text')!=块文本):#段文本必须与正文完全相同
        失败('time-context source must carry only the exact snapshot text, not request authority')#不得夹带请求权威
    渲染浏览器上下文=匹配.group(4)#读数里的时区行
    浏览器上下文=推导浏览器时区上下文(请求消息们(历史,回合))#由本回合用户消息重推导
    期望浏览器上下文=渲染浏览器时区上下文(浏览器上下文)#期望策略行
    if 渲染浏览器上下文!=期望浏览器上下文:#必须一致
        失败('time-context browser-zone text does not match current-turn user messages')#时区行与本回合消息不符
    基线=匹配.group(5)#经过时长基线种类
    if (步骤==1)!=(基线=='model-visible message'):#首步必须用模型可见消息基线
        失败('time-context step '+str(步骤)+' uses the wrong elapsed-time baseline '+编码(基线,ensure_ascii=False))#基线种类错误
    渲染=匹配.group(3)#渲染出的时间戳
    if 渲染 is None:#正则必有第三组
        失败('time-context reading omitted its rendered timestamp')#缺时间戳
        return#已失败
    渲染时间=解析渲染时间(渲染)#去掉时区括号再解析
    事件时间=取字段(事件,'time')#事件时间
    if ((not math.isfinite(渲染时间)) or (not 是否安全整数(事件时间))#必须能解析且事件时间是安全整数
        or 事件时间<渲染时间):#事件时间不得早于渲染时间戳
        失败('time-context rendered timestamp must parse and not postdate its durable event')#时间戳与事件时间不一致
    if 取字段(浏览器上下文,'kind')=='resolved':#唯一浏览器时区时，时间戳必须按该时区重放
        try:#按浏览器时区格式化
            期望时间戳=格式化时间戳(#重放
                渲染时间,#解析出的纪元毫秒
                创建时间戳格式化器(取字段(浏览器上下文,'timeZone')),#该时区格式化器
                取字段(浏览器上下文,'timeZone'),#括号标签
            )#格式化结束
        except Exception as 错误:#时区无法格式化
            失败('time-context browser zone cannot format its durable timestamp: '+str(错误))#格式化失败
            return#已失败
        if 渲染!=期望时间戳:#必须与按该时区重放的结果一致
            失败('time-context rendered timestamp does not match the unique browser zone')#时间戳与浏览器时区不符

def 校验会话(会话,失败):#校验会话已有读数
    """校验一个会话里已经存在的、本包拥有的全部读数。"""
    事件们=list(取字段(会话,'events'))#事件列表
    for 下标,事件 in enumerate(事件们):#带下标扫描
        来源=取字段(取字段(事件,'data'),'source')#来源
        if (取字段(事件,'type')!='user/message'#非用户消息
            or 取字段(来源,'kind')!='plugin'#非插件来源
            or 取字段(来源,'plugin')!=来源名):#非本插件
            continue#跳过
        校验读数(事件们[0:下标],事件,失败)#用该事件之前的历史校验

def 安装(上下文对象,失败):#安装已加载与新追加校验
    """为已加载与新追加的上下文读数安装校验。"""
    for 会话对象 in 上下文对象.sessions.list():#先校验现有会话
        校验会话(会话对象,失败)#校验
    def 会话已创建(会话,*其余):#新会话也校验
        """新会话创建时校验。"""
        校验会话(会话,失败)#校验
    def 内部派发(_模式,事件名,参数,*其余):#新追加事件
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只看会话事件
            return#放过
        会话=参数[0]#会话
        事件=参数[1]#事件
        来源=取字段(取字段(事件,'data'),'source')#来源
        if (取字段(事件,'type')!='user/message'#非用户消息
            or 取字段(来源,'kind')!='plugin'#非插件
            or 取字段(来源,'plugin')!=来源名):#非本插件
            return#放过
        校验读数(取字段(会话,'events'),事件,失败)#追加时历史已含本事件，准备位置按此前边界计算
    上下文对象.on('session/created',会话已创建,{'global':True})#新会话也校验
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听

安装.inject=['sessions']#安装前需要sessions

def 应用(上下文对象):#注册时钟上下文不变量配套
    """注册时钟上下文不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记本包不变量并包成立即兑现的承诺

apply=应用#Cordis插件入口