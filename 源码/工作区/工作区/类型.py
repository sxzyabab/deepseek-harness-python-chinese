"""工作区实体公开类型词汇。"""
__all__=['工作区标识类型','工作区接口字段']

工作区标识类型=str#稳定记录 id（生成 uuid，不是路径）
工作区接口字段=(#消费方工作区接口字段集合
    'id','path','title','createdAt','updatedAt','sessionIds',
    'setTitle','attachSession','insertSessionBefore','detachSession','status',
)
