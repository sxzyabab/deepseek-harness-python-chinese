from ....宿主.在应用中打开.共享 import 图标前缀#线路径
from .控制器 import 在应用中打开控制器#页面控制器
from .打开路径 import 在应用中打开路径控制器#文件打开
from .在应用中打开动作 import 在应用中打开动作,会话头打开动作#目录按钮与会话头适配
from .文案 import 命名空间,中文,英文#词典
from ..异常 import 页面失败文案#去掉路径的失败句
from . import (
    打开失败提示,
    打开目标按钮,
    打开路径,
    打开路径动作,
    打开路径空动作,
    应用列表,
    文件应用,
    文件路由动作,
)

__all__=[#仅中文公开名
    '依赖','应用',
    '在应用中打开控制器','在应用中打开动作','会话头打开动作',
    '命名空间','中文','英文',
]

依赖=['sessions','slots','locale','remote','remote.session','shortcuts','layout']#词典、目录按钮、文件打开与快捷键

def 应用(上下文):#客户端插件体
    '登记词典与会话头部 utilities 分体按钮'
    控制器=在应用中打开控制器()#页面生命一份
    控制器.加载()#每页一次可用性
    def 登记词典():#登记中英文案
        '把 open-in-app 词表写进 locale'
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#词典
    上下文.副作用(登记词典,'open-in-app: dictionaries')#词典
    def 注入面():#控制器注入面
        'hooks / launch / choose / iconUrl'
        def 启动(应用标识,路径):#启动代理
            '转调控制器'
            return 控制器.启动(应用标识,路径)#期约
        def 选定(应用标识):#选定代理
            '转调控制器'
            控制器.选定(应用标识)#持久化
        def 图标网址(应用标识):#图标 URL
            '主机图标前缀加 id'
            return 图标前缀+'/'+应用标识#拼 URL
        return {#OpenInAppActionInjected
            'hooks':{#可观察源
                'openInAppApps':控制器.应用表,#可用性
                'openInAppChoice':控制器.选择,#上次选择
                'openInAppLaunch':控制器.操作,#启动阶段
                'shortcuts':上下文.shortcuts.catalog,#键位目录
            },#hooks 结束
            'launch':启动,
            'choose':选定,#选定
            'iconUrl':图标网址,#图标
        }#注入面结束
    def 挂头部():#登记 utilities 槽
        'conversation.session.header.utilities'
        return 上下文.slots.register({#登记
            'name':'conversation.session.header.utilities',#槽名
            'id':'open-in-app',#贡献 id
            'order':-10,#序
            'locale':命名空间,#词表
            'inject':注入面,#注入
        },会话头打开动作)#只读 cwd，不画文件树
    上下文.slots.inject('conversation.session.header.utilities',挂头部)#等槽
    路径控制器=在应用中打开路径控制器(上下文.remote)#文件打开
    译=上下文.locale.bind(命名空间)#命令标签
    def 取行表():
        '会话列表 byId'
        快照=上下文.sessions.list.getSnapshot()#列表
        if isinstance(快照,dict):#字典快照
            return 快照.get('byId') or {}#表
        表=getattr(快照,'byId',None)#对象
        return 表 if isinstance(表,dict) else {}#表
    def 主视图数(行):
        'mainView 保留数'
        保留=行.get('retainedBy') if isinstance(行,dict) else getattr(行,'retainedBy',None)#保留
        if isinstance(保留,dict):#字典
            return 保留.get('mainView') or 0#数
        return getattr(保留,'mainView',0) or 0#数
    def 工作目录(行):
        '行上的 cwd'
        if isinstance(行,dict):#字典
            return 行.get('cwd')#目录
        return getattr(行,'cwd',None)#目录
    def 是会话界面():
        '活动面板为空才是会话界面。读不到 panelInfo 时按默认：没有活动面板。'
        布局=getattr(上下文,'layout',None)#布局服务
        源=getattr(布局,'panelInfo',None)#面板快照
        if 源 is None or not hasattr(源,'getSnapshot'):#这一版布局没有该源
            return True#默认就是会话界面
        快照=源.getSnapshot()#面板
        if isinstance(快照,dict):#字典
            if 'activePanelId' not in 快照:#字段缺席
                return False#不能当成会话界面
            return 快照['activePanelId'] is None#空才是
        if not hasattr(快照,'activePanelId'):#没有字段
            return False#不能当成会话界面
        return getattr(快照,'activePanelId') is None#空才是
    def 快捷键目标():
        '主视图里的工作区，且已有可命名应用。右栏占住主面时不可用。'
        if not 是会话界面():#不是会话界面
            return None#不可用
        应用标识=控制器.当前应用()#应用
        if 应用标识 is None:#没有
            return None#不可用
        for 行 in 取行表().values():#各会话
            if 主视图数(行)<=0:#不是主视图
                continue#下一条
            目录=工作目录(行)#cwd
            if isinstance(目录,str) and 目录!='':#有目录
                return {'appId':应用标识,'path':目录}#目标
        return None#没有
    def 登记打开命令():
        '在本地打开当前工作区。只调用控制器启动，不改命令分发。'
        def 解析(_事件=None):
            '忙、不是会话界面或没有目标则拦住'
            阶段=控制器.操作.getSnapshot()#启动阶段
            if isinstance(阶段,dict) and 阶段.get('phase')=='busy':#在飞
                return {'status':'blocked','reason':译('shortcut.busy')}#拦住
            选中=快捷键目标()#目标
            if 选中 is None:#没有
                return {'status':'blocked','reason':译('shortcut.unavailable')}#拦住
            def 记下(错误):
                '失败句去掉绝对路径后再留下'
                print('workspace open rejected:',页面失败文案(错误))#警告
            def 执行():
                '启动记住的应用'
                try:#发出
                    产出=控制器.启动(选中['appId'],选中['path'])#打开
                except Exception as 错误:#同步失败
                    记下(错误)#警告
                    return
                if hasattr(产出,'然后'):#本层期约
                    产出.然后(lambda _值:None,记下)#失败警告
                    return
                if hasattr(产出,'then'):#上游期约
                    产出.then(lambda _值:None,记下)#失败警告
            return {'status':'handled','run':执行}#执行
        return 上下文.shortcuts.register({#命令
            'id':'workspace.openLocal',#命令
            'label':lambda: 译('open.tooltip'),#标签
            'aliases':['open workspace locally','open in app'],#别名
            'defaults':{#各平台
                'desktop:macos':{'code':'KeyO','modifiers':['primary','alt']},
                'desktop:windows':{'code':'KeyO','modifiers':['primary','alt']},
                'desktop:linux':{'code':'KeyO','modifiers':['primary','alt']},
                'web:macos':{'code':'KeyO','modifiers':['primary','shift']},
                'web:windows':{'code':'KeyO','modifiers':['primary','shift']},
            },#默认结束
            'regions':['page','editable'],#区域
            'modals':[],#模态
            'resolve':lambda _事件=None: 解析(),#执行
        })#登记结束
    上下文.副作用(登记打开命令,'open-in-app: workspace command')#命令
    def 挂文件页():
        '文件标签动作'
        return 上下文.slots.register({#登记
            'name':'sidebar.right.tab.files.actions',#槽
            'id':'open-in-app',#贡献
            'locale':命名空间,#词表
            'inject':注入面,#与头部同一套目录打开
        },在应用中打开动作)#组件
    上下文.slots.inject('sidebar.right.tab.files.actions',挂文件页)#等槽
    def 路径注入():
        '桌面探测与按路径打开'
        return {#注入
            'hooks':{'openInAppDesktop':路径控制器.桌面},#可用性
            'loadDesktop':路径控制器.加载,#再探测
            'openPath':路径控制器.打开路径,#打开或揭示
            'applications':路径控制器.应用列表,#联想
        }#注入结束
    def 挂文档动作():
        '文档头打开'
        return 上下文.slots.register({#登记
            'name':'sidebar.right.tab.document.actions',#槽
            'id':'open-in-app',#贡献
            'locale':命名空间,#词表
            'inject':路径注入,#注入
        },打开路径动作)#组件
    上下文.slots.inject('sidebar.right.tab.document.actions',挂文档动作)#等槽
    def 挂不可预览():
        '不可预览空态上的大按钮'
        return 上下文.slots.register({#登记
            'name':'sidebar.right.tab.document.unpreviewable',#槽
            'id':'open-in-app',#贡献
            'locale':命名空间,#词表
            'inject':路径注入,#注入
        },打开路径空动作)#组件
    上下文.slots.inject('sidebar.right.tab.document.unpreviewable',挂不可预览)#等槽
    def 挂交付动作():
        '交付文件上的打开'
        return 上下文.slots.register({#登记
            'name':'deliverables.file.actions',#槽
            'id':'open-in-app',#贡献
            'locale':命名空间,#词表
        },文件路由动作)#组件
    上下文.slots.inject('deliverables.file.actions',挂交付动作)#等槽
    def 挂审阅动作():
        '改动审阅文件上的打开'
        return 上下文.slots.register({#登记
            'name':'deliverables.review.file.actions',#槽
            'id':'open-in-app',#贡献
            'locale':命名空间,#词表
        },文件路由动作)#组件
    上下文.slots.inject('deliverables.review.file.actions',挂审阅动作)#等槽

inject=依赖#框架槽
apply=应用#框架槽
