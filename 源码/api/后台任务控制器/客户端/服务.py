import threading
from .....依赖.cordis import 服务
from .....api.网关.流载体 import 远程流载体错误

__all__=['客户端作业']

class 客户端作业(服务):
    """引用计数的名册流与观察流，外加终止透传。"""
    def __init__(自身,上下文,远程,模型):
        """远程为含 $stream 与 job 的 dict。"""
        super().__init__(上下文,'jobs')
        自身._远程=远程
        自身._模型=模型
        自身.状态=模型
        自身._表行项={}
        自身._观察项={}
        def 拆除效果():
            """关掉仍打开的流。"""
            def 清理():
                """等到每条载体结束。"""
                打开=list(自身._表行项.values())+list(自身._观察项.values())
                自身._表行项.clear()
                自身._观察项.clear()
                for 项 in 打开:
                    项['stopped']=True
                for 项 in 打开:
                    try:
                        项['dispose']()
                    except BaseException:
                        pass
            return 清理
        上下文.副作用(拆除效果,'job-controller.client.streams')

    def 终止(自身,会话标识,标识):
        """人类终止透传。"""
        return 自身._远程['job'].kill({'sessionId':会话标识,'jobId':标识})

    def 监视表行(自身,会话标识):
        """引用计数监视一名册。"""
        return 自身._取得(
            自身._表行项,
            str(会话标识),
            lambda:自身._开表行(会话标识),
            lambda:自身._模型.丢弃表行(会话标识),
        )

    def 观察(自身,会话标识,标识):
        """引用计数观察一作业。"""
        return 自身._取得(
            自身._观察项,
            str(标识),
            lambda:自身._开观察(会话标识,标识),
            lambda:自身._模型.观察已停止(标识),
        )

    def _取得(自身,表,键,开工,清空):
        """共享未停止项或新开一项。"""
        已有=表.get(键)
        if 已有 is not None and not 已有['stopped']:
            已有['refs']+=1
            return 自身._释放器(表,键,已有,清空)
        项=开工()
        表[键]=项
        return 自身._释放器(表,键,项,清空)

    def _释放器(自身,表,键,项,清空):
        """绑定铸造时的那一项，不绑表中现占位者。"""
        已释放=[False]
        def 释放():
            """减引用；到零则拆除。"""
            if 已释放[0]:
                return
            已释放[0]=True
            项['refs']-=1
            if 项['refs']>0:
                return
            if 表.get(键) is 项:
                del 表[键]
            项['stopped']=True
            def 收尾():
                """拆除后若无后继再清空模型。"""
                try:
                    项['dispose']()
                except BaseException:
                    pass
                if 键 in 表:
                    return
                清空()
            threading.Thread(target=收尾,daemon=True).start()
        return 释放

    def _开表行(自身,会话标识):
        """打开一条名册流。"""
        名='job rows '+str(会话标识)
        def 开口(信号):
            """打开一代名册。"""
            return 自身._远程['job'].list({'sessionId':会话标识},信号)
        def 已结束(已接受):
            """开口后结束可重试；开口前结束为终态。"""
            if 已接受:
                return 远程流载体错误(名+' ended before release')
            return Exception(名+' ended before its first frame')
        流=自身._远程['$stream']({'name':名,'open':开口,'ended':已结束})
        项={'refs':1,'stopped':False,'dispose':流.dispose}
        def 消费():
            """把整表帧写入模型。"""
            try:
                for 条目 in 流:
                    自身._模型.替换表行(会话标识,条目.value['jobs'])
                    条目.accept()
            except BaseException:
                if not 项['stopped']:
                    自身._模型.丢弃表行(会话标识)
            finally:
                项['stopped']=True
                try:
                    项['dispose']()
                except BaseException:
                    pass
        threading.Thread(target=消费,daemon=True).start()
        return 项

    def _开观察(自身,会话标识,标识):
        """打开一条观察流。"""
        名='job observation '+str(标识)
        def 开口(信号):
            """带游标打开一代观察。"""
            请求={'jobId':标识}
            if 会话标识 is not None:
                请求['sessionId']=会话标识
            起点=自身._模型.游标(标识)
            if 起点 is not None:
                请求['from']=起点
            return 自身._远程['job'].follow(请求,信号)
        def 已结束(已接受):
            """锚后结束可重试。"""
            if 已接受:
                return 远程流载体错误(名+' ended before settlement')
            return Exception(名+' ended before its anchor')
        流=自身._远程['$stream']({'name':名,'open':开口,'ended':已结束})
        项={'refs':1,'stopped':False,'dispose':流.dispose}
        def 消费():
            """按帧推进观察态。"""
            try:
                for 条目 in 流:
                    帧=条目.value
                    if 帧['type']=='opened':
                        自身._模型.观察已打开(标识,帧)
                        条目.accept()
                        continue
                    if 帧['type']=='output':
                        自身._模型.观察输出(标识,帧)
                        continue
                    自身._模型.观察已结算(标识)
                    break
            except BaseException as 错误:
                if not 项['stopped']:
                    自身._模型.观察失败(标识,错误)
            finally:
                项['stopped']=True
                try:
                    项['dispose']()
                except BaseException:
                    pass
        threading.Thread(target=消费,daemon=True).start()
        return 项
