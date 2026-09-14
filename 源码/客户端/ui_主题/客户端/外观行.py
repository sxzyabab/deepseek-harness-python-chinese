from ..主题设置 import 主题偏好表#内置偏好

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

class 外观行:#设置通用区外观行
    """渲染外观行；点击立方写入偏好。"""

    def __init__(自身,属性):#记下 props
        """记下翻译、写偏好与 store 钩。"""
        自身.属性=属性#合成 props

    def 更新(自身,属性):#刷新 props
        """刷新合成 props。"""
        自身.属性=属性#新 props

    def 当前偏好(自身):#读持久化偏好
        """从 useStore 选择 preference。"""
        用存储=自身.属性['useStore']#store 钩
        def 选偏好(快照):
            """preference。"""
            return 快照['preference']#偏好
        return 用存储(选偏好)#选定

    def 渲染(自身):#产出结构树
        """与上游 JSX 同构。"""
        翻译=自身.属性['t']#文案
        设主题=自身.属性['setTheme']#写偏好；注入面键名
        偏好=自身.当前偏好()#当前
        立方列表=[]#立方列表
        for 项 in 立方顺序:#三枚
            标识=项['id']#偏好 id
            def 造点击(选):#闭包点击
                """写入该偏好。"""
                def 点击():#点击
                    """设主题。"""
                    设主题(选)#写
                return 点击#回调
            立方列表.append({#一枚立方
                'id':标识,#id
                'selected':偏好==标识,#是否选中
                'ariaPressed':偏好==标识,#无障碍
                'label':翻译(项['labelKey']),#标签
                'onClick':造点击(标识),#点击
            })#结束一枚
        return {#结构树
            'type':'appearance-row',#类型
            'class':'group',#组类
            'title':翻译('appearance.title'),#标题
            'cubes':立方列表,#立方
            'preferences':主题偏好表,#合法域
        }#结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
