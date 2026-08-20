"""Cordis 动态插件卡片的浏览器半：清单面板、工具行登记与 @pluginId 源。

对齐上游 `ui-cordis/src/client/index.ts` 的 apply 接线。公开面仅中文名。
Define/Run/Action 行与面板已落盘嵌套 JSX 结构树+样式原文；DisclosureRow/CodeBlock/图标/业务视图槽仍需浏览器。
"""
from .文案 import 命名空间,中文,英文,文案键#词典
from .状态 import 取包,可见状态#状态
from .清单 import 创建清单源#清单
from .面板 import 面板,选定包标识,面板可见状态,阻塞优先,样式表 as 面板样式表#面板
from .卡片模型 import 定义卡片,运行卡片,动作卡片,调用状态#卡模型
from .运行卡片索引 import 工具视图键,创建仓,运行卡片注册表#卡仓
from .定义行 import 定义行,样式表 as 定义行样式表#定义行
from .运行行 import 运行行,样式表 as 运行行样式表#运行行
from .动作行 import 动作行#动作行
from .槽位 import (#槽面
    业务视图槽名,业务视图所有者字段,卡片面钩子,运行卡片面钩子,面板面钩子,面板面动词,业务视图键,
)#槽
from .动态端口 import 动作结果成功,动作结果失败,端口动词,规范化动作结果#端口
from .事件 import (#Remote 组装再导出的动态 Cordis 词汇
    审批请求标识,动态包标识,动态插件标识,动态运行标识,动态运行模式,
    清单行字段,动态包公告字段,请求已落定字段,撤回公告字段,运行请求字段,
)#事件

__all__=[#仅中文公开名
    '注入','应用','命名空间','中文','英文','文案键',
    '取包','可见状态','创建清单源','面板',
    '选定包标识','面板可见状态','阻塞优先','面板样式表',
    '定义卡片','运行卡片','动作卡片','调用状态',
    '工具视图键','创建仓','运行卡片注册表',
    '定义行','运行行','动作行','定义行样式表','运行行样式表',
    '业务视图槽名','业务视图所有者字段','卡片面钩子','运行卡片面钩子','面板面钩子','面板面动词','业务视图键',
    '动作结果成功','动作结果失败','端口动词','规范化动作结果',
    '审批请求标识','动态包标识','动态插件标识','动态运行标识','动态运行模式',
    '清单行字段','动态包公告字段','请求已落定字段','撤回公告字段','运行请求字段',
]#公开面结束

注入=['slots','locale','inputTriggers','remote','remote.dynamicCordisRunner','dynamicCordisRunner']#硬依赖

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 应用(上下文):#安装浏览器半
    """登记词典、清单端口、工具行、面板槽与 @pluginId 源。行组件为结构树面。"""
    上下文.effect(lambda:上下文.locale.register(命名空间,{'zh':中文,'en':英文}),'ui-cordis: dictionaries')#词典
    远端=上下文.remote.dynamicCordisRunner#远端运行器

    def 停止(会话标识,插件标识):#停止
        """经远端 stopFromPanel。"""
        答=远端.stopFromPanel(会话标识,插件标识)#远端
        if hasattr(答,'then'):#承诺——宿主解
            return 答#原样
        if not 取字段(答,'ok'):#载体失败
            错=取字段(答,'error')#错
            return {'ok':False,'message':f"{取字段(错,'code')}: {取字段(错,'message')}"}#失败
        值=取字段(答,'value')#业务
        if 取字段(值,'ok') or 取字段(值,'reason')=='not-running':#成功
            return {'ok':True}#成
        return {'ok':False,'message':取字段(值,'message')}#败

    def 移除(会话标识,插件标识):#移除
        """经远端 undefineFromPanel。"""
        答=远端.undefineFromPanel(会话标识,插件标识)#远端
        if hasattr(答,'then'):#承诺
            return 答#原样
        if not 取字段(答,'ok'):#载体失败
            错=取字段(答,'error')#错
            return {'ok':False,'message':f"{取字段(错,'code')}: {取字段(错,'message')}"}#失败
        值=取字段(答,'value')#业务
        return {'ok':True} if 取字段(值,'ok') else {'ok':False,'message':取字段(值,'message')}#结果

    def 拉清单():#拉清单
        """经远端 inventory。"""
        答=远端.inventory()#远端
        if hasattr(答,'then'):#承诺
            return 答#原样
        if not 取字段(答,'ok'):#失败
            错=取字段(答,'error')#错
            raise Exception(f"{取字段(错,'code')}: {取字段(错,'message')}")#抛
        return 取字段(答,'value')#行

    端口={'stop':停止,'remove':移除,'inventory':拉清单}#RPC 端口
    清单=创建清单源(端口,lambda 错:print('[ui-cordis] reading the Cordis inventory failed:',错))#清单源
    运行器=上下文.dynamicCordisRunner#页本地运行器
    已加载={'getSnapshot':lambda:运行器.getSnapshot(),'subscribe':lambda fn:运行器.subscribe(fn)}#已加载面
    运行卡=运行卡片注册表()#按会话分仓

    def 对账():#清单变化对账
        """已读过才对账。"""
        快=清单['getSnapshot']()#快照
        if 快.get('read'):#已读
            运行器.reconcileApprovals(快['rows'])#对账

    上下文.effect(lambda:清单['subscribe'](对账),'ui-cordis: reconcile pending approvals')#对账
    上下文.remote.$on('cordis/dynamic-package',lambda *_a,**_k:清单['refresh']())#包上线
    上下文.remote.$on('cordis/dynamic-retract',lambda *_a,**_k:清单['refresh']())#撤回

    def 新运行请求(请求,*_a,**_k):#本页还没有该行则重读
        """对齐上游：仅缺行时 refresh。"""
        插件=取字段(请求,'pluginId')#插件
        行们=清单['getSnapshot']()['rows']#当前行
        if not any(取字段(r,'pluginId')==插件 for r in 行们):#本页没有
            清单['refresh']()#重读

    上下文.remote.$on('cordis/request-run',新运行请求)#新请求
    上下文.remote.$on('cordis/request-run-resolved',lambda *_a,**_k:清单['refresh']())#落定

    def 重连():#连接重置
        """丢掉旧行并重读。"""
        清单['reset']()#重置
        清单['refresh']()#重读

    上下文.on('connection/reset',重连)#重连

    def 面板停止(会话,插件):#停止并刷新
        """经端口停止后刷新清单。"""
        结果=端口['stop'](会话,插件)#停止
        清单['refresh']()#刷新
        return 结果#结果

    def 面板移除(会话,插件):#移除并刷新
        """成功则 retire。"""
        结果=端口['remove'](会话,插件)#移除
        if 取字段(结果,'ok'):#成功
            清单['retire'](插件)#退役
        清单['refresh']()#刷新
        return 结果#结果

    def 面板注入():#面板注入面
        """钩子与动作。"""
        return {#注入
            'hooks':{#钩
                'inventory':清单,#清单
                'activeRuns':运行器.activeRuns,#活动
                'runErrors':运行器.lastRunError,#失败
                'loaded':已加载,#已加载
                'renderFailures':运行器.renderFailures,#渲染失败
            },#钩结束
            'onApprove':lambda 请求,批后续:运行器.approve(请求,批后续),#批准
            'onDecline':lambda 请求:运行器.decline(请求),#拒绝
            'onRun':lambda 请求:运行器.startUserRun(请求),#运行
            'onStop':面板停止,#停止
            'onRemove':面板移除,#移除
            'onRefresh':lambda:清单['refresh'](),#刷新
        }#结束

    上下文.slots.inject('sidebar.footer.action',lambda:上下文.slots.register({#面板
        'name':'sidebar.footer.action','id':'cordis-panel','locale':命名空间,#选项
        'inject':面板注入,#注入
    },面板))#组件

    def 定义卡面():#定义卡片共用面
        """hooks: inventory + loaded。"""
        return {'hooks':{'inventory':清单,'loaded':已加载}}#面

    上下文.slots.inject('tool.call.toolview',lambda:上下文.slots.register({#定义工具视图
        'name':'tool.call.toolview','key':'cordis_define','locale':命名空间,#槽与键
        'inject':定义卡面,#注入面
    },定义行))#定义行

    def 运行卡面(会话标识):#按会话注入
        """hooks + onObserveRunCard。"""
        仓=运行卡.取会话(会话标识)#该会话仓
        return {#运行卡片面
            'hooks':{'inventory':清单,'loaded':已加载,'runCards':仓,'activeRuns':运行器.activeRuns},#钩
            'onObserveRunCard':lambda 指针:仓['observe'](指针),#发布指针
        }#面

    上下文.slots.inject('tool.call.toolview',lambda:上下文.slots.register({#运行工具视图
        'name':'tool.call.toolview','key':'cordis_run','locale':命名空间,#槽与键
        'children':{'tool.view.cordis':{'kind':'keyed','scope':'session'}},#业务视图子槽
        'inject':运行卡面,#按会话注入
    },运行行))#运行行

    def 动作行们():#停止与移除共用动作行
        """生成器：cordis_stop / cordis_undefine。"""
        yield 上下文.slots.register({#停止
            'name':'tool.call.toolview','key':'cordis_stop','locale':命名空间,#槽与键
        },动作行)#动作行
        yield 上下文.slots.register({#移除
            'name':'tool.call.toolview','key':'cordis_undefine','locale':命名空间,#槽与键
        },动作行)#动作行

    上下文.slots.inject('tool.call.toolview',动作行们)#动作行

    def 本会话行(会话标识,查询):#过滤行
        """本会话且 id 含查询。"""
        return [r for r in 清单['getSnapshot']()['rows'] if 取字段(r,'agentId')==会话标识 and 查询 in str(取字段(r,'pluginId'))]#过滤

    def 候选用包(行):#候选用包
        """优先待切换、当前、最后定义。"""
        包标识=取字段(行,'nextPackageId') or 取字段(行,'currentPackageId')#优先
        if 包标识 is None:#无
            表=取字段(行,'packages') or []#表
            if len(表)==0:#空
                return None#无
            包标识=取字段(表[-1],'packageId')#末
        return 取包(行,包标识)#包

    def 候选(会话,选项):#候选列表
        """映射候选项。"""
        结果=[]#列表
        for r in 本会话行(取字段(会话,'sessionId'),取字段(选项,'query','')):#过滤
            项={'name':str(取字段(r,'pluginId'))}#名
            包=候选用包(r)#包
            if 包 is not None:#有
                项['description']=取字段(包,'purpose')#用途
            结果.append(项)#加
        return 结果#列表

    源={#@pluginId 源
        'trigger':'@','name':'cordis','order':1,#元
        'candidates':候选,#候选
        'warm':lambda *_a,**_k:清单['refresh'](),#预热
        'lexicon':lambda 会话:[str(取字段(r,'pluginId')) for r in 本会话行(取字段(会话,'sessionId'),'')],#词表
        'subscribeLexicon':lambda _会话,听:清单['subscribe'](听),#订阅
        'onPick':lambda 载荷:{'text':'@'+取字段(取字段(载荷,'candidate'),'name')+' '},#选定
    }#源结束
    触发=上下文.get('inputTriggers')#触发服务
    上下文.effect(lambda:触发.registerSource(源),'ui-cordis: @pluginId source')#登记
    清单['refresh']()#启动读一次
