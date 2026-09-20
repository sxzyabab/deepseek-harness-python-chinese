"""一次性应用的命令行提供方：解析任务位置参数、`--session-id`、`--json` 与 `--help`。"""
from ...启动.命令行 import 命令,解析命令行,命令错误
from .json流 import 约束json行
from .启动内部 import 内部流

__all__=['名称','依赖','无头启动服务键','应用']

名称='headless-startup'
依赖=['cmdlineArgs']
无头启动服务键='headlessStartup'

def 无头命令():
    """本应用的命令：任务位置参数、选项与帮助文本。"""
    return (命令()
        .name('dsh --profile headless')
        .description('回答一项任务后退出；答案走标准输出，诊断走标准错误。')
        .helpOption('-h, --help','显示此帮助')
        .option('--json','向标准输出写换行分隔的运行事件，而不是终局消息')
        .option('--session-id <id>','收养具有此 id 的已持久化会话；未知 id 视为错误')
        .argument('[task...]','任务文本；多个词用空格拼接，`-` 表示从标准输入读取')
        .addHelpText('after','''
示例:
  dsh --profile headless "run the tests"          回答一项任务后退出
  echo "run the tests" | dsh --profile headless   从标准输入读任务
  dsh --profile headless --json "run the tests"   发出机器可读运行事件
  dsh --profile headless --session-id session-… "continue"   恢复已有会话
''')
    )

def 请求了json(参数列表):
    """原始调用是否点名机器可读流。遇 `--` 停止，跳过 `--session-id` 的值。"""
    下标=0
    while 下标<len(参数列表):
        参数=参数列表[下标]
        if 参数=='--':
            return False
        if 参数=='--json':
            return True
        if 参数=='--session-id':
            下标=下标+1
        下标=下标+1
    return False

def 应用(上下文):
    """把一次性任务解析并作为普通 Cordis 服务提供。"""
    程序=无头命令()
    参数服务=上下文.获取服务('cmdlineArgs',False)
    原始=[] if 参数服务 is None else 参数服务.取()
    if 请求了json(原始):
        def 错误覆盖(消息,错误选项=None):
            """写出 JSON 错误事件再抛控制流错误。"""
            正文=消息[7:] if 消息.startswith('error: ') else 消息
            内部流['stdout'].write(约束json行({'type':'error','message':正文})+'\n')
            码='commander.error' if 错误选项 is None or 'code' not in 错误选项 else 错误选项['code']
            raise 命令错误(消息,1,码)
        程序.error=错误覆盖
    def 动作():
        """发布任务、会话标识与 JSON 旗。"""
        if len(程序.args)>1 and '-' in 程序.args:
            程序.error('error: `-` 必须是唯一的任务参数')
        拼接=' '.join(程序.args)
        if len(程序.args)>0 and 拼接.strip()=='':
            程序.error('error: 必须提供任务，例如：dsh --profile headless "run the tests"')
        任务=None if len(程序.args)==0 else 拼接
        if 任务 is None and 内部流['stdinIsTty']():
            程序.error('error: 必须提供任务，例如：dsh --profile headless "run the tests"')
        选项=程序.opts()
        会话标识值=选项['sessionId'] if 'sessionId' in 选项 else None
        if 会话标识值 is not None and 会话标识值.strip()=='':
            程序.error('error: --session-id 需要非空会话 id')
        上下文.提供服务(无头启动服务键,{
            'task':任务,
            'sessionId':会话标识值,
            'json':选项['json'] is True if 'json' in 选项 else False,
        })
    程序.action(动作)
    解析命令行(上下文,程序)

name=名称
inject=依赖
apply=应用
