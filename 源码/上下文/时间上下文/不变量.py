"""本包拥有的持久时钟上下文不变量。"""
import json,re#JSON片段与读数格式
from datetime import datetime as 日期时间,timezone as 时区#解析渲染时间戳
from .请求时区 import 推导浏览器时区上下文,渲染浏览器时区上下文#推导与渲染浏览器时区
from .时间戳 import 创建时间戳格式化器,格式化时间戳#时间戳格式化

__all__=['包名','名称','注入','安装','应用']#仅中文公开名

包名='@deepseek-ai/dsh-time-context'#本包的不变量所有权名
来源名='time-context'#来源记录里的插件名
名称='time-context-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
安全整数上限=9007199254740991#外来 JSON 校验点
读数格式=re.compile(#持久读数的整段格式
    r'^Time sampled while preparing turn ([0-9]+), step ([0-9]+): '#回合与步骤
    +r'([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|[+-][0-9]{2}:[0-9]{2})\[[^\]]+\])\n'#形如ISO的时间戳，时区括号标签原样
    +r'(Browser time zone for this request: .+)\n'#浏览器时区行
    +r'Elapsed since the preceding (model-visible message|step context): '#基线种类
    +r'(?:unavailable|(?:(?:[0-9]+d )?(?:[0-9]+h )?(?:[0-9]+m )?[0-9]+s))\.\Z',#不可用或紧凑时长
    re.ASCII,#JS \d 只吃 ASCII
)#读数格式结束

def 准备位置(历史,失败):
    """推导一条时钟上下文读数可以追加的打开步骤边界。"""
    打开回合=None#打开的回合号
    打开步骤=None#打开的步骤号
    请求已开始=False#是否已见到request/header
    for 事件 in 历史:#扫描到当前事件之前
        种类=事件['type']#按事件类型更新边界
        if 种类=='turn/start':#回合开始
            打开回合=事件['data']['turn']#记下回合
            打开步骤=None#步骤尚未开始
            请求已开始=False#新回合尚未请求
        elif 种类=='step/start':#步骤开始
            打开步骤=事件['data']['step']#记下步骤
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
    if 打开回合 is None:#必须在打开回合内
        失败('time-context reading must be appended inside an open turn')#失败
    if 打开步骤 is None:#必须在step/start之后
        失败('time-context reading must follow step/start')#失败
    if 请求已开始:#必须在request/header之前
        失败('time-context reading must precede request/header')#失败
    return {'turn':打开回合,'step':打开步骤}#返回打开边界

def 末次下标(历史,回合):
    """从后往前找本回合 turn/start 下标，没有则 -1。"""
    for 下标 in range(len(历史)-1,-1,-1):#从末尾往前
        事件=历史[下标]#当前
        if 事件['type']=='turn/start' and 事件['data']['turn']==回合:#命中
            return 下标#下标
    return -1#未找到

def 请求消息列表(历史,回合):
    """收集属于一轮打开回合的已进入用户消息。"""
    起点=末次下标(历史,回合)#本回合开始下标
    结果=[]#收集
    for 事件 in 历史[起点+1:]:#开始之后
        if 事件['type']=='user/message':#只收用户消息
            结果.append(事件['data'])#收下
    return 结果#已进入用户消息

def 解析渲染时间(渲染):
    """按读数里写死的 ISO 形态解析为纪元毫秒；时区括号标签先剥掉再解析。"""
    去掉括号=re.sub(r'\[[^\]]+\]\Z','',渲染,count=1,flags=re.ASCII)#去掉时区括号标签
    if 去掉括号.endswith('Z'):#UTC 字面量
        时刻=日期时间.strptime(去掉括号,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=时区.utc)#按 UTC 解析
    else:
        时刻=日期时间.strptime(去掉括号,'%Y-%m-%dT%H:%M:%S%z')#带偏移
    return int(时刻.timestamp()*1000)#纪元毫秒

def 校验读数(历史,事件,失败):
    """按会话位置与时间戳校验一条带插件归属的时钟读数。"""
    内容=事件['data']['content']#内容块列表
    if not isinstance(内容,list):#必须是列表
        内容=[]#空
    块值=内容[0] if len(内容)>0 else None#第一块未知
    块=块值 if isinstance(块值,dict) else None#须为对象
    块文本=块['text'] if 块 is not None and 'text' in 块 else None#可能的文本
    if (len(内容)!=1#必须恰好一块
        or 块 is None#必须是对象
        or len(块)!=2#只有type与text
        or 块['type']!='text'#必须是文本块
        or not isinstance(块文本,str)):#text必须是字符串
        失败('time-context messages must contain exactly one text block')#内容形态非法
    匹配=读数格式.match(块文本) if isinstance(块文本,str) else None#按持久格式匹配
    if 匹配 is None:#格式不对
        失败('time-context message does not match the durable reading format')#格式不对
        return#已失败
    回合=int(匹配.group(1))#捕获的回合
    步骤=int(匹配.group(2))#捕获的步骤
    if 回合<1 or 回合>安全整数上限 or 步骤<1 or 步骤>安全整数上限:#外来读数入口
        失败('time-context turn and step must be positive safe integers')#回合步骤非法
    期望=准备位置(历史,失败)#历史推导的打开边界
    if 回合!=期望['turn'] or 步骤!=期望['step']:#读数自称的位置必须吻合
        失败('time-context reading names turn '+str(回合)+'/step '+str(步骤)+', expected turn '+str(期望['turn'])+'/step '+str(期望['step']))#位置不符
    来源=事件['data']['source']#消息来源
    if 来源['kind']!='plugin' or 来源['plugin']!=来源名:#必须保留本包所有权
        失败('time-context source must retain package ownership')#来源所有权丢失
    分段列表=来源['sections'] if 'sections' in 来源 else None#快照分段
    段值=分段列表[0] if isinstance(分段列表,list) and len(分段列表)>0 else None#第一段未知
    段=段值 if isinstance(段值,dict) else None#须为对象
    if (len(来源)!=4#来源只有kind/plugin/form/sections
        or 来源['form']!='snapshot'#必须是快照形态
        or not isinstance(分段列表,list)#sections必须是数组
        or len(分段列表)!=1#恰好一段
        or 段 is None#第一段必须是对象
        or len(段)!=2#只有name与text
        or 段['name']!=来源名#段名必须是本插件
        or 段['text']!=块文本):#段文本必须与正文完全相同
        失败('time-context source must carry only the exact snapshot text, not request authority')#不得夹带请求权威
    渲染浏览器上下文=匹配.group(4)#读数里的时区行
    浏览器上下文=推导浏览器时区上下文(请求消息列表(历史,回合))#由本回合用户消息重推导
    期望浏览器上下文=渲染浏览器时区上下文(浏览器上下文)#期望策略行
    if 渲染浏览器上下文!=期望浏览器上下文:#必须一致
        失败('time-context browser-zone text does not match current-turn user messages')#时区行与本回合消息不符
    基线=匹配.group(5)#经过时长基线种类
    if (步骤==1)!=(基线=='model-visible message'):#首步必须用模型可见消息基线
        失败('time-context step '+str(步骤)+' uses the wrong elapsed-time baseline '+json.dumps(基线,ensure_ascii=False,separators=(',',':'),allow_nan=False))#基线种类错误
    渲染=匹配.group(3)#渲染出的时间戳
    if 渲染 is None:#正则必有第三组
        失败('time-context reading omitted its rendered timestamp')#缺时间戳
        return#已失败
    try:
        渲染时间=解析渲染时间(渲染)#去掉时区括号再解析
    except ValueError:#格式写死后仍对不上
        失败('time-context rendered timestamp must parse and not postdate its durable event')#时间戳与事件时间不一致
        return#已失败
    事件时间=事件['time']#事件时间
    if (isinstance(事件时间,bool)#布尔不是时间
        or not isinstance(事件时间,int)#必须是整数
        or 事件时间<0 or 事件时间>安全整数上限#外来事件时间入口
        or 事件时间<渲染时间):#事件时间不得早于渲染时间戳
        失败('time-context rendered timestamp must parse and not postdate its durable event')#时间戳与事件时间不一致
    if 浏览器上下文['kind']=='resolved':#唯一浏览器时区时，时间戳必须按该时区重放
        try:
            期望时间戳=格式化时间戳(#重放
                渲染时间,#解析出的纪元毫秒
                创建时间戳格式化器(浏览器上下文['timeZone']),#该时区格式化器
                浏览器上下文['timeZone'],#括号标签，线协议原样
            )#格式化结束
        except (ValueError,OSError,KeyError) as 错误:#时区无法格式化
            失败('time-context browser zone cannot format its durable timestamp: '+str(错误))#格式化失败
            return#已失败
        if 渲染!=期望时间戳:#必须与按该时区重放的结果一致
            失败('time-context rendered timestamp does not match the unique browser zone')#时间戳与浏览器时区不符

def 校验会话(会话,失败):
    """校验一个会话里已经存在的、本包拥有的全部读数。"""
    事件列表=list(会话.events)#事件列表
    for 下标,事件 in enumerate(事件列表):#带下标扫描
        if 'data' not in 事件:#无载荷
            continue#跳过
        数据=事件['data']#载荷
        if not isinstance(数据,dict) or 'source' not in 数据:#无来源
            continue#跳过
        来源=数据['source']#来源
        if (事件['type']!='user/message'#非用户消息
            or 来源['kind']!='plugin'#非插件来源
            or 来源['plugin']!=来源名):#非本插件
            continue#跳过
        校验读数(事件列表[0:下标],事件,失败)#用该事件之前的历史校验

def 安装(上下文对象,失败):
    """为已加载与新追加的上下文读数安装校验。"""
    for 会话对象 in 上下文对象.sessions.list():#先校验现有会话
        校验会话(会话对象,失败)#校验
    def 会话已创建(会话,*其余):
        """新会话创建时校验。"""
        校验会话(会话,失败)#校验
    def 内部派发(_模式,事件名,参数,*其余):
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只看会话事件
            return#放过
        会话=参数[0]#会话
        事件=参数[1]#事件
        if 'data' not in 事件:#无载荷
            continue#跳过
        数据=事件['data']#载荷
        if not isinstance(数据,dict) or 'source' not in 数据:#无来源
            continue#跳过
        来源=数据['source']#来源
        if (事件['type']!='user/message'#非用户消息
            or 来源['kind']!='plugin'#非插件
            or 来源['plugin']!=来源名):#非本插件
            return#放过
        校验读数(会话.events,事件,失败)#追加时历史已含本事件，准备位置按此前边界计算
    上下文对象.监听('session/created',会话已创建,{'全局':True})#新会话也校验
    上下文对象.监听('internal/dispatch',内部派发,{'全局':True})#全局监听

def 应用(上下文对象):
    """注册时钟上下文不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#登记本包不变量

安装.inject=['sessions']#安装前需要sessions
应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出槽
