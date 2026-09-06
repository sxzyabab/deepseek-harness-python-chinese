"""订阅并分发一个稳定 Context 键，不观察兄弟节点。

对齐上游 `ui-conversation/src/client/chat/ChatNodeSeat.tsx`。公开面仅中文名。
属性与快照为 dict；节点仓为含 get 的 dict。
"""

__all__=['节点席']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 空渲染槽(*位置参数,**关键字参数):
    """未注入槽渲染时不画。"""
    return None#不画

class 节点席:
    """按 nodeKey 订阅，经 conversation.chat.node 分发。"""

    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """节点缺席返回 None。"""
        属性=自身.属性#props
        节点键=属性['nodeKey'] if 'nodeKey' in 属性 else None#键
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#槽
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        节点=None#节点
        if 用会话 is not None:#有钩
            def 取节点(快照,钉键=节点键):
                """从表取。"""
                聊天=快照['chat'] if 快照 is not None and 'chat' in 快照 else None#聊天
                表=聊天['nodes'] if 聊天 is not None and 'nodes' in 聊天 else None#仓
                if 表 is None:#无
                    return None#无
                return 表['get'](钉键)#仓 get
            节点=用会话(取节点)#取
        if 节点 is None:#缺席
            return None#空
        属主={#属主份额
            'selectedCallId':属性['selectedCallId'] if 'selectedCallId' in 属性 else None,#选中
            'cwd':属性['cwd'] if 'cwd' in 属性 else None,#cwd
            'openFile':属性['openFile'] if 'openFile' in 属性 else None,#开文件
            'inspectCall':属性['inspectCall'] if 'inspectCall' in 属性 else None,#检查
            'forkAt':属性['forkAt'] if 'forkAt' in 属性 else None,#分叉
            'loadImage':属性['loadImage'] if 'loadImage' in 属性 else None,#图
            'fileMentions':属性['fileMentions'] if 'fileMentions' in 属性 else None,#提及
            'node':节点,#节点
        }#结束属主
        种=节点['kind'] if 'kind' in 节点 else None#kind
        键=节点['key'] if 'key' in 节点 else None#key
        载荷=节点['data'] if 'data' in 节点 else None#载荷
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
                    'payload':载荷,#载荷
                },#结束回退
            }),#结束槽
        }#结束流项
