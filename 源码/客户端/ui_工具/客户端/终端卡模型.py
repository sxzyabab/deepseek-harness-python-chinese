import re#路径段折叠

__all__=['终端块文案','终端已失败','终端卡模型']#仅中文公开名

段切=re.compile(r'[/\\]')#路径段分隔
点点段=re.compile(r'(?:^|[/\\])\.\.?(?:[/\\]|\Z)')#含 . 或 .. 段
unc形=re.compile(r'^[/\\]{2}([^/\\]+)[/\\]+([^/\\]+)')#UNC 根
有根形=re.compile(r'^[/\\]')#绝对根
盘符形=re.compile(r'^[A-Za-z]:')#盘符

def 信号文案(翻译,信号):#signal 插值
    """terminal.signal。"""
    return 翻译('terminal.signal',{'signal':信号})#文案

def 退出码文案(翻译,码):#exitCode 插值
    """terminal.exitCode。"""
    return 翻译('terminal.exitCode',{'code':码})#文案

def 展开无障碍(翻译,隐):#expandAria
    """terminal.expandAria。"""
    return 翻译('terminal.expandAria',{'n':隐})#文案

def 展开其余(翻译,隐):#expandRest
    """terminal.expandRest。"""
    return 翻译('terminal.expandRest',{'n':隐})#文案

def 终端块文案(翻译):#从会话词条组装终端块文案
    """原语文案面与本包词典配对。"""
    def 信号(信号值):#signal
        """插值。"""
        return 信号文案(翻译,信号值)#文案
    def 退出码(码):#exitCode
        """插值。"""
        return 退出码文案(翻译,码)#文案
    def 展开无障碍文(隐):#expandAria
        """插值。"""
        return 展开无障碍(翻译,隐)#文案
    def 展开其余文(隐):#expandRest
        """插值。"""
        return 展开其余(翻译,隐)#文案
    return {#原语文案面
        'signal':信号,
        'exitCode':退出码,
    'noExitCode':翻译('terminal.noExitCode'),
    'running':翻译('terminal.running'),'failed':翻译('terminal.failed'),
    'done':翻译('terminal.done'),'copy':翻译('copy'),'copied':翻译('copied'),
    'noOutput':翻译('terminal.noOutput'),'collapseAria':翻译('terminal.collapseAria'),
    'collapse':翻译('collapse'),
    'expandAria':展开无障碍文,
    'expand':展开其余文,
  }#labels

def 终端已失败(模型):#折叠行的失败信号
    """非运行且（非零码或有信号）。"""
    卡=模型['card'] if 'card' in 模型 else {}#card
    退出码=卡['exitCode'] if 'exitCode' in 卡 else None#exitCode
    信号=卡['signal'] if 'signal' in 卡 else None#signal
    运行中=卡['running'] if 'running' in 卡 else None#running
    return 运行中 is not True and ((退出码 is not None and 退出码!=0) or 信号 is not None)#失败

def 折叠段(体,有根,分隔符='/'):#折叠路径体的 . / ..
    """无前导或尾随分隔符。"""
    保留=[]#保留段
    for 段 in 段切.split(体):#切开
        if 段=='' or 段=='.':#空或 .
            continue#丢掉
        if 段=='..':#上一级
            if len(保留)>0 and 保留[-1]!='..':#可弹
                保留.pop()#弹出
            elif not 有根:#无根时保留 ..
                保留.append(段)#保留
            continue#本段完
        保留.append(段)#普通段
    return 分隔符.join(保留)#重拼

def 归一化段(路径):#折叠路径里的 . / ..
    """分隔符按原文保留。"""
    if 点点段.search(路径) is None:#没有 . / ..
        return 路径#原样
    unc=unc形.match(路径)#UNC
    if unc is not None:#是 UNC
        匹配,服务器,共享=unc.group(0),unc.group(1),unc.group(2)#拆
        根='\\\\'+服务器+'\\'+共享#UNC 根
        剩余=折叠段(路径[len(匹配):],True,'\\')#共享后体
        return 根 if 剩余=='' else 根+'\\'+剩余#拼
    反斜=('\\' in 路径) and ('/' not in 路径)#纯反斜杠
    分隔='\\' if 反斜 else '/'#分隔符
    有根=有根形.match(路径) is not None#是否有根
    盘符匹配=盘符形.match(路径)#盘符
    盘符=盘符匹配.group(0) if 盘符匹配 else ''#盘符
    体=折叠段(路径[len(盘符):],有根 or 盘符!='',分隔)#体
    前导=分隔 if 有根 else ''#前导
    if 盘符=='':#无盘符
        return 前导+体#前导+体
    return 盘符+(前导 if 有根 else 分隔)+体#盘符+分隔+体

def 解析终端工作区(视图工作区,会话工作区,解析工作区路径=None):#解析提示行 cwd
    """绝对原样，相对接到会话工作区，省略则会话工作区。"""
    if 视图工作区 is None or 视图工作区=='':#视图没给
        return 会话工作区#用会话
    if 会话工作区 is None or 会话工作区=='':#无会话根
        return 归一化段(视图工作区)#只折叠段
    if 解析工作区路径 is not None:#有解析器
        return 归一化段(解析工作区路径(会话工作区,视图工作区))#接到后再折叠
    if 视图工作区.startswith('/') or 视图工作区.startswith('\\') or 盘符形.match(视图工作区) is not None:#绝对
        return 归一化段(视图工作区)#原样折叠
    接=会话工作区.rstrip('/\\')+'/'+视图工作区.lstrip('/\\')#拼接
    return 归一化段(接)#折叠

def 终端卡模型(块,会话工作区=None,解析工作区路径=None):#从调用切片派生终端卡片
    """非终端卡片返回 None。"""
    调用视图=块['callView'] if 'callView' in 块 else None#调用视图
    调用=调用视图 if 调用视图 is not None and 调用视图['card']=='terminal' else None#仅 terminal
    已结算='kind' in 块#已结算
    if not 已结算:#仍在跑
        if 调用 is None:#不是终端调用
            return None#通用路径
        return {#进行中
            'description':调用['description'] if 'description' in 调用 else None,
            'card':{
                'command':调用['title'] if 'title' in 调用 else None,
                'cwd':解析终端工作区(调用['cwd'] if 'cwd' in 调用 else None,会话工作区,解析工作区路径),
                'output':None,'exitCode':None,'signal':None,'running':True,
            },
        }#进行中
    结果视图=块['resultView'] if 'resultView' in 块 else None#结果视图
    结果=结果视图 if 结果视图 is not None and 结果视图['card']=='terminal' else None#仅 terminal
    if 结果 is None:#结果不是终端
        return None#通用路径
    命令=结果['title'] if 'title' in 结果 else None#结果标题
    if 命令 is None and 调用 is not None:#回退调用标题
        命令=调用['title'] if 'title' in 调用 else None#调用
    if 命令 is None:#仍无
        命令=''#空
    工作目录=None if 调用 is None else 解析终端工作区(调用['cwd'] if 'cwd' in 调用 else None,会话工作区,解析工作区路径)#有调用侧才解析
    return {#已落定
        'description':调用['description'] if 调用 is not None and 'description' in 调用 else None,
        'card':{
            'command':命令,'cwd':工作目录,
            'output':结果['output'] if 'output' in 结果 else None,
            'exitCode':结果['exitCode'] if 'exitCode' in 结果 else None,
            'signal':结果['signal'] if 'signal' in 结果 else None,'running':False,
        },
    }#落定
