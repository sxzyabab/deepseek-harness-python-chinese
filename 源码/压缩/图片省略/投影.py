from .投影消息 import 图片省略错误,省略消息图片#本包异常与消息投影

__all__=['图片省略错误','省略消息图片','图片省略投影']#仅中文公开名

def 是否记录(值):#是否 JSON 对象
    """耐久值是否为 JSON 对象。"""
    return isinstance(值,dict)#朴素对象

def 是否序号(值):#是否规范序号
    """耐久出现下标或事件序号是否为非负整数。"""
    if isinstance(值,bool) or not isinstance(值,int):#布尔或非整数
        return False#拒绝
    return 值>=0#非负

def 投影(事件,上下文):#校验并重建选中消息
    """原子校验并重建，供实时会话与离线回放共用。"""
    数据=事件['data'] if 'data' in 事件 else None#事件数据
    if (not 是否记录(数据) or len(数据)!=1 or 'targets' not in 数据#必须只有 targets
            or not isinstance(数据['targets'],list) or len(数据['targets'])==0):#非空数组
        raise 图片省略错误('image/offload: data must contain a nonempty targets array')#结构非法
    消息表={}#序号 → 消息
    节点集=set(上下文['nodes'])#当前表面节点
    事件表=上下文['events']#事件日志
    基序号=上下文['baseSeq']#日志基序号
    已有消息=上下文['messages']#已派生消息
    for 目标 in 数据['targets']:#逐个目标
        if (not 是否记录(目标) or len(目标)!=2 or 'seq' not in 目标 or not 是否序号(目标['seq'])#必须 seq
                or 'imageIndexes' not in 目标 or not isinstance(目标['imageIndexes'],list)#必须下标数组
                or len(目标['imageIndexes'])==0):#非空
            raise 图片省略错误('image/offload: each target must contain a seq and nonempty imageIndexes')#目标非法
        序号=目标['seq']#消息事件序号
        if 序号 in 消息表:#重复序号
            raise 图片省略错误('image/offload: duplicate target seq '+str(序号))#重复
        if 序号 not in 节点集:#不是当前表面
            raise 图片省略错误('image/offload: target seq '+str(序号)+' is not a current surface node')#不在表面
        来源=事件表[序号-基序号]#按下标取事件
        来源类型=None if 来源 is None else 来源['type']#事件类型
        if 来源类型!='user/message' and 来源类型!='tool/result':#必须是输入节点
            raise 图片省略错误('image/offload: target seq '+str(序号)+' must be user/message or tool/result')#类型非法
        前一个=-1#严格递增哨兵
        for 下标 in 目标['imageIndexes']:#逐个图片下标
            if not 是否序号(下标) or 下标<=前一个:#必须严格递增非负整数
                raise 图片省略错误('image/offload: imageIndexes must be strictly increasing non-negative safe integers')#下标非法
            前一个=下标#记下
        消息=已有消息[序号] if 序号 in 已有消息 else None#已派生
        if 消息 is None:#尚未派生
            来源数据=来源['data']#事件数据
            if 来源类型=='user/message':#用户消息
                消息=来源数据#消息本体
            else:#工具结果
                消息=来源数据['message']#嵌套消息
        消息表[序号]=省略消息图片(消息,目标['imageIndexes'])#标出已省略
    return 消息表#投影结果

图片省略投影={#会话消息投影
    'type':'image/offload',#事件类型
    'project':投影,#投影函数
}#投影结束
