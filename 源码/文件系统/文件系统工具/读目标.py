"""面向模型的读工具共享的路径解析与普通文件校验。对齐上游 tool-fs/src/read-target.ts。"""
from .. import 文件系统 as fs#文件系统服务定义
from .会话工作目录 import 会话解析选项#导入会话cwd解析选项
from .辅助 import 取字段,试取,解开#字段读取与承诺展开

def 解析普通读目标(上下文,执行,请求路径):#解析并校验可读的普通文件目标
    """解析模型提供的路径，观察缺失，并要求是普通文件。返回已解析目标及其单次 stat 结果（类型、大小、版本）。"""
    目标=解开(上下文.fs.解析(请求路径,会话解析选项(执行,请求路径)))#按会话cwd解析稳定目标
    信息=解开(上下文.fs.状态(目标,试取(执行,'signal')))#一次stat：类型、大小、版本
    if 信息 is None:#目标不存在
        上下文.emit('fs/observed',目标,{'kind':'absent'},执行)#记录缺失观察
        raise fs.文件系统错误('cannot read "'+取字段(目标,'displayPath')+'": not found','FS_NOT_FOUND')#按未找到失败
    if 取字段(信息,'type')!='file':#不是普通文件
        raise fs.文件系统错误('cannot read "'+取字段(目标,'displayPath')+'": not a regular file','FS_NOT_REGULAR_FILE')#拒绝目录等
    return {'target':目标,'info':信息}#返回可供读取的目标与元数据
