"""持久命令事件词汇表以及注册表的 Cordis 事件声明，与仅类型消费方共享。客户端安全：这里碰不到仅 Host 的符号，因此 Client 编译面读到的 commands/change 签名与 Host 发出的相同。"""
from .品牌 import 命令标识#再导出命令配对 id 品牌

命令输入描述字段=('hint',)#命令可选非结构化输入的不可变元数据：用户尚未给出自由输入时显示的占位

命令结果种类=('success','error')#成功或失败判别标签

命令成功结果字段=('kind','text','sourceEventSeq')#成功：kind=success；可选 text；可选更早的权威域事件序号

命令失败结果字段=('kind','text')#失败：kind=error 且带非空错误文本

命令执行字段=('commandId','result')#已结算执行：生命周期配对 id 加归一化结果

命令描述字段=('name','description','input')#返回给 UI 适配器的无处理函数不可变命令视图

命令来源映射=('user',)#命令来源映射：今天唯一变体是人类 UI 派发

命令来源=('user',)#CommandSourceMap 上的联合——谁发出了命令行

命令运行载荷字段=('commandId','name','args','source')#command/run：仅日志；按 commandId 与 done 配对；recordInput false 时无 args

命令完成载荷字段=('commandId','kind','text','sourceEventSeq')#command/done：结算种类、可选文本、成功时可带权威序号
