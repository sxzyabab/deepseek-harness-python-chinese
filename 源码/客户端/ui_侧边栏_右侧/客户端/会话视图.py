'一份侧栏视图自己的会话引用、保留的正文，以及已经挂上的次数'
from ...模块.客户端.通告 import 取握手窗口
from threading import Thread as 线程类

__all__=['侧栏会话视图']


class 侧栏会话视图:
    '自己持有会话引用，直到退役完成或插件关掉'

    def __init__(自身,会话标识,会话面,拆除时,标签释放时):
        '向会话面要一份独立引用'
        自身.会话标识=会话标识
        自身.拆除时=拆除时
        自身.标签释放时=标签释放时
        自身.引用=会话面.retain(会话标识,{'source':'sidebarView'})
        自身.标签表={}
        自身.挂载数=0
        自身.已退役=False
        自身.已拆除=False

        def 等打开():
            '打开失败只记到控制台，不挡住视图'
            try:
                自身.引用.ready
            except Exception as 错误:
                取握手窗口().console.error('Sidebar Session opening failed:',错误)

        线程类(target=等打开,daemon=True).start()

    @property
    def 有保留标签(自身):
        '还有正文需要这份视图'
        return len(自身.标签表)>0

    def 挂载(自身):
        '提交的根挂上一次。最后一次卸载才释放已退役的视图'
        自身.挂载数+=1

        def 卸下():
            '这一次挂载结束'
            自身.挂载数-=1
            if 自身.已退役 and 自身.挂载数==0:
                自身.拆除()

        return 卸下

    def 保留标签(自身,标签标识,信号):
        '正文挂着就占一份。信号中止或已经拆除则空释放'
        if 信号.aborted or 自身.已拆除:
            def 空释放():
                '没有占上'
                return None
            return 空释放
        自身.标签表[标签标识]=自身.标签表.get(标签标识,0)+1
        还占着=[True]

        def 释放():
            '这具正文松手。松第二次没有事'
            if not 还占着[0]:
                return
            还占着[0]=False
            信号.removeEventListener('abort',释放)
            次数=自身.标签表[标签标识]
            if 次数==1:
                del 自身.标签表[标签标识]
            else:
                自身.标签表[标签标识]=次数-1
            自身.标签释放时(自身)

        信号.addEventListener('abort',释放,{'once':True})
        return 释放

    def 退役(自身):
        '撤出视图。已经没有挂载就立刻释放引用'
        自身.已退役=True
        if 自身.挂载数==0:
            自身.拆除()

    def 拆除(自身):
        '只释放一次'
        if 自身.已拆除:
            return
        自身.已拆除=True
        自身.已退役=True
        自身.拆除时(自身)
        自身.引用.release()
