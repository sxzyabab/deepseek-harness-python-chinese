"""fs-observation-policy 插件的词汇表：通过收窄 fs/* 事件携带的不透明 object 行动者，用来推导观察态所有者的最小执行上下文字段。

提供方词汇（FsTarget、FsVersion、写/编辑请求类型）复用自 @deepseek-ai/dsh-fs；本包只在其上拥有观察态所有者结构。
"""
#策略插件推导观察态所有者所需的工具执行最小结构视图。
#dsh-tools 的 ToolExecution 包含这些字段，因此工具把它的 exec 直接作为 fs/* 事件上的不透明 object 行动者传入；本插件把该行动者收窄为观察行动者，不导入 dsh-tools、dsh-agent 或 dsh-session。
#所有者在存在时是 agent.session。它被当作不透明对象身份（弱键字典键）；本包从不读取其任何字段。
#结构：{'agent':{'session':会话对象}}，agent 与 session 均可缺席。
观察行动者字段=('agent',)#策略所见的执行：存在时所属会话经 agent.session
观察行动者智能体字段=('session',)#可选智能体：为其跑调用的智能体，若有
观察行动者=dict#观察策略所用的最小执行上下文名义类型
