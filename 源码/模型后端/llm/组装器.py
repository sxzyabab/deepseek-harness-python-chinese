"""增量的块到消息组装器。

对齐上游 `llm/src/assembler.ts`。公开面仅中文名；无英文别名。
"""
from .品牌 import 调用标识#导入调用 id 品牌
from .永不 import 断言永不#导入封闭联合穷尽辅助
from .消息 import 创建消息#导入消息工厂

__all__=('块组装器',)#仅中文公开名

class 块组装器:#把原始流块增量组装成完整内容块与最终助手消息
    """把原始流块增量组装成完整内容块与最终助手消息。"""
    def __init__(自身):#初始化空的组装状态
        """初始化空的组装状态。"""
        自身.部分表={}#下标到部分块
        自身.顺序=[]#见到下标的顺序
        自身._用量=None#用量，尚未见到则为 None
        自身._结束=None#结束原因，尚未见到则为 None
        自身._回放状态=None#终止块上的回放状态

    def 推入(自身,块):#把一块喂进组装状态
        """把一块喂进组装状态。"""
        类型=块['type']#块类型标签
        if 类型=='block-start':#块开始
            下标=块['index']#块下标
            if 下标 not in 自身.部分表:#尚未见过
                自身.顺序.append(下标)#记下出现顺序
                自身.部分表[下标]={#新建部分块
                    'blockType':块['blockType'],#块类型
                    'text':'',#尚无文本
                    'toolCallArguments':'',#尚无参数
                }#部分块结束
            return#已存在则忽略重复 start
        if 类型=='text-delta' or 类型=='reasoning-delta':#文本或推理增量
            部分=自身.确保(块['index'],'text' if 类型=='text-delta' else 'reasoning')#取出或创建部分块
            if 部分.get('block') is not None:#已被 block-end 关闭
                return#忽略掉队增量
            部分['text']=部分['text']+块['text']#累积文本
            return#增量处理结束
        if 类型=='tool-call-delta':#工具调用增量
            部分=自身.确保(块['index'],'tool-call')#取出或创建部分块
            if 部分.get('block') is not None:#已被 block-end 关闭
                return#忽略掉队增量
            部分['toolCallId']=块['id']#记下调用 id
            if 块.get('name'):#有名字
                部分['toolCallName']=块['name']#有名字则记下
            部分['toolCallArguments']=部分['toolCallArguments']+块['argumentsDelta']#累积参数
            return#增量处理结束
        if 类型=='block-end':#块结束
            部分=自身.确保(块['index'],块['block']['type'])#取出或创建部分块
            if 部分.get('block') is not None:#已关闭
                return#已关闭则忽略
            部分['block']=块['block']#权威块冻结该部分
            return#block-end 处理结束
        if 类型=='usage':#用量
            自身._用量=块['usage']#记下用量
            return#usage 处理结束
        if 类型=='finish':#终止
            自身._结束=块['reason']#记下结束原因
            自身._回放状态=块.get('replayState')#记下回放状态
            return#finish 处理结束
        断言永不(块,'BlockAssembler.push')#封闭联合穷尽

    def 确保(自身,下标,块类型):#取出或创建部分块
        """取出或创建部分块。"""
        部分=自身.部分表.get(下标)#已有则用
        if 部分 is None:#尚未见过
            部分={'blockType':块类型,'text':'','toolCallArguments':''}#按该类型新建
            自身.部分表[下标]=部分#记入表
            自身.顺序.append(下标)#记下出现顺序
        return 部分#返回部分块

    def 组装一块(自身,部分,下标):#把部分块组装成内容块
        """把部分块组装成内容块。"""
        if 部分.get('block') is not None:#已有权威块
            return 部分['block']#已有权威块则用
        块类型=部分['blockType']#按类型从增量组装
        if 块类型=='text':#文本
            return {'type':'text','text':部分['text']}#文本
        if 块类型=='reasoning':#推理
            return {'type':'reasoning','text':部分['text']}#推理
        if 块类型=='tool-call':#工具调用
            调用=部分.get('toolCallId')#调用 id
            if 调用 is None:#缺 id
                调用=调用标识('call-'+str(下标))#缺 id 则按线下标合成
            名字=部分.get('toolCallName')#工具名
            if 名字 is None:#缺名字
                名字=''#缺名字则空串
            return {'type':'tool-call','id':调用,'name':名字,'arguments':部分['toolCallArguments']}#工具调用
        raise Exception('cannot assemble incomplete block of type "'+块类型+'"')#未知类型且未被 block-end 关闭

    def 必须取(自身,下标):#按下标取部分块
        """按下标取部分块；order 有而下表无则违约。"""
        部分=自身.部分表.get(下标)#查表
        if 部分 is None:#违约
            raise Exception('BlockAssembler invariant violated: no partial for index '+str(下标))#违约
        return 部分#部分块

    def 块列表(自身):#按流顺序组装迄今见到的所有块
        """按流顺序组装迄今见到的所有块。"""
        块们=[]#组装结果
        for 下标 in 自身.顺序:#按出现顺序
            块们.append(自身.组装一块(自身.必须取(下标),下标))#按出现顺序组装
        结束=自身.结束#结束原因
        if 结束.get('kind')=='max-tokens':#达到 token 上限
            留下=[]#丢掉不完整工具调用
            for 块 in 块们:#筛选
                if 块['type']!='tool-call':#非工具调用
                    留下.append(块)#保留非工具调用
            return 留下#截断后的块
        return 块们#原样

    @property#用量
    def 用量(自身):#来自 usage 块的用量
        """来自 usage 块的用量；尚未到达则为 None。"""
        return 自身._用量#尚未见到则为 None

    @property#结束
    def 结束(自身):#来自 finish 块的结束原因
        """来自 finish 块的结束原因；流结束时没有则为 stop。"""
        if 自身._结束 is None:#尚未见到
            return {'kind':'stop'}#缺省当作正常停止
        return 自身._结束#已见到的结束原因

    @property#回放状态
    def 回放状态(自身):#终止 finish 上的适配器私有回放状态
        """终止 finish 块上的适配器私有回放状态。"""
        return 自身._回放状态#可能为 None

    def 消息(自身,来源=None):#已组装的助手消息
        """已组装的助手消息。"""
        if 来源 is None:#未传来源
            来源={'kind':'plugin','plugin':'dsh-llm/assembler'}#默认归属本组装器
        return 创建消息({'role':'assistant','content':自身.块列表(),'source':来源})#助手角色
