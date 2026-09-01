"""DSH SDK 子智能体后端（对齐 upstream subagent-dsh-sdk）。"""
import os#路径
from ...依赖 import schemastery#配置
from .运行 import 启动sdk跑,默认关闭超时毫秒,默认处置eof宽限毫秒,默认处置宽限毫秒#运行
名称='subagent-dsh-sdk'#Cordis 插件名
注入=['subagents']#依赖
配置=schemastery.对象字段({
    'providerName':schemastery.字符串字段(默认值='dsh-sdk'),
    'profile':schemastery.字符串字段(默认值='sdk'),
    'patches':schemastery.列表字段(schemastery.字符串字段(),默认值=[]),
    'dshHome':schemastery.字符串字段(),#必填
    'cwd':schemastery.字符串字段(),
    'provider':schemastery.字符串字段(默认值='deepseek-official'),
    'model':schemastery.字符串字段(默认值='deepseek-v4-flash'),
    'maxTokens':schemastery.数字字段(),
    'env':schemastery.字典字段(schemastery.字符串字段(),默认值={}),
    'shutdownTimeoutMs':schemastery.数字字段(默认值=默认关闭超时毫秒),
    'disposeEofGraceMs':schemastery.数字字段(默认值=默认处置eof宽限毫秒),
    'disposeGraceMs':schemastery.数字字段(默认值=默认处置宽限毫秒),
})#配置
__all__=['名称','注入','配置','应用','默认']#公开面

class dshSdk提供方:#SdkProvider
    def __init__(自身,名,规格):#构造
        自身.名称=名;自身.name=名#名
        自身.能力={'agentOptions':True};自身.capabilities=自身.能力#部分能力
        自身.继承父上下文=False;自身.inheritsParentContext=False#契约
        自身._规格=规格#规格
    def 启动(自身,请求):return 启动sdk跑(请求,自身._规格)#跑
    start=启动#槽

def 应用(上下文,配置值):#加载
    家=str(配置值.get('dshHome','')).strip()#DSH_HOME
    if len(家)==0:#空
        raise Exception('subagent-dsh-sdk: dshHome is required')#拒绝
    if not os.path.isabs(家):#非绝对
        raise Exception('subagent-dsh-sdk: dshHome must be absolute')#拒绝
    名=配置值.get('providerName','dsh-sdk')#名
    规格=dict(配置值);规格['dshHome']=家#规格
    上下文.subagents.登记提供方(dshSdk提供方(名,规格))#登记

apply=应用;default=应用;默认=应用#导出
