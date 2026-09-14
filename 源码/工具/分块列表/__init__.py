__all__=['块容量','追加分块列表','迭代分块列表','分块列表模式','分块列表错误']#仅中文公开名

块容量=64#每块最多值数

class 分块列表错误(Exception):#本包异常基类
    """分块列表检查点或结构非法。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 追加分块列表(头,值):#追加而不修改输入
    """追加而不修改输入，最多复制一个 64 值块。空列表传 None。返回共享未改较旧块的新头 dict。"""
    if 头 is None or len(头['values'])==块容量:#空或块已满
        下一={'values':[值]}#新块
        if 头 is not None:#有较旧头
            下一['previous']=头#挂 previous
        return 下一#新头
    下一={'values':list(头['values'])+[值]}#同块复制并追加
    if 'previous' in 头:#有较旧
        下一['previous']=头['previous']#共享 previous
    return 下一#新头

def 迭代分块列表(头):#按插入顺序产出
    """按插入顺序访问全部值。空列表传 None。按引用产出所存值，不截断。"""
    块表=[]#自新到旧收集
    块=头#当前块
    while 块 is not None:#沿 previous 链
        块表.append(块)#收下
        块=块['previous'] if 'previous' in 块 else None#较旧
    块表.reverse()#自旧到新
    for 块 in 块表:#逐块
        for 项 in 块['values']:#块内插入序
            yield 项#产出

def 分块列表模式(值校验):#检查点校验器
    """返回递归校验可调用对象，拒绝空块、超大块与未知字段。值校验接收单项并返回规范值或抛错。"""
    def 校验(值):#校验一个节点
        """校验非空列表检查点节点。"""
        if not isinstance(值,dict):#须映射
            raise 分块列表错误('chunked list checkpoint must be an object')#拒绝
        键集=set(值.keys())#自有键
        if not 键集.issubset({'values','previous'}):#未知字段
            raise 分块列表错误('chunked list checkpoint has unknown fields')#严格
        if 'values' not in 值:#缺 values
            raise 分块列表错误('chunked list checkpoint requires values')#拒绝
        原值=值['values']#本块值
        if not isinstance(原值,list):#须数组
            raise 分块列表错误('chunked list values must be an array')#拒绝
        if len(原值)<1 or len(原值)>块容量:#空或超容量
            raise 分块列表错误('chunked list chunk size out of range')#拒绝
        规范值=[]#规范项
        for 项 in 原值:#逐项
            规范值.append(值校验(项))#调用方校验
        规范={'values':规范值}#本块
        if 'previous' in 值:#有较旧
            规范['previous']=校验(值['previous'])#递归
        return 规范#规范节点
    return 校验#校验器
