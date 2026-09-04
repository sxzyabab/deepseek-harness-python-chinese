"""worker 侧的 `node:module`：`createRequire` 交出 worker 模块加载器的同步 require。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/module.ts`。
公开面中文名；Node 面经别名与 default 暴露英文名。
"""
from ....module_system.模块加载器 import 要求活动模块加载器#导入加载器

__all__=[#中文公开名与Node英文挂名
    '创建要求','是否内置','剥离类型脚本类型','注册','同步内置ESM导出',
    'createRequire','builtinModules','isBuiltin','stripTypeScriptTypes','register',
    'syncBuiltinESMExports','__esModule','default',
]#公开结束

def 创建要求(基址):#创建绑定require
    """构建绑定到基路径或文件 URL 的 `require`。"""
    return 要求活动模块加载器().创建require(基址)#委托活动加载器

builtinModules=[#内置模块名清单
    'assert','async_hooks','buffer','child_process','crypto','events','fs','http','module',#一批内置
    'net','os','path','process','stream','tty','url','util','worker_threads',#续一批
]#builtinModules结束

def 是否内置(说明符):#判定是否内置
    """说明符是否命名 Node 内置。"""
    名=说明符[5:] if 说明符.startswith('node:') else 说明符#去前缀
    return 名 in builtinModules#查表

def 剥离类型脚本类型(*位置参数,**关键字参数):#TS剥离不可用
    """TypeScript 剥离是 Node 22+ 加载器特性，worker 无对应物。"""
    raise Exception('web-preview: node:module.stripTypeScriptTypes is not available in the worker host')#抛不可用

def 注册(*位置参数,**关键字参数):#注册钩子不可用
    """此处加载器钩子无意义：worker 加载器拥有解析。"""
    raise Exception('web-preview: node:module.register is not available in the worker host')#抛不可用

def 同步内置ESM导出():#ESM导出同步空操作
    """worker 加载器只物化 CommonJS。"""
    pass#无需同步

createRequire=创建要求#Node面
isBuiltin=是否内置#Node面
stripTypeScriptTypes=剥离类型脚本类型#Node面
register=注册#Node面
syncBuiltinESMExports=同步内置ESM导出#Node面
__esModule=True#CJS互操作标记
default={#默认导出成员
    'createRequire':创建要求,'builtinModules':builtinModules,'isBuiltin':是否内置,#模块面
    'register':注册,'syncBuiltinESMExports':同步内置ESM导出,'stripTypeScriptTypes':剥离类型脚本类型,#其余
}#默认导出结束
