"""本包拥有的钩子调用与结果流不变量。"""
import json#方言诊断
from ...内核.作用域 import 弱身份表#按身份存取的弱表

包名='@deepseek-ai/dsh-hook-protocol'#本包名
名称='hook-protocol-invariant'#配套插件名
注入=['invariants']#依赖不变量服务

def 钩子键(数据):
    """一次调用与结果对共享的关联键。数据是事件载荷 dict。"""
    return str(数据['turn'])+'\0'+str(数据['point'])+'\0'+str(数据['handlerId'])#NUL 拼接

def 校验钩子事件(踪迹,事件,失败):
    """用已提交的待配对调用校验；有成对变迁则返回否则 None。事件是会话事件 dict。"""
    种类=事件['type']#事件类型
    if 种类!='hook/invoked' and 种类!='hook/result':#非本包事件
        return None#忽略
    if 踪迹['openTurn'] is None:#轮外追加则失败
        失败(种类+' appended outside any open turn')#失败
    数据=事件['data']#载荷
    if 数据['turn']!=踪迹['openTurn']:#轮次必须一致
        失败(种类+' names turn '+str(数据['turn'])+' but open turn is '+str(踪迹['openTurn']))#不一致
    if 种类=='hook/invoked':#调用登记
        点=数据['point'] if 'point' in 数据 else ''#钩子点
        处理器=数据['handlerId'] if 'handlerId' in 数据 else ''#处理器 id
        if len(点)==0 or len(处理器)==0:#不得为空
            失败('hook/invoked point and handlerId must be non-empty')#空则失败
        方言=数据['dialect'] if 'dialect' in 数据 else None#方言
        if 方言!='claude-code' and 方言!='codex':#必须已知
            失败('hook/invoked carries unknown dialect '+json.dumps(方言,ensure_ascii=False,separators=(',',':'),allow_nan=False))#未知
        return {'key':钩子键(数据),'delta':1}#+1
    键=钩子键(数据)#结果关联键
    待配对=踪迹['pending']#待配对表
    已有=待配对[键] if 键 in 待配对 else 0#当前计数
    if 已有==0:#缺调用
        失败('hook/result has no matching hook/invoked for '+json.dumps(数据['handlerId'],ensure_ascii=False,separators=(',',':'),allow_nan=False))#缺配对
    时长=数据['durationMs'] if 'durationMs' in 数据 else None#时长
    if isinstance(时长,bool) or (not isinstance(时长,int)) or 时长<0:#必须非负整数；先排除布尔
        失败('hook/result durationMs must be a non-negative finite number')#非法
    return {'key':键,'delta':-1}#-1

def 应用钩子变迁(待配对,变迁):
    """应用一次已提交的成对变迁。待配对与变迁都是 dict。"""
    键=变迁['key']#关联键
    下一=(待配对[键] if 键 in 待配对 else 0)+变迁['delta']#加减
    if 下一==0:#归零
        待配对.pop(键,None)#删键
    else:
        待配对[键]=下一#写入

def 安装(上下文对象,失败):
    """安装调用与结果成对检查。"""
    踪迹表=弱身份表()#会话跟踪
    暂存表=弱身份表()#预提交暂存
    def 播种(会话):
        """从已提交事件播种。会话是对象。"""
        踪迹={'openTurn':None,'pending':{}}#空跟踪
        踪迹表.设(会话,踪迹)#登记
        for 事件 in 会话.events:#重放
            种类=事件['type']#类型
            if 种类=='turn/start':#开始
                踪迹['openTurn']=事件['data']['turn']#打开
            elif 种类=='turn/end':#结束
                踪迹['openTurn']=None#清空
            变迁=校验钩子事件(踪迹,事件,失败)#校验
            if 变迁 is not None:#有变迁
                应用钩子变迁(踪迹['pending'],变迁)#应用
        return 踪迹#跟踪
    def 取踪迹(会话):
        """取已有否则播种。"""
        已有=踪迹表.取(会话)#已有
        if 已有 is None:#缺
            return 播种(会话)#播种
        return 已有#已有
    for 会话 in 上下文对象.sessions.列出():#现有会话
        播种(会话)#播种
    def 会话已创建(会话,*位置参数):
        """创建时播种。"""
        播种(会话)#播种
    def 已提交事件(会话,事件,*位置参数):
        """提交后应用变迁。"""
        踪迹=取踪迹(会话)#跟踪
        种类=事件['type']#类型
        if 种类=='turn/start':#开始
            踪迹['openTurn']=事件['data']['turn']#打开
            return#结束
        if 种类=='turn/end':#结束
            踪迹['openTurn']=None#清空
            return#结束
        if 种类!='hook/invoked' and 种类!='hook/result':#非本包
            return#忽略
        候选=暂存表.取(事件)#暂存
        if 候选 is None or 候选['session'] is not 会话:#无预提交
            return 失败('hook event published without pre-commit validation')#失败
        暂存表.设(事件,None)#清暂存
        应用钩子变迁(踪迹['pending'],候选['transition'])#应用
    def 内部派发(_模式,事件名,参数,*位置参数):
        """派发前校验。"""
        if 事件名!='session/event':#只拦会话事件
            return#放过
        会话=参数[0]#会话
        事件=参数[1]#事件
        变迁=校验钩子事件(取踪迹(会话),事件,失败)#校验
        if 变迁 is not None:#有变迁
            暂存表.设(事件,{'session':会话,'transition':变迁})#暂存
    上下文对象.监听('session/created',会话已创建,{'全局':True})#创建
    上下文对象.监听('session/event',已提交事件,{'全局':True})#提交
    上下文对象.监听('internal/dispatch',内部派发,{'全局':True})#派发

安装.inject=['sessions']#还要 sessions

def 应用(上下文对象):
    """登记本包不变量配套。"""
    return 上下文对象.invariants.register(包名,安装)#登记

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
apply=应用#Cordis插件入口
default=应用#Cordis默认导出
