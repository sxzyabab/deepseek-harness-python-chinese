'本包看到的客户端远程面：workspaceFiles 的 stat 与 changes，以及监督流'

__all__=[#仅中文公开名
    '监督流项字段','监督流选项字段','工作区文件命名空间方法','工作区文件远程字段',
]#公开面结束

监督流项字段=('value','accept')#value 是帧；accept 把这一代标成健康
监督流选项字段=('name','open','ended')#诊断名、打开一代、正常结束时的错误
工作区文件命名空间方法=('stat','changes')#本包实际调用的方法
工作区文件远程字段=('$stream','workspaceFiles')#上游字段名。网关客户端上 $stream 的方法是 打开逻辑流
