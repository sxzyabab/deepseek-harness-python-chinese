import re
from ....工具.工作区路径 import 是否绝对工作区路径,解析工作区路径
from ....工具输出.溢出策略 import 含溢出须知
from .文案 import 中文文案
from .原始工具调用 import 解析工具调用,单结果文本
from .已记录路径 import 已记录绝对路径

__all__=[
    '终端块文案','本地化终端卡模型','终端已失败','终端退出文案',
    '是后台外壳调用','是已结算持久外壳调用','是溢出外壳调用','终端卡模型',
]

点点段=re.compile(r'(?:^|[/\\])\.\.?(?:[/\\]|$)')
unc形=re.compile(r'^[/\\]{2}([^/\\]+)[/\\]+([^/\\]+)')
有根形=re.compile(r'^[/\\]')
盘符形=re.compile(r'^[A-Za-z]:')
信号标记=re.compile(r'\n\[killed by signal: ([^\]\n]+)\]$')
退出标记=re.compile(r'\n\[exit code: (-?\d+|null)\]$')

def 终端块文案():
    '终端块标签。显示用中文原文'
    def 命令行(行号):
        '命令第几行'
        return 中文文案('terminal.commandLine',{'n':行号})
    def 信号(信号值):
        '信号文案'
        return 中文文案('terminal.signal',{'signal':信号值})
    def 退出码(码):
        '退出码文案'
        return 中文文案('terminal.exitCode',{'code':码})
    def 展开无障碍(隐):
        '展开被折叠行的无障碍名'
        return 中文文案('terminal.expandAria',{'n':隐})
    def 展开其余(隐):
        '展开其余行'
        return 中文文案('terminal.expandRest',{'n':隐})
    return {
        'commandLine':命令行,
        'signal':信号,
        'exitCode':退出码,
        'noExitCode':中文文案('terminal.noExitCode'),
        'running':中文文案('terminal.running'),
        'failed':中文文案('terminal.failed'),
        'done':中文文案('terminal.done'),
        'copy':中文文案('copy'),
        'copied':中文文案('copied'),
        'noOutput':中文文案('terminal.noOutput'),
        'collapseAria':中文文案('terminal.collapseAria'),
        'collapse':中文文案('collapse'),
        'expandAria':展开无障碍,
        'expand':展开其余,
    }

def 本地化终端卡模型(模型):
    'shell 命令与描述原样。terminal_send 的空文本用中文发送输入'
    副本=模型['copy']
    if 副本['kind']=='shell':
        卡片=dict(模型['card'])
        卡片['command']=副本['command']
        return {'card':卡片,'description':副本['description']}
    命令=副本['text']
    if 命令=='':
        命令=中文文案('terminal.sendInput')
    卡片=dict(模型['card'])
    卡片['command']=命令
    return {
        'card':卡片,
        'description':中文文案('terminal.session',{'sessionId':副本['sessionId']}),
    }

def 终端已失败(模型):
    '非运行，且退出码非零或有信号'
    卡片=模型['card']
    if 卡片.get('running') is True:
        return False
    退出码=卡片.get('exitCode',None)
    有码='exitCode' in 卡片 and 退出码!=0
    return 有码 or 'signal' in 卡片

def 终端退出文案(模型):
    '前台失败才有胶囊。运行、后台或成功为 None'
    if 模型 is None or 模型['card'].get('background') or not 终端已失败(模型):
        return None
    卡片=模型['card']
    if 'signal' in 卡片:
        return 中文文案('terminal.signal',{'signal':卡片['signal']})
    if 卡片.get('exitCode') is None:
        return 中文文案('terminal.noExitCode')
    return 中文文案('terminal.exitCode',{'code':卡片['exitCode']})

def 折叠段(体,有根,分隔符='/'):
    '无前导或尾随分隔符'
    保留=[]
    for 段 in re.split(r'[/\\]',体):
        if 段=='' or 段=='.':
            continue
        if 段=='..':
            if len(保留)>0 and 保留[-1]!='..':
                保留.pop()
            elif not 有根:
                保留.append(段)
            continue
        保留.append(段)
    return 分隔符.join(保留)

def 归一化段(路径):
    '分隔符按原文保留。UNC 的服务器和共享不弹出'
    if 点点段.search(路径) is None:
        return 路径
    unc=unc形.match(路径)
    if unc is not None:
        根='\\\\'+unc.group(1)+'\\'+unc.group(2)
        其余=折叠段(路径[unc.end():],True)
        if 其余=='':
            return 根
        return 根+'\\'+其余
    反斜= '\\' in 路径 and '/' not in 路径
    分隔符='\\' if 反斜 else '/'
    有根=有根形.match(路径) is not None
    盘=盘符形.match(路径)
    盘符=盘.group(0) if 盘 is not None else ''
    体=折叠段(路径[len(盘符):],有根 or 盘符!='',分隔符)
    前导=分隔符 if 有根 else ''
    if 盘符=='':
        return 前导+体
    if 有根:
        return 盘符+前导+体
    return 盘符+分隔符+体

def 解析终端工作区(视图工作区,会话工作区):
    '绝对原样，相对接到会话工作区，省略则会话工作区'
    if 视图工作区 is None or 视图工作区=='':
        return 会话工作区
    if 会话工作区 is None or 会话工作区=='':
        return 归一化段(视图工作区)
    return 归一化段(解析工作区路径(会话工作区,视图工作区))

def 外壳调用(名称,参数):
    'bash 或 pwsh。缺描述视为持久外壳'
    if 名称!='bash' and 名称!='pwsh':
        return None
    命令=参数.get('command')
    if not isinstance(命令,str) or 命令.strip()=='':
        return None
    超时=参数.get('timeoutMs',None)
    if 'timeoutMs' in 参数:
        if isinstance(超时,bool) or not isinstance(超时,(int,float)) or 超时!=超时 or 超时==float('inf') or 超时<=0:
            return None
    if 'workdir' in 参数 and not isinstance(参数.get('workdir'),str):
        return None
    if 'run_in_background' in 参数 and not isinstance(参数.get('run_in_background'),bool):
        return None
    if 'description' not in 参数:
        return {
            'kind':'shell','command':命令,'description':None,
            'workdir':None,'persistent':True,'background':False,
        }
    描述=参数.get('description')
    if not isinstance(描述,str) or 描述.strip()=='':
        return None
    return {
        'kind':'shell',
        'command':命令,
        'description':描述,
        'workdir':参数.get('workdir') if isinstance(参数.get('workdir'),str) else None,
        'persistent':False,
        'background':参数.get('run_in_background') is True,
    }

def 是后台外壳调用(块):
    '请求后台外壳任务'
    已解析=解析工具调用(块)
    if 已解析 is None:
        return False
    调用=外壳调用(已解析['name'],已解析['args'])
    return 调用 is not None and 调用['background'] is True

def 是已结算持久外壳调用(块):
    '已结算的根持久 bash 或 pwsh'
    if 'kind' not in 块 or 块.get('parentCallId') is not None:
        return False
    已解析=解析工具调用(块)
    if 已解析 is None:
        return False
    调用=外壳调用(已解析['name'],已解析['args'])
    return 调用 is not None and 调用['persistent'] is True

def 是溢出外壳调用(块):
    '前台外壳结果末尾带溢出须知'
    if 'kind' not in 块:
        return False
    已解析=解析工具调用(块)
    if 已解析 is None:
        return False
    调用=外壳调用(已解析['name'],已解析['args'])
    if 调用 is None or 调用['background']:
        return False
    输出=单结果文本(块)
    return 输出 is not None and 含溢出须知(输出)

def 终端发送调用(名称,参数):
    'terminal_send。后台发送不进终端卡'
    if 名称!='terminal_send':
        return None
    会话标识=参数.get('sessionId')
    文本=参数.get('text')
    if not isinstance(会话标识,str) or 会话标识=='' or not isinstance(文本,str):
        return None
    if 'submit' in 参数 and not isinstance(参数.get('submit'),bool):
        return None
    if 'run_in_background' in 参数 and not isinstance(参数.get('run_in_background'),bool):
        return None
    return {
        'kind':'terminal-send',
        'text':文本,
        'sessionId':会话标识,
        'background':参数.get('run_in_background') is True,
    }

def 解析退出状态(文本):
    '拆掉末尾信号或退出码标记。没有标记则退出码 0'
    信号=信号标记.search(文本)
    if 信号 is not None:
        return {'output':文本[:信号.start()],'signal':信号.group(1)}
    退出=退出标记.search(文本)
    if 退出 is not None:
        码=None if 退出.group(1)=='null' else int(退出.group(1))
        return {'output':文本[:退出.start()],'exitCode':码}
    return {'output':文本,'exitCode':0}

def 终端卡模型(块,会话工作区=None):
    '非终端卡片返回 None'
    已解析=解析工具调用(块)
    if 已解析 is None:
        return None
    调用=外壳调用(已解析['name'],已解析['args'])
    if 调用 is None:
        调用=终端发送调用(已解析['name'],已解析['args'])
    if 调用 is None or (调用['kind']=='terminal-send' and 调用['background']):
        return None
    if 调用['kind']=='shell':
        副本={'kind':'shell','command':调用['command'],'description':调用['description']}
        工作目录=调用['workdir']
    else:
        副本={'kind':'terminal-send','text':调用['text'],'sessionId':调用['sessionId']}
        工作目录=None
    绝对请求=None
    if isinstance(工作目录,str) and 是否绝对工作区路径(工作目录):
        绝对请求=归一化段(工作目录)
    if 'kind' in 块:
        记录=已记录绝对路径(块.get('meta'),'cwd')
        if 记录 is not None:
            工作目录展示=记录
        elif 调用['kind']=='shell' and 块.get('parentCallId') is None:
            工作目录展示=解析终端工作区(工作目录,会话工作区)
        else:
            工作目录展示=绝对请求
    else:
        工作目录展示=绝对请求
    if 'kind' not in 块:
        卡片={
            'cwd':工作目录展示,
            'output':None,
            'running':True,
        }
        if 调用['kind']=='shell' and 调用['background']:
            卡片['background']=调用['background']
        return {'copy':副本,'card':卡片}
    if 块.get('isError') is True or (调用['kind']=='shell' and 调用['persistent']) or 是溢出外壳调用(块):
        return None
    if 调用['kind']=='shell' and 调用['background']:
        return {
            'copy':副本,
            'card':{'cwd':工作目录展示,'running':False,'background':调用['background']},
        }
    输出=单结果文本(块)
    if 输出 is None:
        return None
    if 调用['kind']=='terminal-send':
        状态={'output':输出}
    else:
        状态=解析退出状态(输出)
    卡片={
        'cwd':工作目录展示,
        'output':状态['output'],
        'running':False,
    }
    if 'exitCode' in 状态:
        卡片['exitCode']=状态['exitCode']
    if 'signal' in 状态:
        卡片['signal']=状态['signal']
    return {'copy':副本,'card':卡片}
