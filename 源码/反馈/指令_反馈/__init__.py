"""会话反馈事件与人类面向的 `/feedback` 生产者。

对齐上游 `@deepseek-ai/dsh-command-feedback`。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水

名称='command-feedback'#Cordis插件名
注入=['commands']#依赖命令注册表
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
用法='Usage: /feedback <text>'#用法提示

__all__=['名称','注入','用法','记录反馈','应用','默认']#仅中文公开名

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 断言永不可达(值):#封闭联合穷尽检查
    """封闭联合出现未处理成员时大声失败。"""
    raise TypeError('command-feedback: unsupported sharing status '+repr(值))#未知分享状态

def 分享句子(分享):#披露策略对应的一句说明
    """把披露策略翻译成一句人类可读说明。"""
    if 分享=='full':#全量分享
        return 'Session sharing is enabled.'#已启用
    if 分享=='feedback-only':#仅反馈门控
        return 'Session sharing is feedback-gated; recording feedback uploads the session records not yet shared.'#门控说明
    if 分享=='disabled':#禁用
        return 'Session sharing is disabled.'#已禁用
    return 断言永不可达(分享)#穷尽

def 分享披露(遥测):#读取已挂载后端的披露策略
    """无遥测服务时说明未配置。"""
    if 遥测 is None:#未挂载
        return 'Session sharing is not configured.'#未配置
    return 分享句子(遥测.sharing)#已挂载则读策略

def 记录反馈(会话,文本):#独立于 UI 触发记录反馈
    """追加一条仅日志的 feedback/record 事件。"""
    规范化=str(文本).strip()#去掉首尾空白
    if len(规范化)==0:#空文本
        raise TypeError('feedback text must not be empty')#拒绝空反馈
    会话.append('feedback/record',{'text':规范化})#追加事件

def 执行反馈命令(调用,上下文):#校验、记录并确认一条反馈
    """无正文则返回用法错误，否则记录并返回确认。"""
    if len(str(取字段(调用,'rawInput')).strip())==0:#无正文
        return {'kind':'error','text':'Feedback text is required. '+用法}#用法错误
    记录反馈(取字段(取字段(调用,'agent'),'session'),取字段(调用,'rawInput'))#记录
    遥测=上下文.get('sessionTelemetry') if hasattr(上下文,'get') else getattr(上下文,'sessionTelemetry',None)#可选遥测
    匿名用户='anonymous'#匿名用户占位；完整实现依赖 anonymous-user-id 包
    try:#尝试读取匿名用户 id
        from ...身份.匿名用户id import 获取或创建匿名用户id#延迟导入
        匿名用户=获取或创建匿名用户id()#真实匿名 id
    except Exception:#包未组合
        pass#保留占位
    return {#成功确认
        'kind':'success',#成功
        'text':'Feedback recorded for session '+str(取字段(取字段(取字段(调用,'agent'),'session'),'id'))+'\nAnonymous user: '+str(匿名用户)+'. '+分享披露(遥测),#确认文案
    }#成功返回结束

def 应用(上下文):#注册全局 /feedback 命令
    """为每个已组合的命令适配器注册 /feedback。"""
    上下文.commands.register({#注册命令
        'name':'feedback',#命令名
        'description':'record feedback about this session',#描述
        'input':{'hint':'<text>'},#输入提示
        'recordInput':False,#不记录原始输入
        'handler':lambda 调用:执行反馈命令(调用,上下文),#处理函数
    })#register结束

apply=应用#Cordis插件入口
默认=应用#默认导出
default=应用#Cordis默认导出
