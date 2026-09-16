import threading#操作队列
from ...内核.作用域 import 操作任务#单次等待
from ...工具.超时 import 中止控制器,若已中止则抛出,已中止,合成信号#中止
from ...依赖.工具 import 聚合错误#多失败

__all__=['浏览器操作运行时错误','会话资源']#仅中文公开名

class 浏览器操作运行时错误(Exception):#本包异常基类
    """浏览器会话资源失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 等待操作(操作,信号):#可取消等待
    """停调用方等待，资源所有者的工作仍保留处理器。操作是操作任务。"""
    任务=操作任务()#调用方任务
    def 已中止时():#信号
        """按原因拒绝。"""
        原因=None#原因
        if hasattr(信号,'reason'):#有原因
            原因=信号.reason#原因
        if isinstance(原因,BaseException):#异常
            任务.拒绝(原因)#原因
        else:#包装
            包装=浏览器操作运行时错误('browser operation canceled')#文案
            包装.__cause__=原因#cause
            任务.拒绝(包装)#拒绝
    def 监视():#等中止
        """置位后拒绝。"""
        if hasattr(信号,'wait'):#Event
            信号.wait()#等待
            已中止时()#拒绝
    if 信号 is not None:#有信号
        threading.Thread(target=监视).start()#监视
    def 转交():#操作结算
        """兑现或拒绝调用方任务。"""
        try:#等操作
            值=操作.等待()#结果
            任务.兑现(值)#兑现
        except Exception as 错误:#失败
            任务.拒绝(错误 if isinstance(错误,BaseException) else 浏览器操作运行时错误(str(错误)))#拒绝
    threading.Thread(target=转交).start()#转交
    return 任务.等待()#阻塞调用方

class 会话资源:#每 Session 惰性一份资源
    """按活智能体惰性获取资源，并串行其操作。"""
    def __init__(自身,上下文,选项):#记下上下文与策略
        """选项含 label/exclusive/open。"""
        自身.上下文=上下文#提供者上下文
        自身.选项=选项#策略
        自身.条目={}#智能体 → 条目
        自身.所有者拆除={}#智能体 → 拆除
        自身.已拆所有者=set()#已拆所有者
        自身.拆除中=None#共享拆除任务

    def 可用(自身,智能体):#不占资源的准入
        """该所有者能否使用或获取浏览器。"""
        if 自身.拆除中 is not None:#正在拆
            return False#不可
        if 智能体 in 自身.已拆所有者:#已拆
            return False#不可
        登记=自身.上下文.get('agents')#智能体表
        if 登记 is None or 登记.get(智能体.id) is not 智能体:#不是活的
            return False#不可
        if 智能体 in 自身.条目:#已有
            return True#可
        if 自身.选项['exclusive'] and len(自身.条目)>0:#独占已被占
            return False#不可
        return True#可

    def 取(自身,智能体,信号=None):#获取资源值
        """没有则获取一次。"""
        若已中止则抛出(信号)#中止
        条目=自身.条目于(智能体)#条目
        if 信号 is None:#无取消
            资源=条目['ready'].等待()#资源
        else:#可取消等待
            资源=等待操作(条目['ready'],信号)#等待
        若已中止则抛出(信号)#中止
        若已中止则抛出(条目['controller'].信号)#所有者中止
        return 资源['value']#句柄

    def 运行(自身,智能体,信号,操作):#串行操作
        """等本 Session 先前操作；取消只停本次等待。"""
        若已中止则抛出(信号)#中止
        条目=自身.条目于(智能体)#条目
        合成=合成信号(信号,条目['controller'].信号)#合成
        def 释放已拆():#disposed 中止
            """Session 取消时先关资源。"""
            原因=getattr(信号,'reason',None)#原因
            种=原因['kind'] if isinstance(原因,dict) and 'kind' in 原因 else getattr(原因,'kind',None)#kind
            if 种!='disposed':#不是拆除
                return#忽略
            自身.已拆所有者.add(智能体)#记下
            def 清():#关条目
                """清理失败打日志。"""
                try:#关
                    自身.关条目(智能体,条目).等待()#关
                except Exception as 错误:#失败
                    自身.上下文.logger.warn(自身.选项['label']+': browser cleanup during Session cancellation failed: '+str(错误))#日志
            threading.Thread(target=清).start()#清
        def 监视拆除():#等信号
            """置位后释放。"""
            if hasattr(信号,'wait'):#Event
                信号.wait()#等待
                释放已拆()#释放
        threading.Thread(target=监视拆除).start()#监视
        任务=操作任务()#本次
        def 体():#队列体
            """等尾再跑操作。"""
            try:#串行
                条目['tail'].等待()#先前
                若已中止则抛出(合成)#合成
                资源=等待操作(条目['ready'],合成)#资源
                若已中止则抛出(合成)#合成
                结果=操作(资源['value'],合成)#提供方调用
                若已中止则抛出(合成)#合成
                任务.兑现(结果)#兑现
            except Exception as 错误:#失败
                任务.拒绝(错误)#拒绝
        threading.Thread(target=体).start()#启动
        尾=操作任务()#队列尾
        def 收尾():#忽略对错
            """只跟踪结算。"""
            try:#等本次
                任务.等待()#结算
            except Exception:#忽略
                pass#队列不观察错误
            尾.兑现(None)#尾完成
        threading.Thread(target=收尾).start()#收尾
        条目['tail']=尾#换尾
        return 任务.等待()#返回结果

    def 拆除(自身):#停获取并等全部
        """失败的 close 保留条目并拒绝拆除。"""
        if 自身.拆除中 is not None:#已有
            return 自身.拆除中.等待()#共享
        自身.拆除中=操作任务()#共享
        def 体():#拆除体
            """关每条再关所有者拆除。"""
            try:#结算
                错误表=[]#失败
                for 智能体,条目 in list(自身.条目.items()):#逐条
                    try:#关
                        自身.关条目(智能体,条目).等待()#关
                    except Exception as 错误:#失败
                        错误表.append(错误)#记下
                if len(错误表)>0:#有失败
                    raise 聚合错误(错误表,自身.选项['label']+': browser cleanup failed')#聚合
                for 关 in list(自身.所有者拆除.values()):#所有者
                    关()#拆除
                自身.拆除中.兑现(None)#完成
            except Exception as 错误:#失败
                自身.拆除中.拒绝(错误)#拒绝
        threading.Thread(target=体).start()#启动
        return 自身.拆除中.等待()#等待

    def 条目于(自身,智能体):#取或建条目
        """准入失败则抛英文。"""
        登记=自身.上下文.get('agents')#表
        if 自身.拆除中 is not None or 智能体 in 自身.已拆所有者 or 登记 is None or 登记.get(智能体.id) is not 智能体:#非活所有者
            raise 浏览器操作运行时错误(自身.选项['label']+': Session is not a live browser owner')#非活
        if 智能体 in 自身.条目:#已有
            return 自身.条目[智能体]#条目
        if 自身.选项['exclusive'] and len(自身.条目)>0:#独占
            raise 浏览器操作运行时错误(自身.选项['label']+': attached browser is already reserved by another Session')#已占
        if 智能体 not in 自身.所有者拆除:#尚未挂拆除
            def 会话拆除():#智能体作用域拆除
                """关本条。"""
                def 卸():#异步卸
                    """等 close。"""
                    自身.已拆所有者.add(智能体)#记下
                    if 智能体 in 自身.条目:#仍有
                        自身.关条目(智能体,自身.条目[智能体]).等待()#关
                    if 智能体 in 自身.所有者拆除:#摘
                        del 自身.所有者拆除[智能体]#摘
                    return#结束
                threading.Thread(target=卸).start()#卸
                return 卸#拆除器
            自身.所有者拆除[智能体]=智能体.ctx.副作用(会话拆除,自身.选项['label']+'.session')#挂
        控制器=中止控制器()#本条寿命
        就绪=操作任务()#获取
        def 获取():#open
            """失败则删条目。"""
            try:#open
                若已中止则抛出(控制器.信号)#中止
                资源=自身.选项['open'](智能体,控制器.信号)#获取
                就绪.兑现(资源)#兑现
            except Exception as 错误:#失败
                if 智能体 in 自身.条目:#仍是本条
                    del 自身.条目[智能体]#删
                就绪.拒绝(错误)#拒绝
        threading.Thread(target=获取).start()#获取
        尾=操作任务()#空尾
        尾.兑现(None)#已完成
        条目={'controller':控制器,'ready':就绪,'tail':尾}#条目
        自身.条目[智能体]=条目#挂
        return 条目#条目

    def 关条目(自身,智能体,条目):#关一条
        """共享 closing 任务。"""
        if 'closing' in 条目 and 条目['closing'] is not None:#已有
            return 条目['closing']#共享
        关=操作任务()#关闭
        条目['closing']=关#挂
        def 体():#关体
            """中止获取、close 资源、等尾。"""
            try:#关
                条目['controller'].中止(浏览器操作运行时错误(自身.选项['label']+': Session browser is closing'))#中止
                资源=None#可能失败的获取
                try:#ready
                    资源=条目['ready'].等待()#资源
                except Exception:#获取失败无资源
                    资源=None#无
                try:#close
                    if 资源 is not None:#有
                        资源['close']()#关
                finally:#等尾
                    条目['tail'].等待()#尾
                if 智能体 in 自身.条目:#摘
                    del 自身.条目[智能体]#摘
                关.兑现(None)#完成
            except Exception as 错误:#失败
                关.拒绝(错误)#拒绝
        threading.Thread(target=体).start()#启动
        return 关#任务
