"""回退斜杠命令卡。

对齐上游 `ui-chat/src/client/chat/GenericCommandCard.tsx`。公开面仅中文名。
属性与节点为 dict。
"""

__all__=['回退命令卡']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

class 回退命令卡:
    """运行中/失败/完成态。"""
    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """命令卡。"""
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        结局=节点['outcome'] if 'outcome' in 节点 else None#结局
        if 结局 is None:#运行中
            状态='running'#运行
            状态标签=翻译('command.running')#标签
        else:#有结局
            种类=结局['kind'] if 'kind' in 结局 else None#种类
            if 种类=='failure' or 种类=='error':#失败
                状态='failed'#失败
                状态标签=翻译('command.failed')#标签
            else:#完成
                状态='done'#完成
                状态标签=翻译('command.done')#标签
        命令名=节点['name'] if 'name' in 节点 else None#命令名
        标题=命令名 if 命令名 is not None and 命令名!='' else 翻译('command.title')#标题
        参数=节点['args'] if 'args' in 节点 else None#参数
        return {'type':'generic-command-card','title':标题,'status':状态,'statusLabel':状态标签,'args':参数,'outcome':结局,'cssModule':'通用命令卡.module.css'}#卡

    def __call__(自身,属性=None):
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
