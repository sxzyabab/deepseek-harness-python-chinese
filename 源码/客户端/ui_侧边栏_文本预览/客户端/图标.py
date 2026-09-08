"""本包自绘、共享图标集尚未收录的字形。

对齐上游 `ui-sidebar-textpreview/src/client/icons.tsx`。公开面仅中文名。
与基础界面组件图标同形：视图 dict，便于日后改为共享导入。
"""

__all__=['图标换行线16']#仅中文公开名


def 图标换行线16(属性=None):
    """三行文字，中间一行折回自身下。属性可为 dict，含 size / className。"""
    if 属性 is None:#缺省
        属性={}#空
    尺寸=属性['size'] if 'size' in 属性 and 属性['size'] is not None else 16#边长
    类名=属性['className'] if 'className' in 属性 else None#类
    return {#图标视图
        'type':'icon',
        'name':'wrap-outline-16',
        'size':尺寸,
        'width':尺寸,
        'height':尺寸,
        'className':类名,
        'viewBox':'0 0 16 16',
        'fill':'none',
        'stroke':'currentColor',
        'strokeWidth':'1.3',
        'strokeLinecap':'round',
        'strokeLinejoin':'round',
        'paths':[#描边路径
            {'d':'M2.5 4h11','stroke':'currentColor','strokeWidth':'1.3','fill':'none'},
            {'d':'M2.5 8h8.5a2.5 2.5 0 0 1 0 5H9.5','stroke':'currentColor','strokeWidth':'1.3','fill':'none'},
            {'d':'M11 11.5 9.5 13l1.5 1.5','stroke':'currentColor','strokeWidth':'1.3','fill':'none'},
            {'d':'M2.5 12h3.5','stroke':'currentColor','strokeWidth':'1.3','fill':'none'},
        ],#路径结束
    }#视图结束
