"""通过 ctx.shell 执行命令钩子，复用它的凭证擦除、进程组取消和超时机制。桥接层提供受信任的 stdin 载荷和方言环境，本模块再解码捕获到的结果。"""
import json#序列化 stdin 载荷
from .编解码 import 解析钩子输出#钩子输出解码

默认钩子超时毫秒=600000#单条钩子的参考默认超时（10 分钟）
运行选项=dict#一次钩子执行的选项字段
运行结果=dict#一次钩子执行的返回字段

def 读文本(捕获):
    """从已收集输出映射取出 text。捕获是命令包返回的 dict。"""
    if 捕获 is None:#缺席
        return ''#空串
    if 'text' not in 捕获:#无 text 键
        return ''#空串
    文本=捕获['text']#取出 text
    return 文本 if isinstance(文本,str) else ''#必须是字符串

def 执行钩子(外壳,钩子,选项,现在):
    """用序列化 stdin 执行钩子并解码其结果。钩子自己的秒级超时覆盖默认值；基础设施拒绝会变成没有退出码的结果，因此本函数从不抛出。现在() 返回单调纳秒。钩子与选项都是 dict。"""
    开始=现在()#记下开始时刻
    if 'timeoutSec' in 钩子:#有秒级超时则换算
        超时毫秒=int(钩子['timeoutSec']*1000)#秒数改毫秒
    else:
        超时毫秒=选项['defaultTimeoutMs']#配置未设超时时的默认毫秒
    换行=选项['trailingNewline'] if 'trailingNewline' in 选项 else False#是否追加末尾换行
    载荷文本=json.dumps(选项['payload'],ensure_ascii=False,separators=(',',':'),allow_nan=False)#序列化载荷
    if 换行 is True:#按方言决定是否加换行
        载荷文本=载荷文本+'\n'#追加换行
    请求={'command':钩子['command'],'timeoutMs':超时毫秒,'stdin':载荷文本}#组装 shell 请求
    if 'signal' in 选项 and 选项['signal'] is not None:#有取消信号才写入
        请求['signal']=选项['signal']#写入
    if 'cwd' in 选项 and 选项['cwd'] is not None:#有工作目录才写入
        请求['workdir']=选项['cwd']#写入
    if 'env' in 选项 and 选项['env'] is not None:#有额外环境才写入
        请求['env']=选项['env']#写入
    期望事件名=选项['expectedEventName'] if 'expectedEventName' in 选项 else None#事件名守卫
    try:
        结果=外壳.运行(外壳.解析(请求))#解析请求并执行命令，同步返回 dict
        退出码=结果['exitCode'] if 'exitCode' in 结果 else None#取出退出码；信号死亡则没有
        return {#组装执行结果
            'output':解析钩子输出(退出码,读文本(结果['stdout'] if 'stdout' in 结果 else None),读文本(结果['stderr'] if 'stderr' in 结果 else None),期望事件名),#解码捕获输出
            'durationMs':(现在()-开始)//1000000,#单调纳秒改墙钟毫秒
        }#执行结果对象
    except Exception as 错误:
        #命令包异常基类随 bash/powershell 实现变化，契约未钉死到单一类型；基础设施拒绝必须变成非阻断结果
        消息=str(错误)#取出失败文案
        return {#组装失败结果
            'output':解析钩子输出(None,'',消息),#无退出码，失败文案当 stderr
            'durationMs':(现在()-开始)//1000000,#仍报告墙钟毫秒
        }#失败结果对象
