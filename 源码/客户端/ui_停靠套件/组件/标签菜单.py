"""标签芯片上下文菜单的视图模型。

对齐上游 `ui-dockkit/src/components/TabMenu.tsx`。公开面仅中文名。
锚定与关闭由宿主执行；本类持打开态并产出结构树。
"""

__all__=['标签菜单','菜单间隙']#仅中文公开名

菜单间隙=4#控件与菜单间距及视口边距


class 标签菜单:
    """关标签项 + 宿主附加项；打开时相对锚点定位。"""

    def __init__(自身,文案,关标签,解散,附加=None,锚点矩形=None,菜单宽=96):
        """文案含 closeTab；附加为结构树列表或 None。"""
        自身.文案=文案#文案 dict
        自身.关标签=关标签#回调
        自身.解散=解散#回调
        自身.附加=附加#额外项
        自身.锚点矩形=锚点矩形#宿主量得
        自身.菜单宽=菜单宽#估计宽
        自身.视口宽=None#可选，供翻转

    def 设锚点(自身,矩形,视口宽=None):
        """更新锚点矩形。"""
        自身.锚点矩形=矩形#锚
        自身.视口宽=视口宽#视口

    def 算位置(自身):
        """相对锚点的 top/left；无锚点则 None。"""
        if 自身.锚点矩形 is None:#无
            return None#未置
        矩=自身.锚点矩形#锚
        左=矩['x']#默认左齐
        if 自身.视口宽 is not None and 矩['x']+自身.菜单宽+菜单间隙>自身.视口宽:#越右
            左=max(菜单间隙,矩['x']+矩['width']-自身.菜单宽)#右齐
        return {'top':矩['y']+矩['height']+菜单间隙,'left':左}#位

    def 渲染(自身):
        """结构树：菜单与关项。"""
        位=自身.算位置()#位
        样式={'visibility':'hidden','top':0,'left':0} if 位 is None else 位#未量隐
        子=[{#关项
            'type':'menuitem',
            'key':'close',
            'data':'dockkit-menu-close',
            'label':自身.文案['closeTab'],
            'onClick':自身.关标签,
        }]#项
        if 自身.附加 is not None:#附加
            if isinstance(自身.附加,list):#列表
                子.extend(自身.附加)#并
            else:#单
                子.append(自身.附加)#加
        return {#树
            'type':'menu',
            'data':'dockkit-tab-menu',
            'role':'menu',
            'style':样式,
            'children':子,
            'onDismiss':自身.解散,
        }#结束
