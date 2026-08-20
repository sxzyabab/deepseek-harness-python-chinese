"""叠在子进程 seam 终端原语上的持久 PTY 会话。"""
import codecs,threading,time#流式解码、定时器与毫秒时钟
from cordis.工具 import 承诺,是否thenable#结算承诺与可等待判定
from terminal import 终端错误#带稳定错误码的终端错误
from .清洗 import 受控提示符,终端清洗器#受控提示符与清洗器

安全整数上限=9007199254740991#JS Number.MAX_SAFE_INTEGER
工作线程=threading.Thread#后台工作线程
定时器=threading.Timer#延迟定时器

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 是否安全整数(值):#对齐JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return abs(值)<=安全整数上限#落在安全范围
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return abs(值)<=安全整数上限#落在安全范围
    return False#其它类型

def 此刻毫秒():#对齐Date.now
    """当前毫秒时间戳。"""
    return int(time.time()*1000)#毫秒

def 字节长(文本):#UTF-8字节长度
    """对齐 Node Buffer.byteLength 的 UTF-8 字节数。"""
    return len(文本.encode('utf-8'))#UTF-8字节数

def 安排定时(回调,毫秒):#对齐setTimeout
    """安排一次延迟回调，返回可取消的定时器。"""
    器=定时器(max(0,毫秒)/1000,回调)#延迟秒
    器.daemon=True#不挡住退出
    器.start()#立刻武装
    return 器#定时器句柄

def 清定时(器):#对齐clearTimeout
    """取消尚未触发的定时器。"""
    if 器 is None:#没有定时器
        return#结束
    器.cancel()#取消

def utf8尾部(文本,最大字节):#按UTF-8字节从尾部截取
    """按 UTF-8 字节从尾部截取；超限则 truncated 为真。"""
    if 字节长(文本)<=最大字节:#未超则原样
        return {'text':文本,'truncated':False}#原样
    码点=list(文本)#按码点拆开
    字节=0#已收下的字节
    起点=len(码点)#从尾往前的起点
    while 起点>0:#还能再收一个码点
        下一个=字节长(码点[起点-1])#上一个码点字节
        if 字节+下一个>最大字节:#再收会超
            break#停
        字节+=下一个#累加字节
        起点-=1#起点前移
    return {'text':''.join(码点[起点:]),'truncated':True}#尾部文本

class 有界文本缓冲:#有界文本缓冲
    """按字节与可选行数上限保留尾部文本。"""
    def __init__(自身,最大字节,最大行数=None):#字节与可选行数上限
        """字节与可选行数上限。"""
        自身.值=''#当前文本
        自身.已丢=False#是否丢过前缀
        自身.最大字节=最大字节#字节上限
        自身.最大行数=最大行数#可选行数上限

    def 追加(自身,文本):#追加文本
        """追加文本并按上限截断。"""
        if len(文本)==0:#空则忽略
            return#结束
        自身.值+=文本#接到末尾
        if 自身.最大行数 is not None:#有行数上限
            行们=自身.值.split('\n')#按行切开
            if len(行们)>自身.最大行数:#行数超了
                自身.值='\n'.join(行们[len(行们)-自身.最大行数:])#只留最后若干行
                自身.已丢=True#记截断
        尾=utf8尾部(自身.值,自身.最大字节)#再按字节留尾
        自身.值=尾['text']#写回
        自身.已丢=自身.已丢 or 尾['truncated']#字节截断也记下

    def 消费(自身):#取出并清空增量
        """取出并清空增量。"""
        增量=自身.值#当前增量
        截断=自身.已丢#是否截断
        自身.值=''#清空
        自身.已丢=False#清截断标记
        return {'delta':增量,'truncated':截断}#返回增量

    def 快照(自身):#只看不清空
        """只看不清空。"""
        return {'text':自身.值,'truncated':自身.已丢}#当前文本与截断

class 本地发送操作:#一次本地发送
    """后端拥有的活动发送；每个 PTY 会话恰好可以有一个活动发送。"""
    def __init__(自身,最大字节,开始时刻,取消时):#字节上限、起始时刻与取消回调
        """字节上限、起始时刻与取消回调。"""
        自身.输出=有界文本缓冲(最大字节)#输出缓冲
        自身.结算器=承诺()#结算器
        自身.已结算=False#是否已结算
        自身.已请求取消=False#是否已请求取消
        自身.初始前台已离开等待=True#默认当作已离开等待
        自身.初始前台进程组=None#写入前的前台进程组
        自身.开始时刻=开始时刻#开始时刻
        自身.取消时=取消时#取消时回调

    @property#只读属性
    def done(自身):#完成承诺
        """就绪、超时、取消或顶层进程退出后决议。"""
        return 自身.结算器#取出承诺

    @property#只读属性
    def settled(自身):#是否已结算
        """是否已结算。"""
        return 自身.已结算#已结算标记

    @property#只读属性
    def cancelRequested(自身):#是否已请求取消
        """是否已请求取消。"""
        return 自身.已请求取消#取消标记

    def 追加(自身,文本):#追加输出
        """未结算才收输出。"""
        if not 自身.已结算:#未结算才收
            自身.输出.追加(文本)#追加

    def 结算(自身,等待原因,会话状态,继承截断):#成功结算
        """成功结算一次发送。"""
        if 自身.已结算:#已结算则忽略
            return#结束
        自身.已结算=True#钉死
        读出=自身.输出.快照()#取出视口
        自身.结算器.兑现({#兑现结果
            'viewport':读出['text'],#视口文本
            'waitReason':等待原因,#等待原因
            'sessionStatus':会话状态,#会话状态
            'truncated':读出['truncated'] or 继承截断,#自身或回滚截断
        })#兑现结束

    def 失败(自身,错误):#失败结算
        """失败结算。"""
        if 自身.已结算:#已结算则忽略
            return#结束
        自身.已结算=True#钉死
        自身.结算器.拒绝(错误)#拒绝

    def 读输出(自身):#消费增量
        """消费自上次调用以来产出的输出。"""
        return 自身.输出.消费()#取出并清空

    def 设初始前台(自身,前台):#记下写入前的前台
        """记下写入前的前台进程组与等待态。"""
        自身.初始前台进程组=取字段(前台,'processGroupId')#进程组
        自身.初始前台已离开等待=取字段(前台,'inputWaiting') is not True#当时没在等输入则已离开

    def 接受标准输入等待(自身,进程组,等待中):#是否把这次stdin等待当作写后证据
        """同一进程组仍可能暴露写入前就有的等待；离开过写入前的等待后，再回来才算写后证据。"""
        if 进程组!=自身.初始前台进程组:#换了进程组则直接看当前等待
            return 等待中#换组
        if not 等待中:#离开等待
            自身.初始前台已离开等待=True#记下离开
        return 等待中 and 自身.初始前台已离开等待#须离开过再等待

    def 取消(自身):#请求取消
        """请求 SIGINT；操作结算后返回 false。"""
        if 自身.已结算:#已结算则无效
            return False#无效
        自身.已请求取消=True#记下取消
        自身.取消时()#通知会话打断
        return True#取消已受理

class 本地PTY会话:#本地PTY会话
    """包着一次提供方拥有的终端进程的后端会话。"""
    def __init__(自身,终端句柄,配置):#终端句柄与已解析配置
        """终端句柄与已解析配置。"""
        自身.motd=''#开机信息
        自身.终端=终端句柄#提供方终端
        自身.配置=配置#配置
        自身.pid=取字段(终端句柄,'pid')#记下进程号
        自身.解码器=codecs.getincrementaldecoder('utf-8')()#流式解码器
        自身.清洗器=终端清洗器(取字段(配置,'maxReadBytes'))#清洗器
        自身.回滚=有界文本缓冲(取字段(配置,'scrollbackMaxBytes'),取字段(配置,'scrollbackLines'))#回滚
        自身.输出已结束=承诺()#输出结束
        自身.状态值={'kind':'running'}#当前状态
        #TODO(pty-send-state-consolidation):把下面的每发送字段收进一个发送生命周期所有者
        自身.活动=None#活动发送
        自身.活动定时器=None#就绪轮询定时器
        自身.活动截止定时器=None#绝对超时定时器
        自身.活动摘中止=None#摘取消监听
        自身.打断中=None#正在打断的发送
        自身.活动写入=None#在飞的提供方写入承诺
        自身.轮询就绪=None#就绪轮询所属发送
        自身.轮询中=False#是否正在一轮轮询
        自身.见过提示符=False#是否见过提示符标记
        自身.见过提示符文本=False#是否见过完整提示符文本
        自身.提示符尾巴=''#提示符尾巴累积
        自身.壳进程组=None#shell前台进程组
        自身.初始化中=False#是否在启动就绪
        自身.最近输出时刻=此刻毫秒()#最近输出时刻
        自身.关闭中=False#是否正在关闭
        自身.关闭承诺=None#关闭承诺
        自身.传输失败=None#传输失败
        输出=取字段(终端句柄,'output')#输出流
        输出.on('data',自身.终端数据时)#收数据
        输出.once('end',自身.终端结束时)#结束
        输出.once('error',自身.终端出错时)#出错
        自身.完成=承诺()#进程完成后续
        def 挂钩完成():#进程结束后
            """进程结束后走退出或传输失败。"""
            try:#等进程结局
                自身.退出时(解开(取字段(终端句柄,'done')))#正常退出
                自身.完成.兑现(None)#完成后续落定
            except BaseException as 错误:#传输失败
                自身.传输失败时(错误)#记传输失败
                自身.完成.兑现(None)#也算完成后续
        工作=工作线程(target=挂钩完成)#挂钩线程
        工作.daemon=True#不挡住退出
        工作.start()#立刻开跑

    def 初始化(自身,信号=None):#启动就绪
        """用与后续发送相同的就绪约定捕获启动输出；退出或就绪超时则抛出。"""
        自身.初始化中=True#标记启动中
        try:#空发送等到就绪
            请求={'text':'','submit':False}#不写文本
            if 信号 is not None:#有取消信号
                请求['signal']=信号#带上
            操作=自身.开始发送(请求)#不写文本
            结果=解开(操作.done)#等待就绪
            if 取字段(结果,'waitReason')=='session_exit':#启动期退出
                raise Exception('PTY shell exited during startup')#启动期退出
            if 取字段(结果,'waitReason')=='timeout':#启动超时
                raise Exception('PTY shell did not reach readiness before startup timeout')#启动超时
            自身.motd=取字段(结果,'viewport')#开机信息就是启动视口
        except BaseException as 错误:#失败
            if 信号 is not None:#取消优先
                if hasattr(信号,'throwIfAborted'):#英文API
                    信号.throwIfAborted()#取消优先
                elif hasattr(信号,'抛若中止'):#中文API
                    信号.抛若中止()#取消优先
            raise 错误#原样抛出
        finally:#无论成败
            自身.初始化中=False#清启动标记

    def 开始发送(自身,请求):#开始一次发送
        """开始一次发送；已有活动发送则拒绝。"""
        if 自身.关闭中:#关闭中拒绝
            raise Exception('PTY session is closing')#关闭中拒绝
        if 取字段(自身.状态值,'kind')=='exited':#已退出拒绝
            raise Exception('PTY session has exited')#已退出拒绝
        if 自身.活动 is not None:#已有活动发送
            if 自身.活动写入 is not None:#正在排空写入
                排空=' or draining provider write'#写入中
            elif 自身.打断中 is not None:#正在排空打断
                排空=' or draining foreground interrupt'#打断中
            else:#没有排空
                排空=''#没有排空
            raise 终端错误('PTY session already has an active send'+排空,'SEND_ACTIVE')#拒绝并发发送
        信号=取字段(请求,'signal')#取消信号
        if 取字段(信号,'aborted') is True or 取字段(信号,'已中止') is True:#写前已取消
            raise Exception('PTY send aborted before write')#写前已取消
        操作=本地发送操作(#新建发送
            取字段(自身.配置,'maxReadBytes'),#输出上限
            此刻毫秒(),#起始时刻
            lambda:自身.打断(操作),#取消时打断
        )#构造结束
        自身.活动=操作#占住发送槽
        自身.清就绪证据()#清就绪证据
        if 信号 is not None:#有取消信号
            def 中止时(*位置参数):#取消则打断
                """取消则打断。"""
                操作.取消()#打断
            if hasattr(信号,'addEventListener'):#Web API
                信号.addEventListener('abort',中止时,{'once':True})#只听一次
                def 摘():#记下摘监听
                    """摘掉取消监听。"""
                    信号.removeEventListener('abort',中止时)#摘掉
                自身.活动摘中止=摘#记下
            elif hasattr(信号,'加入监听'):#中文API
                信号.加入监听('abort',中止时,{'once':True})#只听一次
                def 摘中文():#记下摘监听
                    """摘掉取消监听。"""
                    信号.移除监听('abort',中止时)#摘掉
                自身.活动摘中止=摘中文#记下
        def 到期():#绝对超时
            """绝对超时结算。"""
            if 自身.活动 is 操作:#仍是这次发送
                自身.结算活动('timeout',自身.活动写入 is not None or 自身.打断中 is 操作)#超时结算，写入或打断中则保留所有权
        自身.活动截止定时器=安排定时(到期,取字段(自身.配置,'timeoutMs'))#超时毫秒
        def 开跑():#异步开始写入
            """异步开始写入。"""
            自身.开始写入(操作,请求)#写入并进入轮询
        工作=工作线程(target=开跑)#写入线程
        工作.daemon=True#不挡住退出
        工作.start()#立刻开跑
        return 操作#返回操作句柄

    def 开始写入(自身,操作,请求):#写入并进入轮询
        """先探前台再写入，再进入就绪轮询。"""
        前台=None#写入前前台
        try:#先探前台
            前台=解开(自身.终端.inspectForeground())#探前台
        except BaseException as 错误:#探前台失败
            #取消已占槽时，写前探前台失败不得放槽：打断路径的信号后尾巴会恢复轮询
            if 自身.活动 is 操作 and (not 自身.关闭中) and 自身.打断中 is not 操作:#仍是未打断的活动发送
                自身.失败活动(错误)#失败结算
            return#探前台失败则停
        try:#写入
            if 自身.活动 is not 操作 or 自身.关闭中 or 自身.打断中 is 操作:#槽已易主或关闭或正在打断
                return#停
            操作.设初始前台(前台)#记下写入前前台
            输入=取字段(请求,'text')+('\r' if 取字段(请求,'submit') else '')#文本加可选回车
            if len(输入)>0 and not 操作.cancelRequested:#有内容且未取消
                自身.清就绪证据()#写前再清就绪证据
                写入=自身.终端.write(输入)#提供方写入
                写入承诺=承诺()#记下写入成败
                自身.活动写入=写入承诺#在飞写入
                try:#等待写入
                    解开(写入)#等提供方写完
                    写入承诺.兑现(True)#写入成功
                except BaseException:#写入失败
                    写入承诺.兑现(False)#记下失败
                    raise#继续抛
                finally:#无论成败
                    自身.活动写入=None#清在飞写入
            if 操作.cancelRequested:#已取消则交给打断路径
                return#停
            if 自身.活动 is 操作 and 操作.settled:#写时期间已被结算
                自身.清活动()#放槽
                return#结束
            if 自身.活动 is 操作 and not 自身.关闭中:#仍是这次发送且未关闭
                自身.轮询就绪=操作#记下轮询所属
                自身.安排轮询(操作)#开始就绪轮询
        except BaseException as 错误:#写入路径失败
            if 自身.活动 is 操作 and not 自身.关闭中:#仍占槽且未关闭
                if 操作.settled:#已结算则只放槽
                    自身.清活动()#放槽
                else:#否则失败结算
                    自身.失败活动(错误)#失败结算

    def 清就绪证据(自身):#清就绪证据
        """清就绪证据。"""
        自身.最近输出时刻=此刻毫秒()#输出时刻重置
        自身.见过提示符=False#未见提示符标记
        自身.见过提示符文本=False#未见提示符文本
        自身.提示符尾巴=''#清尾巴

    def 读取(自身,请求):#读一页回滚
        """读一页回滚。"""
        快照=自身.回滚.快照()#当前回滚
        行们=快照['text'].split('\n')#按行切
        总行=0 if len(快照['text'])==0 else len(行们)#空文本算0行
        偏移=取字段(请求,'offset')#相对最新偏移
        if 偏移 is None:#缺省
            偏移=0#默认0
        行数=取字段(请求,'count')#默认行数
        if 行数 is None:#缺省
            行数=500#默认500行
        if (not 是否安全整数(偏移)) or 偏移<0:#拒绝非法偏移
            raise Exception('PTY read offset must be a non-negative safe integer')#拒绝非法偏移
        if (not 是否安全整数(行数)) or 行数<=0:#拒绝非法行数
            raise Exception('PTY read count must be a positive safe integer')#拒绝非法行数
        if 偏移>=总行:#偏移超出
            return {'text':'','totalLines':总行,'lineBegin':偏移,'lineEnd':偏移,'truncated':快照['truncated']}#空页
        结束=总行-偏移#结束行
        开始=max(0,结束-行数)#起始行
        请求文本='\n'.join(行们[开始:结束])#取出请求行
        有界=utf8尾部(请求文本,取字段(自身.配置,'maxReadBytes'))#再按字节留尾
        返回行=0 if len(有界['text'])==0 else len(有界['text'].split('\n'))#实际返回行数
        return {#分页结果
            'text':有界['text'],#页文本
            'totalLines':总行,#总行数
            'lineBegin':偏移,#起始偏移
            'lineEnd':偏移+返回行,#结束偏移
            'truncated':快照['truncated'] or 有界['truncated'],#回滚或本页截断
        }#结果结束

    def 发信号(自身,信号名):#向前台进程组发信号
        """向前台进程组发信号。"""
        if 自身.关闭中:#关闭中拒绝
            raise Exception('PTY session is closing')#关闭中拒绝
        目标组=解开(自身.终端.signalForeground(信号名))#交给提供方
        return {'delivered':True,'targetPgid':目标组}#已投递

    def 状态(自身):#当前状态
        """当前状态快照。"""
        return 自身.状态值#返回快照

    def 关闭(自身,原因):#关闭会话
        """关闭会话；复用在飞关闭承诺。"""
        自身.关闭中=True#标记关闭中
        if 自身.关闭承诺 is not None:#复用在飞关闭
            return 自身.关闭承诺#复用
        关闭中=承诺()#单次关闭承诺
        def 跑关闭():#真正关一次
            """真正关一次，失败则清掉承诺并失败活动发送。"""
            try:#单次关闭
                自身.关一次(原因)#关一次
                关闭中.兑现(None)#成功
            except BaseException as 错误:#关闭失败
                自身.关闭承诺=None#清掉失败承诺
                自身.失败活动(错误)#失败活动发送
                关闭中.拒绝(错误)#原样拒绝
        工作=工作线程(target=跑关闭)#关闭线程
        工作.daemon=True#不挡住退出
        工作.start()#立刻开跑
        自身.关闭承诺=关闭中#钉上关闭承诺
        return 关闭中#返回

    def 终端数据时(自身,分片):#终端数据
        """终端数据到达。"""
        if isinstance(分片,str):#字符串
            字节=分片.encode('utf-8')#统一成字节
        else:#已是字节
            字节=分片#原样
        自身.数据时(自身.解码器.decode(字节,False))#流式解码后处理

    def 终端结束时(自身):#输出结束
        """输出结束。"""
        自身.数据时(自身.解码器.decode(b'',True))#冲掉解码器
        自身.追加输出(自身.清洗器.冲掉())#冲掉清洗器
        自身.输出已结束.兑现(None)#标记输出结束

    def 终端出错时(自身,错误):#输出出错
        """输出出错。"""
        自身.传输失败时(错误)#记传输失败
        自身.输出已结束.兑现(None)#也算输出结束

    def 数据时(自身,数据):#处理一段解码文本
        """处理一段解码文本。"""
        已洗=自身.清洗器.推入(数据)#清洗
        自身.追加输出(取字段(已洗,'text'))#追加可见文本
        if 取字段(已洗,'prompt'):#见过提示符标记
            #TODO(pty-delayed-signal-prompt):有复现后，先定义标记生成边界，再把信号延迟的提示符归到后一次发送
            自身.见过提示符=True#记下标记
            自身.提示符尾巴=''#清尾巴
            自身.最近输出时刻=此刻毫秒()#更新输出时刻
        if 自身.见过提示符 and 取字段(已洗,'promptTail') is not None:#标记后继续收尾巴
            剩余=max(0,len(受控提示符)+1-len(自身.提示符尾巴))#还能收多少
            尾巴=取字段(已洗,'promptTail')#本分片尾巴
            自身.提示符尾巴+=尾巴[:剩余]#接上
            if len(尾巴)>剩余:#超长则毒化
                自身.提示符尾巴=受控提示符+'\0'#毒化
            自身.见过提示符文本=自身.提示符尾巴==受控提示符#是否正好是受控提示符

    def 退出时(自身,结局):#进程退出
        """进程退出后结算活动发送。"""
        解开(自身.输出已结束)#先等输出结束
        if 自身.传输失败 is not None:#传输失败已处理过
            return#结束
        自身.状态值={'kind':'exited','exitCode':取字段(结局,'exitCode'),'signal':取字段(结局,'signal')}#记下退出
        自身.结算活动('session_exit')#按会话退出结算

    def 传输失败时(自身,错误):#传输失败
        """传输失败当作退出并失败活动发送。"""
        失败=错误 if isinstance(错误,BaseException) else Exception(str(错误))#收成异常
        if 自身.传输失败 is None:#只记第一次
            自身.传输失败=失败#记下
        自身.状态值={'kind':'exited','exitCode':None,'signal':None}#当作退出
        自身.失败活动(失败)#失败活动发送
        def 尽力终止():#尽力终止
            """尽力终止，吞掉终止失败以免掩盖传输失败。"""
            try:#终止
                解开(自身.终端.terminate())#终止
            except Exception:#吞掉终止失败
                pass#吞掉
        工作=工作线程(target=尽力终止)#终止线程
        工作.daemon=True#不挡住退出
        工作.start()#立刻开跑

    def 追加输出(自身,文本):#追加到回滚与活动发送
        """追加到回滚与活动发送。"""
        if len(文本)==0:#空则忽略
            return#结束
        自身.最近输出时刻=此刻毫秒()#更新输出时刻
        自身.回滚.追加(文本)#回滚
        if 自身.活动 is not None:#活动发送也收
            自身.活动.追加(文本)#活动发送也收

    def 安排轮询(自身,操作,延迟毫秒=None):#安排一轮就绪轮询
        """安排一轮就绪轮询。"""
        if 延迟毫秒 is None:#缺省
            延迟毫秒=取字段(自身.配置,'pollIntervalMs')#配置间隔
        if 自身.活动 is not 操作 or 自身.打断中 is 操作 or 自身.轮询中:#槽已易主、正在打断或已在轮询
            return#停
        清定时(自身.活动定时器)#清掉旧定时器
        def 到期():#到期后轮询
            """到期后探就绪。"""
            自身.活动定时器=None#清定时器
            自身.探就绪(操作)#探就绪
        自身.活动定时器=安排定时(到期,延迟毫秒)#延迟

    def 探就绪(自身,操作):#探一次就绪
        """探一次就绪条件。"""
        if 自身.活动 is not 操作 or 自身.轮询中:#槽已易主或重入
            return#停
        自身.轮询中=True#占轮询
        try:#检查就绪条件
            if 取字段(自身.状态值,'kind')=='exited':#已退出
                自身.结算活动('session_exit')#按退出结算
                return#结束
            前台=解开(自身.终端.inspectForeground())#探前台
            if 自身.活动 is not 操作 or 自身.关闭中 or 自身.打断中 is 操作:#等待期间槽已易主
                return#停
            静默=此刻毫秒()-自身.最近输出时刻#静默时长
            if 自身.见过提示符 and 前台 is not None and 自身.壳进程组 is None:#首次见提示符时记住shell组
                自身.壳进程组=取字段(前台,'processGroupId')#记下shell进程组
            if (自身.见过提示符 and 自身.见过提示符文本 and 静默>=取字段(自身.配置,'pollIntervalMs')#提示符完整且静默过一轮
                and 取字段(前台,'processGroupId')==自身.壳进程组):#且shell占据前台
                自身.结算活动('stdin_read')#按stdin等待结算
                return#结束
            已过=此刻毫秒()-操作.开始时刻#发送已过时长
            启动已有输出=(not 自身.初始化中) or len(自身.回滚.快照()['text'])>0#启动期须已有输出
            接受等待=启动已有输出 and 前台 is not None and 操作.接受标准输入等待(取字段(前台,'processGroupId'),取字段(前台,'inputWaiting') is True)#写后stdin等待证据
            if 已过>=取字段(自身.配置,'exactProbeAfterMs') and 接受等待:#过了精确探测延迟且证据成立
                自身.结算活动('stdin_read')#按stdin等待结算
                return#结束
            #提示符候选可能与bash的前台交接竞态；静默仍是等待shell所有权的边界
            交接宽限=取字段(自身.配置,'handoffGraceMs') if 自身.见过提示符 else 0#见过标记则加交接宽限
            if 启动已有输出 and 静默>=取字段(自身.配置,'idleSilenceMs')+交接宽限:#静默足够
                自身.结算活动('inferred_idle')#按推断空闲结算
        except BaseException as 错误:#探前台失败
            if 自身.活动 is 操作 and (not 自身.关闭中) and 自身.打断中 is not 操作:#仍占槽则失败
                自身.失败活动(错误)#失败
        finally:#无论成败
            自身.轮询中=False#放轮询
            活动=自身.活动#当前活动发送
            if 活动 is not None and 自身.轮询就绪 is 活动:#仍该轮询则安排下一轮
                自身.安排轮询(活动)#下一轮

    def 结算活动(自身,等待原因,保留所有权=False):#结算活动发送
        """结算活动发送。"""
        操作=自身.活动#当前发送
        if 操作 is None:#没有则结束
            return#结束
        回滚截断=自身.回滚.快照()['truncated']#回滚是否截断
        if 保留所有权:#超时且写入/打断仍在飞时保留槽
            自身.停轮询()#停轮询与超时
            if 自身.活动摘中止 is not None:#有摘监听
                自身.活动摘中止()#摘取消监听
            自身.活动摘中止=None#清回调
        else:#普通结算
            自身.清活动()#放槽
        操作.结算(等待原因,自身.状态值,回滚截断)#兑现结果

    def 停轮询(自身):#停全部发送计时
        """停全部发送计时。"""
        自身.停就绪轮询()#停就绪轮询
        清定时(自身.活动截止定时器)#清绝对超时
        自身.活动截止定时器=None#清字段

    def 停就绪轮询(自身):#停就绪轮询
        """停就绪轮询。"""
        清定时(自身.活动定时器)#清定时器
        自身.活动定时器=None#清字段
        自身.轮询就绪=None#清轮询所属

    def 清活动(自身):#放掉活动发送槽
        """放掉活动发送槽。"""
        操作=自身.活动#当前发送
        自身.停轮询()#停计时
        if 自身.活动摘中止 is not None:#有摘监听
            自身.活动摘中止()#摘取消监听
        自身.活动摘中止=None#清回调
        if 自身.打断中 is 操作:#清打断标记
            自身.打断中=None#清打断标记
        自身.轮询就绪=None#清轮询所属
        自身.活动=None#放槽

    def 失败活动(自身,错误):#失败活动发送
        """失败活动发送。"""
        操作=自身.活动#当前发送
        if 操作 is None:#没有则结束
            return#结束
        自身.清活动()#放槽
        操作.失败(错误)#拒绝

    def 打断(自身,操作):#开始打断一次发送
        """开始打断一次发送。"""
        if 自身.活动 is not 操作:#已不是这次发送
            return#停
        自身.打断中=操作#钉上打断
        自身.停就绪轮询()#停就绪轮询但保留绝对超时
        def 开跑():#异步发SIGINT
            """异步发 SIGINT。"""
            自身.打断一次(操作)#对前台发一次SIGINT
        工作=工作线程(target=开跑)#打断线程
        工作.daemon=True#不挡住退出
        工作.start()#立刻开跑

    def 打断一次(自身,操作):#对前台发一次SIGINT
        """对前台发一次 SIGINT。"""
        try:#等写入结束再发信号
            活动写入=自身.活动写入#在飞写入
            if 活动写入 is not None and not 解开(活动写入):#写入失败则停
                return#停
            解开(自身.终端.signalForeground('SIGINT'))#向前台发SIGINT
        except BaseException as 错误:#发信号失败
            if 自身.活动 is 操作 and not 自身.关闭中:#仍占槽则当传输失败
                自身.传输失败时(错误)#传输失败
            return#结束
        finally:#无论成败
            if 自身.打断中 is 操作:#清打断标记
                自身.打断中=None#清打断标记
        if 自身.活动 is 操作 and 操作.settled:#打断期间已被结算
            自身.清活动()#放槽
        elif 自身.活动 is 操作 and not 自身.关闭中:#仍占槽且未关闭
            自身.轮询就绪=操作#恢复轮询所属
            自身.安排轮询(操作,0)#立刻再探就绪

    def 关一次(自身,原因):#真正关一次
        """真正关一次：停轮询、终止进程、按会话退出结算。"""
        #停就绪轮询但留住活动发送：拆除会在下面按session_exit结算
        自身.停轮询()#停计时
        try:#终止提供方进程
            解开(自身.终端.terminate())#终止
        except BaseException as 错误:#终止失败
            包装=Exception('PTY cleanup failed ('+原因+')')#带原因
            包装.__cause__=错误#挂上原因
            raise 包装#抛出
        自身.结算活动('session_exit')#按会话退出结算
        解开(自身.完成)#等进程后续跑完
        输出=取字段(自身.终端,'output')#输出流
        输出.off('data',自身.终端数据时)#摘数据监听
        输出.off('end',自身.终端结束时)#摘结束监听
        输出.off('error',自身.终端出错时)#摘错误监听
        if 自身.传输失败 is not None:#有传输失败则抛出
            raise 自身.传输失败#抛出
