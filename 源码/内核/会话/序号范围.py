from .类型 import 安全整数上限#安全整数上限

__all__=['编码序号范围','解码序号范围']#仅中文公开名

def _严格递增(值列表):#是否严格递增
    """内存侧序号是否严格递增。"""
    return all(索引==0 or 值列表[索引]>值列表[索引-1] for 索引 in range(len(值列表)))#逐项

def _断言序号(值):#断言安全非负整数
    """校验 sourceEventSeqs 成员。"""
    if isinstance(值,bool) or not isinstance(值,int) or 值<0 or abs(值)>安全整数上限:#非法
        raise TypeError('sourceEventSeqs 必须包含非负安全整数')#非法

def 编码序号范围(值列表):#编码序号范围
    """把有利可图的连续段压成闭区间对；非严格递增则原样拷贝。"""
    if not _严格递增(值列表):#非递增
        return list(值列表)#原样
    编码=[]#结果
    起点下标=0#游标
    while 起点下标<len(值列表):#压缩循环
        终点下标=起点下标#段末
        while 终点下标+1<len(值列表) and 值列表[终点下标+1]==值列表[终点下标]+1:#连续
            终点下标+=1#延长
        if 终点下标-起点下标>=2:#长度≥3 压成对
            编码.append([值列表[起点下标],值列表[终点下标]])#范围
        else:#单点或两连点
            for 索引 in range(起点下标,终点下标+1):#逐点
                编码.append(值列表[索引])#单点
        起点下标=终点下标+1#下一段
    return 编码#返回

def 解码序号范围(值,最大条目=安全整数上限):#解码序号范围
    """展开 JSON 存储形态的 sourceEventSeqs。"""
    if not isinstance(值,list):#非数组
        raise TypeError('sourceEventSeqs 必须是数组')#必须数组
    解码=[]#结果
    有范围=False#是否含范围
    for 条目 in 值:#逐项
        if isinstance(条目,int) and not isinstance(条目,bool):#单序号
            _断言序号(条目)#校验
            if len(解码)>=最大条目:#超限
                raise TypeError('sourceEventSeqs 超出其事件序列')#超限
            解码.append(条目)#追加
            continue#下一项
        if not isinstance(条目,list) or len(条目)!=2:#非对
            raise TypeError('sourceEventSeqs 范围条目必须是 [start, end] 对')#必须对
        起,止=条目#拆开
        _断言序号(起)#校验起
        _断言序号(止)#校验止
        if 止<起:#倒置
            raise TypeError('sourceEventSeqs 范围要求 start <= end')#倒置
        长度=止-起+1#长度
        if 长度>最大条目-len(解码):#超限
            raise TypeError('sourceEventSeqs 范围超出其事件序列')#超限
        for 序号 in range(起,止+1):#展开
            解码.append(序号)#追加
        有范围=True#标记
    if 有范围 and not _严格递增(解码):#非严格递增
        raise TypeError('sourceEventSeqs 范围必须严格递增')#非递增
    return 解码#返回
