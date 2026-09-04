"""无密钥快照层背后的会话日志快照支持。

对齐上游 `session-snapshot/src/index.ts`。公开面仅中文名。
"""
from .身份 import 脱敏会话快照标识#身份脱敏
from .测试架 import 运行场景,快照溢出根#场景 harness
from .启动器 import 启动ACP测试智能体,物化配置档补丁#启动器
from .归一化 import (#归一化
    提取快照溢出路径,归一化会话日志,归一化会话快照,归一化会话快照们,归一化标准输出,
    擦除请求头,擦除会话快照,擦除系统提示词,擦除工具模式,令牌化会话夹具工作目录,
)#归一化结束
from .清单 import 解析快照清单#清单
from .套件 import (#套件
    格式化系统提示词快照,格式化工具模式快照,夹具上下文,头变更计数,定义ACP快照套件,
    归一化请求头,归一化系统提示词,归一化工具模式,解析工具模式快照,刷新夹具替换,
    恢复钉住工具模式,会话夹具名,稳定夹具消息标识,稳定刷新日志,
)#套件结束
from .工作区 import 捕获期望工作区快照,捕获工作区快照,空工作区标记#工作区

__all__=[#仅中文公开名
    '脱敏会话快照标识','运行场景','快照溢出根','启动ACP测试智能体','物化配置档补丁',
    '提取快照溢出路径','归一化会话日志','归一化会话快照','归一化会话快照们','归一化标准输出',
    '擦除请求头','擦除会话快照','擦除系统提示词','擦除工具模式','令牌化会话夹具工作目录',
    '解析快照清单','格式化系统提示词快照','格式化工具模式快照','夹具上下文','头变更计数',
    '定义ACP快照套件','归一化请求头','归一化系统提示词','归一化工具模式','解析工具模式快照',
    '刷新夹具替换','恢复钉住工具模式','会话夹具名','稳定夹具消息标识','稳定刷新日志',
    '捕获期望工作区快照','捕获工作区快照','空工作区标记',
]#公开面结束

redactSessionSnapshotIds=脱敏会话快照标识#上游名
runScenario=运行场景#上游名
snapshotSpillRoot=快照溢出根#上游名
launchAcpTestAgent=启动ACP测试智能体#上游名
materializeProfilePatch=物化配置档补丁#上游名
extractSnapshotSpillPaths=提取快照溢出路径#上游名
normalizeSessionLog=归一化会话日志#上游名
normalizeSessionSnapshot=归一化会话快照#上游名
normalizeSessionSnapshots=归一化会话快照们#上游名
normalizeStdout=归一化标准输出#上游名
scrubRequestHeaders=擦除请求头#上游名
scrubSessionSnapshot=擦除会话快照#上游名
scrubSystemPrompts=擦除系统提示词#上游名
scrubToolSchemas=擦除工具模式#上游名
tokenizeSessionFixtureCwd=令牌化会话夹具工作目录#上游名
parseSnapshotManifest=解析快照清单#上游名
formatSystemPromptSnapshot=格式化系统提示词快照#上游名
formatToolSchemasSnapshot=格式化工具模式快照#上游名
fixtureContext=夹具上下文#上游名
headerChangeCount=头变更计数#上游名
defineAcpSnapshotSuite=定义ACP快照套件#上游名
normalizedHeaders=归一化请求头#上游名
normalizedSystemPrompts=归一化系统提示词#上游名
normalizedToolSchemas=归一化工具模式#上游名
parseToolSchemasSnapshot=解析工具模式快照#上游名
refreshFixtureReplacements=刷新夹具替换#上游名
restorePinnedToolSchemas=恢复钉住工具模式#上游名
sessionFixtureNames=会话夹具名#上游名
stabilizeFixtureMessageIds=稳定夹具消息标识#上游名
stabilizeRefreshLog=稳定刷新日志#上游名
captureExpectedWorkspaceSnapshot=捕获期望工作区快照#上游名
captureWorkspaceSnapshot=捕获工作区快照#上游名
EMPTY_WORKSPACE_MARKER=空工作区标记#上游名
