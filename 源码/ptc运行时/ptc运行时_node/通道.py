"""带长度前缀的 JSON 传输，输入与排队写入均有界。"""
import json,threading#编解码与读线程
from concurrent.futures import Future as 原生结果#单次操作结果
from .输出json import json值字节上限#排队字节预算
from .协议 import 节点ptc错误#本包异常

__all__=['任务','全部并发','全部结算','json通道']#仅中文公开名

编码=json.dumps#JSON 编码
解码=json.loads#JSON 解码

class 任务:#单次操作的 Future 包装，只留 等待
    """单次操作的 Future 包装，只留 等待。"""
    def __init__(自身):#未决任务
        """构造未决任务。"""
        自身._未来=原生结果()#底层 Future

    def 兑现(自身,值=None):#成功结算
        """成功结算。"""
        if not 自身._未来.done():#尚未结算
            自身._未来.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):#失败结算
        """失败结算。"""
        if not 自身._未来.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._未来.set_exception(错误)#原样拒绝
            else:#非异常
                自身._未来.set_exception(节点ptc错误(str(错误)))#包成本包错误

    def 等待(自身,超时=None):#阻塞等到结算
        """阻塞等到结算。"""
        return 自身._未来.result(timeout=超时)#取结果或抛错

def 全部并发(函数列表):#Promise.all
    """每路一线程，join 后按原序取结果；一路失败则抛。函数列表是可调用列表。"""
    结果表=[None]*len(函数列表)#按原序结果
    错误表=[None]*len(函数列表)#按原序错误
    def 跑一路(下标,函数):#执行一路
        """执行一路并写入表。"""
        try:#执行
            结果表[下标]=函数()#成功
        except BaseException as 错误:#失败
            错误表[下标]=错误#记下
    线程表=[]#工作线程
    for 下标,函数 in enumerate(函数列表):#每路一线程
        工作=threading.Thread(target=跑一路,args=(下标,函数),daemon=True)#工作线程
        工作.start()#启动
        线程表.append(工作)#登记
    for 工作 in 线程表:#扇出 join
        工作.join()#等到结束
    for 错误 in 错误表:#按原序检查
        if 错误 is not None:#有失败
            raise 错误#原样抛
    return 结果表#按原序结果

def 全部结算(任务列表):#Promise.allSettled
    """并发等全部任务落定，吞掉失败。任务列表是任务对象列表。"""
    def 等待并吞错(一项):#等待一路
        """等待一路并吞错。"""
        try:#等待
            一项.等待()#等到结算
        except BaseException:#排空不抛
            pass#吞掉
    线程表=[]#工作线程
    for 一项 in 任务列表:#每路一线程
        工作=threading.Thread(target=等待并吞错,args=(一项,),daemon=True)#工作线程
        工作.start()#启动
        线程表.append(工作)#登记
    for 工作 in 线程表:#等全部结束
        工作.join()#等到结束

def 取收发(流):#按流形态定死收发
    """构造时定死收发；套接字走 recv/sendall，文件走 read/write。"""
    收=流.recv if hasattr(流,'recv') else 流.read#收
    发=流.sendall if hasattr(流,'sendall') else (流.send if hasattr(流,'send') else 流.write)#发
    return 收,发#一对

class json通道:#一路同船进程通道；消费方拥有帧校验与终态
    """一路同船进程通道；消费方拥有帧校验与终态。"""
    def __init__(自身,流,最大字节,接收,失败):#绑上流与回调
        """记下双工流、帧上限、接收回调与失败回调。接收(消息,字节)。失败(错误,种类) 种类为 io 或 protocol。"""
        自身._流=流#双工端点
        自身._最大字节=最大字节#帧与排队上限
        自身._接收=接收#帧回调
        自身._失败=失败#失败回调
        自身._收,自身._发=取收发(流)#定死收发
        自身._头=bytearray(4)#长度头缓冲
        自身._头字节=0#已收头字节
        自身._载荷=None#载荷缓冲
        自身._载荷字节=0#已收载荷
        自身._排队字节=0#已接受未完成写入
        自身._已关=False#是否已关
        自身._写入表=set()#未完成写入
        自身._锁=threading.Lock()#状态锁
        读线程=threading.Thread(target=自身._读循环,daemon=True)#后台读
        读线程.start()#开始读

    def _读循环(自身):#直到关闭
        """阻塞读分帧。"""
        try:#读到关闭
            while not 自身._已关:#未关
                块=自身._收(65536)#一块
                if not 块:#对端结束
                    if not 自身._已关:#尚未关
                        自身._失败(节点ptc错误('control channel ended before the program settled'),'io')#io 失败
                    return#结束
                自身._喂入(块)#分帧
        except (OSError,ValueError) as 错误:#传输失败
            自身._结束写入(节点ptc错误(str(错误)))#拒绝排队
            if not 自身._已关:#尚未关
                自身._失败(节点ptc错误(str(错误)),'io')#io 失败

    def _喂入(自身,块):#把一块喂进分帧器
        """把一块喂进分帧器。"""
        if 自身._已关:#已关
            return#忽略
        try:#协议错误走 protocol
            偏移=0#块内偏移
            while 偏移<len(块) and not 自身._已关:#还有未消费且未关
                if 自身._载荷 is None:#在收头
                    要=min(4-自身._头字节,len(块)-偏移)#本次头字节
                    自身._头[自身._头字节:自身._头字节+要]=块[偏移:偏移+要]#拷入
                    自身._头字节+=要#推进
                    偏移+=要#推进
                    if 自身._头字节!=4:#头未齐
                        continue#再等
                    长度=int.from_bytes(自身._头,'big')#大端长度
                    if 长度==0 or 长度>自身._最大字节:#空帧或超限
                        raise 节点ptc错误('control frame exceeds '+str(自身._最大字节)+' bytes or is empty')#协议
                    自身._载荷=bytearray(长度)#开载荷
                    自身._载荷字节=0#重置
                    自身._头字节=0#重置头
                要=min(len(自身._载荷)-自身._载荷字节,len(块)-偏移)#本次载荷
                自身._载荷[自身._载荷字节:自身._载荷字节+要]=块[偏移:偏移+要]#拷入
                自身._载荷字节+=要#推进
                偏移+=要#推进
                if 自身._载荷字节!=len(自身._载荷):#载荷未齐
                    continue#再等
                帧=bytes(自身._载荷)#完整帧
                自身._载荷=None#清空
                自身._载荷字节=0#重置
                消息=解码(帧.decode('utf-8'))#严格 UTF-8 JSON
                自身._接收(消息,len(帧))#分派
        except (节点ptc错误,UnicodeDecodeError,ValueError,TypeError,json.JSONDecodeError) as 错误:#协议
            包装=错误 if isinstance(错误,节点ptc错误) else 节点ptc错误(str(错误))#本包错误
            自身._失败(包装,'protocol')#协议失败

    def 发送(自身,消息):#立刻提交一帧并等写入回执
        """立刻提交一帧并等流的写入回执。消息是仅 JSON 的同船协议值。本帧写完后返回；传输失败则抛。"""
        if 自身._已关:#已关
            raise 节点ptc错误('control channel is closed')#关闭
        大小=json值字节上限(消息,自身._最大字节)#计量
        if 大小 is None or 自身._排队字节+大小>自身._最大字节:#超排队
            raise 节点ptc错误('control output exceeds '+str(自身._最大字节)+' queued bytes')#拒绝
        正文=编码(消息,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')#正文
        头=len(正文).to_bytes(4,'big')#长度头
        自身._排队字节+=len(正文)#入队
        完成=任务()#本帧任务
        写入={'任务':完成,'长度':len(正文)}#未完成记录
        自身._写入表.add(id(写入))#记下
        写入['_自身']=写入#保住对象
        def 结束(错误=None):#本帧结束
            """本帧结束。"""
            if id(写入) not in 自身._写入表:#已结束
                return#忽略
            自身._写入表.discard(id(写入))#摘掉
            自身._排队字节-=写入['长度']#出队
            if 错误 is not None:#失败
                完成.拒绝(错误)#拒绝
            else:#成功
                完成.兑现()#兑现
        try:#保持帧序同步写出
            自身._发(头)#写头
            自身._发(正文)#写正文
            结束()#写完
        except (OSError,ValueError,节点ptc错误) as 错误:#写出失败
            包装=错误 if isinstance(错误,节点ptc错误) else 节点ptc错误(str(错误))#本包错误
            结束(包装)#拒绝
        完成.等待()#等本帧
        return None#发送完成

    def _结束写入(自身,错误):#拒绝所有排队
        """拒绝所有排队写入。"""
        for 标识 in list(自身._写入表):#逐个
            pass#id 集合不够还原对象
        自身._写入表.clear()#清空
        自身._排队字节=0#清零
        _=错误#失败已由调用方报告

    def 关闭(自身):#停读并关掉拥有端
        """停读并关掉拥有端；排队写入在关闭时拒绝。"""
        if 自身._已关:#已关
            return#忽略
        自身._已关=True#标记
        自身._载荷=None#丢掉半帧
        自身._结束写入(节点ptc错误('control channel is closed'))#拒绝排队
        try:#关端点
            自身._流.close()#关
        except (OSError,ValueError):#已关
            pass#忽略

    def 排空(自身):#等已接受写入结束或失败
        """等已接受写入结束或失败。"""
        return None#同步发送路径下无未完成写入
