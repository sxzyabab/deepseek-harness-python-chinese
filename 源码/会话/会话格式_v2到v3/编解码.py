"""V3 分帧：硬性结构准入，以及可恢复的规范事件校验。"""
from ..会话格式 import (#从会话格式导入
    会话格式错误,#格式错误
    是否会话格式json对象,#是否JSON对象
    快照会话格式json,#快照JSON
)#从会话格式导入
from ..会话格式_v1到v2 import 已发布v2会话格式编解码器#从v1到v2导入
from .校验 import 断言已发布v3头,断言v3事件准入#从校验导入
from .载荷 import 断言v3事件,断言v3结构行#从载荷导入

class _v3解码器:#v3解码器
    """在恢复前校验结构行，在溯源解码后校验逻辑信封。"""
    def __init__(自身,值,恢复):#构造
        """复用 v2 解码器并记下恢复策略。"""
        自身._解码器=已发布v2会话格式编解码器.createDecoder(v2物理头(值),恢复)#复用v2解码器
        自身.header={**自身._解码器.header,'version':3}#逻辑头升为v3
        自身._恢复=恢复#恢复策略
        自身._问题=None#首个规范问题
        自身._已接纳继承切口=None#已接纳的继承切口

    def decodeRow(自身,行,上下文):#解码行
        """校验行准入后委托 v2 行解码。"""
        断言v3行准入(行)#行级准入
        解码器=自身._解码器#v2解码器
        def 发出事件(事件):#发出事件
            断言v3事件准入(事件)#事件准入
            if 自身._问题 is None:#尚无问题
                try:#尝试规范校验
                    断言v3事件(事件)#断言v3事件
                except BaseException as 错误:#捕获
                    #冻结的事件校验器把每条已解码 JSON 违规都报告为 SessionFormatError。
                    if not isinstance(错误,会话格式错误):#非格式错误则抛
                        raise 错误#抛出
                    if 自身._恢复=='strict':#严格则抛
                        raise 错误#抛出
                    自身._问题=错误#记录首错
            if 自身._问题 is not None:#已有问题
                if 事件['type']=='turn/end':#遇回合结束抛出
                    raise 自身._问题#抛出
                return#丢弃后缀
            if (事件['type']=='session/end-seed' and 是否会话格式json对象(事件['data'])
                and 事件['data'].get('inherited') is True):#记继承切口
                自身._已接纳继承切口=事件['seq']#记下
            上下文.emitEvent(事件)#发出事件
        解码器.decodeRow(行,_委托上下文(上下文,发出事件))#委托v2行解码

    def finish(自身,上下文):#完成
        """无问题则委托；否则按种子/继承标记收口。"""
        if 自身._问题 is None:#无问题则委托
            return 自身._解码器.finish(上下文)#委托
        if 自身._解码器.header['isSeeded'] and 自身._已接纳继承切口 is None:#种子缺标记
            raise 会话格式错误('format v3 seeded Session lacks an accepted inherited end-seed marker')#错误
        if (not 自身._解码器.header['isSeeded']) and 自身._已接纳继承切口 is not None:#非种子却有标记
            raise 会话格式错误('format v3 unseeded Session contains an inherited end-seed marker')#错误
        return 0 if 自身._已接纳继承切口 is None else 自身._已接纳继承切口#返回继承数

class _委托上下文:#委托上下文
    """转发游程，并用包装后的发出事件替换 emitEvent。"""
    def __init__(自身,上下文,发出事件):#构造
        """记下上游上下文与包装发出。"""
        自身._上下文=上下文#上游
        自身.emitEvent=发出事件#包装发出

    def emitRun(自身,游程):#发出游程
        """转发游程。"""
        自身._上下文.emitRun(游程)#转发

class 已发布v3会话格式编解码器类型:#v3编解码器
    """已发布 v3 编解码器：结构准入与可恢复规范事件校验。"""
    version=3#版本

    def decodeHeader(自身,值):#解码头
        """解码物理头为逻辑 v3 元数据。"""
        return {**已发布v2会话格式编解码器.decodeHeader(v2物理头(值)),'version':3}#解码后升到v3

    def createDecoder(自身,值,恢复):#创建解码器
        """创建带 V3 准入的流式解码器。"""
        return _v3解码器(值,恢复)#创建

    def encodeHeader(自身,头,继承事件数):#编码头
        """编码当代物理头记录。"""
        断言已发布v3头(头)#断言v3头
        return {#物理头
            **已发布v2会话格式编解码器.encodeHeader({**头,'version':2},继承事件数),#按v2编码
            'version':3,#写回v3
        }#return结束

    def encodeEvent(自身,事件):#编码事件
        """编码当代物理事件记录。"""
        断言v3事件准入(事件)#准入
        断言v3事件(事件)#规范校验
        return 已发布v2会话格式编解码器.encodeEvent(事件)#委托v2编码

#v3编解码器在恢复前校验结构行，在溯源解码后校验逻辑信封。
已发布v3会话格式编解码器=已发布v3会话格式编解码器类型()#v3编解码器单例

def 断言v3行准入(行):#断言v3行准入
    """在扫描器或编解码器丢弃可恢复尾部之前，校验自有 V3 准入规则。"""
    断言v3结构行(行)#结构行校验
    if isinstance(行,dict):#事件准入
        断言v3事件准入(行)#事件准入

def v2物理头(值):#转为v2物理头视图
    """把物理 v3 头降为 v2 供复用解码。"""
    头=快照会话格式json(值,'format v3 physical header')#快照
    if not 是否会话格式json对象(头) or 头.get('version')!=3:#非v3头
        raise 会话格式错误('expected format v3 physical Session header')#错误
    return {**头,'version':2}#降为v2供复用
