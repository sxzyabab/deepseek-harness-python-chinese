"""回合尾：扩展链 + 助手 IconActions。

对齐上游 `ui-conversation/src/client/chat/TurnTailNodeView.tsx`。公开面仅中文名。
"""
from .消息图标动作 import 消息图标动作#图标行
from .回合助手 import 助手文本#闭包正文

__all__=['回合尾节点视图']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 回合尾节点视图:#turn-tail
    """turnTail 链 + 可选消息动作。"""

    def __init__(自身,属性=None):#构造
        """记下 props 与动作行。"""
        自身.属性=属性 or {}#合成
        自身.动作=消息图标动作()#动作

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """无 turn 返回 None。"""
        属性=自身.属性#props
        节点=取字段(属性,'node')#节点
        数据=取字段(节点,'data')#数据
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        用会话=取字段(属性,'useSession')#会话
        打开文件=取字段(属性,'openFile')#打开
        分叉=取字段(属性,'forkAt')#分叉
        渲染槽=取字段(属性,'renderSlot',lambda *_:None)#槽
        渲染链=取字段(属性,'renderSlotChain',lambda *_:None)#链
        位置=取字段(节点,'location')#位置
        种=取字段(位置,'kind')#种
        回合=取字段(位置,'turn') if 种 in ('turn','step') else None#回合
        if 回合 is None:#无
            return None#停
        有后节点=False#后
        if callable(用会话):#有
            def 判后(快照):#后聊天节点
                """本回合末键是否本节点。"""
                聊天=取字段(快照,'chat')#聊天
                位表=取字段(聊天,'locations')#位
                取回=取字段(位表,'getTurn')#getTurn
                if not callable(取回):#无
                    return False#否
                列=取回(取字段(数据,'turn')) or []#列
                末键=列[-1] if 列 else None#空列对齐 at(-1)→undefined
                return 末键!=取字段(节点,'key')#后
            有后节点=bool(用会话(判后))#后
        收尾=取字段(数据,'closing')#closing
        序号=取字段(取字段(收尾,'finalNode'),'seq') if 收尾 is not None else 取字段(数据,'seq')#seq
        属主={'turn':回合,'seq':序号,'openFile':打开文件}#属主
        尾=渲染链('conversation.chat.turnTail',属主) if callable(渲染链) else None#链
        if 收尾 is None:#无收尾
            if 尾 is None:#空
                return None#不画
            return {'type':'turn-tail','className':'root','tail':尾,'cssModule':'聊天/回合尾节点.module.css'}#仅链
        起点=取字段(取字段(回合,'start'),'time')#start
        终点=取字段(取字段(回合,'end'),'time')#end
        运行毫秒=None if 起点 is None or 终点 is None else max(0,终点-起点)#时长
        消息标识=取字段(取字段(收尾,'finalNode'),'messageId')#消息
        助手动作=None if 消息标识 is None else 渲染槽('conversation.chat.assistant-actions',{'messageId':消息标识})#动作槽
        定稿序号=取字段(取字段(收尾,'finalNode'),'seq')#分支点
        def 分支():#onBranch
            """分叉到定稿序号。"""
            if callable(分叉):#有
                分叉(定稿序号)#叉
        动作视图=自身.动作({#图标行
            'text':助手文本(取字段(收尾,'blocks')),#正文
            'time':取字段(收尾,'time'),#时
            'runMs':运行毫秒,#时长
            'ttftMs':取字段(数据,'ttftMs'),#首字
            'tokensPerSecond':取字段(数据,'tokensPerSecond'),#速率
            'clock':'end',#钟
            'onBranch':分支,#分支
            'branchUnavailable':bool(取字段(数据,'branchUnavailable')) or 有后节点,#不可分支
            'className':'actions',#类
            'extraActions':助手动作,#扩展
            't':翻译,#文案
        })#动作结束
        return {#尾
            'type':'turn-tail',#类型
            'className':'root',#根
            'data-turn-tail':取字段(数据,'turn'),#回合
            'data-time-hover-root':True,#悬停根
            'tail':尾,#链
            'actions':动作视图,#动作
            'cssModule':'聊天/回合尾节点.module.css',#样式
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
