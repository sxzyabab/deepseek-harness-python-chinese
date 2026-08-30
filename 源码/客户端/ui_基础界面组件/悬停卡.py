"""延迟悬停预览卡，传送到 document.body。

对齐上游 `ui-primitives/src/HoverCard.tsx`。公开面仅中文名。
锚点包一层；卡片固定在右缘；指针宽限穿越缝隙。
"""
from .指针宽限 import 指针宽限#离开宽限
from .剪贴板 import 写剪贴板#复制

__all__=['悬停卡','默认打开延迟毫秒']#仅中文公开名

默认打开延迟毫秒=500#悬停驻留

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 悬停卡:#悬停预览
    """状态机：打开延迟、宽限关闭、可选点卡复制。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props 与本地态。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已打开=False#卡是否开
        自身.已复制=False#复制反馈
        自身.位置=None#固定坐标
        自身.宽限=指针宽限(自身.关闭)#离开宽限

    def 更新(自身,属性):#刷新
        """刷新 props；禁用则立即关。"""
        自身.属性=dict(属性)#最新
        if bool(取字段(自身.属性,'disabled')):#禁用
            自身.宽限.取消()#取消宽限
            自身.关闭()#关

    def 关闭(自身):#关卡
        """清复制反馈并关。"""
        自身.已复制=False#清反馈
        自身.已打开=False#关
        自身.位置=None#清位

    def 打开卡(自身):#开卡
        """置开；宿主再量锚定位。"""
        自身.已打开=True#开

    def 复制(自身):#点卡复制
        """有 copyText 且未在反馈中才写。"""
        文本=取字段(自身.属性,'copyText')#可复制值
        if 文本 is None or 自身.已复制:#无或反馈中
            return False#跳
        if not 写剪贴板(str(文本)):#拒绝
            return False#失败
        自身.已复制=True#反馈
        return True#成功

    def 渲染(自身):#结构树
        """锚+条件传送卡。"""
        属性=自身.属性#props
        可复制=取字段(属性,'copyText') is not None#可复制
        延迟=取字段(属性,'openDelayMs',默认打开延迟毫秒)#驻留
        return {#视图
            'type':'hover-card',#类型
            'anchor':取字段(属性,'anchor'),#锚
            'content':取字段(属性,'content'),#卡内容
            'open':自身.已打开,#开
            'pos':自身.位置,#位
            'copied':自身.已复制,#反馈
            'copyable':可复制,#可复制
            'copyLabel':取字段(属性,'copyLabel','复制'),#复制前缀
            'copiedLabel':取字段(属性,'copiedLabel','复制成功'),#成功文案
            'disabled':bool(取字段(属性,'disabled')),#禁
            'openDelayMs':延迟,#延迟
            'onOpen':自身.打开卡,#开
            'onClose':自身.关闭,#关
            'onCopy':自身.复制,#复制
            'armClose':自身.宽限.武装,#装备关
            'cancelClose':自身.宽限.取消,#取消关
            'portal':'body',#传送
            'cssModule':'悬停卡.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
