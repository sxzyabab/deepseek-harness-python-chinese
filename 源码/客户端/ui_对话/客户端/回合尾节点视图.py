"""回合尾：扩展链 + 助手 IconActions。

对齐上游 `ui-conversation/src/client/chat/TurnTailNodeView.tsx`。公开面仅中文名。
属性、节点、快照为 dict。
"""
from .消息图标动作 import 消息图标动作#图标行
from .回合助手 import 助手文本#闭包正文

__all__=['回合尾节点视图']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 空渲染槽(*位置参数,**关键字参数):
    """未注入槽渲染时不画。"""
    return None#不画

class 回合尾节点视图:
    """turnTail 链 + 可选消息动作。"""

    def __init__(自身,属性=None):
        """记下 props 与动作行。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.动作=消息图标动作()#动作

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """无 turn 返回 None。"""
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 else None#节点
        数据=节点['data'] if 节点 is not None and 'data' in 节点 else None#数据
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话
        打开文件=属性['openFile'] if 'openFile' in 属性 else None#打开
        分叉=属性['forkAt'] if 'forkAt' in 属性 else None#分叉
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#槽
        渲染链=属性['renderSlotChain'] if 'renderSlotChain' in 属性 else 空渲染槽#链
        位置=节点['location'] if 节点 is not None and 'location' in 节点 else None#位置
        种=位置['kind'] if 位置 is not None and 'kind' in 位置 else None#种
        回合=位置['turn'] if 种 in ('turn','step') and 位置 is not None and 'turn' in 位置 else None#回合
        if 回合 is None:#无
            return None#停
        有后节点=False#后
        数据回合=数据['turn'] if 数据 is not None and 'turn' in 数据 else None#数据回合
        节点键=节点['key'] if 节点 is not None and 'key' in 节点 else None#键
        if 用会话 is not None:#有
            def 判后(快照,钉回合=数据回合,钉键=节点键):
                """本回合末键是否本节点。locations 为契约 dict。"""
                聊天=快照['chat'] if 快照 is not None and 'chat' in 快照 else None#聊天
                位表=聊天['locations'] if 聊天 is not None and 'locations' in 聊天 else None#位
                if 位表 is None:#无
                    return False#否
                列=位表['getTurn'](钉回合)#列
                列=列 if 列 is not None else []#列
                末键=列[-1] if len(列)>0 else None#空列对齐 at(-1)→undefined；判 length
                return 末键!=钉键#后
            有后节点=用会话(判后) is True#后
        收尾=数据['closing'] if 数据 is not None and 'closing' in 数据 else None#closing
        if 收尾 is not None and 'finalNode' in 收尾 and 收尾['finalNode'] is not None:#定稿序号
            序号=收尾['finalNode']['seq'] if 'seq' in 收尾['finalNode'] else None#seq
        else:#节点序号
            序号=数据['seq'] if 数据 is not None and 'seq' in 数据 else None#seq
        属主={'turn':回合,'seq':序号,'openFile':打开文件}#属主
        尾=渲染链('conversation.chat.turnTail',属主)#链
        if 收尾 is None:#无收尾
            if 尾 is None:#空
                return None#不画
            return {'type':'turn-tail','className':'root','tail':尾,'cssModule':'聊天/回合尾节点.module.css'}#仅链
        起=回合['start'] if 'start' in 回合 else None#start
        终=回合['end'] if 'end' in 回合 else None#end
        起点=起['time'] if 起 is not None and 'time' in 起 else None#起点
        终点=终['time'] if 终 is not None and 'time' in 终 else None#终点
        运行毫秒=None if 起点 is None or 终点 is None else max(0,终点-起点)#时长
        终节=收尾['finalNode'] if 'finalNode' in 收尾 else None#终节
        消息标识=终节['messageId'] if 终节 is not None and 'messageId' in 终节 else None#消息
        助手动作=None if 消息标识 is None else 渲染槽('conversation.chat.assistant-actions',{'messageId':消息标识})#动作槽
        定稿序号=终节['seq'] if 终节 is not None and 'seq' in 终节 else None#分支点
        def 分支(钉分叉=分叉,钉序号=定稿序号):
            """分叉到定稿序号。"""
            if 钉分叉 is not None:#有
                钉分叉(钉序号)#叉
        块列表=收尾['blocks'] if 'blocks' in 收尾 else None#块
        时=收尾['time'] if 'time' in 收尾 else None#时
        首字=数据['ttftMs'] if 数据 is not None and 'ttftMs' in 数据 else None#首字
        速率=数据['tokensPerSecond'] if 数据 is not None and 'tokensPerSecond' in 数据 else None#速率
        不可=数据['branchUnavailable'] is True if 数据 is not None and 'branchUnavailable' in 数据 else False#不可
        动作视图=自身.动作({#图标行
            'text':助手文本(块列表),#正文
            'time':时,#时
            'runMs':运行毫秒,#时长
            'ttftMs':首字,#首字
            'tokensPerSecond':速率,#速率
            'clock':'end',#钟
            'onBranch':分支,#分支
            'branchUnavailable':不可 is True or 有后节点 is True,#不可分支
            'className':'actions',#类
            'extraActions':助手动作,#扩展
            't':翻译,#文案
        })#动作结束
        return {#尾
            'type':'turn-tail',#类型
            'className':'root',#根
            'data-turn-tail':数据回合,#回合
            'data-time-hover-root':True,#悬停根
            'tail':尾,#链
            'actions':动作视图,#动作
            'cssModule':'聊天/回合尾节点.module.css',#样式
        }#结束

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
