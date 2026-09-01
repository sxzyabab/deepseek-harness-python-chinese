"""Codex 子智能体后端（对齐 upstream subagent-codex）。"""
from ...依赖 import schemastery#配置
from .运行 import 启动codex跑,默认处置宽限毫秒#运行
名称='subagent-codex'#Cordis 插件名
注入=['subagents','subprocess']#依赖
配置=schemastery.对象字段({
    'providerName':schemastery.字符串字段(默认值='codex'),
    'permissionMode':schemastery.字符串字段(默认值='never'),
    'disposeGraceMs':schemastery.数字字段(默认值=默认处置宽限毫秒),
})#配置
__all__=['名称','注入','配置','应用','默认']#公开面

class codex提供方:#CodexProvider
    def __init__(自身,名,规格):#构造
        自身.名称=名;自身.name=名#名
        自身.能力={};自身.capabilities=自身.能力#无启动能力
        自身.继承父上下文=False;自身.inheritsParentContext=False#契约
        自身._规格=规格#规格
    def 启动(自身,请求):return 启动codex跑(请求,自身._规格)#跑
    start=启动#槽

def 应用(上下文,配置值):#加载
    名=配置值.get('providerName','codex')#名
    规格={'permissionMode':配置值.get('permissionMode','never'),'disposeGraceMs':配置值.get('disposeGraceMs',默认处置宽限毫秒),'subprocess':上下文.subprocess}#规格
    上下文.subagents.登记提供方(codex提供方(名,规格))#登记

apply=应用;default=应用;默认=应用#导出
