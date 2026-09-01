"""工作区实体公开类型词汇。对齐上游 workspace/src/types.ts。"""
__all__=['工作区标识类型','工作区接口字段']#仅中文公开名

工作区标识类型=str#稳定记录 id 品牌（生成 uuid，不是路径）
工作区接口字段=(#消费方工作区接口
    'id','path','title','createdAt','updatedAt','sessionIds',
    'setTitle','attachSession','insertSessionBefore','detachSession','status',
)#接口字段结束
