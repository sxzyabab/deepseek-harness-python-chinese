"""显式本地坐标重映射；捕获代次与所有者本地计数器保持不透明。"""
from ..会话格式 import 会话格式错误,会话格式计数#从会话格式导入
from .载荷 import 记录#从载荷导入

def 重映射事件(事件,序号,映射):#重映射事件
    """仅重映射经审计的同产物引用，保留标识与内嵌模型输入。"""
    def 一个(值):#映射单个引用
        源=会话格式计数(值,'source event reference')#源序号
        目标=映射[源] if 源<len(映射) else None#目标序号
        if 源>=事件['seq'] or 目标 is None:#须更早且已映射
            raise 会话格式错误('reference must name an earlier source event')#错误
        return 目标#返回目标
    def 列表(值):#映射列表
        if not isinstance(值,list):#须数组
            raise 会话格式错误('sequence references must be an array')#错误
        return [一个(项) for 项 in 值]#逐项映射
    def 范围(值):#映射范围
        源=记录(值,'sequence range')#范围对象
        return {**源,'start':一个(源['start']),'end':一个(源['end'])}#映射端点
    数据=记录(事件['data'],事件['type'])#载荷
    类型=事件['type']#类型
    if 类型=='command/done':#命令完成
        if 'sourceEventSeq' in 数据:#映射源序号
            数据={**数据,'sourceEventSeq':一个(数据['sourceEventSeq'])}#映射
    elif 类型=='compaction/summary' or 类型=='compaction/prune':#压缩
        数据={**数据,'shadowedRange':范围(数据['shadowedRange']),'shadowedSeqs':列表(数据['shadowedSeqs'])}#映射遮蔽
    elif 类型=='session/title' or 类型=='session/title-llm-request':#标题
        数据={**数据,'messageSeqs':列表(数据['messageSeqs'])}#映射消息序号
    #投递水位与会话引用捕获标识其原始代次。
    #工作流 seq、流块索引、回合/步骤及数值工具 JSON 不是会话 seq。
    结果={**事件,'seq':序号,'data':数据}#信封与载荷
    if 'sourceEventSeqs' in 事件:#溯源列表
        结果['sourceEventSeqs']=列表(事件['sourceEventSeqs'])#映射
    if 'surfaceOp' in 事件 and 事件['surfaceOp']!='append':#替换端点
        结果['surfaceOp']=范围(事件['surfaceOp'])#映射
    return 结果#返回目标事件
