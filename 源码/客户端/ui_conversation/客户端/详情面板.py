"""详情第三栏：选中工具的 Input/Output。

对齐上游 `ui-conversation/src/client/skeleton/DetailsPanel.tsx`。公开面仅中文名。
"""

__all__=['详情面板']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 详情面板:#详情栏
    """标题+关闭+工具席或空态。"""

    def __init__(自身,属性=None):#构造
        """记下 props。"""
        自身.属性=属性 or {}#合成

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=属性 or {}#新

    def 渲染(自身):#结构树
        """详情结构。"""
        属性=自身.属性#props
        用仓=取字段(属性,'useStore')#仓
        渲染槽=取字段(属性,'renderSlot',lambda *_a,**_k:None)#槽
        关闭=取字段(属性,'closeDetails')#关
        翻译=取字段(属性,'t',lambda 键,_=None:键)#文案
        选中=用仓(lambda s:取字段(s,'selection')) if 用仓 is not None else None#选中
        有选=选中 is not None and 取字段(选中,'callId') is not None#有调用
        return {#详情
            'type':'details-panel',#类型
            'title':翻译('details.title') if not 有选 else (取字段(选中,'toolName') or 翻译('details.title')),#标题
            'closeLabel':翻译('details.close'),#关
            'onClose':关闭,#关回调
            'empty':not 有选,#空
            'emptyText':翻译('details.empty'),#空文
            'toolSeat':None if not 有选 else 渲染槽('conversation.details.tool',{'selection':选中}),#工具席
            'cssModule':'详情面板.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
