'插件清单的线载荷。只有结构，没有运行时'
__all__=['插件条目标识',#品牌化条目 id
    '插件纤程阶段',#对外阶段
    '插件清单条目',#一条加载器条目
    '预设插件启用',#预设行的有效启用
    '智能体预设插件行',#预设组合里的一行
    '智能体预设插件组',#一个预设及其组合
    '插件清单快照',]#一次 list 的投影

插件条目标识=str#Loader 树条目 id。运行时仍是字符串
插件纤程阶段=str|None#pending、loading、active、failed、unloading，没有活根纤程时是 None
预设插件启用=bool|str#true、false，或 conditional
插件清单条目=dict#entryId、moduleName、可选 meta、enabled、fiberPhase
智能体预设插件行=dict#entryId、moduleName、可选 meta、enabled、可选 condition、fiberPhase
智能体预设插件组=dict#id、可选 name、isDefault、可选 broken、rows
插件清单快照=dict#可选 managementAvailable、entries、可选 agentPresets
