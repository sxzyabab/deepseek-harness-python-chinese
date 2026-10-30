'代码托管提供方注册表。同一变更请求的监视方共用一条轮询'
import threading
import time
from ...依赖.cordis.服务 import 服务
from ...工具.超时 import 定时器延迟上限毫秒
from .键 import 变更请求键
from .调度 import 下次轮询延迟

__all__=['变更请求键','下次轮询延迟','代码托管服务','默认']

默认间隔={
    'activeIntervalMs':30000,
    'idleIntervalMs':120000,
    'maxBackoffMs':600000,
    'fetchTimeoutMs':30000,
}

class 代码托管服务(服务):
    '一个家族同时最多一次抓取，抓取把该家族已到期的变更请求打成一批'
    def __init__(自身,上下文,配置=None):
        '校验间隔后开始轮询。配置缺省项用默认间隔'
        super().__init__(上下文,'forge')
        自身.配置=dict(默认间隔)
        if 配置 is not None:
            自身.配置.update(配置)
        for 键 in 默认间隔:
            值=自身.配置[键]
            if isinstance(值,bool) or not isinstance(值,int) or 值<=0 or 值>定时器延迟上限毫秒:
                raise RuntimeError(f'forge: {键} must be a positive integer no greater than {定时器延迟上限毫秒}')
        if 自身.配置['maxBackoffMs']<自身.配置['activeIntervalMs']:
            raise RuntimeError('forge: maxBackoffMs must be greater than or equal to activeIntervalMs')
        自身.锁=threading.RLock()
        自身.提供方表={}#家族名 → {提供方,停止,在途}
        自身.监视表={}#键 → 监视
        自身.抓取中=set()
        自身.停止=threading.Event()
        自身.定时器=None
        def 装停止():
            '卸下时停轮询'
            def 拆():
                '停定时器。进行中的抓取靠停止信号自行结束'
                自身.停止.set()
                with 自身.锁:
                    定时=自身.定时器
                    自身.定时器=None
                if 定时 is not None:
                    定时.cancel()
            return 拆
        上下文.副作用(装停止)

    def 注册(自身,提供方):
        """登记一个家族的提供方，返回拆除器。
        提供方是 dict，forge 为家族名。同一家族不能登记两次"""
        def 装():
            '占住家族并立刻到期已有监视'
            家族=提供方['forge']
            with 自身.锁:
                if 家族 in 自身.提供方表:
                    raise RuntimeError(f'forge: a provider for "{家族}" is already registered')
                自身.提供方表[家族]={'提供方':提供方,'停止':threading.Event(),'在途':set()}
                现在=自身._现在()
                for 监视 in 自身.监视表.values():
                    if 监视['引用']['repository']['forge']==家族:
                        监视['到期毫秒']=现在
            自身._通知提供方变化(家族)
            自身.安排()
            def 拆():
                '撤回提供方，在途监视收到不可用'
                with 自身.锁:
                    登记=自身.提供方表.pop(家族,None)
                if 登记 is None:
                    return
                登记['停止'].set()
                失败=自身._缺失(家族)
                with 自身.锁:
                    待结算=[监视 for 监视 in 自身.监视表.values() if 监视['引用']['repository']['forge']==家族]
                for 监视 in 待结算:
                    自身._结算(监视,失败,None)
                自身._通知提供方变化(家族)
                自身.安排()
            return 拆
        return 自身.上下文.副作用(装)

    def 从远端找仓库(自身,网址):
        '第一个认领该 Git 远端的提供方返回仓库，否则 None'
        with 自身.锁:
            登记表=list(自身.提供方表.values())
        for 登记 in 登记表:
            仓库=登记['提供方']['repositoryFromRemote'](网址)
            if 仓库 is not None:
                return 仓库
        return None

    def 从网址找变更请求(自身,网址):
        '第一个认领该网页的提供方返回引用，否则 None'
        with 自身.锁:
            登记表=list(自身.提供方表.values())
        for 登记 in 登记表:
            引用=登记['提供方']['changeRequestFromUrl'](网址)
            if 引用 is not None:
                return 引用
        return None

    def 变更请求网址(自身,引用):
        '已登记家族的规范网页'
        return 自身._提供方(引用)['changeRequestUrl'](引用)

    def 按头查找(自身,仓库,分支,信号):
        '打开的、头为该分支的变更请求。排除默认分支与 fork'
        登记=自身._登记(仓库['forge'])
        return 自身._调用(登记,信号,lambda 提供方,操作信号:提供方['findByHead'](仓库,分支,操作信号))

    def 就绪(自身,仓库,信号):
        '当前凭据能否到达该宿主'
        登记=自身._登记(仓库['forge'])
        return 自身._调用(登记,信号,lambda 提供方,操作信号:提供方['readiness'](仓库['host'],操作信号))

    def 标为可评审(自身,引用,信号):
        '草稿改为可评审。若正在监视则马上再抓一次'
        登记=自身._登记(引用['repository']['forge'])
        失败=自身._调用(登记,信号,lambda 提供方,操作信号:提供方['markReady'](引用,操作信号))
        自身.刷新(引用)
        return 失败

    def 合并(自身,引用,请求,信号):
        '头仍是请求里的提交时合并。若正在监视则马上再抓一次'
        登记=自身._登记(引用['repository']['forge'])
        失败=自身._调用(登记,信号,lambda 提供方,操作信号:提供方['merge'](引用,请求,操作信号))
        自身.刷新(引用)
        return 失败

    def 抓取检查(自身,引用,信号):
        '按需读完整检查。提供方没有该方法时返回不可用'
        登记=自身._登记(引用['repository']['forge'])
        操作信号=自身._超时信号(信号,自身.配置['fetchTimeoutMs'])
        def 动作(提供方,当前信号):
            方法=提供方.get('fetchChecks')
            if 方法 is None:
                return {'code':'unavailable','message':'This provider does not support complete check reads'}
            return 方法(引用,当前信号)
        return 自身._调用(登记,操作信号,动作)

    def 差异(自身,引用,信号):
        '宿主算出的统一差异，路径带 a/ 与 b/ 前缀'
        登记=自身._登记(引用['repository']['forge'])
        return 自身._调用(登记,信号,lambda 提供方,操作信号:提供方['diff'](引用,操作信号))

    def 提交评审(自身,引用,请求,信号):
        '发表评论或完成评审。不支持时返回 unsupported'
        登记=自身._登记(引用['repository']['forge'])
        def 动作(提供方,当前信号):
            方法=提供方.get('submitReview')
            if 方法 is None:
                return {'ok':False,'code':'unsupported','message':'This provider does not support review submission'}
            return 方法(引用,请求,当前信号)
        结果=自身._调用(登记,信号,动作)
        自身.刷新(引用)
        return 结果

    def 文件文本(自身,引用,提交,路径,信号):
        '读取该仓库某次提交上的文件文本'
        登记=自身._登记(引用['repository']['forge'])
        return 自身._调用(登记,信号,lambda 提供方,操作信号:提供方['fileText'](引用,提交,路径,操作信号))

    def 文件网址(自身,引用,提交,路径):
        '该文件在该提交上的网页'
        return 自身._提供方(引用)['fileUrl'](引用,提交,路径)

    def 监视(自身,引用,监听):
        '第一个监视方立刻开始轮询。返回停止这一次监视的可调用对象'
        键=变更请求键(引用)
        def 装():
            '加入监听。最后一个离开时停止这条监视'
            with 自身.锁:
                监视=自身.监视表.get(键)
                if 监视 is None:
                    监视={'键':键,'引用':引用,'监听':set(),'最新':None,'到期毫秒':自身._现在(),'失败次数':0}
                    自身.监视表[键]=监视
            自身.安排()
            with 自身.锁:
                监视['监听'].add(监听)
            def 拆():
                '卸掉这个监听。没有监听了就删掉监视'
                with 自身.锁:
                    监视['监听'].discard(监听)
                    if len(监视['监听'])==0 and 自身.监视表.get(键) is 监视:
                        del 自身.监视表[键]
                自身.安排()
            return 拆
        return 自身.上下文.副作用(装)

    def 刷新(自身,引用):
        '正在监视时立刻到期。已经在抓的，这一轮结束后再抓一次'
        键=变更请求键(引用)
        with 自身.锁:
            监视=自身.监视表.get(键)
            if 监视 is None:
                return
            监视['到期毫秒']=自身._现在()
        自身.安排()

    def 最新(自身,引用):
        '最近一次轮询结果。还没有结果或没有监视时为 None'
        with 自身.锁:
            监视=自身.监视表.get(变更请求键(引用))
            if 监视 is None:
                return None
            return 监视['最新']

    def _提供方(自身,引用):
        return 自身._登记(引用['repository']['forge'])['提供方']

    def _登记(自身,家族):
        with 自身.锁:
            登记=自身.提供方表.get(家族)
        if 登记 is None:
            raise RuntimeError('forge: '+自身._缺失(家族)['message'])
        return 登记

    def _缺失(自身,家族):
        return {'code':'unavailable','message':f'no provider is registered for "{家族}"'}

    def _现在(自身):
        return int(time.time()*1000)

    def _若已中止则抛出(自身,信号):
        if 信号 is not None and 信号.is_set():
            raise RuntimeError('The operation was aborted')
        if 自身.停止.is_set():
            raise RuntimeError('forge service disposed')

    def _超时信号(自身,上游,毫秒):
        '上游已中止或到点时，返回的 Event 被设置'
        信号=threading.Event()
        if 上游 is not None and 上游.is_set():
            信号.set()
            return 信号
        if 自身.停止.is_set():
            信号.set()
            return 信号
        def 到时():
            信号.set()
        定时=threading.Timer(毫秒/1000,到时)
        定时.daemon=True
        定时.start()
        if 上游 is not None:
            def 跟上游():
                上游.wait()
                信号.set()
                定时.cancel()
            threading.Thread(target=跟上游,daemon=True).start()
        return 信号

    def _调用(自身,登记,信号,动作):
        '提供方调用期间记在在途集合里。信号已中止则直接抛出'
        自身._若已中止则抛出(信号)
        if 登记['停止'].is_set():
            raise RuntimeError('forge: provider was unregistered')
        登记['在途'].add(threading.get_ident())
        try:
            结果=动作(登记['提供方'],信号)
            自身._若已中止则抛出(信号)
            return 结果
        finally:
            登记['在途'].discard(threading.get_ident())

    def _通知提供方变化(自身,家族):
        if 自身.停止.is_set():
            return
        try:
            自身.上下文.parallel('forge/providers-changed',家族)
        except Exception as 错误:
            自身.上下文.logger.warn('forge: provider change listener failed: '+str(错误))

    def 安排(自身):
        '按最早到期时间重设定时器'
        with 自身.锁:
            if 自身.定时器 is not None:
                自身.定时器.cancel()
                自身.定时器=None
            if 自身.停止.is_set():
                return
            下一=None
            for 监视 in 自身.监视表.values():
                家族=监视['引用']['repository']['forge']
                if 监视['到期毫秒'] is None or 家族 in 自身.抓取中:
                    continue
                if 下一 is None or 监视['到期毫秒']<下一:
                    下一=监视['到期毫秒']
            if 下一 is None:
                return
            等待秒=max(0,下一-自身._现在())/1000
            定时=threading.Timer(等待秒,自身._到点)
            定时.daemon=True
            自身.定时器=定时
            定时.start()

    def _到点(自身):
        with 自身.锁:
            自身.定时器=None
        自身._轮询()

    def _轮询(自身):
        现在=自身._现在()
        到期={}
        with 自身.锁:
            for 监视 in 自身.监视表.values():
                家族=监视['引用']['repository']['forge']
                if 监视['到期毫秒'] is None or 监视['到期毫秒']>现在 or 家族 in 自身.抓取中:
                    continue
                到期.setdefault(家族,[]).append(监视)
            for 家族 in 到期:
                自身.抓取中.add(家族)
                for 监视 in 到期[家族]:
                    监视['到期毫秒']=None
        for 家族,批 in 到期.items():
            threading.Thread(target=自身._抓取,args=(家族,批),daemon=True).start()
        自身.安排()

    def _抓取(自身,家族,批):
        '抓一个家族的一批。失败记成不可用，不把异常抛出定时器'
        失败=None
        结果表=None
        with 自身.锁:
            登记=自身.提供方表.get(家族)
        try:
            if 登记 is None:
                失败=自身._缺失(家族)
            else:
                信号=自身._超时信号(自身.停止,自身.配置['fetchTimeoutMs'])
                引用表=[监视['引用'] for 监视 in 批]
                结果表=自身._调用(登记,信号,lambda 提供方,操作信号:提供方['fetch'](引用表,操作信号))
        except Exception as 错误:
            失败={'code':'unavailable','message':str(错误)}
        finally:
            with 自身.锁:
                自身.抓取中.discard(家族)
        if 自身.停止.is_set():
            return
        with 自身.锁:
            仍是当前=登记 is not None and 自身.提供方表.get(家族) is 登记
        if not 仍是当前:
            自身.安排()
            return
        for 监视 in 批:
            with 自身.锁:
                if 自身.监视表.get(监视['键']) is not 监视:
                    continue
                刷新时刻=监视['到期毫秒']
            if 失败 is not None:
                一项=失败
            elif 结果表 is None or 监视['键'] not in 结果表:
                一项={'code':'unavailable','message':'provider returned no result for '+str(监视['键'])}
            else:
                一项=结果表[监视['键']]
            自身._结算(监视,一项,刷新时刻)
        自身.安排()

    def _结算(自身,监视,结果,刷新时刻):
        '写入最新结果，并按节奏计算下一次到期'
        取到=自身._现在()
        if 'code' in 结果:
            监视['失败次数']=监视['失败次数']+1
            更新={'key':监视['键'],'fetchedAt':取到,'failure':结果}
        else:
            监视['失败次数']=0
            更新={'key':监视['键'],'fetchedAt':取到,'snapshot':结果}
        延迟=下次轮询延迟(结果,监视['失败次数'],自身.配置)
        with 自身.锁:
            监视['最新']=更新
            if 刷新时刻 is not None:
                监视['到期毫秒']=刷新时刻#这一轮开始后又有人要求刷新
            elif 延迟 is None:
                监视['到期毫秒']=None
            else:
                监视['到期毫秒']=取到+延迟
            监听表=list(监视['监听'])
        for 监听 in 监听表:
            try:
                监听(更新)
            except Exception as 错误:
                自身.上下文.logger.warn('forge: change request listener failed: '+str(错误))

默认=代码托管服务
default=代码托管服务
