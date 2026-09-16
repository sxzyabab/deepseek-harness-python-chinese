"""一次性应用的命令行提供方：解析任务位置参数、`--session-id`、`--json` 与 `--help`。"""
from ...启动.命令行 import 命令,解析命令行,命令错误#命令行解析
from .json流 import 约束json行#JSON 错误事件
from .启动内部 import 内部流#进程事实

__all__=['名称','注入','无头启动服务键','应用']#仅中文公开名

名称='headless-startup'#插件名
注入=['cmdlineArgs']#依赖命令行参数
无头启动服务键='headlessStartup'#启动服务键

def 无头命令():
    """本应用的命令：任务位置参数、选项与帮助文本。"""
    return (命令()#新程序
        .name('dsh --profile headless')#程序名
        .description('Answer one task and exit; the answer goes to stdout and diagnostics to stderr.')#描述
        .helpOption('-h, --help','show this help')#帮助选项
        .option('--json','write newline-delimited run events to stdout instead of the final message')#JSON 流
        .option('--session-id <id>','adopt the persisted Session with this id; an unknown id is an error')#会话
        .argument('[task...]','the task text; multiple words are joined by spaces, and `-` reads stdin')#任务
        .addHelpText('after','''
Examples:
  dsh --profile headless "run the tests"          answer one task and exit
  echo "run the tests" | dsh --profile headless   read the task from stdin
  dsh --profile headless --json "run the tests"   emit machine-readable run events
  dsh --profile headless --session-id session-… "continue"   resume an existing Session
''')#帮助示例
    )#结束

def 请求了json(参数列表):
    """原始调用是否点名机器可读流。遇 `--` 停止，跳过 `--session-id` 的值。"""
    下标=0#游标
    while 下标<len(参数列表):#逐参
        参数=参数列表[下标]#当前
        if 参数=='--':#位置分界
            return False#其后不是旗
        if 参数=='--json':#本旗
            return True#是
        if 参数=='--session-id':#跳过值
            下标=下标+1#跳值
        下标=下标+1#推进
    return False#否

def 应用(上下文):
    """把一次性任务解析并作为普通 Cordis 服务提供。"""
    程序=无头命令()#构造命令
    参数服务=上下文.获取服务('cmdlineArgs',False)#命令行
    原始=[] if 参数服务 is None else 参数服务.取()#原始参数
    if 请求了json(原始):#JSON 契约
        def 错误覆盖(消息,错误选项=None):
            """写出 JSON 错误事件再抛控制流错误。"""
            正文=消息[7:] if 消息.startswith('error: ') else 消息#去掉前缀
            内部流['stdout'].write(约束json行({'type':'error','message':正文})+'\n')#事件
            码='commander.error' if 错误选项 is None or 'code' not in 错误选项 else 错误选项['code']#码
            raise 命令错误(消息,1,码)#控制流
        程序.error=错误覆盖#覆盖
    def 动作():
        """发布任务、会话标识与 JSON 旗。"""
        if len(程序.args)>1 and '-' in 程序.args:#`-` 必须独占
            程序.error('error: `-` must be the only task argument')#拒绝
        拼接=' '.join(程序.args)#用空格拼接词
        if len(程序.args)>0 and 拼接.strip()=='':#空任务
            程序.error('error: a task is required, for example: dsh --profile headless "run the tests"')#空任务失败
        任务=None if len(程序.args)==0 else 拼接#缺席则 stdin
        if 任务 is None and 内部流['stdinIsTty']():#交互终端且无任务
            程序.error('error: a task is required, for example: dsh --profile headless "run the tests"')#拒绝
        选项=程序.opts()#已解析选项
        会话标识值=选项['sessionId'] if 'sessionId' in 选项 else None#可选
        if 会话标识值 is not None and 会话标识值.strip()=='':#空白身份
            程序.error('error: --session-id requires a non-empty session id')#拒绝
        上下文.提供服务(无头启动服务键,{#发布启动服务
            'task':任务,
            'sessionId':会话标识值,
            'json':选项['json'] is True if 'json' in 选项 else False,
        })#服务结束
    程序.action(动作)#登记 action
    解析命令行(上下文,程序)#解析命令行

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
