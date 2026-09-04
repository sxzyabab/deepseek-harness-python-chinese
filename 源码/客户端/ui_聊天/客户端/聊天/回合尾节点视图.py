"""回合尾：扩展链 + 助手 IconActions + 用量/时间胶囊。

对齐上游 `ui-chat/src/client/chat/TurnTailNodeView.tsx`。公开面仅中文名。
"""
from .消息图标动作 import 消息图标动作#图标行
from .回合助手 import 助手文本#闭包正文
from .回合用量面板 import 回合用量面板,回合时间面板#胶囊

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
        """记下。"""
        自身.属性=属性 or {}#合成
        自身.动作=消息图标动作()#动作
        自身.用量=回合用量面板()#用量
        自身.时间=回合时间面板()#时间

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """无 turn 返回 None。"""
        属性=自身.属性#props
        节点=取字段(属性,'node')#节点
        数据=取字段(节点,'data')#数据
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        用聊天=取字段(属性,'useChat')#聊天
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
        是最新=False#最新
        if callable(用聊天):#有
            def 判后(快照):#后聊天节点
                """本回合末键是否本节点。"""
                位表=取字段(快照,'locations')#位
                取回=取字段(位表,'getTurn')#getTurn
                if not callable(取回):#无
                    return False#否
                列=取回(取字段(数据,'turn')) or []#列
                末键=列[-1] if 列 else None#末
                return 末键!=取字段(节点,'key')#后
            def 判最新(快照):#是否最新回合
                """timeline.turnOrder 末。"""
                序=取字段(取字段(快照,'timeline'),'turnOrder') or []#序
                return bool(序) and 序[-1]==取字段(数据,'turn')#末
            有后节点=bool(用聊天(判后))#后
            是最新=bool(用聊天(判最新))#最新
        收尾=取字段(数据,'closing')#closing
        序号=取字段(取字段(收尾,'finalNode'),'seq') if 收尾 is not None else 取字段(数据,'seq')#seq
        属主={'turn':回合,'seq':序号,'openFile':打开文件}#属主
        尾=渲染链('conversation.chat.turnTail',属主) if callable(渲染链) else None#链
        if 收尾 is None:#无收尾
            if 尾 is None:#空
                return None#不画
            return {'type':'turn-tail','className':'root','tail':尾,'cssModule':'回合尾节点视图.module.css'}#仅链
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
        用量动作=[]#胶囊
        if 取字段(数据,'tokenUsage') is not None:#有用量
            用量动作.append(自身.用量({'usage':取字段(数据,'tokenUsage'),'t':翻译}))#用量
        if 运行毫秒 is not None:#有墙钟
            用量动作.append(自身.时间({'runMs':运行毫秒,'tokensPerSecond':取字段(数据,'tokensPerSecond'),'ttftMs':取字段(数据,'ttftMs'),'t':翻译}))#时间
        动作视图=自身.动作({'text':助手文本(取字段(收尾,'blocks')),'time':取字段(收尾,'time'),'clock':'end','onBranch':分支,'branchUnavailable':bool(取字段(数据,'branchUnavailable')) or 有后节点,'extraActions':助手动作,'usageAction':用量动作,'t':翻译})#动作
        return {'type':'turn-tail','className':'root','turn':取字段(数据,'turn'),'actionsReveal':'always' if 是最新 else 'hover','tail':尾,'actions':动作视图,'cssModule':'回合尾节点视图.module.css'}#尾

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
