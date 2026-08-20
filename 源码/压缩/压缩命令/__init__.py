"""面向人类的 /compact 命令，走与后端无关的压缩 seam。"""
from cordis.工具 import 承诺,是否thenable#操作链承诺与可等待判定
from compaction import 手动压缩错误#手动压缩预期失败

名称='command-compact'#Cordis插件名
注入=['commands','compaction']#依赖commands与compaction服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
用法='Usage: /compact (no arguments)'#用法提示文案
def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 信号已中止(信号):#对齐 AbortSignal.aborted
    """英文 aborted 或中文 已中止 任一为真则视为已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if 取字段(信号,'aborted') is True:#英文旗标
        return True#已中止
    if 取字段(信号,'已中止') is True:#中文旗标
        return True#已中止
    return False#未中止

def 断言永不可达(值):#本地封闭联合出现未处理成员时大声失败
    """本地封闭联合出现未处理成员时大声失败。"""
    raise TypeError('unknown manual compaction error code: '+str(值))#未知手动压缩错误码

def 预期失败(错误):#把预期的能力失败转成简短的仅人类结果
    """把预期的能力失败转成简短的仅人类结果。"""
    码=取字段(错误,'code')#失败类别
    if 码=='busy':#已有压缩在跑或智能体未空闲
        return {#忙碌错误
            'kind':'error',#错误结果
            'text':'Compaction is unavailable because this process has an active compaction, or the agent is not idle.',#忙碌文案
        }#忙碌返回结束
    if 码=='cancelled':#调用被取消
        return {'kind':'error','text':'Compaction cancelled.'}#取消错误
    if 码=='changed':#待替换历史在提交前已变
        return {#历史已变错误
            'kind':'error',#错误结果
            'text':'The history selected for compaction changed before it could be replaced. The conversation is unchanged; the attempt is recorded in the session log.',#历史已变文案
        }#历史已变返回结束
    if 码=='summary':#未能产出有用摘要
        return {#摘要失败错误
            'kind':'error',#错误结果
            'text':'Compaction could not produce a useful summary. The conversation is unchanged; the attempt is recorded in the session log.',#摘要失败文案
        }#摘要失败返回结束
    if 码=='commit':#提交未干净完成
        return {#提交失败错误
            'kind':'error',#错误结果
            'text':'Compaction did not finish cleanly; some session history may have changed. Inspect the current session state before retrying.',#提交失败文案
        }#提交失败返回结束
    if 码=='persistence':#压缩完成但会话未保存
        return {#持久化失败错误
            'kind':'error',#错误结果
            'text':'Compaction finished, but the session could not be saved.',#持久化失败文案
        }#持久化失败返回结束
    return 断言永不可达(码)#未来未知码穷尽失败

def 执行压缩(上下文,调用):#执行一次无参数的手动压缩请求
    """执行一次无参数的手动压缩请求。"""
    原始=取字段(调用,'rawInput')#原始尾部输入
    if 原始 is None:#缺输入当空
        原始=''#空串
    if len(str(原始).strip())>0:#带了多余参数
        return {'kind':'error','text':用法}#用法错误
    信号=取字段(调用,'signal')#取消信号
    try:#调用压缩seam
        压缩=上下文.compaction#压缩引擎
        立即=getattr(压缩,'compactNow',None) or getattr(压缩,'立即压缩',None)#立即压缩入口
        结果=解开(立即(取字段(调用,'agent'),信号,取字段(调用,'commandId')))#立即压缩
        if 结果 is None:#尚无可压缩历史
            return {'kind':'success','text':'No compactable history yet.'}#尚无可压缩历史
        遮蔽序号=取字段(结果,'shadowedSeqs') or []#被遮蔽序号列表
        遮蔽令牌=取字段(结果,'shadowedTokenCount')#估算token
        return {#压缩成功
            'kind':'success',#成功结果
            'text':'Compacted '+str(len(遮蔽序号))+' history items (~'+str(遮蔽令牌)+' tokens).',#遮蔽条数与估算token
            'sourceEventSeq':取字段(结果,'summarySeq'),#摘要事件序号
        }#成功返回结束
    except Exception as 错误:#压缩过程失败
        if 信号已中止(信号):#取消信号已触发
            return {'kind':'error','text':'Compaction cancelled.'}#取消结算
        if isinstance(错误,手动压缩错误):#预期能力失败
            return 预期失败(错误)#转人类结果
        raise#非预期失败继续抛

def 应用(上下文):#为每个已组合的人类命令适配器注册 /compact
    """为每个已组合的人类命令适配器注册 /compact。"""
    进行中=set()#进行中的处理承诺集合

    def 处理(调用):#命令处理函数
        """启动一次压缩并把原承诺交给命令派发。"""
        操作=承诺()#本轮处理承诺
        def 跑():#同步跑完后结算承诺
            """执行压缩并兑现或拒绝本轮承诺。"""
            try:#执行压缩
                操作.兑现(执行压缩(上下文,调用))#兑现人类结果
            except BaseException as 错误:#非预期失败
                操作.拒绝(错误)#拒绝本轮
        进行中.add(操作)#记入进行中集合
        def 退役(_=None):#完成后从集合移除
            """完成后从集合移除。"""
            进行中.discard(操作)#退役
        跑()#启动一次压缩
        # 成败两支都不重新抛出，因此派生观察不会成为预期处理拒绝的未处理镜像。
        try:#无论成败都退役
            操作.then(退役,退役)#观察结算
        except BaseException:#观察路径吸收
            退役()#仍退役
        return 操作#把原承诺交给命令派发

    def 装寿命():#注册生命周期effect
        """先排空再注册：组合拆除是 LIFO，已启动的处理承诺安静下来之前不会有新调用进入。"""
        def 排空():#拆除时等全部处理结束
            """拆除时等全部处理结束。"""
            for 项 in list(进行中):#拷贝进行中集合
                try:#allSettled 语义
                    解开(项)#等到落定
                except BaseException:#单个失败不挡其余
                    pass#吞掉
        yield 排空#先挂排空，拆除时最后跑
        yield 上下文.commands.register({#注册compact命令
            'name':'compact',#命令名
            'description':'Compact older conversation history',#命令描述
            'handler':处理,#处理函数
        })#register结束

    上下文.effect(装寿命,'command-compact lifecycle')#effect标签

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
