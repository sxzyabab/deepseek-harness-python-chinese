"""进程内 fork 子智能体后端（对齐 upstream subagent-fork-in-process）。"""
from ...依赖.schemastery import 字典字段,字符串字段#配置
from ..子智能体_in_process_driver import 启动进程内跑#共享驱动
名称='subagent-fork-in-process'#Cordis 插件名
注入=['subagents']#依赖
配置=字典字段({'providerName':字符串字段(默认值='fork')})#配置
__all__=['名称','注入','配置','应用','默认']#公开面

def 取字段(对象,键,缺省=None):#读字段
    if 对象 is None:return 缺省#空
    if isinstance(对象,dict):return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

def 已完成回合前缀(父):#completedTurnPrefix
    事件们=父.session.events#日志
    最后结束=None#最后 turn/end
    for 索引 in range(len(事件们)-1,-1,-1):#倒扫
        if 取字段(事件们[索引],'type')=='turn/end':#命中
            最后结束=事件们[索引]#记下
            break#停
    if 最后结束 is None:return []#无完成回合
    return 事件们[:取字段(最后结束,'seq')+1]#前缀

class 进程内分叉提供方:#ForkInProcessProvider
    """用父已完成回合前缀种子化子体。"""
    def __init__(自身,名):#构造
        自身.名称=名#中文名
        自身.name=名#Cordis 名
        自身.能力={'agentOptions':True,'outputSchema':True,'depthLimit':True,'toolFilter':True,'persona':True}#能力
        自身.capabilities=自身.能力#Cordis 槽
        自身.继承父上下文=True#契约
        自身.inheritsParentContext=True#Cordis 槽
    def 启动(自身,请求):#start
        种子=已完成回合前缀(取字段(请求,'parent'))#种子
        选项={} if len(种子)==0 else {'seed':种子}#选项
        return 启动进程内跑(请求,选项)#启动
    start=启动#Cordis 槽
    def 准备可续跑(自身,请求):#prepareContinuable
        种子=已完成回合前缀(取字段(请求,'parent'))#种子
        return {} if len(种子)==0 else {'seed':种子}#规格
    prepareContinuable=准备可续跑#Cordis 槽

def 应用(上下文,配置值):#加载
    名=配置值.get('providerName','fork')#提供方名
    上下文.subagents.登记提供方(进程内分叉提供方(名))#登记

apply=应用#Cordis 插件入口
default=应用#默认
默认=应用#中文默认
