"""继承控制通道上的 Node 子进程执行；此处不跑 Harness 服务。"""
import os,threading#环境清空与发送线程
from .通道 import json通道,任务,全部并发#分帧与未完成发送
from .引导 import 运行程序#程序求值
from .环境 import 启动环境名#启动环境白名单
from .协议 import 节点ptc错误#本包异常

__all__=['运行节点主程序']#仅中文公开名

def 运行节点主程序(流,最大消息字节,进程状态):#握手后跑一个宿主程序
    """在继承、已接管的控制端点上跑一个宿主程序。流是已接管的双工端。最大消息字节是宿主校验过的帧与排队写入上限。进程状态含 env、stdout、stderr、exitCode。控制输出刷完且观察到宿主关闭后返回；传输失败则关通道。"""
    if type(最大消息字节) is bool or type(最大消息字节) is not int or 最大消息字节<=0 or 最大消息字节>0xffffffff:#非法上限
        raise 节点ptc错误('invalid control message limit')#拒绝
    for 键 in list(进程状态.env.keys()):#清掉非启动名
        if 键.upper() not in 启动环境名:#不在白名单
            del 进程状态.env[键]#删除
    进程状态.env=type(进程状态.env)()#换成空环境对象
    引导完成=任务()#boot 数据
    监听器表=[]#回复监听
    已启动=[False]#是否已收到 boot
    已失败=[False]#传输或协议失败
    已发终态=[False]#是否已发 done
    宿主已关=任务()#宿主关闭
    def 通道关闭():#流关闭
        """兑现宿主关闭。"""
        try:#已兑现则忽略
            宿主已关.兑现()#关闭
        except (节点ptc错误,RuntimeError):#重复
            pass#忽略
    def 接收(原始,字节):#一帧
        """分派 boot 或回复。"""
        if not 已启动[0]:#首帧必须是 boot
            已启动[0]=True#已启动
            if type(原始) is not dict or 原始.get('type')!='boot':#不是 boot
                引导完成.拒绝(节点ptc错误('expected program boot frame'))#拒绝
                return#结束
            引导完成.兑现(原始['data'])#引导数据
            return#结束
        if 已发终态[0]:#终态后忽略回复
            return#忽略
        for 监听器 in 监听器表:#逐个
            监听器(原始)#回复
        _=字节#帧长由通道计量
    def 失败(错误,种类):#通道失败
        """协议失败始终结算；传输失败在终态前结算。"""
        if (not 已发终态[0]) or 种类=='protocol':#需失败
            已失败[0]=True#标记
            引导完成.拒绝(错误)#拒绝 boot
            通道.关闭()#关
            进程状态.exitCode=1#失败码
        try:#关闭
            宿主已关.兑现()#关闭
        except (节点ptc错误,RuntimeError):#重复
            pass#忽略
    通道=json通道(流,最大消息字节,接收,失败)#分帧
    未完成=set()#发送任务
    def 发送(消息):#程序到宿主
        """终态后不再发送；done 标记终态。"""
        if 已发终态[0]:#已终态
            return#忽略
        if 消息['type']=='done':#终态帧
            已发终态[0]=True#标记
        完成=任务()#本次发送
        def 跑发送():#后台发送
            """发送并吞掉传输失败。"""
            try:#发送
                通道.发送(消息)#一帧
                完成.兑现()#成功
            except (节点ptc错误,OSError,ValueError) as 错误:#失败
                已失败[0]=True#标记
                通道.关闭()#关
                进程状态.exitCode=1#失败码
                try:#关闭
                    宿主已关.兑现()#关闭
                except (节点ptc错误,RuntimeError):#重复
                    pass#忽略
                完成.兑现()#发送路径吞错
            未完成.discard(完成)#摘掉
        工作=threading.Thread(target=跑发送,daemon=True)#后台
        未完成.add(完成)#登记
        工作.start()#启动
    class 引导端口:#程序端口
        """程序消息与宿主回复。"""
        def 发消息(自身,消息):#发出
            """发出一帧。"""
            发送(消息)#发送
        def 监听(自身,事件,监听器):#挂回复
            """挂一条回复监听。"""
            监听器表.append(监听器)#登记
    try:#握手并跑
        通道.发送({'type':'ready'})#就绪
        数据=引导完成.等待()#boot
        运行程序(引导端口(),数据,{'stdout':进程状态.stdout,'stderr':进程状态.stderr})#求值
        while len(未完成)>0:#未完成发送
            全部并发([项.等待 for 项 in list(未完成)])#等全部
        通道.排空()#排空写入
        宿主已关.等待()#等宿主关通道
    finally:#收尾
        通道.关闭()#关
        if 已失败[0]:#失败
            进程状态.exitCode=1#失败码
