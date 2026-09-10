"""`file` 协议的资源元数据、导航参数、客户端错误码与变更供给通知。

对齐上游 `workspace-files/src/client/types.ts`。公开面仅中文名。
跨线 / 资源值为 dict；`file` 资源值即宿主 `WorkspaceFileStat`。
"""

__all__=[#仅中文公开名
    '工作区文件参数字段','工作区文件编辑种类','工作区文件通知种类',
]#公开面结束

# ResourceProtocolMap.file —— 地址形如
# dsh-resource://file/session/<sessionId>/<path>（绝对或工作区相对）
# 值为 WorkspaceFileStat：absolutePath / version / bytes?

工作区文件参数字段=('line',)#打开/导航时可选 1 起算行号
工作区文件编辑种类=('changed','absent')#宿主写入通知
工作区文件通知种类=('changed','absent')#仅 Host 写入

# 客户端专用 RemoteErrorDetailsMap（宿主从不发射）：
# 'workspace-file/unsupported-address': {address}
# 'workspace-file/unknown-workspace': {address}
