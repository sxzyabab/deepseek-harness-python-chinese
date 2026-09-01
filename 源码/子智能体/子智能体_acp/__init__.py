"""进程外 ACP 子智能体后端（对齐 upstream subagent-acp）。"""
from ...依赖 import schemastery#配置
from .运行 import 启动acp跑,默认处置eof宽限毫秒,默认处置宽限毫秒#运行
名称='subagent-acp'#Cordis 插件名
注入=['subagents','subprocess']#依赖
配置=schemastery.对象字段({
    'providerName':schemastery.字符串字段(默认值='acp'),
    'command':schemastery.字符串字段(),#可执行文件必填
    'args':schemastery.列表字段(schemastery.字符串字段(),默认值=[]),
    'cwd':schemastery.字符串字段(),
    'permission':schemastery.字符串字段(默认值='reject'),
    'env':schemastery.字典字段(schemastery.字符串字段(),默认值={}),
    'disposeEofGraceMs':schemastery.数字字段(默认值=默认处置eof宽限毫秒),
    'disposeGraceMs':schemastery.数字字段(默认值=默认处置宽限毫秒),
})#配置
__all__=['名称','注入','配置','应用','默认']#公开面

class acp提供方:#AcpProvider
    """进程外 ACP 子体；不广告父侧启动能力。"""
    def __init__(自身,名,规格):#构造
        自身.名称=名#名
        自身.name=名#Cordis
        自身.能力={}#无启动能力
        自身.capabilities=自身.能力#槽
        自身.继承父上下文=False#契约
        自身.inheritsParentContext=False#槽
        自身._规格=规格#运行规格
    def 启动(自身,请求):#start
        return 启动acp跑(请求,自身._规格)#进程外跑
    start=启动#槽

def 应用(上下文,配置值):#加载
    if len(str(配置值.get('command','')).strip())==0:#无命令
        raise Exception('subagent-acp: command is required')#拒绝
    名=配置值.get('providerName','acp')#名
    规格={
        'command':配置值['command'],'args':配置值.get('args',[]),
        'cwd':配置值.get('cwd'),'permission':配置值.get('permission','reject'),
        'env':配置值.get('env',{}),
        'disposeEofGraceMs':配置值.get('disposeEofGraceMs',默认处置eof宽限毫秒),
        'disposeGraceMs':配置值.get('disposeGraceMs',默认处置宽限毫秒),
        'subprocess':上下文.subprocess,#子进程缝
    }#规格
    上下文.subagents.登记提供方(acp提供方(名,规格))#登记

apply=应用#Cordis 插件入口
default=应用#默认
默认=应用#中文默认
