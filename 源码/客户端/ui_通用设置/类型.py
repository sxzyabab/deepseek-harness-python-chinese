__all__=['桌面更新失败种类表','桌面更新呈现','桌面更新桥','桌面更新视图']

桌面更新失败种类表=(#Web 文案分类，不暴露原始更新诊断
    'check','check-network','download','download-network',
    'install','install-network','stop-failed','tasks-changed','tasks-unavailable',
)

桌面更新呈现={'phase':'idle'}#phase 另可带 version/percent/failure
桌面更新桥={'status':None,'open':None,'subscribe':None}#可选载体接口
桌面更新视图={'failed':False,'opening':False}#可带 presentation
