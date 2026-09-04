"""worker 侧的 `node:crypto`：WebCrypto 提供随机性，`@noble/hashes` 提供 Node
流式 Hash 对象所提供的同步摘要（SubtleCrypto 是异步的，而此处每个调用方都同步哈希）。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/crypto.ts`。
公开面中文名；Node 面经别名与 default 暴露英文名。
"""
import hashlib#对齐 @noble/hashes 同步摘要
from ......工具.加密 import 随机uuid as 铸造uuid#导入UUID铸造
from buffer import Buffer#导入Buffer

__all__=[#中文公开名与Node英文挂名
    '创建哈希','随机字节','随机uuid','获取随机值','随机整数',
    'createHash','randomBytes','randomUUID','getRandomValues','randomInt','webcrypto',
    '__esModule','default',
]#公开结束

def 摘要sha1(输入):#SHA-1
    """SHA-1 摘要。"""
    return hashlib.sha1(输入).digest()#摘要

def 摘要sha256(输入):#SHA-256
    """SHA-256 摘要。"""
    return hashlib.sha256(输入).digest()#摘要

def 摘要sha512(输入):#SHA-512
    """SHA-512 摘要。"""
    return hashlib.sha512(输入).digest()#摘要

哈希器们={#算法名到摘要函数
    'sha1':摘要sha1,#SHA-1
    'sha256':摘要sha256,#SHA-256
    'sha512':摘要sha512,#SHA-512
}#哈希器们结束

编码器=globals().get('TextEncoder')#文本编码器类

def 归一字节(数据):#归一为字节
    """字符串 / Uint8Array / ArrayBuffer → bytes。"""
    if isinstance(数据,str):#字符串编码
        if 编码器 is not None: return bytes(编码器().encode(数据))#TextEncoder
        return 数据.encode('utf-8')#UTF-8
    if type(数据).__name__=='ArrayBuffer': return bytes(globals()['Uint8Array'](数据))#ArrayBuffer包视图
    return bytes(数据)#已是字节视图

def 创建哈希(算法):#创建同步哈希
    """创建同步哈希对象。"""
    键=算法.lower().replace('-','')#查算法名
    哈希器=哈希器们.get(键)#查算法
    if 哈希器 is None:#未知算法
        raise Exception(f'web-preview: node:crypto.createHash("{算法}") is not available in the worker host')#拒绝
    分块们=[]#分块缓冲
    哈希={}#构造哈希对象

    def 追加(数据,编码=None):#追加数据
        """追加数据并链式返回。"""
        分块们.append(归一字节(数据))#收字节
        return 哈希#链式

    def 摘要(编码=None):#结算摘要
        """返回 Buffer 或编码字符串。"""
        合计=sum(len(块) for 块 in 分块们)#总长度
        合并=bytearray(合计)#合并缓冲
        偏移=0#写入偏移
        for 块 in 分块们:#逐块拷贝
            合并[偏移:偏移+len(块)]=块#写入
            偏移+=len(块)#推进
        摘要缓冲=Buffer.from(哈希器(bytes(合并)))#摘要为Buffer
        if 编码 is None: return 摘要缓冲#Buffer
        return 摘要缓冲.toString(编码)#按编码返回

    哈希['update']=追加#update
    哈希['digest']=摘要#digest
    return 哈希#返回哈希面

def 随机字节(大小):#随机字节
    """密码学强度随机字节的 Buffer。"""
    字节=globals()['Uint8Array'](大小)#分配
    globals()['crypto'].getRandomValues(字节)#填充
    return Buffer.from(字节)#包为Buffer

def 随机uuid():#随机UUID
    """随机 v4 UUID。委托给仓库自有铸造。"""
    return 铸造uuid()#委托铸造

def 获取随机值(目标):#填充随机
    """用随机字节填充类型化数组。"""
    return globals()['crypto'].getRandomValues(目标)#委托WebCrypto

def 随机整数(上限):#随机整数
    """`[0, max)` 中的随机整数。"""
    样本组=globals()['crypto'].getRandomValues(globals()['Uint32Array'](1))#取32位样本
    样本=样本组[0] if 样本组 else 0#样本
    return int((样本/(2**32))*上限)#映射到[0,上限)

createHash=创建哈希#Node面
randomBytes=随机字节#Node面
randomUUID=随机uuid#Node面
getRandomValues=获取随机值#Node面
randomInt=随机整数#Node面
webcrypto=globals().get('crypto')#浏览器Crypto
__esModule=True#CJS互操作标记

default={#默认导出成员
    'createHash':创建哈希,'randomBytes':随机字节,'randomUUID':随机uuid,#摘要与随机
    'getRandomValues':获取随机值,'randomInt':随机整数,'webcrypto':webcrypto,#其余
}#默认导出结束
