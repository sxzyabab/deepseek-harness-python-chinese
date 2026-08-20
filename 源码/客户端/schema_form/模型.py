"""设置编辑器背后的 schema 内省与草稿编辑辅助。

序列化的 schemastery 信封（`schema.toJSON()`）再水合成活动校验器，编辑器探测其节点关系（`dict`/`inner`）以判断字段存在与角色；草稿按路径不可变编辑。

对齐上游 `schema-form/src/model.ts`。公开面仅中文名。
"""
from schemastery import 模式#导入 schemastery 校验器

__all__=[#仅中文公开名
    '模式节点',
    '再水合模式',
    '校验草稿',
    '路径上节点',
    '取路径',
    '有路径',
    '设路径',
    '删路径',
]#公开面结束

模式节点=模式#活动 schemastery 节点；渲染器只读其结构关系

def 再水合模式(序列化):#再水合序列化 schema
    """把序列化的 schema 信封再水合成活动校验器/节点树。"""
    return 模式(序列化)#用信封构造活动节点树

def 校验草稿(模式节点值,草稿):#校验草稿
    """用再水合后的 schema 校验一份草稿；通过返回 None，失败返回消息。"""
    try:#尝试把草稿喂给校验器
        模式节点值(草稿)#调用 schema 函数形态
        return None#通过则无失败消息
    except Exception as 错误:#校验抛错
        return str(错误)#取出失败消息

def 路径上节点(根,路径):#按路径解析节点
    """按设置路径解析 schema 节点；无法解析的段返回 None。"""
    节点=根#从根开始走
    for 键 in 路径:#逐段下降
        if 节点 is None:#中间断了就停
            return None#无法继续
        类型=getattr(节点,'type',None)#节点类型
        if 类型=='object':#对象按属性名取
            字典=getattr(节点,'dict',None)#属性表
            节点=None if 字典 is None else 字典.get(键)#取属性
        elif 类型=='dict' or 类型=='array':#dict/array 走 inner
            节点=getattr(节点,'inner',None)#内层节点
        else:#其它类型无法继续
            return None#停
    return 节点#返回落到的节点

def 取路径(值,路径):#按路径取值
    """按路径读取嵌套值；缺失分支为 None。"""
    当前=值#当前游标
    for 键 in 路径:#逐段下降
        if isinstance(当前,list):#数组按下标
            当前=当前[int(键)]#取该下标元素
            continue#进入下一段
        if not isinstance(当前,dict) or 当前 is None:#非对象无法继续
            return None#缺席
        当前=当前.get(键)#对象按键取
    return 当前#返回落到的值

def 有路径(值,路径):#判断路径是否显式存在
    """草稿是否显式携带该路径（存在标记用户覆盖，与存的值无关）。"""
    if len(路径)==0:#空路径看根是否有值
        return 值 is not None#根是否有值
    父=取路径(值,路径[:-1])#取末键的父
    键=路径[-1]#末段键
    if isinstance(父,list):#数组看下标是否在长度内
        return int(键)<len(父)#下标合法
    if not isinstance(父,dict) or 父 is None:#父不是对象则不存在
        return False#不存在
    return 键 in 父#对象看自有键

def 克隆容器(容器,键):#克隆或物化一层容器
    """克隆一层容器；缺失的中间层按下一键需要的形态物化。"""
    if isinstance(容器,list):#数组浅拷贝
        return list(容器)#拷贝
    if isinstance(容器,dict) and 容器 is not None:#对象浅拷贝
        return dict(容器)#拷贝
    if 键.isdigit():#数字键物化数组
        return []#空数组
    return {}#否则物化对象

def 克隆脊骨(根,路径):#克隆到叶子父的脊骨
    """把容器脊骨克隆到叶子父级，并物化缺失的中间层。"""
    结果=dict(根)#根浅拷贝
    目标=结果#当前写入层
    下标=0#走到叶子父
    while 下标<len(路径)-1:#尚未到叶子
        键=路径[下标]#本段键
        下一键=路径[下标+1]#下一键决定物化形态
        if isinstance(目标,list):#数组层
            子=克隆容器(目标[int(键)],下一键)#克隆或物化子
            目标[int(键)]=子#写下标
        else:#对象层
            子=克隆容器(目标.get(键),下一键)#克隆或物化子
            目标[键]=子#写键
        目标=子#下降到子层
        下标+=1#前进
    return 结果,目标,路径[-1]#根、父、叶子键

def 设路径(根,路径,值):#按路径不可变写入
    """不可变地设置嵌套值，并物化缺失的中间容器。"""
    if len(路径)==0:#空路径拒绝
        raise Exception('schema-form: setPath needs a non-empty path')#空路径拒绝
    结果,父,叶子=克隆脊骨(根,路径)#克隆到叶子父
    if isinstance(父,list):#数组写下标
        父[int(叶子)]=值#写下标
    else:#对象写键
        父[叶子]=值#写键
    return 结果#返回新根

def 删路径(根,路径):#按路径不可变删除
    """不可变地删除嵌套键；沿缺失分支删除则原样返回根。"""
    if len(路径)==0:#空路径拒绝
        raise Exception('schema-form: deletePath needs a non-empty path')#空路径拒绝
    if not 有路径(根,路径):#路径不存在则原样返回
        return 根#原样
    结果,父,叶子=克隆脊骨(根,路径)#克隆到叶子父
    if isinstance(父,list):#数组删下标
        del 父[int(叶子)]#删下标
    else:#对象删键
        del 父[叶子]#删键
    return 结果#返回新根
