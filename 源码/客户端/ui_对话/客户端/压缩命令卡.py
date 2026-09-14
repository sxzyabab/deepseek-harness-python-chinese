from .压缩项 import 压缩项#检查点标记
from .回退命令卡 import 回退命令卡#回退卡

__all__=['压缩命令卡']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

class 压缩命令卡:
    """有 compaction 则压缩项；否则回退卡。"""

    def __init__(自身,属性=None):
        """记下 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.压缩视图=压缩项()#检查点
        自身.回退视图=回退命令卡()#回退

    def 更新(自身,属性):
        """刷新。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """按是否有检查点分发。"""
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 else None#命令
        压缩=属性['compaction'] if 'compaction' in 属性 else None#检查点
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        if 压缩 is not None:#有检查点
            结局=节点['outcome'] if 节点 is not None and 'outcome' in 节点 else None#结局
            回退摘要=结局['text'] if 结局 is not None and 'text' in 结局 else None#摘要
            return 自身.压缩视图({#压缩项
                'node':压缩,#节点
                'title':'compact',#标题
                'fallbackSummary':回退摘要,#回退
                't':翻译,#文案
            })#渲
        结局=节点['outcome'] if 节点 is not None and 'outcome' in 节点 else None#结局
        if 结局 is not None:#已结
            return 自身.回退视图({'node':节点,'t':翻译})#回退
        return 自身.回退视图({#跑中
            'node':节点,#节点
            't':翻译,#文案
            'runningSummary':翻译('message.compaction.running'),#跑文
        })#渲

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
