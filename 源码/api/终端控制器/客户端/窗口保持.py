"""一条可重连窗口保持，由终端的全部出现共享。

对齐上游 `terminal-controller/src/client/retention.ts`。公开面仅中文名。
"""
import threading#等待者
from ..类型 import 远程错误#不可用
from ...工具.超时 import 若已中止则抛出#中止

__all__=['终端窗口保持']#仅中文公开名

class 终端窗口保持:
    """流确认门控每个物理连接的输出附着。"""

    def __init__(自身,网关,远程,会话标识,终端标识):
        """打开保持流并开始消费。"""
        自身._等待者=set()#等待者
        自身._代际=None#当前信号
        自身._失败=None#失败
        自身._流=网关['$stream']({#打开流
            'name':'Browser terminal window hold',#名称
            'open':lambda 信号:远程.retain(会话标识,终端标识,信号),#打开
            'ended':lambda:远程错误('terminal/unavailable','Terminal hold ended',{}),#结束
        })
        线=threading.Thread(target=自身._消费)#消费线程
        线.daemon=True#守护
        线.start()#启动

    @property
    def 已失败(自身):
        """是否因终端域失败结束。"""
        return 自身._失败 is not None#失败

    def 就绪(自身,信号):
        """在跟随屏幕前等待当前物理保持已被确认。"""
        若已中止则抛出(信号)#已取消
        if 自身._失败 is not None:#已失败
            raise 自身._失败#抛出
        if 自身._代际 is not None:#已确认
            return#就绪
        完成=threading.Event()#门
        箱={'错误':None}#错误箱
        def 解决():
            """唤醒。"""
            完成.set()#唤醒
        def 拒绝(错误):
            """拒绝。"""
            箱['错误']=错误#记下
            完成.set()#唤醒
        等待者={'resolve':解决,'reject':拒绝}#等待者
        自身._等待者.add(等待者)#登记
        while not 完成.is_set():#等待
            若已中止则抛出(信号)#中止
            完成.wait(0.05)#短等
        自身._等待者.discard(等待者)#拆除
        if 箱['错误'] is not None:#失败
            raise 箱['错误']#抛出

    def dispose(自身):
        """释放本窗口流与全部确认等待者。"""
        自身._拒绝(远程错误('gateway/internal','Terminal window hold released',{}))#拒绝
        拆除=getattr(自身._流,'dispose',None)#拆除
        if 拆除 is not None:#有
            拆除()#关流

    def _消费(自身):
        """消费保持流。"""
        try:
            for 项 in 自身._流:#逐项
                接受=getattr(项,'accept',None)#接受
                if 接受 is not None:#有
                    接受()#接受
                自身._代际=getattr(项,'signal',项.get('signal') if isinstance(项,dict) else None)#代际
                for 等待者 in list(自身._等待者):#唤醒
                    等待者['resolve']()#解决
                自身._等待者.clear()#清空
        except BaseException as 错误:
            自身._拒绝(错误)#拒绝

    def _拒绝(自身,错误):
        """拒绝全部等待者。"""
        自身._失败=错误 if isinstance(错误,BaseException) else 远程错误('gateway/internal','Terminal window hold failed',{})#记下
        自身._代际=None#清代际
        for 等待者 in list(自身._等待者):#拒绝
            等待者['reject'](错误)#拒绝
        自身._等待者.clear()#清空
