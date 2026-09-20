import threading#恢复任务线程
from ....内核.作用域 import 操作任务#单次恢复任务
from .文案 import 命名空间,中文,英文#词表
from .终端图标 import 终端引导图标#开始页图标
from .终端引导 import 终端引导#开始页卡片
from .终端体 import 终端体#正文
from .终端标题 import 终端标题#页签标题
from .终端恢复 import 终端恢复#会话头恢复
from .终端清理 import 终端清理#清理通知

__all__=['依赖','应用','终端引导','终端体','终端标题','终端恢复','终端清理','命名空间','中文','英文']#仅中文公开名

依赖=['slots','locale','sidebarRight','sidebarRightTabs','webTerminals','theme']#槽、文案、侧栏、终端、主题

def 应用(上下文):#登记终端类型与席位
    """登记类型、可观察视图与后台清理。"""
    已拆除=False#寿命
    已恢复={}#会话 → 操作任务
    def 寿命():#拆除寿命
        """标死并清空恢复表。"""
        def 拆除():#卸载
            """清表。"""
            nonlocal 已拆除#改外层
            已拆除=True#死
            已恢复.clear()#清空
        return 拆除#拆除器
    上下文.副作用(寿命,'ui-sidebar-terminal.lifetime')#寿命
    def 窗口持有():#把打开的终端标签同步给终端控制器
        """订阅 openTabs 并 retainTabs。"""
        def 同步():#同步持有
            """过滤 terminal 种类。"""
            打开=上下文.sidebarRight.openTabs.getSnapshot()#打开标签
            上下文.webTerminals.retainTabs([标签 for 标签 in 打开 if 标签.get('kind')=='terminal' or getattr(标签,'kind',None)=='terminal'])#持有
        退订=上下文.sidebarRight.openTabs.subscribe(同步)#订阅
        同步()#首次
        def 拆除():#卸载
            """退订并清空持有。"""
            退订()#退订
            上下文.webTerminals.retainTabs([])#清空
        return 拆除#拆除器
    上下文.副作用(窗口持有,'ui-sidebar-terminal.window-holds')#窗口持有
    def 目标(会话标识,键):#读导航参数
        """terminal 出现域的 params。"""
        return 上下文.sidebarRight.tabDomain.occurrence(会话标识,{'id':键}).navigation.getSnapshot()['params']#params
    def 终端标识(会话标识,键):#取出 terminalId
        """params 含 terminalId 才返回。"""
        参数=目标(会话标识,键)#params
        if 参数 is not None and 'terminalId' in 参数:#有
            return 参数['terminalId']#id
        return None#无
    def 视图(会话标识,键):#终端模型
        """按出现键解析模型。"""
        参数=目标(会话标识,键)#params
        壳路径=参数['shellPath'] if 参数 is not None and 'shellPath' in 参数 else None#壳
        导航=上下文.sidebarRight.tabDomain.occurrence(会话标识,{'id':键}).navigation.getSnapshot()#导航快照
        内容标识=导航['address'] if 'address' in 导航 else None#内容地址
        return 上下文.webTerminals.view(会话标识,键,内容标识,终端标识(会话标识,键),壳路径)#模型
    包标识='@deepseek-ai/dsh-client-ui-sidebar-terminal'#实现键
    翻译=上下文.locale.bind(命名空间)#绑定
    def 登记词典():#中英文案
        """写 locale。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词典,'ui-sidebar-terminal.copy')#词典
    def 登记类型():#右侧栏类型
        """terminal 可多开。"""
        def 标题文():#类型标题
            """终端。"""
            return 翻译('title')#标题
        def 新建文():#引导标题
            """新建终端。"""
            return 翻译('new')#新建
        def 说明文():#引导说明
            """工作区命令。"""
            return 翻译('description')#说明
        return 上下文.sidebarRightTabs.register({#类型
            'id':包标识,#实现键
            'kind':'terminal',#种类
            'multiple':True,#多开
            'priority':'builtin',#内建
            'title':标题文,#标题
            'guide':[{#引导
                'id':'new',#新建
                'order':20,#顺序
                'title':新建文,#标题
                'description':说明文,#说明
                'icon':终端引导图标,#图标
            }],#引导结束
        })#登记
    上下文.副作用(登记类型,'ui-sidebar-terminal.type')#类型
    def 登记关闭():#关闭处理器
        """关标签即关进程。"""
        def 关闭(会话标识,标签):#关闭
            """同步安排清理。"""
            上下文.webTerminals.close(会话标识,标签['id'],标签.get('contentId'),终端标识(会话标识,标签['id']))#关闭
        return 上下文.sidebarRight.registerCloseHandler('terminal',关闭)#登记
    上下文.副作用(登记关闭,'ui-sidebar-terminal.close')#关闭
    def 注入面(会话标识):#标题与正文共用
        """view 与 keyedHooks。"""
        def 取视图(键):#按键
            """该出现的模型。"""
            return 视图(会话标识,键)#模型
        def 取状态(键):#keyed
            """模型 state 钩。"""
            return 视图(会话标识,键).state#状态
        return {'view':取视图,'keyedHooks':{'terminal':取状态}}#注入
    def 取主题快照():#主题快照
        """当前主题。"""
        return 上下文.theme.getTheme()#快照
    def 订主题(监听):#主题变更
        """订 theme/change。"""
        return 上下文.on('theme/change',监听)#订阅
    主题钩={'getSnapshot':取主题快照,'subscribe':订主题}#主题可观察
    def 挂引导():#开始页入口
        """guide.entry 席位。"""
        def 登记引导():#登记组件
            """注入 loadShells 与 selectShell。"""
            def 注入引导(会话标识):#引导面
                """发现与偏好写入。"""
                def 载壳(信号):#发现
                    """读宿主壳列表。"""
                    return 上下文.webTerminals.launchShells(会话标识,信号)#发现
                def 选壳(路径):#记住
                    """写下一次偏好。"""
                    上下文.webTerminals.selectShell(路径)#偏好
                return {'loadShells':载壳,'selectShell':选壳}#注入
            return 上下文.slots.register({#席位
                'name':'sidebar.right.tab.guide.entry',#槽名
                'key':包标识,#实现键
                'locale':命名空间,#文案
                'inject':注入引导,#注入
            },终端引导)#组件
        return 上下文.slots.inject('sidebar.right.tab.guide.entry',登记引导)#等槽
    上下文.副作用(挂引导,'ui-sidebar-terminal.guide')#引导
    def 挂正文():#正文席位
        """pane.tab 席位。"""
        def 登记正文():#登记组件
            """注入面加主题钩。"""
            def 注入正文(会话标识):#正文面
                """合成 view 与 theme。"""
                基=注入面(会话标识)#共用
                基['hooks']={'theme':主题钩}#主题
                return 基#注入
            return 上下文.slots.register({#席位
                'name':'sidebar.right.pane.tab',#槽名
                'key':包标识,#实现键
                'locale':命名空间,#文案
                'inject':注入正文,#注入
            },终端体)#组件
        return 上下文.slots.inject('sidebar.right.pane.tab',登记正文)#等槽
    上下文.副作用(挂正文,'ui-sidebar-terminal.body')#正文
    def 挂标题():#标题席位
        """pane.tab.title 席位。"""
        def 登记标题():#登记组件
            """注入共用面。"""
            return 上下文.slots.register({#席位
                'name':'sidebar.right.pane.tab.title',#槽名
                'key':包标识,#实现键
                'locale':命名空间,#文案
                'inject':注入面,#注入
            },终端标题)#组件
        return 上下文.slots.inject('sidebar.right.pane.tab.title',登记标题)#等槽
    上下文.副作用(挂标题,'ui-sidebar-terminal.title')#标题
    def 挂恢复():#会话头
        """conversation.session.header.actions。"""
        def 登记恢复():#登记组件
            """每会话一次恢复。"""
            def 注入恢复(会话标识):#恢复面
                """restore 去重。"""
                def 恢复():#一次
                    """已有任务则复用。"""
                    if 会话标识 in 已恢复:#已有
                        return 已恢复[会话标识]#任务
                    任务=操作任务()#新任务
                    已恢复[会话标识]=任务#记下
                    def 工作():#线程体
                        """先物化已开视图，recover 后开标签。"""
                        try:#调用
                            for 标签 in 上下文.sidebarRight.tabsIn(会话标识):#已开标签
                                if (标签.get('kind') if isinstance(标签,dict) else getattr(标签,'kind',None))=='terminal':#终端
                                    视图(会话标识,标签['id'] if isinstance(标签,dict) else 标签.id)#物化
                            终端表=上下文.webTerminals.recover(会话标识)#恢复
                            if 已拆除:#已卸
                                任务.兑现(None)#空
                                return#停
                            for 信息 in 终端表:#每个
                                上下文.sidebarRight.openTabIn(会话标识,'terminal',{#开标签
                                    'params':{'terminalId':信息['id']},#id
                                })#打开
                            任务.兑现(None)#完成
                        except Exception as 错误:#失败
                            if 会话标识 in 已恢复:#仍是本任务
                                del 已恢复[会话标识]#去掉以便重试
                            任务.拒绝(错误)#拒绝
                    threading.Thread(target=工作).start()
                    return 任务#任务
                return {'restore':恢复}#注入
            return 上下文.slots.register({#席位
                'name':'conversation.session.header.actions',#槽名
                'id':包标识,#实现键
                'locale':命名空间,#文案
                'inject':注入恢复,#注入
            },终端恢复)#组件
        return 上下文.slots.inject('conversation.session.header.actions',登记恢复)#等槽
    上下文.副作用(挂恢复,'ui-sidebar-terminal.recovery')#恢复
    def 挂清理():#根覆盖
        """shell.overlay。"""
        def 登记清理():#登记组件
            """失败列表与重试。"""
            def 注入清理():#清理面
                """hooks.closeFailures 与 retryClose。"""
                def 重试关闭(标识):#重试
                    """请求再结束。"""
                    上下文.webTerminals.retryClose(标识)#重试
                return {#注入
                    'hooks':{'closeFailures':上下文.webTerminals.closeFailures},#钩
                    'retryClose':重试关闭,#重试
                }#注入结束
            return 上下文.slots.register({#席位
                'name':'shell.overlay',#槽名
                'id':包标识,#实现键
                'locale':命名空间,#文案
                'inject':注入清理,#注入
            },终端清理)#组件
        return 上下文.slots.inject('shell.overlay',登记清理)#等槽
    上下文.副作用(挂清理,'ui-sidebar-terminal.cleanup')#清理

inject=依赖#框架槽
apply=应用#框架槽
