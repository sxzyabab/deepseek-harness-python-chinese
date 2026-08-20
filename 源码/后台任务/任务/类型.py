"""任务生产者、注册表与控制器共享的类型。服务实现住在包根。"""
from .品牌 import 任务标识#再导出任务id品牌化

任务状态=('running','stopping','completed','killed','failed')#运行中、停止中、已完成、已杀死、已失败
任务种类映射={'bash':'bash','subagent':'subagent'}#生产者定义的任务种类；插件可扩展此映射
任务种类=('bash','subagent')#已注册生产者种类名联合
任务结局字段=('status','detail','output')#生产者经钩子.done提供的终态结果：做完/取消/失败，可选细节与最终输出
任务启动字段=('kind','label','outputLimitBytes','owner','run')#传给注册表.启动的生产者声明：种类、标签、可选输出上限、可选所有者、同步启动器
任务钩子字段=('cancel','done','readOutput')#运行时控制和观察生产者工作的钩子：取消、资源释放后结局、可选增量读取
任务快照字段=('id','kind','label','outputLimitBytes','ownerSession','status','detail','startedAt','finishedAt','reported')#只读投影，每次调用一份新对象
任务读取字段=('text','snapshot')#注册表.读取返回的输出文本与读后快照
任务完成监听器='JobDoneListener'#完成回调：(快照,精确所有者|None)->None|可等待
任务变化监听器='JobsChangedListener'#可见集合变化观察：(所有者|None)->None；None表示无主任务变了
