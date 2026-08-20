"""对话调用配置与冻结工具。

对齐上游 `llm/src/call-config.ts`。公开面仅中文名；无英文别名。
配置字段键保持上游 wire。
"""
import weakref#弱集合
from .类型 import 是否中止信号#中止信号判定

__all__=(#仅中文公开名
    '可弱引用映射','冻结映射','冻结列表',
    '调用配置相等','标记循环请求','是否循环请求','是否冻结','深冻结','结构化克隆',
)#公开面结束

循环请求=weakref.WeakSet()#循环组装请求的弱集合

class 可弱引用映射(dict):#可被弱引用的映射
    """可被弱引用的映射，供进程内身份标记。"""

class 冻结映射(dict):#就地冻结后禁止改写的映射
    """就地冻结后禁止改写的映射。"""
    def __setitem__(自身,键,值):#禁止写入
        raise TypeError('cannot assign to frozen object')#禁止写入
    def __delitem__(自身,键):#禁止删除
        raise TypeError('cannot delete from frozen object')#禁止删除
    def clear(自身):#禁止清空
        raise TypeError('cannot clear frozen object')#禁止清空
    def pop(自身,*位置参数):#禁止弹出
        raise TypeError('cannot pop from frozen object')#禁止弹出
    def popitem(自身):#禁止弹出项
        raise TypeError('cannot popitem from frozen object')#禁止弹出项
    def setdefault(自身,键,默认=None):#禁止设默认
        raise TypeError('cannot setdefault on frozen object')#禁止设默认
    def update(自身,*位置参数,**关键字参数):#禁止更新
        raise TypeError('cannot update frozen object')#禁止更新

class 冻结列表(list):#就地冻结后禁止改写的列表
    """就地冻结后禁止改写的列表。"""
    def __setitem__(自身,键,值):#禁止写入
        raise TypeError('cannot assign to frozen object')#禁止写入
    def __delitem__(自身,键):#禁止删除
        raise TypeError('cannot delete from frozen object')#禁止删除
    def append(自身,值):#禁止追加
        raise TypeError('cannot append to frozen object')#禁止追加
    def extend(自身,值):#禁止扩展
        raise TypeError('cannot extend frozen object')#禁止扩展
    def insert(自身,下标,值):#禁止插入
        raise TypeError('cannot insert into frozen object')#禁止插入
    def pop(自身,*位置参数):#禁止弹出
        raise TypeError('cannot pop from frozen object')#禁止弹出
    def remove(自身,值):#禁止移除
        raise TypeError('cannot remove from frozen object')#禁止移除
    def clear(自身):#禁止清空
        raise TypeError('cannot clear frozen object')#禁止清空
    def reverse(自身):#禁止反转
        raise TypeError('cannot reverse frozen object')#禁止反转
    def sort(自身,*位置参数,**关键字参数):#禁止排序
        raise TypeError('cannot sort frozen object')#禁止排序

def 调用配置相等(甲,乙):#逐字段比较调用配置
    """调用配置逐字段相等，含 stop 列表逐元素。"""
    if 甲.get('provider')!=乙.get('provider'):#提供方不同
        return False#提供方不同
    if 甲.get('model')!=乙.get('model'):#模型不同
        return False#模型不同
    if 甲.get('reasoningEffort')!=乙.get('reasoningEffort'):#推理力度不同
        return False#推理力度不同
    if 甲.get('temperature')!=乙.get('temperature'):#温度不同
        return False#温度不同
    if 甲.get('maxTokens')!=乙.get('maxTokens'):#最大 token 不同
        return False#最大 token 不同
    左停=甲.get('stop')#左 stop
    右停=乙.get('stop')#右 stop
    if 左停 is None or 右停 is None:#一方无 stop
        return 左停 is 右停#两边都无才相等
    if len(左停)!=len(右停):#长度不等
        return False#长度不等
    下标=0#逐元素
    while 下标<len(左停):#尚未比完
        if 左停[下标]!=右停[下标]:#元素不等
            return False#元素不等
        下标+=1#下一元素
    return True#长度与逐元素都相等

def 标记循环请求(请求):#标记循环组装的请求
    """把一个精确请求对象标记为智能体循环组装。"""
    if type(请求) is dict:#普通映射不可弱引用
        请求.__class__=可弱引用映射#使普通映射可弱引用
    循环请求.add(请求)#记入弱集合
    return 请求#原样返回

def 是否循环请求(请求):#是否循环组装的请求
    """测试该精确请求对象是否由智能体循环组装。"""
    return 请求 in 循环请求#查弱集合

def 是否冻结(值):#值是否已经就地深冻结
    """值是否已经就地深冻结。"""
    return isinstance(值,(冻结映射,冻结列表))#类已换成冻结型

def 深冻结(值):#迭代深冻结
    """用迭代遍历就地深冻结一个值并防护环。"""
    已见=set()#已访问对象身份，防环
    待处理=[{'kind':'visit','node':值}]#从根值开始
    while len(待处理)>0:#还有任务
        任务=待处理.pop()#取出一条
        if 任务 is None:#类型收窄：空栈不会到这里
            continue#类型收窄：空栈不会到这里
        if 任务['kind']=='property':#属性取出任务
            源=任务['source']#属性所在对象
            键=任务['key']#属性键
            if isinstance(源,dict):#映射
                子=源[键]#取出映射值
            elif isinstance(源,list):#列表
                子=源[键]#取出列表值
            else:#其它对象
                子=getattr(源,键)#取出对象属性
            待处理.append({'kind':'visit','node':子})#把属性值排进访问
            continue#处理下一条
        节点=任务['node']#当前节点
        if 节点 is None or isinstance(节点,(str,bytes,int,float,bool)):#原语跳过
            continue#原语跳过
        if callable(节点) and not isinstance(节点,(dict,list,type)):#函数不冻结
            continue#函数不冻结
        if 是否中止信号(节点):#中止信号不冻结
            continue#中止信号不冻结
        编号=id(节点)#对象身份
        if 编号 in 已见:#已访问则跳过
            continue#已访问则跳过
        已见.add(编号)#记下已访问
        if isinstance(节点,dict) and not isinstance(节点,冻结映射):#就地换成冻结映射
            节点.__class__=冻结映射#就地换成冻结映射
        elif isinstance(节点,list) and not isinstance(节点,冻结列表):#就地换成冻结列表
            节点.__class__=冻结列表#就地换成冻结列表
        if isinstance(节点,list):#列表子节点
            下标=len(节点)-1#逆序压栈
            while 下标>=0:#尚未压完
                待处理.append({'kind':'property','source':节点,'key':下标})#稍后取出该元素
                下标-=1#前一元素
        elif isinstance(节点,dict):#映射子节点
            键列表=list(节点.keys())#自有可枚举键
            下标=len(键列表)-1#逆序压栈
            while 下标>=0:#尚未压完
                待处理.append({'kind':'property','source':节点,'key':键列表[下标]})#稍后取出该属性
                下标-=1#前一键
    return 值#返回已冻结的同一值

def 结构化克隆(值,引用表=None):#拆离可结构化克隆的映射或列表
    """拆离一份可结构化克隆的映射或列表。"""
    if 引用表 is None:#首次调用
        引用表={}#环引用表
    if 值 is None or isinstance(值,(str,int,float,bool)):#原语原样
        return 值#原语原样
    编号=id(值)#对象身份
    if 编号 in 引用表:#环则复用
        return 引用表[编号]#环则复用
    if isinstance(值,dict):#映射
        结果={}#新映射
        引用表[编号]=结果#登记
        for 键 in 值:#逐字段
            结果[键]=结构化克隆(值[键],引用表)#克隆字段
        return 结果#克隆映射
    if isinstance(值,list):#列表
        结果=[]#新列表
        引用表[编号]=结果#登记
        for 项 in 值:#逐元素
            结果.append(结构化克隆(项,引用表))#克隆元素
        return 结果#克隆列表
    return 值#其余共享
