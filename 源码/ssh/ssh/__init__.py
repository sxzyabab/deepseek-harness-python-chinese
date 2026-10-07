import os,re,sys,tempfile,shutil,threading,subprocess,time,socket
from ...依赖.cordis.服务 import 服务
from ...依赖.schemastery import 字符串字段,正整数字段,自然数字段
from ...基础设施.js特性 import PromiseEX as 期约#就绪、请求、连接流、拆除返回的期约
from ...工具.超时 import 截止
from .协议 import ssh请求对等,ssh协议版本
from .异常 import ssh错误#本包异常基类
from .模式 import 握手模式,流端点模式
from .流安全 import 认证流,套接字流
from . import (
    ssh侧车,
    入口,
    远端进程,
)

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
哈希形态=re.compile(r'^[0-9a-f]{64}\Z',re.ASCII)#SHA-256

def 单引号(值):#远端 argv 引用
    'POSIX 单引号'
    return "'"+值.replace("'","'\\''")+"'"#引用

def 包装管道(文件):#Popen 管道面
    '给请求对等用的文件流'
    流=套接字流.__new__(套接字流)#不调套接字构造
    流._套接字=None#无套接字
    流._文件=文件#管道
    流._监听={'error':[],'close':[],'connect':[],'data':[],'drain':[],'secureConnect':[]}#事件
    流.closed=False#是否已关
    流._暂停事件=threading.Event()#pause
    流._暂停事件.set()#可读
    def 写(字节):#写
        '写入管道'
        文件.write(字节)#写
        文件.flush()#立刻
        return True#接受
    def 读(大小):#读
        '读管道'
        流._暂停事件.wait()#pause
        return 文件.read(大小)#读
    def 关闭流(错误=None):#关
        '关管道'
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
    流.destroy=关闭流#毁
    return 流#面

class ssh连接(服务):
    '一局不重连的 SSH 会话。丢失会使全部活动操作失效'
    Config=配置#框架槽：类级配置
    def __init__(自身,上下文,配置值):#构造
        '校验配置并启动主连接'
        super().__init__(上下文,'ssh')#登记
        平台=sys.platform#平台
        if 平台!='linux' and not 平台.startswith('linux') and 平台!='darwin':#非 POSIX
            raise ssh错误('SSH runtime requires a POSIX client')#拒绝
        自身.配置值=自身._校验配置(配置值)#记下
        自身.对等=None#RPC
        自身.子进程=None#ssh 子进程
        自身.子进程已关=期约()#子进程退出后解决
        自身.目录=None#本地临时
        自身._已关=False#关闭旗
        自身.寿命=中止控制器()#寿命
        自身.操作表=set()#进行中操作的期约
        自身._拆除任务=None#拆除一次，之后共用同一个期约
        自身.失败=None#失败
        自身.套接字表=set()#转发套接字
        自身.下一套接字=0#流序号
        自身.远端=None#握手
        自身.就绪=期约()#hello 握手兑现
        def 启动失败(错误):
            '启动失败：记失败并拒绝就绪'
            自身._失败(错误 if isinstance(错误,BaseException) else ssh错误(str(错误)))#失败
            自身.就绪.拒绝(错误)#拒绝
        def 拆除效果():#fiber
            '拆除连接'
            def 清理():#拆除器
                '关连接，返回拆除期约'
                return 自身.拆除()#拆除
            return 清理#拆除器
        上下文.副作用(拆除效果,'ssh.connection')#登记
        try:#启动主连接并发 hello
            自身._启动().然后(自身.就绪.解决,启动失败)#hello 兑现即就绪
        except BaseException as 错误:#启动的同步部分失败（临时目录、拉起 ssh）
            启动失败(错误)#失败

    def 初始化(自身):#插件就绪
        '返回就绪期约，兑现于远端身份与辅助摘要验证完'
        return 自身.就绪#就绪期约

    def _校验配置(自身,配置值):#构造期校验
        '主机别名、绝对路径与成对引导字段'
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
        '配对 PTC 运行时用'
        if 自身.远端 is None:#未就绪
            raise ssh错误('SSH helper is not ready')#拒绝
        return 自身.远端['node']#路径

    @property#只读
    def 引导路径(自身):#已验证 PTC 入口
        '未配置则在程序执行前拒绝'
        if 自身.远端 is None or 'bootstrapPath' not in 自身.配置值:#未配
            raise ssh错误('SSH PTC requires a verified bootstrapPath and bootstrapHash')#拒绝
        return 自身.配置值['bootstrapPath']#路径

    def 请求(自身,方法,参数,结果模式,信号=None,等待=False):#辅助操作
        '取消从不重放含糊变更。等待=True 时观察可超过管理截止。返回期约，兑现经校验的远端结果'
        结果=期约()#请求结果
        try:#前置检查
            自身._断言开着()#开着
        except Exception as 错误:#已关或已失败
            结果.拒绝(错误)#拒绝
            return 结果#已落定
        def 就绪后(握手值):
            '就绪后再检查一次，按截止组好信号发出请求'
            try:#再检查并组信号
                自身._断言开着()#再检查
                if 等待:#观察
                    有界=信号#只用调用方
                elif 信号 is None:#无信号
                    句柄=截止(None,自身.配置值['requestTimeoutMs'],'ssh-request')#截止
                    有界=句柄.信号#信号
                else:#融合
                    句柄=截止(信号,自身.配置值['requestTimeoutMs'],'ssh-request')#融合
                    有界=句柄.信号#信号
            except Exception as 错误:#已关或已失败
                结果.拒绝(错误)#拒绝
                return#已落定
            自身.对等.请求(方法,参数,结果模式,有界).然后(结果.解决,结果.拒绝)#请求
        自身.就绪.然后(就绪后,结果.拒绝)#就绪失败则同样拒绝
        return 结果#期约

    def 连接流(自身,端点,信号=None):#独立通道转发
        '返回期约，兑现已暂停套接字；消费方挂上后再恢复。建立中的操作被跟踪，拆除要等它们'
        操作=自身._建立流(端点,信号)#建立流的期约
        自身.操作表.add(操作)#跟踪
        def 摘除(落定值):
            '操作结算后不再跟踪'
            自身.操作表.discard(操作)#摘
        操作.然后(摘除,摘除)#成败都摘
        return 操作#流

    def _建立流(自身,端点,信号=None):#转发并认证
        '校验路径后 OpenSSH -L 转发，再 TLS-PSK。返回期约，兑现已暂停认证流'
        结果=期约()#流结果
        def 就绪后(握手):
            '就绪后校验路径，转发，连接，认证'
            nonlocal 信号#融合后的信号
            try:#校验
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
            except Exception as 错误:#校验失败
                结果.拒绝(错误)#拒绝
                return#已落定
            本地=os.path.join(自身.目录,'s'+str(自身.下一套接字))#本地套接字
            自身.下一套接字+=1#序号
            转发=本地+':'+远端# -L
            def 取消转发():#取消 -L
                '主控不可用则监听已没；返回期约，兑现于取消结束与残留套接字文件删除之后，取消命令失败也继续'
                取消完成=期约()#取消完成
                def 删残留(落定值):
                    '取消命令结算后删本地残留套接字文件'
                    if os.path.exists(本地):#残留
                        try:#删
                            os.remove(本地)#删
                        except OSError:#文件已被别处删掉，对调用方无害
                            pass#忽略
                    取消完成.解决(None)#完成
                if not 自身._已关:#仍开
                    自身._控制命令(['-O','cancel','-L',转发]).然后(删残留,删残留)#取消，失败也继续
                else:#主控已关
                    删残留(None)#只删残留
                return 取消完成#期约
            def 转发失败(错误):
                '转发失败：回滚转发后以原错误拒绝'
                def 回滚后拒绝(落定值):
                    '回滚结束后拒绝'
                    结果.拒绝(错误)#原样
                取消转发().然后(回滚后拒绝,回滚后拒绝)#回滚
            def 转发已建(转发值):
                '转发建好后连接本地套接字并 TLS-PSK 认证'
                try:#连接
                    若已中止则抛出(信号)#中止
                    连接=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)#Unix
                    连接.connect(本地)#连
                    套接字对象=套接字流(连接)#面
                except Exception as 错误:#中止或连接失败
                    结果.拒绝(错误)#拒绝
                    return#已落定
                自身.套接字表.add(套接字对象)#登记
                def 已关():#close
                    '摘掉套接字并取消转发；取消作为被跟踪的操作，拆除要等它结束'
                    自身.套接字表.discard(套接字对象)#摘
                    取消=取消转发()#取消的期约，取消命令失败已在取消转发里处理
                    自身.操作表.add(取消)#跟踪
                    def 摘除取消(落定值):
                        '取消结算后不再跟踪'
                        自身.操作表.discard(取消)#摘
                    取消.然后(摘除取消,摘除取消)#成败都摘
                套接字对象.once('close',已关)#关时取消
                def 认证成功(认证):
                    '认证成功：登记认证流并交出'
                    自身.套接字表.add(认证)#登记认证流
                    def 流出错(错误=None):#error
                        '毁掉认证流'
                        认证.destroy()#毁
                    认证.on('error',流出错)#错误则毁
                    def 认证关():#close
                        '从表摘掉'
                        自身.套接字表.discard(认证)#摘
                    认证.once('close',认证关)#摘
                    结果.解决(认证)#已暂停认证流
                认证流(套接字对象,端点['capability'],自身.配置值['requestTimeoutMs'],信号).然后(认证成功,结果.拒绝)#TLS
            自身._控制命令(['-O','forward','-o','ExitOnForwardFailure=yes','-L',转发],信号).然后(转发已建,转发失败)#转发
        自身.就绪.然后(就绪后,结果.拒绝)#就绪失败则同样拒绝
        return 结果#期约

    def 拆除(自身):#先拆远端托管再放主控
        '只跑一次，返回期约，兑现于拆除完成；重复调用共用同一个期约'
        if 自身._拆除任务 is None:#首次才真正拆除
            自身._拆除任务=自身._拆除一次()#拆除并记忆期约
        return 自身._拆除任务#共用

    def _拆除一次(自身):#一次拆除
        '发 close、毁套接字、杀 ssh、等进行中操作、删目录；返回期约，close 请求失败时本地清理照做，最后以那个错误拒绝'
        自身._已关=True#记下
        自身.寿命.中止(ssh错误('SSH connection is closing'))#中止
        拆除完成=期约()#整个拆除落定后解决
        def 空(值):#z.null
            '空'
            return 值#空
        def 本地清理(关闭错误):
            'close 请求结算后（无论成败）：关对等、毁套接字、杀 ssh、等操作、删目录，最后落定拆除期约'
            if 自身.对等 is not None:#对等
                自身.对等.关闭()#关
            套接字关闭列表=[]#每个套接字关闭后解决
            for 套接字对象 in reversed(list(自身.套接字表)):#TLS 先于底层
                已关闭=期约()#本套接字关闭后解决
                if getattr(套接字对象,'closed',False):#已关
                    已关闭.解决(None)#已结束
                else:#等 close
                    套接字对象.once('close',已关闭.解决)#一次
                套接字关闭列表.append(已关闭)#登记
                套接字对象.destroy()#毁
            def 收尾(落定值):
                '操作都结算后删临时目录，按 close 请求的结果落定'
                if 自身.目录 is not None:#临时
                    shutil.rmtree(自身.目录,ignore_errors=True)#删
                if 关闭错误 is not None:#close 请求失败过
                    拆除完成.拒绝(关闭错误)#拒绝
                    return#已落定
                拆除完成.解决(None)#完成
            def 等操作(落定值):
                '进行中的操作都结算后收尾；等的过程中可能又有新的操作入表，所以每轮重新取'
                剩余=list(自身.操作表)#进行中的操作
                if len(剩余)==0:#没有了
                    收尾(None)#收尾
                    return#结束
                期约.全部已结算(剩余).然后(等操作)#等这一批结算再看
            def 等套接字(落定值):
                '套接字都关闭后等进行中的操作'
                if len(套接字关闭列表)==0:#没有套接字
                    等操作(None)#直接等操作
                    return#已挂接
                期约.全部(套接字关闭列表).然后(等操作)#套接字都关了才继续
            if 自身.子进程 is None:#没有 ssh 子进程
                等套接字(None)#直接等套接字
                return#已挂接
            自身.子进程.terminate()#TERM
            强制=threading.Timer(自身.配置值['requestTimeoutMs']/1000.0,自身.子进程.kill)#KILL
            强制.daemon=True#守护
            强制.start()#武装
            def 子进程已退出(退出值):
                '子进程退出后撤掉强杀定时器'
                强制.cancel()#清
                等套接字(None)#继续
            自身.子进程已关.然后(子进程已退出)#等 ssh 退出
        def 发起关闭(就绪值):
            '就绪结算后（启动失败也算），健康则发 close 请求，再做本地清理'
            if 自身.失败 is None and 自身.对等 is not None:#健康
                句柄=截止(None,自身.配置值['requestTimeoutMs'],'ssh-close')#截止
                自身.对等.请求('close',{},空,句柄.信号).然后(本地清理,本地清理)#close，失败也继续清理，错误作为参数传入
                return#已挂接
            本地清理(None)#不健康，只做本地清理
        自身.就绪.然后(发起关闭,发起关闭)#等就绪结算
        return 拆除完成#期约

    def _控制路径(自身):#主控套接字
        'master 路径'
        return os.path.join(自身.目录,'master')#路径

    def _断言开着(自身):#未关且未失败
        '已关或失败则抛'
        if 自身._已关:#关
            raise ssh错误('SSH connection is closed')#拒绝
        if 自身.失败 is not None:#失败
            raise 自身.失败#原样

    def _控制命令(自身,参数,信号=None):#ssh -S master ...
        '管理转发。返回期约，兑现于命令成功退出；已中止、命令失败则拒绝'
        完成=期约()#结果
        信号表=[自身.寿命.信号]#寿命
        句柄=截止(None,自身.配置值['requestTimeoutMs'],'ssh-control')#截止
        信号表.append(句柄.信号)#截止
        if 信号 is not None:#调用方
            信号表.append(信号)#并上
        融合=信号表[0]#先
        for 项 in 信号表[1:]:#其余
            融合=合成信号(融合,项)#融合
        try:#已中止则不启动命令
            若已中止则抛出(融合)#已中止
        except Exception as 错误:#中止原因
            完成.拒绝(错误)#拒绝
            return 完成#已落定
        命令=['ssh','-S',自身._控制路径(),*参数,自身.配置值['host']]#argv
        进程=subprocess.Popen(命令,stdout=subprocess.PIPE,stderr=subprocess.PIPE)#跑
        def 等():#等退出
            '退出码'
            try:#等
                码=进程.wait()#等
            except BaseException as 错误:#线程入口，失败交给期约
                完成.拒绝(错误)#拒绝
                return#已落定
            if 码==0:#成功
                完成.解决(None)#完
            else:#失败
                完成.拒绝(ssh错误('ssh control command failed'))#失败
        threading.Thread(target=等,daemon=True).start()#等
        def 升级():#中止则 KILL
            '宽限后 KILL'
            强制=threading.Timer(自身.配置值['requestTimeoutMs']/1000.0,进程.kill)#KILL
            强制.daemon=True#守护
            强制.start()#武装
        if 已中止(融合):#已中止
            升级()#立刻
        else:#监视
            def 监视():#等中止
                '中止后升级'
                融合.wait()#等
                升级()#KILL
            threading.Thread(target=监视,daemon=True).start()#监视
        return 完成#期约

    def _失败(自身,错误):#只记一次
        '中止寿命、关对等、毁套接字、TERM 子进程'
        if 自身.失败 is not None:#已有
            return#忽略
        自身.失败=错误#记下
        自身.寿命.中止(错误)#中止
        if 自身.对等 is not None:#对等
            自身.对等.关闭(错误)#关
        for 套接字对象 in reversed(list(自身.套接字表)):#套接字
            套接字对象.destroy(错误)#毁
        if 自身.子进程 is not None:#ssh
            自身.子进程.terminate()#TERM

    def _启动(自身):#主连接与 hello
        '临时目录、ControlMaster、hello、心跳。返回期约，兑现握手结果；同步部分失败直接抛出'
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
            '子进程退出'
            子.wait()#等
            自身.子进程已关.解决(None)#广播
            自身._失败(ssh错误('SSH helper disconnected; remote outcomes and cleanup are unknown'))#失败
        threading.Thread(target=等关,daemon=True).start()#等关
        def 丢弃错误():#stderr
            '消费诊断以免堵管'
            try:#读
                while True:#循环
                    块=子.stderr.read(65536)#读
                    if not 块:#结束
                        break#停
            except OSError:#关
                pass
        threading.Thread(target=丢弃错误,daemon=True).start()#丢弃
        对等=ssh请求对等(包装管道(子.stdout),包装管道(子.stdin),自身.配置值['maxFrameBytes'],自身.配置值['maxPending'])#对等
        自身.对等=对等#记下
        def 对等关(错误=None):#closed
            '失败'
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
        def 握手已回(握手):
            'hello 兑现后校验摘要，记下远端身份并开始心跳；摘要不符抛出即拒绝就绪'
            if 握手['hash']!=自身.配置值['helperHash']:#摘要
                raise ssh错误('SSH helper digest differs from the configured artifact')#拒绝
            if 握手.get('bootstrapHash')!=自身.配置值.get('bootstrapHash'):#引导
                raise ssh错误('SSH PTC bootstrap digest differs from the configured artifact')#拒绝
            自身.远端=握手#记下
            心跳进行中=False#一次一心跳
            def 空(值):#null
                '空'
                return 值#空
            def 心跳完成(落定值):
                '心跳成功：恢复可发下一次心跳'
                nonlocal 心跳进行中#改外层
                心跳进行中=False#空闲
            def 心跳失败(错误):
                '心跳失败：整条连接失败，并恢复空闲'
                nonlocal 心跳进行中#改外层
                心跳进行中=False#空闲
                自身._失败(错误 if isinstance(错误,BaseException) else ssh错误(str(错误)))#失败
            def 心跳一次():#心跳
                'lease/2 截止'
                nonlocal 心跳进行中#改外层
                if 心跳进行中:#已有
                    return#跳
                心跳进行中=True#先标记进行中，再发请求
                心=截止(None,自身.配置值['leaseMs']/2,'ssh-heartbeat')#截止
                对等.请求('heartbeat',{},空,心.信号).然后(心跳完成,心跳失败)#心跳
            间隔=自身.配置值['leaseMs']//3#间隔
            def 心跳循环():#循环
                '按间隔心跳直到关闭'
                while not 自身._已关 and 自身.失败 is None:#仍开
                    time.sleep(间隔/1000.0)#等
                    if 自身._已关 or 自身.失败 is not None:#停
                        break#停
                    心跳一次()#跳
            心跳线程=threading.Thread(target=心跳循环)#心跳
            心跳线程.daemon=True#守护
            心跳线程.start()
            return 握手#hello
        return 对等.请求('hello',参数,握手模式,句柄.信号).然后(握手已回)#握手后校验并开始心跳

Config=配置#框架槽
default=ssh连接#框架槽
