'从对话元素找到最具体的身份。不比较已经画出来的文字'

from .文档对象 import 已显示,在聊天内#可见和所属列

def 匹配聊天元素(元素,根):
    '工具调用优先于节点、分组和回合。列外面或藏起来的都不算'
    if not 在聊天内(元素,根) or not 已显示(根) or 元素.closest('[hidden]') is not None:#不在可见对话里
        return None#没有匹配
    def 最近(选择器):
        '最近的匹配必须仍在这列里并且看得到'
        找到=元素.closest(选择器)#最近祖先或自己
        if 找到 is None or not 在聊天内(找到,根) or not 已显示(找到):#不合格
            return None#没有
        return 找到#这个盒子
    节点=最近('[data-chat-node-key]')#节点
    调用=最近('[data-chat-call-id]')#工具调用
    分组=最近('[data-chat-group-key]')#分组
    回合元素=最近('[data-chat-turn]')#回合
    盒=调用 or 节点 or 分组 or 回合元素#预览用最具体的盒子
    if 盒 is None:#都没有
        return None#没有匹配
    回合文本=None if 回合元素 is None else 回合元素.getAttribute('data-chat-turn')#回合属性
    回合=None#回合号
    if 回合文本 not in (None,''):#有文本
        try:#属性可能不是数字
            回合=int(回合文本)#整数回合
        except ValueError:#不是整数
            回合=None#丢掉
        if isinstance(回合,int) and 回合<0:#负数不要
            回合=None#丢掉
    目标={}#身份
    if 节点 is not None and 节点.getAttribute('data-chat-node-key') is not None:#有节点
        目标['nodeKey']=节点.getAttribute('data-chat-node-key')#节点键
    if 节点 is not None and 节点.getAttribute('data-chat-group-part') is not None:#有部位
        目标['groupPart']=节点.getAttribute('data-chat-group-part')#部位
    if 节点 is not None and 节点.getAttribute('data-chat-flow-kind') is not None:#有种类
        目标['nodeKind']=节点.getAttribute('data-chat-flow-kind')#流种类
    if 调用 is not None and 调用.getAttribute('data-chat-call-id') is not None:#有调用
        目标['callId']=调用.getAttribute('data-chat-call-id')#调用号
    if 分组 is not None and 分组.getAttribute('data-chat-group-key') is not None:#有分组
        目标['groupKey']=分组.getAttribute('data-chat-group-key')#分组键
    if 回合 is not None:#安全的非负整数
        目标['turn']=回合#回合
    return {'element':盒,'target':目标}#盒子和身份

def 匹配聊天节点行(目标,行表):
    '先精确到节点部位，再退到节点、分组、步骤或回合'
    条目=list(行表.items())#当前行
    if 目标.get('nodeKey') is not None:#点了节点
        节点行=[]#这个节点的行
        for 键,行 in 条目:#逐行
            if 行.get('nodeKey')==目标.get('nodeKey'):#同一节点
                节点行.append((键,行))#留下
        精确=None#部位也相同
        for 键,行 in 节点行:#先找部位
            if 行.get('groupPart')==目标.get('groupPart'):#部位相同，包括都没有
                精确=(键,行)#命中
                break#停
        if 精确 is None and len(节点行)>0:#没有精确部位
            精确=节点行[0]#退到该节点的第一行
        if 精确 is not None:#有节点行
            return 精确[0]#行键
    if 目标.get('groupKey') is not None:#点了分组
        for 键,行 in 条目:#找分组头
            if 行.get('groupKey')==目标.get('groupKey') and 行.get('nodeKey') is None:#分组本身
                return 键#分组行
    if 目标.get('turn') is None:#没有回合
        return None#对不上
    回合行=[]#这个回合的行
    for 键,行 in 条目:#逐行
        if 行.get('turn')==目标.get('turn'):#同一回合
            回合行.append((键,行))#留下
    if len(回合行)==0:#没有
        return None#对不上
    if 目标.get('step') is None:#只要回合
        return 回合行[0][0]#第一行
    for 键,行 in 回合行:#找步骤
        if 行.get('step')==目标.get('step'):#同一步骤
            return 键#步骤行
    return 回合行[0][0]#退回这个回合的第一行
