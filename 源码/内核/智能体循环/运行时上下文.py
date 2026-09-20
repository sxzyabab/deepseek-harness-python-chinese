from ...模型后端.llm import 创建消息,创建用户消息
from ..会话 import 是否替换表面事件

源='@deepseek-ai/dsh-system-prompt'#本投影归属的插件源
已清空='Current runtime context: none. Earlier runtime-context snapshots no longer apply.'#清空标记文案

def 创建系统消息(文本,插件):
    """创建并冻结一条已标识系统角色消息；空串表示无系统提示。"""
    return 创建消息({
        'role':'system',#系统角色
        'content':[] if len(文本)==0 else [{'type':'text','text':文本}],#空则无块
        'source':{'kind':'plugin','plugin':插件},#插件来源
    })#创建结束

def 是否本源(消息):
    """消息是否由本投影插件拥有。"""
    来源=消息['source'] if 'source' in 消息 else None#消息来源
    if 来源 is None:
        return False#无来源
    return 来源['kind']=='plugin' and 来源['plugin']==源#插件源且插件名匹配

def 取文本(消息):
    """取出单文本块消息的文本；否则缺省。空内容视为空串。"""
    内容=消息['content'] if 'content' in 消息 and 消息['content'] is not None else []#内容块
    if len(内容)==0:
        return ''#空内容视为空串
    if len(内容)!=1:
        return None#非单块
    块=内容[0]#首块
    if 块['type']!='text':
        return None#非文本
    return 块['text']#文本

def 事件最新优先(会话):
    """从最新往回的已提交事件。"""
    return list(reversed(list(会话.events)))#倒序

class 系统提示投影:
    """决定已渲染系统提示如何到达表面，但不拥有提交。"""
    def __init__(自身,会话):
        """持有目标会话。"""
        自身.会话=会话#会话

    def _系统节点(自身):
        """按表面顺序仍存活的 system/message 节点。"""
        节点列表=[]#收集
        事件列表=自身.会话.events#权威日志
        for 序号 in 自身.会话.surface.nodes:#扫表面
            事件=事件列表[序号]#取事件
            if 事件 is None or 事件['type']!='system/message':
                continue#非系统跳过
            内容=事件['data']['message']['content']#内容
            文本='' if len(内容)==0 else 取文本(事件['data']['message'])#空内容视为空串
            节点列表.append({'seq':序号,'text':文本})#记下
        return 节点列表#返回

    def _替换(自身,序号,文本):
        """替换单节点的未提交项。"""
        return {
            'message':创建系统消息(文本,源),#系统消息
            'intent':{'surfaceOp':{'op':'replace','startSeq':序号,'endSeq':序号},'sourceEventSeqs':[序号]},#替换意图
        }#提交项

    def 投影(自身,已渲染,输入):
        """按准备好的路由与系列调和有效文本与保留节点。"""
        节点列表=自身._系统节点()#当前系统节点
        if len(节点列表)==0:#尚无系统节点
            return [{'message':创建系统消息(已渲染,源),'intent':{'surfaceOp':'append'}}]#追加占位
        头=节点列表[0]#表面头
        最近非空=头#默认头
        for 节点 in reversed(节点列表):#找最近非空
            if 节点['text']!='':
                最近非空=节点#记下
                break#找到
        历史内=输入['inHistory'] if 'inHistory' in 输入 else False#是否历史内
        开新系列=输入['startsSeries'] if 'startsSeries' in 输入 else False#是否开新系列
        if (not 历史内) or 开新系列 or len(已渲染)==0:#规范化头并清空活动尾
            更新=[]#更新列表
            for 节点 in 节点列表[1:]:#尾
                if 节点['text']!='':
                    更新.append(自身._替换(节点['seq'],''))#清空
            if 头['text']!=已渲染:
                更新.append(自身._替换(头['seq'],已渲染))#换头
            return 更新#返回
        if 最近非空['text']==已渲染:
            return []#未变
        return [{'message':创建系统消息(已渲染,源),'intent':{'surfaceOp':'append'}}]#历史内追加

class 运行时上下文投影:
    """跟踪上次保留的运行时上下文快照，但不拥有其提交。"""
    def __init__(自身,上下文,会话):
        """先一次性恢复投影状态，再跟随权威会话事件。"""
        自身.保留=None#尚未扫描；见过后可为 None 表示未保留
        自身._已见本源=False#是否见过本源消息
        表面=set(会话.surface.nodes)#当前表面节点
        for 事件 in 事件最新优先(会话):#从新到旧
            if 事件['type']!='user/message' or not 是否本源(事件['data']):
                continue#非本源用户消息
            if not 自身._已见本源:
                自身._已见本源=True#已见本源
            if 事件['seq'] in 表面:
                自身.保留={'seq':事件['seq'],'text':取文本(事件['data'])}#记下该快照
                break#已找到最近保留
        def 跟随(主题,事件):
            """跟随本会话事件。"""
            if 主题 is not 会话:
                return#只看本会话
            if 事件['type']=='user/message' and 是否本源(事件['data']):
                自身.保留={'seq':事件['seq'],'text':取文本(事件['data'])}#更新保留快照
                自身._已见本源=True#已见
            elif 自身.保留 is not None and 是否替换表面事件(事件):
                来源序号=事件['sourceEventSeqs'] if 'sourceEventSeqs' in 事件 else None#被替换序号
                if 来源序号 is not None and 自身.保留['seq'] in 来源序号:
                    自身.保留=None#清掉保留
        上下文.监听('session/event',跟随)#跟随会话事件

    def 投影(自身,当前,段落列表):
        """仅当保留值与当前渲染不同时才创建未提交快照。"""
        从未有过=not 自身._已见本源 and 自身.保留 is None#从未有过快照
        if 从未有过 and len(当前)==0:
            return None#从未有过且当前为空则无需
        快照=已清空 if len(当前)==0 else 当前#空则用清空标记
        保留文本=自身.保留['text'] if isinstance(自身.保留,dict) else None#上次文本
        if 保留文本==快照:
            return None#文本未变则无需
        if len(段落列表)==0:
            来源={'kind':'plugin','plugin':源}#无段落则仅插件源
        else:
            来源={'kind':'plugin','plugin':源,'form':'snapshot','sections':段落列表}#有则带快照段落
        return 创建用户消息({
            'content':[{'type':'text','text':快照}],#单文本块
            'source':来源,#插件来源
        })#候选消息
