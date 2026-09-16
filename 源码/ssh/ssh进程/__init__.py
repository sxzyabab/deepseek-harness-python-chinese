import sys,threading,queue,base64#继承输出、转发线程、贯通缓冲与尾解码
from ...依赖.工具 import 聚合错误#多路清理
from ...内核.作用域 import 操作任务#启动与完成
from ...工具.超时 import 中止控制器,若已中止则抛出,已中止,合成信号#中止
from ...子进程.子进程 import 子进程运行时,可执行未找到错误,句柄#缝
from ...子进程.本地子进程 import 输出收集器#收集尾
from ..ssh.模式 import (
    完成模式,#done
    前台模式,#inspect
    输出快照帧上限,#快照帧
    输出快照模式,#snapshot
    已准备模式,#prepare
    远端路径,#可执行
    流端点模式,#终端流
    ssh错误,#基类
)#模式
from ..ssh.协议 import ssh请求对等,远程操作错误#快照对等与远端错误

__all__=['远端清理错误','ssh子进程运行时']#仅中文公开名

def 环境墓碑(环境):#None 编码墓碑
    """缺席则缺席；值 None 变 JSON null。"""
    if 环境 is None:#无
        return None#缺席
    return {键:(None if 值 is None else 值) for 键,值 in 环境.items()}#墓碑

def 空模式(值):#z.null / z.object({}).strict()
    """空或空对象。"""
    if 值 is None:#空
        return None#空
    if isinstance(值,dict) and len(值)==0:#空对象
        return 值#空
    raise ssh错误('expected null')#失败

def 布尔模式(值):#z.boolean
    """布尔。"""
    if not isinstance(值,bool):#非
        raise ssh错误('expected boolean')#失败
    return 值#布尔

class 贯通管道:#分配期间可写的内存管道
    """stdin/输出在 SSH 分配完成前先落入此缓冲。"""
    def __init__(自身):#构造
        """空队列。"""
        自身._队列=queue.Queue()#块
        自身._结束=object()#EOF 哨兵
        自身.destroyed=False#已毁
        自身.readableEnded=False#读结束
        自身._监听={'error':[],'close':[],'end':[],'data':[]}#事件
    def on(自身,事件,回调):#监听
        """登记。"""
        自身._监听[事件].append(回调)#追加
        return 自身#链式
    def once(自身,事件,回调):#一次
        """触发一次。"""
        def 一次(*参数):#包装
            """摘后再调。"""
            自身.off(事件,一次)#摘
            回调(*参数)#调
        自身.on(事件,一次)#登记
        return 自身#链式
    def off(自身,事件,回调):#摘
        """移除。"""
        表=自身._监听[事件]#表
        if 回调 in 表:#有
            表.remove(回调)#摘
        return 自身#链式
    def write(自身,字节):#写
        """入队。"""
        if 自身.destroyed:#已毁
            return False#拒绝
        自身._队列.put(字节)#入队
        for 回调 in list(自身._监听['data']):#data
            回调(字节)#通知
        return True#接受
    def read(自身,大小=65536):#读
        """出队；结束则空。"""
        项=自身._队列.get()#块
        if 项 is 自身._结束:#EOF
            自身.readableEnded=True#结束
            自身._队列.put(自身._结束)#留给其他读者
            return b''#空
        return 项#块
    def end(自身):#半关写
        """写入结束哨兵。"""
        自身._队列.put(自身._结束)#EOF
        for 回调 in list(自身._监听['end']):#end
            回调()#通知
    def destroy(自身,错误=None):#毁
        """标记毁并通知。"""
        if 自身.destroyed:#已
            return#忽略
        自身.destroyed=True#记下
        自身._队列.put(自身._结束)#唤醒读者
        if 错误 is not None:#有因
            for 回调 in list(自身._监听['error']):#错误
                回调(错误)#通知
        for 回调 in list(自身._监听['close']):#关闭
            回调()#通知
    def pipe(自身,目标,选项=None):#转发
        """后台读自身写目标。"""
        def 转发():#线程
            """直到结束。"""
            try:#转
                while True:#循环
                    块=自身.read()#读
                    if not 块:#结束
                        break#停
                    目标.write(块)#写
            except BaseException:#忽略
                pass#吞
        threading.Thread(target=转发,daemon=True).start()#转发
        return 目标#链式
    def __iter__(自身):#可迭代
        """产出块直到结束。"""
        while True:#循环
            块=自身.read()#读
            if not 块:#结束
                return#停
            yield 块#块

class 远端清理错误(聚合错误):#分配失败且远端清理未知
    """终端分配失败且远端清理未知。"""

class 远端进程(句柄):#一路普通远端进程
    """stdin 与 control 在 SSH 分配期间仍可写。"""
    def __init__(自身,ssh,规格):#构造
        """按 stdio 打开贯通管并开始分配。"""
        自身.ssh=ssh#连接
        自身.规格=规格#规格
        自身.inbound=贯通管道()#stdin 入
        自身.out=贯通管道()#stdout
        自身.err=贯通管道()#stderr
        自身.toControl=贯通管道()#control 写
        自身.fromControl=贯通管道()#control 读
        自身.stdin=自身.inbound if 规格['stdio']['stdin']=='pipe' else None#stdin
        自身.stdout=自身.out if 规格['stdio']['stdout']=='pipe' else None#stdout
        自身.stderr=自身.err if 规格['stdio']['stderr']=='pipe' else None#stderr
        请求控制=规格['stdio'].get('control') if isinstance(规格['stdio'],dict) else None#fd7
        自身.control=None if 请求控制 is None else 自身.toControl#简化双工：写入 toControl
        自身.collected={}#收集读取器
        自身.控制器=中止控制器()#分配寿命
        自身.id=None#远端 id
        自身.套接字表=[]#已连套接字
        自身._静止=False#范围空
        自身._已提交=False#start 已确认
        自身._终止任务=None#终止
        自身.spills={}#溢出路径
        自身.更新收集={}#stdout/stderr 更新
        for 流 in (自身.inbound,自身.out,自身.err,自身.toControl,自身.fromControl):#吞错误
            流.on('error',lambda 错误=None: None)#忽略
        def 收集(名,流,模式):#一路收集
            """pipe 不收集；inherit 写宿主；对象则有界尾。"""
            if 模式=='pipe':#原始
                return None#无
            if 模式=='inherit':#继承
                目标=sys.stdout.buffer if 名=='stdout' else sys.stderr.buffer#宿主
                流.pipe(type('写',(),{'write':lambda 自身2,块:目标.write(块 if isinstance(块,bytes) else 块.encode('utf-8'))})())#转
                return None#无读取器
            箱={'collector':输出收集器(模式['maxBytes'],None,名,''),'base':0,'total':0,'finalized':False}#状态
            def 更新(快照,最终):#快照
                """校验坐标后重建收集器。"""
                字节=base64.b64decode(快照['tail'])#尾
                if len(字节)>模式['maxBytes'] or 快照['totalBytes']<len(字节):#非法
                    raise ssh错误('SSH helper returned invalid collected output coordinates')#拒绝
                if 箱['finalized']:#已终
                    return#忽略
                if 快照['totalBytes']<箱['total']:#回绕
                    raise ssh错误('SSH helper rewound collected output')#拒绝
                箱['finalized']=最终#终?
                箱['collector']=输出收集器(模式['maxBytes'],None,名,'')#重建
                箱['collector'].推入(字节)#推
                箱['base']=快照['totalBytes']-len(字节)#基
                箱['total']=快照['totalBytes']#总量
            自身.更新收集[名]=更新#登记
            class 读取器:#自偏移
                """把远端坐标映射回本地读取器。"""
                def 自偏移读取(读自身,偏移):#读
                    """加基址，带 spill。"""
                    快照=箱['collector'].自偏移读取(偏移-箱['base'])#窗口
                    结果=dict(快照)#拷
                    结果['nextOffset']=快照['nextOffset']+箱['base']#加基
                    if 自身.spills.get(名) is not None:#spill
                        结果['spillPath']=自身.spills[名]#路径
                    return 结果#读取
            return 读取器()#读取器
        出=收集('stdout',自身.out,规格['stdio']['stdout'])#stdout
        错=收集('stderr',自身.err,规格['stdio']['stderr'])#stderr
        if 出 is not None:#有
            自身.collected['stdout']=出#stdout
        if 错 is not None:#有
            自身.collected['stderr']=错#stderr
        def 中止时():#规格信号
            """终止。"""
            自身.终止()#终止
        信号=规格.get('signal')#信号
        自身._摘中止=lambda: None#默认
        if 信号 is not None:#有
            def 监视():#等
                """置位后终止。"""
                信号.wait()#等
                中止时()#终止
            threading.Thread(target=监视,daemon=True).start()#监视
            def 摘():#摘监听
                """标记已摘；监视线程自行结束。"""
                return None#空
            自身._摘中止=摘#记下
        自身._已启动=操作任务()#启动
        threading.Thread(target=自身._启动).start()#启动
        自身.streamsClosed=操作任务()#流关
        def 等流关():#等套接字关
            """启动失败则立刻完。"""
            try:#等启动
                自身._已启动.等待()#等
            except BaseException:#失败
                自身.streamsClosed.兑现(None)#完
                return#结束
            for 套接字对象 in 自身.套接字表:#逐个
                if getattr(套接字对象,'closed',False):#已关
                    continue#跳
                完成=threading.Event()#关
                套接字对象.once('close',完成.set)#等
                完成.wait()#等
            自身.streamsClosed.兑现(None)#完
        threading.Thread(target=等流关,daemon=True).start()#等
        自身.done=操作任务()#退出事实
        def 等完成():#process.done
            """排空、收 spill、兑现退出。"""
            try:#完成
                自身._已启动.等待()#等启动
                结果=自身.ssh.请求('process.done',{'id':自身.id},完成模式,None,True)#done
                自身._排空输出()#排空
                自身.spills=结果['spills']#spill
                for 名 in ('stdout','stderr'):#两路
                    快照=结果['collected'].get(名) if isinstance(结果.get('collected'),dict) else None#快照
                    更新=自身.更新收集.get(名)#更新
                    if (快照 is None)!=(更新 is None):#模式不配
                        raise ssh错误('SSH helper returned mismatched output collection modes')#拒绝
                    if 快照 is not None:#有
                        更新(快照,True)#最终
                自身.done.兑现({'exitCode':结果['outcome']['exitCode'],'signal':结果['outcome']['signal']})#退出
            except BaseException as 错误:#失败
                自身.终止()#终止
                for 套接字对象 in 自身.套接字表:#毁套接字
                    套接字对象.destroy()#毁
                for 流 in (自身.inbound,自身.out,自身.err,自身.toControl,自身.fromControl):#毁管
                    流.destroy(错误 if isinstance(错误,BaseException) else ssh错误(str(错误)))#毁
                自身.done.拒绝(错误)#拒绝
        threading.Thread(target=等完成).start()#完成

    def _启动(自身):#prepare/connect/start
        """失败则终止并毁套接字。"""
        try:#启动
            若已中止则抛出(自身.规格.get('signal'))#已中止
            参数=dict(自身.规格)#拷
            参数.pop('signal',None)#不送信道
            参数['env']=环境墓碑(自身.规格.get('env'))#环境
            已准备=自身.ssh.请求('process.prepare',参数,已准备模式,自身.控制器.信号)#预留
            自身.id=已准备['id']#id
            套接字对=[]#名与套接字
            for 名,坐标 in 已准备['streams'].items():#逐路
                套接字对象=自身.ssh.连接流(坐标,自身.控制器.信号)#连
                套接字对.append((名,套接字对象))#记下
            自身.套接字表=[项[1] for 项 in 套接字对]#表
            for 名,套接字对象 in 套接字对:#接线
                if 名=='stdout' or 名=='stderr':#输出
                    模式=自身.规格['stdio'][名]#处置
                    if isinstance(模式,dict):#收集
                        def 处理快照(方法,原始,信号=None,名=名):#snapshot
                            """只承认 snapshot。"""
                            if 方法!='snapshot':#意外
                                raise ssh错误('Unexpected SSH output-stream operation')#拒绝
                            自身.更新收集[名](输出快照模式(原始),False)#中间尾
                            return None#空
                        ssh请求对等(套接字对象,套接字对象,输出快照帧上限(模式['maxBytes']),1,处理快照)#对等
                    else:#管道
                        套接字对象.end()#半关写
                        输出=自身.out if 名=='stdout' else 自身.err#贯通
                        def 关套接字(套接字对象=套接字对象):#输出关则毁传输
                            """毁套接字。"""
                            套接字对象.destroy()#毁
                        输出.once('close',关套接字)#关
                        def 传输关(输出=输出,关套接字=关套接字):#摘
                            """摘 close 监听。"""
                            输出.off('close',关套接字)#摘
                        套接字对象.once('close',传输关)#摘
                        if 输出.destroyed:#已毁
                            关套接字()#立刻
                        else:#转发
                            套接字对象.pipe(输出)#转
                if 名=='stdin':#stdin
                    自身.inbound.pipe(套接字对象)#转
                if 名=='control':#fd7
                    自身.toControl.pipe(套接字对象)#写
                    套接字对象.pipe(自身.fromControl)#读
            若已中止则抛出(自身.控制器.信号)#中止
            自身.ssh.请求('process.start',{'id':自身.id},空模式,自身.控制器.信号)#start
            自身._已提交=True#确认
            自身._已启动.兑现(None)#完
        except BaseException as 错误:#失败
            自身.终止()#终止
            if 自身._终止任务 is not None:#有终止
                try:#等
                    自身._终止任务.等待()#等
                except BaseException:#忽略
                    pass#吞
            for 套接字对象 in 自身.套接字表:#毁
                套接字对象.destroy()#毁
            自身._已启动.拒绝(错误)#拒绝

    def 终止(自身):#幂等
        """未提交则中止分配；已提交则 process.terminate。"""
        if 自身._静止 or 自身._终止任务 is not None:#已
            return#忽略
        if not 自身._已提交:#尚未确认
            自身.控制器.中止(ssh错误('SSH process terminated before launch acknowledgement'))#中止
        if 自身.id is not None:#有 id
            自身._终止任务=操作任务()#任务
            def 跑():#线程
                """terminate。"""
                try:#请求
                    自身.ssh.请求('process.terminate',{'id':自身.id},空模式)#终止
                    自身._静止=True#空
                    自身._摘中止()#摘
                    自身._终止任务.兑现(None)#完
                except BaseException as 错误:#失败
                    threading.Thread(target=自身.ssh.拆除,daemon=True).start()#放租期
                    自身._终止任务.拒绝(错误)#拒绝
            threading.Thread(target=跑).start()#启动

    def 关闭流(自身):#关掉公开流
        """毁套接字与贯通管。"""
        for 套接字对象 in 自身.套接字表:#套接字
            套接字对象.destroy()#毁
        for 流 in (自身.inbound,自身.out,自身.err,自身.toControl,自身.fromControl,自身.control):#管
            if 流 is not None:#有
                流.destroy()#毁

    def 等待退出(自身,信号=None):#观察托管范围
        """取消返回 False，不停止进程。"""
        if 自身._静止:#已空
            return True#空
        if 已中止(信号):#先中止
            return False#假
        if 信号 is None:#无取消
            return 自身._观察退出()#观察
        取消=操作任务()#取消
        def 中止时():#信号
            """兑现 False。"""
            取消.兑现(False)#假
        def 监视():#等
            """置位。"""
            信号.wait()#等
            中止时()#假
        threading.Thread(target=监视,daemon=True).start()#监视
        观察=操作任务()#观察
        def 跑观察():#线程
            """观察。"""
            try:#观察
                观察.兑现(自身._观察退出(信号))#结果
            except BaseException as 错误:#失败
                观察.拒绝(错误)#拒绝
        threading.Thread(target=跑观察).start()#观察
        完成=threading.Event()#赛跑完
        箱={'值':None,'错误':None}#结算
        def 等观察():#观察路
            """先到。"""
            try:#等
                箱['值']=观察.等待()#值
            except BaseException as 错误:#失败
                箱['错误']=错误#记下
            完成.set()#完
        def 等取消():#取消路
            """False。"""
            try:#等
                值=取消.等待()#假
                if not 完成.is_set():#还没
                    箱['值']=值#假
            except BaseException:#忽略
                pass#吞
            完成.set()#完
        threading.Thread(target=等观察).start()#观察
        threading.Thread(target=等取消).start()#取消
        完成.wait()#赛跑
        if 箱['错误'] is not None:#失败
            raise 箱['错误']#原样
        return 箱['值']#结果

    def _观察退出(自身,信号=None):#process.wait
        """启动失败则先等终止。"""
        try:#启动
            自身._已启动.等待()#等
        except BaseException:#启动失败
            if 自身._终止任务 is not None:#有终止
                自身._终止任务.等待()#等
            自身._静止=True#空
            自身._摘中止()#摘
            return True#空
        if 自身._终止任务 is not None:#已终止
            自身._终止任务.等待()#等
            return True#空
        结果=自身.ssh.请求('process.wait',{'id':自身.id},布尔模式,信号,True)#观察
        if 结果:#空
            自身._静止=True#空
            自身._摘中止()#摘
        return 结果#是否空

    def _排空输出(自身):#graceMs 内排空管道
        """收集模式不等管道 EOF。"""
        输出等待=[]#等待
        for 名 in ('stdout','stderr'):#两路
            if isinstance(自身.规格['stdio'][名],dict):#收集
                输出等待.append(True)#立刻
                continue#跳
            流=自身.out if 名=='stdout' else 自身.err#贯通
            if 流.readableEnded or 流.destroyed:#已结束
                输出等待.append(True)#立刻
                continue#跳
            完成=threading.Event()#结束
            def 完(完成=完成):#end/close/error
                """结算。"""
                完成.set()#完
            流.once('end',完)#end
            流.once('close',完)#close
            流.once('error',完)#error
            输出等待.append(完成)#事件
        宽限=threading.Event()#宽限
        定时=threading.Timer(自身.规格['graceMs']/1000.0,宽限.set)#宽限
        定时.daemon=True#守护
        定时.start()#武装
        def 等输出():#等管道
            """全到则提前结束宽限。"""
            for 项 in 输出等待:#逐个
                if 项 is True:#已完
                    continue#跳
                项.wait()#等
            宽限.set()#提前
        threading.Thread(target=等输出,daemon=True).start()#等
        宽限.wait()#赛跑
        定时.cancel()#清

class ssh子进程运行时(子进程运行时):#与 SSH 文件系统配对
    """远端辅助选择 POSIX 进程归属。"""
    inject=['ssh']#框架槽：类级依赖
    def __init__(自身,上下文):#构造
        """登记拆除。"""
        super().__init__(上下文)#subprocess
        自身.存活=set()#普通句柄
        自身.终端表=set()#终端
        自身.终端分配=set()#进行中分配任务
        自身.寿命=中止控制器()#寿命
        def 拆除效果():#fiber
            """停全部。"""
            def 清理():#拆除器
                """终止并确认。"""
                自身.寿命.中止(ssh错误('SSH subprocess provider disposed'))#中止
                for 句柄对象 in list(自身.存活):#普通
                    句柄对象.终止()#终止
                失败=[]#错误
                for 句柄对象 in list(自身.存活):#等退出
                    try:#等
                        句柄对象.等待退出()#等
                    except BaseException as 错误:#失败
                        失败.append(错误)#收
                    finally:#关流
                        句柄对象.关闭流()#关
                for 任务 in list(自身.终端分配):#分配
                    try:#等
                        任务.等待()#等
                    except 远端清理错误 as 错误:#提升
                        失败.append(错误)#收
                    except BaseException:#其它分配失败
                        pass#创建路径自己报
                for 句柄对象 in list(自身.终端表):#终端
                    try:#终止
                        句柄对象.终止()#终止
                    except BaseException as 错误:#失败
                        失败.append(错误)#收
                if len(失败)>0:#有
                    raise 聚合错误(失败,'SSH process cleanup could not be confirmed')#聚合
            return 清理#拆除器
        上下文.副作用(拆除效果,'ssh.subprocess')#登记

    def 解析可执行文件(自身,命令,环境=None,信号=None):#远端查找
        """未命中提升为可执行未找到错误。"""
        try:#请求
            return 自身.所属上下文.ssh.请求('executable',{'command':命令,'env':环境},远端路径,信号)#路径
        except 远程操作错误 as 错误:#带码
            if 错误.code=='SUBPROCESS_EXECUTABLE_NOT_FOUND':#未找到
                raise 可执行未找到错误(str(错误),错误)#提升
            raise 错误#原样

    def 终端环境(自身,信号=None):#远端壳事实
        """platform 与可选 defaultShell。"""
        def 环境模式(值):#校验
            """posix/windows。"""
            if not isinstance(值,dict) or 值.get('platform') not in ('posix','windows'):#非法
                raise ssh错误('expected terminal environment')#失败
            结果={'platform':值['platform']}#平台
            if 值.get('defaultShell') is not None:#有默认
                结果['defaultShell']=值['defaultShell']#壳
            return 结果#环境
        return 自身.所属上下文.ssh.请求('terminal.environment',{},环境模式,信号)#环境

    def 启动(自身,规格):#普通 spawn
        """立即返回句柄。"""
        若已中止则抛出(自身.寿命.信号)#已拆
        若已中止则抛出(规格.get('signal'))#已中止
        句柄对象=远端进程(自身.所属上下文.ssh,规格)#句柄
        自身.存活.add(句柄对象)#登记
        def 收尾():#退出后摘
            """等 done、静止、流关。"""
            try:#等
                句柄对象.done.等待()#退出
                句柄对象.等待退出()#静止
                句柄对象.streamsClosed.等待()#流关
            except BaseException:#忽略
                pass#吞
            自身.存活.discard(句柄对象)#摘
        threading.Thread(target=收尾,daemon=True).start()#收尾
        return 句柄对象#句柄

    def 启动终端(自身,规格):#PTY
        """分配失败时尝试远端清理。"""
        若已中止则抛出(自身.寿命.信号)#已拆
        信号=自身.寿命.信号 if 规格.get('signal') is None else 合成信号(规格['signal'],自身.寿命.信号)#融合
        若已中止则抛出(信号)#已中止
        任务=操作任务()#分配
        自身.终端分配.add(任务)#登记
        def 跑():#线程
            """分配。"""
            try:#分配
                值=自身._创建终端(规格,信号)#句柄
                任务.兑现(值)#完
            except BaseException as 错误:#失败
                任务.拒绝(错误)#拒绝
            finally:#摘
                自身.终端分配.discard(任务)#摘
        threading.Thread(target=跑).start()#分配
        return 任务.等待()#句柄

    def _创建终端(自身,规格,信号):#prepare/connect/start
        """失败则 terminate；清理失败升远端清理错误。"""
        ssh=自身.所属上下文.ssh#连接
        已准备=ssh.请求('process.prepare',{
            'argv':规格['argv'],#参数
            'cwd':规格['cwd'],#目录
            'env':环境墓碑(规格.get('env')),#环境
            'graceMs':规格['graceMs'],#宽限
            'terminal':{'rows':规格['rows'],'cols':规格['cols'],'terminalType':规格['terminalType']},#终端
        },已准备模式,信号)#预留
        标识=已准备['id']#id
        套接字对象=None#流
        try:#接线
            若已中止则抛出(信号)#中止
            套接字对象=ssh.连接流(流端点模式(已准备['streams']['terminal']),信号)#连
            若已中止则抛出(信号)#中止
            套接字对象.end()#半关写
            输出=贯通管道()#输出
            套接字对象.pipe(输出)#转
            def 正pid(值):#start 结果
                """正整数 pid。"""
                if not isinstance(值,dict) or not isinstance(值.get('pid'),int) or isinstance(值.get('pid'),bool) or 值['pid']<=0:#非法
                    raise ssh错误('expected positive pid')#失败
                return 值#结果
            已启动=ssh.请求('process.start',{'id':标识},正pid,信号)#start
            若已中止则抛出(信号)#中止
            完成=操作任务()#done
            def 等done():#线程
                """退出事实。"""
                try:#done
                    结果=ssh.请求('process.done',{'id':标识},完成模式,None,True)#done
                    完成.兑现({'exitCode':结果['outcome']['exitCode'],'signal':结果['outcome']['signal']})#退出
                except BaseException as 错误:#失败
                    完成.拒绝(错误)#拒绝
            threading.Thread(target=等done,daemon=True).start()#done
            关闭中={'任务':None}#terminate 合并
            句柄对象=type('终端句柄',(),{})()#实例
            句柄对象.pid=已启动['pid']#pid
            句柄对象.output=输出#输出
            句柄对象.done=完成#完成
            def 调整尺寸(列,行):#resize
                """远端尺寸。"""
                ssh.请求('terminal.resize',{'id':标识,'cols':列,'rows':行},空模式)#调
            def 写入(数据):#write
                """原始输入。"""
                ssh.请求('terminal.write',{'id':标识,'value':数据},空模式)#写
            def 检查前台():#inspect
                """可空前台。"""
                return ssh.请求('terminal.inspect',{'id':标识},前台模式)#观察
            def 发信号前台(信号名):#signal
                """投递。"""
                def 正整数(值):#组 id
                    """正整数。"""
                    if isinstance(值,bool) or not isinstance(值,int) or 值<=0:#非法
                        raise ssh错误('expected process group id')#失败
                    return 值#id
                return ssh.请求('terminal.signal',{'id':标识,'value':信号名},正整数)#组
            def 终止():#terminate
                """合并进行中的终止。"""
                if 关闭中['任务'] is not None:#已有
                    关闭中['任务'].等待()#等
                    return#结束
                关闭中['任务']=操作任务()#任务
                def 跑():#线程
                    """terminate 并摘。"""
                    try:#终止
                        ssh.请求('process.terminate',{'id':标识},空模式,None,True)#终止
                        if 套接字对象 is not None:#有
                            套接字对象.destroy()#毁
                        输出.destroy()#毁
                        自身.终端表.discard(句柄对象)#摘
                        关闭中['任务'].兑现(None)#完
                    except BaseException as 错误:#失败
                        关闭中['任务']=None#允许重试
                        raise 错误#原样
                threading.Thread(target=跑).start()#终止
                关闭中['任务'].等待()#等
            句柄对象.调整尺寸=调整尺寸#方法
            句柄对象.写入=写入#方法
            句柄对象.检查前台=检查前台#方法
            句柄对象.发信号前台=发信号前台#方法
            句柄对象.终止=终止#方法
            def 中止时():#信号
                """终止；失败则拆连接。"""
                try:#终止
                    句柄对象.终止()#终止
                except BaseException:#失败
                    threading.Thread(target=ssh.拆除,daemon=True).start()#拆
            if 信号 is not None:#有
                def 监视():#等
                    """置位后中止。"""
                    信号.wait()#等
                    中止时()#终止
                threading.Thread(target=监视,daemon=True).start()#监视
            自身.终端表.add(句柄对象)#登记
            return 句柄对象#句柄
        except BaseException as 错误:#失败
            if 套接字对象 is not None:#有
                套接字对象.destroy()#毁
            try:#清理
                ssh.请求('process.terminate',{'id':标识},空模式)#终止
            except BaseException as 清理错误:#未知
                threading.Thread(target=ssh.拆除,daemon=True).start()#拆
                raise 远端清理错误([错误,清理错误],'SSH terminal allocation failed and remote cleanup is unknown')#聚合
            raise 错误#原样

inject=['ssh']#框架槽
default=ssh子进程运行时#框架槽
