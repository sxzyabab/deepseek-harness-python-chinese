"""V4 分帧：原生工具角色准入与已发布物理行。"""
from ..会话格式 import 会话格式错误,是否会话格式json对象#从会话格式导入
from ..会话格式_v2到v3 import 已发布v2会话格式编解码器#从v2到v3导入v2编解码器
from .消息源列表 import 断言v4源行准入#源行准入
from .已退役语法 import 断言v4已退役语法#已退役语法
from .系统消息 import 断言v4系统消息字段#系统消息字段
from .开发者 import 断言v4开发者数据#开发者数据
from .分叉结果 import 断言v4分叉结果#分叉结果
from .工具角色 import 断言v4工具结果消息#工具结果消息
from .校验 import 断言已发布v4头#断言v4头

class _v4解码器:#v4解码器
    """复用 v2 行分帧，并在解码前做原生 V4 行准入。"""
    def __init__(自身,值,恢复):#构造
        """记下 v2 解码器并把逻辑头升为 v4。"""
        自身._解码器=已发布v2会话格式编解码器.createDecoder(v2物理头(值),恢复)#复用v2解码器
        自身.header={**自身._解码器.header,'version':4}#逻辑头升为v4

    def decodeRow(自身,行,上下文):#解码行
        """行准入后委托 v2 行解码。"""
        断言v4行准入(行)#行级准入
        自身._解码器.decodeRow(行,上下文)#委托v2行解码

    def finish(自身,上下文):#完成
        """委托 v2 解码器收口。"""
        return 自身._解码器.finish(上下文)#委托

class 已发布v4会话格式编解码器类型:#v4编解码器
    """已发布 v4 编解码器：保留已发布行分帧并直接校验工具角色消息。"""
    version=4#版本

    def decodeHeader(自身,值):#解码头
        """解码物理头为逻辑 v4 元数据。"""
        return {**已发布v2会话格式编解码器.decodeHeader(v2物理头(值)),'version':4}#解码后升到v4

    def createDecoder(自身,值,恢复):#创建解码器
        """创建带 V4 准入的流式解码器。"""
        return _v4解码器(值,恢复)#创建

    def encodeHeader(自身,头,继承事件数):#编码头
        """编码当代物理头记录。"""
        断言已发布v4头(头)#断言v4头
        return {#物理头
            **已发布v2会话格式编解码器.encodeHeader({**头,'version':2},继承事件数),#按v2编码
            'version':4,#写回v4
        }#return结束

    def encodeEvent(自身,事件):#编码事件
        """编码当代物理事件记录。"""
        if 事件['type']=='developer/message' and 事件.get('ignorable') is True:#可忽略开发者
            断言v4开发者数据(事件)#校验开发者
            断言v4已退役语法(事件)#校验已退役语法
        断言v4行准入(事件)#行准入
        return 已发布v2会话格式编解码器.encodeEvent(事件)#委托v2编码

#v4编解码器在扫描器丢弃可恢复尾部前做原生准入。
已发布v4会话格式编解码器=已发布v4会话格式编解码器类型()#v4编解码器单例

def 断言v4行准入(行,已知事件类型=None):#断言v4行准入
    """在扫描器丢弃可恢复尾部之前应用原生 V4 准入。"""
    if 是否会话格式json对象(行):#对象行
        if (行.get('type')=='developer/message' and 行.get('ignorable') is True
            and (已知事件类型 is None or 'developer/message' not in 已知事件类型)):#物理解码推迟可忽略开发者
            return#返回
        断言v4开发者数据(行)#开发者数据
    断言v4源行准入(行)#源行准入
    断言v4已退役语法(行)#已退役语法
    断言v4系统消息字段(行)#系统消息字段
    if not 是否会话格式json对象(行) or 行.get('type')!='tool/result':#非工具结果
        return#返回
    断言v4工具结果消息(行)#工具结果消息
    断言v4分叉结果(行)#分叉结果

def v2物理头(值):#转为v2物理头视图
    """把物理 v4 头降为 v2 供复用解码。"""
    if not 是否会话格式json对象(值) or 值.get('version')!=4:#非v4头
        raise 会话格式错误('expected format v4 physical header')#错误
    return {**值,'version':2}#降为v2供复用
