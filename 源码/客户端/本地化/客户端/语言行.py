"""语言偏好行：标题 + 选择器。

对齐上游 `locale/src/client/LanguageRow.tsx`。公开面仅中文名。
"""

__all__=['语言行','样式表']#仅中文公开名

样式表='''#对齐 LanguageRow.module.css
.row{display:flex;align-items:center;justify-content:space-between;gap:16px;min-height:48px}
.rowText{min-width:0}
.title{font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary)}
.selector{display:inline-flex;align-items:center;gap:4px;padding:4px 8px;border:1px solid var(--dsw-alias-border-l2);border-radius:999px;background:var(--dsw-alias-bg-base);cursor:pointer}
.chevron{color:var(--dsw-alias-label-tertiary)}
'''#样式表结束

class 语言行:
    """设置常规条目分区的语言行：打开菜单切换偏好。属性是槽位合成的 dict。"""
    def __init__(自身,属性):
        """记下 props，菜单默认关闭。"""
        自身.属性=属性#合成 props
        自身.打开=False#菜单是否打开

    def 更新(自身,属性):
        """刷新合成 props。"""
        自身.属性=属性#最新 props

    def 切换菜单(自身):
        """切换菜单开闭。"""
        自身.打开=not 自身.打开#翻转

    def 选定(自身,标识):
        """写入偏好并关闭菜单。setLocale 是注入面键名。"""
        自身.属性['setLocale'](标识)#切换
        自身.打开=False#关闭

    def 视图(自身):
        """从仓库镜像出当前标签与选项。仓库快照是 dict。"""
        用存储=自身.属性['useStore']#选择器钩
        def 选当前(态):
            """当前语言 id。"""
            return 态['active']#当前
        def 选选项(态):
            """选项行。"""
            return 态['options']#选项
        当前=用存储(选当前)#当前语言
        选项=用存储(选选项)#选项
        标签=当前#回退为 id
        for 行 in 选项:#找显示名
            if 行['id']==当前:#命中
                标签=行['label']#显示名
                break#找到
        翻译=自身.属性['t']#文案席
        return {#视图模型
            'title':翻译('language.title'),#标题
            'active':当前,#当前 id
            'activeLabel':标签,#显示名
            'options':选项,#选项
            'open':自身.打开,#菜单开闭
        }#视图结束

    def __call__(自身,属性=None):
        """对齐 React 组件调用；返回视图模型。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.视图()#视图模型
