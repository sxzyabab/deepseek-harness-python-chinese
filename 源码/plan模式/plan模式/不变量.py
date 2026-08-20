"""@deepseek-ai/dsh-plan-mode 的本包拥有不变量配套：校验持久计划模式状态。"""
import json#JSON 片段
from cordis.工具 import 已兑现#立刻兑现的拆除器

包名='@deepseek-ai/dsh-plan-mode'#本包的不变量所有权名
名称='plan-mode-invariant'#配套不变量插件名
注入=['invariants']#依赖invariants服务
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

def 校验事件(事件,失败):#校验单条 plan/mode
    """在一条 `plan/mode` 事件进入持久日志之前校验它。`plan/mode` 是独立整值事件：空闲选择在回合之间提交，回合中选择在步骤边界提交，因此不存在回合包围关系——只能检查载荷形状。"""
    if 取字段(事件,'type')!='plan/mode':#非本事件则跳过
        return#放过
    激活=取字段(取字段(事件,'data'),'active')#取出 active，形状未钉死
    if not isinstance(激活,bool):#必须是布尔
        失败('plan/mode carries invalid active state '+json.dumps(激活,ensure_ascii=False)+'; expected a boolean')#报告非法 active

def 安装(上下文对象,失败):#安装已加载与新追加校验
    """为已加载和新追加的计划模式状态安装校验。"""
    def 种子(会话对象):#回放该会话已有事件
        """回放该会话已有事件。"""
        for 事件 in 会话对象.events:#逐条
            校验事件(事件,失败)#校验
    for 会话对象 in 上下文对象.sessions.list():#对当前所有会话做种子校验
        种子(会话对象)#种子
    def 会话已创建(会话对象,*其余):#新会话创建时再种子
        """新会话创建时再种子。"""
        种子(会话对象)#种子
    上下文对象.on('session/created',会话已创建,{'global':True})#全局监听
    def 内部派发(_模式,事件名,参数,*其余):#拦截内部派发以校验新追加事件
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只关心会话事件
            return#放过
        事件=参数[1]#第二参是刚追加的事件
        校验事件(事件,失败)#校验新事件
    上下文对象.on('internal/dispatch',内部派发,{'global':True})#全局监听，不随会话作用域拆除

安装.inject=['sessions']#安装器还要 sessions 才能列会话与监听

def 应用(上下文对象):#注册本包不变量配套
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 已兑现(上下文对象.invariants.register(包名,安装))#登记并包成立即兑现的承诺

apply=应用#Cordis插件入口
