from ....客户端.模块.客户端.通告 import 取握手窗口
import json#服务键进 ctx[键]
import re#上下文属性名
from ..异常 import 错误#调用和线路失败
from . import (
    api名录,#服务与事件目录
    定时器,#定时服务
    巡检注册表,#巡检
    提供方,#内建巡检
    编排器,#运行编排
    槽名录,#槽目录
    运行时,#包运行器
    求值器,#求值
    门面规则,#门面
)
from .api名录 import 服务api,事件api,引用类型闭包#查询用的目录
from .定时器 import 客户端定时器服务#timer 服务
from .巡检注册表 import 客户端巡检注册表#巡检注册表
from .提供方 import (
    登记提供方,读精确,压缩槽树,查看活动槽,客户端内建巡检,
    服务输入,事件输入,服务输出,事件输出,子树输入,子树输出,
)
from .编排器 import 运行编排器#编排器
from .运行时 import 动态包运行器#运行器
from .求值器 import 动态样式,求值客户端半,是否动态插件#求值
from .门面规则 import 动态上下文门面#门面


__all__=[#同目录模块，以及客户端入口的名字
    'api名录','定时器','巡检注册表','提供方','编排器','槽名录','运行时','求值器','门面规则',
    '名称','依赖','应用',
    '运行编排器','客户端巡检注册表','动态包运行器','动态样式','求值客户端半','是否动态插件','动态上下文门面','客户端定时器服务',
]


名称='cordis-client-runner'#插件名
依赖=['加载器','modules','slots','remote','remote.dynamicCordisRunner']#上游 loader 在本仓库叫加载器


def 线路失败文本(插件标识,方法,异常):
    'host.call 在线上没走完时的教学'
    消息=异常.message if isinstance(getattr(异常,'message',None),str) else str(异常)#正文
    return (
        'host.call("'+方法+'") on '+str(插件标识)+' did not complete: '+消息+'\n'
        +'Both directions carry JSON only: pass plain JSON data as the argument — or omit it, and the handler receives '
        +'null — and answer from harness.handle("'+方法+'", fn) with JSON (`return null` when there is nothing to report).'
    )


def 应用(上下文,配置=None):
    '装上定时器、巡检、运行器和编排，并订上宿主转发的事件'
    客户端定时器服务(上下文)#timer
    def 同步清单(提供方列表):
        '把客户端巡检清单推到宿主'
        答=上下文.remote.dynamicCordisRunner.syncInspectManifest(提供方列表)#载体
        if not 答['ok']:#没到宿主
            raise 错误(答['error']['code']+': '+答['error']['message'])
    def 解决查询(会话标识,请求标识,决议):
        '把查询结果交回宿主'
        答=上下文.remote.dynamicCordisRunner.resolveInspectQuery(会话标识,请求标识,决议)#载体
        if not 答['ok']:#没到宿主
            raise 错误(答['error']['code']+': '+答['error']['message'])
    巡检=客户端巡检注册表({'sync':同步清单,'resolve':解决查询})#巡检
    上下文.提供服务('cordisInspect',巡检)#提供
    def 查服务(输入):
        '服务目录。不给键是压缩目录，给了键是一份契约'
        键=读精确(输入,'service')#精确键
        if 键 is None:#目录
            return {'mode':'catalog','services':[{
                'key':服务['key'],
                'description':服务['summary'],
                'methods':[{'signature':方法['signature']} for 方法 in 服务['methods']],
            } for 服务 in 服务api]}
        服务=None#命中
        for 候选 in 服务api:#找键
            if 候选['key']==键:#命中
                服务=候选#这份
                break
        if 服务 is None:#没有
            raise 错误('no catalogued Service named "'+键+'"')
        if re.match(r'^[A-Za-z_$][\w$]*$',服务['key']):#能当属性
            表达式='ctx.'+服务['key']#属性
        else:#要下标
            表达式='ctx['+json.dumps(服务['key'])+']'#下标
        return {#一份服务
            'mode':'service',
            'service':{
                'key':服务['key'],
                'description':服务['description'],
                'access':{
                    'optional':{'expression':'ctx.get('+json.dumps(服务['key'])+')','requiresUndefinedCheck':True},
                    'hardDependency':{'inject':[服务['key']],'expression':表达式},
                },
                'methods':服务['methods'],
            },
            'referencedTypes':引用类型闭包([方法['signature'] for 方法 in 服务['methods']]),
        }
    def 查事件(输入):
        '事件目录。不给名字是压缩目录，给了名字是一份契约'
        名字=读精确(输入,'event')#精确名字
        if 名字 is None:#目录
            return {'mode':'catalog','events':[{
                'name':事件['name'],
                'description':事件['summary'],
                'mode':事件['mode'],
                'signature':事件['signature'],
            } for 事件 in 事件api]}
        事件=None#命中
        for 候选 in 事件api:#找名字
            if 候选['name']==名字:#命中
                事件=候选#这份
                break
        if 事件 is None:#没有
            raise 错误('no catalogued Event named "'+名字+'"')
        return {#一份事件
            'mode':'event',
            'event':{
                'name':事件['name'],
                'description':事件['description'],
                'mode':事件['mode'],
                'signature':事件['signature'],
                'parameters':事件['parameters'],
            },
            'referencedTypes':引用类型闭包([事件['signature']]),
        }
    def 查内建(_输入):
        '动态浏览器半能用的普通符号'
        return {'builtins':[dict(项) for 项 in 客户端内建巡检],'referencedTypes':[]}
    def 查子树(方法,输入):
        '活的槽和工厂树。给了根再附上那一棵的详情'
        if 方法!='listSubTree':#未知方法
            raise 错误('unknown Slots inspect method "'+方法+'"')
        槽=上下文.获取服务('slots',False)#槽服务
        if 槽 is None:#没在跑
            raise 错误('Client Slots service is not running')
        根=None#可选根
        if isinstance(输入,dict) and isinstance(输入.get('root'),str):#给了根
            根=输入['root']#根
        树=槽.snapshot(根)#活拓扑
        选中=树[0] if len(树)>0 else None#第一棵
        结果={'trees':[压缩槽树(节点) for 节点 in 树],'referencedTypes':[]}#压缩树
        if 根 is not None:#请求了根
            结果['requestedRoot']={'name':根,'available':len(树)>0}#在不在
        if 根 is not None and 选中 is not None:#附上详情
            结果['selected']=查看活动槽(选中)#详情
        return 结果
    def 查主题(_输入):
        '当前主题令牌'
        主题=上下文.获取服务('theme',False)#主题
        if 主题 is None:#没在跑
            raise 错误('Client Theme service is not running')
        return {'tokens':主题.导出检视令牌(),'referencedTypes':[]}
    提供方列表=[#内建提供方
        登记提供方('Service','Progressive Client Service discovery: compact capability/signature directory, then one exact coding contract.','listService',查服务,服务输入,服务输出),
        登记提供方('Event','Progressive Client Event discovery: compact listener directory, then one exact event contract.','listEvents',查事件,事件输入,事件输出),
        登记提供方('Builtin','Plain-JavaScript symbols available to a dynamic Client half.','listBuiltins',查内建),
        {
            'manifest':{
                'id':'Slots',
                'description':'Progressive live Slot inspection with explicit Slot and Factory topology nodes.',
                'methods':[{
                    'name':'listSubTree',
                    'description':'Return compact live Slot and Factory trees, plus available detail for one exact root.',
                    'inputSchema':子树输入,
                    'outputSchema':子树输出,
                }],
            },
            'query':查子树,
        },
        登记提供方('Theme','Current theme token names and light/dark override requirements.','listTokens',查主题),
    ]
    for 一项 in 提供方列表:#逐个登记
        def 登记效应(当前=一项):
            '纤程拆除时摘掉这份提供方'
            return 巡检.登记(当前)
        上下文.副作用(登记效应,'cordis-client-runner: inspect '+一项['manifest']['id'])#跟插件走
    def 重连():
        '重连后重发清单'
        巡检.发布()#发布
    上下文.监听('connection/reset',重连)#连接重置
    def 调用(插件标识,运行标识,方法,参数):
        'host.call。线路失败和宿主拒绝教的不是一件事'
        远端=上下文.remote.dynamicCordisRunner#命名空间
        try:#调用
            答=远端.invoke(插件标识,运行标识,方法,参数)#载体
        except Exception as 原因:#没发出去或结果回不来
            raise 错误(线路失败文本(插件标识,方法,原因)) from 原因
        if not 答['ok']:#载体拒绝
            raise 错误(线路失败文本(插件标识,方法,答['error']['code']+': '+答['error']['message']))
        结果=答['value']#宿主半的回答
        if 结果['ok']:#成功
            return 结果['value']
        哪里='host.call("'+方法+'") on '+str(插件标识)#调用点
        if 结果.get('code')=='plugin-not-running':#没有宿主半
            文本=哪里+' found no active Host half — the Plugin is stopped or was removed.'
        elif 结果.get('code')=='stale-run':#激活已被换掉
            文本=哪里+' belongs to an activation that has already been replaced.'
        elif 结果.get('code')=='method-not-found':#没登记
            文本=哪里+' is not registered: the host half must declare it with harness.handle("'+方法+'", fn).'
        else:#处理器里失败
            文本=哪里+' failed inside the host handler: '+str(结果.get('message'))
        异常=错误(文本)#带上调用点
        if 结果.get('stack') is not None:#保留宿主栈
            异常.stack=(getattr(异常,'stack',None) or str(异常))+'\nHost stack:\n'+结果['stack']
        raise 异常
    def 报告渲染失败(会话标识,插件标识,运行标识,失败):
        '渲染失败的报告失败不能再变成一次失败'
        try:#报告
            结果=上下文.remote.dynamicCordisRunner.reportRenderFailure(会话标识,插件标识,运行标识,失败)#载体
            if not 结果['ok']:#载体拒绝
                取握手窗口().console.error(
                    '[cordis-client-runner] reporting a render failure of '+str(插件标识)+' failed:',结果['error'],
                )
        except Exception as 原因:#报告自己失败
            取握手窗口().console.error(
                '[cordis-client-runner] reporting a render failure of '+str(插件标识)+' failed:',原因,
            )
    def 报告门面失败(会话标识,插件标识,运行标识,失败):
        '门面拒绝的报告失败不能再变成一次失败'
        try:#报告
            结果=上下文.remote.dynamicCordisRunner.reportClientGuardFailure(会话标识,插件标识,运行标识,失败)#载体
            if not 结果['ok']:#载体拒绝
                取握手窗口().console.error(
                    '[cordis-client-runner] reporting a guard failure of '+str(插件标识)+' failed:',结果['error'],
                )
        except Exception as 原因:#报告自己失败
            取握手窗口().console.error(
                '[cordis-client-runner] reporting a guard failure of '+str(插件标识)+' failed:',原因,
            )
    运行器=动态包运行器({#运行器环境
        'ctx':上下文,
        'loader':上下文.加载器,
        'modules':上下文.获取服务('modules',False),
        'slots':上下文.获取服务('slots',False),
        'invoke':调用,
        'reportRenderFailure':报告渲染失败,
        'reportGuardFailure':报告门面失败,
    })
    def 跑宿主半(会话标识,插件标识,包标识,模式,请求标识,批后续):
        '宿主半。载体失败折进这个动词自己的失败结果'
        答=上下文.remote.dynamicCordisRunner.runHostHalf(会话标识,插件标识,包标识,模式,请求标识,批后续)#载体
        if 答['ok']:#到了宿主
            return 答['value']
        return {'ok':False,'message':答['error']['code']+': '+答['error']['message']}
    def 取客户端码(会话标识,插件标识,运行标识):
        '取这一次激活的浏览器半源码'
        答=上下文.remote.dynamicCordisRunner.getClientCode(会话标识,插件标识,运行标识)#载体
        if not 答['ok']:#没取到
            raise 错误(答['error']['code']+': '+答['error']['message'])
        return 答['value']
    def 解决运行(请求标识,决议):
        '回答模型发起的运行。失败抛出，由回答自己记日志'
        答=上下文.remote.dynamicCordisRunner.resolveRequestRun(请求标识,决议)#载体
        if not 答['ok']:#没答上
            raise 错误(答['error']['code']+': '+答['error']['message'])
        return 答['value']
    def 落定用户运行(会话标识,插件标识,决议):
        '落定用户自己发起的运行'
        答=上下文.remote.dynamicCordisRunner.settleUserRun(会话标识,插件标识,决议)#载体
        if not 答['ok']:#没落定
            raise 错误(答['error']['code']+': '+答['error']['message'])
        return 答['value']
    编排=运行编排器({#编排环境
        'runner':运行器,
        'host':{
            'runHostHalf':跑宿主半,
            'getClientCode':取客户端码,
            'resolveRequestRun':解决运行,
            'settleUserRun':落定用户运行,
        },
    })
    class 运行面:
        '页面运行面。方法名保持上游，已经写好的界面按这些名字调用'
        def __init__(自身):
            '接上编排器和运行器'
            自身.activeRuns=编排.activeRuns#进行中
            自身.lastRunError=编排.lastRunError#最近失败
            自身.renderFailures=运行器.renderFailures#渲染失败
        def reconcileApprovals(自身,行列表):
            '按清单对账审批'
            编排.对账审批(行列表)#对账
        def approve(自身,请求标识,批后续):
            '批准'
            return 编排.批准(请求标识,批后续)
        def decline(自身,请求标识):
            '拒绝'
            return 编排.拒绝(请求标识)
        def startUserRun(自身,请求):
            '用户自己启动'
            return 编排.启动用户运行(请求)
        def subscribe(自身,函数):
            '订阅本页加载变化'
            return 运行器.订阅(函数)
        def getSnapshot(自身):
            '本页当前加载着的行'
            return 运行器.取快照()
        def isLoaded(自身,插件标识):
            '本页有没有这份浏览器半'
            return 运行器.是否已加载(插件标识)
    上下文.提供服务('dynamicCordisRunner',运行面())#提供
    def 拆运行器():
        '插件拆除时卸掉全部动态包'
        def 拆除():
            '卸掉'
            运行器.拆除全部()#卸
        return 拆除
    上下文.副作用(拆运行器,'cordis-client-runner: dynamic package runner')#跟插件走
    开事件=getattr(上下文.remote,'$on')#宿主转发的事件
    def 请求运行(请求):
        '打开一个运行请求'
        编排.打开(请求)#打开
    def 请求已落定(已落定):
        '别的页落定或取消'
        编排.关闭(已落定['requestId'])#关闭
    def 动态撤回(撤回):
        '卸掉这一次激活'
        运行器.收回(撤回['pluginId'],撤回['pluginRunId'])#收回
    def 巡检查询(请求):
        '查询失败只记日志'
        try:#查询
            巡检.查询(请求)#执行
        except Exception as 原因:#失败
            取握手窗口().console.error(
                '[cordis-client-runner] inspect query '+str(请求.get('provider'))+'.'+str(请求.get('method'))+' failed:',原因,
            )
    def 巡检已落定(已落定):
        '别的页已经回答'
        巡检.关闭(已落定['requestId'])#关闭
    开事件('cordis/request-run',请求运行)#请求运行
    开事件('cordis/request-run-resolved',请求已落定)#请求落定
    开事件('cordis/dynamic-retract',动态撤回)#撤回
    开事件('cordis/inspect-query',巡检查询)#巡检查询
    开事件('cordis/inspect-query-resolved',巡检已落定)#查询落定


name=名称#框架槽
inject=依赖#框架槽
apply=应用#插件入口
