'一个智能体一条到共享原生辅助进程的 JSONL 连接'
import json,math,threading,time,uuid
from ...基础设施.通用工具.序列化编码 import 紧凑json编码
from ...内核.智能体循环.中止与并发 import 已中止

__all__=['原生错误','字节流','原生通道','原生客户端','监听中止','若已中止则抛出']

截图前缀='[cua-screenshot] '#截图诊断行前缀
诊断字节上限=8192#诊断缓冲上限

class 原生错误(Exception):
    '带稳定机器可读码的原生拒绝或传输失败'

    def __init__(自身,码,消息,原因=None):
        '码在前，说明不含码前缀'
        全文=码+': '+消息#对外消息
        super().__init__(全文)#异常文本
        自身.code=码#稳定码
        自身.name='NativeError'#错误名
        自身.message=全文#可追加的消息
        自身.cause=原因#原始失败
        if isinstance(原因,BaseException):#链式原因
            自身.__cause__=原因#链式原因

    def 追加(自身,后缀):
        '把截图诊断接到同一次失败上'
        自身.message=自身.message+后缀#追加
        自身.args=(自身.message,)#str 与 message 一致

class 字节流:
    '给连接两端用的事件字节流'

    def __init__(自身):
        '还没有监听者'
        自身._监听={}#事件到回调
        自身._已毁=False#已经销毁

    def 监听(自身,事件,回调):
        '登记一个事件回调'
        自身._监听.setdefault(事件,[]).append(回调)#追加
        def 取消():
            '摘掉这个回调'
            列表=自身._监听.get(事件,[])#当前列表
            if 回调 in 列表:#还在
                列表.remove(回调)#摘掉
        return 取消#取消函数

    def 发出(自身,事件,数据=None):
        '同步通知当前监听者'
        for 回调 in list(自身._监听.get(事件,[])):#拷贝，回调里可以再改
            if 数据 is None and 事件!='data':#无载荷事件
                回调()#通知
            else:#带载荷
                回调(数据)#通知

    def 销毁(自身,错误=None):
        '发出错误然后关闭。重复销毁无事发生'
        if 自身._已毁:#已经销毁
            return#无事
        自身._已毁=True#只一次
        if 错误 is not None:#有错误
            自身.发出('error',错误)#错误
        自身.发出('close')#关闭

    def 结束(自身):
        '正常结束，先 end 再 close'
        if 自身._已毁:#已经销毁
            return#无事
        自身._已毁=True#只一次
        自身.发出('end')#结束
        自身.发出('close')#关闭

class 原生通道:
    '一个智能体到原生操作的有序连接。标准输入、标准输出、关闭和等待关闭由平台提供方实现'

def 若已中止则抛出(信号):
    '已中止则抛出信号上的异常'
    if not 已中止(信号):#仍活着
        return#继续
    原因=getattr(信号,'原因',None)#中文信号
    if 原因 is None:#也可能挂在 reason 上
        原因=getattr(信号,'reason',None)#英文信号
    if isinstance(原因,BaseException):#异常原因
        raise 原因#抛出
    if 原因 is not None:#非异常原因
        raise RuntimeError(str(原因))#包成异常
    raise RuntimeError('The operation was aborted')#没有原因

def 监听中止(信号,回调):
    '信号中止时调用回调一次。返回取消函数'
    if 已中止(信号):#已经中止
        回调()#立刻
        def 已触发取消():
            '已经触发，没有监听可摘'
            return None
        return 已触发取消#空取消
    停=threading.Event()#取消监视
    def 监视():
        '轮询到中止或取消'
        while not 停.is_set():#还要看
            if 已中止(信号):#中止了
                if not 停.is_set():#没被取消
                    回调()#通知
                return#结束
            等待=getattr(信号,'wait',None)#Event 等待
            if callable(等待):#能等
                等待(0.05)#最多 50 毫秒
            else:#不能等
                停.wait(0.05)#自己睡
    threading.Thread(target=监视,daemon=True).start()#监视线程
    def 取消():
        '停止监视，不再调用回调'
        停.set()#停
    return 取消#取消函数

def 规整数(值):
    '整数值的浮点写成整数，与 JSON.stringify 一致'
    if isinstance(值,float) and math.isfinite(值) and 值==int(值):#整数值
        return int(值)#整数
    return 值#原样

def 是json(值):
    '有限 JSON 值'
    if 值 is None or isinstance(值,str) or isinstance(值,bool):#标量
        return True#是
    if isinstance(值,int):#整数
        return True#是
    if isinstance(值,float):#浮点
        return math.isfinite(值)#有限才是
    if isinstance(值,list):#数组
        return all(是json(项) for 项 in 值)#每一项
    if isinstance(值,dict):#对象
        return all(isinstance(键,str) and 是json(项) for 键,项 in 值.items())#字符串键
    return False#其余不是

class 协议形状错误(Exception):
    '线路帧不符合回复或诊断'

    def __init__(自身):
        '固定说明'
        super().__init__('invalid wire reply')#说明

def 解析严格回复(值):
    '恰好是结果或错误，多余键拒绝'
    if not isinstance(值,dict):#不是对象
        raise 协议形状错误()#拒绝
    键=set(值)#键集合
    if 键=={'id','result'}:#结果
        if not isinstance(值['id'],str) or not 是json(值['result']):#身份或结果非法
            raise 协议形状错误()#拒绝
        return ('result',值['id'],值['result'])#结果
    if 键=={'id','error'}:#错误
        错误=值['error']#错误对象
        if not isinstance(值['id'],str) or not isinstance(错误,dict) or set(错误)!={'code','message'}:#形状不对
            raise 协议形状错误()#拒绝
        if not isinstance(错误['code'],str) or len(错误['code'])==0 or not isinstance(错误['message'],str):#码或说明非法
            raise 协议形状错误()#拒绝
        return ('error',值['id'],错误['code'],错误['message'])#错误
    raise 协议形状错误()#两种都不是

def 解析诊断(值):
    '截图诊断。未知字段丢掉，不进入保留记录'
    if not isinstance(值,dict) or 值.get('type')!='diagnostic':#不是诊断
        raise 协议形状错误()#拒绝
    if not isinstance(值.get('requestId'),str) or not isinstance(值.get('stage'),str):#身份或阶段
        raise 协议形状错误()#拒绝
    经过=值.get('elapsedMs')#耗时
    if isinstance(经过,bool) or not isinstance(经过,(int,float)) or not math.isfinite(经过) or 经过<0:#必须是非负有限数
        raise 协议形状错误()#拒绝
    记录={'requestId':值['requestId'],'stage':值['stage'],'elapsedMs':规整数(经过)}#已知字段
    if 'errorCode' in 值 and 值['errorCode'] is not None:#可选错误码
        if not isinstance(值['errorCode'],str):#必须是字符串
            raise 协议形状错误()#拒绝
        记录['errorCode']=值['errorCode']#带上
    return ('diagnostic',记录)#诊断

def 解析线路(值):
    '先试严格回复，再试诊断'
    try:#回复优先
        return 解析严格回复(值)#回复
    except 协议形状错误:#不是回复
        return 解析诊断(值)#诊断

class 原生客户端:
    '一个智能体拥有这条连接和它的原生句柄'

    def __init__(自身,所有者,配置,创建通道,报告诊断=None):
        '打开平台连接。诊断汇聚点看不到捕获内容'
        自身._配置=配置#限额和截止
        自身._报告诊断=报告诊断#可选诊断汇
        自身._块=[]#未成帧的字节
        自身._缓冲字节=0#已缓冲字节
        自身._失败错误=None#第一条传输失败
        自身._已开始释放=False#释放只做一次
        自身._诊断=[]#本请求的诊断行
        自身._诊断字节=0#诊断字节
        自身._丢掉过诊断=False#缓冲丢过更早的记录
        自身._活动=None#当前请求
        自身._锁=threading.Lock()#缓冲和活动互斥
        自身._释放完成=threading.Event()#释放结束
        自身._通道=创建通道(所有者,配置)#平台连接
        自身._通道.标准输出.监听('data',自身._接收)#数据
        自身._通道.标准输出.监听('error',自身._输出错误)#输出错误
        自身._通道.标准输出.监听('end',自身._输出结束)#输出结束
        自身._通道.标准输出.监听('close',自身._输出关闭)#输出关闭
        自身._通道.标准输入.监听('error',自身._输入错误)#输入错误
        def 监视完成():
            '连接自己结束时让句柄失效'
            try:#等到关闭
                自身._通道.等待关闭()#阻塞
                自身._失败(原生错误('NATIVE_EXITED','Native connection closed; acquire fresh application handles'))#正常退出也要换句柄
            except Exception as 错误:#连接失败
                自身._失败(原生错误('NATIVE_EXITED','Native connection failed',错误))#带上原因
        threading.Thread(target=监视完成,daemon=True).start()#不挡住进程退出

    def _输出错误(自身,错误):
        '标准输出失败'
        自身._失败(原生错误('NATIVE_IO','Native connection failed: '+错误消息(错误),错误))#连接失败

    def _输出结束(自身):
        '标准输出结束'
        自身._失败(原生错误('NATIVE_EOF','Native connection ended; acquire fresh application handles'))#换句柄

    def _输出关闭(自身):
        '标准输出关闭'
        自身._失败(原生错误('NATIVE_EOF','Native connection closed; acquire fresh application handles'))#换句柄

    def _输入错误(自身,错误):
        '写入失败'
        自身._失败(原生错误('NATIVE_IO','Writing native requests failed',错误))#写入失败

    @property
    def 已释放(自身):
        '这条连接是否已经丢掉保留的原生状态'
        return 自身._失败错误 is not None#有失败即释放

    def 作废(自身):
        '让这个智能体的句柄失效并关闭连接'
        自身._失败(原生错误('NATIVE_DISPOSED','Helper disposed'))#释放

    def 释放(自身):
        '停掉未完成的工作并等待原生连接清理'
        自身.作废()#先失效
        with 自身._锁:#只启动一次清理
            开始=not 自身._已开始释放#是否第一次
            自身._已开始释放=True#记下
        if 开始:#第一次
            def 清理():
                '等待通道关闭后再销毁两端'
                try:#等待
                    自身._通道.等待关闭()#关闭确认
                finally:#无论如何销毁流
                    自身._通道.标准输出.销毁()#输出
                    自身._通道.标准输入.销毁()#输入
                    自身._释放完成.set()#结束
            threading.Thread(target=清理,daemon=True).start()#清理线程
        自身._释放完成.wait()#调用方等到清理结束

    def 请求(自身,方法,参数,信号,调用标识=None):
        '发送一次操作。原生拒绝保留连接；传输失败则句柄失效'
        if 已中止(信号):#发出前已取消
            raise 原生错误('NATIVE_CANCELLED','Operation was cancelled before dispatch')#不写
        if 自身.已释放:#连接已死
            自身.释放()#等到清理
            raise 原生错误('NATIVE_CLOSED','Helper is closed; acquire fresh application handles',自身._失败错误)#换句柄
        if 自身._活动 is not None:#上一次还没结束
            raise 原生错误('NATIVE_BUSY','Await native operations sequentially')#必须串行
        标识=调用标识 if 调用标识 is not None else str(uuid.uuid4())#工具调用标识或新标识
        捕获=方法=='screenshot'#截图才收诊断
        自身._诊断=[]#清空
        自身._诊断字节=0#清空
        自身._丢掉过诊断=False#清空
        开始=time.perf_counter()#起点
        帧=紧凑json编码({'id':标识,'method':方法,'params':参数})+'\n'#一帧
        if len(帧.encode('utf-8'))>自身._配置['maxRequestBytes']:#发出前就超限
            raise 原生错误('NATIVE_REQUEST_LIMIT','Request exceeded the configured byte limit before dispatch')#不发出
        盒子={}#结算
        完成=threading.Event()#结算事件
        中断=[None]#取消或超时
        原生失败=[None]#回复里的原生错误
        def 解决(值):
            '成功结算'
            盒子['值']=值#值
            完成.set()#唤醒
        def 拒绝(错误):
            '失败结算'
            原生失败[0]=错误#记下原生错误
            盒子['错误']=错误#错误
            完成.set()#唤醒
        自身._活动={'id':标识,'resolve':解决,'reject':拒绝}#当前请求
        if 捕获:#截图阶段
            自身._诊断消息(截图前缀+紧凑json编码({'requestId':标识,'stage':'host.dispatch','elapsedMs':0}))#发出
        取消定时=[None]#清理宽限
        超时定时=[None]#操作截止
        def 打断(错误):
            '取消这一次，连接要等原生确认清理'
            if 中断[0] is not None or 自身._活动 is None or 自身._活动['id']!=标识:#已经打断或不是这一次
                return#忽略
            中断[0]=错误#记下
            def 清理超时():
                '宽限内没有确认'
                自身._失败(原生错误('NATIVE_CLEANUP','Native operation did not acknowledge cancellation; acquire fresh application handles',错误))#换句柄
            定时器=threading.Timer(自身._配置['graceMs']/1000.0,清理超时)#宽限
            定时器.daemon=True#不挡住退出
            取消定时[0]=定时器#留着取消
            定时器.start()#开始
            取消帧=紧凑json编码({'type':'cancel','id':标识})+'\n'#取消帧
            def 写完(失败=None):
                '取消帧写失败则连接失效'
                if 失败 is not None:#写失败
                    自身._失败(原生错误('NATIVE_IO','Sending native cancellation failed',失败))#写入失败
            try:#发出取消
                自身._通道.标准输入.写入(取消帧,写完)#写入
            except Exception as 失败:#写入直接抛
                自身._失败(原生错误('NATIVE_IO','Sending native cancellation failed',失败))#写入失败
        def 因中止():
            '调用方取消'
            打断(原生错误('NATIVE_CANCELLED','Operation cancelled; inspect fresh state before retrying input'))#取消
        取消监听=监听中止(信号,因中止)#监听
        超时毫秒=min(自身._配置['timeoutMs'],自身._配置['screenshotTimeoutMs']) if 捕获 else 自身._配置['timeoutMs']#截图用更紧的截止
        def 超时():
            '超过截止'
            打断(原生错误('NATIVE_TIMEOUT','Operation exceeded '+str(超时毫秒)+'ms'))#超时
        定时器=threading.Timer(超时毫秒/1000.0,超时)#截止
        定时器.daemon=True#不挡住退出
        超时定时[0]=定时器#留着取消
        定时器.start()#开始
        抛出=None#最终要抛的错误
        返回值=None#成功值
        try:#等待回复
            def 请求写完(失败=None):
                '请求帧写失败则连接失效'
                if 失败 is not None:#写失败
                    自身._失败(原生错误('NATIVE_IO','Writing a helper request failed',失败))#写入失败
            try:#发出请求
                自身._通道.标准输入.写入(帧,请求写完)#写入
            except Exception as 错误:#写入直接抛
                自身._失败(原生错误('NATIVE_IO','Writing a helper request failed',错误))#写入失败
            完成.wait()#等到回复或失败
            if 自身._失败错误 is not None:#传输失败优先
                raise 自身._失败错误#抛出
            if 中断[0] is not None:#取消或超时优先于原生拒绝
                raise 中断[0]#抛出
            if '错误' in 盒子:#原生拒绝
                raise 盒子['错误']#抛出
            if 捕获:#回复阶段
                经过=规整数((time.perf_counter()-开始)*1000)#毫秒
                自身._诊断消息(截图前缀+紧凑json编码({'requestId':标识,'stage':'host.reply','elapsedMs':经过}))#回复
            返回值=盒子.get('值')#成功值
        except Exception as 错误:#失败
            if 中断[0] is not None and 自身._失败错误 is None:#取消优先于回复错误
                抛出=中断[0]#取消
            else:#传输或原生错误
                抛出=错误#原错误
        finally:#诊断和定时器
            if 超时定时[0] is not None:#停截止
                超时定时[0].cancel()#停
            if 取消定时[0] is not None:#停宽限
                取消定时[0].cancel()#停
            取消监听()#摘掉监听
            try:#传输失败要先释放
                if 自身._失败错误 is not None:#连接死了
                    自身.释放()#等待清理
            finally:#截图诊断
                if 捕获:#只对截图
                    诊断文本=自身._截图诊断()#缓冲里的记录
                    失败=自身._失败错误 or 中断[0] or 原生失败[0]#要附上诊断的那次失败
                    if 失败 is not None and 诊断文本:#接到错误消息上
                        失败.追加('\nScreenshot diagnostics:\n'+诊断文本)#追加
                    if 诊断文本:#也发给宿主
                        自身._诊断消息(诊断文本)#报告
                    经过=规整数((time.perf_counter()-开始)*1000)#毫秒
                    自身._诊断消息(截图前缀+紧凑json编码({'requestId':标识,'stage':'host.settled','elapsedMs':经过}))#落定
        if 抛出 is not None:#失败
            raise 抛出#抛出
        return 返回值#成功

    def _截图诊断(自身):
        '拼出有界诊断缓冲'
        记录=list(自身._诊断)#拷贝
        if 自身._丢掉过诊断:#更早的被丢掉了
            记录.insert(0,'[Earlier screenshot diagnostic records were discarded from the bounded diagnostic buffer.]')#说明
        return '\n'.join(记录)#多行

    def _保留诊断(自身,值):
        '只保留当前请求的诊断，超出 8192 字节就丢掉更早的'
        if 自身._活动 is None or 值['requestId']!=自身._活动['id']:#不是这一次
            return#忽略
        行=截图前缀+紧凑json编码(值)#一行
        自身._诊断.append(行)#保留
        自身._诊断字节+=len(行.encode('utf-8'))#字节
        while 自身._诊断字节>诊断字节上限:#超出
            if len(自身._诊断)==0:#字节必须属于保留的记录
                raise AssertionError('Diagnostic bytes must belong to retained records')#不变量
            丢掉=自身._诊断.pop(0)#丢掉最早的
            自身._诊断字节-=len(丢掉.encode('utf-8'))#减去
            自身._丢掉过诊断=True#记过

    def _诊断消息(自身,消息):
        '诊断消费方不能替换原生结果，也不能挡住进程清理'
        if 自身._报告诊断 is None:#没有汇
            return#不发
        try:#消费方可以抛
            自身._报告诊断(消息)#报告
        except Exception:#吞掉
            return#不影响结果

    def _失败(自身,错误):
        '第一条传输失败留下，并拒绝当前请求、关闭连接'
        with 自身._锁:#互斥
            if 自身._失败错误 is not None:#已有
                return#只留第一条
            自身._失败错误=错误#留下
            自身._块=[]#丢掉缓冲
            自身._缓冲字节=0#清零
            活动=自身._活动#当前
            自身._活动=None#清掉
        if 活动 is not None:#有人在等
            活动['reject'](错误)#拒绝
        自身._通道.关闭()#关闭连接

    def _接收(自身,块):
        '按换行切帧。超限在保留下一块之前失败'
        if isinstance(块,str):#文本
            块=块.encode('utf-8')#按 UTF-8
        else:#字节
            块=bytes(块)#拷贝
        成帧=[]#本次切出的完整帧
        超限=False#是否超限
        with 自身._锁:#只改缓冲
            if 自身._失败错误 is not None:#已经失败
                return#丢掉
            偏移=0#起点
            while 偏移<len(块):#还有字节
                换行=块.find(10,偏移)#换行
                结束=len(块) if 换行<0 else 换行+1#这一片的结尾
                片=块[偏移:结束]#一片
                if 自身._缓冲字节+len(片)>自身._配置['maxResponseBytes']:#超限
                    超限=True#记下
                    break#停止留下
                自身._块.append(片)#留下
                自身._缓冲字节+=len(片)#计数
                if 换行>=0:#成帧
                    成帧.append(b''.join(自身._块))#拼出
                    自身._块=[]#清空
                    自身._缓冲字节=0#清零
                偏移=结束#前进
        if 超限:#超限
            自身._失败(原生错误('NATIVE_RESPONSE_LIMIT','Helper response exceeded the configured byte limit'))#失败
            return#停止
        for 帧 in 成帧:#逐帧
            自身._接收帧(帧)#解析

    def _接收帧(自身,帧):
        '解析一帧。协议失败让连接失效'
        try:#解析
            行=帧[:-1].decode('utf-8')#去掉换行，非法 UTF-8 抛错
            回复=解析线路(json.loads(行))#线路
        except Exception as 错误:#协议或解码失败
            自身._失败(原生错误('NATIVE_PROTOCOL','Helper returned an invalid response; acquire fresh application handles',错误))#换句柄
            return#停止
        if 回复[0]=='diagnostic':#诊断
            with 自身._锁:#和失败互斥
                try:#保留
                    自身._保留诊断(回复[1])#保留
                except Exception as 错误:#不变量破坏也是协议失败
                    留错=错误#带出去
                else:#成功
                    留错=None#没有
            if 留错 is not None:#失败
                自身._失败(原生错误('NATIVE_PROTOCOL','Helper returned an invalid response; acquire fresh application handles',留错))#换句柄
            return#不是回复
        with 自身._锁:#取走当前请求
            活动=自身._活动#当前
            if 活动 is None or 回复[1]!=活动['id']:#没有对上的请求
                活动=None#下面当协议失败
                不符=True#不符
            else:#对上了
                自身._活动=None#这一次结束
                不符=False#相符
        if 不符:#没有匹配请求
            自身._失败(原生错误('NATIVE_PROTOCOL','Helper returned an invalid response; acquire fresh application handles',协议形状错误()))#换句柄
            return#停止
        if 回复[0]=='error':#原生拒绝
            错误=原生错误(回复[2],回复[3])#带码
            if 回复[2]=='NATIVE_RESPONSE_LIMIT':#响应超限同时让连接失效
                自身._失败(错误)#失效
            活动['reject'](错误)#拒绝
        else:#结果
            活动['resolve'](回复[2])#成功

def 错误消息(错误):
    '优先用错误自己的 message'
    消息=getattr(错误,'message',None)#message
    if isinstance(消息,str) and len(消息)>0:#有消息
        return 消息#消息
    return str(错误)#退回 str
