"""每轮工作区变更摘要、宣告事件与 Host 服务面。

公开面仅中文名。线协议字段 path/display/added/deleted/binary/oversized/turn/cwd/files/total/snapshot/before/after/kind/coarse/hunks/oldStart/oldLines/newStart/newLines/lines 与事件名 workspace/changes、服务名 workspaceChanges 保持英文。

跨包形态一律 dict。
"""
__all__=[#仅中文公开名
    '工作区变更文件字段','工作区变更摘要字段','差异块字段','工作区文件差异字段','工作区变更服务字段',
]#公开面结束

#常量
工作区变更文件字段=('path','display','added','deleted','binary','oversized')#单文件变更字段
工作区变更摘要字段=('turn','cwd','files','total','added','deleted','snapshot')#一轮摘要字段
差异块字段=('oldStart','oldLines','newStart','newLines','lines')#统一差异块字段
工作区文件差异字段=('kind','path','display','before','after','hunks','coarse')#按需对比字段
工作区变更服务字段=('摘要','差异')#Host 服务方法面
