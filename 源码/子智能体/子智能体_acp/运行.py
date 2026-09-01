"""ACP 子智能体跑生命周期（对齐 upstream subagent-acp/run.ts 骨架）。"""
import uuid#子 id
from ...内核.会话 import 会话标识#品牌
默认处置eof宽限毫秒=6000#EOF 宽限
默认处置宽限毫秒=3000#处置宽限

def 取字段(对象,键,缺省=None):#读字段
    if 对象 is None:return 缺省#空
    if isinstance(对象,dict):return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

def 解开(值):#可等待则等待
    等待=getattr(值,'wait',None) or getattr(值,'等待',None)#方法
    if callable(等待):return 等待()#等待
    return 值#同步

def 启动acp跑(请求,规格):#startAcpRun 骨架
    """启动 ACP 子进程并返回跑句柄。完整 ACP SDK 协议待 Python 绑定。"""
    try:#尝试导入 ACP SDK
        import agentclientprotocol#占位模块名
    except ImportError as 错误:#缺 SDK
        raise Exception('subagent-acp: @agentclientprotocol/sdk Python binding is required: '+str(错误))#阻塞
    子标识=会话标识(str(uuid.uuid4()))#子 id
    raise Exception('subagent-acp: ACP wire protocol driver is not yet implemented in Python')#待实现

__all__=['默认处置eof宽限毫秒','默认处置宽限毫秒','启动acp跑']#公开面
