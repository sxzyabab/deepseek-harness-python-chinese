import os,re,sys,tempfile,shutil,threading,subprocess,time,socket#路径、平台、临时目录、删除、心跳、ssh、宽限与 Unix 套接字
from ...依赖 import cordis#服务
服务=cordis.服务#基类
from ...依赖.schemastery import 字符串字段,正整数字段,自然数字段#配置字段
from ...内核.作用域 import 操作任务#就绪与操作
from ...工具.超时 import 中止控制器,若已中止则抛出,已中止,合成信号,截止#中止与截止
from .协议 import ssh请求对等,ssh协议版本#对等
from .模式 import 握手模式,流端点模式,ssh错误#握手与流坐标
from .流安全 import 认证流,套接字流#认证与套接字面

__all__=['配置','ssh连接']#仅中文公开名

配置={#部署方持有的 SSH 身份与已安装辅助
    'host':字符串字段(),#OpenSSH 主机别名
    'node':字符串字段(),#远端 Node
    'helper':字符串字段(),#辅助入口
    'helperHash':字符串字段(格式=r'^[0-9a-f]{64}$'),#摘要
    'workspace':字符串字段(),#默认工作区
    'bootstrapPath':字符串字段(),#可选 PTC 入口
    'bootstrapHash':字符串字段(格式=r'^[0-9a-f]{64}$'),#引导摘要
    'requestTimeoutMs':正整数字段(最大=2147483647,默认值=30000),#管理截止
    'maxFrameBytes':正整数字段(最大=64*1024*1024,默认值=64*1024*1024),#帧上限
    'maxPending':正整数字段(最大=128,默认值=128),#普通未决
    'leaseMs':自然数字段(最小=3000,最大=600000,默认值=30000),#租期
}#配置结束

主机形态=re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_.@-]*\Z',re.ASCII)#主机别名
哈希形态=re.compile(r'^[0-9a-f]{64}\Z')#SHA-256

def 单引号(值):#远端 argv 引用
    """POSIX 单引号。"""
    return "'"+值.replace("'","'\\''")+"'"#引用

def 包装管道(文件):#Popen 管道面
    """给请求对等用的文件流。"""
    流=套接字流.__new__(套接字流)#不调套接字构造
    流._套接字=None#无套接字
    流._文件=文件#管道
    流._监听={'error':[],'close':[],'connect':[],'data':[],'drain':[],'secureConnect':[]}#事件
    流.closed=False#是否已关
    流._暂停事件=threading.Event()#pause
    流._暂停事件.set()#可读
    def 写(字节):#写
        """写入管道。"""
        文件.write(字节)#写
        文件.flush()#立刻
        return True#接受
    def 读(大小):#读
        """读管道。"""
        流._暂停事件.wait()#pause
        return 文件.read(大小)#读
    def 毁(错误=None):#关
        """关管道。"""
        if 流.closed:#已关
            return#忽略
        流.closed=True#记下
        流._暂停事件.set()#放行
        try:#关
            文件.close()#关
        except OSError:#已关
            pass#忽略
        if 错误 is not None:#有因
            for 回调 in list(流._监听['error']):#错误
                回调(错误 if isinstance(错误,BaseException) else ssh错误(str(错误)))#通知
        for 回调 in list(流._监听['close']):#关闭
            回调()#通知
    流.write=写#写
    流.read=读#读
    流.destroy=毁#毁
    return 流#面

class ssh连接(服务):#一局不重连的 SSH 会话
    """丢失会使全部活动操作失效。"""
    Config=配置#框架槽：类级配置
    def __init__(自身,上下文,配置值):#构造
        """校验配置并启动主连接。"""
        super().__init__(上下文,'ssh')#登记
        平台=sys.platform#平台
        if 平台!='linux' and not 平台.startswith('linux') and 平台!='darwin':#非 POSIX
            raise ssh错误('SSH runtime requires a POSIX client')#拒绝
        自身.配置值=自身._校验配置(配置值)#记下
        自身.对等=None#RPC
        自身.子进程=None#ssh 子进程
        自身.子进程已关=操作任务()#close
        自身.目录=None#本地临时
        自身.心跳=None#心跳定时
        自身._已关=False#关闭旗
        自身.寿命=中止控制器()#寿命
        自身.操作表=set()#进行中操作
        自身._拆除任务=None#拆除一次
        自身.失败=None#失败
        自身.套接字表=set()#转发套接字
        自身.下一套接字=0#流序号
        自身.远端=None#握手
        自身.就绪=操作任务()#hello
        def 启动线程():#后台启动
            """启动失败写入就绪。"""
            try:#启动
                值=自身._启动()#hello
                自身.就绪.兑现(值)#就绪
            except BaseException as 错误:#失败
                自身._失败(错误 if isinstance(错误,BaseException) else ssh错误(str(错误)))#失败
                自身.就绪.拒绝(错误)#拒绝
        threading.Thread(target=启动线程).start()#启动
        def 拆除效果():#fiber
            """拆除连接。"""
            def 清理():#拆除器
                """关连接。"""
                自身.拆除()#拆
            return 清理#拆除器
        上下文.副作用(拆除效果,'ssh.connection')#登记

    def 初始化(自身):#插件就绪
        """等到远端身份与辅助摘要验证完。"""
        自身.就绪.等待()#等

    def _校验配置(自身,配置值):#构造期校验
        """主机别名、绝对路径与成对引导字段。"""
        if not isinstance(配置值,dict):#非对象
            raise ssh错误('expected ssh config object')#失败
        主机=配置值.get('host')#别名
        if not isinstance(主机,str) or 主机形态.match(主机) is None:#非法
            raise ssh错误('expected OpenSSH host alias')#失败
        for 键 in ('node','helper','workspace'):#绝对路径
            值=配置值.get(键)#值
            if not isinstance(值,str) or not 值.startswith('/'):#非法
                raise ssh错误('expected absolute '+键)#失败
        摘要=配置值.get('helperHash')#摘要
        if not isinstance(摘要,str) or 哈希形态.match(摘要) is None:#非法
            raise ssh错误('expected helperHash')#失败
        引导路径=配置值.get('bootstrapPath')#可选
        引导摘要=配置值.get('bootstrapHash')#可选
        if (引导路径 is None)!=(引导摘要 is None):#不成对
            raise ssh错误('bootstrapPath and bootstrapHash must be paired')#失败
        if 引导路径 is not None and (not isinstance(引导路径,str) or not 引导路径.startswith('/')):#路径
            raise ssh错误('expected absolute bootstrapPath')#失败
        if 引导摘要 is not None and (not isinstance(引导摘要,str) or 哈希形态.match(引导摘要) is None):#摘要
            raise ssh错误('expected bootstrapHash')#失败
        结果=dict(配置值)#拷
        if 'requestTimeoutMs' not in 结果 or 结果['requestTimeoutMs'] is None:#默认
            结果['requestTimeoutMs']=30000#默认
        if 'maxFrameBytes' not in 结果 or 结果['maxFrameBytes'] is None:#默认
            结果['maxFrameBytes']=64*1024*1024#默认
        if 'maxPending' not in 结果 or 结果['maxPending'] is None:#默认
            结果['maxPending']=128#默认
        if 'leaseMs' not in 结果 or 结果['leaseMs'] is None:#默认
            结果['leaseMs']=30000#默认
        return 结果#配置

    @property#只读
    def 节点可执行文件(自身):#已验证远端 Node
        """配对 PTC 运行时用。"""
        if 自身.远端 is None:#未就绪
            raise ssh错误('SSH helper is not ready')#拒绝
        return 自身.远端['node']#路径

    @property#只读
    def 引导路径(自身):#已验证 PTC 入口
        """未配置则在程序执行前拒绝。"""
        if 自身.远端 is None or 自身.配置值.get('bootstrapPath') is None:#未配
            raise ssh错误('SSH PTC requires a verified bootstrapPath and bootstrapHash')#拒绝
        return 自身.配置值['bootstrapPath']#路径

    def 请求(自身,方法,参数,结果模式,信号=None,等待=False):#辅助操作
        """取消从不重放含糊变更。等待=True 时观察可超过管理截止。"""
        自身._断言开着()#开着
        自身.就绪.等待()#就绪
        自身._断言开着()#再检查
        if 等待:#观察
            有界=信号#只用调用方
        elif 信号 is None:#无信号
            句柄=截止(None,自身.配置值['requestTimeoutMs'],'ssh-request')#截止
            有界=句柄.信号#信号
        else:#融合
            句柄=截止(信号,自身.配置值['requestTimeoutMs'],'ssh-request')#融合
            有界=句柄.信号#信号
        return 自身.对等.请求(方法,参数,结果模式,有界)#请求

    def 连接流(自身,端点,信号=None):#独立通道转发
        """返回已暂停套接字；消费方挂上后再恢复。"""
        任务=操作任务()#操作
        自身.操作表.add(任务)#跟踪
        def 跑():#线程
            """建立流。"""
            try:#建立
                值=自身._建立流(端点,信号)#流
                任务.兑现(值)#完
            except BaseException as 错误:#失败
                任务.拒绝(错误)#拒绝
            finally:#摘
                自身.操作表.discard(任务)#摘
        threading.Thread(target=跑).start()#启动
        return 任务.等待()#流

    def _建立流(自身,端点,信号=None):#转发并认证
        """校验路径后 OpenSSH -L 转发，再 TLS-PSK。"""
        握手=自身.就绪.等待()#hello
        自身._断言开着()#开着
        if 信号 is None:#无调用方
            信号=自身.寿命.信号#只用寿命
        else:#融合
            信号=合成信号(信号,自身.寿命.信号)#融合
        远端=端点['path']#远端路径
        根前=握手['root']+'/'#根前缀
        if not 远端.startswith(根前) or re.search(r'[:\r\n\0]',远端) is not None:#非法
            raise ssh错误('SSH helper returned an invalid stream path')#拒绝
        若已中止则抛出(信号)#中止
        本地=os.path.join(自身.目录,'s'+str(自身.下一套接字))#本地套接字
        自身.下一套接字+=1#序号
        转发=本地+':'+远端# -L
        def 取消转发():#取消 -L
            """主控不可用则监听已没。"""
            if not 自身._已关:#仍开
                try:#取消
                    自身._控制命令(['-O','cancel','-L',转发])#取消
                except BaseException:#忽略
                    pass#吞
            if os.path.exists(本地):#残留
                try:#删
                    os.remove(本地)#删
                except OSError:#忽略
                    pass#吞
        try:#转发
            自身._控制命令(['-O','forward','-o','ExitOnForwardFailure=yes','-L',转发],信号)#转发
        except BaseException:#失败
            取消转发()#回滚
            raise#原样
        若已中止则抛出(信号)#中止
        连接=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)#Unix
        连接.connect(本地)#连
        套接字对象=套接字流(连接)#面
        自身.套接字表.add(套接字对象)#登记
        def 已关():#close
            """取消转发。"""
            自身.套接字表.discard(套接字对象)#摘
            threading.Thread(target=取消转发,daemon=True).start()#取消
        套接字对象.once('close',已关)#关时取消
        认证=认证流(套接字对象,端点['capability'],自身.配置值['requestTimeoutMs'],信号)#TLS
        自身.套接字表.add(认证)#登记认证流
        def 流出错(错误=None):#error
            """毁掉认证流。"""
            认证.destroy()#毁
        认证.on('error',流出错)#错误则毁
        def 认证关():#close
            """从表摘掉。"""
            自身.套接字表.discard(认证)#摘
        认证.once('close',认证关)#摘
        return 认证#已暂停认证流

    def 拆除(自身):#先拆远端托管再放主控
        """只跑一次。"""
        if 自身._拆除任务 is not None:#已开始
            自身._拆除任务.wait()#等
            return#结束
        完成=threading.Event()#完成
        自身._拆除任务=完成#记下
        def 跑():#一次
            """拆除体。"""
            try:#拆
                自身._拆除一次()#拆
            finally:#广播
                完成.set()#完
        threading.Thread(target=跑).start()#拆
        完成.wait()#等

    def _拆除一次(自身):#一次拆除
        """关心跳、发 close、毁套接字、杀 ssh、删目录。"""
        自身._已关=True#记下
        自身.寿命.中止(ssh错误('SSH connection is closing'))#中止
        if 自身.心跳 is not None:#心跳
            自身.心跳.cancel()#清
        try:#尽量 close
            try:#就绪
                自身.就绪.等待()#等
            except BaseException:#启动失败
                pass#吞
            if 自身.失败 is None and 自身.对等 is not None:#健康
                def 空(值):#z.null
                    """空。"""
                    return 值#空
                句柄=截止(None,自身.配置值['requestTimeoutMs'],'ssh-close')#截止
                自身.对等.请求('close',{},空,句柄.信号)#close
        finally:#本地
            if 自身.对等 is not None:#对等
                自身.对等.关闭()#关
            for 套接字对象 in reversed(list(自身.套接字表)):#TLS 先于底层
                套接字对象.destroy()#毁
            if 自身.子进程 is not None:#ssh
                自身.子进程.terminate()#TERM
                强制=threading.Timer(自身.配置值['requestTimeoutMs']/1000.0,自身.子进程.kill)#KILL
                强制.daemon=True#守护
                强制.start()#武装
                try:#等
                    自身.子进程已关.等待()#等
                finally:#清
                    强制.cancel()#清
            for 任务 in list(自身.操作表):#操作
                try:#等
                    任务.等待()#等
                except BaseException:#忽略
                    pass#吞
            if 自身.目录 is not None:#临时
                shutil.rmtree(自身.目录,ignore_errors=True)#删

    def _控制路径(自身):#主控套接字
        """master 路径。"""
        return os.path.join(自身.目录,'master')#路径

    def _断言开着(自身):#未关且未失败
        """已关或失败则抛。"""
        if 自身._已关:#关
            raise ssh错误('SSH connection is closed')#拒绝
        if 自身.失败 is not None:#失败
            raise 自身.失败#原样

    def _控制命令(自身,参数,信号=None):#ssh -S master ...
        """管理转发。"""
        信号表=[自身.寿命.信号]#寿命
        句柄=截止(None,自身.配置值['requestTimeoutMs'],'ssh-control')#截止
        信号表.append(句柄.信号)#截止
        if 信号 is not None:#调用方
            信号表.append(信号)#并上
        融合=信号表[0]#先
        for 项 in 信号表[1:]:#其余
            融合=合成信号(融合,项)#融合
        若已中止则抛出(融合)#已中止
        命令=['ssh','-S',自身._控制路径(),*参数,自身.配置值['host']]#argv
        进程=subprocess.Popen(命令,stdout=subprocess.PIPE,stderr=subprocess.PIPE)#跑
        完成=操作任务()#结果
        def 等():#等退出
            """退出码。"""
            try:#等
                码=进程.wait()#等
                if 码==0:#成功
                    完成.兑现(None)#完
                else:#失败
                    完成.拒绝(ssh错误('ssh control command failed'))#失败
            except BaseException as 错误:#失败
                完成.拒绝(错误)#拒绝
        threading.Thread(target=等).start()#等
        def 升级():#中止则 KILL
            """宽限后 KILL。"""
            强制=threading.Timer(自身.配置值['requestTimeoutMs']/1000.0,进程.kill)#KILL
            强制.daemon=True#守护
            强制.start()#武装
        if 已中止(融合):#已中止
            升级()#立刻
        else:#监视
            def 监视():#等中止
                """中止后升级。"""
                融合.wait()#等
                升级()#KILL
            threading.Thread(target=监视,daemon=True).start()#监视
        try:#等结果
            完成.等待()#等
        finally:#等进程
            进程.wait()#收尸

    def _失败(自身,错误):#只记一次
        """中止寿命、关对等、毁套接字、TERM 子进程。"""
        if 自身.失败 is not None:#已有
            return#忽略
        自身.失败=错误#记下
        自身.寿命.中止(错误)#中止
        if 自身.心跳 is not None:#心跳
            自身.心跳.cancel()#清
        if 自身.对等 is not None:#对等
            自身.对等.关闭(错误)#关
        for 套接字对象 in reversed(list(自身.套接字表)):#套接字
            套接字对象.destroy(错误)#毁
        if 自身.子进程 is not None:#ssh
            自身.子进程.terminate()#TERM

    def _启动(自身):#主连接与 hello
        """临时目录、ControlMaster、hello、心跳。"""
        自身.目录=tempfile.mkdtemp(prefix='dsh-ssh-',dir='/tmp')#临时
        if 自身._已关:#已关
            raise ssh错误('SSH connection closed before startup')#拒绝
        命令=单引号(自身.配置值['node'])+' --disable-sigusr1 '+单引号(自身.配置值['helper'])#远端 argv
        argv=[
            'ssh','-T','-M','-S',自身._控制路径(),'-o','ControlPersist=no','-o','BatchMode=yes',
            '-o','StrictHostKeyChecking=yes','-o','ForwardAgent=no','-o','ClearAllForwardings=yes',
            '-o','ServerAliveInterval=10','-o','ServerAliveCountMax=3',自身.配置值['host'],命令,
        ]#主连接
        子=subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)#ssh
        自身.子进程=子#记下
        def 等关():#close
            """子进程退出。"""
            子.wait()#等
            自身.子进程已关.兑现(None)#广播
            自身._失败(ssh错误('SSH helper disconnected; remote outcomes and cleanup are unknown'))#失败
        threading.Thread(target=等关,daemon=True).start()#等关
        def 丢弃错误():#stderr
            """消费诊断以免堵管。"""
            try:#读
                while True:#循环
                    块=子.stderr.read(65536)#读
                    if not 块:#结束
                        break#停
            except OSError:#关
                pass#吞
        threading.Thread(target=丢弃错误,daemon=True).start()#丢弃
        对等=ssh请求对等(包装管道(子.stdout),包装管道(子.stdin),自身.配置值['maxFrameBytes'],自身.配置值['maxPending'])#对等
        自身.对等=对等#记下
        def 对等关(错误=None):#closed
            """失败。"""
            自身._失败(错误 if isinstance(错误,BaseException) else ssh错误(str(错误)))#失败
        对等.关闭回调.append(对等关)#监听
        参数={
            'protocol':ssh协议版本,#版本
            'workspace':自身.配置值['workspace'],#工作区
            'leaseMs':自身.配置值['leaseMs'],#租期
        }#hello 参数
        if 自身.配置值.get('bootstrapPath') is not None:#引导
            参数['bootstrapPath']=自身.配置值['bootstrapPath']#路径
        句柄=截止(None,自身.配置值['requestTimeoutMs'],'ssh-hello')#截止
        握手=对等.请求('hello',参数,握手模式,句柄.信号)#握手
        if 握手['hash']!=自身.配置值['helperHash']:#摘要
            raise ssh错误('SSH helper digest differs from the configured artifact')#拒绝
        if 握手.get('bootstrapHash')!=自身.配置值.get('bootstrapHash'):#引导
            raise ssh错误('SSH PTC bootstrap digest differs from the configured artifact')#拒绝
        自身.远端=握手#记下
        心跳未决={'任务':None}#一次一心跳
        def 心跳一次():#心跳
            """lease/2 截止。"""
            if 心跳未决['任务'] is not None:#已有
                return#跳
            def 跑():#线程
                """heartbeat。"""
                try:#请求
                    def 空(值):#null
                        """空。"""
                        return 值#空
                    心=截止(None,自身.配置值['leaseMs']/2,'ssh-heartbeat')#截止
                    对等.请求('heartbeat',{},空,心.信号)#心跳
                except BaseException as 错误:#失败
                    自身._失败(错误 if isinstance(错误,BaseException) else ssh错误(str(错误)))#失败
                finally:#摘
                    心跳未决['任务']=None#空闲
            心跳未决['任务']=threading.Thread(target=跑)#任务
            心跳未决['任务'].daemon=True#守护
            心跳未决['任务'].start()#启动
        间隔=自身.配置值['leaseMs']//3#间隔
        def 心跳循环():#循环
            """按间隔心跳直到关闭。"""
            while not 自身._已关 and 自身.失败 is None:#仍开
                time.sleep(间隔/1000.0)#等
                if 自身._已关 or 自身.失败 is not None:#停
                    break#停
                心跳一次()#跳
        心跳线程=threading.Thread(target=心跳循环)#心跳
        心跳线程.daemon=True#守护
        心跳线程.start()#启动
        自身.心跳=type('定时',(),{'cancel':lambda 自身2: None})()#占位；循环靠 _已关
        return 握手#hello

Config=配置#框架槽
default=ssh连接#框架槽
