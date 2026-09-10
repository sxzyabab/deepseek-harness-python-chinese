"""原生 V3 系统头节点校验，并为冻结的非系统关系提供私有视图。"""
import json#未知类型诊断
from ..会话格式 import 会话格式错误,会话格式不支持迁移错误#从会话格式导入
from ..会话格式_v1到v2 import 断言已发布v2头,恢复已发布v2产物#从v1到v2导入
from .载荷 import 断言v3事件,是否修复标识,记录,表面类型#从载荷导入

def 断言已发布v3头(头):#断言v3头
    """用已发布 v2 字段校验 v3 逻辑元数据。"""
    if 头.get('version')!=3:#须为v3
        raise 会话格式错误('expected format v3 header')#错误
    断言已发布v2头({**头,'version':2})#其余字段按v2校验

def 恢复已发布v3产物(产物,已知事件类型):#恢复v3产物
    """校验系统归属、受保护头节点操作、普通关系与继承切口。"""
    断言已发布v3头(产物['header'])#断言头
    步骤=None#开放步骤
    头节点=None#受保护系统头
    已有表面=False#是否已有surface
    投影事件=[]#投影事件列表
    for 事件 in 产物['events']:#投影事件
        断言v3事件准入(事件)#准入
        断言v3事件(事件,已知事件类型)#规范校验
        系统=事件['type']=='system/message'#是否系统消息
        if 事件['type']=='step/start':#步骤开始
            数据=记录(事件['data'],事件['type'])#载荷
            步骤={'turn':数据['turn'],'step':数据['step']}#开放
        elif 事件['type']=='step/end' or 事件['type']=='turn/end':#关闭
            步骤=None#关闭
        if 系统:#系统消息
            数据=记录(事件['data'],'system/message')#载荷
            if 步骤 is None or 步骤['turn']!=数据['turn'] or 步骤['step']!=数据['step']:#步骤不符
                raise 会话格式错误('system/message does not match an open step')#错误
            操作=事件.get('surfaceOp')#表面操作
            if 已有表面 and 头节点 is None:#需受保护头
                raise 会话格式错误('system/message requires a protected first surface head')#错误
            if 操作=='append':#追加
                if not 已有表面:#首次surface记为头
                    头节点=事件['seq']#记头
            else:#替换
                替换=记录(操作,'system replacement')#替换记录
                if 替换.get('startSeq')==头节点 or 替换.get('endSeq')==头节点:#触及头节点
                    if 替换.get('startSeq')!=头节点 or 替换.get('endSeq')!=头节点:#须恰好覆盖头
                        raise 会话格式错误('system/message must replace exactly the current system head')#错误
                    头节点=事件['seq']#更新头
        elif 事件['type'] in 表面类型 and 事件.get('surfaceOp')!='append':#普通surface替换
            替换=记录(事件.get('surfaceOp'),'surface replacement')#替换
            if 替换.get('startSeq')==头节点 or 替换.get('endSeq')==头节点:#不得遮蔽头
                raise 会话格式错误('surface replacement cannot shadow the protected system head')#错误
        if 事件['type']=='compaction/prune' or 事件['type']=='compaction/summary':#压缩
            数据=记录(事件['data'],事件['type'])#载荷
            序号列表=数据.get('shadowedSeqs')#遮蔽序号
            if isinstance(序号列表,list) and any(序号==头节点 for 序号 in 序号列表):#遮蔽头
                raise 会话格式错误('compaction cannot shadow the protected system head')#错误
        if 事件['type'] in 表面类型:#已有surface
            已有表面=True#标记
        投影=关系事件(事件)#关系视图投影
        if 事件['type'] not in 表面类型 or 事件.get('surfaceOp')=='append':#追加或非surface
            投影事件.append(投影)#原样返回投影
            continue#继续
        替换=事件['surfaceOp']#规范端点
        #仅冻结关系视图使用已发布端点名。
        投影事件.append({**投影,'surfaceOp':{'op':'replace','start':替换['startSeq'],'end':替换['endSeq']}})#降为start/end
    恢复已发布v2产物(#委托v2关系校验
        {**产物,'header':{**产物['header'],'version':2},'events':投影事件},#降为v2视图
        已知事件类型,#已知类型
        3,#关系头版本
    )#恢复结束
    return 产物#返回原产物

def 断言v3事件准入(事件):#断言v3事件准入
    """拒绝必需的前代 PTC 标签，且不解释原生扩展载荷。"""
    if ((事件['type']=='tool/code-dispatch-start' or 事件['type']=='tool/code-dispatch')
        and 事件.get('ignorable') is not True):#必需前代PTC标签
        raise 会话格式不支持迁移错误(#拒绝
            'format v3 contains unknown event type '+json.dumps(事件['type'],ensure_ascii=False,separators=(',',':'))
            +' at seq '+str(事件['seq']),#消息
        )#Error结束

def 关系事件(事件):#关系视图事件
    """把 PTC/系统/修复事件投影为冻结关系视图。"""
    类型=事件['type']#类型
    if 类型=='tool/ptc-dispatch-start':#ptc分发开始
        return {**事件,'type':'tool/code-dispatch-start'}#映射回前代标签供校验
    if 类型=='tool/ptc-dispatch':#ptc分发
        return {**事件,'type':'tool/code-dispatch'}#映射回前代标签
    if 类型=='tool/code-dispatch-start' or 类型=='tool/code-dispatch':#前代分发
        断言v3事件准入(事件)#准入（可忽略路径）
        #已退役的可忽略事件不参与已发布 PTC 生命周期校验。
        return {**事件,'type':'v3/opaque-released-event'}#不透明化
    if 类型=='system/message':#系统消息
        消息=记录(记录(事件['data'],'system data')['message'],'system message')#消息
        #冻结校验器需要可作 surface 的事件，而非模型可见替身。
        return {**事件,'type':'user/message','data':{**消息,'role':'user'}}#投影为用户消息
    if 类型!='tool/result':#非工具结果原样
        return 事件#原样
    数据=记录(事件['data'],'tool result')#载荷
    if 'error' not in 数据:#无错误原样
        return 事件#原样
    错误=记录(数据['error'],'tool error')#错误对象
    if 错误.get('code')!='TOOL_NOT_STARTED':#非该修复码
        return 事件#原样
    消息=记录(数据['message'],'tool message')#消息
    来源=记录(消息['source'],'tool source')#来源
    调用标识=来源.get('callId')#调用标识
    标识=消息.get('id')#消息标识
    if not 是否修复标识(标识,调用标识):#非规范修复标识
        return 事件#原样
    前缀='interrupted-tool-result-'+调用标识+'-'#前缀
    #消息标识在提升中保留；仅此私有冻结修复检查使用目标序号。
    return {**事件,'data':{**数据,'message':{**消息,'id':f'{前缀}{事件["seq"]}'}}}#私有视图改后缀
