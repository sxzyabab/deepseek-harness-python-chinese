"""可安全重放、无模型的工具结果修剪服务。"""
from ...依赖 import cordis#外部依赖胶水
from ...依赖 import schemastery#配置字段
数字字段=schemastery.数字字段#配置字段
服务=cordis.服务#导入Cordis服务基类
from ...模型后端.llm import 冻结消息#导入冻结消息
from .配置 import 码点长度,默认预算,修剪标记,解析配置#导入码点长度、默认值、标记与解析
from .类型 import (
    修剪记账字段,#单条替换记账词汇
    修剪结果字段,#一遍结果词汇
    已解析配置字段,#已解析配置词汇
    工具结果修剪配置字段,#原始配置词汇
)#本包类型

码点长度=码点长度#再导出码点长度
默认预算=默认预算#再导出默认预算
修剪标记=修剪标记#再导出修剪标记
解析配置=解析配置#再导出解析配置

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '码点长度','默认预算','修剪标记','解析配置','取字段','工具结果修剪器',
    '修剪记账字段','修剪结果字段','已解析配置字段','工具结果修剪配置字段','默认',
]#公开面结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

class 工具结果修剪器(服务):#工具结果修剪服务
    """对当前工具结果表面节点做确定性头/中/尾修剪。token-meter 为每条被遮蔽节点的已记录影子价格事件计价，因此修剪确实需要计价能力。"""
    inject=['tokenMeter']#依赖tokenMeter
    注入=inject#中文别名
    Config={#插件配置模式
        'thresholdChars':数字字段(默认值=默认预算['thresholdChars']),#触发阈值
        'headChars':数字字段(默认值=默认预算['headChars']),#开头保留
        'tailChars':数字字段(默认值=默认预算['tailChars']),#结尾保留
    }#Config结束

    def __init__(自身,上下文,配置=None):#构造修剪器
        """注册为 ctx.toolResultPruner，并解析冻结的字符预算。"""
        if 配置 is None:#缺省空配置
            配置={}#空配置
        super().__init__(上下文,'toolResultPruner')#注册服务名
        自身.配置=解析配置(配置)#解析并冻结预算

    def 测量内容(自身,块们):#测量码点数
        """按 Unicode 码点测量文本内容；非文本块代价为零。"""
        字符数=0#累计
        for 块 in 块们:#逐块
            if 取字段(块,'type')=='text':#只计文本
                字符数+=码点长度(取字段(块,'text'))#累加文本码点
        return 字符数#合计

    def 修剪内容(自身,块们):#修剪一块内容
        """替换超预算的文本中间，同时保留富块顺序。文本切片按 Unicode 码点而非 UTF-16 码元，因此保留边界不会拆开代理对。字素簇仍可能被切开。未超阈值返回 None。"""
        总码点=自身.测量内容(块们)#原文码点数
        if 总码点<=自身.配置['thresholdChars']:#未超阈值则不修剪
            return None#不修剪
        删除起点=自身.配置['headChars']#被删中间的起点
        删除终点=总码点-自身.配置['tailChars']#被删中间的终点
        已修剪=[]#输出块
        已消费=0#已消费码点
        已插标记=False#是否已插入标记
        for 块 in 块们:#按原顺序
            if 取字段(块,'type')!='text':#非文本原样保留
                已修剪.append(块)#推入富块
                continue#下一块
            码点们=list(取字段(块,'text'))#拆成码点
            块起点=已消费#本块在全文中的起点
            块终点=块起点+len(码点们)#本块终点
            头结束=min(len(码点们),max(0,删除起点-块起点))#本块内保留头的结束下标
            尾开始=min(len(码点们),max(0,删除终点-块起点))#本块内保留尾的起始下标
            相交删除=块起点<删除终点 and 块终点>删除起点#本块是否碰到被删区间
            标记=修剪标记 if (相交删除 and (not 已插标记)) else ''#首次相交则插入标记
            if len(标记)>0:#记下已插入
                已插标记=True#已插入
            文本=''.join(码点们[0:头结束])+标记+''.join(码点们[尾开始:])#本块头加标记加尾
            if len(文本)>0:#非空才留下
                新块=dict(块)#复制块外壳
                新块['text']=文本#写入修剪后文本
                已修剪.append(新块)#推入输出
            已消费=块终点#推进消费光标
        if not 已插标记:#未找到被删跨度
            raise Exception('tool-result prune: failed to locate the removed text span')#未找到被删跨度
        之后码点=自身.测量内容(已修剪)#替换后码点数
        if 之后码点>自身.配置['thresholdChars'] or 之后码点>=总码点:#未缩小或仍超阈值
            raise Exception('tool-result prune: replacement must be smaller and within threshold')#替换必须更小且在阈值内
        return 已修剪#已修剪内容

    def 修剪会话(自身,会话):#修剪一会话当前表面
        """从一份稳定的当前表面快照修剪每一个超预算工具结果。每次替换除 content 外保留完整事件数据，引用被遮蔽节点以便重放恢复替换输入，并在正前方立即追加经注入 token-meter 为该节点计价的 compaction/prune 影子价格事件，使纯消费方无需逐节点状态即可减去。会话拒绝某次替换时抛错；本遍更早提交的替换仍耐久。"""
        候选们=[]#快照候选
        表面=取字段(会话,'surface')#当前表面
        节点们=list(取字段(表面,'nodes'))#拷贝当前表面序号
        事件们=取字段(会话,'events')#事件日志快照
        for 序号 in 节点们:#扫描表面
            事件=事件们[序号]#按下标取事件
            if 事件 is not None and 取字段(事件,'type')=='tool/result':#只收工具结果
                候选们.append({'seq':序号,'event':事件})#收下候选
        已记账=[]#替换记账
        去掉码点=0#合计去掉码点
        for 候选 in 候选们:#按快照顺序
            序号=候选['seq']#原文序号
            事件=候选['event']#工具结果事件
            数据=取字段(事件,'data')#事件数据
            消息=取字段(数据,'message')#工具结果消息
            结果=取字段(消息,'content')[0]#第一条工具结果内容
            内容=自身.修剪内容(取字段(结果,'content'))#尝试修剪
            if 内容 is None:#未超预算则跳过
                continue#下一条
            修剪前=自身.测量内容(取字段(结果,'content'))#修剪前
            修剪后=自身.测量内容(内容)#修剪后
            新结果=dict(结果)#保留结果外壳
            新结果['content']=内容#已修剪块
            新消息=dict(消息)#其余字段原样
            新消息['content']=[新结果]#只改内容，仍是单元素列表
            冻结后=冻结消息(新消息)#冻结替换消息
            计价=自身.ctx.tokenMeter.estimateMessage(消息)#启发式价格
            会话.追加('compaction/prune',{#影子价格事件
                'shadowedRange':{'start':序号,'end':序号},#单节点区间
                'shadowedSeqs':[序号],#被遮蔽序号
                'shadowedTokenCount':计价,#启发式价格
            })#prune事件结束
            新数据=dict(数据)#其余事件数据
            新数据['message']=冻结后#已修剪消息
            替换=会话.追加('tool/result',新数据,{#追加替换结果
                'surfaceOp':{'op':'replace','start':序号,'end':序号},#替换该节点
                'sourceEventSeqs':[序号],#引用原文
            })#append结束
            已记账.append({#记下本条
                'originalSeq':序号,#原文序号
                'replacementSeq':取字段(替换,'seq'),#替换序号
                'callId':取字段(取字段(消息,'source'),'callId'),#工具调用id
                'charsBefore':修剪前,#修剪前码点
                'charsAfter':修剪后,#修剪后码点
            })#记账结束
            去掉码点+=修剪前-修剪后#累加节省
        return {'pruned':已记账,'charsRemoved':去掉码点}#本遍结果

默认=工具结果修剪器#默认导出
default=工具结果修剪器#Cordis默认导出
