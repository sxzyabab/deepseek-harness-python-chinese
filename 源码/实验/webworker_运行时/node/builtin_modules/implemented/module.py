from ...未实现失败 import 运行时错误
from ....module_system.模块加载器 import 要求活动模块加载器

__all__=[
    'createRequire','builtinModules','isBuiltin','stripTypeScriptTypes','register',
    'syncBuiltinESMExports','__esModule','default',
]

def 创建要求(基址):
    """构建绑定到基路径或文件 URL 的 `require`。"""
    return 要求活动模块加载器().创建require(基址)

builtinModules=[
    'assert','async_hooks','buffer','child_process','crypto','events','fs','http','module',
    'net','os','path','process','stream','tty','url','util','worker_threads',
]

def 是否内置(说明符):
    """说明符是否命名 Node 内置。"""
    名=说明符[5:] if 说明符.startswith('node:') else 说明符
    return 名 in builtinModules

def 剥离类型脚本类型(*位置参数,**关键字参数):
    """TypeScript 剥离是 Node 22+ 加载器特性，worker 无对应物。"""
    raise 运行时错误('web-preview: worker 宿主里没有 node:module.stripTypeScriptTypes')

def 注册(*位置参数,**关键字参数):
    """此处加载器钩子无意义：worker 加载器拥有解析。"""
    raise 运行时错误('web-preview: worker 宿主里没有 node:module.register')

def 同步内置ESM导出():
    """worker 加载器只物化 CommonJS。"""
    pass

createRequire=创建要求
isBuiltin=是否内置
stripTypeScriptTypes=剥离类型脚本类型
register=注册
syncBuiltinESMExports=同步内置ESM导出
__esModule=True
default={
    'createRequire':创建要求,'builtinModules':builtinModules,'isBuiltin':是否内置,
    'register':注册,'syncBuiltinESMExports':同步内置ESM导出,'stripTypeScriptTypes':剥离类型脚本类型,
}
