"""`node:perf_hooks`：worker 自有的高分辨率时钟。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/perf_hooks.ts`。
"""
from ...未实现失败 import 未实现失败#未实现桩

__all__=['performance','PerformanceObserver','__esModule','default']#Node面

模块='node:perf_hooks'#模块名
performance=globals().get('performance')#共享performance
PerformanceObserver=未实现失败(模块,'PerformanceObserver')#观察器桩
__esModule=True#CJS互操作
default={'performance':performance,'PerformanceObserver':PerformanceObserver}#默认导出
