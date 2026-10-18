from . import 创建插件菜单项
from . import 分区存储
from . import 指南文案
from . import 文案
from . import 芯片存储
from . import 设置存储
from . import 预设分区
from . import 预设标签
from . import 预设芯片
from . import 预设指南
from .文案 import 中文
from .设置存储 import 写默认预设 as 写默认预设
from .设置存储 import 设置命名空间 as 设置命名空间

__all__=[
    '命名空间','依赖','应用','设置命名空间','写默认预设',
    '文案','指南文案','设置存储','分区存储','芯片存储',
    '预设标签','预设芯片','预设分区','预设指南','创建插件菜单项',
]

命名空间=文案.命名空间#settings.agentPreset
依赖=['slots','sessions','locale','remote','remote.agentPresets','remote.settings','configForms']#纤程依赖
工具设置命名空间='ui-settings'#编码工具偏好所在的设置

def 应用(上下文,配置=None):
    '登记词典，并挂上新会话芯片、页眉标签、设置分区和创建插件菜单'
    工具设置=上下文.configForms.get(工具设置命名空间)#编码工具
    预设设置=上下文.configForms.get(设置命名空间)#预设默认
    活动=[True]#拆掉之后不再改默认

    def 编码工具已关():
        '宿主偏好第一次被接受前不算关掉。拆掉之后也不再改'
        if 活动[0] is not True:#已拆
            return False#不改
        值=工具设置.getSnapshot().get('value')#已接受的节
        if not isinstance(值,dict):#还没有
            return False#不关
        return 值.get('enabled') is False#显式关掉

    控制器=设置存储.预设设置控制器(上下文)#页眉和创建插件用的名册
    暂存={'id':None,'introduce':False}#同一页芯片共用的下一次选择
    座位表={}#绑定身份到芯片控制器。绑定是字典，弱映射放不进去
    已绑定拆除=set()#随绑定作用域拆掉的订阅

    def 清绑定座位():
        '插件拆掉时拆掉还挂着的绑定订阅'
        def 拆全部():
            '逐个拆'
            for 拆 in list(已绑定拆除):#拷贝
                拆()#拆
        return 拆全部
    上下文.副作用(清绑定座位,'ui-agent-preset: bound selections')

    def 没有会话():
        '新会话画面还没有可套用的会话'
        return None
    未绑定=芯片存储.芯片控制器(上下文,没有会话,暂存)#还没有会话时的芯片

    def 座位给(绑定):
        '每个会话绑定一份芯片。绑定换代后不再套用'
        已有=座位表.get(id(绑定))#已有
        if 已有 is not None:#有
            return 已有#复用

        def 当前会话():
            '绑定还是这一代，并且主视图留着，才返回摘要'
            if 上下文.sessions.binding(绑定['sessionId']) is not 绑定:#换代了
                return None#没有
            摘要=上下文.sessions.list.getSnapshot()['byId'].get(绑定['sessionId'])#摘要
            if 摘要 is None:#不在列表里
                return None#没有
            快照=上下文.sessions.retainInfo(绑定['sessionId'])['getSnapshot']()#保留
            保留=快照.get('retainedBy') if isinstance(快照,dict) else None#按源
            主=0#主视图次数
            if isinstance(保留,dict) and 保留.get('mainView') is not None:#有计数
                主=保留['mainView']#次数
            if 主>0:#主视图还留着
                return 摘要#摘要
            return None#不套用

        座位=芯片存储.芯片控制器(上下文,当前会话,暂存)#这一绑定
        座位表[id(绑定)]=座位#记下

        def 订列表():
            '列表变化时再试着套用。绑定结束就拆掉'
            def 列表变了():
                '会话出现或换代'
                座位.套用()#套用
            停=上下文.sessions.list.subscribe(列表变了)#订

            def 拆():
                '退订并从表里拿掉'
                停()#退订
                座位表.pop(id(绑定),None)#拿掉
                已绑定拆除.discard(拆)#拿掉
            return 拆
        拆除=绑定['ctx'].副作用(订列表,'ui-agent-preset: Provider binding')#跟绑定走
        已绑定拆除.add(拆除)#插件拆掉时也能找到
        return 座位#控制器

    分区=分区存储.分区控制器(上下文)#设置页

    def 守开发工具():
        '关掉开发者工具时清掉还没套用的暂存'
        def 关时清暂存():
            '开着就不动'
            if 开发工具.getSnapshot():#仍开着
                return#不动
            暂存['id']=None#清选择
            暂存['introduce']=False#清介绍
            未绑定.套用()#没有会话的那份
            for 座位 in list(座位表.values()):#每一场
                座位.套用()#套用
        return 开发工具.subscribe(关时清暂存)#订阅
    上下文.副作用(守开发工具,'ui-agent-preset: Developer tools gate')

    def 登记词典():
        '登记中英文案表。页面上的字不走英文表'
        return 上下文.locale.register(命名空间,{'zh':文案.中文,'en':文案.英文})#拆除时卸下
    上下文.副作用(登记词典,'ui-agent-preset: settings row dictionaries')
    请求次=[0]#对齐请求
    进行=[False]#对齐进行中

    def 对齐():
        '设置或编码工具变了就再核对默认。核对途中又变了，用最新的再来一次'
        请求次[0]=请求次[0]+1#新请求
        if 进行[0]:#已经在核对
            return#外层循环会看到新次数
        进行[0]=True#占住
        try:#核对
            while True:#直到没有新请求
                修订=请求次[0]#这一轮
                分区.对齐编码工具(编码工具已关)#可能写回标准
                if 活动[0] is not True or 请求次[0]==修订:#拆了或没有新的
                    return#停
        finally:#放开
            进行[0]=False#结束

    def 刷新(*_参数):
        '设置文档或重连之后，名册和芯片一起重读'
        控制器.加载()#页眉名册
        if 分区.存储.getSnapshot()['status']!='idle':#设置页已经读过
            分区.加载()#再读
        未绑定.加载()#没有会话的芯片
        for 座位 in list(座位表.values()):#每一场
            座位.加载()#再读
        对齐()#默认可能要改回标准

    def 刷新设置():
        '编码工具、预设设置、设置文档和重连都会刷新'
        def 设置文档已更新(命名空间名):
            '只认这份预设设置'
            if 命名空间名!=设置命名空间:#别的命名空间
                return#不管
            刷新()#重读
        拆除器=[#这些订阅
            工具设置.subscribe(对齐),
            预设设置.subscribe(对齐),
            上下文.remote.on('settings/document-updated',设置文档已更新),
            上下文.监听('connection/reset',刷新),
        ]
        对齐()#挂上时先核对一次

        def 拆():
            '停掉订阅。之后的核对不再写默认'
            活动[0]=False#拆了
            for 拆一个 in 拆除器:#逐个
                拆一个()#拆
        return 拆
    上下文.副作用(刷新设置,'ui-agent-preset: settings refresh')
    创造草稿=[None]#设置页按钮读当前有没有会话流

    def 会话范围(范围,配置=None):
        '等会话、对话和工作区都在，再挂芯片、页眉和创建插件'

        def 芯片注入(会话标识=None):
            '没有会话用未绑定的那份，有会话用那一场的'
            绑定=None if 会话标识 is None else 上下文.sessions.binding(会话标识)#绑定
            座位=未绑定 if 绑定 is None else 座位给(绑定)#控制器
            return {#注入
                'hooks':{'agentPresetSeat':座位.存储,'developerTools':上下文.configForms.developerTools.enabled},
                'load':座位.加载,
                'select':座位.选定,
                'dismissRefusal':座位.确认拒绝,
                'introduced':座位.已介绍,
            }

        def 标签注入(会话标识=None):
            '页眉只读名册'
            return {#注入
                'hooks':{'agentPresets':控制器.存储},
                'load':控制器.加载,
            }

        def 开始创造草稿():
            '把创造模式暂存到主视图那场空白会话，并开一场新会话'
            摘要=None#主视图空白会话
            for 会话 in 上下文.sessions.list.getSnapshot()['byId'].values():#找
                保留=会话.get('retainedBy') or {}#保留
                主=保留.get('mainView') or 0#主视图
                if 会话.get('blank') and 主>0:#空白且留在主视图
                    摘要=会话#这场
                    break#停
            绑定=None if 摘要 is None else 上下文.sessions.binding(摘要['id'])#绑定
            座位=未绑定 if 绑定 is None else 座位给(绑定)#芯片
            座位.暂存('cordis',True)#介绍一次
            范围.uiWorkspace.startSession(None,{'clearPreviousDraft':False,'agentPreset':'cordis'})#开一场

        def 挂芯片和标签():
            '新会话芯片和页眉标签。作用域结束就卸下'
            创造草稿[0]=开始创造草稿#设置页这时能看见入口
            芯片=范围.slots.register({#新会话
                'name':'conversation.hero.agentPreset',
                'locale':命名空间,
                'inject':芯片注入,
            },预设芯片.预设芯片)
            标签=范围.slots.register({#页眉
                'name':'conversation.session.header.actions',
                'id':'agent-preset',
                'order':-10,
                'locale':命名空间,
                'inject':标签注入,
            },预设标签.预设标签)

            def 拆():
                '卸下两处，并藏起创造模式入口'
                创造草稿[0]=None#没有会话流
                芯片()#卸芯片
                标签()#卸标签
            return 拆
        范围.副作用(挂芯片和标签,'ui-agent-preset: new-session chip and header label')

        def 登记创建():
            '添加插件菜单里的创造模式一行'
            def 注入():
                '名册和开创造模式'
                return {#注入
                    'hooks':{'agentPresets':控制器.存储},
                    'load':控制器.加载,
                    'startCreatorDraft':开始创造草稿,
                }
            return 范围.slots.register({#菜单行
                'name':'plugins.add.actions',
                'id':'create-plugin',
                'locale':命名空间,
                'inject':注入,
            },创建插件菜单项.创建插件菜单项)
        范围.slots.inject('plugins.add.actions',登记创建)#等菜单槽

    上下文.依赖启动(['slots','conversation','sessions','uiWorkspace'],会话范围)#等这些服务

    def 设为默认(标识):
        '点下时再捕获主视图那场空白会话'
        摘要=None#空白会话
        for 会话 in 上下文.sessions.list.getSnapshot()['byId'].values():#找
            保留=会话.get('retainedBy') or {}#保留
            主=保留.get('mainView') or 0#主视图
            if 会话.get('blank') and 主>0:#留在主视图的空白会话
                摘要=会话#这场
                break#停
        绑定=None if 摘要 is None else 上下文.sessions.binding(摘要['id'])#绑定
        座位=None if 绑定 is None else 座位给(绑定)#芯片
        会话标识=None if 座位 is None else 座位.空白会话标识()#捕获

        def 同步(写入标识):
            '绑定还是这一份，并且捕获的会话没换，才套用'
            if 座位 is None or 会话标识 is None or 绑定 is None or 座位表.get(id(绑定)) is not 座位:#已经不是
                return None#不用套
            return 座位.同步空白会话(会话标识,写入标识)#套用
        return 分区.设为默认(标识,同步)#先写设置再同步

    def 分区注入():
        '设置页的动作。没有会话流时不给创造模式入口'
        面={#注入
            'hooks':{
                'agentPresetSection':分区.存储,
                'developerTools':上下文.configForms.developerTools.enabled,
            },
            'load':分区.加载,
            'view':分区.查看,
            'closeView':分区.关闭查看,
            'makeDefault':设为默认,
        }
        if 创造草稿[0] is not None:#芯片和会话流还在
            面['startCreatorDraft']=创造草稿[0]#入口
        return 面#注入

    def 导航名():
        '设置分区标题。用中文表原文'
        return 中文['nav']#Agent 预设

    def 登记分区():
        '排在模型后面'
        return 上下文.slots.register({#设置分区
            'name':'settings.section',
            'id':'agent-presets',
            'order':20,
            'label':导航名,
            'locale':命名空间,
            'inject':分区注入,
        },预设分区.预设分区)
    上下文.slots.inject('settings.section',登记分区)#等设置分区槽

inject=依赖#纤程依赖
apply=应用#浏览器入口
