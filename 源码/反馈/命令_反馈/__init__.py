"""会话反馈事件与人类面向的 `/feedback` 生产者。

对齐上游 `@deepseek-ai/dsh-command-feedback`。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
from ...身份.匿名用户id import 获取或创建匿名用户id#匿名用户 id

名称='command-feedback'#Cordis插件名
注入=['commands']#依赖命令注册表
用法='Usage: /feedback <text>'#用法提示

__all__=['名称','注入','用法','记录反馈','应用','默认']#仅中文公开名

def 断言永不可达(值):
    """封闭联合出现未处理成员时大声失败。"""
    raise TypeError('command-feedback: unsupported sharing status '+repr(值))#未知分享状态

def 分享句子(分享):
    """把披露策略翻译成一句人类可读说明。"""
    if 分享=='full':#全量分享
        return 'Session sharing is enabled.'#已启用
    if 分享=='feedback-only':#仅反馈门控
        return 'Session sharing is feedback-gated; recording feedback uploads the session records not yet shared.'#门控说明
    if 分享=='disabled':#禁用
        return 'Session sharing is disabled.'#已禁用
    return 断言永不可达(分享)#穷尽

def 分享披露(遥测):
    """无遥测服务时说明未配置。"""
    if 遥测 is None:#未挂载
        return 'Session sharing is not configured.'#未配置
    return 分享句子(遥测.sharing)#已挂载则读策略

def 记录反馈(会话,文本):
    """追加一条仅日志的 feedback/record 事件。"""
    规范化=str(文本).strip()#去掉首尾空白
    if len(规范化)==0:#空文本
        raise TypeError('feedback text must not be empty')#拒绝空反馈
    会话.追加('feedback/record',{'text':规范化})#追加事件

def 执行反馈命令(调用,上下文):
    """无正文则返回用法错误，否则记录并返回确认。调用是 dict。"""
    原文=调用['rawInput'] if 'rawInput' in 调用 else ''#正文
    if len(str(原文).strip())==0:#无正文
        return {'kind':'error','text':'Feedback text is required. '+用法}#用法错误
    智能体=调用['agent']#调用方智能体
    会话=智能体.session#会话对象
    记录反馈(会话,原文)#记录
    遥测=上下文.获取服务('sessionTelemetry',False)#可选遥测
    匿名用户=获取或创建匿名用户id()#真实匿名 id
    return {#成功确认
        'kind':'success',#成功
        'text':'Feedback recorded for session '+str(会话.id)+'\nAnonymous user: '+str(匿名用户)+'. '+分享披露(遥测),#确认文案
    }#成功返回结束

def 应用(上下文):
    """为每个已组合的命令适配器注册 /feedback。"""
    def 处理(调用):
        """处理一条 /feedback。"""
        return 执行反馈命令(调用,上下文)#处理函数
    上下文.commands.register({#注册命令
        'name':'feedback',#命令名
        'description':'record feedback about this session',#描述
        'input':{'hint':'<text>'},#输入提示
        'recordInput':False,#不记录原始输入
        'handler':处理,#处理函数
    })#register结束

name=名称#Cordis插件名
inject=注入#Cordis依赖声明
apply=应用#Cordis插件入口
默认=应用#默认导出
default=应用#Cordis默认导出
