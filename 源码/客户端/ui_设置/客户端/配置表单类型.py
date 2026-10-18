'配置表单的同步快照与写入面。状态字保持 loading、ready、unavailable。快照字段是 status、value、base、user、revision、writable。'

__all__=['加载中','就绪','不可用']

加载中='loading'#还没有接受过的节
就绪='ready'#有一份接受过的节
不可用='unavailable'#这个命名空间没有暴露给本客户端
