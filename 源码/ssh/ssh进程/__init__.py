import sys,threading,queue,base64#继承输出、转发线程、贯通缓冲与尾解码
from ...依赖.工具 import 聚合错误#多路清理
from ...基础设施.js特性 import PromiseEX as 期约#启动、完成、终止等返回的期约
from ...子进程.子进程 import 子进程运行时,句柄#缝
from ...子进程.子进程.异常 import 可执行未找到错误#缝
from ...子进程.本地子进程 import 输出收集器#收集尾
from ..ssh.模式 import (
    完成模式,#done
    前台模式,#inspect
    终端活动模式,#activity
    输出快照帧上限,#快照帧
    输出快照模式,#snapshot
    已准备模式,#prepare
    远端路径,#可执行
    流端点模式,#终端流
)#模式
from ..ssh.协议 import ssh请求对等#快照对等
from ..ssh.异常 import ssh错误,远程操作错误#基类与带码远端错误
from .异常 import 远端清理错误#分配失败且远端清理未知

__all__=['远端清理错误','ssh子进程运行时','依赖']

依赖=['ssh']

def 环境墓碑(环境):#None 编码墓碑
    '缺席则缺席；值 None 变 JSON null'
    if 环境 is None:#无
        return None#缺席
    return {键:(None if 值 is None else 值) for 键,值 in 环境.items()}#墓碑

def 空模式(值):#z.null / z.object({}).strict()
    '空或空对象'
    if 值 is None:#空
        return None#空
    if isinstance(值,dict) and len(值)==0:#空对象
        return 值#空
    raise ssh错误('expected null')#失败

def 布尔模式(值):#z.boolean
    '布尔'
    if not isinstance(值,bool):#非
        raise ssh错误('expected boolean')#失败
    return 值#布尔

class 贯通管道:#分配期间可写的内存管道
    'stdin/输出在 SSH 分配完成前先落入此缓冲'
    def __init__(自身):#构造
        '空队列'
        自身._队列=queue.Queue()#块
        自身._结束=None#EOF 哨兵
        自身.destroyed=False#已毁
        自身.readableEnded=False#读结束
        自身._监听={'error':[],'close':[],'end':[],'data':[]}#事件
    def on(自身,事件,回调):#监听
        '登记'
        自身._监听[事件].append(回调)#追加
        return 自身#链式
    def once(自身,事件,回调):#一次
        '触发一次'
        def 一次(*参数):#包装
            '摘后再调'
            自身.off(事件,一次)#摘
            回调(*参数)#调
        自身.on(事件,一次)#登记
        return 自身#链式
    def off(自身,事件,回调):#摘
        '移除'
        表=自身._监听[事件]#表
        if 回调 in 表:#有
            表.remove(回调)#摘
        return 自身#链式
    def write(自身,字节):#写
        '入队'
        if 自身.destroyed:#已毁
            return False#拒绝
        自身._队列.put(字节)#入队
        for 回调 in list(自身._监听['data']):#data
            回调(字节)#通知
        return True#接受
    def read(自身,大小=65536):#读
        '出队；结束则空'
        项=自身._队列.get()#块
        if 项 is None:#EOF
            自身.readableEnded=True#结束
            自身._队列.put(自身._结束)#留给其他读者
            return b''#空
        return 项#块
    def end(自身):#半关写
        '写入结束哨兵'
        自身._队列.put(自身._结束)#EOF
        for 回调 in list(自身._监听['end']):#end
            回调()#通知
    def destroy(自身,错误=None):#毁
        '标记毁并通知'
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
        '后台读自身写目标'
        def 转发():#线程
            '直到结束'
            try:#转
                while True:#循环
                    块=自身.read()#读
                    if not 块:#结束
                        break#停
                    目标.write(块)#写
            except BaseException:#忽略
                pass
        threading.Thread(target=转发,daemon=True).start()#转发
        return 目标#链式
    def __iter__(自身):#可迭代
        '产出块直到结束'
        while True:#循环
            块=自身.read()#读
            if not 块:#结束
                return#停
            yield 块#块

class 远端进程(句柄):#一路普通远端进程
    'stdin 与 control 在 SSH 分配期间仍可写'
    def __init__(自身,ssh,规格):#构造
        '按 stdio 打开贯通管并开始分配'
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
        自身._终止任务=None#终止期约，终止请求发出后才有
        自身.spills={}#溢出路径
        自身.更新收集={}#stdout/stderr 更新
        def 忽略流错误(错误=None):
            '流错误由完成观察统一处理，这里只让流有错误监听'
            return None#无动作
        for 流 in (自身.inbound,自身.out,自身.err,自身.toControl,自身.fromControl):#吞错误
            流.on('error',忽略流错误)#忽略
        def 收集(名,流,模式):#一路收集
            'pipe 不收集；inherit 写宿主；对象则有界尾'
            if 模式=='pipe':#原始
                return None#无
            if 模式=='inherit':#继承
                目标=sys.stdout.buffer if 名=='stdout' else sys.stderr.buffer#宿主，贯通管道只产出字节块
                流.pipe(目标)#转
                return None#无读取器
            箱={'collector':输出收集器(模式['maxBytes'],None,名,''),'base':0,'total':0,'finalized':False}#状态
            def 更新(快照,最终):#快照
                '校验坐标后重建收集器'
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
                '把远端坐标映射回本地读取器'
                def 自偏移读取(读自身,偏移):#读
                    '加基址，带 spill'
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
            '终止'
            自身.终止()#终止
        信号=规格.get('signal')#信号
        if 信号 is not None:#有
            def 监视():#等
                '置位后终止'
                信号.wait()#等
                中止时()#终止
            threading.Thread(target=监视,daemon=True).start()#监视
        自身._已启动=自身._启动()#启动期约，所有字段都已就绪后才能开始
        自身.streamsClosed=期约()#所有流套接字关闭后解决
        def 套接字都已关闭(落定值):
            '套接字都关闭了'
            自身.streamsClosed.解决(None)#解决
        def 等套接字关闭(启动值):
            '启动成功后，等每个已连接套接字关闭'
            关闭期约表=[]#每个套接字关闭后解决
            for 套接字对象 in 自身.套接字表:#逐个
                已关闭=期约()#本套接字
                if getattr(套接字对象,'closed',False):#已关
                    已关闭.解决(None)#已结束
                else:#等 close
                    套接字对象.once('close',已关闭.解决)#等
                关闭期约表.append(已关闭)#登记
            if len(关闭期约表)==0:#没有套接字
                套接字都已关闭(None)#直接完
                return#已处理
            期约.全部(关闭期约表).然后(套接字都已关闭)#都关了才完
        def 启动失败时流已关(启动错误):
            '启动失败则没有流可等，立刻完；启动错误由完成观察负责报告'
            自身.streamsClosed.解决(None)#完
        自身._已启动.然后(等套接字关闭,启动失败时流已关)#等启动
        自身.done=期约()#退出事实，兑现退出结果，失败则拒绝
        def 完成失败(错误):
            '完成观察失败：终止，毁套接字与管道，再拒绝 done'
            自身.终止()#终止
            for 套接字对象 in 自身.套接字表:#毁套接字
                套接字对象.destroy()#毁
            for 流 in (自身.inbound,自身.out,自身.err,自身.toControl,自身.fromControl):#毁管
                流.destroy(错误 if isinstance(错误,BaseException) else ssh错误(str(错误)))#毁
            自身.done.拒绝(错误)#拒绝
        def 收到完成(结果):
            'process.done 兑现后排空输出，收 spill，交出退出结果'
            def 排空之后(排空值):
                '输出排空后收 spill 与收集快照'
                try:#校验收集模式
                    自身.spills=结果['spills']#spill
                    for 名 in ('stdout','stderr'):#两路
                        快照=结果['collected'].get(名) if isinstance(结果.get('collected'),dict) else None#快照
                        更新=自身.更新收集.get(名)#更新
                        if (快照 is None)!=(更新 is None):#模式不配
                            raise ssh错误('SSH helper returned mismatched output collection modes')#拒绝
                        if 快照 is not None:#有
                            更新(快照,True)#最终
                except Exception as 错误:#模式不配或快照坐标非法
                    完成失败(错误)#失败
                    return#已落定
                自身.done.解决({'exitCode':结果['outcome']['exitCode'],'signal':结果['outcome']['signal']})#退出
            自身._排空输出().然后(排空之后,完成失败)#排空
        def 取完成(启动值):
            '启动成功后请求 process.done'
            自身.ssh.请求('process.done',{'id':自身.id},完成模式,None,True).然后(收到完成,完成失败)#done
        自身._已启动.然后(取完成,完成失败)#启动失败同样走完成失败

    def _启动(自身):#prepare/connect/start
        '返回期约，兑现于 process.start 已确认；任何一步失败则终止、毁套接字并以那个错误拒绝'
        已启动=期约()#启动结果
        def 启动失败(错误):
            '终止，等终止结束，毁套接字，再以原错误拒绝'
            自身.终止()#终止
            def 终止之后(终止值):
                '终止结算后毁套接字并拒绝'
                for 套接字对象 in 自身.套接字表:#毁
                    套接字对象.destroy()#毁
                已启动.拒绝(错误)#拒绝
            if 自身._终止任务 is not None:#有终止
                自身._终止任务.然后(终止之后,终止之后)#终止失败也继续
                return#已挂接
            终止之后(None)#没有终止在进行
        try:#启动前检查
            若已中止则抛出(自身.规格.get('signal'))#已中止
            参数=dict(自身.规格)#拷
            参数.pop('signal',None)#不送信道
            参数['env']=环境墓碑(自身.规格.get('env'))#环境
        except Exception as 错误:#已中止
            启动失败(错误)#失败
            return 已启动#已落定
        def 已准备(已准备值):
            '预留好后连接全部数据流，再接线并发起 process.start'
            自身.id=已准备值['id']#id
            名列表=list(已准备值['streams'].keys())#流名，与套接字按序对应
            连接期约表=[自身.ssh.连接流(已准备值['streams'][名],自身.控制器.信号) for 名 in 名列表]#逐路连
            def 已连接(套接字列表):
                '全部数据流连好后接线，再发起 process.start'
                自身.套接字表=list(套接字列表)#表
                套接字对=list(zip(名列表,套接字列表))#名与套接字
                try:#接线
                    for 名,套接字对象 in 套接字对:#接线
                        if 名=='stdout' or 名=='stderr':#输出
                            模式=自身.规格['stdio'][名]#处置
                            if isinstance(模式,dict):#收集
                                def 处理快照(方法,原始,信号=None,名=名):#snapshot
                                    '只承认 snapshot；返回期约，兑现为空，校验失败则拒绝'
                                    结果期约=期约()#快照处理结果
                                    try:#校验并更新
                                        if 方法!='snapshot':#意外
                                            raise ssh错误('Unexpected SSH output-stream operation')#拒绝
                                        自身.更新收集[名](输出快照模式(原始),False)#中间尾
                                    except Exception as 错误:#意外方法或坐标非法
                                        结果期约.拒绝(错误)#拒绝
                                        return 结果期约#已落定
                                    结果期约.解决(None)#空
                                    return 结果期约#期约
                                ssh请求对等(套接字对象,套接字对象,输出快照帧上限(模式['maxBytes']),1,处理快照)#对等
                            else:#管道
                                套接字对象.end()#半关写
                                输出=自身.out if 名=='stdout' else 自身.err#贯通
                                def 关套接字(套接字对象=套接字对象):#输出关则毁传输
                                    '毁套接字'
                                    套接字对象.destroy()#毁
                                输出.once('close',关套接字)#关
                                def 传输关(输出=输出,关套接字=关套接字):#摘
                                    '摘 close 监听'
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
                except Exception as 错误:#接线失败或已中止
                    启动失败(错误)#失败
                    return#已落定
                def 启动已确认(启动值):
                    'process.start 确认：已提交'
                    自身._已提交=True#确认
                    已启动.解决(None)#完
                自身.ssh.请求('process.start',{'id':自身.id},空模式,自身.控制器.信号).然后(启动已确认,启动失败)#start
            期约.全部(连接期约表).然后(已连接,启动失败)#全部连好
        自身.ssh.请求('process.prepare',参数,已准备模式,自身.控制器.信号).然后(已准备,启动失败)#预留
        return 已启动#期约

    def 终止(自身):#幂等
        '未提交则中止分配；已提交则 process.terminate'
        if 自身._静止 or 自身._终止任务 is not None:#已
            return#忽略
        if not 自身._已提交:#尚未确认
            自身.控制器.中止(ssh错误('SSH process terminated before launch acknowledgement'))#中止
        if 自身.id is not None:#有 id
            终止任务=期约()#终止结果，终止请求结算后落定
            自身._终止任务=终止任务#先登记，别处据此判断终止在进行
            def 终止成功(终止值):
                '远端确认终止：范围已空'
                自身._静止=True#空
                终止任务.解决(None)#完
            def 终止失败(错误):
                '无法确认终止的连接必须放掉租期，再以原错误拒绝'
                自身.ssh.拆除()#放租期，拆除失败没有调用方可接
                终止任务.拒绝(错误)#拒绝
            自身.ssh.请求('process.terminate',{'id':自身.id},空模式).然后(终止成功,终止失败)#终止

    def 关闭流(自身):#关掉公开流
        '毁套接字与贯通管'
        for 套接字对象 in 自身.套接字表:#套接字
            套接字对象.destroy()#毁
        for 流 in (自身.inbound,自身.out,自身.err,自身.toControl,自身.fromControl,自身.control):#管
            if 流 is not None:#有
                流.destroy()#毁

    def 等待退出(自身,信号=None):#观察托管范围
        '取消返回 False，不停止进程。返回期约，兑现进程范围是否已空'
        结果=期约()#观察结果
        if 自身._静止:#已空
            结果.解决(True)#空
            return 结果#已落定
        if 已中止(信号):#先中止
            结果.解决(False)#假
            return 结果#已落定
        if 信号 is None:#无取消
            return 自身._观察退出()#观察
        取消=期约()#调用方取消观察时兑现 False
        def 监视():#等
            '置位后以 False 解决取消期约'
            信号.wait()#等
            取消.解决(False)#假
        threading.Thread(target=监视,daemon=True).start()#监视
        return 期约.竞速([自身._观察退出(信号),取消])#观察与取消谁先到谁决定

    def _观察退出(自身,信号=None):#process.wait
        '返回期约，兑现范围是否已空；启动失败则先等终止结束'
        结果=期约()#观察结果
        def 静止了(落定值=None):
            '范围已空：记下并兑现 True'
            自身._静止=True#空
            结果.解决(True)#空
        def 启动失败(错误):
            '启动失败的错误留在 done 上；已准备的进程要先等终止结束'
            if 自身._终止任务 is not None:#有终止
                自身._终止任务.然后(静止了,结果.拒绝)#等终止，终止失败则拒绝
                return#已挂接
            静止了()#没有终止在进行
        def 得到观察结果(范围已空):
            'process.wait 兑现：已空则记下'
            if 范围已空:#空
                自身._静止=True#空
            结果.解决(范围已空)#是否空
        def 启动成功(启动值):
            '启动成功后：已终止则等终止结束，否则向远端观察'
            if 自身._终止任务 is not None:#已终止
                自身._终止任务.然后(静止了,结果.拒绝)#等终止
                return#已挂接
            自身.ssh.请求('process.wait',{'id':自身.id},布尔模式,信号,True).然后(得到观察结果,结果.拒绝)#观察
        自身._已启动.然后(启动成功,启动失败)#等启动落定
        return 结果#期约

    def _排空输出(自身):#graceMs 内排空管道
        '收集模式不等管道 EOF。返回期约，兑现于管道全部结束或宽限到期'
        排空完成=期约()#排空结果
        def 等流结束(流):
            '返回期约，兑现于该流 end、close、error 之一先到，随即摘掉其余监听'
            已结束=期约()#本流结束
            def 完(*参数):
                '首个事件到达：摘掉全部监听后解决'
                for 事件 in ('end','close','error'):#摘监听
                    流.off(事件,完)#摘
                已结束.解决(None)#结束
            for 事件 in ('end','close','error'):#登记监听
                流.on(事件,完)#登记
            return 已结束#期约
        输出等待=[]#还没结束的流
        for 名 in ('stdout','stderr'):#两路
            if isinstance(自身.规格['stdio'][名],dict):#收集
                continue#跳
            流=自身.out if 名=='stdout' else 自身.err#贯通
            if 流.readableEnded or 流.destroyed:#已结束
                continue#跳
            输出等待.append(等流结束(流))#登记
        if len(输出等待)==0:#没有要等的管道
            排空完成.解决(None)#立刻
            return 排空完成#已落定
        def 宽限执行器(解决,拒绝):
            '管道迟迟不结束也不能一直等，宽限后放行'
            定时=threading.Timer(自身.规格['graceMs']/1000.0,解决)#宽限
            定时.daemon=True#守护
            定时.start()#武装
        期约.竞速([期约.全部(输出等待),期约(宽限执行器)]).然后(排空完成.解决)#管道全到或宽限先到
        return 排空完成#期约

class ssh子进程运行时(子进程运行时):#与 SSH 文件系统配对
    '远端辅助选择 POSIX 进程归属'
    inject=依赖
    def __init__(自身,上下文):#构造
        '登记拆除'
        super().__init__(上下文)#subprocess
        自身.存活=set()#普通句柄
        自身.终端表=set()#终端
        自身.终端分配=set()#进行中分配的期约
        自身.寿命=中止控制器()#寿命
        def 拆除效果():#fiber
            '停全部'
            def 清理():#拆除器
                '终止并确认；返回期约，兑现于全部确认，任一失败则聚合拒绝'
                自身.寿命.中止(ssh错误('SSH subprocess provider disposed'))#中止
                for 远端进程句柄 in list(自身.存活):#普通
                    远端进程句柄.终止()#终止
                失败=[]#错误
                def 记录失败(错误):
                    '某一路清理失败，记下'
                    失败.append(错误)#收
                def 只记清理错误(错误):
                    '终端分配失败只有远端清理错误才算清理失败，其它分配失败由创建路径自己报'
                    if isinstance(错误,远端清理错误):#提升
                        失败.append(错误)#收
                def 等句柄退出(远端进程句柄):
                    '返回期约：等句柄退出，不论成败都关流，失败记下'
                    退出完成=期约()#本句柄
                    def 退出了(退出值):
                        '退出后关流'
                        远端进程句柄.关闭流()#关
                        退出完成.解决(None)#完
                    def 退出失败(错误):
                        '退出失败：记下，仍要关流'
                        记录失败(错误)#收
                        远端进程句柄.关闭流()#关
                        退出完成.解决(None)#完
                    远端进程句柄.等待退出().然后(退出了,退出失败)#等
                    return 退出完成#期约
                等待列表=[等句柄退出(远端进程句柄) for 远端进程句柄 in list(自身.存活)]#普通进程
                for 分配 in list(自身.终端分配):#分配
                    分配.捕获(只记清理错误)#失败按种类记下
                    等待列表.append(分配)#等它结算
                for 远端进程句柄 in list(自身.终端表):#终端
                    终止期约=远端进程句柄.终止()#终止
                    终止期约.捕获(记录失败)#失败记下
                    等待列表.append(终止期约)#等它结算
                清理结果=期约()#整体结果
                def 全部结算后(结算值):
                    '全部结算后，有失败则聚合拒绝'
                    if len(失败)>0:#有
                        清理结果.拒绝(聚合错误(失败,'SSH process cleanup could not be confirmed'))#聚合
                        return#已落定
                    清理结果.解决(None)#干净
                if len(等待列表)==0:#没有要等的
                    全部结算后(None)#直接收口
                else:#有
                    期约.全部已结算(等待列表).然后(全部结算后)#全部结算后收口
                return 清理结果#期约
            return 清理#拆除器
        上下文.副作用(拆除效果,'ssh.subprocess')#登记

    def 解析可执行文件(自身,命令,环境=None,信号=None):#远端查找
        '返回期约，兑现远端路径；未命中提升为可执行未找到错误'
        def 转换未找到(错误):
            '带码的远端错误里，未找到提升为可执行未找到错误，其余原样'
            if isinstance(错误,远程操作错误) and 错误.code=='SUBPROCESS_EXECUTABLE_NOT_FOUND':#未找到
                raise 可执行未找到错误(str(错误),错误)#提升
            raise 错误#原样
        return 自身.所属上下文.ssh.请求('executable',{'command':命令,'env':环境},远端路径,信号).捕获(转换未找到)#路径

    def 终端环境(自身,信号=None):#远端壳事实
        'platform 与可选 defaultShell'
        def 环境模式(值):#校验
            'posix/windows'
            if not isinstance(值,dict) or 值.get('platform') not in ('posix','windows'):#非法
                raise ssh错误('expected terminal environment')#失败
            结果={'platform':值['platform']}#平台
            if 值.get('defaultShell') is not None:#有默认
                结果['defaultShell']=值['defaultShell']#壳
            return 结果#环境
        return 自身.所属上下文.ssh.请求('terminal.environment',{},环境模式,信号)#环境

    def 启动(自身,规格):#普通 spawn
        '立即返回句柄'
        若已中止则抛出(自身.寿命.信号)#已拆
        若已中止则抛出(规格.get('signal'))#已中止
        远端进程句柄=远端进程(自身.所属上下文.ssh,规格)#句柄
        自身.存活.add(远端进程句柄)#登记
        def 摘除句柄(落定值=None):
            '句柄退出、静止、流关闭之后（或其中任一步失败）不再登记为存活'
            自身.存活.discard(远端进程句柄)#摘
        def 等流关(静止值):
            '静止后等流关闭'
            远端进程句柄.streamsClosed.然后(摘除句柄,摘除句柄)#流关
        def 等静止(退出值):
            '退出后等进程范围静止'
            远端进程句柄.等待退出().然后(等流关,摘除句柄)#静止
        远端进程句柄.done.然后(等静止,摘除句柄)#退出
        return 远端进程句柄#句柄

    def 启动终端(自身,规格):#PTY
        '返回期约，兑现终端句柄；分配失败时尝试远端清理，清理未知则以远端清理错误拒绝'
        try:#前置检查
            若已中止则抛出(自身.寿命.信号)#已拆
            信号=自身.寿命.信号 if 'signal' not in 规格 else 合成信号(规格['signal'],自身.寿命.信号)#融合
            若已中止则抛出(信号)#已中止
        except Exception as 错误:#已拆或已中止
            未分配=期约()#拒绝结果
            未分配.拒绝(错误)#拒绝
            return 未分配#已落定
        分配=自身._创建终端(规格,信号)#分配的期约
        自身.终端分配.add(分配)#登记
        def 摘除分配(落定值):
            '分配结算后不再登记'
            自身.终端分配.discard(分配)#摘
        分配.然后(摘除分配,摘除分配)#成败都摘
        return 分配#句柄

    def _创建终端(自身,规格,信号):#prepare/connect/start
        '返回期约，兑现终端句柄；失败则 terminate，清理失败升远端清理错误'
        结果=期约()#分配结果
        ssh=自身.所属上下文.ssh#连接
        标识=None#预留 id，准备成功后才有
        套接字对象=None#流，连上后才有
        def 失败后清理(错误):
            '准备之后的任何失败：毁套接字，远端终止；终止失败则放掉连接并升远端清理错误'
            if 套接字对象 is not None:#有
                套接字对象.destroy()#毁
            def 清理成功(清理值):
                '远端清理成功，以原错误拒绝'
                结果.拒绝(错误)#原样
            def 清理失败(清理错误):
                '远端清理结果未知：放掉连接，聚合两个错误拒绝'
                ssh.拆除()#放租期，拆除失败没有调用方可接
                结果.拒绝(远端清理错误([错误,清理错误],'SSH terminal allocation failed and remote cleanup is unknown'))#聚合
            ssh.请求('process.terminate',{'id':标识},空模式).然后(清理成功,清理失败)#终止
        def 已准备(已准备值):
            '预留好后连接终端流'
            nonlocal 标识#记下预留 id
            标识=已准备值['id']#id
            try:#中止检查
                若已中止则抛出(信号)#中止
            except Exception as 错误:#已中止
                失败后清理(错误)#清理
                return#已落定
            ssh.连接流(流端点模式(已准备值['streams']['terminal']),信号).然后(已连接,失败后清理)#连
        def 已连接(流):
            '终端流连好后半关写、接输出，再发起 process.start'
            nonlocal 套接字对象#记下流
            套接字对象=流#流
            try:#接线
                若已中止则抛出(信号)#中止
                套接字对象.end()#半关写
                输出=贯通管道()#输出
                套接字对象.pipe(输出)#转
            except Exception as 错误:#已中止或接线失败
                失败后清理(错误)#清理
                return#已落定
            def 正pid(值):#start 结果
                '正整数 pid'
                if not isinstance(值,dict) or not isinstance(值.get('pid'),int) or isinstance(值.get('pid'),bool) or 值['pid']<=0:#非法
                    raise ssh错误('expected positive pid')#失败
                return 值#结果
            def 已启动(启动值):
                '终端已启动：组装终端句柄'
                try:#中止检查
                    若已中止则抛出(信号)#中止
                except Exception as 错误:#已中止
                    失败后清理(错误)#清理
                    return#已落定
                def 转为退出结果(完成结果):
                    'process.done 兑现后取出退出结果'
                    return {'exitCode':完成结果['outcome']['exitCode'],'signal':完成结果['outcome']['signal']}#退出
                完成=ssh.请求('process.done',{'id':标识},完成模式,None,True).然后(转为退出结果)#退出事实
                关闭中=None#terminate 合并：终止请求发出后共用同一个期约
                远端进程句柄=type('终端句柄',(),{})()#实例
                远端进程句柄.pid=启动值['pid']#pid
                远端进程句柄.output=输出#输出
                远端进程句柄.done=完成#完成
                def 调整尺寸(列,行):#resize
                    '远端尺寸，返回期约'
                    return ssh.请求('terminal.resize',{'id':标识,'cols':列,'rows':行},空模式)#调
                def 写入(数据):#write
                    '原始输入，返回期约'
                    return ssh.请求('terminal.write',{'id':标识,'value':数据},空模式)#写
                def 检查前台():#inspect
                    '可空前台，返回期约'
                    return ssh.请求('terminal.inspect',{'id':标识},前台模式)#观察
                def 检查活动():#activity
                    'shell 活动，返回期约'
                    return ssh.请求('terminal.activity',{'id':标识},终端活动模式)#活动
                def 发信号前台(信号名):#signal
                    '投递，返回期约，兑现组 id'
                    def 正整数(值):#组 id
                        '正整数'
                        if isinstance(值,bool) or not isinstance(值,int) or 值<=0:#非法
                            raise ssh错误('expected process group id')#失败
                        return 值#id
                    return ssh.请求('terminal.signal',{'id':标识,'value':信号名},正整数)#组
                def 终止():#terminate
                    '合并进行中的终止，返回期约；失败后允许重试'
                    nonlocal 关闭中#改外层
                    if 关闭中 is not None:#已有
                        return 关闭中#共用
                    本次终止=期约()#本次终止结果
                    关闭中=本次终止#先登记
                    def 终止成功(终止值):
                        '远端确认终止：毁流并摘掉登记'
                        if 套接字对象 is not None:#有
                            套接字对象.destroy()#毁
                        输出.destroy()#毁
                        自身.终端表.discard(远端进程句柄)#摘
                        本次终止.解决(None)#完
                    def 终止失败(终止错误):
                        '终止失败：允许重试，拒绝本次'
                        nonlocal 关闭中#改外层
                        关闭中=None#允许重试
                        本次终止.拒绝(终止错误)#拒绝
                    ssh.请求('process.terminate',{'id':标识},空模式,None,True).然后(终止成功,终止失败)#终止
                    return 本次终止#期约
                远端进程句柄.调整尺寸=调整尺寸#方法
                远端进程句柄.写入=写入#方法
                远端进程句柄.检查前台=检查前台#方法
                远端进程句柄.检查活动=检查活动#方法
                远端进程句柄.发信号前台=发信号前台#方法
                远端进程句柄.终止=终止#方法
                def 中止时():#信号
                    '终止；失败则拆连接'
                    def 终止失败后拆连接(错误):
                        '终止失败：放掉连接'
                        ssh.拆除()#拆，拆除失败没有调用方可接
                    远端进程句柄.终止().捕获(终止失败后拆连接)#终止
                if 信号 is not None:#有
                    def 监视():#等
                        '置位后中止'
                        信号.wait()#等
                        中止时()#终止
                    threading.Thread(target=监视,daemon=True).start()#监视
                自身.终端表.add(远端进程句柄)#登记
                结果.解决(远端进程句柄)#句柄
            ssh.请求('process.start',{'id':标识},正pid,信号).然后(已启动,失败后清理)#start
        ssh.请求('process.prepare',{
            'argv':规格['argv'],#参数
            'cwd':规格['cwd'],#目录
            'env':环境墓碑(规格.get('env')),#环境
            'graceMs':规格['graceMs'],#宽限
            'terminal':{'rows':规格['rows'],'cols':规格['cols'],'terminalType':规格['terminalType'],'shellActivity':规格.get('shellActivity')},#终端
        },已准备模式,信号).然后(已准备,结果.拒绝)#预留，准备失败无需清理
        return 结果#期约

inject=依赖
default=ssh子进程运行时
