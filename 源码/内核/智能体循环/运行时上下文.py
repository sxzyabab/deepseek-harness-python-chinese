"""动态运行时上下文的可持久化投影状态。"""
from ...模型后端.llm import 创建用户消息
from ..会话 import 是否替换表面事件
from .辅助 import 取

源='@deepseek-ai/dsh-system-prompt'#本投影归属的插件源
已清空='Current runtime context: none. Earlier runtime-context snapshots no longer apply.'#清空标记文案

def 是否本源(消息):
    """消息是否由本投影插件拥有。"""
    来源=取(消息,'source')#消息来源
    return 取(来源,'kind')=='plugin' and 取(来源,'plugin')==源#插件源且插件名匹配

def 取文本(消息):
    """取出单文本块消息的文本；否则缺省。"""
    内容=取(消息,'content') or []#内容块
    if len(内容)!=1:
        return None#非单块
    块=内容[0]#首块
    if 取(块,'type')!='text':
        return None#非文本
    return 取(块,'text')#文本

class 运行时上下文投影:
    """跟踪上次保留的运行时上下文快照，但不拥有其提交。"""
    def __init__(自身,上下文对象,会话):
        """先一次性恢复投影状态，再跟随权威会话事件。"""
        自身.保留=None#尚未扫描
        自身._已见本源=False#是否见过本源消息
        表面=set(会话.surface.nodes)#当前表面节点
        下标=len(会话.events)-1#从后往前
        while 下标>=0:
            事件=会话.events[下标]#当前事件
            if 取(事件,'type')!='user/message' or not 是否本源(取(事件,'data')):
                下标-=1#非本源用户消息
                continue#继续往前
            if not 自身._已见本源:
                自身.保留=False#见过本源则至少标成未保留
                自身._已见本源=True#已见
            if 取(事件,'seq') in 表面:
                自身.保留={'seq':取(事件,'seq'),'text':取文本(取(事件,'data'))}#记下该快照
                break#已找到最近保留
            下标-=1#继续往前
        def 跟随(主题,事件):
            """跟随本会话事件。"""
            if 主题 is not 会话:
                return#只看本会话
            if 取(事件,'type')=='user/message' and 是否本源(取(事件,'data')):
                自身.保留={'seq':取(事件,'seq'),'text':取文本(取(事件,'data'))}#更新保留快照
                自身._已见本源=True#已见
            elif 自身.保留 and 是否替换表面事件(事件):
                来源序号=取(事件,'sourceEventSeqs')#被替换序号
                if 来源序号 is not None and 自身.保留['seq'] in 来源序号:
                    自身.保留=False#清掉保留
        上下文对象.on('session/event',跟随)#跟随会话事件

    def 投影(自身,当前,段落们):
        """仅当保留值与当前渲染不同时才创建未提交快照。"""
        从未有过=not 自身._已见本源 and 自身.保留 is None#从未有过快照
        if 从未有过 and len(当前)==0:
            return None#从未有过且当前为空则无需
        快照=已清空 if len(当前)==0 else 当前#空则用清空标记
        保留文本=自身.保留['text'] if isinstance(自身.保留,dict) else None#上次文本
        if 保留文本==快照:
            return None#文本未变则无需
        if len(段落们)==0:
            来源={'kind':'plugin','plugin':源}#无段落则仅插件源
        else:
            来源={'kind':'plugin','plugin':源,'form':'snapshot','sections':段落们}#有则带快照段落
        return 创建用户消息({
            'content':[{'type':'text','text':快照}],#单文本块
            'source':来源,#插件来源
        })#候选消息
