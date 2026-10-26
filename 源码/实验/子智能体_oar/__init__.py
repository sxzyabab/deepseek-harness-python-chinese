'具名的一次性子智能体提供方，背后是 OAR 的默认运行时注册表'
from ...依赖.schemastery import 字符串字段,数字字段,列表字段,字典字段,复合类型字段,常量字段
from ...子智能体.子智能体 import 无启动能力,断言正有限
from ...工具.超时 import 定时器延迟上限毫秒
from . import 环境,运行
from .运行 import 启动运行,运行规格,要求默认运行时

__all__=['名称','依赖','配置','应用','环境','运行']

名称='experimental-subagent-oar'
依赖=['subagents']
默认提供方名='oar'

运行时字段=字符串字段(最小长度=1)
名称字段=字符串字段(最小长度=1)
环境字段=字典字段(键值结构=(字符串字段(),复合类型字段(字符串字段(),常量字段(None))))
参数字段=列表字段(字符串字段())
超时字段=数字字段(最小=1,最大=定时器延迟上限毫秒)

def 归一配置(数据):
    '补上提供方名、环境和启动参数的默认值'
    if 数据 is None:
        数据={}
    if not isinstance(数据,dict):
        raise TypeError('subagent-oar config must be an object')
    if 'runtime' not in 数据:
        raise TypeError('subagent-oar: runtime is required')
    运行时字段.校验数据(数据['runtime'])
    提供方名=默认提供方名 if 'providerName' not in 数据 or 数据['providerName'] is None else 数据['providerName']
    名称字段.校验数据(提供方名)
    模型=数据['model'] if 'model' in 数据 else None
    if 模型 is not None:
        名称字段.校验数据(模型)
    力度=数据['effort'] if 'effort' in 数据 else None
    if 力度 is not None:
        名称字段.校验数据(力度)
    环境=数据['env'] if 'env' in 数据 and 数据['env'] is not None else {}
    环境字段.校验数据(环境)
    启动参数=数据['launchArgs'] if 'launchArgs' in 数据 and 数据['launchArgs'] is not None else []
    参数字段.校验数据(启动参数)
    超时毫秒=数据['timeoutMs'] if 'timeoutMs' in 数据 else None
    if 超时毫秒 is not None:
        超时字段.校验数据(超时毫秒)
    return {
        'runtime':数据['runtime'],
        'providerName':提供方名,
        'model':模型,
        'effort':力度,
        'env':环境,
        'launchArgs':list(启动参数),
        'timeoutMs':超时毫秒,
    }

class 配置模式:
    '一个提供方实例的原生运行时选择和部署设置'
    def 校验数据(自身,数据=None):
        '加载前归一化。未知运行时要等到应用时才失败'
        return 归一配置(数据)

配置=配置模式()

class oar提供方:
    '不继承父对话的一次性 OAR 提供方'
    def __init__(自身,名,规格):
        '记下注册名、无启动能力和运行规格'
        自身.名称=名
        自身.能力=dict(无启动能力)
        自身.继承父上下文=False
        自身._规格=规格

    def 启动(自身,请求):
        '打开一次原生会话。请求里的工作目录已经由服务解析'
        return 启动运行(请求,自身._规格)

def 应用(上下文,配置值):
    '用 OAR 默认注册表里的一个运行时登记提供方'
    已解析=配置值 if isinstance(配置值,dict) and 'runtime' in 配置值 else 归一配置(配置值)
    运行时=要求默认运行时(已解析['runtime'])
    超时毫秒=已解析['timeoutMs']
    提供方名=已解析['providerName']
    if 超时毫秒 is not None:
        断言正有限('subagent-oar','timeoutMs',超时毫秒)
        if 超时毫秒>定时器延迟上限毫秒:
            raise ValueError('subagent-oar: timeoutMs must be no greater than '+str(定时器延迟上限毫秒))
    def 出错(错误,停止原因):
        '只把安全摘要写进日志。原生原因留在错误对象上'
        if 停止原因!='error':
            return
        上下文.日志.警告('subagent-oar "%s": %s',提供方名,错误)
    规格=运行规格(
        运行时,
        已解析['env'],
        已解析['launchArgs'],
        None if 已解析['model'] is None else 已解析['model'],
        None if 已解析['effort'] is None else 已解析['effort'],
        超时毫秒,
        出错,
    )
    上下文.subagents.登记提供方(oar提供方(提供方名,规格))

name=名称
inject=依赖
Config=配置
apply=应用
