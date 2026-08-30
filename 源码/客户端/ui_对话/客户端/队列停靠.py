"""队列停靠：输入区上方的排队条。

对齐上游 `ui-conversation/src/client/queue/QueueDock.tsx`。公开面仅中文名。
"""

__all__=['队列停靠','队列停靠条目']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 取文本(内容):#队列正文
    """从 content 块拼文本。"""
    if isinstance(内容,str):#已是串
        return 内容#串
    if not isinstance(内容,(list,tuple)):#非列表
        return ''#空
    段=[]#段
    for 块 in 内容:#块
        if isinstance(块,dict) and 块.get('type')=='text' and isinstance(块.get('text'),str):#文本块
            段.append(块['text'])#收
    return ''.join(段)#拼

class 队列停靠:#排队条
    """单条直出；多条默认可折叠计数头。"""

    def __init__(自身,属性=None):#构造
        """记下 props 与本地态。"""
        自身.属性=属性 or {}#合成
        自身.折叠=True#折叠
        自身.编辑=None#编辑 {id,text}
        自身.忙碌=None#忙碌 id

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """空队列返回 None。"""
        属性=自身.属性#props
        用会话=取字段(属性,'useSession')#会话
        更新队列=取字段(属性,'updateQueue')#更新
        通知=取字段(属性,'notify')#通知
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        收件=用会话(lambda s:取字段(s,'queue') or []) if 用会话 is not None else []#收件
        队列=[行 for 行 in 收件 if 取字段(行,'placement')=='queued']#排队
        可改=用会话(lambda s:取字段(s,'subagent') is None) if 用会话 is not None else True#可改
        if len(队列)==0:#空
            return None#不画
        if 自身.编辑 is not None and (not 可改 or not any(取字段(行,'id')==自身.编辑.get('id') for 行 in 队列)):#编辑失效
            自身.编辑=None#清
        if len(队列)==0 and not 自身.折叠:#空则折
            自身.折叠=True#折
        交互中=可改 and (自身.编辑 is not None or 自身.忙碌 is not None)#交互
        展开=not 自身.折叠 or 交互中#展开
        列表可见=len(队列)==1 or 展开#列表
        行视图=[]#行
        for 行 in 队列:#逐行
            标识=取字段(行,'id')#id
            正文=取文本(取字段(行,'content'))#正文
            在编=自身.编辑 is not None and 自身.编辑.get('id')==标识#编辑中
            行视图.append({#行
                'id':标识,#id
                'text':正文,#文
                'editing':在编,#编
                'editText':自身.编辑.get('text') if 在编 else None,#编文
                'busy':自身.忙碌==标识,#忙
                'showLead':len(队列)==1,#单条带头标
                'onStartEdit':(lambda 标识=标识,正文=正文:自身.__setattr__('编辑',{'id':标识,'text':正文}) if 可改 else None),#开编
                'onCancelEdit':lambda:自身.__setattr__('编辑',None),#取消
                'onEditChange':(lambda 文,标识=标识:自身.__setattr__('编辑',{'id':标识,'text':文})),#改
                'onSaveEdit':(lambda 标识=标识:自身._存编辑(标识,更新队列,通知,翻译)),#存
                'onSend':(lambda 标识=标识:自身._动作(标识,{'kind':'send'},翻译('queue.sendFailed'),更新队列,通知)),#发
                'onDelete':(lambda 标识=标识:自身._动作(标识,{'kind':'delete'},翻译('queue.deleteFailed'),更新队列,通知)),#删
            })#行结束
        return {#停靠
            'type':'queue-dock',#类型
            'count':len(队列),#数
            'countLabel':翻译('queue.count',{'n':len(队列)}),#计数文
            'expanded':展开,#展
            'listVisible':列表可见,#列表
            'interactionActive':交互中,#交互
            'mutable':可改,#可改
            'header':len(队列)>1,#多条头
            'onToggle':lambda:自身.__setattr__('折叠',not 自身.折叠) if not 交互中 else None,#折切
            'rows':行视图,#行
            'cssModule':'队列停靠.module.css',#样式
        }#视图结束

    def _动作(自身,标识,动作,失败文,更新队列,通知):#派动作
        """忙态围栏。"""
        自身.忙碌=标识#忙
        try:#派
            if 更新队列 is not None:#有
                更新队列(标识,动作)#派
            return True#成
        except Exception:#败
            if 通知 is not None:#有
                通知('error',失败文)#报
            return False#败
        finally:#清忙
            if 自身.忙碌==标识:#本项
                自身.忙碌=None#清

    def _存编辑(自身,标识,更新队列,通知,翻译):#存编辑
        """写 edit 动作。"""
        if 自身.编辑 is None or str(自身.编辑.get('text','')).strip()=='':#无效
            return#停
        文=自身.编辑['text']#文
        if 自身._动作(标识,{'kind':'edit','content':[{'type':'text','text':文}]},翻译('queue.editFailed'),更新队列,通知):#成
            自身.编辑=None#清

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

def 队列停靠条目():#登记插件形
    """对齐 queueDockEntry：独立激活边界的 plain registrant。"""
    from .文案 import 命名空间#词典 NS
    def 应用(上下文):#登记队列停靠
        """终端 input-dock 条目（order 20）。"""
        def 注入(会话标识):#按会话解析动作
            """updateQueue + notify。"""
            作用域=上下文.sessions.scope(会话标识)#作用域
            if 作用域 is None:#无
                raise Exception('queue dock: session "'+str(会话标识)+'" resolved no scope')#抛
            会话=作用域.get('conversation')#conversation
            if 会话 is None:#无
                raise Exception('queue dock: conversation service unavailable')#抛
            def 通知(级别,正文):#经输入机浮出
                """input.for(actx).notify。"""
                会话.input.for_(作用域).notify(级别,正文)#通知
            return {#注入面
                'updateQueue':lambda 项标识,动作:会话.updateQueue(项标识,动作),#改队列
                'notify':通知,#通知
            }#结束
        def 登记():#等停靠槽
            """register。"""
            return 上下文.slots.register({#条目
                'name':'conversation.input.dock',#停靠
                'id':'queue',#id
                'order':20,#序
                'locale':命名空间,#文案
                'inject':注入,#注入
            },队列停靠)#组件
        上下文.slots.inject('conversation.input.dock',登记)#等槽
    return {'name':'conversation-queue-dock','inject':['slots','conversation','sessions'],'apply':应用}#插件
