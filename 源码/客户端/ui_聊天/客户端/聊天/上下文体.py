
__all__=['上下文体']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键即文案

class 上下文体:
    """按 form 选渲染形态；缺席不透明。"""
    def __init__(自身,属性=None):
        """记下合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#合成

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        """解析包：summary / body / rendered。"""
        属性=自身.属性#props
        形态=属性['form'] if 'form' in 属性 else None#form
        内容=属性['content'] if 'content' in 属性 else None#内容
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        摘要=''#摘要
        if isinstance(内容,list):#块
            段列表=[]#文本段
            for 块 in 内容:#逐块
                种=块['type'] if 'type' in 块 else None#种
                if 种=='text':#文本
                    段=块['text'] if 'text' in 块 and 块['text'] is not None else ''#段
                    段列表.append(段)#收
            摘要=''.join(段列表)[:80]#截
        elif isinstance(内容,str):#串
            摘要=内容[:80]#截
        摘要出=摘要 if 摘要!='' else 翻译('message.extraBlock')#空摘要回退
        形态出=形态 if 形态 is not None and 形态!='' else 'opaque'#缺席不透明
        return {'summary':摘要出,'body':内容,'rendered':形态出,'form':形态,'cssModule':'上下文体.module.css'}#包

    def __call__(自身,属性=None):
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
