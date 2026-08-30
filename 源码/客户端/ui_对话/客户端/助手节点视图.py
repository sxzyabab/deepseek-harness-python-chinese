"""助手步骤节点：流式/定稿/中断共用一个键控渲染器。

对齐上游 `ui-conversation/src/client/chat/AssistantNodeView.tsx`。公开面仅中文名。
"""
from .助手Markdown import 助手Markdown#块体

__all__=['助手节点视图']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 助手节点视图:#assistant-step
    """块经助手 Markdown；收尾才挂文件提及。"""

    def __init__(自身,属性=None):#记下
        """记下合成 props 与块体实例。"""
        自身.属性=属性 or {}#合成
        自身.块体=助手Markdown()#保推理展开

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构
        """派生回合尾属主与提及。"""
        属性=自身.属性#props
        节点=取字段(属性,'node')#节点
        数据=取字段(节点,'data')#数据
        位置=取字段(节点,'location')#位置
        种=取字段(位置,'kind')#位置种
        回合=取字段(位置,'turn') if 种 in ('turn','step') else None#回合
        用回合数据=取字段(属性,'useTurnData')#回合数据钩
        尾=用回合数据('turn-tail') if callable(用回合数据) else None#尾
        打开文件=取字段(属性,'openFile')#开文件
        文件提及=取字段(属性,'fileMentions')#提及
        定稿=取字段(数据,'finalNode')#定稿
        属主=None#尾属主
        if 取字段(回合,'status')=='closed' and 定稿 is not None:#已收尾
            收尾=取字段(取字段(尾,'closing'),'finalNode') if 尾 is not None else None#closing
            if 取字段(收尾,'seq')==取字段(定稿,'seq'):#匹配
                属主={'turn':回合,'seq':取字段(定稿,'seq'),'openFile':打开文件}#属主
        提及=文件提及(属主) if 属主 is not None and callable(文件提及) else None#提及
        return 自身.块体({#Markdown
            'blocks':取字段(数据,'blocks'),#块
            'streaming':取字段(数据,'status')=='running',#流式
            'interrupted':取字段(数据,'status')=='interrupted',#中断
            'loadImage':取字段(属性,'loadImage'),#图
            'mentions':提及,#提及
            't':取字段(属性,'t'),#文案
        })#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
