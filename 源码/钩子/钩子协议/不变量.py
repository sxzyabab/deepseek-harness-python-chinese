"""本包拥有的钩子调用与结果流不变量。"""
import json,math#方言诊断与有限数校验
from cordis.工具 import 已兑现#立刻兑现的拆除器
from scope import 弱身份表#按身份存取的弱表

包名='@deepseek-ai/dsh-hook-protocol'#本包名
名称='hook-protocol-invariant'#配套插件名
注入=['invariants']#依赖不变量服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 钩子键(数据):#组成关联键
    """一次调用与结果对共享的关联键。"""
    return str(取字段(数据,'turn'))+'\0'+str(取字段(数据,'point'))+'\0'+str(取字段(数据,'handlerId'))#NUL 拼接

def 校验钩子事件(踪迹,事件,失败):#校验一条事件
    """用已提交的待配对调用校验；有成对变迁则返回否则 None。"""
    种类=取字段(事件,'type')#事件类型
    if 种类!='hook/invoked' and 种类!='hook/result':#非本包事件
        return None#忽略
    if 取字段(踪迹,'openTurn') is None:#轮外追加则失败
        失败(种类+' appended outside any open turn')#失败
    数据=取字段(事件,'data')#载荷
    if 取字段(数据,'turn')!=取字段(踪迹,'openTurn'):#轮次必须一致
        失败(种类+' names turn '+str(取字段(数据,'turn'))+' but open turn is '+str(取字段(踪迹,'openTurn')))#不一致
    if 种类=='hook/invoked':#调用登记
        if len(取字段(数据,'point') or '')==0 or len(取字段(数据,'handlerId') or '')==0:#不得为空
            失败('hook/invoked point and handlerId must be non-empty')#空则失败
        方言=取字段(数据,'dialect')#方言
        if 方言!='claude-code' and 方言!='codex':#必须已知
            失败('hook/invoked carries unknown dialect '+json.dumps(方言,ensure_ascii=False))#未知
        return {'key':钩子键(数据),'delta':1}#+1
    键=钩子键(数据)#结果关联键
    待配对=取字段(踪迹,'pending')#待配对表
    if (待配对.get(键) or 0)==0:#缺调用
        失败('hook/result has no matching hook/invoked for '+json.dumps(取字段(数据,'handlerId'),ensure_ascii=False))#缺配对
    时长=取字段(数据,'durationMs')#时长
    if (not isinstance(时长,(int,float))) or (not math.isfinite(时长)) or 时长<0:#必须非负有限
        失败('hook/result durationMs must be a non-negative finite number')#非法
    return {'key':键,'delta':-1}#-1

def 应用钩子变迁(待配对,变迁):#应用到待配对集合
    """应用一次已提交的成对变迁。"""
    下一=(待配对.get(取字段(变迁,'key')) or 0)+取字段(变迁,'delta')#加减
    if 下一==0:#归零
        待配对.pop(取字段(变迁,'key'),None)#删键
    else:#否则
        待配对[取字段(变迁,'key')]=下一#写入

def 安装(上下文对象,失败):#安装成对检查
    """安装调用与结果成对检查。"""
    踪迹表=弱身份表()#会话跟踪
    暂存表=弱身份表()#预提交暂存
    def 播种(会话):#播种跟踪
        """从已提交事件播种。"""
        踪迹={'openTurn':None,'pending':{}}#空跟踪
        踪迹表.设(会话,踪迹)#登记
        for 事件 in 取字段(会话,'events') or []:#重放
            种类=取字段(事件,'type')#类型
            if 种类=='turn/start':#开始
                踪迹['openTurn']=取字段(取字段(事件,'data'),'turn')#打开
            elif 种类=='turn/end':#结束
                踪迹['openTurn']=None#清空
            变迁=校验钩子事件(踪迹,事件,失败)#校验
            if 变迁 is not None:#有变迁
                应用钩子变迁(踪迹['pending'],变迁)#应用
        return 踪迹#跟踪
    def 取踪迹(会话):#取或播种
        """取已有否则播种。"""
        已有=踪迹表.取(会话)#已有
        if 已有 is None:#缺
            return 播种(会话)#播种
        return 已有#已有
    for 会话 in 上下文对象.sessions.list():#现有会话
        播种(会话)#播种
    def 会话已创建(会话,*其余):#创建时播种
        """创建时播种。"""
        播种(会话)#播种
    def 已提交事件(会话,事件,*其余):#提交后应用
        """提交后应用变迁。"""
        踪迹=取踪迹(会话)#跟踪
        种类=取字段(事件,'type')#类型
        if 种类=='turn/start':#开始
            踪迹['openTurn']=取字段(取字段(事件,'data'),'turn')#打开
            return#结束
        if 种类=='turn/end':#结束
            踪迹['openTurn']=None#清空
            return#结束
        if 种类!='hook/invoked' and 种类!='hook/result':#非本包
            return#忽略
        候选=暂存表.取(事件)#暂存
        if 候选 is None or 取字段(候选,'session') is not 会话:#无预提交
            return 失败('hook event published without pre-commit validation')#失败
        暂存表.设(事件,None)#清暂存
        应用钩子变迁(踪迹['pending'],取字段(候选,'transition'))#应用
    def 内部派发(_模式,事件名,参数,*其余):#预提交
        """派发前校验。"""
        if 事件名!='session/event':#只拦会话事件
            return#放过
        会话=参数[0]#会话
        事件=参数[1]#事件
        变迁=校验钩子事件(取踪迹(会话),事件,失败)#校验
        if 变迁 is not None:#有变迁
            暂存表.设(事件,{'session':会话,'transition':变迁})#暂存
    上下文对象.on('session/created',会话已创建,{'global':True})#创建
    上下文对象.on('session/event',已提交事件,{'global':True})#提交
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#派发

安装.inject=['sessions']#还要 sessions

def 应用(上下文对象):#登记配套
    """登记本包不变量配套。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记

apply=应用#Cordis入口
