"""宿主 session/queue 帧与持久 user/message 之间的客户端队列镜像。

对齐上游 `runtime/src/client/sessions/queue-mirror.ts`。公开面仅中文名。
"""

__all__=['队列预览字数','会话队列镜像']#仅中文公开名

队列预览字数=200#队列预览字数上限

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 预览自(内容):#内容 → 单行预览
    """把内容块压成单行预览；超上限截断并加省略号。"""
    片段们=[]#各块展平
    for 块 in 内容:#逐块
        if 取字段(块,'type')=='text':#文本
            片段们.append(取字段(块,'text') or '')#正文
        else:#其它
            片段们.append('['+str(取字段(块,'type'))+']')#种类占位
    扁平=' '.join(片段们)#空格连接
    扁平=' '.join(扁平.split())#压空白
    字符们=list(扁平)#按码点切
    if len(字符们)>队列预览字数:#超上限
        return ''.join(字符们[0:队列预览字数])+'…'#截断加省略号
    return 扁平#原文

def 文本自(内容):#纯文本或不可编辑
    """全是 text 块才拼纯文本，否则 None。"""
    for 块 in 内容:#检查
        if 取字段(块,'type')!='text':#夹了非文本块
            return None#不能当可编辑正文
    return ''.join([(取字段(块,'text') or '') for 块 in 内容])#拼接全部 text 块

class 会话队列镜像:#队列镜像
    """权威的瞬时队列投影，以及持久化转向交接。"""

    def __init__(自身):#空队列
        """当前不可变投影。"""
        自身._当前=[]#当前行

    def 快照(自身):#读投影
        """返回当前不可变队列投影。"""
        return 自身._当前#调用方不得原地改

    def 重置(自身):#清空世代
        """在替换队列基线到达之前丢掉过期世代。

        @returns 是否移除过任何已投影的队列行。
        """
        if len(自身._当前)==0:#已经空
            return False#未变
        自身._当前=[]#换成空数组引用
        return True#投影变了

    def 替换(自身,项们):#整表替换
        """用一帧权威的流队列整表替换。

        @param 项们 - 完整的宿主队列快照。
        """
        行们=[]#映射成客户端行
        for 项 in 项们:#逐项
            消息=取字段(项,'message')#消息
            内容=取字段(消息,'content') or []#内容块
            行们.append({#客户端行
                'id':取字段(项,'id'),#队列项 id
                'messageId':取字段(消息,'id'),#消息 id，供持久交接
                'placement':取字段(项,'placement'),#排队位置
                'content':内容,#完整内容块
                'preview':预览自(内容),#单行预览
                'text':文本自(内容),#可编辑纯文本或 None
            })#结束
        自身._当前=行们#换表

    def 接纳持久(自身,事件):#持久交接
        """瞬时转向行在对应持久消息进入日志后退役。

        @param 事件 - 新近连续的持久 Session 事件。
        @returns 投影是否改变。
        """
        if 取字段(事件,'type')!='user/message':#只有用户消息能退役转向行
            return False#未变
        消息标识=取字段(取字段(事件,'data'),'id')#刚进入日志的消息 id
        下标=-1#找对应瞬时行
        查=0#扫描
        while 查<len(自身._当前):#找
            项=自身._当前[查]#当前行
            if 取字段(项,'placement')=='steering' and 取字段(项,'messageId')==消息标识:#命中
                下标=查#记下
                break#停
            查+=1#下一个
        if 下标<0:#队列里没有这行
            return False#未变
        自身._当前=[项 for 序,项 in enumerate(自身._当前) if 序!=下标]#按原下标剔除
        return True#投影变了
