'workspaceFiles 远程命名空间的线路类型。运行时都是带英文字段的 dict'

__all__=[#仅中文公开名
    '工作区文件状态字段','工作区文件行窗口字段','工作区文件文本字段',
    '工作区字节窗口字段','工作区字节读取选项字段','工作区文件字节字段',
    '工作区目录条目字段','工作区目录列举字段',
    '工作区文件变更存在字段','工作区文件变更缺失字段',
    '工作区文件监视帧就绪字段','工作区文件监视帧变更字段',
]#公开面结束

# read、readBytes、stat、changes 用执行世界绝对路径。list 用工作区相对路径。

工作区文件状态字段=('absolutePath','version','bytes')#绝对路径、版本、可选整文件字节
工作区文件行窗口字段=('offset','limit')#read 行窗：1 起算，均可省略
工作区文件文本字段=('absolutePath','version','bytes','offset','text','lines','eof')#一页文本
工作区字节窗口字段=('offset','length')#readBytes 字节窗：0 起算，均可省略
工作区字节读取选项字段=('range','baseFile')#可选字节窗；baseFile 存在时 path 相对它的目录
工作区文件字节字段=('absolutePath','version','bytes','offset','data','eof')#原始字节窗
工作区目录条目字段=('name','type','size')#直接子项：基名、file|directory|other、可选 size
工作区目录列举字段=('path','entries','truncated')#工作区相对路径、截断后的子项、是否被条目上限截掉
工作区文件变更存在字段=('absolutePath','version')#目标仍在，带当前版本
工作区文件变更缺失字段=('absolutePath','absent')#目标已消失，absent 固定为 True
工作区文件监视帧就绪字段=('kind',)#kind 固定为 ready
工作区文件监视帧变更字段=('kind','change')#kind 固定为 change，change 为上面两种变更之一

# 宿主 RemoteErrorDetailsMap：
# workspace-file/watch-unsupported: {path}
# workspace-file/not-found: {path}
# workspace-file/outside-workspace: {path}
# workspace-file/too-large: {path, limit}
# workspace-file/not-text: {path}
# workspace-file/not-regular-file: {path, kind: directory|symlink|other}
# workspace-file/not-directory: {path, kind: file|symlink|other}
