"""解释器：遍历已解析命令行，对照 VFS 运行命令表。结构（`;` `&` `|` `|&`
`&&` `||`、子 shell、分组、重定向、前缀赋值）在此兑现；命令*做什么*
属于 `programs/` 中的程序。

输出是文本而非流：每个程序都是返回后才运行下一个的函数，
因此管道沿路传递字符串，而非浏览器 worker 无法在其间调度的字节流。

对齐上游 `webworker-runtime/src/shell/interpret.ts`。公开面仅中文名。
"""
import re as 正则#剥尾换行
from .展开 import 展开参数,是否glob模式#展开
from .文件系统访问 import 描述失败,宿主文件系统,在目录解析#FS辅助
from .programs import 标准程序#命令表

__all__=['运行shell命令','运行shell程序']#仅中文公开名

中止退出码=130#调用方abort信号已触发后命令行报告的状态
未找到退出码=127#表中不持有的命令名所报告的状态
替换嵌套上限=16#`$( … )` 的嵌套上限

def 解析shell(源,选项):#对齐上游 @yarnpkg/parsers.parseShell
    """解析命令源为 AST。实现由宿主绑定 yarnpkg parsers，本批次不迁解析器。"""
    raise NotImplementedError('@yarnpkg/parsers.parseShell')#外部依赖

def 缓冲汇():#创建字符串缓冲汇
    """覆盖字符串缓冲的汇，供管道与命令替换使用。"""
    块们=[]#块收集
    def 写入(文本):#追加块
        """追加文本。"""
        块们.append(文本)#追加
    def 文本():#拼接全文
        """取全文。"""
        return ''.join(块们)#拼接
    return {'write':写入,'text':文本}#汇对象

def 启动运行(选项):#构建运行上下文
    """构建状态、汇，以及一次运行经其报告的落定。"""
    标准输出=缓冲汇()#标准输出缓冲
    标准错误=缓冲汇()#标准错误缓冲
    报告=选项.get('onOutput')#可选增量回调
    def 写stdout(文本):#写stdout
        """缓冲并报告。"""
        标准输出['write'](文本)#缓冲
        if 报告 is not None:#增量报告
            报告('stdout',文本)#回调
    def 写stderr(文本):#写stderr
        """缓冲并报告。"""
        标准错误['write'](文本)#缓冲
        if 报告 is not None:#增量报告
            报告('stderr',文本)#回调
    def 落定(退出码):#组装结果
        """落定结果。"""
        return {'exitCode':退出码,'stdout':标准输出['text'](),'stderr':标准错误['text']()}#结果
    return {#组装
        'state':{#初始状态
            'cwd':选项['cwd'],#工作目录
            'environment':dict(选项['env']),#环境副本
            'variables':{},#空变量
            'lastStatus':0,#初始退出码
            'exitRequested':None,#未请求退出
            'signal':选项.get('signal'),#取消信号
        },#state结束
        'io':{#字节面
            'stdin':选项.get('stdin') or '',#标准输入
            'out':写stdout,#写stdout
            'err':写stderr,#写stderr
        },#io结束
        'settle':落定,#落定函数
    }#return结束

def 记录赋值(状态,名,值):#记录赋值
    """已导出名称保持其导出；其他一切留为 shell 变量。"""
    if 名 in 状态['environment']:#更新环境
        状态['environment'][名]=值#写环境
    else:#写入shell变量
        状态['variables'][名]=值#写变量

def 运行shell命令(源,选项):#运行命令行
    """将一行 shell 命令运行至完成。"""
    运行=启动运行(选项)#启动运行上下文
    try:#解析源
        行=解析shell(源,{'isGlobPattern':是否glob模式})#解析为AST
    except Exception as 错误:#语法错误
        消息=str(错误).split('\n')[0]#首行
        运行['io']['err'](f'bash: syntax error: {消息}\n')#报告首行
        return 运行['settle'](2)#语法失败码
    机=解释器(标准程序(),选项.get('fs') or 宿主文件系统(),选项.get('signal'))#建解释器
    return 运行['settle'](机.行(行,运行['state'],运行['io']))#解释并落定

def 运行shell程序(argv,选项):#直接运行程序
    """直接运行一个程序，无需解析命令行。"""
    运行=启动运行(选项)#启动运行上下文
    名=argv[0] if len(argv)>0 else None#程序名
    程序=None if 名 is None else 标准程序().get(名)#查表
    if 名 is None or 程序 is None:#未找到
        运行['io']['err'](f"bash: {名 if 名 is not None else ''}: command not found\n")#报告
        return 运行['settle'](未找到退出码)#127
    信号=选项.get('signal')#取消信号
    if 信号 is not None and 信号.get('aborted') is True:#已中止
        return 运行['settle'](中止退出码)#130
    try:#执行
        return 运行['settle'](程序(argv,运行['io'],运行['state'],选项.get('fs') or 宿主文件系统()))#落定结果
    except Exception as 错误:#程序缺陷
        运行['io']['err'](f'bash: {名}: {错误}\n')#诊断
        return 运行['settle'](1)#失败码

class 解释器:#解释器
    """一次解释通行；持有每个嵌套命令共享的内容。"""
    def __init__(自身,程序表,文件系统,信号,深度=0):#构造
        """记下命令表、文件系统、取消信号与替换深度。"""
        自身.程序表=程序表#命令表
        自身.文件系统=文件系统#文件系统
        自身.信号=信号#取消信号
        自身.深度=深度#替换深度

    def 行(自身,行,状态,io):#解释一行
        """从左到右运行一行的每条命令。"""
        状态码=状态['lastStatus']#当前状态
        for 项 in 行:#逐命令项
            if 自身.信号 is not None and 自身.信号.get('aborted') is True:#已中止
                return 中止退出码#130
            # `&` 在此不启动后台作业：worker 没有能运行它的调度器，因此后台命令就地运行至完成。
            状态码=自身.命令行(项['command'],状态,io)#跑命令行
            状态['lastStatus']=状态码#更新$?
            if 状态['exitRequested'] is not None:#exit请求
                return 状态['exitRequested']#退出
        return 状态码#末状态

    def 命令行(自身,命令行节点,状态,io):#求值&&/||链
        """运行一条 `&&` / `||` 链。"""
        链接们=[]#展平链接
        当前=命令行节点.get('then')#首then
        while 当前 is not None:#沿then走
            链接们.append({'type':当前['type'],'chain':当前['line']['chain']})#收集链接
            当前=当前['line'].get('then')#推进
        状态码=自身.管道(命令行节点['chain'],状态,io)#首段管道
        状态['lastStatus']=状态码#更新状态
        for 链接 in 链接们:#逐链接
            if 状态['exitRequested'] is not None:#exit中断
                return 状态码#中断
            if (状态码!=0 if 链接['type']=='&&' else 状态码==0):#短路跳过
                continue#跳过
            状态码=自身.管道(链接['chain'],状态,io)#跑下一段
            状态['lastStatus']=状态码#更新
        return 状态码#链末状态

    def 管道(自身,链,状态,io):#求值管道
        """运行一条 `|` / `|&` 管道；其状态是最后一阶段的。"""
        阶段们=[]#阶段列表
        当前=链#起点
        while 当前 is not None:#展平管道
            链接=当前.get('then')#下一链接
            阶段们.append({'command':当前,'mergesStderr':链接 is not None and 链接.get('type')=='|&'})#记阶段
            当前=None if 链接 is None else 链接.get('chain')#推进
        输入=io['stdin']#管道输入
        状态码=0#阶段状态
        for 索引,阶段 in enumerate(阶段们):#逐阶段
            if 自身.信号 is not None and 自身.信号.get('aborted') is True:#已中止
                return 中止退出码#130
            末段=索引==len(阶段们)-1#是否末段
            中间=缓冲汇()#中间缓冲
            if 末段:#末段用外层汇
                阶段io={'stdin':输入,'out':io['out'],'err':io['err']}#直通
            else:#管道或合并
                阶段io={'stdin':输入,'out':中间['write'],'err':中间['write'] if 阶段['mergesStderr'] else io['err']}#汇
            状态码=自身.命令(阶段['command'],状态,阶段io)#跑阶段
            if not 末段:#传给下一段
                输入=中间['text']()#管道文本
            if 状态['exitRequested'] is not None:#exit中断
                return 状态码#中断
        return 状态码#末阶段状态

    def 命令(自身,命令,状态,io):#跑命令节点
        """运行一个命令节点：程序调用、子 shell、分组，或裸赋值。"""
        类型=命令['type']#节点类型
        if 类型=='envs':#裸赋值
            for 环境 in 命令['envs']:#逐项赋值
                右=环境['args'][0] if 环境.get('args') and len(环境['args'])>0 else None#右值
                记录赋值(状态,环境['name'],自身.赋值右值(右,状态))#赋值
            return 0#赋值成功
        if 类型=='subshell':#子shell
            嵌套={**状态,'environment':dict(状态['environment']),'variables':dict(状态['variables'])}#状态副本
            def 主体(内层):#带重定向跑
                """跑子shell行。"""
                return 自身.行(命令['subshell'],嵌套,内层)#嵌套行
            return 自身.带重定向(命令.get('args') or [],状态,io,主体)#重定向
        if 类型=='group':#分组
            def 主体(内层):#共享状态
                """跑分组行。"""
                return 自身.行(命令['group'],状态,内层)#共享
            return 自身.带重定向(命令.get('args') or [],状态,io,主体)#重定向
        if 类型=='command':#程序调用
            return 自身.程序调用(命令,状态,io)#跑程序
        raise Exception(f'webworker shell: unknown command type {类型}')#未知

    def 程序调用(自身,命令,状态,io):#跑程序调用
        """展开命令的词并运行它们所指名的程序。"""
        argv=[]#参数向量
        重定向们=[]#重定向列表
        for 参数 in 命令.get('args') or []:#拆参数
            if 参数.get('type')=='redirection':#重定向
                重定向们.append(参数)#收集
                continue#下一参数
            argv.extend(展开参数(参数,自身.上下文(状态)))#展开入argv
        前缀={}#前缀环境
        for 环境 in 命令.get('envs') or []:#收集前缀赋值
            右=环境['args'][0] if 环境.get('args') and len(环境['args'])>0 else None#右值
            前缀[环境['name']]=自身.赋值右值(右,状态)#赋值
        if len(argv)==0:#仅赋值
            for 名,值 in 前缀.items():#写入状态
                记录赋值(状态,名,值)#赋值
            return 0#成功
        if len(前缀)==0:#无前缀用原状态
            作用域=状态#共享
        else:#前缀环境副本
            作用域={**状态,'environment':{**状态['environment'],**前缀}}#副本
        名=argv[0]#程序名
        程序=自身.程序表.get(名)#查表
        if 程序 is None:#未找到
            io['err'](f'bash: {名}: command not found\n')#诊断
            return 未找到退出码#127
        def 主体(内层):#带重定向跑
            """执行程序。"""
            try:#执行程序
                return 程序(argv,内层,作用域,自身.文件系统)#返回退出码
            except Exception as 错误:#程序缺陷
                内层['err'](f'bash: {名}: {错误}\n')#诊断
                return 1#失败
        return 自身.带重定向(重定向们,状态,io,主体)#redirected

    def 带重定向(自身,重定向们,状态,io,主体):#应用重定向
        """在一个主体周围应用重定向，然后什么也不恢复。"""
        stdin=io['stdin']#当前stdin
        out=io['out']#当前stdout
        err=io['err']#当前stderr
        for 重定向 in 重定向们:#逐重定向
            目标们=[]#展开目标
            for 参数 in 重定向.get('args') or []:#展开
                目标们.extend(展开参数(参数,自身.上下文(状态)))#展开
            目标=目标们[0] if len(目标们)>0 else None#首目标
            if 目标 is None or len(目标们)>1:#歧义
                io['err']('bash: ambiguous redirect\n')#诊断
                return 1#失败
            try:#应用一种重定向
                子类型=重定向.get('subtype')#子类型
                if 子类型=='<':#读入
                    stdin=自身.文件系统['readText'](在目录解析(状态['cwd'],目标))#读文件为stdin
                elif 子类型=='<<<':#here-string
                    stdin=f'{目标}\n'#字面加换行
                elif 子类型 in ('>','>>'):#截断写或追加写
                    路径=在目录解析(状态['cwd'],目标)#绝对路径
                    if 子类型=='>':#先截断
                        自身.文件系统['writeText'](路径,'')#截断
                    def 文件汇(文本,路径=路径):#文件汇
                        """串行追加。"""
                        自身.文件系统['writeText'](路径,文本,True)#串行追加
                    if 重定向.get('fd')==2:#stderr
                        err=文件汇#挂stderr
                    else:#stdout
                        out=文件汇#挂stdout
                elif 子类型=='>&':#描述符复制
                    if 重定向.get('fd')==2 and 目标=='1':#2>&1
                        err=out#复制
                    elif (重定向.get('fd') is None or 重定向.get('fd')==1) and 目标=='2':#1>&2
                        out=err#复制
                    else:#不支持
                        描述符=重定向.get('fd') if 重定向.get('fd') is not None else 1#描述符
                        io['err'](f'bash: {描述符}>&{目标}: unsupported descriptor redirection\n')#诊断
                        return 1#失败
                elif 子类型=='<&':#不支持
                    io['err'](f'bash: <&{目标}: unsupported descriptor redirection\n')#诊断
                    return 1#失败
            except Exception as 错误:#文件系统失败
                io['err'](f"{描述失败('bash',在目录解析(状态['cwd'],目标),错误)}\n")#诊断
                return 1#失败
        return 主体({'stdin':stdin,'out':out,'err':err})#跑主体

    def 上下文(自身,状态):#构建展开上下文
        """展开钩子：`$( … )` 在同一表的嵌套解释器上运行。"""
        def 命令替换(shell行):#命令替换
            """跑嵌套并剥尾换行。"""
            if 自身.深度>=替换嵌套上限:#过深
                raise Exception(f'command substitution nested deeper than {替换嵌套上限} levels')#拒绝
            捕获=缓冲汇()#捕获输出
            嵌套={**状态,'environment':dict(状态['environment']),'variables':dict(状态['variables'])}#副本
            内层=解释器(自身.程序表,自身.文件系统,自身.信号,自身.深度+1)#嵌套解释器
            def 吞stderr(文本):#忽略stderr
                """丢弃。"""
                return None#无
            内层.行(shell行,嵌套,{'stdin':'','out':捕获['write'],'err':吞stderr})#跑嵌套
            return 正则.sub(r'\n+$','',捕获['text']())#剥尾换行
        return {'state':状态,'fs':自身.文件系统,'substitute':命令替换}#上下文

    def 赋值右值(自身,参数,状态):#展开赋值右值
        """展开一次 `NAME=value` 赋值的右侧。"""
        if 参数 is None:#空右值
            return ''#空
        return ' '.join(展开参数(参数,自身.上下文(状态)))#字段空格拼接
