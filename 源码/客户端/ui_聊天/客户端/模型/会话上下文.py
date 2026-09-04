"""由表面替换重建的一代不可变模型上下文。

对齐上游 `ui-chat/src/client/model/conversation-context.ts`。公开面仅中文名。
"""

__all__=['会话上下文起源种','会话上下文']#仅中文公开名

会话上下文起源种=('compaction','rewind','rewrite')#压缩|回退|改写

def 会话上下文(标识,节点们,父标识=None,起源=None,起源序号=None,创建于=None,提示=None):#会话上下文工厂
    """一代不可变模型上下文。"""
    出={'id':标识,'nodes':节点们}#基
    if 父标识 is not None:#有父
        出['parentId']=父标识#挂
    if 起源 is not None:#有起源
        出['origin']=起源#挂
    if 起源序号 is not None:#有 seq
        出['originSeq']=起源序号#挂
    if 创建于 is not None:#有时
        出['createdAt']=创建于#挂
    if 提示 is not None:#有提示
        出['prompt']=提示#挂
    return 出#上下文
