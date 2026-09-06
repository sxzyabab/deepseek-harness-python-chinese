"""按轮次物化的跨节点过程布局事实投影。

对齐上游 `ui-chat/src/client/conversation-nodes/turn-process-presentation.ts`。公开面仅中文名。
"""
from ..约定.回合过程 import 回合过程独立种类#独立种类

__all__=['同过程呈现','推导过程呈现','聊天回合过程投影器']#仅中文公开名

def 节点回合(节点):#从节点取轮次
    """turn/step 位置。"""
    if 节点 is None:#无
        return None#无
    位置=节点['location'] if 'location' in 节点 else None#位置
    if 位置 is None:#无
        return None#无
    种=位置['kind'] if 'kind' in 位置 else None#种
    if 种 in ('turn','step'):#有
        回合位=位置['turn'] if 'turn' in 位置 else None#回合位
        return 回合位['turn'] if 回合位 is not None and 'turn' in 回合位 else None#轮次
    return None#无

def 同过程呈现(左,右):#呈现相等判定
    """双侧字段与规格引用。"""
    if 左 is 右:#同引用
        return True#同
    if 左 is None or 右 is None:#单侧
        return False#异
    return (#字段
        左['spec'] is 右['spec']#规格
        and 左['turn']==右['turn']#轮次
        and 左['turnClosed']==右['turnClosed']#已关
        and 左['hasExternalProcess']==右['hasExternalProcess']#外部
        and 左['compactAnswer']==右['compactAnswer']#紧凑
    )#结束

def 推导过程呈现(回合,位置索引,节点表):#推导一轮过程呈现
    """无过程控件则缺席。位置与仓为本包可变对象。"""
    键列表=位置索引.getTurn(回合)#轮内键
    控件=None#过程控件
    for 键 in 键列表:#找
        节=节点表.get(键)#节点
        if 节 is not None and 节['kind']=='turn-process':#控件
            控件=节#记下
            break#停
    if 控件 is None:#无
        return None#缺席
    规格=控件['data']#规格
    位置=控件['location']#位置
    种=位置['kind'] if 'kind' in 位置 else None#种
    if 种 not in ('turn','step'):#无轮
        return None#缺
    控件锚=规格['controlAnchorSeq'] if 'controlAnchorSeq' in 规格 else 0#控件锚
    开场人=None#开场人工锚
    for 键 in 键列表:#扫开场
        节=节点表.get(键)#节点
        if 节 is None:#无
            continue#下
        节种=节['kind']#种
        锚=节['anchorSeq'] if 'anchorSeq' in 节 else 0#锚
        if 节种 in ('user','steering') and 锚<控件锚:#开场
            开场人=锚 if 开场人 is None else min(开场人,锚)#最早
    有外部=False#外部过程
    紧凑=True#紧凑正文
    过程起=规格['processStartSeq'] if 'processStartSeq' in 规格 else 0#过程起
    正文锚=规格['answerAnchorSeq'] if 'answerAnchorSeq' in 规格 else None#正文锚
    正文步=规格['answerStep'] if 'answerStep' in 规格 else None#正文步
    for 键 in 键列表:#扫成员
        节=节点表.get(键)#节点
        if 节 is None or 节['kind']=='turn-process':#跳控件
            continue#下
        节种=节['kind']#种
        锚=节['anchorSeq'] if 'anchorSeq' in 节 else 0#锚
        if 节种 in ('user','steering') and (开场人 is None or 锚>开场人) and (正文锚 is None or 锚<正文锚):#过程区人工
            紧凑=False#不紧凑
        if 节种 in 回合过程独立种类 or 锚<过程起 or (正文锚 is not None and 锚>=正文锚):#范围外
            continue#跳
        数据=节['data'] if 'data' in 节 else None#数据
        步=数据['step'] if 数据 is not None and 'step' in 数据 else None#步
        if 节种!='assistant-step' or 正文步 is None or 步!=正文步:#非正文步
            有外部=True#外部
    回合位=位置['turn'] if 'turn' in 位置 else None#回合位
    态=回合位['status'] if 回合位 is not None and 'status' in 回合位 else None#状态
    return {#呈现
        'turn':回合,#轮次
        'spec':规格,#规格
        'turnClosed':态=='closed',#已关
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

    def replace(自身,顺序,位置索引,节点表):#全量替换
        """返回变更轮次集。"""
        轮集=set()#可见轮
        for 键 in 顺序:#扫
            节=节点表.get(键)#节点
            回合=节点回合(节)#轮
            if 回合 is not None:#有
                轮集.add(回合)#记
        变更=set()#变更
        for 回合 in set(list(自身.呈现表.keys())+list(轮集)):#并集
            下一=推导过程呈现(回合,位置索引,节点表) if 回合 in 轮集 else None#推导
            if 自身.set(回合,下一):#变
                变更.add(回合)#记
        return 变更#返回
