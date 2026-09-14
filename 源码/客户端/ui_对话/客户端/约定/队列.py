__all__=['队列项标识','队列动作','队列行']#仅中文公开名

#队列项标识：SessionFace.updateQueue 第 0 参（行 id）
#队列动作：SessionFace.updateQueue 第 1 参（变更）
#队列行：ConversationSnapshot.queue 数组元素
队列项标识=str#队列项 id
队列动作=dict#变更载荷形
队列行=dict#权威队列快照一行
