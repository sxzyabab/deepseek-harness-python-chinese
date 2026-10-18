'每个智能体一条到每用户原生截图进程的字节连接'
import hashlib,json,os,select,socket,stat,threading,time
from ..计算机操作.原生客户端 import 字节流,若已中止则抛出
from .原生构建 import 等到
from ...内核.智能体循环.中止与并发 import 中止控制器,已中止

__all__=['创建共享原生通道']

握手字节上限=8192#握手行上限
可重试码=('ENOENT','ECONNREFUSED','ECONNRESET','NATIVE_EOF')#服务器还没接上

class 传输错误(Exception):
    '带稳定码的连接失败'

    def __init__(自身,码,消息,原因=None):
        '记下码和说明'
        super().__init__(消息)#说明
        自身.code=码#稳定码
        自身.message=消息#说明
        自身.cause=原因#原因
        if isinstance(原因,BaseException):#链式
            自身.__cause__=原因#链式

def 作为错误(错误):
    '不是异常的失败也收成连接错误'
    if isinstance(错误,Exception):#已经是异常
        return 错误#原样
    return 传输错误('NATIVE_CONNECT','Native connection failed',错误)#包起来

def 套接字码(错误):
    '把系统连接失败收成可重试的码'
    if isinstance(错误,FileNotFoundError):#套接字文件还没有
        错误.code='ENOENT'#可重试
    elif isinstance(错误,ConnectionRefusedError):#还没监听
        错误.code='ECONNREFUSED'#可重试
    elif isinstance(错误,ConnectionResetError):#对端重置
        错误.code='ECONNRESET'#可重试
    return 错误#带码

def 当前用户编号():
    'Windows 上与 Node 一样用 -1'
    取=getattr(os,'getuid',None)#POSIX
    if 取 is None:#没有 uid
        return -1#Node 在 Windows 上的值
    return 取()#用户编号

def 是正整数(值):
    '进程号必须是正整数'
    return isinstance(值,int) and not isinstance(值,bool) and 值>0#正整数

def 解析就绪(值,运行时键):
    '握手成功必须是 protocol 1，并且运行时身份一致'
    if not isinstance(值,dict) or set(值)!={'type','protocol','runtimeKey','pid','instanceId'}:#严格字段
        raise 传输错误('NATIVE_PROTOCOL','Native helper refused or returned an invalid handshake')#拒绝
    if 值['type']!='ready' or 值['protocol']!=1 or not isinstance(值['runtimeKey'],str):#不是就绪
        raise 传输错误('NATIVE_PROTOCOL','Native helper refused or returned an invalid handshake')#拒绝
    if not 是正整数(值['pid']) or not isinstance(值['instanceId'],str) or len(值['instanceId'])<1:#身份不完整
        raise 传输错误('NATIVE_PROTOCOL','Native helper refused or returned an invalid handshake')#拒绝
    if 值['runtimeKey']!=运行时键:#不是这一份可执行文件
        raise 传输错误('NATIVE_PROTOCOL','Native handshake returned a different runtime identity')#拒绝
    return 值#就绪

def 解析拒绝(值):
    '错误握手。不是错误对象就返回空'
    if not isinstance(值,dict) or set(值)!={'type','code','message'}:#不是严格错误
        return None#去试就绪
    if 值['type']!='error' or not isinstance(值['code'],str) or len(值['code'])<1 or not isinstance(值['message'],str):#字段不对
        return None#去试就绪
    return 值#拒绝

class 输入端:
    '写入要等到身份核对通过'

    def __init__(自身,通道):
        '挂到所属通道'
        自身._通道=通道#通道
        自身._监听={}#错误监听

    def 监听(自身,事件,回调):
        '登记错误或关闭'
        自身._监听.setdefault(事件,[]).append(回调)#追加
        def 取消():
            '摘掉'
            列表=自身._监听.get(事件,[])#列表
            if 回调 in 列表:#还在
                列表.remove(回调)#摘掉
        return 取消#取消

    def 发出(自身,事件,数据=None):
        '通知监听者'
        for 回调 in list(自身._监听.get(事件,[])):#拷贝
            if 数据 is None:#无载荷
                回调()#通知
            else:#有载荷
                回调(数据)#通知

    def 写入(自身,数据,回调=None):
        '等到套接字就绪再写。失败交给回调'
        try:#写
            if isinstance(数据,str):#文本帧
                数据=数据.encode('utf-8')#UTF-8
            自身._通道.写到套接字(数据)#写
            if 回调 is not None:#成功
                回调(None)#无错误
        except Exception as 错误:#失败
            if 回调 is not None:#回调
                回调(错误)#错误
            else:#没有回调
                raise#抛出

    def 销毁(自身,错误=None):
        '关闭通道。有错误再发出'
        自身._通道.关闭()#关闭
        if 错误 is not None:#有错误
            自身.发出('error',错误)#错误

class 共享原生通道:
    '准备或加入原生进程。写入要等到身份核对通过'

    def __init__(自身,所有者,配置):
        '启动连接。失败也会让完成结束'
        自身._所有者=所有者#子进程提供者
        自身._配置=配置#限额
        自身.标准输出=字节流()#给客户端的输出
        自身.标准输入=输入端(自身)#写入
        自身._启动=中止控制器()#连接截止和提前关闭
        自身._就绪=threading.Event()#套接字就绪
        自身._就绪错误=None#没就绪的原因
        自身._套接字=None#已连接的套接字
        自身._已连接=False#握手通过
        自身._关闭中=False#已经要求关闭
        自身._完成=threading.Event()#run 结束
        自身._完成错误=None#run 的失败
        自身._套接字结束=threading.Event()#套接字关闭
        自身._套接字错误=None#套接字关闭原因
        自身._启动器=None#短命启动进程
        自身._启动器结束=None#启动进程的两个期约
        自身._启动器已结束=False#启动进程已经收口
        自身._清理失败=None#清理超时
        超时秒=配置['connectTimeoutMs']/1000.0#连接超时秒
        def 连接超时():
            '超过连接截止'
            自身._启动.中止(传输错误('NATIVE_CONNECT_TIMEOUT','Native connection exceeded '+str(配置['connectTimeoutMs'])+'ms'))#超时
        自身._启动定时=threading.Timer(超时秒,连接超时)#定时
        自身._启动定时.daemon=True#不挡住退出
        自身._启动定时.start()#开始
        自身._清理定时=None#已连接之后的清理宽限
        threading.Thread(target=自身._跑,daemon=True).start()#连接线程

    def 关闭(自身):
        '停止写入并释放这条连接的原生状态'
        if 自身._关闭中:#已经在关
            return#无事
        自身._关闭中=True#记下
        自身._启动定时.cancel()#停连接定时
        if not 自身._已连接:#还没就绪
            自身._启动.中止(传输错误('NATIVE_CLOSED','Native connection closed before it became ready'))#拒绝就绪
            if 自身._套接字 is not None:#有套接字
                try:#拆掉
                    自身._套接字.close()#关闭
                except OSError:#已经关了
                    pass#忽略
            if not 自身._启动器已结束 and 自身._启动器 is not None:#启动进程还在
                自身._启动器.终止()#终止
        else:#已经在传数据
            try:#让对端收完
                自身._套接字.shutdown(socket.SHUT_WR)#停止写
            except OSError:#可能已经关了
                pass#忽略
            def 清理超时():
                '宽限内没清理完'
                自身._清理失败=传输错误('NATIVE_CLEANUP','Native connection did not finish cleanup within '+str(自身._配置['graceMs'])+'ms')#超时
                try:#拆掉套接字
                    自身._套接字.close()#关闭
                except OSError:#已经关了
                    pass#忽略
                自身._套接字结束.set()#不要再等
            自身._清理定时=threading.Timer(自身._配置['graceMs']/1000.0,清理超时)#宽限
            自身._清理定时.daemon=True#不挡住退出
            自身._清理定时.start()#开始

    def 等待关闭(自身):
        '阻塞到连接和它拥有的启动进程都关闭'
        自身._完成.wait()#run 结束
        if 自身._完成错误 is not None:#有失败
            raise 自身._完成错误#抛出

    def 写到套接字(自身,数据):
        '就绪之前阻塞。正在关闭则拒绝'
        自身._就绪.wait()#等到握手或失败
        if 自身._就绪错误 is not None:#没连上
            raise 自身._就绪错误#抛出
        if 自身._关闭中:#正在关
            raise 传输错误('NATIVE_CLOSED','Native connection is closing')#拒绝
        自身._套接字.sendall(数据)#写完

    def _跑(自身):
        '连接、搬运字节，然后清理'
        失败=None#连接失败
        try:#主路径
            套接字=自身._连接(自身._准备())#握手
            若已中止则抛出(自身._启动.信号)#关闭或超时
            自身._启动定时.cancel()#连上了
            自身._已连接=True#可以写
            自身._套接字=套接字#留下
            自身._就绪.set()#唤醒写入
            自身._套接字结束.wait()#等到对端关闭
        except Exception as 错误:#失败
            原因=自身._启动.信号.原因 if 已中止(自身._启动.信号) else 错误#关闭原因优先
            失败=作为错误(原因)#收成异常
            自身._就绪错误=失败#写入会看到
            自身._就绪.set()#唤醒写入
        finally:#清理
            自身._启动定时.cancel()#停
            if 自身._清理定时 is not None:#停宽限
                自身._清理定时.cancel()#停
            自身._关闭中=True#不再接受写入
            if 自身._套接字 is not None:#还有套接字
                try:#关掉
                    自身._套接字.close()#关
                except OSError:#已经关了
                    pass#忽略
            try:#收启动进程
                自身._清理()#清理
            except Exception as 错误:#清理失败
                if 自身._清理失败 is None:#还没有
                    自身._清理失败=作为错误(错误)#记下
            自身.标准输入.销毁()#输入结束
            if 自身._清理失败 is not None:#清理没完成
                自身.标准输出.销毁(自身._清理失败)#输出失败
                自身._完成错误=自身._清理失败#等待关闭会抛
            elif 失败 is not None:#连接失败
                自身.标准输出.销毁(失败)#输出失败
                自身._完成错误=失败#等待关闭会抛
            else:#正常结束
                自身.标准输出.结束()#输出结束
            自身._完成.set()#结束

    def _准备(自身):
        '解析真实可执行文件，并确认每用户运行目录'
        辅助路径=os.path.realpath(自身._配置['helperPath'])#真实路径
        若已中止则抛出(自身._启动.信号)#取消
        文件=open(辅助路径,'rb')#读内容
        try:#算摘要
            运行时键=hashlib.sha256(文件.read()).hexdigest()#内容地址
        finally:#关闭
            文件.close()#关闭
        用户=当前用户编号()#当前用户
        目录='/tmp/dsh-cua-'+str(用户)#每用户目录
        try:#创建
            os.mkdir(目录,0o700)#只有所有者
        except FileExistsError:#已经有
            pass#继续检查
        except OSError as 错误:#其他失败
            if getattr(错误,'errno',None)!=17:#不是 EEXIST
                raise#抛出
        状态=os.lstat(目录)#不跟随链接
        if not stat.S_ISDIR(状态.st_mode) or 状态.st_uid!=用户 or (状态.st_mode & 0o777)!=0o700:#必须是本人独占的真目录
            raise 传输错误('NATIVE_RUNTIME_DIRECTORY','Native runtime directory must be a real, owner-only directory owned by the current user')#拒绝
        return {'helperPath':辅助路径,'runtimeKey':运行时键,'directory':目录}#位置

    def _确保共享(自身,位置):
        '短命启动进程保证共享服务在听'
        若已中止则抛出(自身._启动.信号)#取消
        自身._启动器已结束=False#还在跑
        自身._启动器=自身._所有者.subprocess.启动({#启动
            'argv':[位置['helperPath'],'--ensure-shared','--runtime-key',位置['runtimeKey'],'--runtime-directory',位置['directory'],'--startup-timeout-ms',str(自身._配置['connectTimeoutMs'])],#参数
            'cwd':自身._配置['cwd'],#工作目录
            'graceMs':自身._配置['graceMs'],#宽限
            'signal':自身._启动.信号,#取消
            'stdio':{'stdin':'ignore','stdout':{'maxBytes':8192},'stderr':{'maxBytes':8192}},#有界
        })#句柄
        结局=等到(自身._启动器.done)#退出事实
        范围=等到(自身._启动器.等待退出())#整棵树
        自身._启动器已结束=True#收口了
        若已中止则抛出(自身._启动.信号)#取消
        if 范围 is False:#树没退出
            raise 传输错误('NATIVE_CLEANUP','Native launcher process range did not close')#没收口
        if 结局['exitCode']!=0 or 结局['signal'] is not None:#启动失败
            标准误=''#错误输出
            收集=自身._启动器.collected if isinstance(自身._启动器.collected,dict) else {}#收集
            读取器=收集.get('stderr')#标准错误
            if 读取器 is not None:#有
                标准误=读取器.自偏移读取(0).get('text') or ''#文本
            后缀=': '+标准误 if 标准误 else ''#有输出才附上
            raise 传输错误('NATIVE_STARTUP','Native launcher failed (exit '+str(结局['exitCode'])+', signal '+str(结局['signal'])+')'+后缀)#失败

    def _连接(自身,位置):
        '共享进程可能在接入前退出，这时隔 25 毫秒再试'
        while True:#直到握手通过或失败
            自身._确保共享(位置)#保证在听
            套接字=自身._连接一次(os.path.join(位置['directory'],位置['runtimeKey']+'.sock'),位置['runtimeKey'])#一次
            if 套接字 is not None:#接上了
                return 套接字#返回
            若已中止则抛出(自身._启动.信号)#取消
            time.sleep(0.025)#再试

    def _连接一次(自身,路径,运行时键):
        '连上并核对握手。还没准入就遇到可重试错误时返回空'
        若已中止则抛出(自身._启动.信号)#取消
        套接字=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)#本机套接字
        自身._套接字=套接字#关闭时能找到
        准入='pending'#还没裁定
        try:#连接和握手
            套接字.connect(路径)#连接
            你好={'type':'hello','protocol':1,'runtimeKey':运行时键,'config':{#问候
                'maxRequestBytes':自身._配置['maxRequestBytes'],'maxResponseBytes':自身._配置['maxResponseBytes'],#帧
                'axTimeoutMs':自身._配置['axTimeoutMs'],'textEventIntervalMs':自身._配置['textEventIntervalMs'],#辅助功能和按键
                'screenshotTimeoutMs':自身._配置['screenshotTimeoutMs'],'timeoutMs':自身._配置['timeoutMs'],'graceMs':自身._配置['graceMs'],#截止
            }}#问候结束
            套接字.sendall((json.dumps(你好,separators=(',',':'),ensure_ascii=False)+'\n').encode('utf-8'))#一行
            缓冲=b''#握手字节
            while b'\n' not in 缓冲:#还没一行
                若已中止则抛出(自身._启动.信号)#取消
                可读,_,_=select.select([套接字],[],[],0.05)#短等
                if len(可读)==0:#这一拍没有数据
                    continue#再看取消
                块=套接字.recv(握手字节上限)#读
                if len(块)==0:#对端关了
                    raise 传输错误('NATIVE_EOF','Native socket ended before its handshake')#没握手
                if len(缓冲)+len(块)>握手字节上限 and b'\n' not in 块[:握手字节上限-len(缓冲)]:#超限
                    准入='refused'#拒绝
                    raise 传输错误('NATIVE_PROTOCOL','Native handshake exceeded its byte limit')#超限
                缓冲+=块#留下
            换行=缓冲.index(10)#第一行
            行=缓冲[:换行]#不含换行
            其余=缓冲[换行+1:]#握手后的字节
            值=json.loads(行.decode('utf-8'))#一行 JSON
            拒绝=解析拒绝(值)#也许是拒绝
            if 拒绝 is not None:#对端拒绝
                准入='refused'#拒绝
                raise 传输错误(拒绝['code'],拒绝['message'])#用它的码
            解析就绪(值,运行时键)#必须是这一份运行时
            准入='accepted'#接受
            if len(其余)>0:#握手行后面还有响应
                自身.标准输出.发出('data',其余)#先交给客户端
            def 搬运():
                '握手之后的字节进标准输出，套接字结束不结束输出'
                try:#读到关闭
                    while not 自身._关闭中:#还开着
                        可读,_,_=select.select([套接字],[],[],0.05)#短等
                        if len(可读)==0:#没有数据
                            continue#再看
                        块=套接字.recv(65536)#读
                        if len(块)==0:#对端关了
                            break#结束
                        自身.标准输出.发出('data',块)#交给客户端
                except Exception as 错误:#读失败
                    自身._套接字错误=套接字码(作为错误(错误))#记下
                finally:#结束等待
                    自身._套接字结束.set()#主循环可以清理
            threading.Thread(target=搬运,daemon=True).start()#搬运线程
            return 套接字#已接受
        except Exception as 错误:#这次没接上
            错误=套接字码(作为错误(错误))#带码
            try:#关掉这次的套接字
                套接字.close()#关
            except OSError:#已经关了
                pass#忽略
            if 准入=='pending' and getattr(错误,'code',None) in 可重试码:#还可以再试
                return None#再来一次
            raise#不能重试
        finally:#没接受就不再读
            if 准入!='accepted':#没接上
                自身._套接字=None#清掉

    def _清理(自身):
        '终止还没结束的启动进程，并在宽限内等它和套接字'
        if not 自身._启动器已结束 and 自身._启动器 is not None:#还在跑
            自身._启动器.终止()#终止
        截止=time.perf_counter()+自身._配置['graceMs']/1000.0#宽限
        while 自身._启动器 is not None and not 自身._启动器已结束:#还没收口
            if time.perf_counter()>=截止:#超时
                raise 传输错误('NATIVE_CLEANUP','Native startup cleanup exceeded '+str(自身._配置['graceMs'])+'ms')#超时
            time.sleep(0.02)#再看
        if 自身._启动器 is not None:#有过启动进程
            范围=等到(自身._启动器.等待退出())#整棵树
            if 范围 is False:#没退出
                raise 传输错误('NATIVE_CLEANUP','Native launcher process range did not close')#没收口

def 创建共享原生通道(所有者,配置):
    '为这个智能体连接共享辅助进程'
    return 共享原生通道(所有者,配置)#一条连接
