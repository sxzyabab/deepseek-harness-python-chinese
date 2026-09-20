from ...未实现失败 import 运行时错误
import hashlib
from ......工具.加密 import 随机uuid as 铸造uuid
from buffer import Buffer

__all__=[
    'createHash','randomBytes','randomUUID','getRandomValues','randomInt','webcrypto',
    '__esModule','default',
]

def 摘要sha1(输入):
    """SHA-1 摘要。"""
    return hashlib.sha1(输入).digest()

def 摘要sha256(输入):
    """SHA-256 摘要。"""
    return hashlib.sha256(输入).digest()

def 摘要sha512(输入):
    """SHA-512 摘要。"""
    return hashlib.sha512(输入).digest()

哈希器表={
    'sha1':摘要sha1,
    'sha256':摘要sha256,
    'sha512':摘要sha512,
}

编码器=globals()['TextEncoder'] if 'TextEncoder' in globals() else None

def 归一字节(数据):
    """字符串 / Uint8Array / ArrayBuffer → bytes。"""
    if isinstance(数据,str):
        if 编码器 is not None: return bytes(编码器().encode(数据))
        return 数据.encode('utf-8')
    if type(数据).__name__=='ArrayBuffer': return bytes(globals()['Uint8Array'](数据))
    return bytes(数据)

def 创建哈希(算法):
    """创建同步哈希对象。"""
    键=算法.lower().replace('-','')
    if 键 not in 哈希器表:
        raise 运行时错误(f'web-preview: worker 宿主里没有 node:crypto.createHash("{算法}")')
    哈希器=哈希器表[键]
    分块列表=[]
    哈希={}

    def 追加(数据,编码=None):
        """追加数据并链式返回。"""
        分块列表.append(归一字节(数据))
        return 哈希

    def 摘要(编码=None):
        """返回 Buffer 或编码字符串。"""
        合计=sum(len(块) for 块 in 分块列表)
        合并=bytearray(合计)
        偏移=0
        for 块 in 分块列表:
            合并[偏移:偏移+len(块)]=块
            偏移+=len(块)
        摘要缓冲=Buffer.from(哈希器(bytes(合并)))
        if 编码 is None: return 摘要缓冲
        return 摘要缓冲.toString(编码)

    哈希['update']=追加
    哈希['digest']=摘要
    return 哈希

def 随机字节(大小):
    """密码学强度随机字节的 Buffer。"""
    字节=globals()['Uint8Array'](大小)
    globals()['crypto'].getRandomValues(字节)
    return Buffer.from(字节)

def 随机uuid():
    """随机 v4 UUID。委托给仓库自有铸造。"""
    return 铸造uuid()

def 获取随机值(目标):
    """用随机字节填充类型化数组。"""
    return globals()['crypto'].getRandomValues(目标)

def 随机整数(上限):
    """`[0, max)` 中的随机整数。"""
    样本组=globals()['crypto'].getRandomValues(globals()['Uint32Array'](1))
    样本=样本组[0] if 样本组 else 0
    return int((样本/(2**32))*上限)

createHash=创建哈希
randomBytes=随机字节
randomUUID=随机uuid
getRandomValues=获取随机值
randomInt=随机整数
webcrypto=globals()['crypto'] if 'crypto' in globals() else None
__esModule=True

default={
    'createHash':创建哈希,'randomBytes':随机字节,'randomUUID':随机uuid,
    'getRandomValues':获取随机值,'randomInt':随机整数,'webcrypto':webcrypto,
}
