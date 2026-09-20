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
    '依赖','应用','命名空间','中文','英文','文案键',
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

依赖=['slots','locale','remote','remote.dynamicCordisRunner','dynamicCordisRunner']

class 远端错误(Exception):
    """远端 RPC 载体失败。"""
    pass#消息在构造时传入

def 读远端错(答):
    """从 RPC 载体拼失败消息。答为 dict。"""
    错=答['error'] if 'error' in 答 else {}#错
    码=错['code'] if 'code' in 错 else ''#码
    消息=错['message'] if 'message' in 错 else ''#消息
    return str(码)+': '+str(消息)#拼

def 应用(上下文):
    """登记词典、清单端口、工具行与面板槽。行组件为结构树面。"""
    def 挂词典():
        """登记本包词典。"""
        上下文.locale.register(命名空间,{'zh':中文,'en':英文})#词典
    上下文.副作用(挂词典,'ui-cordis: dictionaries')#词典
    远端=上下文.remote.dynamicCordisRunner#远端运行器

    def 停止(会话标识,插件标识):
        """经远端 stopFromPanel。答为 RPC 载体 dict。"""
        答=远端.stopFromPanel(会话标识,插件标识)#远端
        if not 答['ok']:#载体失败
            return {'ok':False,'message':读远端错(答)}#失败
        值=答['value']#业务
        if 值['ok'] or ('reason' in 值 and 值['reason']=='not-running'):#成功或幂等未跑
            return {'ok':True}#成
        return {'ok':False,'message':值['message']}#败

    def 移除(会话标识,插件标识):
        """经远端 undefineFromPanel。答为 RPC 载体 dict。"""
        答=远端.undefineFromPanel(会话标识,插件标识)#远端
        if not 答['ok']:#载体失败
            return {'ok':False,'message':读远端错(答)}#失败
        值=答['value']#业务
        return {'ok':True} if 值['ok'] else {'ok':False,'message':值['message']}#结果

    def 拉清单():
        """经远端 inventory。答为 RPC 载体 dict。"""
        答=远端.inventory()#远端
        if not 答['ok']:#失败
            raise 远端错误(读远端错(答))#抛
        return 答['value']#行

    def 清单读失败(错):
        """清单源读失败回调。"""
        print('[ui-cordis] reading the Cordis inventory failed:',错)#打印

    端口={'stop':停止,'remove':移除,'inventory':拉清单}#RPC 端口
    清单=创建清单源(端口,清单读失败)#清单源
    运行器=上下文.dynamicCordisRunner#页本地运行器

    def 已加载快照():
        """转发编排器快照。"""
        return 运行器.getSnapshot()#编排器英文方法名属另一包

    def 已加载订阅(函数):
        """转发编排器订阅。"""
        return 运行器.subscribe(函数)#编排器英文方法名属另一包

    已加载={'getSnapshot':已加载快照,'subscribe':已加载订阅}#清单对象 API 键
    运行卡=运行卡片注册表()#按会话分仓

    def 对账():
        """已读过才对账。"""
        快=清单['getSnapshot']()#快照
        if 快['read']:#已读
            运行器.reconcileApprovals(快['rows'])#对账

    def 订阅对账():
        """副作用：订阅清单对账。"""
        return 清单['subscribe'](对账)#订阅

    上下文.副作用(订阅对账,'ui-cordis: reconcile pending approvals')#对账

    def 包上线():
        """动态包上线则重读清单。"""
        清单['refresh']()#重读

    def 包撤回():
        """动态包撤回则重读清单。"""
        清单['refresh']()#重读

    上下文.remote.$on('cordis/dynamic-package',包上线)#包上线
    上下文.remote.$on('cordis/dynamic-retract',包撤回)#撤回

    def 新运行请求(请求):
        """仅缺行时刷新。请求为事件 dict。"""
        插件=请求['pluginId']#插件
        行列表=清单['getSnapshot']()['rows']#当前行
        已有=False#本页是否已有该插件
        for 行 in 行列表:#扫描
            if 行['pluginId']==插件:#命中
                已有=True#有
                break#停
        if not 已有:#本页没有
            清单['refresh']()#重读

    def 请求已落定():
        """运行请求落定则重读。"""
        清单['refresh']()#重读

    上下文.remote.$on('cordis/request-run',新运行请求)#新请求
    上下文.remote.$on('cordis/request-run-resolved',请求已落定)#落定

    def 重连():
        """丢掉旧行并重读。"""
        清单['reset']()#重置
        清单['refresh']()#重读

    上下文.监听('connection/reset',重连)#重连

    def 面板停止(会话,插件):
        """经端口停止后刷新清单。"""
        结果=端口['stop'](会话,插件)#停止
        清单['refresh']()#刷新
        return 结果#结果

    def 面板移除(会话,插件):
        """成功则 retire。"""
        结果=端口['remove'](会话,插件)#移除
        if 结果['ok']:#成功
            清单['retire'](插件)#退役
        清单['refresh']()#刷新
        return 结果#结果

    def 面板批准(请求,批后续):
        """转发编排器批准。"""
        return 运行器.approve(请求,批后续)#批准

    def 面板拒绝(请求):
        """转发编排器拒绝。"""
        return 运行器.decline(请求)#拒绝

    def 面板运行(请求):
        """转发编排器用户运行。"""
        return 运行器.startUserRun(请求)#运行

    def 面板刷新():
        """重读清单。"""
        清单['refresh']()#刷新

    def 面板注入():
        """钩子与动作。"""
        return {#注入
            'hooks':{#钩
                'inventory':清单,#清单
                'activeRuns':运行器.activeRuns,#活动
                'runErrors':运行器.lastRunError,#失败
                'loaded':已加载,#已加载
                'renderFailures':运行器.renderFailures,#渲染失败
            },#钩结束
            'onApprove':面板批准,#批准
            'onDecline':面板拒绝,#拒绝
            'onRun':面板运行,#运行
            'onStop':面板停止,#停止
            'onRemove':面板移除,#移除
            'onRefresh':面板刷新,#刷新
        }#结束

    def 登记面板():
        """登记侧栏面板槽。"""
        return 上下文.slots.register({#面板
            'name':'sidebar.footer.action','id':'cordis-panel','locale':命名空间,#选项
            'inject':面板注入,#注入
        },面板)#组件

    上下文.slots.inject('sidebar.footer.action',登记面板)#面板

    def 定义卡面():
        """hooks: inventory + loaded。"""
        return {'hooks':{'inventory':清单,'loaded':已加载}}#面

    def 登记定义行():
        """登记定义工具视图。"""
        return 上下文.slots.register({#定义工具视图
            'name':'tool.call.toolview','key':'cordis_define','locale':命名空间,#槽与键
            'inject':定义卡面,#注入面
        },定义行)#定义行

    上下文.slots.inject('tool.call.toolview',登记定义行)#定义行

    def 观察运行卡(仓):
        """闭包：把指针交给该会话仓。"""
        def 观察(指针):
            """发布运行卡片指针。"""
            return 仓['observe'](指针)#观察
        return 观察#回调

    def 运行卡面(会话标识):
        """hooks + onObserveRunCard。"""
        仓=运行卡.取会话(会话标识)#该会话仓
        return {#运行卡片面
            'hooks':{'inventory':清单,'loaded':已加载,'runCards':仓,'activeRuns':运行器.activeRuns},#钩
            'onObserveRunCard':观察运行卡(仓),#发布指针
        }#面

    def 登记运行行():
        """登记运行工具视图。"""
        return 上下文.slots.register({#运行工具视图
            'name':'tool.call.toolview','key':'cordis_run','locale':命名空间,#槽与键
            'children':{'tool.view.cordis':{'kind':'keyed','scope':'session'}},#业务视图子槽
            'inject':运行卡面,#按会话注入
        },运行行)#运行行

    上下文.slots.inject('tool.call.toolview',登记运行行)#运行行

    def 登记动作行():
        """生成器：cordis_stop / cordis_undefine。"""
        yield 上下文.slots.register({#停止
            'name':'tool.call.toolview','key':'cordis_stop','locale':命名空间,#槽与键
        },动作行)#动作行
        yield 上下文.slots.register({#移除
            'name':'tool.call.toolview','key':'cordis_undefine','locale':命名空间,#槽与键
        },动作行)#动作行

    上下文.slots.inject('tool.call.toolview',登记动作行)#动作行
    清单['refresh']()#启动读一次

inject=依赖
apply=应用
