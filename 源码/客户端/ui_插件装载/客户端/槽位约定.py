__all__=[]#槽位约定仅作类型契约说明，运行时无导出

#主栏 plugins.*：plugins.add.actions、plugins.item、plugins.bundle.activation、
#plugins.bundle.config、plugins.row.config、plugins.detail.actions、
#plugins.detail.badge、plugins.detail.section。
#登记方以类型合并契约，经 slots 登记，运行时不导入本包。
#view 为 summary 或 page。行没有说明时，说明位置回退到 plugins.row.config 的 summary。
#槽里没有登记时渲染结果为空，本页不再另写产品文案。
