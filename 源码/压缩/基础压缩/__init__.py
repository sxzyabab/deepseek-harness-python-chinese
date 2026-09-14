import weakref#每智能体溢出计数与会话→智能体弱映射
from ...依赖.schemastery import 字符串字段,整数字段,数字字段,布尔字段,列表字段#配置字段
from ..压缩 import 压缩引擎,手动压缩错误#导入压缩引擎与手动失败
from ...模型后端.llm import 上下文窗口溢出码,断言永不#导入上下文溢出码与穷尽断言
from ...工具.超时 import 合成信号#对应 AbortSignal.any
from .配置 import (#导入配置解析
    解析压缩规格,#缩放到 token 预算
    解析配置,#解析服务配置
    解析目标政策,#合并目标政策
    目标压力配置错误,#目标压力配置错误
    基础压缩错误,#本包异常
)#本包配置
from .区间 import (#导入区间事务
    校验无活动压缩,#校验无活动压缩
    压缩表面区间,#跑一次表面压缩事务
    选择可压缩区间,#选择可压缩区间
    已中止,#中止判定
    若已中止则抛出,#中止抛出
)#本包区间
from .摘要器 import 经语言模型摘要#导入默认 LLM 摘要
from .类型 import (#再导出配置词汇
    基础压缩配置字段,#插件顶层配置
    压缩政策配置字段,#政策字段
    模型压缩政策配置字段,#精确目标覆盖
    已解析压缩规格字段说明,#容量缩放后规格
    已解析配置字段说明,#服务级已解析配置
    已解析保留形态说明,#已解析保留形态
    已解析目标政策字段说明,#目标级已解析政策
)#本包类型

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '阈值比例模式','保留比例模式','保留令牌模式','摘要提供方模式','摘要模型模式',
    '最大令牌模式','压缩重试模式','溢出重试模式','模型政策模式',
    '已中止','若已中止则抛出','基础压缩引擎','基础压缩错误',
    '基础压缩配置字段','压缩政策配置字段','模型压缩政策配置字段',
    '已解析压缩规格字段说明','已解析配置字段说明','已解析保留形态说明','已解析目标政策字段说明',
    '解析压缩规格','解析配置','解析目标政策','目标压力配置错误',
    '校验无活动压缩','压缩表面区间','选择可压缩区间','经语言模型摘要',
]#公开面结束

阈值比例模式=数字字段()#阈值比例模式
保留比例模式=数字字段()#保留比例模式
保留令牌模式=整数字段(默认值=0)#绝对保留模式
摘要提供方模式=字符串字段()#摘要提供方模式
摘要模型模式=字符串字段()#摘要模型模式
最大令牌模式=整数字段(默认值=1)#生成上限模式
压缩重试模式=整数字段(默认值=0)#压缩重试模式
溢出重试模式=整数字段(默认值=0)#溢出重试模式

模型政策模式={#精确目标覆盖模式
    'provider':字符串字段(可空=False),#提供方必填
    'model':字符串字段(可空=False),#模型必填
    'thresholdRatio':阈值比例模式,#阈值比例
    'retainRatio':保留比例模式,#保留比例
    'retainTokens':保留令牌模式,#绝对保留
    'summarizationProvider':摘要提供方模式,#摘要提供方
    'summarizationModel':摘要模型模式,#摘要模型
    'maxTokens':最大令牌模式,#生成上限
    'compactionRetries':压缩重试模式,#压缩重试
    'maxOverflowRetries':溢出重试模式,#溢出重试
}#modelPolicy 结束

注入=['llm','tokenMeter','sessions']#依赖 llm、计量与会话协调器
配置={#插件配置模式
    'thresholdRatio':阈值比例模式,#阈值比例
    'retainRatio':保留比例模式,#保留比例
    'retainTokens':保留令牌模式,#绝对保留
    'summarizationProvider':摘要提供方模式,#摘要提供方
    'summarizationModel':摘要模型模式,#摘要模型
    'maxTokens':最大令牌模式,#生成上限
    'compactionRetries':压缩重试模式,#压缩重试
    'maxOverflowRetries':溢出重试模式,#溢出重试
    'modelPolicies':列表字段(模型政策模式),#精确目标表
    'auto':布尔字段(),#是否自动
}#Config 结束

def 已路由目标(会话):
    """返回精确路由或 None。"""
    请求头=会话.请求头()#最近请求头
    配置值=请求头['config'] if 请求头 is not None and 'config' in 请求头 else None#最近请求配置
    if 配置值 is None or len(配置值['provider'] if 'provider' in 配置值 and 配置值['provider'] is not None else '')==0 or len(配置值['model'] if 'model' in 配置值 and 配置值['model'] is not None else '')==0:#没有完整路由
        return None#无法选政策
    return {'provider':配置值['provider'],'model':配置值['model']}#精确目标

def 对话目标(智能体):
    """返回精确路由或 None。"""
    已路由=已路由目标(智能体.session)#优先已路由请求
    if 已路由 is not None:#有则用
        return 已路由#已路由
    选项=智能体.options if 智能体.options is not None else {}#智能体选项
    提供方=选项['provider'] if 'provider' in 选项 else None#选项提供方
    模型=选项['model'] if 'model' in 选项 else None#选项模型
    if 提供方 is None or len(提供方 or '')==0 or 模型 is None or len(模型 or '')==0:#选项也空
        return None#无目标
    return {'provider':提供方,'model':模型}#用智能体选项

class 基础压缩引擎(压缩引擎):
    """依赖很轻的压缩后端，用 ctx.tokenMeter 做压力、保留、被引用源事件与摘要收敛计价。summarize() 是唯一的子类定制钩子。"""

    def __init__(自身,上下文,配置值=None):
        """绑定 compaction 服务，解析并冻结配置；auto 时挂自动监听。"""
        if 配置值 is None:#缺省空配置
            配置值={}#空配置
        super().__init__(上下文)#绑定 compaction 服务
        自身.配置=解析配置(配置值)#解析并冻结配置
        自身.已警告压力配置目标=set()#已警告过的压力配置目标
        自身.溢出重试表=weakref.WeakKeyDictionary()#每智能体溢出恢复次数
        自身.溢出智能体表=weakref.WeakKeyDictionary()#会话→溢出恢复所用智能体
        if 自身.配置['auto']:#自动则挂监听
            自身._登记自动压缩()#挂监听

    def _登记自动压缩(自身):
        """compactIfNeeded 保持动态分发，以便子类覆盖在事件时生效。"""
        上下文=自身.ctx#本插件上下文
        def 记结果(结果,触发):
            """信息级遮蔽节点与估算 token。"""
            区间=结果['shadowedRange']#被遮蔽区间
            上下文.日志.信息(#信息级
                'compaction ('+触发+'): shadowed '+str(len(结果['shadowedSeqs'] if 'shadowedSeqs' in 结果 and 结果['shadowedSeqs'] is not None else []))
                +' surface nodes (seqs '+str(区间['start'])+'-'+str(区间['end'])
                +', ~'+str(结果['shadowedTokenCount'])+' tokens)'#遮蔽节点与估算 token
            )#info 结束
        def 步进前(载荷,下一步):
            """跑压力压缩后委托下一环。"""
            智能体=载荷['agent']#智能体
            信号=载荷['signal'] if 'signal' in 载荷 else None#取消
            if not 已中止(信号):#尚未取消
                try:#尝试压力压缩
                    结果=自身.按需压缩(智能体,'pressure',信号)#按需压缩
                    if 结果 is not None:#有结果则记日志
                        记结果(结果,'step pressure')#记日志
                except Exception as 错误:#压力路径任意失败不得打断回合
                    if isinstance(错误,目标压力配置错误):#目标配置错误
                        if 错误.targetKey in 自身.已警告压力配置目标:#已警告过则静默继续
                            return 下一步()#委托
                        自身.已警告压力配置目标.add(错误.targetKey)#记下已警告
                    消息=错误.message if hasattr(错误,'message') and 错误.message else str(错误)#诊断文案
                    上下文.日志.警告('step compaction failed: '+str(消息)+'; continuing the turn')#警告后继续回合
            return 下一步()#委托下一环
        上下文.监听('agent/pre-step',步进前)#pre-step 结束
        def 状态监听(载荷,*其余):
            """空闲则清溢出计数。"""
            智能体=载荷['agent']#智能体
            状态=载荷['status']#状态
            if 状态=='idle':#空闲
                try:#弱键可能已失效
                    del 自身.溢出重试表[智能体]#清溢出计数
                except KeyError:#本无
                    pass#放过
        上下文.监听('agent/status',状态监听)#status 结束
        def 会话事件(会话,事件,*其余):
            """只看助手消息；成功响应清计数。"""
            if 事件['type']!='assistant/message':#只看助手消息
                return#放过
            智能体=自身.溢出智能体表.get(会话)#该会话的溢出智能体
            if 智能体 is not None:#有记下
                try:#清计数
                    del 自身.溢出重试表[智能体]#成功响应清计数
                except KeyError:#本无
                    pass#放过
        上下文.监听('session/event',会话事件)#session/event 结束
        def 请求错误(载荷,下一步):
            """溢出则尝试压缩并重试；否则原样委托。"""
            智能体=载荷['agent']#智能体
            失败=载荷['failure']#失败
            信号=载荷['signal'] if 'signal' in 载荷 else None#取消
            if 失败['code']!=上下文窗口溢出码 or 已中止(信号):#非溢出或已取消
                return 下一步()#委托
            自身.溢出智能体表[智能体.session]=智能体#记下本会话智能体
            目标=已路由目标(智能体.session)#须有已路由目标
            if 目标 is None:#没有则无法恢复
                return 下一步()#委托
            政策=解析目标政策(自身.配置,目标)#目标政策
            重试次数=自身.溢出重试表.get(智能体,0)#已恢复次数
            if 重试次数>=政策['maxOverflowRetries']:#达到上限则放弃
                return 下一步()#委托
            代数=智能体.session.surface.replaceGeneration#压缩前的表面代数
            结果=None#摘要结果
            try:#尝试溢出压缩
                结果=自身.按需压缩(智能体,'context-overflow',信号)#强制有用缩减
            except Exception as 恢复错误:#恢复路径任意抛错仍可能已有耐久进展
                消息=str(恢复错误)#诊断
                if (not 已中止(信号)#尚未取消
                        and 智能体.session.surface.replaceGeneration>代数):#已有耐久表面进展
                    上下文.日志.警告(#警告后仍重试
                        'context-overflow compaction failed after durable surface progress: '+消息
                        +'; retrying from the replacement surface'#从替换表面重试
                    )#warn 结束
                    自身.溢出重试表[智能体]=重试次数+1#记一次恢复
                    return {'kind':'retry'}#重试原请求
                取消文案='cancellation prevents retry' if 已中止(信号) else 'preserving the original request error'#取消则不重试，否则保留原错
                上下文.日志.警告('context-overflow compaction failed: '+消息+'; '+取消文案)#无进展则保留原错误
                return 下一步()#委托原失败
            if (已中止(信号)#等待期间被取消
                    or 智能体.session.surface.replaceGeneration<=代数):#或表面未推进
                return 下一步()#委托
            if 结果 is not None:#有摘要则记日志
                记结果(结果,'context overflow recovery')#记日志
            自身.溢出重试表[智能体]=重试次数+1#记一次恢复
            return {'kind':'retry'}#从替换表面重试
        上下文.监听('agent/request-error',请求错误)#request-error 结束

    def 摘要(自身,输入,智能体,信号=None):
        """通过一次直接的 ctx.llm.stream() 调用摘要重放对话区间；覆盖这一唯一钩子即可换成模板或远程摘要器。"""
        目标=对话目标(智能体)#对话目标
        if 目标 is None:#没有精确目标
            配置值=自身.配置#用服务默认
        else:#否则合并覆盖
            配置值=解析目标政策(自身.配置,目标)#目标政策
        return 经语言模型摘要(自身.ctx,配置值,输入,智能体,信号)#默认 LLM 一次性摘要

    def 按需压缩(自身,智能体,触发,信号):
        """两种触发都为最近一次耐久已路由请求信封计价；溢出绕过常规阈值与保留尾政策。"""
        目标=已路由目标(智能体.session)#须有已路由目标
        if 目标 is None:#没有则无法选政策
            return None#无需摘要
        政策=解析目标政策(自身.配置,目标)#目标政策
        计量器=自身.ctx.tokenMeter#单例计量
        计量=计量器.测量(智能体.session)#当前表面计量
        if 触发=='context-overflow':#溢出恢复
            pass#下面单独处理
        elif 触发=='pressure':#步进压力
            pass#下面单独处理
        else:#未来未知触发
            断言永不(触发,'compaction trigger')#穷尽失败
        修剪=自身.ctx.获取服务('toolResultPruner')#可选修剪器；compaction-basic 保持可独立组合
        if 触发=='context-overflow':#溢出路径
            if 修剪 is not None:#挂了修剪器
                修剪.修剪会话(智能体.session)#先无模型修剪
                计量=计量器.测量(智能体.session)#修剪后重测
            区间=选择可压缩区间(智能体.session,计量,0)#不保留尾，尽量缩
            if 区间 is None:#没有可压缩区间
                return None#无可摘要
            return 自身.压缩区间(区间['start'],区间['end'],智能体,信号)#强制压缩该区间
        模型信息=自身.ctx.llm.解析模型信息(目标['provider'],目标['model'],信号)#解析模型容量
        上下文容量=模型信息['context'] if 模型信息 is not None and 'context' in 模型信息 else None#可选上下文
        校验无活动压缩(智能体.session,'automatic pressure compaction')#异步决策后复核锁
        目标键=str(目标['provider'])+'/'+str(目标['model'])#警告键
        if 上下文容量 is None:#适配器没报窗口
            raise 目标压力配置错误(#可抑制警告
                目标键,#目标键
                'compaction-basic: no context capacity for '+目标键+'; '
                +'configure contextWindow on that adapter model',#须配置窗口
            )#抛出结束
        规格=解析压缩规格(政策,上下文容量['contextWindow'])#缩成 token 预算
        if 计量['totalTokens']<规格['thresholdTokens']:#未达压力阈值
            return None#无需摘要
        if 修剪 is not None:#压力够格后，先落地无模型遍再选摘要区间
            修剪.修剪会话(智能体.session)#无模型修剪
            计量=计量器.测量(智能体.session)#修剪后重测
        if 计量['totalTokens']<规格['thresholdTokens']:#修剪后已低于阈值
            return None#无需摘要
        结果=None#最近一次摘要结果
        for 尝试 in range(规格['compactionRetries']+1):#含首次在内的尝试
            区间=选择可压缩区间(智能体.session,计量,规格['retainTokens'])#保留近期尾
            if 区间 is None:#没有可压缩区间
                if 结果 is None:#从未摘要成功
                    return None#无可摘要
                break#已有成功结果则停止
            结果=自身.压缩区间(区间['start'],区间['end'],智能体,信号)#压缩该区间
            计量=计量器.测量(智能体.session)#压缩后重测
            if 计量['totalTokens']<规格['thresholdTokens']:#已低于阈值
                return 结果#返回
        raise 基础压缩错误(#仍高于阈值
            'compaction still above threshold after '+str(规格['compactionRetries']+1)
            +' compaction attempts ('+str(计量['totalTokens'])
            +' estimated tokens >= threshold '+str(规格['thresholdTokens'])+')'#尝试次数与计量
        )#抛出结束

    def 压缩区间(自身,起点,终点,智能体,信号=None):
        """返回成功的耐久压缩结果。"""
        return 压缩表面区间(#跑共享事务
            自身.区间依赖(),#计量与摘要钩子
            智能体.session,#目标会话
            起点,#起始
            终点,#结束
            智能体,#摘要用智能体
            {'owner':'current-turn','stability':'whole-surface'},#回合内、整表面稳定
            信号,#取消
        )#事务结束

    def 立即压缩(自身,智能体,信号,来源命令标识=None):
        """仅在其独立标记对耐久检查点之后才决议；没有可安全有用区间时为 None。"""
        若已中止则抛出(信号)#入口即检查取消
        try:#同步启动空闲任务
            def 维护任务(智能体信号):
                """跑区间事务；智能体取消映射为 cancelled。"""
                操作信号=合成信号(智能体信号,信号)#智能体取消或请求取消
                try:#跑区间事务
                    若已中止则抛出(操作信号)#进入前再检查
                    区间=选择可压缩区间(#选有用区间
                        智能体.session,#会话
                        自身.ctx.tokenMeter.测量(智能体.session),#当前计量
                        0,#不强制保留尾
                    )#选择结束
                    if 区间 is None:#没有可压缩区间
                        return None#无可压缩
                    def 刷盘():
                        """刷盘会话。"""
                        return 自身.ctx.sessions.flush(智能体.session)#刷盘
                    选项={#独立括号选项
                        'owner':None,#回合之间的独立事务
                        'stability':'selected-span',#只要求所选跨度稳定
                        'flush':刷盘,#刷盘
                    }#选项基础
                    if 来源命令标识 is not None:#有命令 id 才写入
                        选项['sourceCommandId']=来源命令标识#来源命令
                    return 压缩表面区间(#跑独立事务
                        自身.区间依赖(),#计量与摘要钩子
                        智能体.session,#目标会话
                        区间['start'],#起始
                        区间['end'],#结束
                        智能体,#摘要用智能体
                        选项,#选项
                        操作信号,#组合取消
                    )#事务结束
                except Exception as 错误:#维护任务内失败按取消优先分类
                    if 已中止(智能体信号) and 操作信号._异常 is 智能体信号._异常:#是智能体取消赢了
                        raise 手动压缩错误(#映射为 cancelled
                            'cancelled',#取消码
                            'manual compaction was cancelled',#取消诊断
                            {'cause':错误},#保留原因
                        )#抛出结束
                    若已中止则抛出(操作信号)#请求取消则抛原中止
                    raise 错误#其他失败原样抛
            return 智能体.执行维护(维护任务).等待()#空闲维护结束
        except 手动压缩错误:#已分类则原样抛
            raise#原样
        except Exception as 错误:#同步拒绝：智能体非空闲
            raise 手动压缩错误(#映射为 busy
                'busy',#忙碌码
                'manual compaction requires an idle agent with no waking queued work',#须空闲
                {'cause':错误},#保留原因
            )#抛出结束

    def 区间依赖(自身):
        """返回区间事务依赖。"""
        def 摘要钩子(输入,所有者,中止=None):
            """转给自身.摘要。"""
            return 自身.摘要(输入,所有者,中止)#动态分发
        return {#依赖对象
            'meter':自身.ctx.tokenMeter,#单例计量
            'summarize':摘要钩子,#动态分发钩子
        }#返回结束

基础压缩引擎.inject=注入#Cordis inject 槽
基础压缩引擎.Config=配置#Cordis Config 槽
default=基础压缩引擎#Cordis默认导出
