'客户端拥有的网关复用 Remote 流套接字'
import json,threading#帧与等待
from uuid import uuid4 as 生成标识#逻辑流标识
from ....工具.双端队列 import 双端队列#收件箱
from ....类型化远程调用.协议 import 是否远程上行项#上行项
from ..异常 import 远程流载体错误#物理套接字失败
from ..流协议 import 远程流复用路径,解析远程流服务端报文,已中止,若中止则抛#下行报文

class 流收件箱:
    '一条逻辑流的下行帧'
    def __init__(自身):
        '空队列'
        自身.帧=双端队列()#帧
        自身.失败=None#失败
        自身._条件=threading.Condition()#等待

    def 推入(自身,帧):
        '已失败则丢'
        with 自身._条件:#互斥
            if 自身.失败 is not None:#已经失败
                return#丢
            自身.帧.尾推(帧)#入队
            自身._条件.notify_all()#叫醒

    def 失败(自身,错误):
        '清空并让下一次读取抛出'
        with 自身._条件:#互斥
            if 自身.失败 is not None:#已经
                return#停
            自身.失败=错误 if isinstance(错误,BaseException) else Exception(str(错误))#异常
            自身.帧.清空()#丢掉
            自身._条件.notify_all()#叫醒

    def 下一项(自身):
        '阻塞到有帧或失败'
        with 自身._条件:#互斥
            while 自身.帧.大小==0:#空
                if 自身.失败 is not None:#失败
                    raise 自身.失败#抛
                自身._条件.wait()#等
            return 自身.帧.头弹()#一帧

class 客户端上行队列:
    '流句柄排给载体的上行。end 是半关，close 之后 push 抛'
    def __init__(自身,端点):
        '端点写进失败说明'
        自身.端点=端点#端点
        自身.项=双端队列()#项
        自身.已结束=False#半关
        自身.已关=False#终止
        自身._条件=threading.Condition()#读者

    def __iter__(自身):
        '自己就是迭代器'
        return 自身#自己

    def __next__(自身):
        '下一项。结束后 StopIteration'
        with 自身._条件:#互斥
            while True:#直到有项或结束
                if 自身.已关:#终止
                    raise StopIteration#结束
                if 自身.项.大小>0:#有
                    return 自身.项.头弹()#项
                if 自身.已结束:#半关且空
                    raise StopIteration#结束
                自身._条件.wait()#等

    def push(自身,项):
        '排上一项。半关或终止后抛'
        with 自身._条件:#互斥
            if 自身.已关:#终止
                raise Exception('client api: '+自身.端点+' stream has terminated')#拒绝
            if 自身.已结束:#半关
                raise Exception('client api: '+自身.端点+' uplink was ended')#拒绝
            自身.项.尾推(项)#入队
            自身._条件.notify_all()#叫醒

    def end(自身):
        '半关。重复或终止后忽略'
        with 自身._条件:#互斥
            if 自身.已结束 or 自身.已关:#不用
                return#停
            自身.已结束=True#半关
            自身._条件.notify_all()#叫醒

    def close(自身):
        '载体不再读。之后 push 抛'
        with 自身._条件:#互斥
            if 自身.已关:#已经
                return#停
            自身.已关=True#关
            自身.项.清空()#丢掉
            自身._条件.notify_all()#叫醒

    def 交还(自身):
        '迭代器交还即关闭'
        自身.close()#关

class 远程流复用客户端:
    '一条物理 WebSocket 上挂多条可单独取消的逻辑流'
    def __init__(自身,打开套接字=None,等待重连=False):
        '打开套接字缺省用浏览器 WebSocket。应答客户端丢套接字后等待重连'
        if 打开套接字 is None:#缺省
            def 缺省打开(路径):
                '这个网页引擎不再打开浏览器上的复用套接字'
                raise 远程流载体错误('api gateway: 这个网页引擎不再打开浏览器套接字 '+str(路径))#拒绝
            打开套接字=缺省打开#用它
        自身._打开套接字=打开套接字#打开
        自身._等待重连=等待重连#应答客户端
        自身.套接字=None#当前物理套接字
        自身._取消候选=None#连接中可取消
        自身._修订=0#重连代际
        自身.流表={ }#逻辑流
        自身._等待者=[]#等套接字的人
        自身._运行=False#start 过
        自身._已拆除=False#close 过
        自身.失败=None#最近的载体失败
        自身._锁=threading.Lock()#维护与发送

    def start(自身):
        '确保有一次物理连接尝试'
        if 自身._已拆除:#已关
            return#停
        自身._运行=True#运行
        if 自身.套接字 is not None and getattr(自身.套接字,'readyState',None)==1:#已经开着
            return#停
        自身._维护()#开始

    def reconnect(自身):
        '取消当前套接字并立刻再连'
        if not 自身._运行 or 自身._已拆除:#没在跑
            return#停
        失败=远程流载体错误('api gateway: Remote stream reconnect requested')#原因
        自身._修订+=1#新代际
        自身.失败=None#清掉旧失败
        取消=自身._取消候选#连接中的尝试
        套接字=自身.套接字#当前
        if 套接字 is not None:#有
            自身.套接字=None#摘掉
            自身._全部失败(失败)#失败逻辑流
            if hasattr(套接字,'close'):#可关
                套接字.close(4000,'reconnect requested')#关
        if callable(取消):#还在连接
            取消(失败)#取消这次
        自身._维护()#再来

    def open(自身,端点,载荷,信号,上行=None):
        '打开一条逻辑流并产出宿主项'
        若中止则抛(信号)#已经取消
        流标识=str(生成标识())#标识
        收件箱=流收件箱()#下行
        流={'收件箱':收件箱,'泵':None}#逻辑流
        载体=None#这次用的套接字
        已打开=False#open 帧是否送出
        已终端=False#是否收到终端帧
        def 当中止():
            '取消时失败收件箱'
            原因=getattr(信号,'reason',None)#原因
            收件箱.失败(原因 if isinstance(原因,BaseException) else Exception('The operation was aborted.'))#失败
        摘=None#下面挂
        from ..流协议 import 挂中止#中止
        摘=挂中止(信号,当中止)#听
        try:#打开并读
            套接字=自身._等待套接字(信号)#物理套接字
            若中止则抛(信号)#再看一次
            载体=套接字#记下
            自身.流表[流标识]=流#登记
            自身._发送(套接字,{'type':'open','streamId':流标识,'endpoint':端点,'payload':载荷})#打开
            已打开=True#送出
            if 上行 is not None:#有上行
                流['泵']=自身._泵上行(套接字,流标识,上行,信号,收件箱)#泵
            while True:#读下行
                帧=收件箱.下一项()#一帧
                若中止则抛(信号)#取消
                if 帧['type']=='item':#项
                    yield 帧.get('value')#值
                    continue#下一
                已终端=True#终端
                if 帧['type']=='error':#错误
                    from ....类型化远程调用.协议 import 远程错误#还原
                    错误=帧['error']#错误体
                    raise 远程错误(错误['code'],错误['message'],错误['details'])#抛
                return#end
        finally:#清理
            if 摘 is not None:#摘监听
                摘()#摘
            自身.流表.pop(流标识,None)#摘掉
            泵=流.get('泵')#泵
            if 泵 is not None:#有
                泵['stop']()#停
            if 已打开 and not 已终端 and 载体 is not None and getattr(载体,'readyState',None)==1:#还开着
                自身._发送(载体,{'type':'cancel','streamId':流标识})#取消
            if 泵 is not None:#等泵停
                泵['done'].wait()#等

    def _泵上行(自身,套接字,流标识,上行,信号,收件箱):
        '把调用方的上行项送出。stop 打断阻塞的 next'
        完成=threading.Event()#泵停了
        停止旗={'v':False}#是否停止
        迭代=iter(上行)#迭代器
        def 释放():
            '交还迭代器'
            if isinstance(上行,客户端上行队列):#队列
                上行.close()#关
            关闭=getattr(迭代,'close',None)#生成器
            if callable(关闭):#有
                try:#不等待阻塞的 next
                    关闭()#交还
                except Exception:#失败忽略
                    pass#忽略
        def 跑():
            '读上行并发送'
            try:#泵
                while not 停止旗['v']:#还要
                    if 已中止(信号) or 自身.套接字 is not 套接字:#换代或取消
                        return#停
                    try:#下一项
                        项=next(迭代)#项
                    except StopIteration:#半关
                        自身._发送(套接字,{'type':'end','streamId':流标识})#end
                        return#停
                    if 停止旗['v'] or 已中止(信号) or 自身.套接字 is not 套接字:#停了
                        return#停
                    自身._发送(套接字,{'type':'item','streamId':流标识,'value':项})#项
            except Exception as 错误:#上行失败则失败下行
                收件箱.失败(错误)#失败
            finally:#释放
                释放()#交还
                完成.set()#停了
        threading.Thread(target=跑,daemon=True).start()#泵
        def 停止():
            '打断泵'
            if 停止旗['v']:#已经
                return#停
            停止旗['v']=True#停
            释放()#让阻塞的 next 起来
        return {'done':完成,'stop':停止}#泵

    def close(自身):
        '永久停止，关掉套接字并失败全部逻辑流'
        if not 自身._已拆除:#第一次
            自身._已拆除=True#关
            自身._运行=False#停
            错误=Exception('api gateway: Remote stream client disposed')#原因
            自身._全部失败(错误)#逻辑流
            for 等待 in list(自身._等待者):#等套接字的
                等待['reject'](错误)#拒绝
            自身._等待者.clear()#清空
            取消=自身._取消候选#连接中
            if callable(取消):#有
                取消(错误)#取消
            套接字=自身.套接字#当前
            自身.套接字=None#摘
            if 套接字 is not None and hasattr(套接字,'close'):#可关
                套接字.close(1000,'disposed')#关

    def _等待套接字(自身,信号):
        '已经开着就直接返回。否则等到 open 或失败'
        若中止则抛(信号)#已取消
        if 自身.套接字 is not None and getattr(自身.套接字,'readyState',None)==1:#开着
            return 自身.套接字#用它
        if 自身._已拆除:#已关
            raise Exception('api gateway: Remote stream client disposed')#拒绝
        if not 自身._运行:#没 start
            raise Exception('api gateway: Remote stream client not started')#拒绝
        if 自身.失败 is not None:#上次失败
            raise 自身.失败#抛
        盒={'完成':threading.Event()}#等待
        def 成功(套接字):
            '连上了'
            盒['套接字']=套接字#记下
            盒['完成'].set()#放开
        def 拒绝(错误):
            '失败'
            盒['错误']=错误#记下
            盒['完成'].set()#放开
        等待={'revision':自身._修订,'resolve':成功,'reject':拒绝}#等待者
        自身._等待者.append(等待)#登记
        def 当中止():
            '取消等待'
            拒绝(getattr(信号,'reason',None) or Exception('The operation was aborted.'))#拒绝
        from ..流协议 import 挂中止#听
        摘=挂中止(信号,当中止)#听
        盒['完成'].wait()#阻塞
        if 等待 in 自身._等待者:#还在
            自身._等待者.remove(等待)#摘
        摘()#摘监听
        if '错误' in 盒:#失败
            错误=盒['错误']#错误
            if isinstance(错误,BaseException):#异常
                raise 错误#抛
            raise Exception(str(错误))#其它
        return 盒['套接字']#套接字

    def _接收(自身,套接字,数据):
        '当前套接字上的一帧'
        if 套接字 is not 自身.套接字:#旧代际
            return#丢
        try:#解析
            if not isinstance(数据,str):#必须文本
                raise Exception('api gateway: Remote stream WebSocket requires text messages')#拒绝
            帧=解析远程流服务端报文(数据)#帧
            流=自身.流表.get(帧['streamId'])#逻辑流
            if 流 is None:#已经没了
                return#丢
            流['收件箱'].推入(帧)#交给读者
            if 帧['type']!='item' and 流.get('泵') is not None:#终端帧立刻停上行
                流['泵']['stop']()#停
        except Exception as 错误:#坏帧
            失败=远程流载体错误('api gateway: invalid Remote stream frame',错误)#载体失败
            自身._全部失败(失败)#全部
            自身._丢失(套接字,失败)#丢掉套接字
            if hasattr(套接字,'close'):#可关
                套接字.close(4002,'invalid Remote stream frame')#关

    def _丢失(自身,套接字,错误=None):
        '套接字没了'
        if 自身.套接字 is not 套接字:#不是当前
            return#停
        if 错误 is None:#缺省说明
            错误=远程流载体错误('api gateway: Remote stream WebSocket closed')#关闭
        自身.套接字=None#摘
        if not 自身._等待重连:#被动客户端不再等
            自身.失败=错误#记下
        自身._全部失败(错误)#逻辑流
        if not 自身._等待重连:#不等重连
            for 等待 in list(自身._等待者):#等套接字的
                等待['reject'](错误)#拒绝
            自身._等待者.clear()#清空

    def _维护(自身):
        '没有套接字也没有进行中的尝试时连一次'
        if not 自身._运行 or 自身._已拆除:#不该连
            return#停
        if 自身.套接字 is not None and getattr(自身.套接字,'readyState',None)==1:#已经开着
            return#停
        修订=自身._修订#这一次
        自身.失败=None#清失败
        def 跑():
            '连接。失败则拒绝这一修订及更早的等待者'
            try:#连
                自身._连接()#阻塞到 open 或失败
            except Exception as 错误:#失败
                if not 自身._运行:#已经停
                    return#不通知
                失败=错误 if isinstance(错误,远程流载体错误) else 远程流载体错误('api gateway: Remote stream WebSocket failed to open',错误)#载体
                if 自身._修订==修订:#还是这一次
                    自身.失败=失败#记下
                for 等待 in list(自身._等待者):#等待者
                    if 等待['revision']<=修订:#这一代或更早
                        等待['reject'](失败)#拒绝
        threading.Thread(target=跑,daemon=True).start()#不堵 start

    def _连接(自身):
        '打开套接字并等到 open'
        套接字=自身._打开套接字(远程流复用路径)#打开
        完成=threading.Event()#open 或失败
        盒={ }#结果
        已结算={'v':False}#只结算一次
        def 拒绝候选(错误):
            '连接阶段被取消或失败'
            已结算['v']=True#占住
            自身._取消候选=None#摘
            if getattr(套接字,'readyState',1)<2 and hasattr(套接字,'close'):#还没关
                套接字.close()#关
            盒['错误']=错误#记下
            完成.set()#放开
        def 已开():
            'open'
            已结算['v']=True#占住
            自身._取消候选=None#摘
            自身.套接字=套接字#当前
            for 等待 in list(自身._等待者):#等的人
                等待['resolve'](套接字)#交给他们
            完成.set()#放开
        def 出错():
            'error'
            if not 已结算['v']:#还在连接
                拒绝候选(远程流载体错误('api gateway: Remote stream WebSocket failed to open'))#没打开
                return#停
            错误=远程流载体错误('api gateway: Remote stream WebSocket failed')#打开后失败
            自身._丢失(套接字,错误)#丢
            if getattr(套接字,'readyState',1)<2 and hasattr(套接字,'close'):#还没关
                套接字.close()#关
        def 已关():
            'close'
            if not 已结算['v']:#还没 open
                拒绝候选(远程流载体错误('api gateway: Remote stream WebSocket closed before opening'))#没打开
                return#停
            自身._丢失(套接字)#丢
        def 收到(事件=None):
            'message。浏览器事件或直接给数据'
            数据=事件#直接是数据
            if isinstance(事件,dict) and 'data' in 事件:#事件
                数据=事件['data']#数据
            elif hasattr(事件,'data'):#事件对象
                数据=事件.data#数据
            自身._接收(套接字,数据)#处理
        自身._取消候选=拒绝候选#可取消
        if hasattr(套接字,'addEventListener'):#浏览器
            套接字.addEventListener('open',已开)
            套接字.addEventListener('error',出错)
            套接字.addEventListener('message',收到)
            套接字.addEventListener('close',已关)
        elif hasattr(套接字,'on'):#Node 风格
            套接字.on('open',已开)
            套接字.on('error',出错)
            套接字.on('message',收到)
            套接字.on('close',已关)
        if getattr(套接字,'readyState',0)==1:#已经开着
            已开()#补一次
        完成.wait()#阻塞到结算
        if '错误' in 盒:#失败
            错误=盒['错误']#错误
            if isinstance(错误,BaseException):#异常
                raise 错误#抛
            raise Exception(str(错误))#其它
        return 套接字#开着

    def _全部失败(自身,错误):
        '失败全部逻辑流并停上行'
        for 流 in list(自身.流表.values()):#每一个
            流['收件箱'].失败(错误)#下行
            if 流.get('泵') is not None:#有泵
                流['泵']['stop']()#停

    def _发送(自身,套接字,报文):
        '送一条客户端报文'
        套接字.send(json.dumps(报文,separators=(',',':'),ensure_ascii=False))#文本

__all__=['远程流复用客户端','客户端上行队列','远程流载体错误']#公开名
