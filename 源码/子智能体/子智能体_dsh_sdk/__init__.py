import os#路径
from ...依赖.schemastery import 字典字段,字符串字段,列表字段,数字字段#配置
from ..子智能体 import 无启动能力,断言可用工作目录#无能力广告与目录校验
from ..子智能体.异常 import 子智能体错误#缝内失败
from .运行 import 启动sdk运行,默认关闭超时毫秒,默认处置eof宽限毫秒,默认处置宽限毫秒#运行

名称='subagent-dsh-sdk'#Cordis 插件名
依赖=['subagents']#依赖
配置=字典字段(字典结构={
    'providerName':字符串字段(默认值='dsh-sdk'),
    'profile':字符串字段(默认值='sdk'),
    'patches':列表字段(字符串字段(),默认值=[]),
    'dshHome':字符串字段(),#必填
    'cwd':字符串字段(),
    'provider':字符串字段(默认值='deepseek-official'),
    'model':字符串字段(默认值='deepseek-v4-flash'),
    'maxTokens':数字字段(),
    'env':字典字段(键值结构=(字符串字段(),字符串字段()),默认值={}),
    'shutdownTimeoutMs':数字字段(默认值=默认关闭超时毫秒),
    'disposeEofGraceMs':数字字段(默认值=默认处置eof宽限毫秒),
    'disposeGraceMs':数字字段(默认值=默认处置宽限毫秒),
})#配置

__all__=['名称','依赖','配置','应用']#公开面

class dshSdk提供方:
    '进程外 SDK 子体；不继承父对话'
    def __init__(自身,名,规格):
        '记下提供方名、能力与运行规格。规格为 dict'
        自身.名称=名#名
        能力=dict(无启动能力)#其余启动能力关闭
        能力['agentOptions']=True#只支持路由选项
        自身.能力=能力#能力
        自身.继承父上下文=False#契约
        自身.agentRouteDefaults={#实例默认路由
            'provider':规格['provider'] if 'provider' in 规格 else 'deepseek-official',
            'model':规格['model'] if 'model' in 规格 else 'deepseek-v4-flash',
        }#路由结束
        自身._规格=规格#规格

    def 启动(自身,请求):
        '启动 SDK 一次性跑。工作目录来自服务；推理力度按请求覆盖实例默认'
        规格=dict(自身._规格)#拷贝
        规格['cwd']=断言可用工作目录('subagent-dsh-sdk','child cwd',请求['cwd'])#绝对可进入目录
        选项=请求['agentOptions'] if 'agentOptions' in 请求 and isinstance(请求['agentOptions'],dict) else {}#请求路由
        if 'provider' in 选项 and 选项['provider'] is not None:#覆盖提供方
            规格['provider']=选项['provider']#请求优先
        if 'model' in 选项 and 选项['model'] is not None:#覆盖模型
            规格['model']=选项['model']#请求优先
        if 'reasoningEffort' in 选项 and 选项['reasoningEffort'] is not None:#请求点了力度
            规格['reasoningEffort']=选项['reasoningEffort']#合并
        if 'maxTokens' in 选项 and 选项['maxTokens'] is not None:#覆盖 token 上限
            规格['maxTokens']=选项['maxTokens']#请求优先
        return 启动sdk运行(请求,规格)#跑

def 应用(上下文,配置值):
    '加载 SDK 提供方。配置为 dict'
    家=str(配置值['dshHome'] if 'dshHome' in 配置值 else '').strip()#DSH_HOME
    if len(家)==0:#空
        raise 子智能体错误('subagent-dsh-sdk: dshHome is required','INVALID_CONFIG')#拒绝
    if not os.path.isabs(家):#非绝对
        raise 子智能体错误('subagent-dsh-sdk: dshHome must be absolute','INVALID_CONFIG')#拒绝
    名=配置值['providerName'] if 'providerName' in 配置值 else 'dsh-sdk'#名
    规格=dict(配置值)#规格
    规格['dshHome']=家#绝对家目录
    上下文.subagents.登记提供方(dshSdk提供方(名,规格))#登记

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=应用#框架槽
