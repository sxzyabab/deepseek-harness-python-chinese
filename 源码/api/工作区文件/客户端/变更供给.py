"""每 Session 一条宿主 `changes` 订阅，扇出到该 Session 已打开的文件。

宿主在一条流上报告 Session 内每次 Agent 写入；每个打开文件只要自己的。
首个跟随者到达时打开 Session 流，末个离开时拆除；跟随者在 `stat` 给出宿主绝对路径前缓冲，
随后按该路径过滤（`\\` 归一为 `/`）。
"""
import json#断言帧
import threading#唤醒与结算
from concurrent.futures import Future as 原生结果#就绪与拆除
from ..类型 import 已中止,远程错误#中止查询与包异常

__all__=['变更供给']#仅中文公开名


def _路径键(路径):
    """宿主绝对路径的跟随键：反斜杠归一为斜杠。"""
    return 路径.replace('\\','/')#归一


class _跟随者:
    """一个跟随者的有序通知；由消费方拉取。"""

    def __init__(自身,离开):
        """记下注销回调。"""
        自身._离开=离开#注销
        自身._待发=[]#待发 (key, notice)
        自身._事件=threading.Event()#唤醒
        自身._已结束=False
        自身._宿主键=None#绑定后的绝对路径键
        自身._就绪结果=原生结果()#ready：True 已确认 / False 提前结束

    def 绑定(自身,绝对路径):
        """选定排队与后续变更所用的宿主路径。"""
        自身._宿主键=_路径键(绝对路径)#绑定

    def 启动(自身):
        """宿主已确认订阅并解析工作区根。"""
        if not 自身._就绪结果.done():#尚未结算
            自身._就绪结果.set_result(True)#就绪

    def 推(自身,通知,键):
        """排队一则通知。键为变更的归一路径。"""
        自身._待发.append({'key':键,'notice':通知})#入队
        自身._事件.set()#唤醒

    def 结束(自身):
        """交付已排队者后结束。"""
        自身._已结束=True#标记
        if not 自身._就绪结果.done():#未就绪
            自身._就绪结果.set_result(False)#失败就绪
        自身._事件.set()#唤醒

    def 拆除(自身):
        """即使消费方尚未拉取也注销。"""
        自身._离开()#离开

    def 就绪(自身):
        """阻塞至宿主确认订阅，或本跟随者在确认前结束。返回 bool。"""
        return 自身._就绪结果.result()#True/False

    def __iter__(自身):
        """产出通知直至结束。"""
        try:
            while True:#拉取
                if len(自身._待发)>0:#有待发
                    下一条=自身._待发.pop(0)#取头
                    键=下一条['key']#路径键
                    if 自身._宿主键 is None or 键==自身._宿主键:#匹配或尚未绑定
                        yield 下一条['notice']#通知
                    continue#下一条
                if 自身._已结束:
                    return#停
                自身._事件.clear()#清
                if len(自身._待发)>0 or 自身._已结束:#竞态
                    continue#重试
                自身._事件.wait(0.05)#短等
        finally:
            自身.拆除()#注销


class _会话供给:
    """一个 Session 的流与跟随者。"""

    def __init__(自身,远程,会话标识,前任,关闭后):
        """打开监督流；前任拆除完成后再开物理代。远程为本包 Remote 面。"""
        自身._跟随者集合=set()#跟随者
        自身._已关闭=False#关闭
        自身._已启动=False#收到 ready
        自身._关闭后=关闭后#关闭回调
        自身._拆除结果=原生结果()#dispose 结算

        def 打开(信号):
            """等前任后打开宿主 changes。"""
            自身._已启动=False#新代
            if 前任 is not None:#有前任
                try:
                    前任.等待()#等拆除
                except BaseException:
                    pass#拆除失败仍视为已结
            return 远程.workspaceFiles.changes(会话标识,信号)#物理代

        def 已结束(_已接受):
            """正常结束：Session 或宿主关闭，无可重开。"""
            return Exception('workspace file changes of '+str(会话标识)+' ended')#终态

        开流=getattr(远程,'$stream')#监督流工厂
        自身._流=开流({#监督流
            'name':'workspace file changes of '+str(会话标识),#诊断名
            'open':打开,#开代
            'ended':已结束,#终态分类
        })#流
        线=threading.Thread(target=自身._泵,daemon=True,name='dsh-workspace-files-feed')#泵线程
        线.start()

    def 加入(自身,跟随者):
        """在宿主路径已知前登记跟随者。"""
        自身._跟随者集合.add(跟随者)#登记
        if 自身._已启动:#已 ready
            跟随者.启动()#立刻就绪

    def 移除(自身,跟随者):
        """注销；末个离开则拆除流。"""
        自身._跟随者集合.discard(跟随者)#移除
        if len(自身._跟随者集合)==0:#空
            自身.关闭()#拆流

    def _泵(自身):
        """消费监督流帧。"""
        try:
            for 项 in 自身._流:#逐项
                帧=项.value#帧（监督流项为本包约定对象面）
                种类=帧['kind']#kind；帧为跨线 dict
                if 种类=='ready':#就绪
                    项.accept()#标记健康
                    自身._已启动=True#已启动
                    for 跟随者 in list(自身._跟随者集合):#通知
                        跟随者.启动()#就绪
                elif 种类=='change':#变更
                    变更=帧['change']#变更
                    键=_路径键(变更['absolutePath'])#键
                    通知=_编辑于(变更)#通知
                    for 跟随者 in list(自身._跟随者集合):#扇出
                        跟随者.推(通知,键)#推
                else:#未知
                    raise 远程错误('gateway/internal','Unexpected workspace file watch frame: '+json.dumps(帧,ensure_ascii=False,separators=(',',':'),allow_nan=False),{})#拒绝
        except BaseException:
            pass#终态失败：跟随者在下方安静结束，元数据保留最后已知
        finally:
            自身.关闭()#关闭

    def 关闭(自身):
        """拆除流并结束跟随者。"""
        if 自身._已关闭:#已关
            return#停
        自身._已关闭=True#标记
        关闭任务=_包装拆除(自身._流.dispose)#包装 dispose
        for 跟随者 in list(自身._跟随者集合):
            跟随者.结束()
        自身._跟随者集合.clear()#清空
        自身._关闭后(关闭任务)#通知供给
        if not 自身._拆除结果.done():#本对象
            自身._拆除结果.set_result(None)#结算


def _包装拆除(拆除):
    """把 dispose 收成带 等待 的任务。dispose 翻译时已是同步阻塞。"""
    任务=_可等待()#任务
    def 后台拆除():
        """执行拆除。"""
        try:
            拆除()#同步拆除
            任务.兑现()#成功
        except BaseException as 错误:
            任务.拒绝(错误)
    线=threading.Thread(target=后台拆除,daemon=True)#后台
    线.start()
    return 任务#任务


class _可等待:
    """只留 等待 的 Future 包装。"""

    def __init__(自身):
        """未决。"""
        自身._未来=原生结果()#底层

    def 兑现(自身,值=None):
        """成功。"""
        if not 自身._未来.done():#未结
            自身._未来.set_result(值)#写入

    def 拒绝(自身,错误):
        """失败。"""
        if not 自身._未来.done():#未结
            自身._未来.set_exception(错误 if isinstance(错误,BaseException) else Exception(str(错误)))#拒绝

    def 等待(自身,超时=None):
        """阻塞至结算。"""
        return 自身._未来.result(timeout=超时)#结果


def _编辑于(变更):
    """宿主帧对应的写入通知。变更为 dict。"""
    if 'absent' in 变更:#消失
        return {'kind':'absent'}#缺失
    return {'kind':'changed','version':变更['version']}#版本


class 变更供给:
    """按 Session 扇出宿主工作区文件变更流。提供方持有；一个实例服务客户端全部 Session。"""

    def __init__(自身,远程):
        """记下 Remote 面。"""
        自身._远程=远程#Remote
        自身._会话表={}#会话 → 供给
        自身._关闭中={}#会话 → 可等待拆除

    def 跟随(自身,会话标识,信号):
        """在宿主路径已知前跟随。

        调用时即登记，非首次拉取。stat 挂起期间变更排队。
        先 `就绪()` 为真再 stat，再 `绑定` 每次 stat 的绝对路径。
        """
        if 已中止(信号):#已取消
            跟随者=_跟随者(lambda:None)#空离开
            跟随者.结束()#立刻结束
            return 跟随者#空订阅
        供给=自身._供给于(会话标识)#取供给
        完成=threading.Event()#寿命结束
        盒={'跟随者':None}#回填

        def 离开():
            """幂等注销。"""
            if 完成.is_set():#已离开
                return#停
            完成.set()#标记
            跟随者=盒['跟随者']#跟随者
            if 跟随者 is None:#尚未建
                return#停
            跟随者.结束()#结束通知
            供给.移除(跟随者)#从供给移除

        跟随者=_跟随者(离开)#新建
        盒['跟随者']=跟随者#回填
        供给.加入(跟随者)#登记

        def 盯中止():
            """信号置位则离开；跟随者结束后退出。"""
            while not 完成.is_set():#仍活跃
                if 信号.wait(0.05):#已中止
                    离开()#注销
                    return#停

        线=threading.Thread(target=盯中止,daemon=True,name='dsh-workspace-files-follow-abort')#盯中止
        线.start()
        return 跟随者#订阅

    def 结算(自身):
        """等待仍在关闭的流，使拆除不留下宿主流。"""
        for 任务 in list(自身._关闭中.values()):#逐个
            try:
                任务.等待()#等
            except BaseException:
                pass#继续

    def _供给于(自身,会话标识):
        """取或建 Session 供给。"""
        if 会话标识 in 自身._会话表:#已有
            return 自身._会话表[会话标识]#返回
        前任=自身._关闭中[会话标识] if 会话标识 in 自身._关闭中 else None#前任拆除

        def 关闭后(已关):
            """流消失时登记关闭中。"""
            自身._会话表.pop(会话标识,None)#摘活表
            追踪=_可等待()#追踪

            def 收尾():
                """拆除无论成败都算结清。"""
                try:
                    已关.等待()#等拆除
                except BaseException:
                    pass#吞
                if 会话标识 in 自身._关闭中 and 自身._关闭中[会话标识] is 追踪:#仍是自己
                    自身._关闭中.pop(会话标识,None)#摘
                追踪.兑现()#结

            线=threading.Thread(target=收尾,daemon=True)#收尾
            线.start()
            自身._关闭中[会话标识]=追踪#记下

        供给=_会话供给(自身._远程,会话标识,前任,关闭后)#新建
        自身._会话表[会话标识]=供给#挂上
        return 供给#供给
