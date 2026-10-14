from .文案 import 命名空间,中文,英文,文案键
from ....基础设施.通用工具 import 获取内部数据
from .状态 import 取包,可见状态
from .清单 import 创建清单源
from .面板 import 面板,选定包标识,面板可见状态,阻塞优先,样式表 as 面板样式表
from .卡片模型 import 定义卡片,运行卡片,动作卡片,调用状态
from .运行卡片索引 import 工具视图键,创建仓,运行卡片注册表
from .定义行 import 定义行,样式表 as 定义行样式表
from .运行行 import 运行行,样式表 as 运行行样式表
from .动作行 import 动作行
from .槽位 import (
    业务视图槽名,业务视图所有者字段,卡片面钩子,运行卡片面钩子,面板面钩子,面板面动词,业务视图键,
)
from .动态端口 import 动作结果成功,动作结果失败,端口动词,规范化动作结果
from .事件 import (
    审批请求标识,动态包标识,动态插件标识,动态运行标识,动态运行模式,
    清单行字段,动态包公告字段,请求已落定字段,撤回公告字段,运行请求字段,
)

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
]

依赖=['slots','locale','remote','remote.dynamicCordisRunner','dynamicCordisRunner']

from ..异常 import 远端错误,页面失败文案#远端 RPC 载体失败

def 读远端错(答):
    """从 RPC 载体拼失败消息。
    答为 dict
    """
    错=答['error'] if 'error' in 答 else {}
    码=错['code'] if 'code' in 错 else ''
    消息=错['message'] if 'message' in 错 else ''
    if isinstance(消息,(str,BaseException)) and 消息!='':
        消息=页面失败文案(消息)
    return str(码)+': '+str(消息)

def 应用(上下文):
    """登记词典、清单端口、工具行与面板槽。
    行组件为结构树面
    """
    def 挂词典():
        '登记本包词典'
        上下文.locale.register(命名空间,{'zh':中文,'en':英文})
    上下文.副作用(挂词典,'ui-cordis: dictionaries')
    远端=上下文.remote.dynamicCordisRunner

    def 停止(会话标识,插件标识):
        """经远端 stopFromPanel。
        答为 RPC 载体 dict
        """
        答=远端.stopFromPanel(会话标识,插件标识)
        if not 答['ok']:
            return {'ok':False,'message':读远端错(答)}
        值=答['value']
        if 值['ok'] or ('reason' in 值 and 值['reason']=='not-running'):
            return {'ok':True}
        return {'ok':False,'message':值['message']}

    def 移除(会话标识,插件标识):
        """经远端 undefineFromPanel。
        答为 RPC 载体 dict
        """
        答=远端.undefineFromPanel(会话标识,插件标识)
        if not 答['ok']:
            return {'ok':False,'message':读远端错(答)}
        值=答['value']
        return {'ok':True} if 值['ok'] else {'ok':False,'message':值['message']}

    def 拉清单():
        """经远端 inventory。
        答为 RPC 载体 dict
        """
        答=远端.inventory()
        if not 答['ok']:
            raise 远端错误(读远端错(答))
        return 答['value']

    def 清单读失败(错):
        '清单源读失败回调'
        print('[ui-cordis] reading the Cordis inventory failed:',页面失败文案(错))

    端口={'stop':停止,'remove':移除,'inventory':拉清单}
    清单=创建清单源(端口,清单读失败)
    运行器=上下文.dynamicCordisRunner

    def 已加载快照():
        '转发编排器快照'
        return 运行器.getSnapshot()#编排器英文方法名属另一包

    def 已加载订阅(函数):
        '转发编排器订阅'
        return 运行器.subscribe(函数)#编排器英文方法名属另一包

    已加载={'getSnapshot':已加载快照,'subscribe':已加载订阅}

    运行卡=运行卡片注册表()

    def 对账():
        '已读过才对账'
        快=清单['getSnapshot']()
        if 快['read']:
            运行器.reconcileApprovals(快['rows'])

    def 订阅对账():
        '副作用：订阅清单对账'
        return 清单['subscribe'](对账)

    上下文.副作用(订阅对账,'ui-cordis: reconcile pending approvals')

    def 包上线():
        '动态包上线则重读清单'
        清单['refresh']()

    def 包撤回():
        '动态包撤回则重读清单'
        清单['refresh']()

    获取内部数据(上下文.remote,'on')('cordis/dynamic-package',包上线)
    获取内部数据(上下文.remote,'on')('cordis/dynamic-retract',包撤回)

    def 新运行请求(请求):
        """仅缺行时刷新。
        请求为事件 dict
        """
        插件=请求['pluginId']
        行列表=清单['getSnapshot']()['rows']
        已有=False
        for 行 in 行列表:
            if 行['pluginId']==插件:
                已有=True
                break
        if not 已有:
            清单['refresh']()

    def 请求已落定():
        '运行请求落定则重读'
        清单['refresh']()

    获取内部数据(上下文.remote,'on')('cordis/request-run',新运行请求)
    获取内部数据(上下文.remote,'on')('cordis/request-run-resolved',请求已落定)

    def 重连():
        '丢掉旧行并重读'
        清单['reset']()
        清单['refresh']()

    上下文.监听('connection/reset',重连)

    def 面板停止(会话,插件):
        '经端口停止后刷新清单'
        结果=端口['stop'](会话,插件)
        清单['refresh']()
        return 结果

    def 面板移除(会话,插件):
        '成功则 retire'
        结果=端口['remove'](会话,插件)
        if 结果['ok']:
            清单['retire'](插件)
        清单['refresh']()
        return 结果

    def 面板批准(请求,批后续):
        '转发编排器批准'
        return 运行器.approve(请求,批后续)

    def 面板拒绝(请求):
        '转发编排器拒绝'
        return 运行器.decline(请求)

    def 面板运行(请求):
        '转发编排器用户运行'
        return 运行器.startUserRun(请求)

    def 面板刷新():
        '重读清单'
        清单['refresh']()

    def 面板注入():
        '钩子与动作'
        return {
            'hooks':{
                'inventory':清单,
                'activeRuns':运行器.activeRuns,
                'runErrors':运行器.lastRunError,
                'loaded':已加载,
                'renderFailures':运行器.renderFailures,
            },
            'onApprove':面板批准,
            'onDecline':面板拒绝,
            'onRun':面板运行,
            'onStop':面板停止,
            'onRemove':面板移除,
            'onRefresh':面板刷新,
        }

    def 登记面板():
        '登记侧栏面板槽'
        return 上下文.slots.register({
            'name':'sidebar.footer.action','id':'cordis-panel','locale':命名空间,
            'inject':面板注入,
        },面板)

    上下文.slots.inject('sidebar.footer.action',登记面板)

    def 定义卡面():
        'hooks: inventory + loaded'
        return {'hooks':{'inventory':清单,'loaded':已加载}}

    def 登记定义行():
        '登记定义工具视图'
        return 上下文.slots.register({
            'name':'tool.call.toolview','key':'cordis_define','locale':命名空间,
            'inject':定义卡面,
        },定义行)

    上下文.slots.inject('tool.call.toolview',登记定义行)

    def 观察运行卡(仓):
        '闭包：把指针交给该会话仓'
        def 观察(指针):
            '发布运行卡片指针'
            return 仓['observe'](指针)
        return 观察

    def 运行卡面(会话标识):#运行卡片面
        'hooks + onObserveRunCard'
        仓=运行卡.取会话(会话标识)
        return {
            'hooks':{'inventory':清单,'loaded':已加载,'runCards':仓,'activeRuns':运行器.activeRuns},
            'onObserveRunCard':观察运行卡(仓),
        }

    def 登记运行行():#运行工具视图
        '登记运行工具视图'
        return 上下文.slots.register({
            'name':'tool.call.toolview','key':'cordis_run','locale':命名空间,
            'children':{'tool.view.cordis':{'kind':'keyed','scope':'session'}},
            'inject':运行卡面,
        },运行行)

    上下文.slots.inject('tool.call.toolview',登记运行行)

    def 登记动作行():
        '生成器：cordis_stop / cordis_undefine'
        yield 上下文.slots.register({
            'name':'tool.call.toolview','key':'cordis_stop','locale':命名空间,
        },动作行)
        yield 上下文.slots.register({
            'name':'tool.call.toolview','key':'cordis_undefine','locale':命名空间,
        },动作行)

    上下文.slots.inject('tool.call.toolview',登记动作行)
    清单['refresh']()
