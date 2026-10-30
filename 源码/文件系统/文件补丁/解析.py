'Codex 风格补丁解析。只看字符串，不碰文件系统'
import re#按 LF 切行
from .异常 import 补丁解析错误#语法错误

开始标记='*** Begin Patch'#补丁开头
结束标记='*** End Patch'#补丁结尾
文件结束标记='*** End of File'#hunk 之后的文件尾
移动标记='*** Move to: '#更新的目标路径
新增标记='*** Add File: '#新增文件
删除标记='*** Delete File: '#删除文件
更新标记='*** Update File: '#更新文件

def 是空白(字符):
    'Unicode White_Space。不含 BOM'
    return 字符.isspace()#与上游 White_Space 对齐，BOM 不是空白

def 去尾空白(文本):
    '去掉末尾空白，保留内容空白'
    止=len(文本)#从尾扫描
    while 止>0 and 是空白(文本[止-1]):#末尾仍是空白
        止=止-1
    return 文本[:止]#不含末尾空白

def 去首尾空白(文本):
    '去掉两端空白'
    起=0#从头扫描
    while 起<len(文本) and 是空白(文本[起]):#开头仍是空白
        起=起+1
    return 去尾空白(文本[起:])#再去尾

def 补丁行(补丁):
    """按原始输入行号列出有效行。
    字面量 EOF heredoc 包装会被剥掉，不执行。
    缺 Begin 或 End 时抛补丁解析错误"""
    前导长=0#开头空白的字符数
    while 前导长<len(补丁) and 是空白(补丁[前导长]):#数前导空白
        前导长=前导长+1
    偏移=补丁[:前导长].count('\n')#前导空白里的换行，行号要算上
    正文=去首尾空白(补丁)#裁掉外围空白
    行表=[]#带行号的行
    序号=0#切分后的下标
    for 文本 in re.split(r'\r?\n',正文):#只按 LF 与 CRLF 切
        行表.append({'文本':文本,'行号':偏移+序号+1})#原始行号
        序号=序号+1
    首行=行表[0]#包装或 Begin
    末行=行表[-1]#包装或 End
    if 首行['文本'] in ("<<EOF","<<'EOF'",'<<"EOF"') and 末行['文本'].endswith('EOF') and len(行表)>=4:#字面量包装
        行表=行表[1:-1]#剥掉包装，行号保留
    起点=行表[0]#Begin
    终点=行表[-1]#End
    if 去首尾空白(起点['文本'])!=开始标记:#缺开头
        raise 补丁解析错误(起点['行号'],"Expected '"+开始标记+"'")#拒绝
    if 去首尾空白(终点['文本'])!=结束标记:#缺结尾
        raise 补丁解析错误(终点['行号'],"Expected '"+结束标记+"'")#拒绝
    结果=[]#去掉行尾 CR
    下标=0
    总数=len(行表)#最后一行不再剥 CR
    for 行 in 行表:#Codex 会再剥一次 CR
        if 下标<总数-1:#非最后一行
            结果.append({'文本':re.sub(r'\r$','',行['文本']),'行号':行['行号']})#剥 CR
        else:
            结果.append(行)#最后一行原样
        下标=下标+1
    return 结果#可解析的行

def 修改块为空(修改块):
    '旧行和新行都没有'
    return len(修改块['旧行'])==0 and len(修改块['新行'])==0

def 保证更新完整(操作,行号):
    '更新必须已有非空 hunk。不是更新则放过'
    if 操作 is None or 操作['种类']!='更新':#不是更新
        return
    if len(操作['修改块'])==0:#一个 hunk 都没有
        raise 补丁解析错误(操作['行号'],"Update for '"+操作['路径']+"' requires at least one hunk")
    if 修改块为空(操作['修改块'][-1]):#最后一个是空的
        raise 补丁解析错误(行号,'Update hunk must contain context, added, or removed lines')

def 新修改块(行号):
    '空 hunk，行号是标记或第一行隐式内容所在行'
    return {'行号':行号,'旧行':[],'新行':[],'文件结束':False}

def 读更新(操作,行):
    '把一行填进当前更新。Move 只允许出现在第一个 hunk 之前'
    文本=去尾空白(行['文本'])#标记行去尾空白
    已有=操作['修改块'][-1] if len(操作['修改块'])>0 else None#当前 hunk
    是标记=文本=='@@' or 文本.startswith('@@ ')#新 hunk
    if 已有 is not None and 已有['文件结束']:#EOF 之后
        if 文本=='':#允许空行
            return
        if not 是标记:#必须新 hunk
            raise 补丁解析错误(行['行号'],"Expected '@@' after '*** End of File'")
    if 已有 is None and '移动到' not in 操作 and 文本.startswith(移动标记):#紧跟文件头的移动
        操作['移动到']=文本[len(移动标记):]#目标路径
        return
    if 是标记:#开一个 hunk
        if 已有 is not None and 修改块为空(已有):#上一个还是空的
            raise 补丁解析错误(行['行号'],'Update hunk must contain context, added, or removed lines')
        修改块=新修改块(行['行号'])#新块
        if 文本.startswith('@@ '):#带锚点
            修改块['上下文']=文本[3:]#@@ 后的文本
        操作['修改块'].append(修改块)#收下
        return
    if 文本==文件结束标记:#EOF 标志
        if 已有 is not None:#有 hunk 才能标记
            if 修改块为空(已有):#空 hunk 不能收尾
                raise 补丁解析错误(行['行号'],'Update hunk must contain context, added, or removed lines')
            已有['文件结束']=True#只搜文件尾
        return
    前缀=行['文本'][0] if 行['文本']!='' else ''#第一字符
    if 行['文本']!='' and 前缀 not in (' ','+','-'):#非法标记
        raise 补丁解析错误(行['行号'],"Expected a context (' '), added ('+'), removed ('-') line, or '@@'")
    修改块=已有 if 已有 is not None else 新修改块(行['行号'])#隐式第一块
    if 已有 is None:#第一次出现内容
        操作['修改块'].append(修改块)#挂上
    内容=行['文本'][1:]#去掉前缀；空行前缀视为上下文，内容为空
    if 前缀=='+':#插入
        修改块['新行'].append(内容)
    elif 前缀=='-':#删除
        修改块['旧行'].append(内容)
    else:#上下文，两边都记
        修改块['旧行'].append(内容)
        修改块['新行'].append(内容)

def 解析补丁(补丁):
    """解析完整补丁。
    返回有序操作 dict。空补丁返回空列表。
    语法错误抛补丁解析错误"""
    行表=补丁行(补丁)#带行号
    操作表=[]#按出现顺序
    已结束=False#见过 End
    for 行 in 行表[1:]:#跳过 Begin
        操作=操作表[-1] if len(操作表)>0 else None#当前文件
        if 操作 is not None and 操作['种类']=='更新' and 行 is not 行表[-1]:#更新内部只去尾
            头=去尾空白(行['文本'])
        else:
            头=去首尾空白(行['文本'])#文件头与最终标记去两端
        if 已结束 and 行 is not 行表[-1]:#End 之后
            if 去首尾空白(行['文本'])!='':#不允许内容
                raise 补丁解析错误(行['行号'],"Unexpected content after '"+结束标记+"'")
            continue
        if 头==结束标记:#收束当前更新
            保证更新完整(操作,行['行号'])
            已结束=True
        elif 头.startswith(新增标记):#新文件
            保证更新完整(操作,行['行号'])
            操作表.append({'种类':'新增','路径':头[len(新增标记):],'行号':行['行号'],'内容':''})
        elif 头.startswith(删除标记):#删文件
            保证更新完整(操作,行['行号'])
            操作表.append({'种类':'删除','路径':头[len(删除标记):],'行号':行['行号']})
        elif 头.startswith(更新标记):#改文件
            保证更新完整(操作,行['行号'])
            操作表.append({'种类':'更新','路径':头[len(更新标记):],'行号':行['行号'],'修改块':[]})
        elif len(操作表)==0 and 头.startswith('*** Environment ID:'):#不支持的头
            raise 补丁解析错误(行['行号'],'Environment ID headers are unsupported; the caller selects the filesystem provider')
        elif 操作 is not None and 操作['种类']=='新增' and 行['文本'].startswith('+'):#新增内容
            操作['内容']=操作['内容']+行['文本'][1:]+'\n'#每行都带 LF
        elif 操作 is not None and 操作['种类']=='更新':#更新正文
            读更新(操作,行)
        else:#无法归类
            raise 补丁解析错误(行['行号'],'Expected an Add File, Delete File, or Update File header; added content must start with +')
    return 操作表#有序操作
