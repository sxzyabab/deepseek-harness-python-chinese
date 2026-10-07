import os,secrets,threading,uuid,base64#路径、能力密钥、转发线程、进程 id 与尾编码
import ssl,socket,stat,shutil#TLS 监听、Unix 套接字、权限与删目录
from ...基础设施.js特性 import PromiseEX as 期约#准备、启动、完成、释放等返回的期约
from ...子进程.本地子进程 import 输出收集器,准备受管进程绑定#收集与溢出根
from ...依赖.工具 import 聚合错误#多路清理失败
from .异常 import ssh错误#本包异常基类
from .模式 import 启动模式,完成模式,输出快照帧上限#启动与完成
from .协议 import ssh请求对等#快照 RPC
from .流安全 import ssh流tls选项,套接字流#PSK 选项与套接字面

__all__=['关闭端点','收集输出转发','远端进程']#仅中文公开名

通道名=('stdin','stdout','stderr','control','terminal')#流名

def 空模式(值):#z.null
    '须为空'
    if 值 is not None:#非空
        raise ssh错误('expected null')#失败
    return 值#空

def 关闭端点(端点):#TLS、底层套接字与监听一并关
    '先关连接再关监听，返回期约，兑现于每个套接字与监听都已关闭；删目录前要等它'
    套接字表=[]#待关
    if 端点.get('socket') is not None:#已认证
        套接字表.append(端点['socket'])#收下
    套接字表.extend(端点['pending'])#未决
    去重=[]#去重后
    for 项 in 套接字表:#逐个
        if 项 not in 去重:#未见
            去重.append(项)#收下
    关闭期约列表=[]#每个套接字与监听各一个关闭期约
    for 项 in 去重:#逐个
        已关闭=期约()#本套接字关闭后解决
        if getattr(项,'closed',False):#已关
            已关闭.解决(None)#已结束
        else:#等 close
            项.once('close',已关闭.解决)#一次
        关闭期约列表.append(已关闭)#登记
        项.destroy()#毁
    监听已关=期约()#监听关闭后解决
    try:#关监听
        端点['server'].close()#关
    except OSError:#监听早已关闭，再关无副作用
        pass#无害
    监听已关.解决(None)#监听已处理
    关闭期约列表.append(监听已关)#列表因此不会为空
    return 期约.全部(关闭期约列表)#全部关闭后兑现

class 收集输出转发:#合流尾更新，捕获独立于网络读者
    '在收集继续时合并实时尾推送'
    def __init__(自身,套接字对象,收集器,最大字节):#绑 RPC
        '用快照帧上限开一对等'
        自身.对等=ssh请求对等(套接字对象,套接字对象,输出快照帧上限(最大字节),1)#一对等
        自身.收集器=收集器#收集器
        自身._脏=False#有未推尾
        自身._已停=False#已停
        自身._运行=None#进行中的冲刷期约，空闲时为 None
        def 已关(错误=None):#对等关闭
            '停止后续推送'
            自身._已停=True#停
        自身.对等.关闭回调.append(已关)#监听 closed

    def 提供(自身):#有新尾
        '标记脏并在空闲时冲刷'
        if 自身._已停:#已停
            return#忽略
        自身._脏=True#脏
        if 自身._运行 is not None:#已在冲
            return#合并
        自身._运行=期约()#冲刷期约，冲刷结束时解决
        自身._冲刷()#推第一份快照

    def _冲刷(自身):#循环推快照
        '脏则推 snapshot，每推完一份再看是否又脏，直到干净或停；结束时解决进行中的冲刷期约'
        def 收尾(落定值=None):
            '冲刷结束：摘掉运行标记并解决冲刷期约'
            运行=自身._运行#进行中的冲刷期约
            自身._运行=None#空闲
            运行.解决(None)#通知等它的结束
        def 推送失败(错误):
            '推送失败则停并关对等，再收尾'
            自身._已停=True#停
            自身.对等.关闭()#关对等
            收尾()#收尾
        def 推一份(落定值=None):
            '上一份推完（或首次）后，还脏就再推一份'
            if not (自身._脏 and not 自身._已停):#干净或已停
                收尾()#收尾
                return#结束
            自身._脏=False#先清
            快照=自身.收集器.快照()#尾
            自身.对等.请求('snapshot',{'tail':base64.b64encode(快照['bytes']).decode('ascii'),'totalBytes':快照['totalBytes']},空模式).然后(推一份,推送失败)#推
        推一份()#开始

    def 结束(自身):#最后一推
        '再提供一次，等冲刷完再关对等；返回期约'
        自身.提供()#最后
        结束完成=期约()#关对等后解决
        def 等冲刷(落定值=None):
            '冲刷还在就等它，再检查一次，冲刷空闲了才关对等'
            运行=自身._运行#当前
            if 运行 is not None:#还在
                运行.然后(等冲刷,等冲刷)#等它落定后再看
                return#等待中
            自身.对等.关闭()#关
            结束完成.解决(None)#结束
        等冲刷()#开始
        return 结束完成#调用方链式

class 远端进程:#拥有远端启动预留直到进程范围静止
    '从预留到范围静止的远端进程表'
    def __init__(自身,上下文,根,上限,准备毫秒):#记下
        '记下上下文、套接字根、句柄上限与准备超时'
        自身.上下文=上下文#宿主
        自身.根=根#套接字根
        自身.上限=上限#句柄上限
        自身.准备毫秒=准备毫秒#准备超时
        自身.记录={}#id → 记录
        自身.已完成={}#id → 完成观察期约，保留原始拒绝供迟到的完成请求读取
        自身.清理表=set()#进行中清理的期约
        自身._关闭中=False#是否关闭

    def 准备(自身,原始):#分配监听，start 前不执行目标
        '返回期约，兑现预留 id 与已认证流坐标；容量不足、请求非法或准备失败则拒绝'
        结果=期约()#准备结果
        if 自身._关闭中 or len(自身.记录)>=自身.上限:#满或关
            结果.拒绝(ssh错误('SSH process capacity unavailable'))#满
            return 结果#已落定
        try:#校验请求
            请求=启动模式(原始)#校验
        except ssh错误 as 错误:#请求非法
            结果.拒绝(错误)#拒绝
            return 结果#已落定
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
            '释放未启动预留；没有调用方可接这个期约，失败只记警告'
            def 记录释放失败(错误):
                '超时释放失败时记警告'
                自身.上下文.日志.警告(f'SSH 预留超时释放失败：{错误}')#无调用方可接
            自身.释放(标识).捕获(记录释放失败)#释放
        定时=threading.Timer(自身.准备毫秒/1000.0,到期)#超时
        定时.daemon=True#守护
        定时.start()#武装
        记录['expiry']=定时#记下
        自身.记录[标识]=记录#登记
        记录['preparing']=期约()#准备期约，建目录与端点都完成后解决，释放要等它
        def 准备失败(错误):
            '准备出错：先释放预留，释放完成后再以原错误拒绝'
            记录['preparing'].拒绝(错误)#让释放知道准备已落定
            def 释放后拒绝(落定值):
                '释放结束（无论成败）后以准备错误拒绝'
                结果.拒绝(错误)#拒绝
            自身.释放(标识).然后(释放后拒绝,释放后拒绝)#释放
        try:#建目录与端点；直接调用，因为紧接着就要等它结束
            os.mkdir(目录,0o700)#私有目录
            若已中止则抛出(记录['controller'].信号)#中止
            if 'terminal' not in 请求:#普通
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
        except BaseException as 错误:#失败则释放
            准备失败(错误)#释放后拒绝
            return 结果#已交出拒绝
        记录['preparing'].解决(None)#准备完成
        流表={}#坐标
        for 名,端点 in 记录['endpoints'].items():#逐路
            流表[名]={'path':端点['path'],'capability':端点['capability']}#坐标
        结果.解决({'id':标识,'streams':流表})#预留
        return 结果#期约

    def 启动(自身,标识,信号=None):#通道认证后启动；重复拒绝
        'PTY 请求返回 pid。返回期约，兑现 {} 或 {pid}；预留未知、重复启动、已中止或启动失败则拒绝'
        结果=期约()#启动结果
        try:#前置检查
            记录=自身.取记录(标识)#记录
            if 记录['start'] is not None:#已请求
                raise ssh错误('SSH process launch was already requested')#重复
            若已中止则抛出(信号)#已中止
        except Exception as 错误:#预留未知、重复或已中止
            结果.拒绝(错误)#拒绝
            return 结果#已落定
        def 中止时():#转发中止
            '把调用方中止写进记录控制器'
            记录['controller'].中止(ssh错误('SSH process terminated before launch acknowledgement') if 信号 is None else None)#中止
        if 信号 is not None:#有信号
            def 监视():#等
                '置位后中止'
                信号.wait()#等
                中止时()#中止
            监视线程=threading.Thread(target=监视)#监视
            监视线程.daemon=True#守护
            监视线程.start()
        def 启动成功(落定值):
            '启动成功：终端返回 pid，普通进程无 pid'
            终端=记录['terminal']#终端
            结果.解决({} if 终端 is None else {'pid':终端.pid})#终端 pid
        def 启动失败(错误):
            '启动失败：留下原拒绝作为完成观察，终止并记住，收尾后以原错误拒绝'
            失败=期约()#保留拒绝
            失败.拒绝(错误)#拒绝
            记录['done']=失败#记下
            def 收尾后拒绝(落定值):
                '失败收尾结束后以启动错误拒绝'
                结果.拒绝(错误)#原样
            自身._失败收尾(标识,记录,失败).然后(收尾后拒绝,收尾后拒绝)#收尾
        已连接列表=[端点['connected'] for 端点 in 记录['endpoints'].values()]#逐路认证期约
        def 通道都已认证(认证值):
            '所有数据通道认证后才真正启动目标'
            自身._启动一次(标识,记录)#启动目标，失败抛出即拒绝
        记录['start']=期约.全部(已连接列表).然后(通道都已认证)#启动期约
        记录['start'].然后(启动成功,启动失败)#按启动结果落定
        return 结果#期约

    def _启动一次(自身,标识,记录):#所有通道认证后 spawn
        '所有数据通道已认证后启动，认证的套接字取自各端点的 socket；关闭中则拒绝'
        记录['expiry'].cancel()#准备超时
        if 自身._关闭中:#关闭中
            raise ssh错误('SSH helper is closing')#拒绝
        若已中止则抛出(记录['controller'].信号)#中止
        请求=记录['request']#请求
        工作目录=自身.上下文.fs.进程路径(自身.上下文.fs.解析(请求['cwd'],{'signal':记录['controller'].信号}))#cwd
        若已中止则抛出(记录['controller'].信号)#中止
        环境={} if 'env' not in 请求 else {键:(None if 值 is None else 值) for 键,值 in 请求['env'].items()}#环境
        if 请求.get('terminal') is not None:#终端
            终端规格={
                'argv':请求['argv'],#参数
                'cwd':工作目录,#目录
                'env':{键:值 for 键,值 in 环境.items() if 值 is not None},#去掉墓碑
                'graceMs':请求['graceMs'],#宽限
                'signal':记录['controller'].信号,#中止
            }#规格
            终端规格.update(请求['terminal'])#尺寸与类型
            终端=自身.上下文.subprocess.启动终端(终端规格)
            记录['terminal']=终端#记下
            若已中止则抛出(记录['controller'].信号)#中止
            套接字对象=记录['endpoints']['terminal']['socket']#已认证
            输出完成=期约()#转发输出结束后解决
            def 转发输出():#输出到套接字
                '直到输出结束；转发中的错误只意味着输出到此为止，结束时都要解决输出完成'
                try:#转发
                    for 块 in 终端.output:#逐块
                        套接字对象.write(块 if isinstance(块,bytes) else 块.encode('utf-8'))#写
                except BaseException:#转发出错即停止转发，由退出观察负责结局
                    pass#对调用方无害
                finally:#无论怎样输出都到此为止
                    输出完成.解决(None)#解决
            输出线程=threading.Thread(target=转发输出)#转发
            输出线程.daemon=True#守护
            输出线程.start()
            完成=期约()#完成观察
            def 终端已退出(结局):
                '终端退出：先交出完成观察，再按 shell 活动决定是否由此回收'
                完成.解决({'outcome':结局,'spills':{},'collected':{}})#完成
                if 请求.get('terminal') is not None and 请求['terminal'].get('shellActivity') is True:#shell 活动
                    return#由客户端回收
                def 输出已结束(输出值):
                    '终端终止且输出转发结束后，记住完成'
                    自身._记住完成(标识,记录,完成)#记住
                def 终端已终止(终止值):
                    '终端静止后，等输出转发结束'
                    输出完成.然后(输出已结束)#等转发
                终端.终止().然后(终端已终止)#静止
            def 终端失败(错误):
                '终端退出观察失败：拒绝完成观察并收尾'
                完成.拒绝(错误)#拒绝
                自身._失败收尾(标识,记录,完成)#收尾
            终端.done.然后(终端已退出,终端失败)#退出
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
        普通=自身.上下文.subprocess.启动(规格)
        记录['ordinary']=普通#记下
        控制=普通.control#fd7
        if 记录['endpoints'].get('control') is not None and 控制 is None:#未建立
            raise ssh错误('Remote subprocess provider did not establish fd 7')#失败
        收集器表={}#stdout/stderr 收集
        停捕获=[]#停止捕获
        转发器表=[]#转发器
        流转发=[]#管道转发的结束期约
        for 名 in ('stdout','stderr'):#两路
            流=getattr(普通,名)#流
            模式=输入输出[名]#处置
            套接字对象=记录['endpoints'][名]['socket']#已认证
            if isinstance(模式,dict):#收集
                溢出根=准备受管进程绑定().get('spillDir','')#溢出目录
                收集器=输出收集器(模式['maxBytes'],模式['spill']['maxBytes'] if 模式.get('spill') is not None else None,名,溢出根)#收集
                收集器表[名]=收集器#记下
                转发器=收集输出转发(套接字对象,收集器,模式['maxBytes'])#转发
                转发器表.append(转发器)#登记
                def 接收(块,收集器=收集器,转发器=转发器):#闭包
                    '推入并提供'
                    收集器.推入(块)#推
                    转发器.提供()#脏
                def 读收集(流=流,接收=接收):#读线程
                    '读到 EOF'
                    try:#读
                        while True:#循环
                            块=流.read(65536) if hasattr(流,'read') else None#读
                            if not 块:
                                break#停
                            接收(块)
                    except OSError:#失败
                        pass
                读线程=threading.Thread(target=读收集)#读
                读线程.daemon=True#守护
                读线程.start()
                def 停止(流=流,收集器=收集器):#停捕获
                    '摘读并封上'
                    if hasattr(流,'destroy'):#毁流
                        流.destroy()#毁
                    收集器.封上()#封
                停捕获.append(停止)#登记
            else:#管道
                def 管道(流=流,套接字对象=套接字对象,完成表=流转发):#转发
                    '管道直到结束，结束（含出错）时解决本路的结束期约'
                    转发结束=期约()#本路结束
                    def 复制():#线程
                        '复制'
                        try:#复制
                            while True:#循环
                                块=流.read(65536) if hasattr(流,'read') else None#读
                                if not 块:
                                    break#停
                                套接字对象.write(块)#写
                        except BaseException:#转发出错即这一路到此为止，上游同样吞掉
                            pass#对调用方无害
                        finally:#无论怎样都已结束
                            转发结束.解决(None)#仍结算
                    线程=threading.Thread(target=复制)#转发
                    线程.daemon=True#守护
                    线程.start()
                    完成表.append(转发结束)#登记
                管道()
        if 记录['endpoints'].get('stdin') is not None:#stdin
            套接字对象=记录['endpoints']['stdin']['socket']#已认证
            套接字对象.end()#半关写，读方向进进程
            def 转stdin():#套接字到 stdin
                '直到结束'
                try:#转
                    while True:#循环
                        块=套接字对象.read(65536)#读
                        if not 块:
                            break#停
                        普通.stdin.write(块)#写
                    if hasattr(普通.stdin,'close'):#关
                        普通.stdin.close()#关
                except OSError:#忽略
                    pass
            入线程=threading.Thread(target=转stdin)#转发
            入线程.daemon=True#守护
            入线程.start()
        if 记录['endpoints'].get('control') is not None:#fd7
            通道=控制#双工
            套接字对象=记录['endpoints']['control']['socket']#已认证
            def 双向():#互转
                '错误则互毁'
                def 去进程():#套接到 control
                    '复制'
                    try:#复制
                        while True:#循环
                            块=套接字对象.read(65536)#读
                            if not 块:
                                break#停
                            通道.write(块)#写
                    except OSError:#失败
                        if hasattr(通道,'destroy'):#毁
                            通道.destroy()#毁
                def 去套接字():#control 到套接字
                    '复制'
                    try:#复制
                        while True:#循环
                            块=通道.read(65536) if hasattr(通道,'read') else None#读
                            if not 块:
                                break#停
                            套接字对象.write(块)#写
                    except OSError:#失败
                        套接字对象.destroy()#毁
                threading.Thread(target=去进程,daemon=True).start()#去进程
                threading.Thread(target=去套接字,daemon=True).start()#去套接字
            双向()
        完成=期约()#完成观察
        def 记录收尾失败(错误):
            '完成观察交出之后的收尾失败没有调用方可接，记警告'
            自身.上下文.日志.警告(f'SSH 进程收尾失败：{错误}')#无调用方可接
        def 进程失败(错误):
            '进程退出观察失败：停止捕获，拒绝完成观察并收尾'
            for 停止 in 停捕获:#停捕获
                停止()#停
            完成.拒绝(错误)#拒绝
            自身._失败收尾(标识,记录,完成)#收尾
        def 进程已退出(结局):
            '停捕获、结束转发器、等流或宽限、收 spill，交出完成观察后等进程范围静止再记住'
            for 停止 in 停捕获:#停捕获
                停止()#停
            转发结束列表=[转发器.结束() for 转发器 in 转发器表]#结束转发，各一个期约
            def 记住(转发值):
                '转发都结束后记住完成'
                自身._记住完成(标识,记录,完成).捕获(记录收尾失败)#记住
            def 范围已静止(静止值):
                '进程范围静止后等剩余转发结束，再记住完成'
                剩余=流转发+转发结束列表#剩余要等的转发
                期约.全部(剩余).然后(记住,记录收尾失败)#剩余里至少有两路（stdout 与 stderr 各一）
            def 流已收尾(竞速值):
                '流转发结束或宽限到期后，收集 tail 与 spill 并交出完成观察'
                溢出={}#spill
                已收集={}#collected
                for 名 in ('stdout','stderr'):#两路
                    if 名 not in 收集器表:#无
                        continue#跳
                    收集器=收集器表[名]#收集器
                    快照=收集器.快照()#尾
                    已收集[名]={'tail':base64.b64encode(快照['bytes']).decode('ascii'),'totalBytes':快照['totalBytes']}#快照
                    读=收集器.自偏移读取(0)#溢出路径
                    if 读.get('spillPath') is not None:#有
                        溢出[名]=读['spillPath']#路径
                完成.解决({'outcome':结局,'spills':溢出,'collected':已收集})#完成
                普通.等待退出().然后(范围已静止,记录收尾失败)#静止
            if len(流转发)==0:#没有管道转发，不必等流
                流已收尾(None)#直接收尾
                return#已处理
            def 宽限执行器(解决,拒绝):
                '管道转发迟迟不结束也不能一直占着进程范围，宽限后放行'
                定时=threading.Timer(请求['graceMs']/1000.0,解决)#宽限
                定时.daemon=True#守护
                定时.start()#武装
            期约.竞速([期约.全部(流转发),期约(宽限执行器)]).然后(流已收尾)#流先结束或宽限先到
        普通.done.然后(进程已退出,进程失败)#退出
        记录['done']=完成#记下

    def 完成(自身,标识):#直接结果，不声称子孙已退出
        '返回期约，兑现完成观察；启动或进程失败时保留原始拒绝'
        if 标识 in 自身.已完成:#缓存
            return 自身.已完成[标识]#原结果，已完成表里存的就是完成观察期约
        结果=期约()#完成结果
        try:#查记录
            记录=自身.取记录(标识)#记录
            if 记录['start'] is None:#未启动
                raise ssh错误('SSH process has not started')#拒绝
        except ssh错误 as 错误:#未知预留或未启动
            结果.拒绝(错误)#拒绝
            return 结果#已落定
        def 启动已落定(启动值):
            '启动成功后，完成观察落定即落定'
            记录['done'].然后(结果.解决,结果.拒绝)#跟随完成观察
        记录['start'].然后(启动已落定,结果.拒绝)#启动失败则同样拒绝
        return 结果#期约

    def 等待(自身,标识,信号=None):#观察托管范围
        '取消只停本次观察，不放掉所有权。返回期约，兑现进程范围是否已空'
        结果=期约()#观察结果
        if 标识 in 自身.已完成:#已完成
            结果.解决(True)#空
            return 结果#已落定
        try:#查记录
            记录=自身.取记录(标识)#记录
        except ssh错误 as 错误:#未知预留
            结果.拒绝(错误)#拒绝
            return 结果#已落定
        def 启动已落定(启动值):
            '启动落定后按进程种类观察'
            if 记录['ordinary'] is not None:#普通
                记录['ordinary'].等待退出(信号).然后(结果.解决,结果.拒绝)#观察
                return#已挂接
            if 记录['terminal'] is not None:#终端
                def 终端已终止(终止值):
                    '终端终止即范围为空'
                    结果.解决(True)#空
                记录['terminal'].终止().然后(终端已终止,结果.拒绝)#终止即空
                return#已挂接
            结果.拒绝(ssh错误('SSH process was not started'))#未启动
        if 记录['start'] is None:#尚未请求启动，直接走种类判断
            启动已落定(None)#种类都为空则拒绝
        else:#已请求启动
            记录['start'].然后(启动已落定,结果.拒绝)#先等启动
        return 结果#期约

    def 终止(自身,标识):#终止并等托管范围
        '与输出读者独立。返回期约，兑现于托管范围静止'
        结果=期约()#终止结果
        if 标识 in 自身.已完成:#已完成
            结果.解决(None)#空
            return 结果#已落定
        try:#查记录
            记录=自身.取记录(标识)#记录
        except ssh错误 as 错误:#未知预留
            结果.拒绝(错误)#拒绝
            return 结果#已落定
        记录['controller'].中止(ssh错误('SSH process termination requested'))#中止
        def 范围已静止(静止值):
            '进程已静止；尚未启动的预留还要释放'
            if 记录['ordinary'] is None and 记录['terminal'] is None:#尚未启动
                自身.释放(标识).然后(结果.解决,结果.拒绝)#释放预留
                return#已挂接
            结果.解决(None)#空
        if 记录['ordinary'] is not None:#普通
            记录['ordinary'].终止()#终止
            记录['ordinary'].等待退出().然后(范围已静止,结果.拒绝)#等
        elif 记录['terminal'] is not None:#终端
            def 终端已终止(终止值):
                '终端静止后，shell 活动的完成观察由此记住'
                if 记录['request'].get('terminal') is not None and 记录['request']['terminal'].get('shellActivity') is True and 记录['done'] is not None:#shell 活动
                    自身._记住完成(标识,记录,记录['done']).然后(范围已静止,结果.拒绝)#记住完成
                    return#已挂接
                范围已静止(None)#无需记住
            记录['terminal'].终止().然后(终端已终止,结果.拒绝)#终止
        else:#尚未启动
            范围已静止(None)#直接走释放
        return 结果#期约

    def 终端操作(自身,标识,操作,值=None):#write/inspect/activity/signal
        '对预留拥有的终端操作，返回期约，兑现操作的线结果；预留未知、无终端或信号非法则拒绝'
        结果=期约()#操作结果
        try:#查记录与参数
            终端=自身.取记录(标识)['terminal']#终端
            if 终端 is None:#无
                raise ssh错误('SSH handle does not own a terminal')#拒绝
            if 操作=='signal' and 值 not in ('SIGINT','SIGTERM','SIGKILL','SIGTSTP','SIGHUP'):#信号
                raise ssh错误('expected terminal signal')#拒绝
        except ssh错误 as 错误:#未知预留、无终端或信号非法
            结果.拒绝(错误)#拒绝
            return 结果#已落定
        def 写入完成(写入值):
            '写入没有返回值，线结果为空'
            结果.解决(None)#空
        if 操作=='write':#写
            终端.写入(值 if isinstance(值,str) else str(值)).然后(写入完成,结果.拒绝)#写
        elif 操作=='inspect':#前台
            终端.检查前台().然后(结果.解决,结果.拒绝)#观察，可空
        elif 操作=='activity':#活动
            终端.检查活动().然后(结果.解决,结果.拒绝)#观测
        else:#信号
            终端.发信号前台(值).然后(结果.解决,结果.拒绝)#组 id
        return 结果#期约

    def 调整终端尺寸(自身,标识,列,行):#不换进程
        '本地提供方接受尺寸后兑现；返回期约，预留未知或无终端则拒绝'
        try:#查记录
            终端=自身.取记录(标识)['terminal']#终端
            if 终端 is None:#无
                raise ssh错误('SSH handle does not own a terminal')#拒绝
        except ssh错误 as 错误:#未知预留或无终端
            无法调整=期约()#拒绝结果
            无法调整.拒绝(错误)#拒绝
            return 无法调整#已落定
        return 终端.调整尺寸(列,行)#调，期约由提供方返回

    def 关闭(自身):#租期或断连时停全部
        '等释放与进行中清理全部结算；返回期约，失败聚合成一条拒绝'
        结果=期约()#关闭结果
        if 自身._关闭中:#已关
            结果.解决(None)#忽略
            return 结果#已落定
        自身._关闭中=True#记下
        失败列表=[]#错误，同一个错误只记一次
        def 记录失败(错误):
            '某个释放或清理失败，记下不重复的错误'
            if not any(错误 is 已有 for 已有 in 失败列表):#未记过
                失败列表.append(错误)#记下
        等待列表=[自身.释放(标识) for 标识 in list(自身.记录.keys())]+list(自身.清理表)#释放与进行中清理
        for 项 in 等待列表:#逐个登记失败
            项.捕获(记录失败)#失败只记下，由全部已结算收口
        def 全部结算后(结算值):
            '全部结算后，有失败则聚合拒绝'
            if len(失败列表)>0:#有
                结果.拒绝(聚合错误(失败列表,'SSH remote process cleanup failed'))#聚合
                return#已落定
            结果.解决(None)#干净
        if len(等待列表)==0:#没有要等的
            全部结算后(None)#直接收口
        else:#有
            期约.全部已结算(等待列表).然后(全部结算后)#全部结算后收口
        return 结果#期约

    def 释放(自身,标识):#释放预留
        '停准备、关端点、终止进程、删目录。返回期约，兑现于释放完成；预留未知则拒绝'
        try:#查记录
            记录=自身.取记录(标识)#记录
        except ssh错误 as 错误:#未知或过期
            无记录=期约()#拒绝结果
            无记录.拒绝(错误)#拒绝
            return 无记录#已落定
        if 记录['release'] is None:#首次释放才真正做
            记录['release']=自身._跟踪清理(自身._释放体,标识,记录)#跟踪
        return 记录['release']#重复调用共用同一个期约

    def _释放体(自身,标识,记录):#一次释放
        '清超时、中止、关端点、停进程、删目录；返回期约，兑现于全部做完。各步等候的期约不论成败都继续往下'
        记录['expiry'].cancel()#超时
        记录['controller'].中止(ssh错误('SSH process reservation closed'))#中止
        完成=期约()#释放完成
        def 删除记录(落定值):
            '最后一步：摘记录，删目录'
            if 标识 in 自身.记录:#仍在
                del 自身.记录[标识]#摘
            shutil.rmtree(记录['directory'],ignore_errors=True)#删目录
            完成.解决(None)#完成
        def 终止终端(落定值):
            '终止终端'
            if 记录['terminal'] is not None:#终端
                记录['terminal'].终止().然后(删除记录,完成.拒绝)#终止
                return#已挂接
            删除记录(None)#无终端
        def 终止普通(落定值):
            '终止普通进程并等进程范围静止'
            if 记录['ordinary'] is not None:#普通
                记录['ordinary'].终止()#终止
                记录['ordinary'].等待退出().然后(终止终端,完成.拒绝)#等
                return#已挂接
            终止终端(None)#无普通进程
        def 等启动(落定值):
            '启动请求不论成败都已落定后再终止进程'
            if 记录['start'] is not None:#已启动
                记录['start'].然后(终止普通,终止普通)#等启动落定，失败也继续
                return#已挂接
            终止普通(None)#未启动
        def 关端点(落定值):
            '准备已落定后，关全部端点'
            关闭列表=[关闭端点(端点) for 端点 in 记录['endpoints'].values()]#端点
            if len(关闭列表)==0:#准备失败，一个端点也没建
                等启动(None)#无端点可关
                return#已挂接
            期约.全部(关闭列表).然后(等启动,完成.拒绝)#端点都关了才继续
        if 记录['preparing'] is not None:#准备中
            记录['preparing'].然后(关端点,关端点)#等准备落定，失败也继续
        else:#未准备
            关端点(None)#直接关
        return 完成#期约

    def 取记录(自身,标识):#查找
        '未知或过期则拒绝'
        记录=自身.记录.get(标识)
        if 记录 is None:#无
            raise ssh错误('Unknown or expired SSH process handle')#拒绝
        return 记录#记录

    def _失败收尾(自身,标识,记录,结果):#启动失败后终止并记住
        '清超时、终止、记住完成；返回期约，兑现于记住完成'
        记录['expiry'].cancel()
        收尾期约=期约()#收尾结果
        def 记住(落定值):
            '进程都静止后记住完成'
            自身._记住完成(标识,记录,结果).然后(收尾期约.解决,收尾期约.拒绝)#跟随记住的结果
        def 终止终端(落定值):
            '终止终端后记住'
            if 记录['terminal'] is not None:#终端
                记录['terminal'].终止().然后(记住,收尾期约.拒绝)#终止
                return#已挂接
            记住(None)#无终端
        if 记录['ordinary'] is not None:#普通
            记录['ordinary'].终止()#终止
            记录['ordinary'].等待退出().然后(终止终端,收尾期约.拒绝)#等
        else:#无普通进程
            终止终端(None)#看终端
        return 收尾期约#期约

    def _记住完成(自身,标识,记录,结果):#完成后关端点
        '仍是本记录且未释放才记住；返回期约，兑现于端点清理完成'
        if 自身.记录.get(标识) is not 记录 or 记录['release'] is not None:#过期
            过期=期约()#无需记住
            过期.解决(None)#忽略
            return 过期#已落定
        清理=自身._跟踪清理(自身._完成清理,记录)#清理端点
        del 自身.记录[标识]#摘活表
        自身.已完成[标识]=结果#缓存
        if len(自身.已完成)>自身.上限*4:#有界
            最旧=next(iter(自身.已完成))#插入序最旧
            del 自身.已完成[最旧]#丢
        return 清理#等清理的期约

    def _完成清理(自身,记录):#关端点删目录
        '完成后的端点与目录；返回期约，兑现于端点都已关闭、目录已删'
        完成=期约()#清理完成
        def 删目录(落定值):
            '端点都关后删目录'
            shutil.rmtree(记录['directory'],ignore_errors=True)#删
            完成.解决(None)#完成
        关闭列表=[关闭端点(端点) for 端点 in 记录['endpoints'].values()]#端点
        if len(关闭列表)==0:#没有端点
            删目录(None)#直接删
        else:#有
            期约.全部(关闭列表).然后(删目录,完成.拒绝)#都关后删
        return 完成#期约

    def _跟踪清理(自身,工作,*位置参数):#登记清理任务
        '执行返回期约的工作，并在它结算后从清理表摘掉；返回跟踪中的期约'
        清理=期约()#清理结果
        自身.清理表.add(清理)#登记
        def 摘除(落定值):
            '清理结算后不再跟踪'
            自身.清理表.discard(清理)#摘
        清理.然后(摘除,摘除)#成败都摘
        try:#工作同步部分出错也要落定
            工作(*位置参数).然后(清理.解决,清理.拒绝)#跟随工作期约
        except Exception as 错误:#工作开头就失败
            清理.拒绝(错误)#拒绝
        return 清理#期约

    def 端点(自身,路径):#私有 TLS 监听
        'PSK 身份 dsh-stream，套接字 0600'
        已连接=期约()#第一个认证套接字
        能力=secrets.token_bytes(32)#256 位
        上下文=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)#服务 TLS
        上下文.minimum_version=ssl.TLSVersion.TLSv1_2#下限
        上下文.maximum_version=ssl.TLSVersion.TLSv1_2#上限
        上下文.set_ciphers(ssh流tls选项['ciphers'])#PSK
        上下文.check_hostname=False#无主机名
        上下文.verify_mode=ssl.CERT_NONE#无证书
        def 服务psk(身份):#PSK 服务
            '仅承认 dsh-stream'
            if 身份=='dsh-stream':#匹配
                return 能力#密钥
            return None#拒绝
        上下文.set_psk_server_callback(服务psk)#PSK
        监听=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)#Unix
        端点={'path':路径,'capability':能力.hex(),'server':监听,'connected':已连接,'pending':set(),'socket':None}#端点
        def 接受循环():#接受
            '握手成功则交给 connected'
            监听失败=None#监听失败的原因
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
                        '从未决摘掉'
                        端点['pending'].discard(流)#摘
                    包装流.once('close',已关)#摘
                    def 握手(连接=连接,包装流=包装流):#TLS
                        'PSK 握手'
                        try:#包装
                            包装=上下文.wrap_socket(连接,server_side=True)#握手
                            认证=套接字流(包装)#面
                            if 端点['socket'] is not None:#已有
                                认证.destroy()#拒第二路
                                return
                            认证.pause()#暂停
                            端点['socket']=认证#记下
                            try:#关听
                                监听.close()#不再接受
                            except OSError:#已关
                                pass#忽略
                            已连接.解决(认证)#交出
                        except BaseException as 错误:#握手失败
                            包装流.destroy()#毁
                    threading.Thread(target=握手,daemon=True).start()#握手
            except BaseException as 错误:#监听失败，线程入口把错误收进期约
                监听失败=错误#记下，由 finally 唯一一次拒绝
            finally:#监听结束时若无人认证
                if 端点['socket'] is None:#无人
                    已连接.拒绝(监听失败 if 监听失败 is not None else ssh错误('SSH stream reservation closed'))#拒绝
        try:#启动听
            听线程=threading.Thread(target=接受循环)#听
            听线程.daemon=True#守护
            听线程.start()
            return 端点#端点
        except BaseException:#失败
            关闭端点(端点)#关
            raise#原样
