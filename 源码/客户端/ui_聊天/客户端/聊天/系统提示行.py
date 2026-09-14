__all__=['系统提示行']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

class 系统提示行:
    """折叠展示完整 system 文本。"""
    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.打开=False#开

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换(自身):
        """翻转开合。"""
        自身.打开=not 自身.打开#翻

    def 渲染(自身):
        """披露。"""
        属性=自身.属性#props
        节点=属性['node'] if 'node' in 属性 and 属性['node'] is not None else {}#节点
        数据=节点['data'] if 'data' in 节点 and 节点['data'] is not None else 节点#数据
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        文=数据['text'] if 'text' in 数据 and 数据['text'] is not None else ''#文本
        return {'type':'system-prompt-row','title':翻译('message.systemPrompt'),'summary':文[:80],'open':自身.打开,'body':文 if 自身.打开 is True else None,'onToggle':自身.切换,'cssModule':'系统提示行.module.css'}#行

    def __call__(自身,属性=None):
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
