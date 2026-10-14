'侧栏槽组件：品牌、新建会话、全局面板、工作区浏览和设置都从子槽画出来'

import os
from nicegui import ui as 界面
from ...ui_聊天.异常 import 页面失败文案
from ...ui_基础界面组件.鱼标 import 鱼标
from .文案 import 中文

__all__=['侧栏壳']

样式表=(
    '.侧栏壳{display:flex;flex-direction:column;height:100%;min-height:0;width:100%;box-sizing:border-box;padding:6px 12px;overflow:hidden;background:var(--dsw-specific-sidebar-fill);color:var(--dsw-alias-label-primary);font-size:14px}'
    '.侧栏壳.收起{padding:18px 10px 6px;align-items:center}'
    '.侧栏壳 .顶{width:100%;flex:none;align-items:center;justify-content:space-between;flex-wrap:nowrap;gap:8px;min-height:36px}'
    '.侧栏壳.收起 .顶{justify-content:center}'
    '.侧栏壳 .浏览{flex:1 1 auto;min-height:0;width:100%;overflow:auto}'
    '.侧栏壳 .脚{flex:none;width:100%}'
    'button.q-btn.侧栏品牌,button.q-btn.侧栏新建,button.q-btn.侧栏开关,button.q-btn.侧栏面板{color:inherit !important;background:transparent;min-height:36px}'
    '.侧栏壳.收起 button.q-btn.侧栏开关,.侧栏壳.收起 button.q-btn.侧栏新建,.侧栏壳.收起 button.q-btn.侧栏面板{width:36px;height:36px;min-height:36px;padding:0}'
    '.侧栏壳 .品牌名{font-size:14px;line-height:20px;font-weight:510}'
    '.侧栏壳.收起 .轨鱼{display:inline-flex}.侧栏壳.收起 .轨面板{display:none}'
    '.侧栏壳.收起 .侧栏开关:hover .轨鱼{display:none}.侧栏壳.收起 .侧栏开关:hover .轨面板{display:inline-flex}'
    '.侧栏壳 button.q-btn.text-primary,.侧栏壳 button.q-btn.text-primary .q-icon{color:var(--dsw-alias-label-primary,#111827) !important}'
)
样式已登记=False

def 本地构建版本():
    '与上游 localBuildVersion 相同：没有版本就没有第二行'
    版本=os.environ.get('DSH_CLIENT_VERSION')
    if 版本 is None:
        return None
    提交=os.environ.get('DSH_CLIENT_COMMIT_HASH')
    尾='' if 提交 is None else '-'+提交
    if os.environ.get('DSH_CLIENT_GIT_DIRTY')=='true':
        尾=尾+'-dirty'
    return 版本+尾

def 登记样式():
    '同一段侧栏样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表, shared=True)
    样式已登记=True

class 侧栏壳:
    'root 槽交给侧栏的那一列'

    def __init__(自身,属性):
        '记下 props 并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成 props
        自身._已订=False#面板钩子只订一次
        自身._盒=None#可清空的列
        自身.渲染()#槽位只调用构造

    def 取(自身,键,默认=None):
        '缺键时用默认'
        if 键 in 自身.属性:
            return 自身.属性[键]#值
        return 默认#默认

    def 文(自身,键):
        '侧栏文案。注入翻译抛错后改用本包词表，两边都没有则返回失败句'
        译=自身.取('t')#文案座位
        if callable(译):
            try:
                文本=译(键)#词
            except Exception:
                文本=None
            if isinstance(文本,str) and 文本!=键:
                return 文本
        if 键 in 中文:
            return 中文[键]
        if 键=='brand.localBuild':
            return 'DSH 本地构建'
        return '文案没有读到'

    def 画槽(自身,名,拥有方=None,选项=None):
        '有 renderSlot 才画子槽；一个子槽失败不拆掉整列'
        画=自身.取('renderSlot')#座位
        if callable(画) is not True:#没装
            return None#跳过
        方={} if 拥有方 is None else 拥有方#属主
        try:#子槽
            if 选项 is None:#无选项
                return 画(名,方)#画
            return 画(名,方,选项)#带选项
        except Exception as 错误:
            界面.label(页面失败文案(错误))
            return False

    def 槽空(自身,结果):
        '没有登记，或出口没有内容'
        if 结果 is None:#没画
            return True#空
        if isinstance(结果,dict) and 结果.get('type')=='slot-outlet' and 结果.get('content') is None:#空出口
            return True#空
        return False

    def 渲染(自身):
        '宽列或 56 像素图标轨'
        登记样式()
        收起=自身.取('collapsed') is True#左栏收起
        开新=自身.取('startSession')#新建
        切换=自身.取('toggleSidebar')#折叠
        选面板=自身.取('selectPanel')#选面板
        用面板=自身.取('usePanels')#面板列表钩
        用面板信息=自身.取('usePanelInfo')#当前面板钩
        面板=[]#行
        if callable(用面板):
            值=用面板(lambda 快照:快照)#整表
            if isinstance(值,list):#是列表
                面板=值#用
        def 点新建():
            '开始一条新会话'
            if callable(开新):
                开新()
        def 点切换():
            '收起或展开左栏'
            if callable(切换):
                切换()#切
        def 请求展开():
            '轨态下的浏览区请求把列展开'
            if 收起 and callable(切换):#收着
                切换()#展开
        if 自身._盒 is None:#第一次
            自身._盒=界面.column()#列
        自身._盒.clear()#重画前清掉旧控件
        自身._盒.classes(remove='侧栏壳 收起')#去掉上一态
        自身._盒.classes(add='侧栏壳 收起' if 收起 else '侧栏壳')#当前态
        with 自身._盒:#列
            with 界面.row().classes('顶'):#顶
                if not 收起:#宽
                    def 点品牌():
                        '字标同时是新建会话'
                        点新建()
                    品牌钮=界面.button(on_click=点品牌).props('flat no-caps').classes('侧栏品牌')
                    品牌钮.props('aria-label="'+自身.文('session.new.label')+'"')
                    品牌钮.tooltip(自身.文('session.new.label'))
                    with 品牌钮:
                        标=自身.画槽('sidebar.brand.mark',{'size':24})
                        if 自身.槽空(标):
                            鱼标({'size':24}).渲染()
                        名=自身.画槽('sidebar.brand.name',{})
                        if 自身.槽空(名):
                            版本=本地构建版本()
                            if 版本 is None:
                                界面.label(自身.文('brand.localBuild')).classes('回退品牌名')
                            else:
                                with 界面.column().classes('本地构建牌'):
                                    界面.label(自身.文('brand.localBuild')).classes('本地构建题')
                                    界面.label(版本).classes('构建版本')
                开关=界面.button(on_click=点切换).props('flat dense round').classes('侧栏开关')#折叠
                开关.tooltip(自身.文('toggle.open' if 收起 else 'toggle.collapse'))#提示
                with 开关:
                    if 收起:
                        with 界面.element('span').classes('轨鱼'):
                            轨标=自身.画槽('sidebar.brand.mark',{'size':24})
                            if 自身.槽空(轨标):
                                鱼标({'size':24}).渲染()
                        with 界面.element('span').classes('轨面板'):
                            界面.icon('menu', size='18px')
                    else:
                        界面.icon('menu', size='16px')
            新建=界面.button(on_click=点新建).props('flat no-caps').classes('侧栏新建')#新建
            新建.tooltip(自身.文('session.new.label'))#提示
            with 新建:#图标和字
                界面.icon('edit', size='18px' if 收起 else '14px')#新会话
                if not 收起:#宽才出字
                    界面.label(自身.文('session.new'))#新会话
            if len(面板)>0:
                for 行 in 面板:#逐行
                    if not isinstance(行,dict):#不是行
                        continue#跳
                    身份=行['id'] if 'id' in 行 else None#id
                    标签=行['label'] if 'label' in 行 else 身份#标签
                    def 点(钉=身份):
                        '切到这个面板'
                        if callable(选面板) and 钉 is not None:
                            选面板(钉)#选
                    活动=False#是否当前
                    if callable(用面板信息) and 身份 is not None:#能读
                        活动=用面板信息(lambda 信息,钉=身份: isinstance(信息,dict) and 信息.get('activePanelId')==钉) is True#当前
                    面板钮=界面.button(on_click=点).props('flat no-caps'+((' aria-current=page') if 活动 else '')).classes('侧栏面板')#行
                    if 标签 is not None:
                        面板钮.tooltip(str(标签))#轨态提示
                    with 面板钮:#图标
                        图标=自身.画槽('sidebar.panellist',{'size':16 if not 收起 else 18,'active':活动},{'only':身份})#图标
                        if 自身.槽空(图标):#没有登记
                            界面.icon('dashboard', size='16px')#回退
                        if not 收起 and 标签 is not None:#宽
                            界面.label(str(标签))#标题
            with 界面.column().classes('浏览'):#工作区
                自身.画槽('sidebar.workspaces',{'wide':not 收起,'expandSidebar':请求展开})#浏览区
            with 界面.column().classes('脚'):#脚
                自身.画槽('sidebar.footer.action',{'wide':not 收起})#页脚动作
                自身.画槽('sidebar.settings',{'wide':not 收起})#设置
        if 自身._已订 is not True:#只订一次
            def 重画():
                '面板列表或当前面板变了就重画这一列。列已被拆掉则不再画。'
                盒=自身._盒#列
                if 盒 is None:#还没有
                    return#不画
                槽=getattr(盒,'parent_slot',None)#父槽
                if 槽 is not None and getattr(槽,'parent',None) is None:#已从页面拆掉
                    return#不画
                自身.渲染()
            for 钩 in (用面板,用面板信息):#两个钩
                订=getattr(钩,'_subscribe',None) if 钩 is not None else None#订阅
                if callable(订):#能订
                    订(重画)#订上
            自身._已订=True

    def __call__(自身):
        '再画一次'
        return 自身.渲染()
