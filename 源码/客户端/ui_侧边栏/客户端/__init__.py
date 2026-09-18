from ...存储 import 创建快照存储#快照存储
from .文案 import 中文,英文,侧栏文案键#词典
from .约定.槽位 import 侧栏槽名,侧栏子槽,侧栏词表命名空间#槽约定
from .侧栏根 import 侧栏根,折叠落定毫秒,滚动条滞留毫秒,样式表#根组件
from .头部前置控件 import 头部前置控件#macOS 前置控件

__all__=[#仅中文公开名
    '注入','应用','命名空间','中文','英文','侧栏文案键',
    '侧栏槽名','侧栏子槽','侧栏词表命名空间',
    '侧栏根','折叠落定毫秒','滚动条滞留毫秒','样式表','头部前置控件',
]#公开面结束

命名空间=侧栏词表命名空间#词表命名空间
注入=['slots','layout','uiWorkspace','locale']#槽位、布局、工作区 UI、文案

def 解析槽标签(标签):#解析槽标签
    """对齐 ui-slots resolveSlotLabel。字面量或零参 thunk。"""
    if 标签 is None:return None#无标签
    if callable(标签):return 标签()#thunk
    return 标签#字面量

def 应用(上下文):#安装侧栏壳
    """登记词典、同步全局面板列表，并注入登记侧栏壳槽位。"""
    def 登记词表():#登记本包词典
        """把中英文词表交给 locale。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词表,'ui-sidebar: dictionaries')#登记中英文案
    面板=创建快照存储([])#面板元数据快照
    def 同步面板():#同步面板列表登记
        """从 `sidebar.panellist` 条目重建可序列化元数据。"""
        下一批=[]#收集
        for 条目 in 上下文.slots.entriesOfSlot('sidebar.panellist'):#列表项
            选项=条目['options'] if 'options' in 条目 else 条目.options#选项
            身份=选项['id'] if isinstance(选项,dict) else 选项.id#主面板身份
            序=选项['order'] if isinstance(选项,dict) and 'order' in 选项 else getattr(选项,'order',0)#行序
            if 序 is None:序=0#缺省
            标签源=选项['label'] if isinstance(选项,dict) and 'label' in 选项 else getattr(选项,'label',None)#标签源
            标签=解析槽标签(标签源)#已解析标签
            if 标签 is None:标签=身份#回退 id
            下一批.append({'id':身份,'order':序,'label':标签})#元数据行
        下一批.sort(key=lambda 行:行['order'])#按行序升序
        上一=面板.getSnapshot()#上一快照
        if len(上一)==len(下一批) and all(#内容未变则跳过
            上一[下标]['id']==下一批[下标]['id']
            and 上一[下标]['order']==下一批[下标]['order']
            and 上一[下标]['label']==下一批[下标]['label']
            for 下标 in range(len(上一))
        ):return#无变更
        面板.set(下一批)#写入新快照
    def 订面板条目():#订阅面板登记
        """订阅 `sidebar.panellist`。"""
        return 上下文.slots.subscribe('sidebar.panellist',同步面板)#订阅
    上下文.副作用(订面板条目,'ui-sidebar: panel entries')#面板登记
    def 订面板文案():#订阅文案变更
        """语言切换时重算面板标签。"""
        return 上下文.locale.subscribe(同步面板)#订阅
    上下文.副作用(订面板文案,'ui-sidebar: panel labels')#面板文案
    def 开新会话(工作区标识=None):#开新会话
        """转调 uiWorkspace.startSession。"""
        return 上下文.get('uiWorkspace').startSession(工作区标识)#开新会话
    def 切换侧栏():#切换侧栏
        """转调 layout.toggleSidebar。"""
        return 上下文.layout.toggleSidebar()#切换
    def 选面板(身份):#选中全局面板
        """转调 layout.selectPanel。"""
        return 上下文.layout.selectPanel(身份)#选面板
    def 注入面():#根注入
        """开新会话、切换侧栏、选面板与面板钩子。"""
        return {#注入
            'startSession':开新会话,#开新会话
            'toggleSidebar':切换侧栏,#切换侧栏
            'selectPanel':选面板,#选面板
            'hooks':{'panels':面板},#面板快照钩子
        }#注入结束
    def 挂槽():#登记侧栏槽
        """注入并登记侧栏壳。"""
        return 上下文.slots.register({#登记
            'name':侧栏槽名,#槽名
            'locale':命名空间,#文案
            'children':侧栏子槽,#子槽
            'inject':注入面,#注入
        },侧栏根)#根组件
    上下文.slots.inject('sidebar',挂槽)#注入登记
    def 挂前置():#对话 header 前置席
        """macOS 折叠侧栏时的打开/新建控件。"""
        return 上下文.slots.register({#登记
            'name':'conversation.session.header.leading',#前置席
            'locale':命名空间,#文案
            'inject':注入面,#复用根注入
        },头部前置控件)#组件
    上下文.slots.inject('conversation.session.header.leading',挂前置)#注入前置
    同步面板()#首次同步面板列表

inject=注入#框架槽
apply=应用#框架槽
