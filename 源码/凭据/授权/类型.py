"""授权能力缝线安全类型（无 cordis 依赖）。"""
授权方法字段=('id','label')#方法 id 与标签
授权通知字段=('message','url','code')#通知字段
授权提示选项字段=('id','label','description')#选项字段
授权状态=('authorized','cancelled')#begin 结果状态
授权结算=('authorized','cancelled','failed')#settled 事件状态
授权条目字段=('key','label','methods','inFlight')#注册表条目

__all__=[#仅中文公开名
    '授权方法字段','授权通知字段','授权提示选项字段',
    '授权状态','授权结算','授权条目字段',
]#公开面结束
