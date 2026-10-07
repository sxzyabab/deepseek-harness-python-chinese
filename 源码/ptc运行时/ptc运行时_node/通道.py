'带长度前缀的 JSON 传输，输入与排队写入均有界'
import json,threading#编解码与读线程
from ...基础设施.通用工具.序列化编码 import 紧凑json编码
from ...基础设施.js特性 import PromiseEX as 期约#期约
from .输出json import json值字节上限#排队字节预算
from .异常 import 节点ptc错误#本包异常

__all__=['json通道']#仅中文公开名

解码=json.loads#JSON 解码

def 取收发(流):#按流形态定死收发
    '构造时定死收发；套接字走 recv/sendall，文件走 read/write'
    收=流.recv if hasattr(流,'recv') else 流.read#收
    发=流.sendall if hasattr(流,'sendall') else (流.send if hasattr(流,'send') else 流.write)#发
    return 收,发#一对

class json通道:#一路同船进程通道；消费方拥有帧校验与终态
    '一路同船进程通道；消费方拥有帧校验与终态'
    def __init__(自身,流,最大字节,接收,失败):#绑上流与回调
        """记下双工流、帧上限、接收回调与失败回调。
        接收(消息,字节)。
        失败(错误,种类) 种类为 io 或 protocol
        """
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
        自身.读线程=threading.Thread(target=自身._读循环,daemon=True)#后台读
        自身.读线程.start()#开始读

    def _读循环(自身):#直到关闭
        '阻塞读分帧'
        try:#读到关闭
            while not 自身._已关:#未关
                块=自身._收(65536)#一块
                if not 块:#对端结束
                    if not 自身._已关:#尚未关
                        自身._失败(节点ptc错误('control channel ended before the program settled'),'io')#io 失败
                    return
                自身._喂入(块)#分帧
        except (OSError,ValueError) as 错误:#传输失败
            自身._结束写入(节点ptc错误(str(错误)))#拒绝排队
            if not 自身._已关:#尚未关
                自身._失败(节点ptc错误(str(错误)),'io')#io 失败

    def _喂入(自身,块):#把一块喂进分帧器
        '把一块喂进分帧器'
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

    def 发送(自身,消息):#立刻提交一帧，写入回执以期约返回
        """立刻提交一帧并返回写入回执期约。
        消息是仅 JSON 的同船协议值。
        本帧写完后期约解决；传输失败则拒绝
        """
        if 自身._已关:#已关
            失败=期约()#关闭回执
            失败.拒绝(节点ptc错误('控制通道已关闭'))#拒绝
            return 失败#已关闭
        大小=json值字节上限(消息,自身._最大字节)#计量
        if 大小 is None or 自身._排队字节+大小>自身._最大字节:#超排队
            失败=期约()#超限回执
            失败.拒绝(节点ptc错误('控制输出超过'+str(自身._最大字节)+'字节排队上限'))#拒绝
            return 失败#超限
        正文=紧凑json编码(消息).encode('utf-8')#正文
        头=len(正文).to_bytes(4,'big')#长度头
        自身._排队字节+=len(正文)#入队
        完成=期约()#本帧回执
        写入={'任务':完成,'长度':len(正文)}#未完成记录
        自身._写入表.add(id(写入))#记下
        写入['_自身']=写入#保住对象
        def 结束(错误=None):#本帧结束
            '本帧结束'
            if id(写入) not in 自身._写入表:#已结束
                return#忽略
            自身._写入表.discard(id(写入))#摘掉
            自身._排队字节-=写入['长度']#出队
            if 错误 is not None:#失败
                完成.拒绝(错误)#拒绝
            else:#成功
                完成.解决()#解决
        try:#保持帧序同步写出
            自身._发(头)#写头
            自身._发(正文)#写正文
            结束()#写完
        except (OSError,ValueError,节点ptc错误) as 错误:#写出失败
            包装=错误 if isinstance(错误,节点ptc错误) else 节点ptc错误(str(错误))#本包错误
            结束(包装)#拒绝
        return 完成#写入回执

    def _结束写入(自身,错误):#拒绝所有排队
        '拒绝所有排队写入'
        for 标识 in list(自身._写入表):#逐个
            pass#id 集合不够还原对象
        自身._写入表.clear()#清空
        自身._排队字节=0#清零
        _=错误#失败已由调用方报告

    def 关闭(自身):#停读并关掉拥有端
        '停读并关掉拥有端；排队写入在关闭时拒绝'
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
        '等已接受写入结束或失败，返回期约'
        落定=期约()#排空回执
        def 已排空(结算=None):#写出都已结束
            '排空完成'
            if 落定.状态=='pending':#尚未解决
                落定.解决()#解决
        def 排空失败(错误):#结算失败
            '排空失败'
            if 落定.状态=='pending':#尚未拒绝
                落定.拒绝(错误)#拒绝
        期约.全部已结算([]).然后(已排空,排空失败)#发送回执解决前写出已经结束
        return 落定#排空回执
