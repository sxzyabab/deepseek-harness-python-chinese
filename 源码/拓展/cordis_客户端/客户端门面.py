"""浏览器半运行面：门面契约、装配接线与失败教学。

对齐上游 `cordis-client-runner/src/client/index.ts`。公开面仅中文名。
硬缺口（保留不通过，勿假实现）：evaluateClientHalf 的 new Function、React 闭包符号、
document 真插入样式、Loader/ModuleLoader 挂载执行体。
本模块落盘门面形状、失败文案与 apply 装配接线（定时器/巡检/编排/事件/拆除）。
"""
from .定时器 import 安装客户端定时器#定时器
from .巡检注册表 import 客户端巡检注册表,提供客户端巡检#巡检
from .提供方 import 客户端巡检提供方们#内置提供方
from .编排器 import 运行编排器#编排
from .运行时 import 包运行器记账#现场记账
from .守卫 import 动态上下文门面#再导出（对齐 upstream export）

__all__=[#公开面
    '说明','注入','插件名','调用失败文本','调用错误','线路失败文本','活动阶段','失败原因','加载失败阶段',
    '门面动词','装配客户端运行面','应用','动态上下文门面',
]#结束

说明=('求值/加载/守卫 Proxy 需浏览器 Function、React、DOM、cordis Loader；'
      'Python 半承载门面契约、教学文案、装配接线与编排/巡检状态机。'
      '硬缺口：new Function / React DOM / document 真插入 — 不冒充。')#说明

插件名='cordis-client-runner'#Cordis 插件名

注入=['loader','modules','slots','remote','remote.dynamicCordisRunner']#硬依赖

活动阶段=('awaiting-approval','orchestrating')#活动阶段

失败原因=('host-half-failed','client-half-failed')#失败半

加载失败阶段=('evaluate','module-import','activate')#加载阶段

门面动词=(#CordisRunnerFace 动词
    'activeRuns','lastRunError','renderFailures',
    'reconcileApprovals','approve','decline','startUserRun',
    'subscribe','getSnapshot','isLoaded',
)#结束

def 调用失败文本(插件标识,方法,结果):#基础设施路由失败教学
    """对齐 invokeFailure；结果须含 code。"""
    处=f'host.call("{方法}") on {插件标识}'#调用点
    码=结果.get('code') if isinstance(结果,dict) else None#码
    if 码=='plugin-not-running':#没在跑
        return f'{处} found no active Host half — the Plugin is stopped or was removed.'#无宿主半
    if 码=='stale-run':#过期
        return f'{处} belongs to an activation that has already been replaced.'#已替换
    if 码=='method-not-found':#未登记
        return f'{处} is not registered: the host half must declare it with harness.handle("{方法}", fn).'#未声明
    消息=结果.get('message') if isinstance(结果,dict) else 结果#消息
    return f'{处} failed inside the host handler: {消息}'#处理内失败

def 调用错误(插件标识,方法,结果):#保留宿主栈并加客户端调用点
    """对齐 invokeError；结果可含 stack。"""
    错误=Exception(调用失败文本(插件标识,方法,结果))#教学消息
    栈=结果.get('stack') if isinstance(结果,dict) else None#宿主栈
    if isinstance(栈,str):#有
        错误.stack=f'{getattr(错误,"stack",None) or 错误}\nHost stack:\n{栈}'#拼
    return 错误#带栈

def 线路失败文本(插件标识,方法,错误):#编解码/传输失败教学
    """对齐 wireFailure。"""
    消息=str(错误)#文本
    if isinstance(错误,BaseException):#异常
        消息=str(错误)#消息
    return (
        f'host.call("{方法}") on {插件标识} did not complete: {消息}\n'
        'Both directions carry JSON only: pass plain JSON data as the argument — or omit it, and the handler receives '
        f'null — and answer from harness.handle("{方法}", fn) with JSON (`return null` when there is nothing to report).'
    )#结束

def 装配客户端运行面(上下文):#对齐 apply 装配
    """安装定时器、巡检、编排与门面；事件订阅挂 Remote。返回门面字典。"""
    安装客户端定时器(上下文)#定时器
    远端=getattr(getattr(上下文,'remote',None),'dynamicCordisRunner',None)#远端命名空间

    def 同步清单(清单们):#syncInspectManifest
        """推给宿主。"""
        if 远端 is None:#无
            return#停
        答=远端.syncInspectManifest(清单们)#推
        if isinstance(答,dict) and not 答.get('ok'):#失败
            错=答.get('error') or {}#错
            raise Exception(f"{错.get('code')}: {错.get('message')}")#抛

    def 落定查询(会话,请求标识,决议):#resolveInspectQuery
        """推决议。"""
        if 远端 is None:#无
            return#停
        答=远端.resolveInspectQuery(会话,请求标识,决议)#推
        if isinstance(答,dict) and not 答.get('ok'):#失败
            错=答.get('error') or {}#错
            raise Exception(f"{错.get('code')}: {错.get('message')}")#抛

    巡检=客户端巡检注册表({'sync':同步清单,'resolve':落定查询})#注册表
    提供客户端巡检(上下文,巡检)#挂服务
    for 提供方 in 客户端巡检提供方们(上下文):#内置
        清单=提供方.get('manifest') or {}#清单
        if hasattr(上下文,'effect'):#有 effect
            上下文.effect((lambda 登=提供方:巡检.register(登)),f"cordis-client-runner: inspect {清单.get('id')}")#登记
        else:#无
            巡检.register(提供方)#直接
    if hasattr(上下文,'on'):#重连后重发清单（对齐 upstream 早挂）
        上下文.on('connection/reset',巡检.publish)#重发

    def 调用宿主(插件标识,运行标识,方法,参数):#runner.invoke
        """host.call 路由；载体/路由失败折教学。"""
        if 远端 is None:#无远端
            raise Exception(线路失败文本(插件标识,方法,'remote.dynamicCordisRunner missing'))#抛
        try:#远程
            答=远端.invoke(插件标识,运行标识,方法,参数)#调
        except Exception as 错:#线路
            raise Exception(线路失败文本(插件标识,方法,错))#教学
        if isinstance(答,dict) and not 答.get('ok'):#载体失败
            错=答.get('error') or {}#错
            raise Exception(线路失败文本(插件标识,方法,f"{错.get('code')}: {错.get('message')}"))#抛
        结果=答.get('value') if isinstance(答,dict) else 答#命名空间结果
        if isinstance(结果,dict) and 结果.get('ok'):#成功
            return 结果.get('value')#值
        if isinstance(结果,dict) and 结果.get('ok') is False:#路由拒绝
            raise 调用错误(插件标识,方法,结果)#带栈
        return 结果#其它

    def 报告渲染失败(会话,插件标识,运行标识,失败):#即发即忘
        """渲染崩溃报告。"""
        if 远端 is None:#无
            return#停
        try:#推
            答=远端.reportRenderFailure(会话,插件标识,运行标识,失败)#远程
            if isinstance(答,dict) and not 答.get('ok'):#载体
                print('[cordis-client-runner] reporting a render failure of',插件标识,'failed:',答.get('error'))#日志
        except Exception as 错:#传输
            print('[cordis-client-runner] reporting a render failure of',插件标识,'failed:',错)#日志

    def 报告守卫失败(会话,插件标识,运行标识,失败):#即发即忘
        """守卫拒绝报告。"""
        if 远端 is None:#无
            return#停
        try:#推
            答=远端.reportClientGuardFailure(会话,插件标识,运行标识,失败)#远程
            if isinstance(答,dict) and not 答.get('ok'):#载体
                print('[cordis-client-runner] reporting a guard failure of',插件标识,'failed:',答.get('error'))#日志
        except Exception as 错:#传输
            print('[cordis-client-runner] reporting a guard failure of',插件标识,'failed:',错)#日志

    def _取服务(名):#ctx.get 安全读
        """有 get 则取。"""
        return 上下文.get(名) if hasattr(上下文,'get') else None#服务

    槽服务=_取服务('slots')#槽位
    记账=包运行器记账({#对齐 DynamicCordisRunnerEnv（mount 仍欠 Loader 硬缺口）
        'ctx':上下文,#根上下文
        'loader':getattr(上下文,'loader',None),#loader
        'modules':_取服务('modules'),#模块表
        'slots':槽服务,#槽位
        'invoke':调用宿主,#host.call
        'reportRenderFailure':报告渲染失败,#渲染
        'reportGuardFailure':报告守卫失败,#守卫
        # mount 故意不给：勿用硬缺口挂载冒充 Function/Loader
    })#记账

    if 槽服务 is not None and hasattr(槽服务,'onEntryError') and hasattr(上下文,'effect'):#入口崩溃监督
        上下文.effect(lambda:槽服务.onEntryError(记账.处理入口崩溃),'cordis-client-runner: slot entry errors')#随 Fiber 拆除

    def 跑宿主半(会话,插件标识,包标识,模式,请求标识,批后续):#runHostHalf
        """折载体失败为业务失败。"""
        if 远端 is None:#无
            return {'ok':False,'message':'remote.dynamicCordisRunner missing'}#失败
        答=远端.runHostHalf(会话,插件标识,包标识,模式,请求标识,批后续)#远程
        if isinstance(答,dict) and 答.get('ok'):#成功
            return 答.get('value')#值
        错=(答 or {}).get('error') or {}#错
        return {'ok':False,'message':f"{错.get('code')}: {错.get('message')}"}#折

    def 取客户端码(会话,插件标识,运行标识):#getClientCode
        """载体失败则抛。"""
        if 远端 is None:#无
            raise Exception('remote.dynamicCordisRunner missing')#抛
        答=远端.getClientCode(会话,插件标识,运行标识)#远程
        if isinstance(答,dict) and not 答.get('ok'):#失败
            错=答.get('error') or {}#错
            raise Exception(f"{错.get('code')}: {错.get('message')}")#抛
        return 答.get('value') if isinstance(答,dict) else 答#源码

    def 落定审批(请求标识,决议):#resolveRequestRun
        """载体失败则抛。"""
        if 远端 is None:#无
            raise Exception('remote.dynamicCordisRunner missing')#抛
        答=远端.resolveRequestRun(请求标识,决议)#远程
        if isinstance(答,dict) and not 答.get('ok'):#失败
            错=答.get('error') or {}#错
            raise Exception(f"{错.get('code')}: {错.get('message')}")#抛
        return 答.get('value') if isinstance(答,dict) else 答#应答

    def 落定用户跑(会话,插件标识,决议):#settleUserRun
        """载体失败则抛。"""
        if 远端 is None:#无
            raise Exception('remote.dynamicCordisRunner missing')#抛
        答=远端.settleUserRun(会话,插件标识,决议)#远程
        if isinstance(答,dict) and not 答.get('ok'):#失败
            错=答.get('error') or {}#错
            raise Exception(f"{错.get('code')}: {错.get('message')}")#抛
        return 答.get('value') if isinstance(答,dict) else 答#应答

    编排=运行编排器({#对齐 CordisRunOrchestrator：runner + host（决议走 host.resolveRequestRun）
        'runner':记账,#页本地加载器
        'host':{#折好的宿主操作
            'runHostHalf':跑宿主半,#宿主半
            'getClientCode':取客户端码,#取码
            'resolveRequestRun':落定审批,#审批
            'settleUserRun':落定用户跑,#用户
        },#host
        # drive 故意不挂假 Loader：有 Remote 时仍欠 evaluate/mount 硬缺口
    })#编排

    门面={#CordisRunnerFace
        'activeRuns':编排.activeRuns,#活动
        'lastRunError':编排.lastRunError,#失败
        'renderFailures':记账.renderFailures,#渲染失败
        'reconcileApprovals':编排.reconcileApprovals,#对账
        'approve':编排.approve,#批准
        'decline':编排.decline,#拒绝
        'startUserRun':编排.startUserRun,#用户启动
        'subscribe':记账.subscribe,#订阅
        'getSnapshot':记账.getSnapshot,#快照
        'isLoaded':记账.isLoaded,#是否已加载
    }#结束
    if hasattr(上下文,'provide'):#有
        上下文.provide('dynamicCordisRunner',门面)#提供

    if hasattr(上下文,'effect'):#拆除路径：对齐 runner.dispose
        上下文.effect(lambda:(lambda:记账.dispose()),'cordis-client-runner: dynamic package runner')#卸载

    def 巡检查询(请求):#inspect-query：失败只记日志
        """对齐 void inspect.query.catch。"""
        try:#执行
            return 巡检.query(请求)#查询
        except Exception as 错:#失败
            提供=请求.get('provider') if isinstance(请求,dict) else None#提供方
            方法=请求.get('method') if isinstance(请求,dict) else None#方法
            print('[cordis-client-runner] inspect query',提供,'.',方法,'failed:',错)#日志

    if hasattr(上下文,'remote') and hasattr(上下文.remote,'$on'):#事件
        上下文.remote.$on('cordis/request-run',编排.open)#打开审批
        上下文.remote.$on('cordis/request-run-resolved',lambda 已落:编排.close(已落.get('requestId') if isinstance(已落,dict) else 已落))#他页落定
        上下文.remote.$on('cordis/dynamic-retract',lambda 收:记账.retract(收.get('pluginId'),收.get('pluginRunId')) if isinstance(收,dict) else None)#收回
        上下文.remote.$on('cordis/inspect-query',巡检查询)#巡检
        上下文.remote.$on('cordis/inspect-query-resolved',lambda 已:巡检.close(已.get('requestId') if isinstance(已,dict) else 已))#关闭
    return 门面#门面

def 应用(上下文=None):#插件体
    """有上下文则装配；无则空（宿主 Loader 行）。"""
    if 上下文 is None:#宿主侧空
        return#无贡献
    return 装配客户端运行面(上下文)#浏览器半装配
