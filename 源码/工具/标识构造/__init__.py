__all__=['标识构造']#仅中文公开名

# 上游 TypeScript 用 declare const BRAND: unique symbol 做编译期唯一标识符号，运行时擦除；Python 无等价符号，仅保留名义约定。

def 标识构造(原始):#把字符串打成携带仅编译期标识的名义类型，不做校验
    """携带仅编译期标识的字符串。原始不透明 id 原样返回；零运行时成本。"""
    return 原始#原样返回，编译期标识在 Python 中无运行时成本
