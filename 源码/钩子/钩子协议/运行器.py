"""通过 ctx.shell 执行命令钩子，复用它的凭证擦除、进程组取消和超时机制。桥接层提供受信任的 stdin 载荷和方言环境，本模块再解码捕获到的结果。"""
import json#序列化 stdin 载荷
from cordis.工具 import 是否thenable#可等待判定
from .编解码 import 解析钩子输出#钩子输出解码

默认钩子超时毫秒=600000#单条钩子的参考默认超时（10 分钟）
运行选项=dict#一次钩子执行的选项字段
运行结果=dict#一次钩子执行的返回字段

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 读文本(捕获):#读已收集输出的 text
    """从 CollectedOutput 或映射取出 text。"""
    if 捕获 is None:#缺席
        return ''#空串
    文本=取字段(捕获,'text')#取出 text
    return 文本 if isinstance(文本,str) else ''#必须是字符串

def 跑钩子(外壳,钩子,选项,现在):#执行一条命令钩子
    """用序列化 stdin 跑钩子并解码其结果。钩子自己的秒级超时覆盖默认值；基础设施拒绝会变成没有退出码的结果，因此本函数从不抛出。"""
    开始=现在()#记下开始时刻
    超时秒=取字段(钩子,'timeoutSec')#单条超时秒
    if 超时秒 is not None:#有秒级超时则换算
        超时毫秒=超时秒*1000#换算毫秒
    else:#否则用默认
        超时毫秒=取字段(选项,'defaultTimeoutMs')#配置未设超时时的默认毫秒
    换行=取字段(选项,'trailingNewline')#是否追加末尾换行
    载荷文本=json.dumps(取字段(选项,'payload'),ensure_ascii=False,separators=(',',':'))#序列化载荷
    if 换行:#按方言决定是否加换行
        载荷文本=载荷文本+'\n'#追加换行
    请求={'command':取字段(钩子,'command'),'timeoutMs':超时毫秒,'stdin':载荷文本,'signal':取字段(选项,'signal')}#组装 shell 请求
    工作目录=取字段(选项,'cwd')#工作目录
    if 工作目录 is not None:#有工作目录才写入
        请求['workdir']=工作目录#写入
    环境=取字段(选项,'env')#额外环境
    if 环境 is not None:#有额外环境才写入
        请求['env']=环境#写入
    try:#执行命令并解码
        解析=getattr(外壳,'resolve',None) or getattr(外壳,'解析',None)#解析请求
        运行=getattr(外壳,'run',None) or getattr(外壳,'运行',None)#跑命令
        结果=解开(运行(解析(请求)))#解析请求并跑命令
        退出码=取字段(结果,'exitCode')#取出退出码
        if 退出码 is None:#信号死亡则没有退出码
            退出码=None#保持缺席
        return {#组装执行结果
            'output':解析钩子输出(退出码,读文本(取字段(结果,'stdout')),读文本(取字段(结果,'stderr')),取字段(选项,'expectedEventName')),#解码捕获输出
            'durationMs':现在()-开始,#墙钟时长
        }#执行结果对象
    except Exception as 错误:#吞掉基础设施故障，变成非阻断结果
        #执行器只在基础设施故障时拒绝。钩子跑不起来是非阻断错误：没有退出码，失败信息进 stderr。
        消息=str(错误)#取出失败文案
        return {#组装失败结果
            'output':解析钩子输出(None,'',消息),#无退出码，失败文案当 stderr
            'durationMs':现在()-开始,#仍报告墙钟时长
        }#失败结果对象
