"""按轮次物化的跨节点过程布局事实投影。

对齐上游 `ui-chat/src/client/conversation-nodes/turn-process-presentation.ts`。公开面仅中文名。
"""
from ..约定.回合过程 import 回合过程独立种类#独立种类
from .面辅助 import 取字段#字段

__all__=['同过程呈现','推导过程呈现','聊天回合过程投影器']#仅中文公开名

def 节点回合(节点):#从节点取轮次
    """turn/step 位置。"""
    位置=取字段(节点,'location')#位置
    种=取字段(位置,'kind')#种
    if 种 in ('turn','step'):#有
        return 取字段(取字段(位置,'turn'),'turn')#轮次
    return None#无

def 同过程呈现(左,右):#呈现相等判定
    """双侧字段与规格引用。"""
    if 左 is 右:#同引用
        return True#同
    if 左 is None or 右 is None:#单侧
        return False#异
    return (#字段
        取字段(左,'spec') is 取字段(右,'spec')#规格
        and 取字段(左,'turn')==取字段(右,'turn')#轮次
        and 取字段(左,'turnClosed')==取字段(右,'turnClosed')#已关
        and 取字段(左,'hasExternalProcess')==取字段(右,'hasExternalProcess')#外部
        and 取字段(左,'compactAnswer')==取字段(右,'compactAnswer')#紧凑
    )#结束

def 推导过程呈现(回合,位置们,节点们):#推导一轮过程呈现
    """无过程控件则缺席。"""
    键们=位置们.getTurn(回合) if hasattr(位置们,'getTurn') else []#轮内键
    控件=None#过程控件
    for 键 in 键们:#找
        节=节点们.get(键) if hasattr(节点们,'get') else None#节点
        if 取字段(节,'kind')=='turn-process':#控件
            控件=节#记下
            break#停
    if 控件 is None:#无
        return None#缺席
    规格=取字段(控件,'data')#规格
    位置=取字段(控件,'location')#位置
    if 取字段(位置,'kind') not in ('turn','step'):#无轮
        return None#缺
    开场人=None#开场人工锚
    for 键 in 键们:#扫开场
        节=节点们.get(键) if hasattr(节点们,'get') else None#节点
        种=取字段(节,'kind')#种
        if 种 in ('user','steering') and 取字段(节,'anchorSeq',0)<取字段(规格,'controlAnchorSeq',0):#开场
            锚=取字段(节,'anchorSeq')#锚
            开场人=锚 if 开场人 is None else min(开场人,锚)#最早
    有外部=False#外部过程
    紧凑=True#紧凑正文
    for 键 in 键们:#扫成员
        节=节点们.get(键) if hasattr(节点们,'get') else None#节点
        if 节 is None or 取字段(节,'kind')=='turn-process':#跳控件
            continue#下
        种=取字段(节,'kind')#种
        锚=取字段(节,'anchorSeq',0)#锚
        正文锚=取字段(规格,'answerAnchorSeq')#正文锚
        if 种 in ('user','steering') and (开场人 is None or 锚>开场人) and (正文锚 is None or 锚<正文锚):#过程区人工
            紧凑=False#不紧凑
        if 种 in 回合过程独立种类 or 锚<取字段(规格,'processStartSeq',0) or (正文锚 is not None and 锚>=正文锚):#范围外
            continue#跳
        正文步=取字段(规格,'answerStep')#正文步
        if 种!='assistant-step' or 正文步 is None or 取字段(取字段(节,'data'),'step')!=正文步:#非正文步
            有外部=True#外部
    return {#呈现
        'turn':回合,#轮次
        'spec':规格,#规格
        'turnClosed':取字段(取字段(位置,'turn'),'status')=='closed',#已关
        'hasExternalProcess':有外部,#外部
        'compactAnswer':紧凑,#紧凑
    }#结束

class 聊天回合过程投影器:#过程呈现投影器
    """按轮次物化的可变投影。"""

    def __init__(自身):#构造
        """空表。"""
        自身.呈现表={}#按轮

    def get(自身,节点):#按节点取呈现
        """缺席则 None。"""
        回合=节点回合(节点)#轮次
        return None if 回合 is None else 自身.呈现表.get(回合)#查

    def set(自身,回合,呈现):#写入一轮
        """变则 True。"""
        旧=自身.呈现表.get(回合)#旧
        if 同过程呈现(旧,呈现):#同
            return False#未变
        if 呈现 is None:#删
            自身.呈现表.pop(回合,None)#删
        else:#写
            自身.呈现表[回合]=呈现#写
        return True#变

    def replace(自身,顺序,位置们,节点们):#全量替换
        """返回变更轮次集。"""
        轮集=set()#可见轮
        for 键 in 顺序:#扫
            节=节点们.get(键) if hasattr(节点们,'get') else None#节点
            回合=节点回合(节)#轮
            if 回合 is not None:#有
                轮集.add(回合)#记
        变更=set()#变更
        for 回合 in set(list(自身.呈现表.keys())+list(轮集)):#并集
            下一=推导过程呈现(回合,位置们,节点们) if 回合 in 轮集 else None#推导
            if 自身.set(回合,下一):#变
                变更.add(回合)#记
        return 变更#返回
