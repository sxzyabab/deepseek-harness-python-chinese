import os,secrets,threading,uuid,base64#路径、能力密钥、转发线程、进程 id 与尾编码
import ssl,socket,stat,shutil#TLS 监听、Unix 套接字、权限与删目录
from ...内核.作用域 import 操作任务#未决连接
from ...工具.超时 import 中止控制器,若已中止则抛出#中止
from ...子进程.本地子进程 import 输出收集器,准备受管进程绑定#收集与溢出根
from ...依赖.工具 import 聚合错误#多路清理失败
from .模式 import 启动模式,完成模式,输出快照帧上限,ssh错误#启动与完成
from .协议 import ssh请求对等#快照 RPC
from .流安全 import ssh流tls选项,套接字流#PSK 选项与套接字面

__all__=['关闭端点','收集输出转发','远端进程']#仅中文公开名

通道名=('stdin','stdout','stderr','control','terminal')#流名

def 空模式(值):#z.null
    """须为空。"""
    if 值 is not None:#非空
        raise ssh错误('expected null')#失败
    return 值#空

def 关闭端点(端点):#TLS、底层套接字与监听一并关
    """先关连接再关监听，再删目录前调用。"""
    套接字表=[]#待关
    if 端点.get('socket') is not None:#已认证
        套接字表.append(端点['socket'])#收下
    套接字表.extend(端点['pending'])#未决
    去重=[]#去重后
    for 项 in 套接字表:#逐个
        if 项 not in 去重:#未见
            去重.append(项)#收下
    关闭事件=[]#关闭等待
    for 项 in 去重:#逐个
        完成=threading.Event()#关闭
        if getattr(项,'closed',False):#已关
            完成.set()#已结束
        else:#等 close
            项.once('close',完成.set)#一次
        关闭事件.append(完成)#登记
        项.destroy()#毁
    监听=端点['server']#监听
    try:#关监听
        监听.close()#关
    except OSError:#已关
        pass#忽略
    for 完成 in 关闭事件:#等套接字
        完成.wait()#等

class 收集输出转发:#合流尾更新，捕获独立于网络读者
    """在收集继续时合并实时尾推送。"""
    def __init__(自身,套接字对象,收集器,最大字节):#绑 RPC
        """用快照帧上限开一对等。"""
        自身.对等=ssh请求对等(套接字对象,套接字对象,输出快照帧上限(最大字节),1)#一对等
        自身.收集器=收集器#收集器
        自身._脏=False#有未推尾
        自身._已停=False#已停
        自身._运行=None#冲刷任务
        def 已关(错误=None):#对等关闭
            """停止后续推送。"""
            自身._已停=True#停
        自身.对等.关闭回调.append(已关)#监听 closed

    def 提供(自身):#有新尾
        """标记脏并在空闲时冲刷。"""
        if 自身._已停:#已停
            return#忽略
        自身._脏=True#脏
        if 自身._运行 is not None:#已在冲
            return#合并
        自身._运行=threading.Thread(target=自身._冲刷)#冲刷
        自身._运行.daemon=True#守护
        自身._运行.start()#启动

    def _冲刷(自身):#循环推快照
        """脏则推 snapshot 直到干净或停。"""
        try:#推
            while 自身._脏 and not 自身._已停:#还有
                自身._脏=False#先清
                快照=自身.收集器.快照()#尾
                自身.对等.请求('snapshot',{'tail':base64.b64encode(快照['bytes']).decode('ascii'),'totalBytes':快照['totalBytes']},空模式)#推
        except BaseException:#失败则停
            自身._已停=True#停
            自身.对等.关闭()#关对等
        finally:#摘运行
            自身._运行=None#空闲

    def 结束(自身):#最后一推
        """再提供一次，等冲刷完再关对等。"""
        自身.提供()#最后
        运行=自身._运行#当前
        if 运行 is not None:#还在
            运行.join()#等
        自身.对等.关闭()#关

class 远端进程:#拥有远端启动预留直到进程范围静止
    """从预留到范围静止的远端进程表。"""
    def __init__(自身,上下文,根,上限,准备毫秒):#记下
        """记下上下文、套接字根、句柄上限与准备超时。"""
        自身.上下文=上下文#宿主
        自身.根=根#套接字根
        自身.上限=上限#句柄上限
        自身.准备毫秒=准备毫秒#准备超时
        自身.记录={}#id → 记录
        自身.已完成={}#id → 完成任务
        自身.清理表=set()#进行中清理
        自身._关闭中=False#是否关闭

    def 准备(自身,原始):#分配监听，start 前不执行目标
        """返回预留 id 与已认证流坐标。"""
        if 自身._关闭中 or len(自身.记录)>=自身.上限:#满或关
            raise ssh错误('SSH process capacity unavailable')#满
        请求=启动模式(原始)#校验
        标识=str(uuid.uuid4())#进程 id
        目录=os.path.join(自身.根,标识)#私有目录
        记录={
            'request':请求,#请求
            'directory':目录,#目录
            'endpoints':{},#端点
            'controller':中止控制器(),#寿命
            'preparing':None,#准备任务
            'release':None,#释放
            'ordinary':None,#普通句柄
            'terminal':None,#终端句柄
            'start':None,#启动任务
            'done':None,#完成任务
            'expiry':None,#准备超时
        }#记录
        def 到期():#准备超时
            """释放未启动预留。"""
            try:#释放
                自身.释放(标识)#放
            except BaseException:#忽略
                pass#吞
        定时=threading.Timer(自身.准备毫秒/1000.0,到期)#超时
        定时.daemon=True#守护
        定时.start()#武装
        记录['expiry']=定时#记下
        自身.记录[标识]=记录#登记
        try:#准备监听
            记录['preparing']=操作任务()#准备
            def 做准备():#线程
                """建目录与端点。"""
                try:#准备
                    os.mkdir(目录,0o700)#私有目录
                    若已中止则抛出(记录['controller'].信号)#中止
                    if 请求.get('terminal') is None:#普通
                        名表=['stdout','stderr']#默认
                        输入输出=请求.get('stdio')#stdio
                        if 输入输出 is not None and 输入输出.get('stdin')=='pipe':#stdin 管
                            名表.append('stdin')#stdin
                        if 输入输出 is not None and 输入输出.get('control')=='pipe':#fd7
                            名表.append('control')#control
                    else:#终端
                        名表=['terminal']#仅终端
                    for 名 in 名表:#逐路
                        记录['endpoints'][名]=自身.端点(os.path.join(目录,名))#监听
                        若已中止则抛出(记录['controller'].信号)#中止
                    记录['preparing'].兑现(None)#完成
                except BaseException as 错误:#失败
                    记录['preparing'].拒绝(错误)#拒绝
            线程=threading.Thread(target=做准备)#准备
            线程.start()#启动
            记录['preparing'].等待()#等
            流表={}#坐标
            for 名,端点 in 记录['endpoints'].items():#逐路
                流表[名]={'path':端点['path'],'capability':端点['capability']}#坐标
            return {'id':标识,'streams':流表}#预留
        except BaseException:#失败则释放
            自身.释放(标识)#放
            raise#原样

    def 启动(自身,标识,信号=None):#通道认证后启动；重复拒绝
        """PTY 请求返回 pid。"""
        记录=自身.取记录(标识)#记录
        if 记录['start'] is not None:#已请求
            raise ssh错误('SSH process launch was already requested')#重复
        若已中止则抛出(信号)#已中止
        def 中止时():#转发中止
            """把调用方中止写进记录控制器。"""
            记录['controller'].中止(ssh错误('SSH process terminated before launch acknowledgement') if 信号 is None else None)#中止
        if 信号 is not None:#有信号
            def 监视():#等
                """置位后中止。"""
                信号.wait()#等
                中止时()#中止
            监视线程=threading.Thread(target=监视)#监视
            监视线程.daemon=True#守护
            监视线程.start()#启动
        记录['start']=操作任务()#启动任务
        try:#启动一次
            自身._启动一次(标识,记录)#启动
            记录['start'].兑现(None)#成功
        except BaseException as 错误:#失败
            失败=操作任务()#保留拒绝
            失败.拒绝(错误)#拒绝
            记录['done']=失败#记下
            自身._失败收尾(标识,记录,失败)#收尾
            记录['start'].拒绝(错误)#拒绝启动
            raise 错误#原样
        终端=记录['terminal']#终端
        if 终端 is None:#普通
            return {}#无 pid
        return {'pid':终端.pid}#终端 pid

    def _启动一次(自身,标识,记录):#等通道认证后 spawn
        """所有数据通道认证后启动；关闭中则拒绝。"""
        for 端点 in 记录['endpoints'].values():#逐路
            端点['connected'].等待()#等认证
        记录['expiry'].cancel()#清准备超时
        if 自身._关闭中:#关闭中
            raise ssh错误('SSH helper is closing')#拒绝
        若已中止则抛出(记录['controller'].信号)#中止
        请求=记录['request']#请求
        工作目录=自身.上下文.fs.进程路径(自身.上下文.fs.解析(请求['cwd'],{'signal':记录['controller'].信号}))#cwd
        若已中止则抛出(记录['controller'].信号)#中止
        环境={} if 请求.get('env') is None else {键:(None if 值 is None else 值) for 键,值 in 请求['env'].items()}#环境
        if 请求.get('terminal') is not None:#终端
            终端规格={
                'argv':请求['argv'],#参数
                'cwd':工作目录,#目录
                'env':{键:值 for 键,值 in 环境.items() if 值 is not None},#去掉墓碑
                'graceMs':请求['graceMs'],#宽限
                'signal':记录['controller'].信号,#中止
            }#规格
            终端规格.update(请求['terminal'])#尺寸与类型
            终端=自身.上下文.subprocess.启动终端(终端规格)#启动
            记录['terminal']=终端#记下
            若已中止则抛出(记录['controller'].信号)#中止
            套接字对象=记录['endpoints']['terminal']['connected'].等待()#已认证
            def 转发输出():#输出到套接字
                """直到输出结束。"""
                try:#转发
                    for 块 in 终端.output:#逐块
                        套接字对象.write(块 if isinstance(块,bytes) else 块.encode('utf-8'))#写
                except BaseException:#忽略
                    pass#吞
            输出线程=threading.Thread(target=转发输出)#转发
            输出线程.daemon=True#守护
            输出线程.start()#启动
            完成=操作任务()#完成
            def 等终端():#等退出
                """收成完成观察。"""
                try:#等
                    结局=终端.done.等待() if hasattr(终端.done,'等待') else 终端.done#退出
                    完成.兑现({'outcome':结局,'spills':{},'collected':{}})#完成
                    终端.终止()#静止
                    输出线程.join()#等转发
                    自身._记住完成(标识,记录,完成)#记住
                except BaseException as 错误:#失败
                    完成.拒绝(错误)#拒绝
                    自身._失败收尾(标识,记录,完成)#收尾
            等线程=threading.Thread(target=等终端)#等
            等线程.daemon=True#守护
            等线程.start()#启动
            记录['done']=完成#记下
            return#终端路径结束
        输入输出=请求['stdio']#stdio
        规格={
            'argv':请求['argv'],#参数
            'cwd':工作目录,#目录
            'env':环境,#环境
            'graceMs':请求['graceMs'],#宽限
            'signal':记录['controller'].信号,#中止
            'stdio':{
                'stdin':输入输出['stdin'],#stdin
                'stdout':'pipe',#始终管
                'stderr':'pipe',#始终管
            },#stdio
        }#规格
        if 输入输出.get('control') is not None:#fd7
            规格['stdio']['control']=输入输出['control']#control
        普通=自身.上下文.subprocess.启动(规格)#启动
        记录['ordinary']=普通#记下
        控制=普通.control#fd7
        if 记录['endpoints'].get('control') is not None and 控制 is None:#未建立
            if hasattr(普通.done,'拒绝'):#忽略后续
                pass#无
            raise ssh错误('Remote subprocess provider did not establish fd 7')#失败
        收集器表={}#stdout/stderr 收集
        停捕获=[]#停止捕获
        转发器表=[]#转发器
        转发完成=[]#结束等待
        流转发=[]#管道转发
        for 名 in ('stdout','stderr'):#两路
            流=getattr(普通,名)#流
            模式=输入输出[名]#处置
            套接字对象=记录['endpoints'][名]['connected'].等待()#已认证
            if isinstance(模式,dict):#收集
                溢出根=准备受管进程绑定().get('spillDir','')#溢出目录
                收集器=输出收集器(模式['maxBytes'],模式['spill']['maxBytes'] if 模式.get('spill') is not None else None,名,溢出根)#收集
                收集器表[名]=收集器#记下
                转发器=收集输出转发(套接字对象,收集器,模式['maxBytes'])#转发
                转发器表.append(转发器)#登记
                def 接收(块,收集器=收集器,转发器=转发器):#闭包
                    """推入并提供。"""
                    收集器.推入(块)#推
                    转发器.提供()#脏
                def 读收集(流=流,接收=接收):#读线程
                    """读到 EOF。"""
                    try:#读
                        while True:#循环
                            块=流.read(65536) if hasattr(流,'read') else None#读
                            if not 块:#结束
                                break#停
                            接收(块)#收
                    except OSError:#失败
                        pass#吞
                读线程=threading.Thread(target=读收集)#读
                读线程.daemon=True#守护
                读线程.start()#启动
                def 停止(流=流,收集器=收集器):#停捕获
                    """摘读并封上。"""
                    if hasattr(流,'destroy'):#毁流
                        流.destroy()#毁
                    收集器.封上()#封
                停捕获.append(停止)#登记
            else:#管道
                def 管道(流=流,套接字对象=套接字对象,完成表=流转发):#转发
                    """管道直到结束。"""
                    完成=操作任务()#完成
                    def 跑():#线程
                        """复制。"""
                        try:#复制
                            while True:#循环
                                块=流.read(65536) if hasattr(流,'read') else None#读
                                if not 块:#结束
                                    break#停
                                套接字对象.write(块)#写
                            完成.兑现(None)#完
                        except BaseException:#忽略
                            完成.兑现(None)#仍结算
                    线程=threading.Thread(target=跑)#转发
                    线程.daemon=True#守护
                    线程.start()#启动
                    完成表.append(完成)#登记
                管道()#启动
        if 记录['endpoints'].get('stdin') is not None:#stdin
            套接字对象=记录['endpoints']['stdin']['connected'].等待()#已认证
            套接字对象.end()#半关写，读方向进进程
            def 转stdin():#套接字到 stdin
                """直到结束。"""
                try:#转
                    while True:#循环
                        块=套接字对象.read(65536)#读
                        if not 块:#结束
                            break#停
                        普通.stdin.write(块)#写
                    if hasattr(普通.stdin,'close'):#关
                        普通.stdin.close()#关
                except OSError:#忽略
                    pass#吞
            入线程=threading.Thread(target=转stdin)#转发
            入线程.daemon=True#守护
            入线程.start()#启动
        if 记录['endpoints'].get('control') is not None:#fd7
            通道=控制#双工
            套接字对象=记录['endpoints']['control']['connected'].等待()#已认证
            def 双向():#互转
                """错误则互毁。"""
                def 去进程():#套接到 control
                    """复制。"""
                    try:#复制
                        while True:#循环
                            块=套接字对象.read(65536)#读
                            if not 块:#结束
                                break#停
                            通道.write(块)#写
                    except OSError:#失败
                        if hasattr(通道,'destroy'):#毁
                            通道.destroy()#毁
                def 去套接字():#control 到套接字
                    """复制。"""
                    try:#复制
                        while True:#循环
                            块=通道.read(65536) if hasattr(通道,'read') else None#读
                            if not 块:#结束
                                break#停
                            套接字对象.write(块)#写
                    except OSError:#失败
                        套接字对象.destroy()#毁
                threading.Thread(target=去进程,daemon=True).start()#去进程
                threading.Thread(target=去套接字,daemon=True).start()#去套接字
            双向()#启动
        完成=操作任务()#完成
        def 等普通():#等退出后收观察
            """停捕获、等流宽限、收 spill。"""
            try:#等
                结局=普通.done.等待() if hasattr(普通.done,'等待') else 普通.done#退出
                for 停止 in 停捕获:#停捕获
                    停止()#停
                for 转发器 in 转发器表:#结束转发
                    转发完成.append(操作任务())#占位
                    def 结束一个(转发器=转发器,任务=转发完成[-1]):#闭包
                        """结束转发。"""
                        try:#结束
                            转发器.结束()#结束
                            任务.兑现(None)#完
                        except BaseException:#忽略
                            任务.兑现(None)#仍结算
                    threading.Thread(target=结束一个,daemon=True).start()#结束
                宽限=threading.Event()#宽限到
                定时=threading.Timer(请求['graceMs']/1000.0,宽限.set)#宽限
                定时.daemon=True#守护
                定时.start()#武装
                def 等流():#等管道
                    """等流转发。"""
                    for 项 in 流转发:#逐个
                        项.等待()#等
                    宽限.set()#提前结束宽限
                threading.Thread(target=等流,daemon=True).start()#等流
                宽限.wait()#赛跑
                定时.cancel()#清
                溢出={}#spill
                已收集={}#collected
                for 名 in ('stdout','stderr'):#两路
                    收集器=收集器表.get(名)#收集器
                    if 收集器 is None:#无
                        continue#跳
                    快照=收集器.快照()#尾
                    已收集[名]={'tail':base64.b64encode(快照['bytes']).decode('ascii'),'totalBytes':快照['totalBytes']}#快照
                    读=收集器.自偏移读取(0)#溢出路径
                    if 读.get('spillPath') is not None:#有
                        溢出[名]=读['spillPath']#路径
                完成.兑现({'outcome':结局,'spills':溢出,'collected':已收集})#完成
                普通.等待退出()#静止
                for 项 in list(流转发)+转发完成:#等剩余
                    try:#等
                        项.等待()#等
                    except BaseException:#忽略
                        pass#吞
                自身._记住完成(标识,记录,完成)#记住
            except BaseException as 错误:#失败
                完成.拒绝(错误)#拒绝
                自身._失败收尾(标识,记录,完成)#收尾
        等线程=threading.Thread(target=等普通)#等
        等线程.daemon=True#守护
        等线程.start()#启动
        记录['done']=完成#记下

    def 完成(自身,标识):#直接结果，不声称子孙已退出
        """启动或进程失败时保留原始拒绝。"""
        if 标识 in 自身.已完成:#缓存
            return 自身.已完成[标识].等待()#原结果
        记录=自身.取记录(标识)#记录
        if 记录['start'] is None:#未启动
            raise ssh错误('SSH process has not started')#拒绝
        记录['start'].等待()#等启动
        return 记录['done'].等待()#完成

    def 等待(自身,标识,信号=None):#观察托管范围
        """取消只停本次观察，不放掉所有权。"""
        if 标识 in 自身.已完成:#已完成
            return True#空
        记录=自身.取记录(标识)#记录
        if 记录['start'] is not None:#已启动
            记录['start'].等待()#等启动
        if 记录['ordinary'] is not None:#普通
            return 记录['ordinary'].等待退出(信号)#观察
        if 记录['terminal'] is not None:#终端
            记录['terminal'].终止()#终止即空
            return True#空
        raise ssh错误('SSH process was not started')#未启动

    def 终止(自身,标识):#终止并等托管范围
        """与输出读者独立。"""
        if 标识 in 自身.已完成:#已完成
            return#空
        记录=自身.取记录(标识)#记录
        记录['controller'].中止(ssh错误('SSH process termination requested'))#中止
        if 记录['ordinary'] is not None:#普通
            记录['ordinary'].终止()#终止
            记录['ordinary'].等待退出()#等
        if 记录['terminal'] is not None:#终端
            记录['terminal'].终止()#终止
        if 记录['ordinary'] is None and 记录['terminal'] is None:#尚未启动
            自身.释放(标识)#释放预留

    def 终端操作(自身,标识,操作,值=None):#write/inspect/signal
        """对预留拥有的终端操作。"""
        终端=自身.取记录(标识)['terminal']#终端
        if 终端 is None:#无
            raise ssh错误('SSH handle does not own a terminal')#拒绝
        if 操作=='write':#写
            终端.写入(值 if isinstance(值,str) else str(值))#写
            return None#空
        if 操作=='inspect':#前台
            前台=终端.检查前台()#观察
            return 前台#可空
        if 值 not in ('SIGINT','SIGTERM','SIGKILL','SIGTSTP','SIGHUP'):#信号
            raise ssh错误('expected terminal signal')#拒绝
        return 终端.发信号前台(值)#组 id

    def 调整终端尺寸(自身,标识,列,行):#不换进程
        """本地提供方接受尺寸后返回。"""
        终端=自身.取记录(标识)['terminal']#终端
        if 终端 is None:#无
            raise ssh错误('SSH handle does not own a terminal')#拒绝
        终端.调整尺寸(列,行)#调

    def 关闭(自身):#租期或断连时停全部
        """等释放与进行中清理；失败聚合成一条。"""
        if 自身._关闭中:#已关
            return#忽略
        自身._关闭中=True#记下
        失败=[]#错误
        for 标识 in list(自身.记录.keys()):#活记录
            try:#释放
                自身.释放(标识)#放
            except BaseException as 错误:#失败
                失败.append(错误)#收
        for 项 in list(自身.清理表):#清理
            try:#等
                项.等待()#等
            except BaseException as 错误:#失败
                失败.append(错误)#收
        if len(失败)>0:#有
            raise 聚合错误(失败,'SSH remote process cleanup failed')#聚合

    def 释放(自身,标识):#释放预留
        """停准备、关端点、终止进程、删目录。"""
        记录=自身.取记录(标识)#记录
        if 记录['release'] is not None:#已释放
            记录['release'].等待()#等
            return#结束
        记录['release']=自身._跟踪清理(lambda:自身._释放体(标识,记录))#跟踪
        记录['release'].等待()#等

    def _释放体(自身,标识,记录):#一次释放
        """清超时、中止、关端点、停进程、删目录。"""
        记录['expiry'].cancel()#清超时
        记录['controller'].中止(ssh错误('SSH process reservation closed'))#中止
        if 记录['preparing'] is not None:#准备中
            try:#等
                记录['preparing'].等待()#等
            except BaseException:#忽略
                pass#吞
        for 端点 in 记录['endpoints'].values():#端点
            关闭端点(端点)#关
        if 记录['start'] is not None:#已启动
            try:#等
                记录['start'].等待()#等
            except BaseException:#忽略
                pass#吞
        if 记录['ordinary'] is not None:#普通
            记录['ordinary'].终止()#终止
            记录['ordinary'].等待退出()#等
        if 记录['terminal'] is not None:#终端
            记录['terminal'].终止()#终止
        if 标识 in 自身.记录:#仍在
            del 自身.记录[标识]#摘
        shutil.rmtree(记录['directory'],ignore_errors=True)#删目录

    def 取记录(自身,标识):#查找
        """未知或过期则拒绝。"""
        记录=自身.记录.get(标识)#查找
        if 记录 is None:#无
            raise ssh错误('Unknown or expired SSH process handle')#拒绝
        return 记录#记录

    def _失败收尾(自身,标识,记录,结果):#启动失败后终止并记住
        """清超时、终止、记住完成。"""
        记录['expiry'].cancel()#清
        if 记录['ordinary'] is not None:#普通
            记录['ordinary'].终止()#终止
            记录['ordinary'].等待退出()#等
        if 记录['terminal'] is not None:#终端
            记录['terminal'].终止()#终止
        自身._记住完成(标识,记录,结果)#记住

    def _记住完成(自身,标识,记录,结果):#完成后关端点
        """仍是本记录且未释放才记住。"""
        if 自身.记录.get(标识) is not 记录 or 记录['release'] is not None:#过期
            return#忽略
        清理=自身._跟踪清理(lambda:自身._完成清理(记录))#清理端点
        del 自身.记录[标识]#摘活表
        自身.已完成[标识]=结果#缓存
        if len(自身.已完成)>自身.上限*4:#有界
            最旧=next(iter(自身.已完成))#插入序最旧
            del 自身.已完成[最旧]#丢
        清理.等待()#等清理

    def _完成清理(自身,记录):#关端点删目录
        """完成后的端点与目录。"""
        for 端点 in 记录['endpoints'].values():#端点
            关闭端点(端点)#关
        shutil.rmtree(记录['directory'],ignore_errors=True)#删

    def _跟踪清理(自身,工作):#登记清理任务
        """结束后从表摘掉。"""
        任务=操作任务()#任务
        自身.清理表.add(任务)#登记
        def 跑():#线程
            """跑工作。"""
            try:#跑
                工作()#工作
                任务.兑现(None)#完
            except BaseException as 错误:#失败
                任务.拒绝(错误)#拒绝
            finally:#摘
                自身.清理表.discard(任务)#摘
        threading.Thread(target=跑).start()#启动
        return 任务#任务

    def 端点(自身,路径):#私有 TLS 监听
        """PSK 身份 dsh-stream，套接字 0600。"""
        已连接=操作任务()#第一个认证套接字
        能力=secrets.token_bytes(32)#256 位
        上下文=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)#服务 TLS
        上下文.minimum_version=ssl.TLSVersion.TLSv1_2#下限
        上下文.maximum_version=ssl.TLSVersion.TLSv1_2#上限
        上下文.set_ciphers(ssh流tls选项['ciphers'])#PSK
        上下文.check_hostname=False#无主机名
        上下文.verify_mode=ssl.CERT_NONE#无证书
        def 服务psk(身份):#PSK 服务
            """仅承认 dsh-stream。"""
            if 身份=='dsh-stream':#匹配
                return 能力#密钥
            return None#拒绝
        上下文.set_psk_server_callback(服务psk)#PSK
        监听=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)#Unix
        端点={'path':路径,'capability':能力.hex(),'server':监听,'connected':已连接,'pending':set(),'socket':None}#端点
        def 接受循环():#接受
            """握手成功则交给 connected。"""
            try:#听
                监听.bind(路径)#绑定
                os.chmod(路径,stat.S_IRUSR|stat.S_IWUSR)#0600
                监听.listen(8)#最多 8
                监听.settimeout(自身.准备毫秒/1000.0)#握手超时量级
                while 端点['socket'] is None:#尚未认证
                    try:#接受
                        连接,地址=监听.accept()#接受
                    except socket.timeout:#超时
                        continue#再试
                    except OSError:#关监听
                        break#停
                    包装流=套接字流(连接)#面
                    端点['pending'].add(包装流)#未决
                    def 已关(流=包装流):#close
                        """从未决摘掉。"""
                        端点['pending'].discard(流)#摘
                    包装流.once('close',已关)#摘
                    def 握手(连接=连接,包装流=包装流):#TLS
                        """PSK 握手。"""
                        try:#包装
                            包装=上下文.wrap_socket(连接,server_side=True)#握手
                            认证=套接字流(包装)#面
                            if 端点['socket'] is not None:#已有
                                认证.destroy()#拒第二路
                                return#结束
                            认证.pause()#暂停
                            端点['socket']=认证#记下
                            try:#关听
                                监听.close()#不再接受
                            except OSError:#已关
                                pass#忽略
                            已连接.兑现(认证)#交出
                        except BaseException as 错误:#握手失败
                            包装流.destroy()#毁
                    threading.Thread(target=握手,daemon=True).start()#握手
            except BaseException as 错误:#监听失败
                try:#拒绝
                    已连接.拒绝(错误)#拒绝
                except BaseException:#已结算
                    pass#忽略
            finally:#关闭时若无人
                if 端点['socket'] is None:#无人
                    try:#拒绝
                        已连接.拒绝(ssh错误('SSH stream reservation closed'))#关闭
                    except BaseException:#已结算
                        pass#忽略
        try:#启动听
            听线程=threading.Thread(target=接受循环)#听
            听线程.daemon=True#守护
            听线程.start()#启动
            return 端点#端点
        except BaseException:#失败
            关闭端点(端点)#关
            raise#原样
