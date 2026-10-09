运算符至特殊方法映射={
    ###正负数###
    #+a
    '+a':'__pos__',
    '+x':'__pos__',
    '取正':'__pos__',
    #-a
    '-a':'__neg__',
    '-x':'__neg__',
    '取负':'__neg__',

    ###二元算术###
    #a + b
    '+':'__add__',
    '加':'__add__',
    #a - b
    '-':'__sub__',
    '减':'__sub__',
    #a * b
    '*':'__mul__',
    '乘':'__mul__',
    #a / b
    '/':'__truediv__',
    '真除':'__truediv__',
    #a // b
    '//':'__floordiv__',
    '整除':'__floordiv__',
    #a % b
    '%':'__mod__',
    '取模':'__mod__',
    #a ** b
    '**':'__pow__',
    '幂':'__pow__',
    #a @ b
    '@':'__matmul__',
    '矩阵乘':'__matmul__',

    ###位运算###
    #~a
    '~':'__invert__',
    '按位取反':'__invert__',
    #a << b
    '<<':'__lshift__',
    '左移':'__lshift__',
    #a >> b
    '>>':'__rshift__',
    '右移':'__rshift__',
    #a & b
    '&':'__and__',
    '按位与':'__and__',
    #a | b
    '|':'__or__',
    '按位或':'__or__',
    #a ^ b
    '^':'__xor__',
    '按位异或':'__xor__',

    ###赋值运算###
    #a += b
    '+=':'__iadd__',
    '就地加':'__iadd__',
    #a -= b
    '-=':'__isub__',
    '就地减':'__isub__',
    #a *= b
    '*=':'__imul__',
    '就地乘':'__imul__',
    #a /= b
    '/=':'__itruediv__',
    '就地除':'__itruediv__',
    #a //= b
    '//=':'__ifloordiv__',
    '就地整除':'__ifloordiv__',
    #a %= b
    '%=':'__imod__',
    '就地取模':'__imod__',
    #a **= b
    '**=':'__ipow__',
    '就地幂':'__ipow__',
    #a @= b
    '@=':'__imatmul__',
    '就地矩阵乘':'__imatmul__',
    #a <<= b
    '<<=':'__ilshift__',
    '就地左移':'__ilshift__',
    #a >>= b
    '>>=':'__irshift__',
    '就地右移':'__irshift__',
    #a &= b
    '&=':'__iand__',
    '就地与':'__iand__',
    #a |= b
    '|=':'__ior__',
    '就地或':'__ior__',
    #a ^= b
    '^=':'__ixor__',
    '就地异或':'__ixor__',
    #a &= b
    '就地与':'__iand__',

    ###比较###
    #a == b
    '==':'__eq__',
    '等于':'__eq__',
    #a != b
    '!=':'__ne__',
    '不等':'__ne__',
    #a < b
    '<':'__lt__',
    '小于':'__lt__',
    #a <= b
    '<=':'__le__',
    '小于等于':'__le__',
    #a > b
    '>':'__gt__',
    '大于':'__gt__',
    #a >= b
    '>=':'__ge__',
    '大于等于':'__ge__',

    ###反射算术（左操作不支持时，由右操作数接管，如 3 + a）
    #b + a
    'r+':'__radd__',
    '反射加':'__radd__',
    #b - a
    'r-':'__rsub__',
    '反射减':'__rsub__',
    #b * a
    'r*':'__rmul__',
    '反射乘':'__rmul__',
    #b / a
    'r/':'__rtruediv__',
    '反射除':'__rtruediv__',
    #b // a
    'r//':'__rfloordiv__',
    '反射整除':'__rfloordiv__',
    #b % a
    'r%':'__rmod__',
    '反射取模':'__rmod__',
    #b ** a
    'r**':'__rpow__',
    '反射幂':'__rpow__',
    #b @ a
    'r@':'__rmatmul__',
    '反射矩阵乘':'__rmatmul__',
    #b << a
    'r<<':'__rlshift__',
    '反射左移':'__rlshift__',
    #b >> a
    'r>>':'__rrshift__',
    '反射右移':'__rrshift__',
    #b & a
    'r&':'__rand__',
    '反射与':'__rand__',
    #b | a
    'r|':'__ror__',
    '反射或':'__ror__',
    #b ^ a
    'r^':'__rxor__',
    '反射异或':'__rxor__',

    ###容器类###
    #item in container
    'in':'__contains__',
    '成员检测':'__contains__',
    #container[key]
    '[]':'__getitem__',
    '取值':'__getitem__',
    #container[key] = value
    '[]=':'__setitem__',
    '写值':'__setitem__',
    #del container[key]
    'del[]':'__delitem__',
    '删值':'__delitem__',

    ###可调用###
    #function(...)
    '()':'__call__',
    '调用':'__call__',

    ###内置函数钩子###
    #divmod(value, divisor)
    'divmod':'__divmod__',
    '求商余':'__divmod__',
    #abs(value)
    'abs':'__abs__',
    '求绝对值':'__abs__',
    #len(container)
    'len':'__len__',
    '长度':'__len__',
    #bool(value)
    'bool':'__bool__',
    '转布尔值':'__bool__',
    #iter(iterable) / for item in iterable
    'iter':'__iter__',
    '迭代':'__iter__',
    #hash(value)
    'hash':'__hash__',
    '哈希':'__hash__',
    #iterable[index]、bin(value) 等前置的对象转整数步骤
    'index':'__index__',
    '索引':'__index__',
    #reversed(iterable)
    'reversed':'__reversed__',
    '反向迭代':'__reversed__',

    ###字符串与表示###
    #repr(value)
    'repr':'__repr__',
    '官方表示':'__repr__',
    #str(value)
    'str':'__str__',
    '转字符串':'__str__',

    ###类型转换###
    #int(a)
    'int':'__int__',
    '转整数':'__int__',
    #float(a)
    'float':'__float__',
    '转浮点数':'__float__',
    #complex(a)
    'complex':'__complex__',
    '转复数':'__complex__',

    ###数值取整###
    #round(a,n)
    'round':'__round__',
    '四舍五入':'__round__',
    #math.trunc(a)
    'trunc':'__trunc__',
    '取整':'__trunc__',
    #math.floor(a)
    'floor':'__floor__',
    '向下取整':'__floor__',
    #math.ceil(a)
    'ceil':'__ceil__',
    '向上取整':'__ceil__',

    ###上下文管理器###
    #with a as x
    'enter':'__enter__',
    '进入上下文':'__enter__',
    #离开 with 块
    'exit':'__exit__',
    '退出上下文':'__exit__',
}


def 重载运算符(运算符:str):
    '对类中的函数装饰,将指定运算符的操作转发至被装饰的函数'
    if 运算符 not in 运算符至特殊方法映射:
        raise ValueError(f'不支持的运算符：{运算符!r}')
    重载方法名=运算符至特殊方法映射[运算符]
    def 装饰器(函数):
        try:
            raise Exception
        except Exception as 异常:
            类命名空间=异常.__traceback__.tb_frame.f_back.f_locals
        类命名空间[重载方法名]=函数
        return 函数
    return 装饰器