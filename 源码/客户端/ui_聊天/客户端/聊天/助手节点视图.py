"""助手步骤节点视图。

对齐上游 `ui-chat/src/client/chat/AssistantNodeView.tsx`。公开面仅中文名。
"""
from .助手Markdown import 助手Markdown#块体
from .消息图标动作 import 消息图标动作#动作行

__all__=['助手节点视图']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 助手节点视图:#assistant-step 键
    """Markdown 体 + 动作行。"""

    def __init__(自身,属性=None):#构造
        """记下。"""
        自身.属性=属性 or {}#合成
        自身.体=助手Markdown()#体
        自身.动作=消息图标动作()#动作

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """助手行。"""
        属性=自身.属性#props
        节点=取字段(属性,'node') or {}#节点
        数据=取字段(节点,'data') or 节点#数据
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        状态=取字段(数据,'status')#态
        流式=状态=='running'#流式
        中断=状态=='interrupted'#中断
        return {'type':'assistant-node','status':状态,'body':自身.体({'blocks':取字段(数据,'blocks'),'streaming':流式,'interrupted':中断,'t':翻译,'loadImage':取字段(属性,'loadImage'),'mentions':取字段(属性,'fileMentions')}),'actions':自身.动作({'node':数据,'t':翻译,'forkAt':取字段(属性,'forkAt')}) if not 流式 else None,'cssModule':'助手节点视图.module.css'}#视图

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
