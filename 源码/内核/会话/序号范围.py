from .类型 import 安全整数上限

__all__=['编码序号范围','解码序号范围']

def _严格递增(值列表):
    """内存侧序号是否严格递增。"""
    return all(索引==0 or 值列表[索引]>值列表[索引-1] for 索引 in range(len(值列表)))

def _断言序号(值):
    """校验 sourceEventSeqs 成员。"""
    if isinstance(值,bool) or not isinstance(值,int) or 值<0 or abs(值)>安全整数上限:
        raise TypeError('sourceEventSeqs 必须包含非负安全整数')

def 编码序号范围(值列表):
    """把有利可图的连续段压成闭区间对；非严格递增则原样拷贝。"""
    if not _严格递增(值列表):
        return list(值列表)
    编码=[]
    起点下标=0
    while 起点下标<len(值列表):
        终点下标=起点下标
        while 终点下标+1<len(值列表) and 值列表[终点下标+1]==值列表[终点下标]+1:
            终点下标+=1
        if 终点下标-起点下标>=2:#长度≥3 压成对
            编码.append([值列表[起点下标],值列表[终点下标]])
        else:
            for 索引 in range(起点下标,终点下标+1):
                编码.append(值列表[索引])
        起点下标=终点下标+1
    return 编码

def 解码序号范围(值,最大条目=安全整数上限):
    """展开 JSON 存储形态的 sourceEventSeqs。"""
    if not isinstance(值,list):
        raise TypeError('sourceEventSeqs 必须是数组')
    解码=[]
    有范围=False
    for 条目 in 值:
        if isinstance(条目,int) and not isinstance(条目,bool):
            _断言序号(条目)
            if len(解码)>=最大条目:
                raise TypeError('sourceEventSeqs 超出其事件序列')
            解码.append(条目)
            continue
        if not isinstance(条目,list) or len(条目)!=2:
            raise TypeError('sourceEventSeqs 范围条目必须是 [start, end] 对')
        起,止=条目
        _断言序号(起)
        _断言序号(止)
        if 止<起:
            raise TypeError('sourceEventSeqs 范围要求 start <= end')
        长度=止-起+1
        if 长度>最大条目-len(解码):
            raise TypeError('sourceEventSeqs 范围超出其事件序列')
        for 序号 in range(起,止+1):
            解码.append(序号)
        有范围=True
    if 有范围 and not _严格递增(解码):
        raise TypeError('sourceEventSeqs 范围必须严格递增')
    return 解码
