"""预览的异步半边：把页读进存储。

对齐上游 `ui-sidebar-textpreview/src/client/face.ts`。公开面仅中文名。
组件从不阻塞等待。它请求一页，本面执行读取并把结果经存储动作写回——
槽位标准的 `inject` 形，写集合仍是存储的。读取所在会话来自文件地址，不是槽位会话：
地址是读取的全部权威。

一 tab 的页是同一文件版本从首行走下来的。丢掉它们——重载，或越过首行到达的
更新版本页（会重启行走）——作废该 tab 仍在飞的读取：丢弃前的结算不写。
清理骑在拥有方 `signal` 上，由首次读取挂一次：中止忘掉桶与本账本；
已结束的记录不再发请求；记录消失后到达的结算无写处。从未读过的 tab 无桶可忘。

AbortSignal 译为 threading.Event；TS 的 fire-and-forget then 译为守护线程。
"""
import threading#读页线程与中止监视

__all__=['已中止','文本面']#仅中文公开名


def 已中止(信号):
    """信号是否已中止。无信号视为未中止。信号为 threading.Event。"""
    if 信号 is None:#无
        return False#未中止
    return 信号.is_set()#Event 置位


def 文本面(读取):
    """把预览面绑到一份分页读。

    读取为 (会话标识, 路径, 偏移, 信号) → RemoteResult dict。
    返回槽位 `inject` 工厂：会话标识与已绑定动作进，注入面出。
    槽位会话标识不用，因为地址自带会话。
    """

    def 工厂(_会话标识,动作):
        """构造 loadPage / reloadPages。"""
        标签表={}#标签标识 → {generation, version}

        def 读取账(标签标识,信号):
            """取或建一 tab 的读取账；首次时挂中止监听忘掉桶。"""
            if 标签标识 in 标签表:#已有
                return 标签表[标签标识]#复用
            新建={'generation':0,'version':None}#初账
            标签表[标签标识]=新建#挂上

            def 盯中止():
                """信号置位则清账并遗忘桶。"""
                while not 已中止(信号):#未中止
                    信号.wait(0.05)#短等
                if 标签标识 in 标签表:#仍有账
                    del 标签表[标签标识]#忘掉账
                动作['forget'](标签标识)#忘掉桶

            if 已中止(信号):#已结束则立刻遗忘
                if 标签标识 in 标签表:#有账
                    del 标签表[标签标识]#清
                动作['forget'](标签标识)#忘
            else:#监视一次
                线=threading.Thread(target=盯中止,daemon=True,name='dsh-sidebar-textpreview-abort')#盯中止
                线.start()#启动
            return 新建#账

        def 加载页(标签标识,文件,偏移,信号):
            """把一页读进存储；已中止则不发。"""
            if 已中止(信号):#记录已结束
                return#停
            账=读取账(标签标识,信号)#账
            代次=账['generation']#本代
            动作['loading'](标签标识)#先标在飞

            def 结算():
                """后台读页；代次失配或已中止则不写。"""
                结果=读取(文件['sessionId'],文件['path'],偏移,信号)#同步读
                if 已中止(信号) or 标签标识 not in 标签表 or 标签表[标签标识]['generation']!=代次:#过期
                    return#丢弃
                if not 结果['ok']:#失败
                    动作['failed'](标签标识,结果['error'])#记下失败
                    return#停
                值=结果['value']#页
                持有版本=账['version']#当前持有版本
                # 两版本的页永不相遇：越过首行的更新文件从第 1 行重启行走
                if 偏移!=1 and 持有版本 is not None and 值['version']!=持有版本:#版本变且非首行
                    重启(标签标识,文件,信号)#重启
                    return#停
                账['version']=值['version']#挂版本
                动作['page'](标签标识,值)#收下页

            线=threading.Thread(target=结算,daemon=True,name='dsh-sidebar-textpreview-read')#守护线程
            线.start()#启动

        def 重启(标签标识,文件,信号):
            """丢掉全部页并再读第一页（宿主报告变更时）。视图保留。"""
            if 已中止(信号):#已结束
                return#停
            账=读取账(标签标识,信号)#账
            账['generation']=账['generation']+1#推进代次
            账['version']=None#清版本
            动作['reset'](标签标识)#清页
            加载页(标签标识,文件,1,信号)#从首行

        return {#注入面
            'loadPage':加载页,#读一页
            'reloadPages':重启,#重载
        }#面结束

    return 工厂#inject 工厂
