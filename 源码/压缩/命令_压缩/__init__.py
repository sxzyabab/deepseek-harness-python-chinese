"""面向人类的 /compact 命令，经压缩服务接口触发手动压缩。"""
from ...交互.命令.标识构造 import 命令定义标识#命令定义身份
from ..压缩 import 手动压缩错误#预期手动压缩失败

名称='command-compact'#框架插件名
依赖=['commands','compaction']#依赖命令注册表与压缩缝
用法='Usage: /compact (no arguments)'#用法提示文案

__all__=['名称','依赖','应用','默认']#仅中文公开名

def 断言永不可达(值):
    """本地封闭联合出现未处理成员时大声失败。"""
    raise TypeError('unknown manual compaction error code: '+str(值))#未知手动压缩错误码

def 预期失败(错误):
    """把预期的能力失败转成简短的仅人类结果。"""
    码=错误.code#失败类别
    if 码=='busy':#已有压缩在跑或智能体未空闲
        return {'kind':'error','text':'Compaction is unavailable because this process has an active compaction, or the agent is not idle.'}#忙碌
    if 码=='cancelled':#调用被取消
        return {'kind':'error','text':'Compaction cancelled.'}#取消
    if 码=='changed':#待替换历史在提交前已变
        return {'kind':'error','text':'The history selected for compaction changed before it could be replaced. The conversation is unchanged; the attempt is recorded in the session log.'}#历史已变
    if 码=='summary':#未能产出有用摘要
        return {'kind':'error','text':'Compaction could not produce a useful summary. The conversation is unchanged; the attempt is recorded in the session log.'}#摘要失败
    if 码=='commit':#提交未干净完成
        return {'kind':'error','text':'Compaction did not finish cleanly; some session history may have changed. Inspect the current session state before retrying.'}#提交失败
    if 码=='persistence':#压缩完成但会话未保存
        return {'kind':'error','text':'Compaction finished, but the session could not be saved.'}#持久化失败
    return 断言永不可达(码)#未来未知码穷尽失败

def 执行压缩(上下文,调用):
    """执行一次无参数的手动压缩请求。调用是 dict。"""
    原文=调用['rawInput'] if 'rawInput' in 调用 else ''#原始输入
    if len(str(原文).strip())>0:#带了多余参数
        return {'kind':'error','text':用法}#用法错误
    信号=调用['signal'] if 'signal' in 调用 else None#取消信号
    配对=调用['commandId'] if 'commandId' in 调用 else None#命令配对 id
    try:#调用压缩服务接口
        结果=上下文.compaction.立即压缩(调用['agent'],信号,配对)#立即压缩
        if 结果 is None:#尚无可压缩历史
            return {'kind':'success','text':'No compactable history yet.'}#空成功
        return {#压缩成功
            'kind':'success',#成功
            'text':'Compacted '+str(len(结果['shadowedSeqs']))+' history items (~'+str(结果['shadowedTokenCount'])+' tokens).',#遮蔽条数与估算 token
            'sourceEventSeq':结果['summarySeq'],#摘要事件序号
        }#成功返回结束
    except 手动压缩错误 as 错误:#预期能力失败
        if 信号 is not None and 信号.is_set():#取消信号已触发
            return {'kind':'error','text':'Compaction cancelled.'}#取消优先
        return 预期失败(错误)#按码映射
    except BaseException as 错误:#压缩过程失败
        if 信号 is not None and 信号.is_set():#取消信号已触发
            return {'kind':'error','text':'Compaction cancelled.'}#取消
        raise 错误#非预期失败继续抛

def 应用(上下文):
    """为每个已组合的人类命令适配器注册 /compact。"""
    def 处理(调用):
        """处理一条 /compact。"""
        return 执行压缩(上下文,调用)#同步执行
    上下文.commands.register({#注册 compact 命令
        'definitionId':命令定义标识('@deepseek-ai/dsh-command-compact'),#稳定定义身份
        'name':'compact',#命令名
        'description':'Compact older conversation history',#命令描述
        'handler':处理,#处理函数
    })#register结束

name=名称#框架插件名
inject=依赖#框架依赖声明
apply=应用#框架插件入口
默认=应用#默认导出
default=应用#框架默认导出
