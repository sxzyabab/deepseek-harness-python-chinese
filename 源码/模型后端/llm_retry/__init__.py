import json,math,random,threading,uuid#标准库
from concurrent.futures import Future as 原生结果#单次操作结果
from .标识构造 import 重试身份#导入重试链身份

__all__=('名称','注入','配置','应用','重试身份')#仅中文公开名

名称='llm-retry'#插件名
注入=['agents']#依赖 agents 服务
配置={}#空对象模式；本执行器无自有策略配置

class 重试错误(Exception):
    """llm-retry 配置与拆除失败。"""

class 操作任务:
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._原生结果=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._原生结果.done():#尚未结算
            自身._原生结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._原生结果.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._原生结果.set_exception(错误)#原样拒绝
            else:#非异常
                自身._原生结果.set_exception(重试错误(str(错误)))#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._原生结果.result(timeout=超时)#取结果或抛错

class 中止信号:
    """threading.Event 取消通道。"""
    def __init__(自身,事件=None):
        """创建一条取消通道。"""
        自身._事件=事件 if 事件 is not None else threading.Event()#中止信号
        自身._异常=None#中止时抛出的异常

    def 触发(自身,原因=None):
        """标记中止。"""
        if 自身._事件.is_set():#只触发一次
            return#已触发
        if isinstance(原因,BaseException):#已是异常
            自身._异常=原因#承载
        elif 原因 is not None:#非异常
            自身._异常=重试错误(str(原因))#包装
        自身._事件.set()#置位

class 中止控制器:
    """发出中止的控制器。"""
    def __init__(自身):
        """创建配套信号。"""
        自身.信号=中止信号()#本控制器的信号

    def 中止(自身,原因=None):
        """中止配套信号。"""
        自身.信号.触发(原因)#触发一次

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位

def 合成信号(信号列表):
    """最先中止的那路胜出。"""
    融合=中止信号()#融合通道
    for 信号 in 信号列表:#已中止则立刻胜出
        if 信号 is None:#无信号
            continue#跳过
        if 已中止(信号):#已中止
            融合.触发()#立刻胜出
            return 融合#已中止的融合信号
    def 转发中止(源):
        """等一路置位后触发融合。"""
        源._事件.wait()#阻塞
        融合.触发()#转发
    for 信号 in 信号列表:#并行听
        if 信号 is None:#无信号
            continue#跳过
        threading.Thread(target=转发中止,args=(信号,),daemon=True).start()#听一路
    return 融合#融合信号

def 校验配置(配置值):
    """拒绝未知键。配置为 dict。"""
    键名列表=list(配置值)#自有键
    if len(键名列表)==0:#没有键则通过
        return#没有键则通过
    键名=键名列表[0]#第一个键
    if 键名=='retryPolicy':#政策被错放在这里
        raise 重试错误('llm-retry: retryPolicy 应写在各提供方配置下')#政策属于各提供方配置
    raise 重试错误('llm-retry: 未知键 "'+键名+'"')#未知键

def 全部结算(任务列表):
    """等全部操作任务落定，吞掉失败。"""
    for 任务 in 任务列表:#逐路
        try:#等待
            任务.等待()#等待
        except Exception:#排空不抛；全部结算吞任意任务失败
            pass#排空不抛

def 接住下游(下一步):
    """接住下游恢复，收成决策或错误。"""
    try:#调用下游
        决策=下一步()#得到决策
        return {'类型':'决策','决策':决策}#决策结果
    except Exception as 错误:#下游恢复契约未收窄抛出类型
        return {'类型':'错误','错误':错误}#错误结果

def 本地延迟(配置值,重试序号,随机):
    """计算本地退避延迟。配置为 dict。"""
    指数=min(重试序号-1,1024)#指数上限，避免溢出
    指数退避=min(配置值['initialDelayMs']*(2**指数),配置值['maxDelayMs'])#指数退避并封顶
    抖动=1-配置值['jitterRatio']+2*配置值['jitterRatio']*随机()#对称抖动乘数
    return min(指数退避*抖动,配置值['maxDelayMs'])#再封顶

def 政策指纹(政策):
    """政策指纹。政策为 dict。"""
    模式值=政策['mode']#模式
    if 模式值=='always':#始终模式不含次数与码
        return json.dumps([模式值,政策['initialDelayMs'],政策['maxDelayMs'],政策['jitterRatio']],ensure_ascii=False,separators=(',',':'),allow_nan=False)#模式加退避
    可重试码=sorted(list(政策['retryableCodes']))#排序后的可重试码
    return json.dumps([模式值,政策['maxRetries'],可重试码,政策['initialDelayMs'],政策['maxDelayMs'],政策['jitterRatio']],ensure_ascii=False,separators=(',',':'),allow_nan=False)#普通指纹

def 可取消等待(延迟毫秒,信号):
    """可取消等待。等到时为 True，中止为 False。"""
    if 已中止(信号):#已中止则不等
        return False#已中止则不等
    完成=threading.Event()#等到时或中止
    def 等待中止():
        """中止时放行等待。"""
        信号._事件.wait()#阻塞到中止
        完成.set()#放行
    if 信号 is not None:#有信号
        threading.Thread(target=等待中止,daemon=True).start()#听中止
    完成.wait(延迟毫秒/1000.0)#延迟秒
    if 已中止(信号):#未等到
        return False#未等到
    return True#等到了

def 从后找(事件列表,判断):
    """从后往前找出第一条命中的事件。"""
    下标=len(事件列表)-1#最后一个下标
    while 下标>=0:#尚未到头
        事件=事件列表[下标]#当前事件
        if 判断(事件):#命中
            return 事件#命中
        下标-=1#继续往前
    return None#没有命中

def 应用(上下文,配置值=None,内部=None):
    """安装提供方路由的普通或无界请求恢复。配置与内部钩子为 dict。"""
    if 配置值 is None:#空配置
        配置值={}#空配置
    if 内部 is None:#空内部钩子
        内部={}#空内部钩子
    校验配置(配置值)#校验空配置
    随机=内部['random'] if 'random' in 内部 else random.random#可选随机源
    生命周期=中止控制器()#插件生命周期中止
    活动=set()#活动恢复
    活动锁=threading.Lock()#活动集锁

    def 跟踪(操作):
        """跟踪活动恢复。操作同步跑到等待点。"""
        已跟踪=操作任务()#本次跟踪任务
        with 活动锁:#记入活动集
            活动.add(已跟踪)#记入活动集
        try:#兑现决策
            值=操作()#同步恢复
            已跟踪.兑现(值)#兑现
            return 值#决策
        except Exception as 错误:#恢复操作契约未收窄抛出类型
            已跟踪.拒绝(错误)#拒绝
            raise#再抛给瀑布
        finally:#结束后从表里去掉
            with 活动锁:#活动集锁
                活动.discard(已跟踪)#结束后从表里去掉

    def 退避(智能体,回合,步,失败,提供方,政策,政策键,重试序号,链身份,延迟毫秒,信号):
        """持久化并等待一次重试。政策与失败为 dict；智能体为对象。"""
        融合信号=合成信号([信号,生命周期.信号])#调用方与插件生命周期融合
        if 已中止(融合信号):#已中止则不再调度
            return None#已中止则不再调度
        模式值=政策['mode']#政策模式
        if 模式值=='normal':#普通
            事件数据={
                'retryId':链身份,#链身份
                'turn':回合,#回合
                'step':步,#步
                'provider':提供方,#提供方
                'mode':模式值,#普通
                'policyKey':政策键,#指纹
                'retry':重试序号,#序号
                'maxRetries':政策['maxRetries'],#上限
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
        智能体.session.追加('llm/retry',事件数据)#等待前持久化
        if not 可取消等待(延迟毫秒,融合信号):#等待被取消则停
            return None#等待被取消则停
        智能体.session.追加('llm/retry-started',{'retryId':链身份,'turn':回合,'step':步,'retry':重试序号})#等待成功后记过渡
        return {'kind':'retry'}#请求再试

    def 恢复(载荷,下一步):
        """在请求错误瀑布上恢复。载荷为 dict。"""
        智能体=载荷['agent']#智能体
        回合=载荷['turn']#回合
        步=载荷['step']#步
        提供方=载荷['provider']#提供方
        失败=载荷['failure']#失败事实
        政策=载荷['retryPolicy'] if 'retryPolicy' in 载荷 else None#已解析政策
        信号=载荷['signal'] if 'signal' in 载荷 else None#调用方取消
        if 政策 is None:#没有政策则交给下游
            return 下一步()#没有政策则交给下游
        if 政策['mode']=='always':#始终模式先问下游
            if 已中止(信号) or 已中止(生命周期.信号):#已中止则停
                return None#已中止则停
            融合信号=合成信号([信号,生命周期.信号])#融合中止
            下游=接住下游(下一步)#接住下游
            if 已中止(融合信号):#结算后已中止则不再改状态
                return None#结算后已中止则不再改状态
            if 下游['类型']=='错误':#下游抛错
                上下文.日志.警告('llm-retry: provider "'+str(提供方)+'" always policy ignored a downstream recovery failure: %o',下游['错误'])#记下但忽略
            决策=下游['决策'] if 下游['类型']=='决策' else None#下游决策
            if 决策 is not None and 'kind' in 决策 and 决策['kind']=='retry':#下游已决定重试
                return 决策#尊重下游
        else:#普通模式
            可重试码=政策['retryableCodes']#可重试码
            失败码=失败['code'] if 'code' in 失败 else None#失败码
            if 失败码 not in 可重试码:#码不可重试
                return 下一步()#交给下游
        政策键=政策指纹(政策)#政策指纹
        def 是同政策重试(先前):
            """同回合同一步同一提供方同一政策的重试。"""
            if 先前['type']!='llm/retry':#不是重试
                return False#不是重试
            先前载荷=先前['data']#先前载荷
            return 先前载荷['turn']==回合 and 先前载荷['step']==步 and 先前载荷['provider']==提供方 and 先前载荷['policyKey']==政策键#同一政策
        先前政策重试=从后找(智能体.session.events,是同政策重试)#同政策上一次调度
        上次序号=0 if 先前政策重试 is None else 先前政策重试['data']['retry']#上次序号
        if 政策['mode']=='normal' and 上次序号>=政策['maxRetries']:#已达上限
            return 下一步()#已达上限
        重试序号=上次序号+1#本次序号
        if 先前政策重试 is None:#新签发链身份
            链身份=重试身份(str(uuid.uuid4()))#新签发链身份
        else:#沿用链身份
            链身份=先前政策重试['data']['retryId']#沿用链身份
        建议等待=失败['providerRetryAfterMs'] if 'providerRetryAfterMs' in 失败 else None#提供方建议等待
        if 建议等待 is not None and not isinstance(建议等待,bool) and isinstance(建议等待,(int,float)) and math.isfinite(建议等待) and 建议等待>0:#提供方给了有效等待
            if 建议等待>政策['maxDelayMs']:#超过本地上限
                if 政策['mode']=='normal':#普通模式不再等
                    return 下一步()#普通模式不再等
                延迟毫秒=本地延迟(政策,重试序号,随机)#始终模式改用本地退避
            else:#在上限内
                延迟毫秒=建议等待#用提供方建议
        else:#没有有效建议
            延迟毫秒=本地延迟(政策,重试序号,随机)#本地退避
        return 退避(智能体,回合,步,失败,提供方,政策,政策键,重试序号,链身份,延迟毫秒,信号)#调度等待

    def 监听器(载荷,下一步):
        """请求错误瀑布监听器。"""
        if 已中止(生命周期.信号):#已拆除则短路
            return None#已拆除则短路
        def 本次恢复():
            """跑一次恢复。"""
            return 恢复(载荷,下一步)#本次恢复
        return 跟踪(本次恢复)#跟踪本次恢复

    去掉监听=上下文.监听('agent/request-error',监听器)#挂请求错误瀑布

    def 副作用体():
        """登记拆除。"""
        def 拆除():
            """去掉监听器、中止生命周期并排空活动恢复。"""
            去掉监听()#去掉监听器
            生命周期.中止(重试错误('llm-retry 插件已拆除'))#中止生命周期
            with 活动锁:#拷贝活动恢复
                进行中=list(活动)#拷贝活动恢复
            全部结算(进行中)#排空活动恢复
        return 拆除#拆除释放器
    上下文.副作用(副作用体,'llm-retry: abort and drain active recovery')#副作用标签

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=应用#框架槽
