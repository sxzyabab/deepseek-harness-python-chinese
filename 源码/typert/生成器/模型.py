"""与编译器无关的 Typert 分析模型。

对齐上游 `typert/generator/src/model.ts`。公开面仅中文名；运行时以字典形状承载。
TypeScript 节点与 checker 对象只是抽取输入；发射器消费本图。
"""

__all__=[#仅中文公开名
    '子类型节点标识们','childTypeNodeIds','取字段','关键字类型名','类型运算符名','成员可见性',
]#公开面结束

关键字类型名=frozenset([#普通源码声明中接受的关键字类型
    'any','bigint','boolean','never','number','object',
    'string','symbol','undefined','unknown','void',
])#结束

类型运算符名=frozenset(['keyof','readonly','unique'])#类型前缀运算符

成员可见性=frozenset(['public','protected','private'])#类成员可见性

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 子类型节点标识们(节点):#收集直接子类型节点 id
    """返回一个节点所拥有的直接类型表达式边的图内 id。"""
    种类=取字段(节点,'kind')#节点种类
    if 种类 in ('parenthesized','operator'):#括号或运算符
        return [取字段(节点,'type')]#作用的类型
    if 种类=='reference':#具名引用
        return list(取字段(节点,'arguments') or [])#类型实参
    if 种类 in ('union','intersection'):#联合或交叉
        return list(取字段(节点,'types') or [])#成员类型
    if 种类=='array':#数组
        return [取字段(节点,'element')]#元素
    if 种类=='tuple':#元组
        return [取字段(元素,'type') for 元素 in (取字段(节点,'elements') or [])]#元素类型
    if 种类=='indexed-access':#索引访问
        return [取字段(节点,'object'),取字段(节点,'index')]#对象与索引
    if 种类=='conditional':#条件类型
        return [取字段(节点,'check'),取字段(节点,'extends'),取字段(节点,'whenTrue'),取字段(节点,'whenFalse')]#四元
    if 种类=='mapped':#映射类型
        参数=取字段(节点,'parameter') or {}#映射参数
        结果=[]#边
        if 取字段(参数,'constraint') is not None:#参数约束
            结果.append(取字段(参数,'constraint'))#约束
        if 取字段(参数,'default') is not None:#参数缺省
            结果.append(取字段(参数,'default'))#缺省
        if 取字段(节点,'nameType') is not None:#重映射名
            结果.append(取字段(节点,'nameType'))#名
        if 取字段(节点,'value') is not None:#值类型
            结果.append(取字段(节点,'value'))#值
        return 结果#边
    if 种类=='template-literal':#模板字面量类型
        return [取字段(跨,'type') for 跨 in (取字段(节点,'spans') or [])]#插值类型
    if 种类 in ('type-query','import-type'):#typeof / import()
        return list(取字段(节点,'arguments') or [])#类型实参
    if 种类=='predicate':#类型谓词
        类型=取字段(节点,'type')#谓词目标
        return [] if 类型 is None else [类型]#有则一条
    if 种类=='infer':#infer
        参数=取字段(节点,'parameter') or {}#infer 参数
        结果=[]#边
        if 取字段(参数,'constraint') is not None:#约束
            结果.append(取字段(参数,'constraint'))#约束
        if 取字段(参数,'default') is not None:#缺省
            结果.append(取字段(参数,'default'))#缺省
        return 结果#边
    if 种类 in ('keyword','literal','object','function','constructor','this'):#叶子或另走成员/签名
        return []#无子类型边
    raise Exception('unsupported model variant '+repr(节点))#未覆盖变体

childTypeNodeIds=子类型节点标识们#上游名
