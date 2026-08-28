"""提供方路由的模型请求重试政策，挂在智能体循环的请求恢复扩展点上。

对齐上游 `llm-retry/src/index.ts`。公开面仅中文名。每次调度的重试在其可取消等待之前持久化。
"""
import json,math,random,threading,uuid#标准库
from .. import llm#语言模型失败事实与中止信号
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 路径上节点#配置字段
承诺=cordis.工具.承诺#承诺
已兑现=cordis.工具.已兑现#立刻兑现
是否thenable=cordis.工具.是否thenable#可等待判定
from .品牌 import 重试身份#导入重试链身份
from .类型 import 取,试取#读取字段

__all__=('名称','注入','配置','应用','默认','重试身份')#仅中文公开名

编码=json.dumps#JSON序列化
是否有限=math.isfinite#有限数判断
均匀随机=random.random#含端0到1开区间随机
生成UUID=uuid.uuid4#随机UUID
线程=threading.Thread#工作线程
互斥锁=threading.Lock#互斥锁
完成事件=threading.Event#完成事件
名称='llm-retry'#插件名（字面量不译）
注入=['agents']#依赖 agents 服务
配置=路径上节点({})#空对象模式；本执行器无自有策略配置

def 已中止(信号):#信号是否已中止
    """英文 aborted 或中文 已中止 任一为真则视为已中止。"""
    if 信号 is None:#无信号
        return False#无信号
    if getattr(信号,'aborted',False):#英文旗标
        return True#英文旗标
    if getattr(信号,'已中止',False):#中文旗标
        return True#中文旗标
    return False#未中止

def 中止原因(信号):#取出中止原因
    """取出中止原因。"""
    if 信号 is None:#无信号
        return None#无信号
    原因=getattr(信号,'reason',None)#英文原因
    if 原因 is not None:#有英文原因
        return 原因#英文原因
    return getattr(信号,'原因',None)#中文原因

def 听中止(信号,回调):#登记一次性 abort 回调
    """登记一次性 abort 回调。"""
    if 信号 is None:#无信号
        return#无信号
    if hasattr(信号,'addEventListener'):#Web API
        信号.addEventListener('abort',回调,{'once':True})#Web API
        return#已登记
    if hasattr(信号,'加入监听'):#中文 API
        信号.加入监听('abort',回调,{'once':True})#中文 API

def 摘中止(信号,回调):#去掉 abort 回调
    """去掉 abort 回调。"""
    if 信号 is None:#无信号
        return#无信号
    if hasattr(信号,'removeEventListener'):#Web API
        信号.removeEventListener('abort',回调)#Web API
        return#已摘掉
    if hasattr(信号,'移除监听'):#中文 API
        信号.移除监听('abort',回调)#中文 API

class 中止信号(llm.中止信号):#可监听的取消通道
    """只通知的中止信号，字段名对齐 llm.类型.中止信号。"""
    def __init__(自身,已中止旗=False):#创建一条取消通道
        """初始化未中止状态。"""
        llm.中止信号.__init__(自身,已中止旗)#基类旗标
        自身._监听表=[]#回调表
        自身._锁=互斥锁()#并发锁

    def 触发(自身,原因):#标记中止并通知
        """标记中止并通知。"""
        with 自身._锁:#并发锁
            if 自身.aborted:#只触发一次
                return#只触发一次
            自身.aborted=True#英文旗标
            自身.已中止=True#中文旗标
            自身.reason=原因#英文原因
            自身.原因=原因#中文原因
            回调们=list(自身._监听表)#拷贝
            自身._监听表=[]#清空
        for 回调 in 回调们:#通知
            回调()#通知

    def 加入监听(自身,事件名,回调,选项=None):#登记 abort 回调
        """登记 abort 回调。"""
        if 事件名!='abort':#只支持abort
            return#只支持abort
        立刻=False#是否已中止需立刻通知
        with 自身._锁:#并发锁
            if 自身.aborted:#已中止
                立刻=True#锁外调用
            else:#尚未中止
                自身._监听表.append(回调)#登记
        if 立刻:#已中止需立刻通知
            回调()#立刻通知

    def 移除监听(自身,事件名,回调):#去掉 abort 回调
        """去掉 abort 回调。"""
        if 事件名!='abort':#只支持abort
            return#只支持abort
        with 自身._锁:#并发锁
            自身._监听表=[项 for 项 in 自身._监听表 if 项 is not 回调]#按引用删除

    def addEventListener(自身,事件名,回调,选项=None):#AbortSignal 协议
        """AbortSignal.addEventListener。"""
        自身.加入监听(事件名,回调,选项)#委托中文入口

    def removeEventListener(自身,事件名,回调,选项=None):#AbortSignal 协议
        """AbortSignal.removeEventListener。"""
        自身.移除监听(事件名,回调)#委托中文入口

    @staticmethod#静态方法
    def 任一(信号列表):#最先中止的那路胜出
        """最先中止的那路胜出。"""
        融合=中止控制器()#融合控制器
        for 信号 in 信号列表:#已中止则立刻胜出
            if 已中止(信号):#已中止
                融合.中止(中止原因(信号))#已中止则立刻胜出
                return 融合.信号#已中止的融合信号
        def 绑定(来源):#转发某一路中止
            """转发某一路中止。"""
            def 转发(*位置参数):#把来源原因交给融合控制器
                """把来源原因交给融合控制器。"""
                融合.中止(中止原因(来源))#转发原因
            return 转发#该路回调
        for 信号 in 信号列表:#只听一次
            听中止(信号,绑定(信号))#只听一次
        return 融合.信号#融合信号

class 中止控制器:#发出中止的控制器
    """发出中止的控制器。"""
    def __init__(自身):#创建配套信号
        """创建配套信号。"""
        自身.信号=中止信号()#本控制器的信号
        自身.signal=自身.信号#AbortController 协议

    def 中止(自身,原因=None):#中止配套信号
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次

    def abort(自身,原因=None):#AbortController.abort
        """AbortController.abort。"""
        自身.中止(原因)#委托中文入口

def 校验配置(配置):#拒绝未知键
    """拒绝未知键。"""
    键名们=list(配置)#自有键
    if not 键名们:#没有键则通过
        return#没有键则通过
    键名=键名们[0]#第一个键
    if 键名=='retryPolicy':#政策被错放在这里
        raise Exception('llm-retry: retryPolicy belongs under each provider configuration')#政策属于各提供方配置
    raise Exception('llm-retry: unknown key "'+键名+'"')#未知键

def 解开(结果):#若为承诺则等待，否则原样返回
    """若为承诺则等待，否则原样返回。"""
    if 是否thenable(结果):#对齐 async 函数 return promise 的展平
        return 结果.等待()#等待承诺
    return 结果#同步值

def 全部结算(任务列表):#对齐 Promise.allSettled
    """并发等全部落定，吞掉失败。"""
    def 盯(任务):#等待一路并吞错
        """等待一路并吞错。"""
        try:#等待
            解开(任务)#等待
        except Exception:#排空不抛
            pass#排空不抛
    线程们=[]#工作线程
    for 任务 in 任务列表:#逐路启动
        工作=线程(target=盯,args=(任务,))#工作线程
        工作.start()#启动
        线程们.append(工作)#登记
    for 工作 in 线程们:#等到结束
        工作.join()#等到结束

def 接住下游(下一步):#接住下游恢复，收成决策或错误
    """接住下游恢复，收成决策或错误。"""
    try:#调用下游
        决策=解开(下一步())#得到决策
        return {'类型':'决策','决策':决策}#决策结果
    except Exception as 错误:#下游抛错
        return {'类型':'错误','错误':错误}#错误结果

def 本地延迟(配置,重试序号,随机):#计算本地退避延迟
    """计算本地退避延迟。"""
    指数=min(重试序号-1,1024)#指数上限，避免溢出
    指数退避=min(取(配置,'initialDelayMs')*(2**指数),取(配置,'maxDelayMs'))#指数退避并封顶
    抖动=1-取(配置,'jitterRatio')+2*取(配置,'jitterRatio')*随机()#对称抖动乘数
    return min(指数退避*抖动,取(配置,'maxDelayMs'))#再封顶

def 政策指纹(政策):#政策指纹
    """政策指纹。"""
    模式值=取(政策,'mode')#模式
    if 模式值=='always':#始终模式不含次数与码
        return 编码([模式值,取(政策,'initialDelayMs'),取(政策,'maxDelayMs'),取(政策,'jitterRatio')],separators=(',',':'),ensure_ascii=False)#模式加退避
    可重试码=sorted(list(取(政策,'retryableCodes')))#排序后的可重试码
    return 编码([模式值,取(政策,'maxRetries'),可重试码,取(政策,'initialDelayMs'),取(政策,'maxDelayMs'),取(政策,'jitterRatio')],separators=(',',':'),ensure_ascii=False)#普通指纹

def 可取消等待(延迟毫秒,信号):#可取消等待
    """可取消等待。等到时为 True，中止为 False。"""
    if 已中止(信号):#已中止则不等
        return False#已中止则不等
    完成=完成事件()#等到时或中止
    def 中止时(*位置参数):#中止回调
        """中止回调。"""
        完成.set()#放行等待
    听中止(信号,中止时)#只听一次中止
    完成.wait(延迟毫秒/1000.0)#延迟秒
    摘中止(信号,中止时)#去掉中止监听
    if 已中止(信号):#未等到
        return False#未等到
    return True#等到了

def 从后找(事件们,判断):#对齐 Array.prototype.findLast
    """从后往前找出第一条命中的事件。"""
    下标=len(事件们)-1#最后一个下标
    while 下标>=0:#尚未到头
        事件=事件们[下标]#当前事件
        if 判断(事件):#命中
            return 事件#命中
        下标-=1#继续往前
    return None#没有命中

def 应用(上下文,配置=None,内部=None):#安装提供方路由的普通或无界请求恢复
    """安装提供方路由的普通或无界请求恢复。

    参数：
    上下文:上下文
    配置:dict
    内部:dict
    返回：
    None
    """
    if 配置 is None:#空配置
        配置={}#空配置
    if 内部 is None:#空内部钩子
        内部={}#空内部钩子
    校验配置(配置)#校验空配置
    随机=试取(内部,'random')#可选随机源
    if 随机 is None:#默认随机源
        随机=均匀随机#默认随机源
    生命周期=中止控制器()#插件生命周期中止
    活动=set()#活动恢复
    活动锁=互斥锁()#活动集锁

    def 跟踪(操作):#跟踪活动恢复
        """跟踪活动恢复。在调用方线程跑到等待点，对齐 async 直到 await。"""
        已跟踪=承诺()#本次数承诺
        with 活动锁:#记入活动集
            活动.add(已跟踪)#记入活动集
        try:#兑现决策
            已跟踪.兑现(解开(操作()))#兑现决策
        except Exception as 错误:#拒绝
            已跟踪.拒绝(错误)#拒绝
        finally:#结束后从表里去掉
            with 活动锁:#活动集锁
                活动.discard(已跟踪)#结束后从表里去掉
        return 已跟踪#同一承诺

    def 退避(智能体,回合,步,失败,提供方,政策,政策键,重试序号,链身份,延迟毫秒,信号):#持久化并等待一次重试
        """持久化并等待一次重试。"""
        融合信号=中止信号.任一([信号,生命周期.信号])#调用方与插件生命周期融合
        if 已中止(融合信号):#已中止则不再调度
            return None#已中止则不再调度
        模式值=取(政策,'mode')#政策模式
        if 模式值=='normal':#普通
            事件数据={
                'retryId':链身份,#链身份
                'turn':回合,#回合
                'step':步,#步
                'provider':提供方,#提供方
                'mode':模式值,#普通
                'policyKey':政策键,#指纹
                'retry':重试序号,#序号
                'maxRetries':取(政策,'maxRetries'),#上限
                'delayMs':延迟毫秒,#等待
                'failure':失败,#失败
            }#普通载荷
        else:#始终
            事件数据={
                'retryId':链身份,#链身份
                'turn':回合,#回合
                'step':步,#步
                'provider':提供方,#提供方
                'mode':模式值,#始终
                'policyKey':政策键,#指纹
                'retry':重试序号,#序号
                'delayMs':延迟毫秒,#等待
                'failure':失败,#失败
            }#始终载荷
        智能体.session.append('llm/retry',事件数据)#等待前持久化
        if not 可取消等待(延迟毫秒,融合信号):#等待被取消则停
            return None#等待被取消则停
        智能体.session.append('llm/retry-started',{'retryId':链身份,'turn':回合,'step':步,'retry':重试序号})#等待成功后记过渡
        return {'kind':'retry'}#请求再试

    def 恢复(载荷,下一步):#在请求错误瀑布上恢复
        """在请求错误瀑布上恢复。"""
        智能体=取(载荷,'agent')#智能体
        回合=取(载荷,'turn')#回合
        步=取(载荷,'step')#步
        提供方=取(载荷,'provider')#提供方
        失败=取(载荷,'failure')#失败事实
        政策=试取(载荷,'retryPolicy')#已解析政策
        信号=取(载荷,'signal')#调用方取消
        if 政策 is None:#没有政策则交给下游
            return 解开(下一步())#没有政策则交给下游
        if 取(政策,'mode')=='always':#始终模式先问下游
            if 已中止(信号) or 已中止(生命周期.信号):#已中止则停
                return None#已中止则停
            融合信号=中止信号.任一([信号,生命周期.信号])#融合中止
            下游=接住下游(下一步)#接住下游
            if 已中止(融合信号):#结算后已中止则不再改状态
                return None#结算后已中止则不再改状态
            if 下游['类型']=='错误':#下游抛错
                上下文.logger.warn('llm-retry: provider "'+str(提供方)+'" always policy ignored a downstream recovery failure: %o',下游['错误'])#记下但忽略
            决策=下游.get('决策') if 下游['类型']=='决策' else None#下游决策
            if 决策 is not None and 试取(决策,'kind')=='retry':#下游已决定重试
                return 决策#尊重下游
        else:#普通模式
            可重试码=取(政策,'retryableCodes')#可重试码
            if 试取(失败,'code') not in 可重试码:#码不可重试
                return 解开(下一步())#交给下游
        政策键=政策指纹(政策)#政策指纹
        def 是同政策重试(先前):#同回合同一步同一提供方同一政策的重试
            """同回合同一步同一提供方同一政策的重试。"""
            if 取(先前,'type')!='llm/retry':#不是重试
                return False#不是重试
            先前载荷=取(先前,'data')#先前载荷
            return 取(先前载荷,'turn')==回合 and 取(先前载荷,'step')==步 and 取(先前载荷,'provider')==提供方 and 取(先前载荷,'policyKey')==政策键#同一政策
        先前政策重试=从后找(智能体.session.events,是同政策重试)#同政策上一次调度
        上次序号=0 if 先前政策重试 is None else 取(取(先前政策重试,'data'),'retry')#上次序号
        if 取(政策,'mode')=='normal' and 上次序号>=取(政策,'maxRetries'):#已达上限
            return 解开(下一步())#已达上限
        重试序号=上次序号+1#本次序号
        if 先前政策重试 is None:#新签发链身份
            链身份=重试身份(str(生成UUID()))#新签发链身份
        else:#沿用链身份
            链身份=取(取(先前政策重试,'data'),'retryId')#沿用链身份
        建议等待=试取(失败,'providerRetryAfterMs')#提供方建议等待
        if 建议等待 is not None and not isinstance(建议等待,bool) and isinstance(建议等待,(int,float)) and 是否有限(建议等待) and 建议等待>0:#提供方给了有效等待
            if 建议等待>取(政策,'maxDelayMs'):#超过本地上限
                if 取(政策,'mode')=='normal':#普通模式不再等
                    return 解开(下一步())#普通模式不再等
                延迟毫秒=本地延迟(政策,重试序号,随机)#始终模式改用本地退避
            else:#在上限内
                延迟毫秒=建议等待#用提供方建议
        else:#没有有效建议
            延迟毫秒=本地延迟(政策,重试序号,随机)#本地退避
        return 退避(智能体,回合,步,失败,提供方,政策,政策键,重试序号,链身份,延迟毫秒,信号)#调度等待

    def 监听器(载荷,下一步):#请求错误瀑布监听器
        """请求错误瀑布监听器。"""
        if 已中止(生命周期.信号):#已拆除则短路
            return 已兑现(None)#已拆除则短路
        def 本次恢复():#跑一次恢复
            """跑一次恢复。"""
            return 恢复(载荷,下一步)#本次恢复
        return 跟踪(本次恢复)#跟踪本次恢复

    去掉监听=上下文.on('agent/request-error',监听器)#挂请求错误瀑布

    def 副作用体():#登记拆除
        """登记拆除。"""
        def 拆除():#去掉监听器、中止生命周期并排空活动恢复
            """去掉监听器、中止生命周期并排空活动恢复。"""
            去掉监听()#去掉监听器
            生命周期.中止(Exception('llm-retry plugin disposed'))#中止生命周期
            with 活动锁:#拷贝活动恢复
                进行中=list(活动)#拷贝活动恢复
            全部结算(进行中)#排空活动恢复
        return 拆除#拆除释放器
    上下文.effect(副作用体,'llm-retry: abort and drain active recovery')#effect标签

默认=应用#中文默认导出
