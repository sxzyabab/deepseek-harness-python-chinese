"""外观偏好行：标题 + 三枚偏好立方（浅色/深色/跟随系统）。

对齐上游 `ui-theme/src/client/AppearanceRow.tsx`。公开面仅中文名。
选择跟随持久化偏好，从不跟随已解析的活动主题。
"""
from ..主题设置 import 主题偏好们#内置偏好

__all__=['外观行','样式表','立方顺序']#仅中文公开名

立方顺序=(#立方顺序与文案键（figma Light/Dark/System）
    {'id':'light','labelKey':'appearance.light'},#浅色
    {'id':'dark','labelKey':'appearance.dark'},#深色
    {'id':'system','labelKey':'appearance.system'},#跟随系统
)#结束

样式表='''#对齐 AppearanceRow.module.css
.group{display:flex;flex-direction:column;gap:8px;padding:16px 0;border-bottom:1px solid var(--dsw-alias-border-l2)}
.title{font-size:14px;font-weight:400;line-height:22px;color:var(--dsw-alias-label-primary)}
.cubeRow{display:flex;align-items:stretch;gap:8px;flex-wrap:wrap}
.themeCube{box-sizing:border-box;flex:1 1 180px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;padding:20px 32px;border:1px solid var(--dsw-alias-border-l2);border-radius:16px;background:transparent;font:inherit;font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary);cursor:pointer}
.themeCube:hover:not(.selected){background:var(--dsw-alias-interactive-bg-hover)}
.selected{background:var(--dsw-alias-bg-module-platform);border-color:var(--dsw-static-neutral-bluish-400)}
'''#样式表结束

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 外观行:#设置通用区外观行
    """渲染外观行；点击立方写入偏好。"""

    def __init__(自身,属性=None):#记下 props
        """记下翻译、写偏好与 store 钩。"""
        自身.属性=属性 or {}#合成 props

    def 更新(自身,属性):#刷新 props
        """刷新合成 props。"""
        自身.属性=属性#新 props

    def 当前偏好(自身):#读持久化偏好
        """从 useStore 选择 preference。"""
        用仓库=取字段(自身.属性,'useStore')#store 钩
        if callable(用仓库):#有钩
            return 用仓库(lambda 快照:取字段(快照,'preference'))#选定
        return 取字段(自身.属性,'preference')#直接字段

    def 渲染(自身):#产出结构树
        """与上游 JSX 同构。"""
        翻译=取字段(自身.属性,'t')#文案
        设主题=取字段(自身.属性,'setTheme')#写偏好
        偏好=自身.当前偏好()#当前
        立方们=[]#立方列表
        for 项 in 立方顺序:#三枚
            标识=项['id']#偏好 id
            立方们.append({#一枚立方
                'id':标识,#id
                'selected':偏好==标识,#是否选中
                'ariaPressed':偏好==标识,#无障碍
                'label':翻译(项['labelKey']) if callable(翻译) else 项['labelKey'],#标签
                'onClick':(lambda 选=标识:设主题(选) if callable(设主题) else None),#点击
            })#结束一枚
        return {#结构树
            'type':'appearance-row',#类型
            'class':'group',#组类
            'title':翻译('appearance.title') if callable(翻译) else 'appearance.title',#标题
            'cubes':立方们,#立方
            'preferences':主题偏好们,#合法域
        }#结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
