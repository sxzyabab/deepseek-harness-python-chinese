"""`node:worker_threads` 桩。不支持嵌套 Worker，因此工作流与
code-runtime 插件体可挂载、在使用时失败。
线程身份值是真实的：它们表示「这是主线程」。

对齐上游 `webworker-runtime/src/node/builtin_modules/mock/worker_threads.ts`。
"""
from ...未实现失败 import 未实现失败#导入未实现桩

__all__=[#Node面
    'Worker','isMainThread','threadId','parentPort','workerData',
    'MessageChannel','MessagePort','markAsUntransferable','receiveMessageOnPort',
    '__esModule','default',
]#公开结束

模块='node:worker_threads'#模块说明符
Worker=未实现失败(模块,'Worker')#Worker拒绝桩
isMainThread=True#主线程标记
threadId=0#主线程id
parentPort=None#无父端口
workerData=None#无线程数据
MessageChannel=未实现失败(模块,'MessageChannel')#MessageChannel拒绝桩
MessagePort=未实现失败(模块,'MessagePort')#MessagePort拒绝桩
markAsUntransferable=未实现失败(模块,'markAsUntransferable')#不可转移标记桩
receiveMessageOnPort=未实现失败(模块,'receiveMessageOnPort')#端口收消息桩
__esModule=True#CJS互操作标记

default={#默认导出成员
    'Worker':Worker,'isMainThread':isMainThread,'threadId':threadId,#线程身份
    'parentPort':parentPort,'workerData':workerData,#端口与数据
    'MessageChannel':MessageChannel,'MessagePort':MessagePort,#构造
    'markAsUntransferable':markAsUntransferable,'receiveMessageOnPort':receiveMessageOnPort,#转移与收消息
}#默认导出结束
