'file 协议的资源元数据、导航参数、客户端错误码和变更供给通知'

__all__=[#仅中文公开名
    '工作区文件参数字段','工作区文件编辑变更字段','工作区文件编辑缺失字段',
    '工作区文件通知刷新字段',
]#公开面结束

# ResourceProtocolMap.file 的值是工作区文件状态：absolutePath、version、可选 bytes。
# 地址是 dsh-resource://file/session/<sessionId>/<path>，路径可为绝对或工作区相对。

工作区文件参数字段=('line',)#打开或导航时可选的 1 起算行号
工作区文件编辑变更字段=('kind','version')#kind 固定为 changed
工作区文件编辑缺失字段=('kind',)#kind 固定为 absent
工作区文件通知刷新字段=('kind',)#kind 固定为 refresh，重连后要求重新 stat

# 客户端才发射、宿主从不发射的 RemoteErrorDetailsMap：
# workspace-file/unsupported-address: {address}
# workspace-file/unknown-workspace: {address}
