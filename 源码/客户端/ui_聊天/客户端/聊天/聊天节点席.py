"""聊天流节点席：订阅稳定键、施加过程可见性并分发 conversation.chat.node。

对齐上游 `ui-chat/src/client/chat/ChatNodeSeat.tsx`。公开面仅中文名。
"""
from ..约定.回合过程 import 回合过程独立种类#过程折叠独立种类
from ..仓库 import 已存回合过程条目#持久过程开合
from .可搜索隐藏 import 可搜索隐藏#可搜索隐藏

__all__=['聊天节点席']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 回合数据(节点):#取回合数据 store
    """仅 turn/step 位置。"""
    位置=取字段(节点,'location')#位置
    种=取字段(位置,'kind')#种
    if 种 in ('turn','step'):#有
        return 取字段(取字段(位置,'turn'),'data')#数据
    return None#无

def 回合号(节点):#取回合号
    """仅 turn/step。"""
    位置=取字段(节点,'location')#位置
    种=取字段(位置,'kind')#种
    if 种 in ('turn','step'):#有
        return 取字段(取字段(位置,'turn'),'turn')#号
    return None#无

class 聊天节点席:#单行稳定席
    """订阅一 Node 键；兄弟更新不重挂。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """过程折叠 + 槽分发或 JSON 回退。"""
        属性=自身.属性#props
        节点键=取字段(属性,'nodeKey')#键
        用节点=取字段(属性,'useChatNode')#读节点
        用过程=取字段(属性,'useChatNodeProcess')#过程呈现
        用仓=取字段(属性,'useStore')#UI store
        动作=取字段(属性,'actions') or {}#动作
        渲染槽=取字段(属性,'renderSlot',lambda *_a,**_k:None)#槽
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        紧凑=bool(取字段(属性,'compactTranscript'))#紧凑
        历史不全=bool(取字段(属性,'historyIncomplete'))#历史不全
        节点=用节点(节点键) if callable(用节点) else None#节点
        if 节点 is None:#未物化
            return None#不画
        过程呈现=用过程(节点键) if callable(用过程) else None#呈现
        规格=取字段(过程呈现,'spec')#规格
        存条目=用仓(lambda 态:已存回合过程条目(态,取字段(规格,'turn'))) if callable(用仓) and 规格 is not None else None#存
        过程条目=存条目 if 规格 is not None and 取字段(规格,'answerStep') is not None and 取字段(存条目,'answerStep')==取字段(规格,'answerStep') else None#匹配
        过程开=过程条目 is not None#开合
        def 设开(开):#写开合
            """写入 store。"""
            写=取字段(动作,'setTurnProcessOpen')#写
            if callable(写) and 规格 is not None and 取字段(规格,'answerStep') is not None:#可写
                写(取字段(规格,'turn'),取字段(规格,'answerStep'),开)#写
        窗口就绪=规格 is not None and 过程呈现 is not None and 紧凑 and 取字段(规格,'answerAnchorSeq') is not None and 取字段(过程呈现,'turn')==取字段(规格,'turn') and bool(取字段(过程呈现,'turnClosed')) and not 历史不全#就绪
        锚=取字段(节点,'anchorSeq')#锚
        种=取字段(节点,'kind')#种
        成员=窗口就绪 and 种 not in 回合过程独立种类 and 锚 is not None and 锚>=取字段(规格,'processStartSeq') and 锚<取字段(规格,'answerAnchorSeq')#成员
        答案=窗口就绪 and 种=='assistant-step' and 取字段(取字段(节点,'data'),'step')==取字段(规格,'answerStep')#答案
        持披露=种=='turn-process' or 答案#披露主
        可折=窗口就绪 and (成员 or (持披露 and (bool(取字段(过程呈现,'hasExternalProcess')) or bool(取字段(规格,'inlineReasoning')))))#可折
        过程面={'spec':规格,'foldable':可折,'open':过程开,'setOpen':设开} if 规格 is not None else None#过程面
        控件失活=种=='turn-process' and not 可折#失活
        紧凑答=答案 and 可折 and bool(取字段(过程呈现,'compactAnswer')) and not 过程开#紧凑答
        过程隐=控件失活 or (可折 and 成员 and not 过程开)#隐藏
        def 揭开():#查找命中展开
            """成员则开。"""
            if 成员:#成员
                设开(True)#开
        包装=可搜索隐藏(过程隐,揭开)()#包装
        属主={'selectedCallId':取字段(属性,'selectedCallId'),'cwd':取字段(属性,'cwd'),'openFile':取字段(属性,'openFile'),'inspectCall':取字段(属性,'inspectCall'),'forkAt':取字段(属性,'forkAt'),'loadImage':取字段(属性,'loadImage'),'renderMessageImages':取字段(属性,'renderMessageImages'),'fileMentions':取字段(属性,'fileMentions'),'turnProcess':过程面,'node':节点}#属主
        回退={'type':'json-block','label':翻译('message.unknownSurface',{'type':种}),'payload':取字段(节点,'data'),'truncatedLabel':lambda 总:翻译('json.truncated',{'total':总})}#回退
        return {'type':'chat-node-seat','wrapper':包装,'anchorKey':取字段(节点,'key'),'flowKey':取字段(节点,'key'),'flowKind':种,'turn':回合号(节点),'processMember':成员 or None,'processHidden':过程隐 or None,'processAnswer':紧凑答 or None,'node':渲染槽('conversation.chat.node',属主,{'entryKey':种,'hookContext':回合数据(节点),'fallback':回退}),'cssModule':'聊天视图.module.css'}#视图

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
