"""TypeScript SDK 客户端的类型：启动选项、通知字段，以及所拥有活动的结果。

对齐上游 `sdk/client/src/types.ts`。公开面仅中文名。配置键与方法名保持上游。
"""

__all__=[#仅中文公开名
    '装备通知','通知过滤','装备客户端选项','深求装备选项','运行结果',
]#公开面结束

# 一条从线上收到的服务端到客户端通知：method + params。
装备通知=('method','params')#线通知字段

# 决定订阅是否接收某条通知的谓词：callable(通知) -> bool。
通知过滤=None#类型占位，运行时为可调用

# HarnessClient 的启动与超时选项字段。
装备客户端选项=(#底层客户端启动选项
    'command','args','cwd','env',
    'requestTimeoutMs','shutdownTimeoutMs','disposeEofGraceMs','disposeGraceMs',
)#字段结束

# 高层 DeepSeekHarness 封装的选项字段。
深求装备选项=('launch','cwd','provider','model','maxTokens')#高层封装选项

# 一次拥有的会话活动区间字段。
运行结果=('sessionId','finalResponse','events','notifications')#一次运行结果
