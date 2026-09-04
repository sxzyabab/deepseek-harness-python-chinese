"""命令表的文本工具。每个都将操作数读为文件，并在空时回退到标准输入，
与其 POSIX 对应物一样。

对齐上游 `webworker-runtime/src/shell/programs/text.ts`。公开面仅中文名。
"""
import re as 正则#正则与转义
from ..文件系统访问 import 描述失败,在目录解析#FS辅助
from .选项 import 数值选项,解析选项,拆成行#选项工具

__all__=['文本程序']#仅中文公开名

def 读各输入(程序,操作数,io,state,fs):#读各输入源
    """将每个操作数读为文件，报告失败者。"""
    if len(操作数)==0:#空则stdin
        return {'sources':[{'name':'-','text':io['stdin']}],'status':0}#stdin
    源们=[]#源缓冲
    状态=0#累积状态
    for 操作数名 in 操作数:#逐操作数
        if 操作数名=='-':#stdin记号
            源们.append({'name':'-','text':io['stdin']})#收录stdin
            continue#下一操作数
        路径=在目录解析(state['cwd'],操作数名)#绝对路径
        try:#尝试读
            源们.append({'name':操作数名,'text':fs['readText'](路径)})#收录文件
        except Exception as 错误:#失败
            io['err'](f'{描述失败(程序,操作数名,错误)}\n')#诊断
            状态=1#失败
    return {'sources':源们,'status':状态}#返回

def 确保尾换行(文本):#确保尾换行
    """追加尾随换行，除非文本已以换行结尾。"""
    return 文本 if 文本=='' or 文本.endswith('\n') else f'{文本}\n'#补换行

def echo程序(argv,io,state=None,fs=None):#echo程序
    """打印参数。"""
    抑制换行=len(argv)>1 and argv[1]=='-n'#是否-n
    词们=argv[2 if 抑制换行 else 1:]#输出词
    io['out'](f"{' '.join(词们)}{'' if 抑制换行 else chr(10)}")#打印
    return 0#成功

def printf程序(argv,io,state=None,fs=None):#printf程序
    """格式化打印。"""
    格式=argv[1] if len(argv)>1 else ''#格式串
    操作数=argv[2:]#操作数
    游标=[0]#消费游标
    def 替换(匹配):#替换转换
        """shell 脚本现实会用到的转换。"""
        记号=匹配.group(0)#匹配文本
        if 记号=='%%':#百分号
            return '%'#百分号
        值=操作数[游标[0]] if 游标[0]<len(操作数) else ''#取值
        游标[0]+=1#推进
        if 记号=='%s':#字符串
            return 值#字符串
        try:#解析整数
            已解析=int(值,10)#解析
        except ValueError:#非法
            已解析=0#零
        return str(已解析)#数值
    已渲染=正则.sub(r'%[sdi%]',替换,格式)#替换转换
    io['out'](已渲染.replace('\\n','\n').replace('\\t','\t'))#转义输出
    return 0#成功

def cat程序(argv,io,state,fs):#cat程序
    """连接文件。"""
    选项=解析选项(argv)#解析选项
    结果=读各输入('cat',选项['operands'],io,state,fs)#读源
    行号=1#行号
    for 源 in 结果['sources']:#逐源
        if 'n' not in 选项['flags']:#无编号
            io['out'](源['text'])#原文输出
            continue#下一源
        for 内容 in 拆成行(源['text']):#逐行
            io['out'](f"{str(行号).rjust(6)}\t{内容}\n")#编号行
            行号+=1#推进行号
    return 结果['status']#返回状态

def head程序(argv,io,state,fs):#head程序
    """前N行。"""
    选项=解析选项(argv,{'n'})#解析带n
    行数=数值选项(选项,'n',10)#行数
    结果=读各输入('head',选项['operands'],io,state,fs)#读源
    for 索引,源 in enumerate(结果['sources']):#逐源
        if len(结果['sources'])>1:#多源标题
            io['out'](f"{chr(10) if 索引>0 else ''}==> {源['name']} <==\n")#标题
        io['out'](确保尾换行('\n'.join(拆成行(源['text'])[:行数])))#前N行
    return 结果['status']#返回状态

def tail程序(argv,io,state,fs):#tail程序
    """后N行。"""
    选项=解析选项(argv,{'n'})#解析带n
    行数=数值选项(选项,'n',10)#行数
    结果=读各输入('tail',选项['operands'],io,state,fs)#读源
    for 索引,源 in enumerate(结果['sources']):#逐源
        if len(结果['sources'])>1:#多源标题
            io['out'](f"{chr(10) if 索引>0 else ''}==> {源['name']} <==\n")#标题
        io['out'](确保尾换行('\n'.join(拆成行(源['text'])[-行数:])))#后N行
    return 结果['status']#返回状态

def wc程序(argv,io,state,fs):#wc程序
    """计行词字符。"""
    选项=解析选项(argv)#解析选项
    结果=读各输入('wc',选项['operands'],io,state,fs)#读源
    所选=[旗 for 旗 in ('l','w','c') if 旗 in 选项['flags']]#所选列
    列们=所选 if len(所选)>0 else ['l','w','c']#默认全列
    for 源 in 结果['sources']:#逐源
        计数={#计数
            'l':len(拆成行(源['text'])),#行数
            'w':len([词 for 词 in 正则.split(r'\s+',源['text']) if 词!='']),#词数
            'c':len(源['text']),#字符数
        }#counts结束
        单元格=[str(计数.get(列,0)).rjust(8 if len(列们)>1 else 1) for 列 in 列们]#对齐单元格
        后缀='' if 源['name']=='-' else f" {源['name']}"#文件名
        io['out'](f"{' '.join(单元格)}{后缀}\n")#打印
    return 结果['status']#返回状态

def 遍历文件(路径,显示,收集,fs):#递归收集文件
    """收集一个目录下的每个文件，供 `grep -r`。"""
    for 条目 in fs['list'](路径):#逐条目
        子=f"{路径 if 路径.endswith('/') else 路径+'/'}{条目['name']}"#子路径
        示=f"{显示 if 显示.endswith('/') else 显示+'/'}{条目['name']}"#显示名
        if 条目['directory']:#递归目录
            遍历文件(子,示,收集,fs)#递归
        else:#收录文件
            收集.append({'path':子,'display':示})#收录

def grep程序(argv,io,state,fs):#grep程序
    """搜索文本。"""
    选项=解析选项(argv,{'e'})#解析带e
    模式=选项['values'].get('e',选项['operands'][0] if len(选项['operands'])>0 else None)#模式
    目标们=选项['operands'] if 'e' in 选项['values'] else 选项['operands'][1:]#目标
    if 模式 is None:#缺模式
        io['err']('grep: no pattern given\n')#诊断
        return 2#用法错
    源模式=正则.escape(模式) if 'F' in 选项['flags'] else 模式#字面或正则
    try:#编译
        匹配器=正则.compile(源模式,正则.I if 'i' in 选项['flags'] else 0)#建正则
    except 正则.error as 错误:#非法
        io['err'](f'grep: invalid pattern: {错误}\n')#诊断
        return 2#用法错
    源们=[]#源缓冲
    状态码=0#累积状态
    if len(目标们)==0:#无目标用stdin
        源们.append({'name':'','text':io['stdin']})#收录stdin
    else:#有目标
        for 目标 in 目标们:#逐目标
            路径=在目录解析(state['cwd'],目标)#绝对路径
            统计=fs['stat'](路径)#查询
            if 统计 is not None and 统计['directory'] is True:#目录
                if 'r' not in 选项['flags'] and 'R' not in 选项['flags']:#未递归
                    io['err'](f'grep: {目标}: Is a directory\n')#诊断
                    状态码=max(状态码,2)#抬高状态
                    continue#下一目标
                文件们=[]#文件列表
                遍历文件(路径,目标,文件们,fs)#收集
                for 文件 in 文件们:#读入
                    源们.append({'name':文件['display'],'text':fs['readText'](文件['path'])})#收录
                continue#下一目标
            try:#读文件
                源们.append({'name':目标,'text':fs['readText'](路径)})#收录
            except Exception as 错误:#失败
                io['err'](f'{描述失败("grep",目标,错误)}\n')#诊断
                状态码=max(状态码,2)#抬高状态
    贴名=len(源们)>1 or 'H' in 选项['flags']#是否贴文件名
    有匹配=False#是否有匹配
    for 条目 in 源们:#逐源
        命中们=[]#命中行
        for 序号,行文 in enumerate(拆成行(条目['text'])):#分行
            命中=匹配器.search(行文) is not None#是否匹配
            if 命中==('v' not in 选项['flags']):#匹配或反选
                命中们.append({'text':行文,'number':序号+1})#收录
        if len(命中们)>0:#记有匹配
            有匹配=True#有
        if 'l' in 选项['flags']:#仅文件名
            if len(命中们)>0:#有命中
                io['out'](f"{条目['name']}\n")#打印名
            continue#下一源
        if 'c' in 选项['flags']:#计数
            前=f"{条目['name']}:" if 贴名 and 条目['name']!='' else ''#前缀
            io['out'](f"{前}{len(命中们)}\n")#打印计数
            continue#下一源
        for 命中 in 命中们:#逐命中
            名前=f"{条目['name']}:" if 贴名 and 条目['name']!='' else ''#文件前缀
            号前=f"{命中['number']}:" if 'n' in 选项['flags'] else ''#行号前缀
            io['out'](f"{名前}{号前}{命中['text']}\n")#打印行
    return 状态码 if 状态码!=0 else (0 if 有匹配 else 1)#错误或匹配结果

def sort程序(argv,io,state,fs):#sort程序
    """排序行。"""
    选项=解析选项(argv)#解析选项
    结果=读各输入('sort',选项['operands'],io,state,fs)#读源
    行们=[]#合并行
    for 源 in 结果['sources']:#逐源
        行们.extend(拆成行(源['text']))#合并
    if 'n' in 选项['flags']:#数值排序
        def 数值键(行):#键
            """解析浮点。"""
            try:#解析
                return float(行)#浮点
            except ValueError:#非法
                return 0.0#零
        行们=sorted(行们,key=数值键)#数值排
    else:#字典序
        行们=sorted(行们)#字典序
    if 'r' in 选项['flags']:#逆序
        行们.reverse()#逆
    if 'u' in 选项['flags']:#去重
        见过=[]#保序去重
        for 行 in 行们:#逐行
            if 行 not in 见过:#未见
                见过.append(行)#收录
        行们=见过#替换
    io['out'](确保尾换行('\n'.join(行们)))#输出
    return 结果['status']#返回状态

def uniq程序(argv,io,state,fs):#uniq程序
    """相邻去重。"""
    选项=解析选项(argv)#解析选项
    结果=读各输入('uniq',选项['operands'],io,state,fs)#读源
    行们=[]#合并行
    for 源 in 结果['sources']:#逐源
        行们.extend(拆成行(源['text']))#合并
    组们=[]#相邻组
    for 行 in 行们:#逐行
        if len(组们)>0 and 组们[-1]['text']==行:#同文累加
            组们[-1]['count']+=1#累加
        else:#新组
            组们.append({'text':行,'count':1})#新组
    if 'd' in 选项['flags']:#仅重复
        所选=[组 for 组 in 组们 if 组['count']>1]#重复组
    elif 'u' in 选项['flags']:#仅唯一
        所选=[组 for 组 in 组们 if 组['count']==1]#唯一
    else:#全部
        所选=组们#全部
    for 组 in 所选:#逐组
        前=f"{str(组['count']).rjust(7)} " if 'c' in 选项['flags'] else ''#计数前缀
        io['out'](f"{前}{组['text']}\n")#打印
    return 结果['status']#返回状态

def cut程序(argv,io,state,fs):#cut程序
    """切字段或字符。"""
    选项=解析选项(argv,{'d','f','c'})#解析带值标志
    分隔=选项['values'].get('d','\t')#分隔符
    字段们=[]#字段号
    for 字段 in 选项['values'].get('f','').split(','):#拆字段
        try:#解析
            字段们.append(int(字段,10))#收录
        except ValueError:#非法
            pass#跳过
    字符范围=选项['values'].get('c')#字符范围
    结果=读各输入('cut',选项['operands'],io,state,fs)#读源
    if len(字段们)==0 and 字符范围 is None:#缺选择
        io['err']('cut: expected -f or -c\n')#诊断
        return 2#用法错
    for 源 in 结果['sources']:#逐源
        for 行 in 拆成行(源['text']):#逐行
            if 字符范围 is not None:#按字符
                段们=字符范围.split('-')#拆范围
                try:#起点
                    起点=int(段们[0] if 段们[0]!='' else '1',10) or 1#起点
                except ValueError:#非法
                    起点=1#默认
                if len(段们)<2 or 段们[1]=='':#无终点
                    终点=起点#单字符
                else:#有终点
                    try:#解析终点
                        终点=int(段们[1],10)#终点
                    except ValueError:#非法
                        终点=起点#回退
                io['out'](f"{行[起点-1:终点]}\n")#切片
                continue#下一行
            片=行.split(分隔)#按分隔切
            io['out'](f"{分隔.join([片[字段-1] if 0<=字段-1<len(片) else '' for 字段 in 字段们])}\n")#选字段
    return 结果['status']#返回状态

def 字符集(集合):#展开字符集
    """展开一个 `tr` 集合：`a-z` 变成该范围内的每个字符。"""
    字符们=list(集合)#码点列表
    展开=[]#展开缓冲
    索引=0#游标
    while 索引<len(字符们):#逐码点
        起点=字符们[索引]#起点字符
        终点=字符们[索引+2] if 索引+2<len(字符们) else None#终点候选
        if 索引+1<len(字符们) and 字符们[索引+1]=='-' and 终点 is not None:#范围
            for 码 in range(ord(起点),ord(终点)+1):#扫范围
                展开.append(chr(码))#收录
            索引+=3#跳过-与终点
            continue#下一
        展开.append(起点)#单字符
        索引+=1#推进
    return 展开#返回集合

def tr程序(argv,io,state=None,fs=None):#tr程序
    """翻译或删除字符。"""
    选项=解析选项(argv)#解析选项
    源集文=选项['operands'][0] if len(选项['operands'])>0 else None#源集
    目标集文=选项['operands'][1] if len(选项['operands'])>1 else None#目标集
    源=None if 源集文 is None else ''.join(字符集(源集文))#源集
    目标=None if 目标集文 is None else ''.join(字符集(目标集文))#目标集
    if 源 is None:#缺源集
        io['err']('tr: expected a source set\n')#诊断
        return 2#用法错
    if 'd' in 选项['flags']:#删除
        io['out'](''.join([字 for 字 in io['stdin'] if 字 not in 源]))#删后输出
        return 0#成功
    if 目标 is None:#缺替换集
        io['err']('tr: expected a replacement set\n')#诊断
        return 2#用法错
    出=[]#输出缓冲
    for 字 in io['stdin']:#翻译
        位=源.find(字)#源位置
        if 位<0:#原样
            出.append(字)#原样
        else:#映射
            出.append(目标[min(位,len(目标)-1)])#映射
    io['out'](''.join(出))#输出
    return 0#成功

def sed程序(argv,io,state,fs):#sed程序
    """`sed` 仅接受替换命令；其他一切被报告，而非猜测。"""
    选项=解析选项(argv,{'e'})#解析带e
    脚本=选项['values'].get('e',选项['operands'][0] if len(选项['operands'])>0 else None)#脚本
    目标们=选项['operands'] if 'e' in 选项['values'] else 选项['operands'][1:]#目标
    解析=正则.match(r'^s(.)(.*?[^\\])?\1(.*?)\1([gi]*)$',脚本 if 脚本 is not None else '')#解析s命令
    if 解析 is None:#非替换
        io['err']('sed: only substitution scripts (s/pattern/replacement/) run in the worker host\n')#诊断
        return 2#用法错
    模式=解析.group(2) if 解析.group(2) is not None else ''#模式
    替换文=解析.group(3) if 解析.group(3) is not None else ''#替换
    修饰=解析.group(4) if 解析.group(4) is not None else ''#修饰
    旗=正则.I if 'i' in 修饰 else 0#正则旗
    次数=0 if 'g' in 修饰 else 1#全局或单次
    try:#编译
        匹配器=正则.compile(模式,旗)#建正则
    except 正则.error as 错误:#非法
        io['err'](f'sed: invalid pattern: {错误}\n')#诊断
        return 2#用法错
    结果=读各输入('sed',目标们,io,state,fs)#读源
    def 转引用(匹配):#\\n → \\g<n>
        """对齐 JS $$$1。"""
        return f'\\g<{匹配.group(1)}>'#Python反向引用
    js替换=正则.sub(r'\\(\d)',转引用,替换文)#转引用
    for 源 in 结果['sources']:#逐源
        for 行 in 拆成行(源['text']):#逐行
            io['out'](f"{匹配器.sub(js替换,行,count=次数)}\n")#替换输出
    return 结果['status']#返回状态

def tee程序(argv,io,state,fs):#tee程序
    """透传并写文件。"""
    选项=解析选项(argv)#解析选项
    io['out'](io['stdin'])#透传stdout
    for 操作数 in 选项['operands']:#逐文件
        try:#写文件
            fs['writeText'](在目录解析(state['cwd'],操作数),io['stdin'],'a' in 选项['flags'])#写或追加
        except Exception as 错误:#失败
            io['err'](f'{描述失败("tee",操作数,错误)}\n')#诊断
            return 1#失败
    return 0#成功

文本程序={#文本程序表
    'echo':echo程序,#echo
    'printf':printf程序,#printf
    'cat':cat程序,#cat
    'head':head程序,#head
    'tail':tail程序,#tail
    'wc':wc程序,#wc
    'grep':grep程序,#grep
    'sort':sort程序,#sort
    'uniq':uniq程序,#uniq
    'cut':cut程序,#cut
    'tr':tr程序,#tr
    'sed':sed程序,#sed
    'tee':tee程序,#tee
}#文本程序结束
