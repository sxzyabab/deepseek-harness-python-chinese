"""包内审批审计流不变量。"""
import json#诊断里序列化未知词表值
from ...依赖 import cordis#外部依赖胶水
已兑现=cordis.工具.已兑现#立刻兑现的拆除器
from ..作用域 import 弱身份表#按身份存取的弱表

包名='@deepseek-ai/dsh-user-approval'#本包名，用于登记所有权
名称='user-approval-invariant'#配套插件名
注入=['invariants']#依赖不变量服务
name=名称#Cordis 插件名
inject=注入#Cordis 依赖声明
审批策略表=('ask','never')#与主包 APPROVAL_POLICIES 同词表；本地复述以免加载服务模块
审批结果表=('allowed-once','rejected','cancelled','unavailable')#封闭结果表

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 校验审批事件(踪迹,事件,失败):#校验单条审批事件
    """对照已提交的未匹配提问校验一条审批事件。返回可应用的转移或 None（无关）。"""
    种类=取字段(事件,'type')#事件类型
    数据=取字段(事件,'data')#事件载荷
    if 种类=='approval/asked':#提问事件
        if 取字段(踪迹,'openTurn') is None:#必须在打开回合内
            失败('approval/asked appended outside any open turn')#回合外提问
        if len(取字段(数据,'toolName') or '')==0:#工具名不得空
            失败('approval/asked toolName must be non-empty')#空工具名
        配对=取字段(数据,'id')#请求 id
        if 配对 in 取字段(踪迹,'pending'):#id 不得重复打开
            失败('approval/asked repeated open id '+json.dumps(配对,ensure_ascii=False))#重复打开
        return {'kind':'asked','id':配对}#接受提问转移
    if 种类=='approval/decided':#裁决事件
        if 取字段(踪迹,'openTurn') is None:#必须在打开回合内
            失败('approval/decided appended outside any open turn')#回合外裁决
        配对=取字段(数据,'id')#请求 id
        if 配对 not in 取字段(踪迹,'pending'):#必须先有提问
            失败('approval/decided has no matching approval/asked for id '+json.dumps(配对,ensure_ascii=False))#孤立裁决
        结果=取字段(数据,'outcome')#封闭结果
        if 结果 not in 审批结果表:#结果必须在封闭表内
            失败('approval/decided carries unknown outcome '+json.dumps(结果,ensure_ascii=False))#未知结果
        return {'kind':'decided','id':配对}#接受裁决转移
    if 种类=='approval/policy':#策略事件也要封闭词表
        策略=取字段(数据,'policy')#策略值
        if 策略 not in 审批策略表:#未知策略
            失败('approval/policy carries unknown policy '+json.dumps(策略,ensure_ascii=False))#未知策略
    return None#非配对事件

def 应用审批转移(待决,转移):#更新未匹配集合
    """应用一次已接受的审批配对转移。"""
    if 取字段(转移,'kind')=='asked':#提问则加入
        待决.add(取字段(转移,'id'))#加入
    else:#裁决则移除
        待决.discard(取字段(转移,'id'))#移除

def 安装(上下文对象,失败):#安装审计校验
    """安装审计配对与封闭词表检查。事件所有者把预提交暂存留在本地，使其词表永不搬进中央助手。"""
    踪迹表=弱身份表()#每会话跟踪
    暂存表=弱身份表()#预提交暂存
    def 播种(会话):#从已提交事件播种跟踪
        """从已提交事件播种跟踪。"""
        踪迹={'openTurn':None,'pending':set()}#空跟踪
        踪迹表.设(会话,踪迹)#挂到会话
        for 事件 in 取字段(会话,'events') or []:#回放历史
            种类=取字段(事件,'type')#事件类型
            if 种类=='turn/start':#打开回合
                踪迹['openTurn']=取字段(取字段(事件,'data'),'turn')#记下回合号
            elif 种类=='turn/end':#关闭回合
                踪迹['openTurn']=None#清打开回合
            转移=校验审批事件(踪迹,事件,失败)#校验审批事件
            if 转移 is not None:#已接受转移
                应用审批转移(踪迹['pending'],转移)#应用已接受转移
        return 踪迹#返回播种结果
    def 取踪迹(会话):#取出或播种
        """取出或播种。"""
        已有=踪迹表.取(会话)#已有
        if 已有 is None:#缺
            return 播种(会话)#播种
        return 已有#已有
    for 会话 in 上下文对象.sessions.list():#扫描已加载会话
        播种(会话)#播种
    def 会话已创建(会话,*其余):#新会话立即播种
        """新会话立即播种。"""
        播种(会话)#播种
    def 已提交事件(会话,事件,*其余):#提交后应用转移
        """提交后应用转移。"""
        踪迹=取踪迹(会话)#本会话跟踪
        种类=取字段(事件,'type')#事件类型
        if 种类=='turn/start':#打开回合
            踪迹['openTurn']=取字段(取字段(事件,'data'),'turn')#记下回合号
            return#回合事件到此
        if 种类=='turn/end':#关闭回合
            踪迹['openTurn']=None#清打开回合
            return#回合事件到此
        if 种类!='approval/asked' and 种类!='approval/decided':#只应用配对事件
            return#忽略
        候选=暂存表.取(事件)#取预提交暂存
        if 候选 is None or 取字段(候选,'session') is not 会话:#缺少预提交
            return 失败('approval audit event published without pre-commit validation')#缺少预提交
        暂存表.设(事件,None)#清暂存
        应用审批转移(踪迹['pending'],取字段(候选,'transition'))#提交后应用
    def 内部派发(_模式,事件名,参数,*其余):#提交前校验
        """派发前校验。"""
        if 事件名!='session/event':#只关心会话事件
            return#放过
        会话=参数[0]#拆出会话
        事件=参数[1]#拆出事件
        转移=校验审批事件(取踪迹(会话),事件,失败)#预提交校验
        if 转移 is not None:#已接受转移
            暂存表.设(事件,{'session':会话,'transition':转移})#暂存已接受转移
    上下文对象.on('session/created',会话已创建,{'global':True})#新会话立即播种
    上下文对象.on('session/event',已提交事件,{'global':True})#提交后应用
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#派发前校验

安装.inject=['sessions']#安装器还依赖 sessions

def 应用(上下文对象):#对外导出配套入口
    """登记审批不变量配套，返回安装成功后已登记项的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#向不变量服务登记安装器

apply=应用#Cordis 插件入口
