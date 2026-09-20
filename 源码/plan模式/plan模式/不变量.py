"""@deepseek-ai/dsh-plan-mode 的本包拥有不变量配套：校验持久计划模式状态。"""
import json#JSON 片段
包名='@deepseek-ai/dsh-plan-mode'#本包的不变量所有权名
名称='plan-mode-invariant'#配套不变量插件名
依赖=['invariants']

def 校验事件(事件,失败):
    """在一条 `plan/mode` 事件进入持久日志之前校验它。`plan/mode` 是独立整值事件：空闲选择在回合之间提交，回合中选择在步骤边界提交，因此不存在回合包围关系——只能检查载荷形状。事件是 dict。"""
    if 事件['type']!='plan/mode':#非本事件则跳过
        return#放过
    载荷=事件['data']#事件载荷
    激活=载荷['active'] if 'active' in 载荷 else None#取出 active
    if not isinstance(激活,bool):#必须是布尔
        失败('plan/mode carries invalid active state '+json.dumps(激活,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'; expected a boolean')#报告非法 active

def 安装(上下文,失败):
    """为已加载和新追加的计划模式状态安装校验。"""
    def 种子(会话):
        """回放该会话已有事件。"""
        for 事件 in 会话.events:#逐条
            校验事件(事件,失败)#校验
    for 会话 in 上下文.sessions.列出():#对当前所有会话做种子校验
        种子(会话)#种子
    def 会话已创建(会话,*其余):
        """新会话创建时再种子。"""
        种子(会话)#种子
    上下文.监听('session/created',会话已创建,{'全局':True})#全局监听
    def 内部派发(_模式,事件名,参数,*其余):
        """提交前检查 session/event。"""
        if 事件名!='session/event':#只关心会话事件
            return#放过
        事件=参数[1]#第二参是刚追加的事件
        校验事件(事件,失败)#校验新事件
    上下文.监听('internal/dispatch',内部派发,{'全局':True})#全局监听，不随会话作用域拆除

安装.inject=['sessions']#安装器还要 sessions 才能列会话与监听

def 应用(上下文):
    """注册本包的不变量配套，返回安装成功后已登记贡献的拆除器。"""
    return 上下文.invariants.register(包名,安装)#登记

__all__=['包名','名称','依赖','安装','应用']
name=名称
inject=依赖
apply=应用#Cordis 插件入口
default=应用#Cordis 默认导出
