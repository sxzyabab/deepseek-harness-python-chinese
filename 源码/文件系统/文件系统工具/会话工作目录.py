'文件系统调用的当前目录与取消信号。非智能体调用不设目录，交给提供方默认'

def 会话解析选项(上下文,执行):
    '解析此次调用的当前目录与取消信号。执行是 dict'
    智能体=执行['agent'] if 'agent' in 执行 else None#调用方智能体
    if 智能体 is None:#非智能体
        工作目录=None#不设目录
    else:#有智能体
        工作目录=上下文.workingDirectory.ensure(智能体,执行['signal'] if 'signal' in 执行 else None)#目录消失时回到原项目
    选项={'signal':执行['signal'] if 'signal' in 执行 else None}#取消信号
    if 工作目录 is not None:#有目录
        选项['cwd']=工作目录#解析用的当前目录
    return 选项#解析选项
