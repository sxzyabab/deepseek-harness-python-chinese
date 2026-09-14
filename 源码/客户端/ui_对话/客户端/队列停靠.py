from .服务 import 对话错误#本包异常

__all__=['队列停靠','队列停靠条目']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 取队列(快照):
    """会话 queue 字段。"""
    队列=快照['queue'] if 快照 is not None and 'queue' in 快照 else None#队列
    return 队列 if 队列 is not None else []#空容器仍返回

def 取可改(快照):
    """无 subagent 才可改。"""
    return 快照 is None or 'subagent' not in 快照 or 快照['subagent'] is None#可改

def 取文本(内容):
    """从 content 块拼文本。"""
    if isinstance(内容,str):#已是串
        return 内容#串
    if not isinstance(内容,(list,tuple)):#非列表
        return ''#空
    段=[]#段
    for 块 in 内容:#块
        种=块['type'] if isinstance(块,dict) and 'type' in 块 else None#种
        文=块['text'] if isinstance(块,dict) and 'text' in 块 else None#文
        if 种=='text' and isinstance(文,str):#文本块
            段.append(文)#收
    return ''.join(段)#拼

class 队列停靠:
    """单条直出；多条默认可折叠计数头。"""

    def __init__(自身,属性=None):
        """记下 props 与本地态。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.折叠=True#折叠
        自身.编辑=None#编辑 {id,text}
        自身.忙碌=None#忙碌 id

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 开编(自身,标识,正文,可改):
        """开始编辑一行。"""
        if 可改 is True:#可
            自身.编辑={'id':标识,'text':正文}#开

    def 取消编(自身):
        """取消编辑。"""
        自身.编辑=None#清

    def 改编(自身,标识,文):
        """改编辑正文。"""
        自身.编辑={'id':标识,'text':文}#改

    def 切换折叠(自身,交互中):
        """非交互才翻转。"""
        if 交互中 is False:#闲
            自身.折叠=not 自身.折叠#翻

    def 渲染(自身):
        """空队列返回 None。"""
        属性=自身.属性#props
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话
        更新队列=属性['updateQueue'] if 'updateQueue' in 属性 else None#更新
        通知=属性['notify'] if 'notify' in 属性 else None#通知
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        收件=用会话(取队列) if 用会话 is not None else []#收件
        队列=[行 for 行 in 收件 if 'placement' in 行 and 行['placement']=='queued']#排队
        可改=用会话(取可改) if 用会话 is not None else True#可改
        if len(队列)==0:#空
            return None#不画
        编标识=自身.编辑['id'] if 自身.编辑 is not None and 'id' in 自身.编辑 else None#编 id
        仍在=False#是否仍在队列
        for 行 in 队列:#扫
            if 'id' in 行 and 行['id']==编标识:#命中
                仍在=True#在
                break#停
        if 自身.编辑 is not None and (可改 is False or 仍在 is False):#编辑失效
            自身.编辑=None#清
        编标识=自身.编辑['id'] if 自身.编辑 is not None and 'id' in 自身.编辑 else None#编 id
        if len(队列)==0 and 自身.折叠 is False:#空则折
            自身.折叠=True#折
        交互中=可改 is True and (自身.编辑 is not None or 自身.忙碌 is not None)#交互
        展开=自身.折叠 is False or 交互中 is True#展开
        列表可见=len(队列)==1 or 展开 is True#列表
        行视图=[]#行
        for 行 in 队列:#逐行
            标识=行['id'] if 'id' in 行 else None#id
            正文=取文本(行['content'] if 'content' in 行 else None)#正文
            在编=自身.编辑 is not None and 编标识==标识#编辑中
            编文=自身.编辑['text'] if 在编 is True and 'text' in 自身.编辑 else None#编文
            def 开编(钉标识=标识,钉正文=正文,钉可改=可改):
                """开编本行。"""
                自身.开编(钉标识,钉正文,钉可改)#开
            def 改编(文,钉标识=标识):
                """改本行。"""
                自身.改编(钉标识,文)#改
            def 存编(钉标识=标识,钉更新=更新队列,钉通知=通知,钉翻译=翻译):
                """存本行。"""
                自身._存编辑(钉标识,钉更新,钉通知,钉翻译)#存
            def 发送(钉标识=标识,钉更新=更新队列,钉通知=通知,钉翻译=翻译):
                """发本行。"""
                自身._动作(钉标识,{'kind':'send'},钉翻译('queue.sendFailed'),钉更新,钉通知)#发
            def 删除(钉标识=标识,钉更新=更新队列,钉通知=通知,钉翻译=翻译):
                """删本行。"""
                自身._动作(钉标识,{'kind':'delete'},钉翻译('queue.deleteFailed'),钉更新,钉通知)#删
            行视图.append({#行
                'id':标识,#id
                'text':正文,#文
                'editing':在编,#编
                'editText':编文,#编文
                'busy':自身.忙碌==标识,#忙
                'showLead':len(队列)==1,#单条带头标
                'onStartEdit':开编,#开编
                'onCancelEdit':自身.取消编,#取消
                'onEditChange':改编,#改
                'onSaveEdit':存编,#存
                'onSend':发送,#发
                'onDelete':删除,#删
            })#行结束
        def 折切():
            """折切。"""
            自身.切换折叠(交互中)#翻
        return {#停靠
            'type':'queue-dock',#类型
            'count':len(队列),#数
            'countLabel':翻译('queue.count',{'n':len(队列)}),#计数文
            'expanded':展开,#展
            'listVisible':列表可见,#列表
            'interactionActive':交互中,#交互
            'mutable':可改,#可改
            'header':len(队列)>1,#多条头
            'onToggle':折切,#折切
            'rows':行视图,#行
            'cssModule':'队列停靠.module.css',#样式
        }#视图结束

    def _动作(自身,标识,动作,失败文,更新队列,通知):
        """忙态围栏。"""
        自身.忙碌=标识#忙
        try:#派
            if 更新队列 is not None:#有
                更新队列(标识,动作)#派
            return True#成
        except 对话错误:#败
            if 通知 is not None:#有
                通知('error',失败文)#报
            return False#败
        finally:#清忙
            if 自身.忙碌==标识:#本项
                自身.忙碌=None#清

    def _存编辑(自身,标识,更新队列,通知,翻译):
        """写 edit 动作。"""
        if 自身.编辑 is None:#无
            return#停
        文=自身.编辑['text'] if 'text' in 自身.编辑 else ''#文
        if str(文).strip()=='':#无效
            return#停
        if 自身._动作(标识,{'kind':'edit','content':[{'type':'text','text':文}]},翻译('queue.editFailed'),更新队列,通知) is True:#成
            自身.编辑=None#清

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

def 队列停靠条目():
    """对齐 queueDockEntry：独立激活边界的 plain registrant。"""
    from .文案 import 命名空间#词典 NS
    def 应用(上下文):
        """终端 input-dock 条目（order 20）。"""
        def 注入(会话标识):
            """updateQueue + notify。"""
            作用域=上下文.sessions.scope(会话标识)#作用域
            if 作用域 is None:#无
                raise 对话错误('queue dock: session "'+str(会话标识)+'" resolved no scope')#抛
            会话=作用域.获取服务('conversation')#conversation
            if 会话 is None:#无
                raise 对话错误('queue dock: conversation service unavailable')#抛
            def 通知(级别,正文):
                """input.for(actx).notify。"""
                会话.input.按作用域取门面(作用域).notify(级别,正文)#通知
            def 改队列(项标识,动作):
                """改队列。"""
                return 会话.updateQueue(项标识,动作)#改
            return {#注入面
                'updateQueue':改队列,#改队列
                'notify':通知,#通知
            }#结束
        def 登记():
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
