'宿主上复用 Typert Remote 流的 WebSocket。上游 ws 没有中文包，握手和文本帧写在这里'
import base64,hashlib,json,threading#握手、帧与心跳
from collections import deque#上行队列
from ...类型化远程调用.协议 import 远程错误,取远程错误#协议失败与上行溢出
from ...客户端.连接.rpc import 中止控制器#逻辑流取消
from .流协议 import 解析远程流客户端报文#浏览器报文

错过心跳上限=2#连续两次没有回应就拆套接字
握手魔数='258EAFA5-E914-47DA-95CA-C5AB0DC85B11'#RFC6455

def _编码帧(操作码,载荷):
    '服务端帧不打掩码'
    长度=len(载荷)#载荷长度
    if 长度<126:#短
        头=bytes([0x80|操作码,长度])#一头
    elif 长度<65536:#中
        头=bytes([0x80|操作码,126])+长度.to_bytes(2,'big')#二字节长度
    else:#长
        头=bytes([0x80|操作码,127])+长度.to_bytes(8,'big')#八字节长度
    return 头+载荷#完整帧

class 网页套接字:
    '把网页服务器交出来的原始套接字说成一条 WebSocket'
    def __init__(自身,请求,壳):
        '先握手，读循环等监听挂上再开'
        自身.请求=请求#HTTP 请求
        自身.壳=壳#升级套接字壳
        自身.readyState=0#连接中
        自身.bufferedAmount=0#已完成的同步写不记缓冲
        自身._监听={ }#事件到监听
        自身._写锁=threading.Lock()#写帧串行
        自身._读流=请求.rfile#缓冲输入

    def on(自身,事件,监听):
        '登记监听'
        自身._监听.setdefault(事件,[]).append(监听)#追加

    def once(自身,事件,监听):
        '只调用一次'
        def 一次(*参数):
            '摘掉自己再调用'
            自身.off(事件,一次)#摘
            监听(*参数)#调用
        自身.on(事件,一次)#登记

    def off(自身,事件,监听):
        '按身份摘掉'
        表=自身._监听.get(事件)#这一类
        if 表 is not None and 监听 in 表:#还在
            表.remove(监听)#摘

    def _发出(自身,事件,*参数):
        '同步通知当前监听'
        for 监听 in list(自身._监听.get(事件,[])):#拷贝
            监听(*参数)#调用

    def 握手(自身):
        '写出 101。读循环由开始读启动'
        键=自身.请求.headers.get('sec-websocket-key')#客户端键
        if not isinstance(键,str) or 键=='':#没有
            raise RuntimeError('api gateway: missing Sec-WebSocket-Key')#不能升级
        摘要=hashlib.sha1((键+握手魔数).encode('ascii')).digest()#接受摘要
        接受=base64.b64encode(摘要).decode('ascii')#接受键
        响应=(#101
            'HTTP/1.1 101 Switching Protocols\r\n'
            'Upgrade: websocket\r\n'
            'Connection: Upgrade\r\n'
            'Sec-WebSocket-Accept: '+接受+'\r\n\r\n'
        )#响应结束
        自身.请求._处理.wfile.write(响应.encode('ascii'))#写出
        自身.请求._处理.wfile.flush()#发出
        自身.readyState=1#已开

    def 开始读(自身):
        '监听挂好之后再读，避免丢第一帧'
        threading.Thread(target=自身._读循环,daemon=True).start()#读线程

    def send(自身,文本,回调=None):
        '送一条文本帧。回调收到 None 表示写完'
        数据=文本.encode('utf-8') if isinstance(文本,str) else 文本#字节
        帧=_编码帧(1,数据)#文本帧
        try:#写
            with 自身._写锁:#串行
                自身.bufferedAmount=len(帧)#写之前视为还在缓冲
                自身.请求._处理.wfile.write(帧)#写
                自身.请求._处理.wfile.flush()#发出
                自身.bufferedAmount=0#写完
            if 回调 is not None:#有回调
                回调(None)#成功
        except Exception as 错误:#写失败
            自身.bufferedAmount=0#不再占
            if 回调 is not None:#有回调
                回调(错误)#失败
            else:#没有回调
                raise#交给调用方

    def ping(自身):
        '送 ping'
        with 自身._写锁:#串行
            自身.请求._处理.wfile.write(_编码帧(9,b''))#ping
            自身.请求._处理.wfile.flush()#发出

    def close(自身,码=1000,原因=''):
        '先送关闭帧再拆'
        if 自身.readyState>=2:#已经在关
            return#停
        自身.readyState=2#关闭中
        载荷=int(码).to_bytes(2,'big')+(原因.encode('utf-8') if isinstance(原因,str) else 原因)#关闭载荷
        try:#对方可能已经没了
            with 自身._写锁:#串行
                自身.请求._处理.wfile.write(_编码帧(8,载荷))#关闭帧
                自身.请求._处理.wfile.flush()#发出
        except OSError:#写不出去
            pass#接着拆
        自身.terminate()#拆

    def terminate(自身):
        '不再读写，发出 close'
        if 自身.readyState==3:#已经关
            return#停
        自身.readyState=3#已关
        try:#壳可能已经关
            自身.壳.destroy()#关原始套接字
        except Exception:#关失败
            pass#仍然通知
        自身._发出('close')#close

    def _写帧(自身,操作码,载荷):
        '读循环里回 pong'
        with 自身._写锁:#串行
            自身.请求._处理.wfile.write(_编码帧(操作码,载荷))#写
            自身.请求._处理.wfile.flush()#发出

    def _读确切(自身,数量):
        '读满指定字节'
        块=b''#已读
        while len(块)<数量:#还不够
            片=自身._读流.read(数量-len(块))#再读
            if not 片:#对端关了
                raise EOFError('socket closed')#结束
            块+=片#拼上
        return 块#满

    def _读一帧(自身):
        '读一帧并解开客户端掩码'
        头=自身._读确切(2)#基本头
        操作码=头[0] & 0x0f#操作码
        终帧=(头[0] & 0x80)!=0#是否最后一帧
        长度=头[1] & 0x7f#长度
        有掩码=(头[1] & 0x80)!=0#客户端必须打掩码
        if 长度==126:#两字节长度
            长度=int.from_bytes(自身._读确切(2),'big')#长度
        elif 长度==127:#八字节长度
            长度=int.from_bytes(自身._读确切(8),'big')#长度
        掩码=自身._读确切(4) if 有掩码 else None#掩码
        载荷=自身._读确切(长度) if 长度 else b''#载荷
        if 掩码 is not None:#解开
            载荷=bytes(载荷[下标]^掩码[下标%4] for 下标 in range(len(载荷)))#逐字节
        return 终帧,操作码,载荷#一帧

    def _读循环(自身):
        '读到关闭或出错'
        缓冲=b''#分片
        操作=None#数据操作码
        try:#读
            while 自身.readyState==1:#还开着
                终帧,码,载荷=自身._读一帧()#一帧
                if 码==8:#关闭
                    自身.terminate()#拆
                    return#停
                if 码==9:#ping
                    自身._写帧(10,载荷)#pong
                    continue#下一帧
                if 码==10:#pong
                    自身._发出('pong')#活动
                    continue#下一帧
                if 码 in (1,2):#新的数据消息
                    操作=码#记下
                    缓冲=载荷#起
                elif 码==0:#续片
                    缓冲+=载荷#拼
                else:#不认识
                    continue#丢
                if 终帧 and 操作 is not None:#消息齐了
                    if 操作==1:#文本
                        自身._发出('message',缓冲.decode('utf-8'),False)#文本
                    else:#二进制
                        自身._发出('message',缓冲,True)#二进制
                    缓冲=b''#清空
                    操作=None#清空
        except Exception:#读失败
            if 自身.readyState==1:#还以为开着
                自身._发出('error')#出错
                自身.terminate()#拆

class 上行收件箱:
    '一条逻辑流的有界上行队列。方法经 invocation.uplink() 来读'
    def __init__(自身,最大字节,端点,违规时):
        '违规时用远程失败中止逻辑流'
        自身.最大字节=最大字节#上限
        自身.端点=端点#失败里的端点
        自身.违规时=违规时#中止回调
        自身.队列=deque()#项
        自身.字节=0#已缓冲字节
        自身.已结束=False#客户端半关
        自身.已关=False#读者不要了
        自身.已取=False#只有一个读者
        自身.失败=None#读到这里抛出
        自身._条件=threading.Condition()#读者等待

    def __iter__(自身):
        '只允许一个消费者'
        if 自身.已取:#第二个
            raise Exception('api gateway: Remote stream uplink inbox already has a consumer')#拒绝
        自身.已取=True#占住
        return 自身#自己就是迭代器

    def __next__(自身):
        '下一项。结束抛 StopIteration，失败抛原来的错误'
        with 自身._条件:#互斥
            while True:#直到有项、结束或失败
                if 自身.已关:#读者已停
                    raise StopIteration#结束
                if len(自身.队列)>0:#有项
                    条目=自身.队列.popleft()#取出
                    自身.字节-=条目['bytes']#减字节
                    return 条目['value']#值
                if 自身.失败 is not None:#失败
                    raise 自身.失败#抛
                if 自身.已结束:#半关且队列空
                    raise StopIteration#结束
                自身._条件.wait()#等下一次 push

    def 推入(自身,值,帧字节):
        '客户端的一条上行。半关之后或超过上限则失败整条流'
        with 自身._条件:#互斥
            if 自身.失败 is not None or 自身.已关:#已经没了
                return#丢
            if 自身.已结束:#半关之后又来项
                自身._违规(远程错误(
                    'gateway/protocol',
                    'api gateway: Remote stream uplink item after end',
                    {'endpoint':自身.端点},
                ))#协议
                return#停
            if 自身.字节+帧字节>自身.最大字节:#超过上限
                自身._违规(远程错误(
                    'gateway/uplink-overflow',
                    'api gateway: Remote stream uplink exceeded '+str(自身.最大字节)+' buffered bytes',
                    {'endpoint':自身.端点},
                ))#溢出
                return#停
            自身.队列.append({'value':值,'bytes':帧字节})#入队
            自身.字节+=帧字节#记账
            自身._条件.notify_all()#叫醒读者

    def 结束(自身):
        '客户端半关。重复调用无效果'
        with 自身._条件:#互斥
            if 自身.已结束:#已经
                return#停
            自身.已结束=True#半关
            自身._条件.notify_all()#叫醒

    def 失败(自身,错误):
        '下次读取抛出错误，并丢掉缓冲。重复调用无效果'
        with 自身._条件:#互斥
            if 自身.失败 is not None:#已经
                return#停
            自身.失败=错误#记下
            自身.队列.clear()#丢掉
            自身.字节=0#清零
            自身._条件.notify_all()#叫醒

    def 交还(自身):
        '读者不再读。后来的项丢掉'
        with 自身._条件:#互斥
            自身.已关=True#关
            自身.队列.clear()#丢掉
            自身.字节=0#清零
            自身._条件.notify_all()#叫醒挂起的读

    def _违规(自身,错误):
        '先失败队列，再让连接中止逻辑流'
        自身.失败=错误#下次读抛出
        自身.队列.clear()#丢掉
        自身.字节=0#清零
        自身._条件.notify_all()#叫醒
        自身.违规时(错误)#中止

class 远程流复用连接:
    '一条物理套接字上的全部逻辑流'
    def __init__(自身,套接字,打开,失败映射,收件箱字节,存活):
        '打开函数已经绑好对等端'
        自身.套接字=套接字#物理套接字
        自身.打开=打开#打开一条逻辑流
        自身.失败映射=失败映射#错误到线路字段
        自身.收件箱字节=收件箱字节#上行上限
        自身.存活=存活#任何活动都清零错过的心跳
        自身.流表={ }#流标识到活动流
        自身._写锁=threading.Lock()#下行写串行
        自身._关闭=threading.Event()#套接字关闭
        自身._泵={ }#流标识到线程

    def 登记(自身):
        '在开始读之前挂上套接字事件'
        def 当关闭():
            '套接字没了'
            自身._关闭.set()#放开运行
        def 当错误():
            '出错就拆'
            自身.套接字.terminate()#拆
        def 当消息(数据,是二进制):
            '一帧文本'
            自身.存活()#活动
            if 是二进制:#必须是文本
                自身.套接字.close(1003,'text messages required')#关
                return#停
            try:#解析
                自身.接收(数据)#分发
            except Exception:#坏请求
                自身.套接字.close(1008,'invalid Remote stream request')#关
        自身.套接字.once('close',当关闭)#关闭
        自身.套接字.once('error',当错误)#出错
        自身.套接字.on('pong',自身.存活)#pong 也算活动
        自身.套接字.on('message',当消息)#帧

    def 运行(自身):
        '阻塞到套接字关闭，然后停掉全部逻辑流'
        自身._关闭.wait()#等关闭
        活动=list(自身.流表.values())#当时还在的流
        for 流 in 活动:#逐个
            流['停止'](Exception('Remote stream socket closed'))#停
        for 线程 in list(自身._泵.values()):#等泵
            线程.join()#等

    def 接收(自身,文本):
        '分发一帧。已经结束的流上的 item、end、cancel 丢掉。重复 open 关掉套接字'
        报文=解析远程流客户端报文(文本)#校验
        种类=报文['type']#种类
        if 种类=='open':#打开
            自身.打开流(报文)#打开
            return#完
        if 种类=='item':#上行项
            流=自身.流表.get(报文['streamId'])#可能已经结束
            if 流 is not None:#还在
                流['收件箱'].推入(报文.get('value'),len(文本.encode('utf-8')))#入队
            return#完
        if 种类=='end':#半关
            流=自身.流表.get(报文['streamId'])#可能已经结束
            if 流 is not None:#还在
                流['收件箱'].结束()#半关
            return#完
        if 种类=='cancel':#取消
            流=自身.流表.get(报文['streamId'])#可能已经结束
            if 流 is not None:#还在
                流['停止'](Exception('Remote stream cancelled'))#停
            return#完
        raise Exception('api gateway: unknown Remote stream client message '+json.dumps(报文,ensure_ascii=False))#解析不应放行

    def 打开流(自身,报文):
        'open 帧。收件箱先建好，紧跟着的 item 不会丢'
        if 报文['streamId'] in 自身.流表:#重复
            raise Exception('api gateway: duplicate Remote stream id '+json.dumps(报文['streamId'],ensure_ascii=False))#关掉套接字
        中止=中止控制器()#逻辑流取消
        def 违规(错误,中止=中止):
            '上行违规中止逻辑流，原因是远程失败'
            中止.abort(错误)#中止
        收件箱=上行收件箱(自身.收件箱字节,报文['endpoint'],违规)#先建
        活动={'中止':中止,'收件箱':收件箱,'停止':None}#活动记录
        def 停止(原因,中止=中止,收件箱=收件箱):
            '取消并结束还堵在上行上的读取'
            中止.abort(原因)#中止
            收件箱.失败(原因)#叫醒读者
        活动['停止']=停止#填上
        自身.流表[报文['streamId']]=活动#占住标识
        def 跑():
            '泵下行，结束时摘掉'
            try:#泵
                自身.泵(报文['streamId'],报文['endpoint'],报文['payload'],活动)#泵
            finally:#无论成败
                自身.流表.pop(报文['streamId'],None)#摘掉
                自身._泵.pop(报文['streamId'],None)#摘线程
        线程=threading.Thread(target=跑,daemon=True)#不堵接收
        自身._泵[报文['streamId']]=线程#记下
        线程.start()#开始

    def 泵(自身,流标识,端点,载荷,活动):
        '打开业务流并把项写回套接字'
        失败=False#是否抛了
        错误=None#抛出的东西
        try:#打开并消费
            样本=json.dumps({'type':'item','streamId':流标识,'value':None},separators=(',',':'))#带 null 的样例
            开销=len(样本.encode('utf-8'))-len('null')#去掉值本身
            源=自身.打开(端点,载荷,活动['收件箱'],活动['中止'],{#窗口
                'maxBytes':自身.收件箱字节,
                'frameOverheadBytes':开销,
            })#打开
            for 值 in 源:#逐项
                自身.发送({'type':'item','streamId':流标识,'value':值})#下行
        except Exception as 捕获:#打开或消费失败
            失败=True#失败
            错误=捕获#记下
        活动['收件箱'].失败(Exception('Remote stream ended'))#后来的上行改变不了结局
        if 活动['中止'].signal.aborted:#被中止
            原因=活动['中止'].signal.reason#原因
            if 取远程错误(原因) is not None:#远程失败要送到客户端
                自身.发送失败(流标识,原因)#错误帧
            return#取消则不再送 end
        if 失败:#业务失败
            自身.发送失败(流标识,错误)#错误帧
            return#完
        try:#正常结束
            自身.发送({'type':'end','streamId':流标识})#结束帧
        except Exception as 捕获:#结束帧写不出去
            自身.发送失败(流标识,捕获)#改送失败

    def 发送失败(自身,流标识,错误):
        '套接字还开着才送错误帧。送不出去就关掉这一代'
        if 自身.套接字.readyState!=1:#已经关
            return#停
        try:#编码或写可能失败
            自身.发送({'type':'error','streamId':流标识,'error':自身.失败映射(错误)})#错误帧
        except Exception:#终端帧送不出去
            自身.套接字.close(1011,'Remote stream failure could not be delivered')#拆掉物理代际

    def 发送(自身,报文):
        '按顺序写一条下行。写完即返回'
        try:#可能不是 JSON
            文本=json.dumps(报文,separators=(',',':'),ensure_ascii=False)#紧凑
        except (TypeError,ValueError) as 原因:#不能编码
            raise Exception('api gateway: Remote stream item is not JSON serializable') from 原因#失败
        with 自身._写锁:#串行
            if 自身.套接字.readyState!=1:#已经关
                raise Exception('api gateway: Remote stream socket is closed')#失败
            自身.套接字.send(文本)#写

class 远程流复用服务器:
    '无独立监听端口。网页服务器把已准入的升级交过来'
    def __init__(自身,打开,失败映射,心跳间隔毫秒,收件箱字节):
        '打开、失败映射和两个传输参数'
        自身.打开=打开#网关分发
        自身.失败映射=失败映射#线路错误
        自身.心跳间隔毫秒=心跳间隔毫秒#ping 间隔
        自身.收件箱字节=收件箱字节#每条流的上行上限
        自身.客户=set()#打开的套接字
        自身.错过={ }#套接字身份到错过次数
        自身._连接={ }#套接字身份到运行线程
        自身._停心跳=threading.Event()#关闭时停
        自身._心跳线程=None#第一次升级才启动

    def 处理升级(自身,请求,套接字,头,对等):
        '完成握手并服务这条套接字上的逻辑流。对等端在升级时定死'
        网页=网页套接字(请求,套接字)#包装
        try:#握手可能失败
            网页.握手()#101
        except Exception as 错误:#升级失败
            print('[api-gateway] Remote stream upgrade failed:',错误)#诊断
            try:#尽量拆
                套接字.destroy()#拆
            except Exception:#壳没有 destroy
                pass#忽略
            return#不服务
        上下文=对等['ctx'] if isinstance(对等,dict) else 对等.ctx#对等端上下文
        try:#对等端已经拆除时 effect 会失败
            def 绑定寿命():
                '对等端离开时关掉套接字'
                def 离开():
                    '1001 peer left'
                    网页.close(1001,'peer left')#关
                return 离开#拆除器
            释放=上下文.副作用(绑定寿命,'api-gateway: Remote stream socket bound to its Peer')#登记
        except Exception:#已经没有对等端
            网页.close(1001,'peer left')#现在就关
            return#不服务
        def 存活(网页=网页):
            '清零错过的心跳'
            自身.错过[id(网页)]=0#清零
        存活()#刚连上
        自身.客户.add(网页)#记入
        自身._启动心跳()#第一次才启动
        def 绑定打开(端点,载荷,上行,控制,窗口,对等=对等):
            '这条套接字上的流都代表升级时的对等端'
            return 自身.打开(端点,载荷,上行,对等,控制,窗口)#转发
        连接=远程流复用连接(网页,绑定打开,自身.失败映射,自身.收件箱字节,存活)#连接
        连接.登记()#先听
        网页.开始读()#再读
        def 跑完():
            '运行到套接字关闭。对等端作用域仍由 effect 持有，离开时再关套接字'
            try:#连接失败只记日志
                连接.运行()#阻塞到关闭
            except Exception as 错误:#失败
                print('[api-gateway] Remote stream connection failed:',错误)#诊断
            finally:#摘掉心跳记账
                自身.客户.discard(网页)#摘掉
                自身.错过.pop(id(网页),None)#摘掉
        线程=threading.Thread(target=跑完,daemon=True)#不堵升级
        自身._连接[id(网页)]=线程#记下
        线程.start()#运行

    def 关闭(自身):
        '拆掉全部套接字并等到迭代器返回'
        自身._停心跳.set()#停心跳
        for 套接字 in list(自身.客户):#全部
            套接字.terminate()#拆
        for 线程 in list(自身._连接.values()):#等运行结束
            线程.join()#等

    def _启动心跳(自身):
        '第一次升级后启动。空窗期也继续，直到关闭'
        if 自身._心跳线程 is not None:#已经有
            return#停
        def 循环():
            '按间隔 ping。错过两次就拆'
            while not 自身._停心跳.wait(自身.心跳间隔毫秒/1000):#到点且未停
                for 套接字 in list(自身.客户):#每个客户
                    if 套接字.readyState!=1:#不是打开
                        continue#下一个
                    错过=自身.错过.get(id(套接字),0)#当前
                    if 错过>=错过心跳上限:#太久
                        def 再查(套接字=套接字):
                            '等这一拍，若仍然没有活动再拆'
                            if 自身.错过.get(id(套接字),0)>=错过心跳上限:#仍错过
                                套接字.terminate()#拆
                        threading.Thread(target=再查,daemon=True).start()#不堵心跳
                        continue#下一个
                    自身.错过[id(套接字)]=错过+1#记一次
                    try:#ping 可能失败
                        套接字.ping()#ping
                    except Exception:#写失败
                        套接字.terminate()#拆
        自身._心跳线程=threading.Thread(target=循环,daemon=True)#后台
        自身._心跳线程.start()#启动

def 拒绝远程流升级(套接字,状态):
    '不把套接字交给 WebSocket，直接回一段 HTTP 拒绝'
    if 状态==401:#未认证
        原因='Unauthorized'#短语
    elif 状态==403:#禁止
        原因='Forbidden'#短语
    else:#409
        原因='Conflict'#短语
    正文=原因.lower()#小写正文
    字节=正文.encode('utf-8')#长度按字节
    文本='\r\n'.join([#响应
        'HTTP/1.1 '+str(状态)+' '+原因,
        'Connection: close',
        'Content-Type: text/plain; charset=utf-8',
        'Content-Length: '+str(len(字节)),
        '',
        正文,
    ])#拼接
    数据=文本.encode('utf-8')#字节
    if hasattr(套接字,'end'):#Node 双工
        套接字.end(文本)#写出并结束
        return#完
    原始=getattr(套接字,'原始',None)#网页服务器的套接字壳
    if 原始 is not None:#有原始套接字
        原始.sendall(数据)#写出
        套接字.destroy()#关
        return#完
    if hasattr(套接字,'sendall'):#裸套接字
        套接字.sendall(数据)#写出
        套接字.close()#关
        return#完
    if hasattr(套接字,'write'):#类文件
        套接字.write(数据)#写出
        if hasattr(套接字,'close'):#可关
            套接字.close()#关

__all__=['远程流复用服务器','拒绝远程流升级']#公开名
