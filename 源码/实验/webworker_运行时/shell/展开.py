"""词展开：一个已解析参数变成程序在 argv 中收到的零个或多个字段。覆盖文法
产生的片段种类——字面文本、变量（含 `:-` / `:+` 形式）、命令替换、算术，
以及对照 VFS 匹配的 glob。

对齐上游 `webworker-runtime/src/shell/expand.ts`。公开面仅中文名。
"""
import fnmatch as 文件名匹配#glob段匹配（对齐 picomatch 用法）
import math as 数学#整除
import re as 正则#glob特征
from ..module_system.posix路径 import 解析 as 解析路径#路径解析

__all__=['是否glob模式','读变量','展开glob','展开参数']#仅中文公开名

glob特征=正则.compile(r'[*?]|\[[^\]]*\]')#使文法把整个词当作glob模式的字符

def 是否glob模式(词):#是否glob模式
    """一个词是否为 shell 应对照文件系统匹配的 glob。"""
    return glob特征.search(词) is not None#测通配符

def 读变量(状态,名):#读变量
    """按 `$name` 的方式读取一个变量。"""
    if 名=='?':#上一状态
        return str(状态['lastStatus'])#字符串化
    # worker 宿主以 pid 1 运行整棵树；`$$` 原样报告它。
    if 名=='$':#宿主pid
        return '1'#固定报告
    if 名=='0':#脚本名
        return 'bash'#固定名
    # 此处没有位置参数到达 `bash -c` 命令行。
    if 名=='#':#位置参数个数
        return '0'#零个
    if 名 in ('@','*'):#位置参数展开为空
        return ''#空串
    return 状态['variables'].get(名,状态['environment'].get(名))#普通变量

def 算术(表达式,状态):#求算术
    """求值 `$(( … ))`。"""
    类型=表达式['type']#节点类型
    if 类型=='number':#字面数
        return 表达式['value']#返回
    if 类型=='variable':#变量转整数
        原始=读变量(状态,表达式['name'])#读值
        try:#解析
            return int(原始 if 原始 is not None else '0',10) or 0#转整数
        except ValueError:#非法
            return 0#零
    if 类型=='addition':#加
        return 算术(表达式['left'],状态)+算术(表达式['right'],状态)#加
    if 类型=='subtraction':#减
        return 算术(表达式['left'],状态)-算术(表达式['right'],状态)#减
    if 类型=='multiplication':#乘
        return 算术(表达式['left'],状态)*算术(表达式['right'],状态)#乘
    if 类型=='division':#整除
        return int(数学.trunc(算术(表达式['left'],状态)/算术(表达式['right'],状态)))#整除
    raise Exception(f'webworker shell: unknown arithmetic type {类型}')#未知

def 段匹配器(段):#编译段匹配器
    """对齐 picomatch(segment, { dot: segment.startsWith('.') })。"""
    点文件=段.startswith('.')#模式以点开头则匹配点文件
    def 匹配(名称):#匹配函数
        """对照子项名。"""
        if not 点文件 and 名称.startswith('.'):#默认忽略点文件
            return False#不匹配
        return 文件名匹配.fnmatch(名称,段)#通配匹配
    return 匹配#返回

def 展开glob(模式,工作目录,文件系统):#展开glob
    """一次一个路径段地对照文件系统展开一个 glob。"""
    绝对=模式.startswith('/')#是否绝对模式
    段们=[段 for 段 in 模式.split('/') if 段!='']#路径段
    def 安全列出(路径):#安全列目录
        """列表失败在此吸收。"""
        try:#尝试
            return 文件系统['list'](路径)#列出
        except Exception:#失败
            return []#无匹配贡献
    前沿=[{'path':'/' if 绝对 else 工作目录,'display':'/' if 绝对 else ''}]#起始前沿
    for 索引,段 in enumerate(段们):#逐段
        末段=索引==len(段们)-1#是否末段
        下一代=[]#下一代前沿
        for 条目 in 前沿:#逐前沿
            if 段=='**':#递归段
                栈=[条目]#DFS栈
                while len(栈)>0:#遍历子树
                    当前=栈.pop()#弹出当前
                    下一代.append(当前)#收入下一代
                    for 子 in 安全列出(当前['path']):#子项
                        if 子['directory']:#仅目录
                            栈.append({'path':解析路径(当前['path'],子['name']),'display':f"{当前['display']}{子['name']}/"})#入栈
                continue#下一段
            if not 是否glob模式(段):#字面段
                路径=解析路径(条目['path'],段)#拼路径
                if 文件系统['stat'](路径) is None:#不存在则跳过
                    continue#跳过
                下一代.append({'path':路径,'display':f"{条目['display']}{段}{'' if 末段 else '/'}"})#收入
                continue#下一段
            匹配=段匹配器(段)#编译匹配器
            for 子 in 安全列出(条目['path']):#对照子项
                if not 匹配(子['name']):#名不匹配
                    continue#跳过
                if not 末段 and not 子['directory']:#非末段需目录
                    continue#跳过
                下一代.append({'path':解析路径(条目['path'],子['name']),'display':f"{条目['display']}{子['name']}{'' if 末段 else '/'}"})#收入
        前沿=下一代#推进前沿
    # `**` 前沿自带展开留下的尾随分隔符；shell 报告目录匹配时不带。
    去重=sorted({条目['display'].rstrip('/') for 条目 in 前沿 if 条目['display'].rstrip('/')!=''})#去重排序
    return 去重#匹配列表

def 展开变量(片段,上下文):#展开变量片段
    """解析一个 `${name}` 片段，含其 `:-` 与 `:+` 备选。"""
    值=读变量(上下文['state'],片段['name'])#读当前值
    已设=值 is not None and 值!=''#是否已设置非空
    if not 已设 and 片段.get('defaultValue') is not None:#:-默认
        return 拼接参数(片段['defaultValue'],上下文)#默认
    if 已设 and 片段.get('alternativeValue') is not None:#:+备选
        return 拼接参数(片段['alternativeValue'],上下文)#备选
    return 值 if 值 is not None else ''#原值或空

def 拼接参数(操作数,上下文):#拼接操作数
    """展开 `:-` / `:+` 操作数，其本身是参数列表。"""
    片=[]#片段缓冲
    for 参数 in 操作数:#逐参数
        片.extend(展开参数(参数,上下文))#展开并收集
    return ' '.join(片)#空格拼接

def 展开参数(参数,上下文):#展开参数
    """将一个参数展开为字段。"""
    字段们=[]#字段缓冲
    # `None` 表示「尚未开始字段」：未设置的未加引号变量必须贡献无，而非空参数。
    当前=None#当前字段
    def 追加(文本):#追加到当前字段
        """追加文本。"""
        nonlocal 当前#字段
        当前=('' if 当前 is None else 当前)+文本#追加
    def 追加拆分(文本):#空白拆分追加
        """未加引号按空白拆。"""
        nonlocal 当前#字段
        片们=正则.split(r'\s+',文本)#按空白切
        for 索引,片 in enumerate(片们):#逐片
            if 索引>0:#非首片开启新字段
                if 当前 is not None:#落定当前
                    字段们.append(当前)#落入
                当前=None#清空
            if 片!='':#非空则追加
                追加(片)#追加
    for 片段 in 参数['segments']:#逐片段
        类型=片段['type']#片段类型
        if 类型=='text':#字面
            追加(片段['text'])#追加文本
        elif 类型=='arithmetic':#算术
            追加(str(算术(片段['arithmetic'],上下文['state'])))#追加结果
        elif 类型=='variable':#变量
            值=展开变量(片段,上下文)#展开变量
            if 片段.get('quoted'):#加引号不拆
                追加(值)#追加
            else:#未加引号拆分
                追加拆分(值)#拆分
        elif 类型=='shell':#命令替换
            输出=上下文['substitute'](片段['shell'])#跑嵌套
            if 片段.get('quoted'):#加引号不拆
                追加(输出)#追加
            else:#未加引号拆分
                追加拆分(输出)#拆分
        elif 类型=='glob':#glob
            匹配们=展开glob(片段['pattern'],上下文['state']['cwd'],上下文['fs'])#匹配
            if len(匹配们)==0:#无匹配
                # 无匹配：POSIX shell 原样传递模式。
                追加(片段['pattern'])#原样传递
            else:#有匹配
                for 索引,匹配 in enumerate(匹配们):#逐匹配
                    if 索引>0:#非首匹配新字段
                        字段们.append(当前)#落定
                        当前=None#清空
                    追加(匹配)#追加匹配
    if 当前 is not None:#落定末字段
        字段们.append(当前)#落入
    return 字段们#返回字段
