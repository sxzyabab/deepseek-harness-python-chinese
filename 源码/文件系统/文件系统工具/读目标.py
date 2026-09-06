"""面向模型的读工具共享的路径解析与普通文件校验。对齐上游 tool-fs/src/read-target.ts。"""
from .. import 文件系统 as fs#文件系统服务定义
from .会话工作目录 import 会话解析选项#导入会话cwd解析选项

def 解析普通读目标(上下文,执行,请求路径):#解析并校验可读的普通文件目标
    """解析模型提供的路径，观察缺失，并要求是普通文件。返回已解析目标及其单次 stat 结果（类型、大小、版本）。目标与信息都是 dict。"""
    目标=上下文.fs.解析(请求路径,会话解析选项(执行,请求路径))#按会话cwd解析稳定目标
    信息=上下文.fs.状态(目标,执行['signal'] if 'signal' in 执行 else None)#一次stat：类型、大小、版本
    if 信息 is None:#目标不存在
        上下文.广播('fs/observed',目标,{'kind':'absent'},执行)#记录缺失观察
        raise fs.文件系统错误('cannot read "'+目标['displayPath']+'": not found','FS_NOT_FOUND')#按未找到失败
    if 信息['type']!='file':#不是普通文件
        raise fs.文件系统错误('cannot read "'+目标['displayPath']+'": not a regular file','FS_NOT_REGULAR_FILE')#拒绝目录等
    return {'target':目标,'info':信息}#返回可供读取的目标与元数据
