"""消息项：用户泡、重试、回合错、插话等简单聊天节点。

对齐上游 `ui-conversation/src/client/chat/MessageItem.tsx`。公开面仅中文名。
"""
import math#重试秒
import time#倒计时

__all__=['内容分片','重试秒数','模型重试行','回合错行','回合顶格行','待插话泡','用户消息行']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 内容分片(内容):#拆 text/image/rest
    """用户消息内容分片。"""
    文本们=[]#文本
    图们=[]#图
    其余=[]#其余
    for 块 in 内容 or []:#块
        类型=取字段(块,'type')#类型
        if 类型=='text' and isinstance(取字段(块,'text'),str):#文本
            文本们.append(取字段(块,'text'))#收
        elif 类型=='image' and 取字段(块,'attachment') is not None:#图
            图们.append({'attachment':取字段(块,'attachment')})#收
        else:#其余
            其余.append(块)#收
    return {'text':''.join(文本们),'images':图们,'rest':其余}#分片

def 重试秒数(毫秒):#至少 1 秒
    """ceil(ms/1000) 下限 1。"""
    return max(1,math.ceil(毫秒/1000))#秒

class 模型重试行:#重试披露
    """倒计时挂在首次渲染。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成
        节点=取字段(自身.属性,'node') or {}#节点
        自身.截止=int(time.time()*1000)+int(取字段(节点,'delayMs') or 0)#截止

    def 更新(自身,属性):#刷新
        """刷新；delay/seq 变则重锚。"""
        旧=取字段(自身.属性,'node')#旧
        自身.属性=属性 or {}#新
        新=取字段(自身.属性,'node')#新
        if 取字段(旧,'delayMs')!=取字段(新,'delayMs') or 取字段(旧,'seq')!=取字段(新,'seq'):#重锚
            自身.截止=int(time.time()*1000)+int(取字段(新,'delayMs') or 0)#截止

    def 渲染(自身):#结构树
        """重试 details。"""
        属性=自身.属性#props
        节点=取字段(属性,'node') or {}#节点
        活跃=bool(取字段(属性,'active'))#活跃
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        计划秒=重试秒数(取字段(节点,'delayMs') or 0)#计划
        最大=取字段(节点,'maxRetries') if 取字段(节点,'mode')=='normal' else '∞'#最大
        剩余=重试秒数(自身.截止-int(time.time()*1000)) if 活跃 else 计划秒#秒
        态=取字段(节点,'retryState')#态
        if 活跃:#活跃
            标签=翻译('message.retry.active')#活
        elif 态=='cancelled':#取消
            标签=翻译('message.retry.cancelled')#取消
        elif 态=='started':#已开
            标签=翻译('message.retry.started')#开
        else:#排定
            标签=翻译('message.retry.scheduled')#排
        return {#重试
            'type':'model-retry',#类型
            'active':活跃,#活
            'status':翻译('message.retry.status',{'label':标签,'retry':取字段(节点,'retry'),'maximum':最大,'seconds':剩余}),#状态
            'delayLabel':翻译('message.retry.delay'),#延迟标
            'delayMs':取字段(节点,'delayMs'),#延迟
            'failureLabel':翻译('message.retry.failure'),#失败标
            'failure':取字段(取字段(节点,'failure'),'message'),#失败文
            'cssModule':'消息项.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 回合错行:#回合失败
    """终端失败反馈。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """错行。"""
        节点=取字段(自身.属性,'node') or {}#节点
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        return {#错
            'type':'turn-error',#类型
            'title':翻译('message.turnError'),#标题
            'message':取字段(节点,'message'),#消息
            'code':取字段(节点,'code'),#码
            'dot':'error',#点
            'cssModule':'消息项.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 回合顶格行:#max tokens
    """输出顶格提示。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """警告行。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        return {#顶格
            'type':'turn-max-tokens',#类型
            'title':翻译('message.maxTokens'),#标题
            'hint':翻译('message.maxTokens.hint'),#提示
            'dot':'warning',#点
            'cssModule':'消息项.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 待插话泡:#pending steering
    """进行中插话预览。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """右对齐泡。"""
        分片=内容分片(取字段(自身.属性,'content'))#分片
        return {#泡
            'type':'pending-steering',#类型
            'text':分片['text'],#文
            'images':分片['images'],#图
            'pending':True,#待
            'cssModule':'消息项.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲

class 用户消息行:#用户泡
    """右对齐用户消息。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """用户行。"""
        节点=取字段(自身.属性,'node') or {}#节点
        分片=内容分片(取字段(节点,'content'))#分片
        return {#用户
            'type':'user-message',#类型
            'text':分片['text'],#文
            'images':分片['images'],#图
            'rest':分片['rest'],#其余
            'cssModule':'消息项.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
