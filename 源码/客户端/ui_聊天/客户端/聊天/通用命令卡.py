"""通用斜杠命令卡。

对齐上游 `ui-chat/src/client/chat/GenericCommandCard.tsx`。公开面仅中文名。
"""

__all__=['通用命令卡']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或属性。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 通用命令卡:#命令行卡
    """运行中/失败/完成态。"""

    def __init__(自身,属性=None):#构造
        """记下。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """命令卡。"""
        属性=自身.属性#props
        节点=取字段(属性,'node') or {}#节点
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        结局=取字段(节点,'outcome')#结局
        if 结局 is None:#运行中
            态='running'#运行
            标=翻译('command.running')#标
        elif 取字段(结局,'kind')=='failure' or 取字段(结局,'kind')=='error':#失败
            态='failed'#失败
            标=翻译('command.failed')#标
        else:#完成
            态='done'#完成
            标=翻译('command.done')#标
        return {'type':'generic-command-card','title':取字段(节点,'name') or 翻译('command.title'),'status':态,'statusLabel':标,'args':取字段(节点,'args'),'outcome':结局,'cssModule':'通用命令卡.module.css'}#卡

    def __call__(自身,属性=None):#调用形
        """对齐。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
