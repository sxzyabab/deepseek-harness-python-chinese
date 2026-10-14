from nicegui import ui as 界面
from ...ui_基础界面组件.icons import 图标下chevron14
from ...ui_基础界面组件.菜单 import 菜单
from ..异常 import 页面失败文案

__all__=['语言行','样式表']#仅中文公开名

样式表='''
.语言行{display:flex;align-items:center;gap:8px;width:100%;padding:16px 0;border-bottom:1px solid var(--dsw-alias-border-l2)}
.语言文{flex:1;min-width:0;display:flex;flex-direction:column;gap:4px;padding-right:48px}
.语言标题{font-size:14px;font-weight:400;line-height:22px;color:var(--dsw-alias-label-primary)}
button.q-btn.语言选择{display:inline-flex;align-items:center;gap:12px;height:36px;min-height:36px;padding:0 14px;border:none;border-radius:18px;background:var(--dsw-alias-bg-module-platform) !important;box-shadow:none !important;color:var(--dsw-alias-label-primary) !important;font-size:14px;line-height:22px;cursor:pointer}
button.q-btn.语言选择 .q-btn__content{gap:12px;flex-wrap:nowrap}
button.q-btn.语言选择:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
.语言选择文{font-size:14px;line-height:22px;color:var(--dsw-alias-label-primary)}
.语言箭头{flex:none;color:var(--dsw-alias-label-tertiary)}
'''#样式表结束

样式已登记=False

def 登记样式():
    '语言行样式每个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表)
    样式已登记=True

class 语言选择锚:
    '菜单在渲染里调用本锚的渲染；构造时不画'
    def __init__(自身,标签,打开,点击):
        '记下当前语言、展开态与点击'
        自身.标签=标签 if isinstance(标签,str) else ''#显示名
        自身.打开=打开 is True#是否展开
        自身.点击=点击#翻转菜单

    def 渲染(自身):
        '画出语言药丸与下拉箭头。构造时不调用本方法'
        展开='true' if 自身.打开 is True else 'false'#无障碍展开态
        钮=界面.button(on_click=自身.点击).props('flat no-caps type=button aria-haspopup=menu aria-expanded='+展开).classes('语言选择')#药丸
        with 钮:#文案与箭头
            if 自身.标签!='':#有显示名
                界面.label(自身.标签).classes('语言选择文')#当前语言
            图标下chevron14({'className':'语言箭头'})#下拉箭头
        return 钮#锚

class 语言行:
    '设置常规条目分区的语言行：打开菜单切换偏好。属性是槽位合成的 dict'
    def __init__(自身,属性):
        '记下 props，菜单默认关闭，槽位只调用构造'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成 props
        自身.打开=False#菜单是否打开
        自身.根=None#可反复清空的行
        自身.画面失败=None
        自身.渲染()#槽位只调用构造

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新 props

    def 切换菜单(自身):
        '切换菜单开闭'
        自身.打开=not 自身.打开#翻转

    def 选定(自身,标识):
        '写入偏好并关闭菜单。setLocale 是注入面键名'
        if 'setLocale' in 自身.属性 and callable(自身.属性['setLocale']):#有写入
            自身.属性['setLocale'](标识)#切换
        自身.打开=False#关闭

    def 视图(自身):
        '从仓库镜像出当前标签与选项。仓库快照是 dict'
        属性=自身.属性#合成 props
        if 't' in 属性 and callable(属性['t']):#有文案席
            标题=属性['t']('language.title')#标题
        else:#槽位尚未给文案
            标题='语言'#词表标题
        当前=''#当前 id
        选项=[]#选项行
        if 'useStore' in 属性 and callable(属性['useStore']):#有存储钩
            用存储=属性['useStore']#选择器钩
            def 选当前(态):
                '当前语言 id'
                if isinstance(态,dict) is False or 'active' not in 态:#缺键
                    return ''#空
                return 态['active']#当前
            def 选选项(态):
                '选项行；空列表仍是列表'
                if isinstance(态,dict) is False or 'options' not in 态:#缺键
                    return []#空
                值=态['options']#选项
                if isinstance(值,list):#列表
                    return 值#原列表
                return []#其余当空
            当前=用存储(选当前)#当前语言
            取到=用存储(选选项)#选项
            if isinstance(取到,list):#列表
                选项=取到#收下
        标签=当前#回退为 id
        for 行 in 选项:#找显示名
            if isinstance(行,dict) and 'id' in 行 and 行['id']==当前:#命中
                if 'label' in 行:#有显示名
                    标签=行['label']#显示名
                break#找到
        return {#视图模型
            'title':标题,#标题
            'active':当前,#当前 id
            'activeLabel':标签,#显示名
            'options':选项,#选项
            'open':自身.打开,#菜单开闭
        }#视图结束

    def 菜单条目(自身,选项):
        '把选项收成菜单行。空列表仍然返回空列表'
        条目=[]#行
        for 行 in 选项:#逐项
            if isinstance(行,dict) is False or 'id' not in 行:#缺 id
                continue#下
            标签=行['label'] if 'label' in 行 else 行['id']#显示名
            条目.append({'id':行['id'],'label':标签})#一行
        return 条目#列表

    def 渲染(自身):
        '先画标题与语言菜单，再返回行。语言选择锚在这里才画'
        登记样式()
        视=自身.视图()#视图
        条目=自身.菜单条目(视['options'])#菜单行
        自身.画面失败=None
        if 自身.根 is not None:#已有行
            try:#清空后重画
                自身.根.clear()#清空
            except Exception as 错误:
                自身.根=None
                自身.画面失败=页面失败文案(错误)
        if 自身.根 is None:#新建行
            自身.根=界面.element('div').classes('语言行')#行
        def 点锚():
            '打开或关闭语言菜单'
            自身.切换菜单()#翻转
            自身.渲染()#重画
        def 选定(标识):
            '写入该语言；菜单随后用 onClose 重画'
            自身.选定(标识)#写入并关闭
        def 关闭():
            '收起菜单并重画'
            自身.打开=False#关闭
            自身.渲染()#重画
        with 自身.根:#行内
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            with 界面.element('div').classes('语言文'):#标题列
                界面.label(视['title']).classes('语言标题')#标题
            锚=语言选择锚(视['activeLabel'],自身.打开 is True,点锚)#药丸；菜单来画
            菜单({#语言菜单
                'open':自身.打开 is True,#开合
                'onClose':关闭,#关闭
                'items':条目,#选项
                'selectedId':视['active'],#当前
                'onSelect':选定,#写入
                'align':'end',#靠右
                'anchor':锚,#药丸
            }).渲染()#父组件调用渲染
        return 自身.根#行

    def __call__(自身,属性=None):
        '对齐 React 组件调用'
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
