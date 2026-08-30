"""订阅并分发一个稳定 Context 键，不观察兄弟节点。

对齐上游 `ui-conversation/src/client/chat/ChatNodeSeat.tsx`。公开面仅中文名。
"""

__all__=['节点席']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 节点席:#单节点席
    """按 nodeKey 订阅，经 conversation.chat.node 分发。"""

    def __init__(自身,属性=None):#记下 props
        """记下合成 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """节点缺席返回 None。"""
        属性=自身.属性#props
        节点键=取字段(属性,'nodeKey')#键
        用会话=取字段(属性,'useSession')#会话
        渲染槽=取字段(属性,'renderSlot',lambda *a,**k:None)#槽
        翻译=取字段(属性,'t',lambda 键,**_:键)#文案
        节点=None#节点
        if callable(用会话):#有钩
            def 取节点(快照):#选择器
                """从表取。"""
                表=取字段(取字段(快照,'chat'),'nodes')#表
                if 表 is None:#无
                    return None#无
                取=getattr(表,'get',None)#get
                return 取(节点键) if callable(取) else (表.get(节点键) if isinstance(表,dict) else None)#节点
            节点=用会话(取节点)#取
        if 节点 is None:#缺席
            return None#空
        属主={#属主份额
            'selectedCallId':取字段(属性,'selectedCallId'),#选中
            'cwd':取字段(属性,'cwd'),#cwd
            'openFile':取字段(属性,'openFile'),#开文件
            'inspectCall':取字段(属性,'inspectCall'),#检查
            'forkAt':取字段(属性,'forkAt'),#分叉
            'loadImage':取字段(属性,'loadImage'),#图
            'fileMentions':取字段(属性,'fileMentions'),#提及
            'node':节点,#节点
        }#结束属主
        种=取字段(节点,'kind')#kind
        键=取字段(节点,'key')#key
        return {#流项
            'className':'flowItem',#类
            'data-chat-anchor-key':键,#锚
            'data-chat-flow-key':键,#流键
            'data-chat-flow-kind':种,#种
            'slot':渲染槽('conversation.chat.node',属主,{#分发
                'entryKey':种,#键控
                'hookContext':节点键,#钩上下文
                'fallback':{#未知面
                    'type':'JsonBlock',#块
                    'label':翻译('message.unknownSurface',{'type':种}),#标签
                    'payload':取字段(节点,'data'),#载荷
                },#结束回退
            }),#结束槽
        }#结束流项
