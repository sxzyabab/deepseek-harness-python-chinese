"""输入消息会话节点：用户 / 插话 / 注入上下文。

对齐上游 `ui-conversation/src/client/conversation-nodes/message.ts`。公开面仅中文名。
"""
from .公共 import 聊天节点#聊天节点工厂
from .面辅助 import 取字段,是追加面事件,是替换面事件,上下文出处,上下文形态#面谓词

__all__=['消息定义','登记消息会话节点']#仅中文公开名

def 是压缩检查点(事件):#是否 compact 插件的替换检查点
    """user/message + 替换面 + compact 插件。"""
    if 取字段(事件,'type')!='user/message' or not 是替换面事件(事件):#非
        return False#否
    来源=取字段(取字段(事件,'data'),'source') or {}#来源
    return 取字段(来源,'kind')=='plugin' and 取字段(来源,'plugin')=='compact'#compact

消息定义={#输入消息分类定义
    'kind':'input-message',#本贡献 kind
    'target':'chat',#Chat 目标
}#骨架；函数下挂

def 消息匹配(事件):#是否归本定义
    """追加面 user/message，排除 compact 检查点。"""
    if 取字段(事件,'type')!='user/message':#非
        return None#不认领
    if not 是追加面事件(事件):#非追加
        return None#不认领
    if 是压缩检查点(事件):#检查点
        return None#留给压缩
    数据=取字段(事件,'data') or {}#载荷
    return {'id':str(取字段(数据,'id')),'role':'start'}#以消息 id 开

def 消息开始(_上下文,匹配项,读取器):#按来源与收件箱认领分类
    """非用户 → context；已认领 → steering；否则 user。"""
    事件=取字段(匹配项,'event')#事件
    if 取字段(事件,'type')!='user/message':#必须
        raise Exception('input-message start requires user/message')#硬失败
    数据=取字段(事件,'data') or {}#载荷
    来源=取字段(数据,'source') or {}#来源
    if 取字段(来源,'kind')!='user':#非用户 → 上下文
        return {#上下文消息
            'kind':'context',#上下文
            'seq':取字段(事件,'seq'),#序号
            'time':取字段(事件,'time'),#时刻
            'content':取字段(数据,'content'),#内容
            'source':来源,#来源
            'provenance':上下文出处(来源),#出处
            'form':上下文形态(来源),#形态
        }#结束
    上一=读取器.previous('inbox-next-step') if hasattr(读取器,'previous') else None#收件箱
    已认领=False#默认
    if 上一 is not None:#有
        态=取字段(上一,'state') or {}#态
        集=取字段(态,'claimed') or set()#集
        已认领=str(取字段(数据,'id')) in 集#是否认领
    if 已认领:#插话
        return {#插话
            'kind':'steering',#插话
            'messageId':取字段(数据,'id'),#消息 id
            'seq':取字段(事件,'seq'),#序号
            'time':取字段(事件,'time'),#时刻
            'content':取字段(数据,'content'),#内容
            'source':来源,#来源
        }#结束
    return {#开回合用户消息
        'kind':'user',#用户
        'seq':取字段(事件,'seq'),#序号
        'time':取字段(事件,'time'),#时刻
        'content':取字段(数据,'content'),#内容
        'source':来源,#来源
    }#结束

def 消息更新(上下文,_匹配项=None):#开节点后状态不再变
    """原样。"""
    return 取字段(上下文,'state')#态

def 消息建视图(上下文):#按分类 kind 组装 Chat 节点
    """尚无状态则不渲染。"""
    态=取字段(上下文,'state')#态
    if 态 is None:#无
        return None#不渲染
    return 聊天节点(上下文,取字段(态,'kind'),取字段(态,'seq'),态)#锚在 seq

消息定义['match']=消息匹配#挂
消息定义['start']=消息开始#挂
消息定义['update']=消息更新#挂
消息定义['buildViewNode']=消息建视图#挂

def 登记消息会话节点(上下文):#登记输入消息分类贡献
    """挂到 conversationEvents。"""
    上下文.conversationEvents.register(消息定义)#登记
