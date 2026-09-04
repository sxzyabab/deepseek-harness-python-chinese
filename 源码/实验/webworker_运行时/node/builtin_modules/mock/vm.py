"""`node:vm` 桩。在独立 realm 中编译脚本无浏览器对应物；
自修改与工作流行可挂载，在尝试编译时报告缺口。

对齐上游 `webworker-runtime/src/node/builtin_modules/mock/vm.ts`。
"""
from ...未实现失败 import 未实现失败#导入未实现桩

__all__=[#Node面
    'Script','createContext','runInContext','runInNewContext','runInThisContext','isContext',
    '__esModule','default',
]#公开结束

模块='node:vm'#模块说明符
Script=未实现失败(模块,'Script')#Script拒绝桩
createContext=未实现失败(模块,'createContext')#createContext拒绝桩
runInContext=未实现失败(模块,'runInContext')#runInContext拒绝桩
runInNewContext=未实现失败(模块,'runInNewContext')#runInNewContext拒绝桩
runInThisContext=未实现失败(模块,'runInThisContext')#runInThisContext拒绝桩
isContext=未实现失败(模块,'isContext')#isContext拒绝桩
__esModule=True#CJS互操作标记

default={#默认导出成员
    'Script':Script,'createContext':createContext,'runInContext':runInContext,#求值
    'runInNewContext':runInNewContext,'runInThisContext':runInThisContext,'isContext':isContext,#上下文
}#默认导出结束
