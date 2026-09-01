"""ACP 自动化服务器应用：默认智能体主干、JSONL 会话持久化，以及 ACP 桥。

对齐上游 `@deepseek-ai/dsh-acp-demo`（`示例/acp-demo/src/index.ts`）。公开面仅中文名。
应用经一条有序生命周期拥有这些插件，使 ACP 会话在持久化拆离前静止。它不向 stdout 写任何东西。
必须用具名导出，Loader 才能保留本插件的 Config schema。
"""
import os#路径拼接
from ...依赖 import cordis#外部依赖胶水
from ...依赖 import schemastery#配置字段
字符串字段=schemastery.字符串字段#配置字段
整数字段=schemastery.整数字段#配置字段
列表字段=schemastery.列表字段#配置字段
布尔字段=schemastery.布尔字段#配置字段
复合类型字段=schemastery.复合类型字段#配置字段
常量字段=schemastery.常量字段#配置字段
枚举字段=schemastery.枚举字段#配置字段
from ...acp import acp#ACP 桥
from .. import 智能体主干演示 as agentCore#默认智能体主干
from ...上下文 import 智能体指令 as workspaceContext#工作区上下文加载器
from ...内核.工具 import ToolRuntime#工具运行时
from ...会话 import 会话持久化 as JsonlSessionPersistence#JSONL 会话持久化
from .. import 会话检查点策略 as sessionCheckpointPolicy#检查点策略
from ..会话检索sqlite import SqliteSessionQueryEngine#SQLite 会话检索引擎（内置相对导入）

__all__=['名称','配置','应用']#仅中文公开名

名称='acp-demo'#插件名
默认持久化根='./.sessions'#默认 JSONL 根目录
持久化压缩模式=枚举字段('zstd','none')#JSONL 产物编码

配置={#ACP demo 应用配置 schema
    'provider':字符串字段(可空=False),#提供方必填
    'model':字符串字段(可空=False),#模型必填
    'maxParallelToolCalls':整数字段(默认值=1),#并行上限为正整数
    'persona':字符串字段(),#可选人设
    'toolOrder':列表字段(字符串字段(),默认值=None),#缺席即字典序
    'tools':ToolRuntime.Config if hasattr(ToolRuntime,'Config') else {},#工具注册表
    'dshHome':字符串字段(),#可选主目录
    'sessionTitle':agentCore.会话标题配置模式,#会话标题
    'persistenceRoot':字符串字段(默认值=默认持久化根),#默认 .sessions
    'packChunks':布尔字段(默认值=True),#默认打包块
    'persistenceCompression':持久化压缩模式,#压缩取值
    'workspaceContext':复合类型字段(常量字段(False),workspaceContext.Config if hasattr(workspaceContext,'Config') else {},可空=False),#必须显式
    'skills':agentCore.技能配置模式,#技能
    'toolBash':agentCore.Bash工具配置模式,#bash 工具
    'jobs':agentCore.作业配置模式,#作业
    'toolJobs':复合类型字段(常量字段(False),agentCore.作业工具配置模式),#作业工具或 false
    'goals':复合类型字段(常量字段(False),agentCore.目标配置模式),#目标或 false
}#配置结束

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性

def 应用(上下文,配置值):#安装 ACP demo 组合
    """把主干与 ACP 自动化传输组合起来。组合 effect 按相反顺序卸载。"""
    目标=取字段(配置值,'goals')#目标栈
    if 目标 is None:#缺省为空对象以启用默认目标栈
        目标={}#启用默认
    持久化根=取字段(配置值,'persistenceRoot')#持久化根
    if 持久化根 is None:#缺省
        持久化根=默认持久化根#默认目录

    def 组合():#按序挂载并反向卸载
        """有序生命周期组合。"""
        主干配置=dict(agentCore.挑选主干配置(配置值))#拷贝主干字段
        主干配置['goals']=目标#带上目标
        主干=解开(上下文.plugin(agentCore,主干配置))#挂载主干
        yield 主干.dispose#卸载时拆除主干
        持久化配置={'root':持久化根}#JSONL 配置
        if 取字段(配置值,'packChunks') is not None:#显式才转发 packChunks
            持久化配置['packChunks']=取字段(配置值,'packChunks')#转发
        if 取字段(配置值,'persistenceCompression') is not None:#显式才转发压缩
            持久化配置['compression']=取字段(配置值,'persistenceCompression')#转发
        持久化=解开(上下文.plugin(JsonlSessionPersistence,持久化配置))#挂载 JSONL
        yield 持久化.dispose#卸载时拆除持久化
        检查点=解开(上下文.plugin(sessionCheckpointPolicy))#挂载检查点策略
        yield 检查点.dispose#卸载时拆除检查点
        检索=解开(上下文.plugin(SqliteSessionQueryEngine,{'path':os.path.join(持久化根,'session-query.db')}))#挂载检索
        yield 检索.dispose#卸载时拆除检索引擎
        传输=解开(上下文.plugin(acp,{'provider':取字段(配置值,'provider'),'model':取字段(配置值,'model')}))#挂载 ACP 桥
        yield 传输.dispose#卸载时拆除传输

    上下文.effect(组合,'acp-demo.composition')#组合 effect 名
