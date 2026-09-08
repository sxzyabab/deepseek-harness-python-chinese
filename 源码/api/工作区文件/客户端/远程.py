"""本包调用的 Client Remote 切片：按名的 `workspaceFiles` 方法，以及结构上的流监督器。

对齐上游 `workspace-files/src/client/remote.ts`。公开面仅中文名。
供给与提供方相对可脚本化的面做测试；跨包 Remote 面为对象，方法名保持线路英文
（`workspaceFiles`、`$stream`、`stat`、`changes`）。
"""

__all__=[#仅中文公开名
    '监督流选项字段','监督流项字段','工作区文件命名空间方法','工作区文件远程字段',
]#公开面结束

# SupervisedStreamItem：{'value': 帧, 'accept': 可调用} —— accept 标记本代健康
监督流项字段=('value','accept')#监督流一项

# SupervisedStreamOptions
# name: 诊断用所有者名
# open: (signal) -> 同步可迭代帧；signal 为 threading.Event
# ended: (accepted: bool) -> Exception；正常结束对应的错误；载体错误要求重开
监督流选项字段=('name','open','ended')#开流选项

# WorkspaceFilesNamespace：Pick<workspaceFiles, 'stat' | 'changes'>
工作区文件命名空间方法=('stat','changes')#本包调用的方法名

# WorkspaceFilesRemote：带 $stream 与 workspaceFiles 的 Client Remote 面
工作区文件远程字段=('$stream','workspaceFiles')#Remote 面字段
