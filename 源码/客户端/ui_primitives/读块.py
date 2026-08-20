"""读工具结果：行号+可选高亮源码面。

对齐上游 `ui-primitives/src/ReadBlock.tsx`。公开面仅中文名。
窗口读保留文件行号；高亮由宿主/语法表完成，本组件产出行材料。
"""
from .头尾封顶 import 头尾封顶#高度封顶
from .复制反馈 import 复制反馈#复制反馈

__all__=['读块','默认读最大行']#仅中文公开名

默认读最大行=16#与终端同预算

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 读块:#读卡
    """banner+行号 gutter；复制写窗口原文。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已展开=False#展开
        自身.反馈=复制反馈()#复制

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 切换展开(自身):#翻转
        """封顶切换。"""
        自身.已展开=not 自身.已展开#翻

    def 渲染(自身):#结构树
        """配对行号+文本并封顶。"""
        属性=自身.属性#props
        行们=list(取字段(属性,'lines') or [])#窗口行
        总行=取字段(属性,'totalLines',0)#文件总行
        最大=取字段(属性,'maxLines',默认读最大行)#封顶
        语言=取字段(属性,'lang')#语法提示
        原文='\n'.join((取字段(行,'text') or '') for 行 in 行们)#原文
        规范=[{'number':取字段(行,'number'),'text':取字段(行,'text') or ''} for 行 in 行们]#规范行        自身.反馈.置文本(原文)#可复制
        度量=头尾封顶(len(规范),最大,自身.已展开)#度量
        头=规范[:度量['headLines']] if 度量['capped'] else 规范#头
        尾=规范[len(规范)-度量['tailLines']:] if 度量['capped'] else []#尾
        窗口化=len(规范)<总行#窗口读
        return {#视图
            'type':'read-block',#类型
            'label':取字段(属性,'label'),#标签
            'lang':语言,#语言
            'lines':规范,#全行
            'head':头,#头
            'tail':尾,#尾
            'totalLines':总行,#总
            'windowed':窗口化,#窗口
            'countNote':('显示 '+str(len(规范))+' / '+str(总行)+' 行') if 窗口化 else None,#计数注
            'hidden':度量['hidden'],#隐
            'capped':度量['capped'],#封
            'expanded':自身.已展开,#展
            'copied':自身.反馈.已复制,#反馈
            'onCopy':自身.反馈.复制 if len(规范)>0 else None,#空窗不复制
            'onToggle':自身.切换展开,#切换
            'className':取字段(属性,'className'),#类
            'cssModule':'读块.module.css',#样式
        }#结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
