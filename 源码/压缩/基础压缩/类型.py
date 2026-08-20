"""可感知回放的基础压缩后端的配置词汇。"""
# 本模块只声明词汇字段名元组；运行时解析住在配置.py

压缩政策配置字段=(#默认政策与精确模型覆盖共用的政策字段
    'thresholdRatio',#在模型上下文窗口的此比例处压缩；默认 0.8
    'retainRatio',#作为模型窗口比例保留的近期上下文；默认 0.16
    'retainTokens',#绝对近期上下文预算；与 retainRatio 互斥
    'summarizationProvider',#摘要提供方；与 summarizationModel 一起设置，或继承对话目标
    'summarizationModel',#摘要模型；与 summarizationProvider 一起设置，或继承对话目标
    'maxTokens',#摘要的提供方生成上限；默认 8192
    'compactionRetries',#压力仍高于阈值时，第一次压缩后的额外尝试；默认 1
    'maxOverflowRetries',#规范上下文溢出后的最大重试；0 禁用恢复；默认 1
)#压缩政策配置字段结束

模型压缩政策配置字段=(#叠在默认压缩政策上的精确提供方/模型覆盖
    'provider',#要匹配的已注册提供方路由
    'model',#provider 内要匹配的精确路由模型 id
)+压缩政策配置字段#精确目标覆盖=路由键+政策字段

基础压缩配置字段=压缩政策配置字段+(#带可选精确目标政策表的基础压缩配置
    'modelPolicies',#精确提供方/模型覆盖；重复目标会使插件加载失败
    'auto',#启用自动步进边界压力与溢出恢复监听器；默认 True
)#基础压缩配置字段结束

已解析保留形态说明=('retainRatio','retainTokens')#恰好一种已校验保留形态：按比例或按绝对 token

已解析政策字段说明=(#精确目标匹配前后共用的已校验政策字段
    'thresholdRatio',#压力阈值比例
    'summarizationProvider',#摘要提供方
    'summarizationModel',#摘要模型
    'maxTokens',#摘要生成上限
    'compactionRetries',#压缩重试
    'maxOverflowRetries',#溢出重试
)#已解析政策字段说明结束

已解析配置字段说明=已解析政策字段说明+已解析保留形态说明+(#已校验的不可变配置，目标特有默认值仍未解析
    'modelPolicies',#精确目标表
    'auto',#是否自动
)#已解析配置字段说明结束

已解析目标政策字段说明=已解析政策字段说明+已解析保留形态说明+(#一个路由对话目标在容量缩放之前的完全合并政策
    'target',#精确路由目标 provider/model
)#已解析目标政策字段说明结束

已解析压缩规格字段说明=(#一个路由模型的具体压力与保留预算
    'target',#精确路由目标
    'contextWindow',#模型上下文窗口
    'thresholdRatio',#阈值比例
    'thresholdTokens',#压力阈值 token
    'retainTokens',#保留 token
    'summarizationProvider',#摘要提供方
    'summarizationModel',#摘要模型
    'maxTokens',#生成上限
    'compactionRetries',#压缩重试
    'maxOverflowRetries',#溢出重试
)#已解析压缩规格字段说明结束
