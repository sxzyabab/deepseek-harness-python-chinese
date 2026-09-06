"""审批详情命令卡。

对齐上游 `ui-chat/src/client/chat/ApprovalCommand.tsx`。公开面仅中文名。
属性为 dict。
"""
from .回退命令卡 import 回退命令卡#命令卡

__all__=['审批命令']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

class 审批命令:
    """复用回退命令卡展示关联命令。"""
    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.卡=回退命令卡()#卡

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """审批命令。"""
        属性=自身.属性#props
        if 'node' in 属性 and 属性['node'] is not None:#有节点
            节点=属性['node']#节点
        elif 'command' in 属性 and 属性['command'] is not None:#有命令
            节点=属性['command']#命令
        else:#缺
            节点={}#空
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        return {'type':'approval-command','card':自身.卡({'node':节点,'t':翻译}),'cssModule':'审批命令.module.css'}#视图

    def __call__(自身,属性=None):
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
