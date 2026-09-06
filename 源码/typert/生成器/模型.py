"""与编译器无关的 Typert 分析模型。

对齐上游 `typert/generator/src/model.ts`。公开面仅中文名；运行时以字典形状承载。
TypeScript 节点与 checker 对象只是抽取输入；代码输出消费本图。
"""

__all__=[#仅中文公开名
    '子类型节点标识列表','关键字类型名','类型运算符名','成员可见性','模型错误',
]#公开面结束

关键字类型名=frozenset([#普通源码声明中接受的关键字类型
    'any','bigint','boolean','never','number','object',
    'string','symbol','undefined','unknown','void',
])#结束

类型运算符名=frozenset(['keyof','readonly','unique'])#类型前缀运算符

成员可见性=frozenset(['public','protected','private'])#类成员可见性

class 模型错误(Exception):
    """未覆盖的类型图变体。"""

def 子类型节点标识列表(节点):
    """返回一个节点所拥有的直接类型表达式边的图内 id。节点是 dict。"""
    种类=节点['kind'] if 'kind' in 节点 else None#节点种类
    if 种类 in ('parenthesized','operator'):#括号或运算符
        return [节点['type'] if 'type' in 节点 else None]#作用的类型
    if 种类=='reference':#具名引用
        return list(节点['arguments'] if 'arguments' in 节点 and 节点['arguments'] is not None else [])#类型实参
    if 种类 in ('union','intersection'):#联合或交叉
        return list(节点['types'] if 'types' in 节点 and 节点['types'] is not None else [])#成员类型
    if 种类=='array':#数组
        return [节点['element'] if 'element' in 节点 else None]#元素
    if 种类=='tuple':#元组
        元素列表=节点['elements'] if 'elements' in 节点 and 节点['elements'] is not None else []#元素
        return [元素['type'] if 'type' in 元素 else None for 元素 in 元素列表]#元素类型
    if 种类=='indexed-access':#索引访问
        return [节点['object'] if 'object' in 节点 else None,节点['index'] if 'index' in 节点 else None]#对象与索引
    if 种类=='conditional':#条件类型
        return [#四元
            节点['check'] if 'check' in 节点 else None,
            节点['extends'] if 'extends' in 节点 else None,
            节点['whenTrue'] if 'whenTrue' in 节点 else None,
            节点['whenFalse'] if 'whenFalse' in 节点 else None,
        ]#四元结束
    if 种类=='mapped':#映射类型
        参数=节点['parameter'] if 'parameter' in 节点 and 节点['parameter'] is not None else {}#映射参数
        结果=[]#边
        if 'constraint' in 参数 and 参数['constraint'] is not None:#参数约束
            结果.append(参数['constraint'])#约束
        if 'default' in 参数 and 参数['default'] is not None:#参数缺省
            结果.append(参数['default'])#缺省
        if 'nameType' in 节点 and 节点['nameType'] is not None:#重映射名
            结果.append(节点['nameType'])#名
        if 'value' in 节点 and 节点['value'] is not None:#值类型
            结果.append(节点['value'])#值
        return 结果#边
    if 种类=='template-literal':#模板字面量类型
        跨列表=节点['spans'] if 'spans' in 节点 and 节点['spans'] is not None else []#跨
        return [跨['type'] if 'type' in 跨 else None for 跨 in 跨列表]#插值类型
    if 种类 in ('type-query','import-type'):#typeof / import()
        return list(节点['arguments'] if 'arguments' in 节点 and 节点['arguments'] is not None else [])#类型实参
    if 种类=='predicate':#类型判断
        类型=节点['type'] if 'type' in 节点 else None#判断目标
        return [] if 类型 is None else [类型]#有则一条
    if 种类=='infer':#infer
        参数=节点['parameter'] if 'parameter' in 节点 and 节点['parameter'] is not None else {}#infer 参数
        结果=[]#边
        if 'constraint' in 参数 and 参数['constraint'] is not None:#约束
            结果.append(参数['constraint'])#约束
        if 'default' in 参数 and 参数['default'] is not None:#缺省
            结果.append(参数['default'])#缺省
        return 结果#边
    if 种类 in ('keyword','literal','object','function','constructor','this'):#叶子或另走成员/签名
        return []#无子类型边
    raise 模型错误('unsupported model variant '+repr(节点))#未覆盖变体
