'Node PTC 的执行模式与资源界限'
import math#有限数
from ...依赖.schemastery import 数字字段,字符串字段,常量字段,复合类型字段#配置字段
from ...工具.超时 import 定时器延迟上限毫秒#定时器上限
from ...基础设施.通用工具.数值判定 import 最大安全整数#安全整数
from .异常 import 节点ptc错误#本包异常

__all__=['配置','校验配置']#仅中文公开名

配置={#部署可变界限与启动选择
    'executionMode':复合类型字段(常量字段('per-call'),常量字段('persistent-in-memory'),默认值='per-call'),#每次新进程或按所有者保留
    'timeoutMs':数字字段(默认值=120_000),#默认经过时间截止
    'maxTimeoutMs':数字字段(默认值=600_000),#解析器接受的数值上限
    'maxOutputBytes':数字字段(默认值=67_108_864),#日志、完成值与诊断合计
    'maxOldGenerationSizeMb':数字字段(默认值=512),#V8 老生代 MiB，不含本机分配
    'maxMessageBytes':数字字段(默认值=134_217_728),#控制帧、未决参数与排队控制输出
    'maxPendingCalls':数字字段(默认值=128),#同时宿主绑定调用
    'graceMs':数字字段(默认值=3_000),#终止与排空宽限
    'launch':复合类型字段(#子进程世界里的工人启动
        {
            'kind':常量字段('node-script'),#单独的可执行文件与引导
            'executable':字符串字段(),#子进程提供方解析的名字或路径
            'bootstrapPath':字符串字段(),#绝对预装引导；缺席则映射本包引导
        },
        {
            'kind':常量字段('embedded'),#打包可执行文件里的私有工人
            'executable':字符串字段(),#打包可执行文件
        },
    ),
}#配置结束

def 是安全整数(值):#Number.isSafeInteger
    '排除布尔；整数必须落在安全范围内'
    if type(值) is not int:#布尔与浮点都不是
        return False#拒绝
    return -最大安全整数<=值<=最大安全整数#安全范围

def 校验配置(配置值):#校验已解析的 Node 界限
    """校验已解析的 Node 界限与路径。
    配置值是加载器填过默认值、并已选定可执行文件的字段
    """
    for 键,值 in 配置值.items():#每个已解析字段
        if type(值) is not bool and isinstance(值,(int,float)) and (not math.isfinite(值) or 值<=0):#数必须正且有限
            raise 节点ptc错误('ptc-runtime-node: '+键+' must be positive and finite')#拒绝
    for 键 in ('timeoutMs','maxTimeoutMs','graceMs'):#定时器字段
        if 配置值[键]>定时器延迟上限毫秒:#超上限；布尔按 1 比较，与上游 typeof 之后的比较一致
            raise 节点ptc错误('ptc-runtime-node: '+键+' exceeds the supported timer range')#拒绝
    if not 是安全整数(配置值['maxOutputBytes']) or 配置值['maxOutputBytes']<4:#至少 4
        raise 节点ptc错误('ptc-runtime-node: maxOutputBytes must be an integer of at least 4')#拒绝
    if not 是安全整数(配置值['maxMessageBytes']) or 配置值['maxMessageBytes']>0xffffffff:#32 位帧
        raise 节点ptc错误('ptc-runtime-node: maxMessageBytes must fit an unsigned 32-bit frame length')#拒绝
    if not 是安全整数(配置值['maxPendingCalls']):#必须是安全整数
        raise 节点ptc错误('ptc-runtime-node: maxPendingCalls must be an integer')#拒绝
    if not 是安全整数(配置值['maxOldGenerationSizeMb']):#必须是安全整数
        raise 节点ptc错误('ptc-runtime-node: maxOldGenerationSizeMb must be an integer')#拒绝
