"""侧栏外壳：列几何与折叠交叉淡入。

对齐上游 `ui-sidebar/src/client/SidebarRoot.tsx`。公开面仅中文名。
折叠是滑动加交叉淡入：宽内容在展开宽度冻结并就地淡出，滑动列裁剪；
落定后宽态卸载，轨上控件从同一水平偏移进入。滚动条跟随指针示意。
"""

__all__=['侧栏根','折叠落定毫秒','滚动条滞留毫秒','样式表']#仅中文公开名

折叠落定毫秒=150#宽内容卸载延迟，对齐 150ms 淡出
滚动条滞留毫秒=2000#指针离开后滚动条仍绘制的时长

样式表='''#对齐 SidebarRoot.module.css
.root{--dsh-sidebar-inline-padding:12px;display:flex;flex-direction:column;height:100%;padding:6px var(--dsh-sidebar-inline-padding);box-sizing:border-box;background:var(--dsw-specific-sidebar-fill);color:var(--dsw-alias-label-primary);font-size:14px;--dsh-scrollbar-thumb:var(--dsw-alias-scrollbar-bg-l2);--dsh-scrollbar-thumb-hover:var(--dsw-alias-scrollbar-hover-l2)}
.root.collapsed{padding:18px 10px 6px}
.root.quietBars{--dsh-scrollbar-thumb:transparent;--dsh-scrollbar-thumb-hover:transparent}
.fading>*{opacity:0;transition:opacity 150ms var(--ds-ease-in-out)}
.wide{animation:wide-in 200ms var(--ds-ease-in-out)}
@keyframes wide-in{from{opacity:0}}
.railIn .iconButton,.railIn .newSession,.railIn .regionArea{animation:rail-in 150ms var(--ds-ease-in-out) backwards}
.railIn .footArea{animation:rail-fade-in 150ms var(--ds-ease-in-out) backwards}
@keyframes rail-in{from{opacity:0;transform:translateX(49px)}}
@keyframes rail-fade-in{from{opacity:0}}
.logoRow{flex:none;display:flex;align-items:center;justify-content:flex-end;gap:8px;height:60px;padding:8px 0 8px 4px;margin-bottom:8px;box-sizing:border-box;overflow:hidden}
.collapsed .logoRow{height:36px;padding:0;margin-bottom:12px;justify-content:flex-start}
.brand{flex:1;min-width:0;display:inline-flex;align-items:center;overflow:hidden;padding:0;border:none;background:transparent;color:inherit;cursor:pointer}
.iconButton{flex:none;display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border:none;border-radius:50%;padding:0;background:transparent;cursor:pointer;color:var(--dsw-alias-label-secondary)}
.iconButton:hover{background:var(--dsw-alias-interactive-bg-hover)}
.collapsed .iconButton{width:36px;height:36px;color:var(--dsw-alias-label-primary)}
.collapsed .toggle .panelIcon{display:none}
.collapsed .toggle:hover .panelIcon{display:inline}
.collapsed .toggle:hover .railFish{display:none}
.newSession{flex:none;display:flex;align-items:center;justify-content:center;gap:6px;height:38px;padding:8px 16px;margin:0 2px 8px;box-sizing:border-box;border:1px solid var(--dsw-alias-border-l2);border-radius:12px;background:var(--dsw-alias-button-elevated-fill);color:var(--dsw-alias-label-primary);font-size:14px;font-weight:500;line-height:22px;cursor:pointer;overflow:hidden}
.newSession:hover{background:var(--dsw-alias-button-floating-hover)}
.collapsed .newSession{align-self:flex-start;width:36px;height:36px;padding:0;margin:0 0 12px;gap:0;border-color:transparent;background:transparent}
.collapsed .newSession:hover{background:var(--dsw-alias-interactive-bg-hover)}
.newSessionLabel{max-width:200px;overflow:hidden;white-space:nowrap}
.collapsed .newSessionLabel{max-width:0}
.regionArea{flex:1;min-height:0;display:flex;flex-direction:column;margin-left:-4px;margin-right:calc(-1 * var(--dsh-sidebar-inline-padding));padding-left:4px;overflow:hidden}
.collapsed .regionArea{margin-left:0;margin-right:0;padding-left:0}
.footArea{flex:none;display:flex;flex-direction:column}
.settingsArea,.footerActions{flex:none;min-width:0;width:100%}
.footerActions{display:flex}
.collapsed .footArea{align-items:center}
.collapsed .settingsArea,.collapsed .footerActions{display:flex;justify-content:center;width:auto}
@media (prefers-reduced-motion:reduce){.wide,.fading>*,.railIn .iconButton,.railIn .newSession,.railIn .footArea,.railIn .regionArea{transition:none;animation:none}}
'''#样式表结束

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 侧栏根:#侧栏列外壳
    """渲染侧栏列外壳；折叠落定后卸宽态，轨态四枚上控件同源进入。"""

    def __init__(自身,属性):#记下合成 props
        """记下折叠、宽度、注入动作与槽渲染。"""
        自身.属性=属性#合成 props
        自身.已落定=取字段(属性,'collapsed') is True#初始与 collapsed 对齐
        自身.上次宽宽=取字段(属性,'width') or 0#冻结宽态宽度
        自身.曾宽=取字段(属性,'collapsed') is not True#冷启轨态不播 railIn
        自身.指针内=False#指针是否在列内
        自身.滞留句柄=None#滞留定时器句柄（宿主注入）

    def 更新(自身,属性):#props 变更
        """折叠变化时调度落定；展开时立刻取消落定。"""
        旧折=取字段(自身.属性,'collapsed') is True#旧折叠
        自身.属性=属性#最新
        新折=取字段(属性,'collapsed') is True#新折叠
        if not 新折:#展开
            自身.已落定=False#立刻宽态
            自身.曾宽=True#活折叠才 railIn
            自身.上次宽宽=取字段(属性,'width') or 自身.上次宽宽#记下宽宽
            return#已处理
        if not 旧折 and 新折:#刚折叠
            自身.上次宽宽=取字段(属性,'width') or 自身.上次宽宽#冻结
            自身.已落定=False#先淡出
            return#落定由宿主在折叠落定毫秒后调 落定

    def 落定(自身):#折叠动画落定
        """宽内容卸载，轨布局生效。"""
        if 取字段(自身.属性,'collapsed') is True:#仍折叠
            自身.已落定=True#落定

    def 宽态(自身):#是否仍挂宽内容
        """未折叠或未落定则为宽。"""
        return 取字段(自身.属性,'collapsed') is not True or not 自身.已落定#宽态

    def 进入指针(自身):#指针进入列
        """取消滞留并标内。"""
        自身.取消滞留()#取消
        自身.指针内=True#在内

    def 离开指针(自身):#元素 leave
        """武装滞留隐藏。"""
        自身.武装滞留()#滞留

    def 武装滞留(自身):#安排滞留隐藏
        """已有定时则不再排。"""
        if 自身.滞留句柄 is not None:#已排
            return#幂等
        自身.滞留句柄='armed'#占位；宿主用 滚动条滞留毫秒 回调 滞留到期

    def 取消滞留(自身):#取消滞留
        """清句柄。"""
        自身.滞留句柄=None#清

    def 滞留到期(自身):#滞留到点
        """指针外则隐藏滚动条。"""
        自身.滞留句柄=None#清
        自身.指针内=False#外

    def 指针移动(自身,客户X,客户Y,列盒):#按列盒几何判定内外
        """仅在已绘制滚动条时由宿主在 document 上转发。"""
        if not 自身.指针内:#未绘制
            return#不动
        if 列盒 is None:#无盒
            return#不动
        内=客户X>=列盒['left'] and 客户X<列盒['right'] and 客户Y>=列盒['top'] and 客户Y<列盒['bottom']#几何内
        if 内:#回内
            自身.取消滞留()#取消隐藏
        else:#出外
            自身.武装滞留()#滞留

    def 渲染(自身):#产出结构化视图
        """与上游 JSX 同构的结构树。"""
        折=取字段(自身.属性,'collapsed') is True#折叠
        宽=自身.宽态()#宽态
        翻译=取字段(自身.属性,'t')#文案
        渲染槽=取字段(自身.属性,'renderSlot')#子槽
        开会话=取字段(自身.属性,'startSession')#新建会话
        切换=取字段(自身.属性,'toggleSidebar')#折叠开关
        类们=['root']#根类
        if not 宽:#轨布局
            类们.append('collapsed')#collapsed
            if 自身.曾宽:#活折叠
                类们.append('railIn')#railIn
        if 折 and 宽:#淡出中
            类们.append('fading')#fading
        if not 自身.指针内:#安静滚动条
            类们.append('quietBars')#quietBars
        样式=None#内联宽
        if 宽:#冻结或当前宽
            样式={'width':自身.上次宽宽 if 折 else 取字段(自身.属性,'width')}#宽度
        def 展开侧栏():#浏览区请求展开
            """折叠时切换。"""
            if 折 and callable(切换):#折叠
                切换()#展开
        return {#结构树
            'type':'sidebar-root',#根类型
            'class':' '.join(类们),#类名
            'style':样式,#内联
            'wide':宽,#宽态旗
            'ariaToggle':翻译('toggle.open') if 折 else 翻译('toggle.collapse'),#折叠无障碍
            'ariaNew':翻译('session.new.label'),#新建无障碍
            'newLabel':翻译('session.new') if 宽 else None,#宽态标签
            'startSession':开会话,#新建
            'toggleSidebar':切换,#折叠
            'workspaces':渲染槽('sidebar.workspaces',{'wide':宽,'expandSidebar':展开侧栏}) if callable(渲染槽) else None,#浏览区
            'footerAction':渲染槽('sidebar.footer.action',{'wide':宽}) if callable(渲染槽) else None,#页脚
            'settings':渲染槽('sidebar.settings',{'wide':宽}) if callable(渲染槽) else None,#设置
        }#结束
