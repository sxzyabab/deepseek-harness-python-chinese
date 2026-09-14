__all__=['推理行','首行','末行']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

def 首行(文本):
    """取第一行。"""
    换行=文本.find('\n')#换行
    return 文本 if 换行==-1 else 文本[:换行]#首行

def 末行(文本):
    """取末可见行。"""
    可见=文本.rstrip()#去尾
    换行=可见.rfind('\n')#末换行
    return 可见 if 换行==-1 else 可见[换行+1:]#末行

class 推理行:
    """流式跟末行；定稿取首行。"""
    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.展开=False#展开

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换(自身):
        """翻转开合。"""
        自身.展开=not 自身.展开#翻

    def 渲染(自身):
        """DisclosureRow 形。"""
        属性=自身.属性#props
        文本=属性['text'] if 'text' in 属性 and 属性['text'] is not None else ''#文
        运行中=属性['running'] is True if 'running' in 属性 else False#流式
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        摘要=末行(文本) if 运行中 is True else 首行(文本)#摘要
        return {'type':'reasoning-row','title':翻译('message.think'),'summary':摘要,'open':自身.展开,'running':运行中,'body':文本 if 自身.展开 is True else None,'onToggle':自身.切换,'cssModule':'推理行.module.css'}#行

    def __call__(自身,属性=None):
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
