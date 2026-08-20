"""聊天流节点席：按稳定 Context 键订阅并分发 conversation.chat.node。

对齐上游 `ui-conversation/src/client/chat/ChatNodeSeat.tsx`。公开面仅中文名。
"""

__all__=['聊天节点席']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 聊天节点席:#单行稳定席
    """订阅一 Node 键；兄弟更新不重挂。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """锚点包装 + 槽分发或 JSON 回退。"""
        属性=自身.属性#props
        节点键=取字段(属性,'nodeKey')#键
        用会话=取字段(属性,'useSession')#会话
        渲染槽=取字段(属性,'renderSlot',lambda *_a,**_k:None)#槽
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        节点=None#节点
        if 用会话 is not None and 节点键 is not None:#可读
            def 选(快照):#取节点
                """chat.nodes.get。"""
                表=取字段(取字段(快照,'chat'),'nodes')#表
                if 表 is None:#无
                    return None#无
                取=getattr(表,'get',None)#get
                return 取(节点键) if callable(取) else (表.get(节点键) if isinstance(表,dict) else None)#节点
            节点=用会话(选)#投影
        if 节点 is None:#未物化
            return None#不画
        属主={#属主份额
            'selectedCallId':取字段(属性,'selectedCallId'),#选中调用
            'cwd':取字段(属性,'cwd'),#工作目录
            'openFile':取字段(属性,'openFile'),#打开文件
            'inspectCall':取字段(属性,'inspectCall'),#检视
            'forkAt':取字段(属性,'forkAt'),#分叉
            'loadImage':取字段(属性,'loadImage'),#载图
            'fileMentions':取字段(属性,'fileMentions'),#提及
            'node':节点,#节点
        }#结束
        种=取字段(节点,'kind')#kind
        回退={#未知表面
            'type':'json-block',#JSON
            'label':翻译('message.unknownSurface',{'type':种}),#标签
            'payload':取字段(节点,'data'),#载荷
            'truncatedLabel':lambda 总:翻译('json.truncated',{'total':总}),#截断
        }#结束
        return {#视图
            'type':'chat-node-seat',#类型
            'anchorKey':取字段(节点,'key'),#锚
            'flowKey':取字段(节点,'key'),#流键
            'flowKind':种,#种
            'node':渲染槽('conversation.chat.node',属主,{'entryKey':种,'hookContext':节点键,'fallback':回退}),#分发
            'cssModule':'聊天视图.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
