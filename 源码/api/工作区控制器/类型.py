'浏览器侧工作区与目录选择的请求、结果和状态流词汇。运行时值是 dict，键保持上游原文'
__all__=[
    '工作区视图字段','工作区创建请求字段','工作区创建值字段','工作区重命名请求字段','工作区值字段',
    '工作区删除请求字段','工作区删除值字段','工作区插入请求字段','工作区顺序值字段',
    '工作区会话插入请求字段','工作区归档请求字段','工作区取消归档请求字段','工作区归档值字段',
    '工作区钉住请求字段','工作区取消钉住请求字段','工作区钉住值字段','工作区基线字段',
    '工作区跟随帧种类',
]

工作区视图字段=('workspaceId','path','title','sessionIds','createdAt','updatedAt')#一行工作区
工作区创建请求字段=('path',)#采纳已有目录
工作区创建值字段=('workspace','created')#工作区，以及这次是否新建
工作区重命名请求字段=('workspaceId','title')#身份与标题
工作区值字段=('workspace',)#变更后的整行
工作区删除请求字段=('workspaceId',)#要移除的登记
工作区删除值字段=('deleted',)#删除回执，值为 true
工作区插入请求字段=('workspaceId','beforeWorkspaceId')#移动的工作区与可选锚
工作区顺序值字段=('workspaceIds',)#变更后的完整顺序
工作区会话插入请求字段=('workspaceId','sessionId','beforeSessionId')#工作区、会话与可选锚
工作区归档请求字段=('sessionId','stopActivity')#会话，以及是否先停掉运行中的工作
工作区取消归档请求字段=('sessionId',)#要还原的会话
工作区归档值字段=('archivedSessionIds',)#完整归档集
工作区钉住请求字段=('sessionId',)#要钉住的会话
工作区取消钉住请求字段=('sessionId',)#要去掉钉的会话
工作区钉住值字段=('pinnedSessionIds',)#完整钉住集，最近钉的在前
工作区基线字段=('items','archivedSessionIds','pinnedSessionIds')#重连基线
工作区跟随帧种类=('baseline','replace','upsert','remove','order','archived','pinned')#帧的 type
