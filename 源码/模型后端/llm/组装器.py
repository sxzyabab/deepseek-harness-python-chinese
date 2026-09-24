"""增量的块到消息组装器。

公开面仅中文名；无英文别名。
"""
from .标识构造 import 调用标识#导入调用标识构造
from .永不 import 断言永不,永不错误#导入封闭联合穷尽辅助与组装违约
from .消息 import 创建助手消息#导入助手消息工厂

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
            if 'block' in 部分:#已被 block-end 关闭
                return#忽略掉队增量
            部分['text']=部分['text']+块['text']#累积文本
            return#增量处理结束
        if 类型=='tool-call-delta':#工具调用增量
            部分=自身.确保(块['index'],'tool-call')#取出或创建部分块
            if 'block' in 部分:#已被 block-end 关闭
                return#忽略掉队增量
            部分['toolCallId']=块['id']#记下调用 id
            if 'name' in 块 and len(块['name'])>0:#有名字
                部分['toolCallName']=块['name']#有名字则记下
            部分['toolCallArguments']=部分['toolCallArguments']+块['argumentsDelta']#累积参数
            return#增量处理结束
        if 类型=='block-end':#块结束
            部分=自身.确保(块['index'],块['block']['type'])#取出或创建部分块
            if 'block' in 部分:#已关闭
                return#已关闭则忽略
            部分['block']=块['block']#权威块冻结该部分
            return#block-end 处理结束
        if 类型=='usage':#用量
            自身._用量=块['usage']#记下用量
            return#usage 处理结束
        if 类型=='finish':#终止
            自身._结束=块['reason']#记下结束原因
            自身._回放状态=块['replayState'] if 'replayState' in 块 else None#记下回放状态
            return#finish 处理结束
        断言永不(块,'BlockAssembler.push')#封闭联合穷尽

    def 确保(自身,下标,块类型):#取出或创建部分块
        """取出或创建部分块。"""
        部分=自身.部分表[下标] if 下标 in 自身.部分表 else None#已有则用
        if 部分 is None:#尚未见过
            部分={'blockType':块类型,'text':'','toolCallArguments':''}#按该类型新建
            自身.部分表[下标]=部分#记入表
            自身.顺序.append(下标)#记下出现顺序
        return 部分#返回部分块

    def 组装一块(自身,部分,下标):#把部分块组装成内容块
        """把部分块组装成内容块。"""
        if 'block' in 部分:#已有权威块
            return 部分['block']#已有权威块则用
        块类型=部分['blockType']#按类型从增量组装
        if 块类型=='text':#文本
            return {'type':'text','text':部分['text']}#文本
        if 块类型=='reasoning':#推理
            return {'type':'reasoning','text':部分['text']}#推理
        if 块类型=='tool-call':#工具调用
            调用=部分['toolCallId'] if 'toolCallId' in 部分 else None#调用 id
            if 调用 is None:#缺 id
                调用=调用标识('call-'+str(下标))#缺 id 则按线下标合成
            名字=部分['toolCallName'] if 'toolCallName' in 部分 else None#工具名
            if 名字 is None:#缺名字
                名字=''#缺名字则空串
            return {'type':'tool-call','id':调用,'name':名字,'arguments':部分['toolCallArguments']}#工具调用
        raise 永不错误('cannot assemble incomplete block of type "'+块类型+'"')#未知类型且未被 block-end 关闭

    def 必须取(自身,下标):#按下标取部分块
        """按下标取部分块；order 有而下表无则违约。"""
        部分=自身.部分表[下标] if 下标 in 自身.部分表 else None#查表
        if 部分 is None:#违约
            raise 永不错误('BlockAssembler invariant violated: no partial for index '+str(下标))#违约
        return 部分#部分块

    def 已组装(自身):#共享保留/丢弃决定
        """达到令牌上限时丢掉不能安全执行的工具调用；回放元数据与发出块同源。"""
        全部=[]#全部组装块
        for 下标 in 自身.顺序:#按出现顺序
            全部.append(自身.组装一块(自身.必须取(下标),下标))#组装
        结束=自身.结束#结束原因
        if 结束['kind']=='max-tokens':#达到 token 上限
            保留标记=[]#每块是否留下
            for 块 in 全部:#筛选标记
                保留标记.append(块['type']!='tool-call')#丢掉工具调用
            块列表=[]#截断后的块
            位置=0#下标
            while 位置<len(全部):#逐块
                if 保留标记[位置]:#留下
                    块列表.append(全部[位置])#保留
                位置+=1#下一步
        else:#不截断
            保留标记=None#无筛选
            块列表=全部#原样
        信封=自身._回放状态#终止块上的回放
        if 信封 is None or 'blocks' not in 信封 or 信封['blocks'] is None:#无按块元数据
            return {'blocks':块列表,'replay':信封}#原信封
        if len(信封['blocks'])!=len(全部):#与发出块数不对齐
            return {'blocks':块列表,'replay':None}#丢弃整份信封
        if 保留标记 is None or len(块列表)==len(全部):#未截断
            return {'blocks':块列表,'replay':信封}#原信封
        回放块=[]#按同一标记筛选
        位置=0#下标
        while 位置<len(信封['blocks']):#逐条
            if 保留标记[位置]:#留下
                回放块.append(信封['blocks'][位置])#保留
            位置+=1#下一步
        return {'blocks':块列表,'replay':{'response':信封['response'],'blocks':回放块}}#对齐后的信封

    def 块列表(自身):#按流顺序组装迄今见到的所有块
        """按流顺序组装迄今见到的所有块。"""
        return 自身.已组装()['blocks']#与回放同源的保留/丢弃

    def 中断块列表(自身):#中断时可定稿的块
        """组装中断流可安全定稿的前缀：非空白文本/推理；省略工具调用与未关闭未知块。"""
        留下=[]#可定稿前缀
        for 下标 in 自身.顺序:#按出现顺序
            部分=自身.必须取(下标)#取部分块
            if 'block' in 部分:#权威块
                类型=部分['block']['type']#权威类型
            else:#声明类型
                类型=部分['blockType']#声明类型
            if 类型!='text' and 类型!='reasoning':#非文本/推理丢掉
                continue#跳过
            块=自身.组装一块(部分,下标)#组装
            if (块['type']=='text' or 块['type']=='reasoning') and 块['text'].strip()!='':#非空白
                留下.append(块)#保留
        return 留下#中断前缀

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
        """终止 finish 块上的适配器私有回放状态；按块条目与发出块同步剪枝。"""
        return 自身.已组装()['replay']#可能为 None

    def 消息(自身,来源):#已组装的助手消息
        """已组装的助手消息。来源为不含 kind 的提供方/模型归属。"""
        return 创建助手消息({'content':自身.块列表(),'source':来源})#助手角色
