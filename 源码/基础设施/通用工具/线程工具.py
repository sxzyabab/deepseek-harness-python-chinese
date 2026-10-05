from threading import Thread as 线程类#线程类
__all__=['启动守护线程']#仅中文公开名

def 启动守护线程(目标函数,*位置参数,**关键字参数)->线程类:
    '在守护线程中立即运行函数，进程退出时不等待它；返回线程对象'
    线程=线程类(target=目标函数,args=位置参数,kwargs=关键字参数,daemon=True)#创建守护线程
    线程.start()#立即启动
    return 线程#返回线程对象，调用方需要时可等待
