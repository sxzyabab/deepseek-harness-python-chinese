import re

__all__=['终端块文案','终端已失败','终端卡模型']

段切=re.compile(r'[/\\]')
点点段=re.compile(r'(?:^|[/\\])\.\.?(?:[/\\]|\Z)')
unc形=re.compile(r'^[/\\]{2}([^/\\]+)[/\\]+([^/\\]+)')
有根形=re.compile(r'^[/\\]')
盘符形=re.compile(r'^[A-Za-z]:')

def 信号文案(翻译,信号):
    'terminal.signal'
    return 翻译('terminal.signal',{'signal':信号})

def 退出码文案(翻译,码):
    'terminal.exitCode'
    return 翻译('terminal.exitCode',{'code':码})

def 展开无障碍(翻译,隐):
    'terminal.expandAria'
    return 翻译('terminal.expandAria',{'n':隐})

def 展开其余(翻译,隐):
    'terminal.expandRest'
    return 翻译('terminal.expandRest',{'n':隐})

def 终端块文案(翻译):
    '原语文案面与本包词典配对'
    def 信号(信号值):
        '插值'
        return 信号文案(翻译,信号值)
    def 退出码(码):
        '插值'
        return 退出码文案(翻译,码)
    def 展开无障碍文(隐):
        '插值'
        return 展开无障碍(翻译,隐)
    def 展开其余文(隐):
        '插值'
        return 展开其余(翻译,隐)
    return {
        'signal':信号,
        'exitCode':退出码,
        'noExitCode':翻译('terminal.noExitCode'),
        'running':翻译('terminal.running'),'failed':翻译('terminal.failed'),
        'done':翻译('terminal.done'),'copy':翻译('copy'),'copied':翻译('copied'),
        'noOutput':翻译('terminal.noOutput'),'collapseAria':翻译('terminal.collapseAria'),
        'collapse':翻译('collapse'),
        'expandAria':展开无障碍文,
        'expand':展开其余文,
    }

def 终端已失败(模型):
    '非运行且（非零码或有信号）'
    卡=模型['card'] if 'card' in 模型 else {}
    退出码=卡['exitCode'] if 'exitCode' in 卡 else None
    信号=卡['signal'] if 'signal' in 卡 else None
    运行中=卡['running'] if 'running' in 卡 else None
    return 运行中 is not True and ((退出码 is not None and 退出码!=0) or 信号 is not None)

def 折叠段(体,有根,分隔符='/'):
    '无前导或尾随分隔符'
    保留=[]
    for 段 in 段切.split(体):
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
    '分隔符按原文保留'
    if 点点段.search(路径) is None:
        return 路径
    unc=unc形.match(路径)
    if unc is not None:
        匹配,服务器,共享=unc.group(0),unc.group(1),unc.group(2)
        根='\\\\'+服务器+'\\'+共享
        剩余=折叠段(路径[len(匹配):],True,'\\')
        return 根 if 剩余=='' else 根+'\\'+剩余
    反斜=('\\' in 路径) and ('/' not in 路径)
    分隔='\\' if 反斜 else '/'
    有根=有根形.match(路径) is not None
    盘符匹配=盘符形.match(路径)
    盘符=盘符匹配.group(0) if 盘符匹配 else ''
    体=折叠段(路径[len(盘符):],有根 or 盘符!='',分隔)
    前导=分隔 if 有根 else ''
    if 盘符=='':
        return 前导+体
    return 盘符+(前导 if 有根 else 分隔)+体

def 解析终端工作区(视图工作区,会话工作区,解析工作区路径=None):
    '绝对路径原样折叠；相对路径接到会话工作区；省略则用会话工作区'
    if 视图工作区 is None or 视图工作区=='':
        return 会话工作区
    if 会话工作区 is None or 会话工作区=='':
        return 归一化段(视图工作区)
    if 解析工作区路径 is not None:
        return 归一化段(解析工作区路径(会话工作区,视图工作区))
    if 视图工作区.startswith('/') or 视图工作区.startswith('\\') or 盘符形.match(视图工作区) is not None:
        return 归一化段(视图工作区)
    接=会话工作区.rstrip('/\\')+'/'+视图工作区.lstrip('/\\')
    return 归一化段(接)

def 终端卡模型(块,会话工作区=None,解析工作区路径=None):
    '非终端卡片返回 None'
    调用视图=块['callView'] if 'callView' in 块 else None
    调用=调用视图 if 调用视图 is not None and 调用视图['card']=='terminal' else None
    已结算='kind' in 块
    if not 已结算:
        if 调用 is None:
            return None
        return {
            'description':调用['description'] if 'description' in 调用 else None,
            'card':{
                'command':调用['title'] if 'title' in 调用 else None,
                'cwd':解析终端工作区(调用['cwd'] if 'cwd' in 调用 else None,会话工作区,解析工作区路径),
                'output':None,'exitCode':None,'signal':None,'running':True,
            },
        }
    结果视图=块['resultView'] if 'resultView' in 块 else None
    结果=结果视图 if 结果视图 is not None and 结果视图['card']=='terminal' else None
    if 结果 is None:
        return None
    命令=结果['title'] if 'title' in 结果 else None
    if 命令 is None and 调用 is not None:
        命令=调用['title'] if 'title' in 调用 else None
    if 命令 is None:
        命令=''
    工作目录=None if 调用 is None else 解析终端工作区(调用['cwd'] if 'cwd' in 调用 else None,会话工作区,解析工作区路径)
    return {
        'description':调用['description'] if 调用 is not None and 'description' in 调用 else None,
        'card':{
            'command':命令,'cwd':工作目录,
            'output':结果['output'] if 'output' in 结果 else None,
            'exitCode':结果['exitCode'] if 'exitCode' in 结果 else None,
            'signal':结果['signal'] if 'signal' in 结果 else None,'running':False,
        },
    }
