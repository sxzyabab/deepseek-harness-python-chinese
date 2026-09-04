"""经 Inspector Worker ingest WebSocket 的 Client 观测与 Runtime 端点。

对齐上游 `client/bridge/transport.ts`。公开面仅中文名。
"""
import json,threading#序列化与中止
from ...共享.json import 是否json值,json字节长度#JSON工具
from ...共享.桥接.版本 import 检查器协议版本#协议版本
from ...共享.桥接.消息.观察 import 解析工作者源帧#Worker源帧
from ...共享.桥接.发布器 import 检查器源连接#源连接基类
from ...共享.桥接.缓冲 import 检查器源缓冲选项#缓冲选项
from ...共享.桥接.rpc import 检查器查询连接选项#查询选项
from ..cdp.运行时 import 客户端运行时上限,客户端运行时执行器#Runtime
from ..cdp.控制台 import 客户端控制台观察器#Console
from ..cdp.源 import 客户端源目录错误,发现检查器客户端源目录#Sources
from ..检视.领域 import 客户端领域源#realm源
from ..检视.网络 import 网络主题#网络主题
from .生命周期 import 客户端桥生命周期#生命周期
from .发布器 import 客户端桥发布器#发布器
from .rpc import 客户端桥rpc#查询RPC
from .分发器 import 分发桥帧#帧分发

__all__=['打开客户端套接字','客户端检查器源']#仅中文公开名

def 取引导(引导,键):#取引导字段
    """兼容对象与字典引导。"""
    return getattr(引导,键) if hasattr(引导,键) else 引导[键]#取值

def 打开客户端套接字(端点,协议):#打开WebSocket
    """打开 Client ingest 套接字；需运行时绑定。"""
    raise Exception('inspector: Client WebSocket requires a runtime binding')#需绑定

def 渲染错误(错误):#渲染错误
    """渲染错误消息。"""
    return 错误.args[0] if isinstance(错误,Exception) and 错误.args else str(错误)#消息

class _中止控制器:#中止控制器
    """近似 AbortController。"""
    def __init__(自身):#构造
        """创建事件。"""
        自身.事件=threading.Event()#中止事件
        自身.signal=自身.事件#信号别名

    def abort(自身):#中止
        """置位中止。"""
        自身.事件.set()#置位

class 客户端检查器源(检查器源连接):#Client检查器源
    """重连 Client 源：有界队列永不阻塞页面工作。"""
    def __init__(自身,引导,标签='Client',源目录=None,领域源=None):#构造
        """构造并首次连接。"""
        super().__init__()#基类
        自身.引导=引导#引导
        自身.领域源=领域源 or 客户端领域源(标签)#realm源
        if 源目录 is None:#默认发现
            源目录=发现检查器客户端源目录()#发现
        自身.源目录=源目录#源目录
        自身.套接字=None#活动套接字
        自身.代数=None#当前代数
        自身.已接受=False#是否已接受
        自身.已关闭=False#是否已永久关闭
        自身.运行时请求={}#进行中Runtime请求
        自身.生命周期=客户端桥生命周期(取引导(引导,'reconnectBaseMs'),取引导(引导,'reconnectMaxMs'))#生命周期
        自身.发布器实例=客户端桥发布器(检查器源缓冲选项(#发布器
            ['*'],取引导(引导,'maxQueuedRecords'),取引导(引导,'maxQueuedBytes'),#队列
            取引导(引导,'maxRecordsPerFrame'),取引导(引导,'maxFrameBytes'),#帧
        ),取引导(引导,'maxQueuedBytes'))#缓冲上限
        def 脚本键(网址):#脚本键查找
            """脚本键查找。"""
            return None if 自身.源目录 is None else 自身.源目录.按网址取脚本键(网址)#委托
        自身.运行时=客户端运行时执行器(客户端运行时上限(#Runtime
            取引导(引导,'maxRuntimeObjectsPerSession'),#对象上限
            取引导(引导,'maxRuntimePropertiesPerResult'),#属性上限
            取引导(引导,'maxFrameBytes'),#响应字节
        ),脚本键)#执行器
        自身.控制台=客户端控制台观察器(自身.运行时,自身._投递控制台,脚本键)#Console
        自身.查询实例=客户端桥rpc(检查器查询连接选项(取引导(引导,'queryTimeoutMs'),取引导(引导,'maxFrameBytes')))#查询
        自身.连接()#首次连接

    def _发布器(自身):#状态发布器
        """状态发布器。"""
        return 自身.发布器实例#发布器

    def _查询器(自身):#查询请求器
        """查询请求器。"""
        return 自身.查询实例#查询

    def _投递控制台(自身,会话标识,事件):#Console回调
        """投递 Console 事件帧。"""
        套接字=自身.套接字#套接字
        代数=自身.代数#代数
        if 自身.已关闭 or not 自身.已接受 or 套接字 is None or 代数 is None:#不可发
            return#返回
        if getattr(套接字,'readyState',1)!=1:#未开
            return#返回
        帧={'v':检查器协议版本,'t':'client-console/event','sourceId':自身.领域源.sourceId,'generation':代数,'sessionId':会话标识,'event':事件}#事件帧
        if not 是否json值(帧) or json字节长度(帧)>取引导(自身.引导,'maxFrameBytes'):#超限
            return#丢弃
        try:#发送
            套接字.send(json.dumps(帧,ensure_ascii=False))#发送
        except Exception:#发送失败
            pass#套接字关闭路径会重置

    def 关闭(自身):#永久关闭
        """永久停止重连并关闭活动 source 代数。"""
        if 自身.已关闭:#幂等
            return#返回
        自身.已关闭=True#置位
        自身.控制台.关闭()#关闭Console
        自身.取消全部运行时请求()#取消请求
        自身.运行时.重置()#重置Runtime
        自身.查询实例.关闭('Inspector Client source closed')#关闭查询
        自身.生命周期.关闭()#关闭生命周期
        自身.发布器实例.关闭()#关闭发布器
        套接字=自身.套接字#套接字
        代数=自身.代数#代数
        try:#发送关闭
            if 套接字 is not None and getattr(套接字,'readyState',1)==1 and 代数 is not None:#可发
                帧={'v':检查器协议版本,'t':'source/close','sourceId':自身.领域源.sourceId,'generation':代数}#关闭帧
                套接字.send(json.dumps(帧,ensure_ascii=False))#发送
                套接字.close(1000,'Client source closed')#正常关闭
            elif 套接字 is not None:#不可发
                套接字.close()#尽力关
        finally:#清理
            自身.套接字=None#清空套接字
            自身.领域源.关闭()#释放realm

    def 连接(自身):#连接或重连
        """打开下一传输代数。"""
        if 自身.已关闭:#已永久关闭
            return#返回
        自身.控制台.重置()#重置Console
        自身.取消全部运行时请求()#取消请求
        自身.运行时.重置()#重置Runtime
        自身.查询实例.断开('Inspector Client source reconnecting')#断开查询
        源=自身.领域源.连接(自身.源目录 is not None)#新代数
        代数=源['generation']#代数
        套接字=打开客户端套接字(取引导(自身.引导,'endpoint'),取引导(自身.引导,'protocol'))#打开WS
        自身.套接字=套接字#保存
        自身.代数=代数#保存代数
        自身.已接受=False#未接受
        自身.发布器实例.连接(套接字,源)#接通发布器
        def 打开(_事件=None):#打开
            """发送 source/open。"""
            if 自身.套接字 is not 套接字 or 自身.已关闭:#过期
                return#返回
            帧={'v':检查器协议版本,'t':'source/open','source':源,'topics':['*',*网络主题]}#打开帧
            套接字.send(json.dumps(帧,ensure_ascii=False))#发送
        def 消息(事件):#消息
            """解析并分发入站帧。"""
            数据=事件 if isinstance(事件,str) else getattr(事件,'data',None)#文本
            if 自身.套接字 is not 套接字 or not isinstance(数据,str):#过期或非文本
                return#返回
            try:#解析分发
                if len(数据.encode('utf-8'))>取引导(自身.引导,'maxFrameBytes'):#超限
                    raise Exception(f'inspector protocol: Worker frame exceeds {取引导(自身.引导,"maxFrameBytes")} bytes')#拒绝
                值=json.loads(数据)#解析JSON
                if 自身.查询实例.接收(值):#RPC已消费
                    return#结束
                帧=解析工作者源帧(值)#校验源帧
                if 帧['t']!='source/rejected' and (帧.get('sourceId')!=自身.领域源.sourceId or 帧.get('generation')!=代数):#身份
                    return#不匹配
                自身._分发(套接字,源,代数,帧)#分发
            except Exception as 错误:#畸形帧
                print(f'[inspector] invalid Worker control frame: {错误}')#记录
                套接字.close(1008,'invalid Worker control frame')#关闭
        def 关闭(_事件=None):#关闭
            """调度重连。"""
            if 自身.套接字 is not 套接字 or 自身.已关闭:#过期或永久关闭
                return#返回
            自身.套接字=None#清空
            自身.已接受=False#未接受
            自身.发布器实例.断开(套接字)#断开发布器
            自身.控制台.重置()#重置Console
            自身.取消全部运行时请求()#取消请求
            自身.运行时.重置()#重置Runtime
            自身.查询实例.断开('Inspector Client source disconnected')#断开查询
            自身.生命周期.重连(自身.连接)#调度重连
        if hasattr(套接字,'addEventListener'):#浏览器风格
            def 忽略错误(_事件=None):#错误
                """close 拥有重连。"""
                return#空
            套接字.addEventListener('open',打开)#打开
            套接字.addEventListener('message',消息)#消息
            套接字.addEventListener('close',关闭)#关闭
            套接字.addEventListener('error',忽略错误)#错误由close处理
        else:#可调用钩子
            套接字.on('open',打开)#打开
            套接字.on('message',消息)#消息
            套接字.on('close',关闭)#关闭

    def _分发(自身,套接字,源,代数,帧):#分发处理器表
        """绑定帧族处理器。"""
        class _处理器:#帧处理器
            def 接纳(内,_帧):#接受
                """接受。"""
                自身.已接受=True#置位
                自身.生命周期.已连接()#已连接
                自身.查询实例.接通套接字(源,套接字)#接通查询
                自身.发布器实例.接受(套接字)#接受发布
            def 确认(内,_帧):#确认空操作
                """确认空操作。"""
                return#空
            def 重快照(内,_帧):#重快照
                """重快照。"""
                自身.发布器实例.替换(套接字)#替换
            def 拒绝(内,拒绝帧):#拒绝
                """拒绝。"""
                print(f'[inspector] Client source rejected: {拒绝帧.get("message")}')#记录
                套接字.close(1008,'source rejected')#关闭
            def 运行时(内,请求):#Runtime请求
                """Runtime请求。"""
                try:#执行
                    自身.执行运行时(套接字,代数,请求)#执行
                except Exception as 错误:#失败
                    print(f'[inspector] Client Runtime transport failed: {错误}')#记录
                    套接字.close(1011,'Client Runtime transport failed')#关闭
            def 运行时取消(内,取消):#取消
                """取消。"""
                自身.取消运行时(取消['sessionId'],取消['requestId'])#取消
            def 运行时确认(内,确认):#确认
                """确认。"""
                自身.确认运行时(确认['sessionId'],确认['requestId'])#确认
            def 运行时关闭(内,关闭帧):#会话关闭
                """会话关闭。"""
                自身.取消运行时会话(关闭帧['sessionId'])#取消会话请求
                自身.控制台.禁用(关闭帧['sessionId'])#禁用Console
                自身.运行时.关闭会话(关闭帧['sessionId'])#关闭Runtime会话
            def 控制台启用(内,启用):#启用Console
                """启用。"""
                自身.控制台.启用(启用['sessionId'])#启用
            def 控制台禁用(内,禁用):#禁用Console
                """禁用。"""
                自身.控制台.禁用(禁用['sessionId'])#禁用
            def 源(内,请求):#Sources请求
                """Sources。"""
                try:#执行
                    自身.执行源请求(套接字,代数,请求)#执行
                except Exception as 错误:#失败
                    print(f'[inspector] Client Sources transport failed: {错误}')#记录
                    套接字.close(1011,'Client Sources transport failed')#关闭
            def 源关闭(内,_帧):#Sources会话关闭空操作
                """Sources会话关闭空操作。"""
                return#空
        分发桥帧(帧,_处理器())#分发

    def 执行运行时(自身,套接字,代数,帧):#执行Runtime请求
        """执行一次 Runtime 请求并回写响应。"""
        控制器=_中止控制器()#中止
        操作={'controller':控制器,'sessionId':帧['sessionId']}#操作记录
        自身.运行时请求[帧['requestId']]=操作#登记
        响应=自身.运行时.执行(帧,控制器.signal,True)#执行
        if 自身.运行时请求.get(帧['requestId']) is not 操作:#已取消
            return#结束
        if 自身.已关闭 or 自身.套接字 is not 套接字 or 自身.代数!=代数 or getattr(套接字,'readyState',1)!=1:#过期
            自身.取消运行时(帧['sessionId'],帧['requestId'])#清理
            return#结束
        套接字.send(json.dumps(响应,ensure_ascii=False))#发送响应

    def 确认运行时(自身,会话标识,请求标识):#确认Runtime
        """确认 Runtime 响应。"""
        操作=自身.运行时请求.get(请求标识)#查找
        if 操作 is None or 操作['sessionId']!=会话标识:#不匹配
            return#返回
        del 自身.运行时请求[请求标识]#移除
        自身.运行时.确认(会话标识,请求标识)#通知执行器

    def 取消运行时(自身,会话标识,请求标识):#取消Runtime
        """取消 Runtime 请求。"""
        操作=自身.运行时请求.get(请求标识)#查找
        if 操作 is None or 操作['sessionId']!=会话标识:#不匹配
            return#返回
        del 自身.运行时请求[请求标识]#移除
        操作['controller'].abort()#中止
        自身.运行时.取消(会话标识,请求标识)#通知执行器

    def 取消运行时会话(自身,会话标识):#取消会话全部请求
        """取消某会话全部请求。"""
        for 请求标识,操作 in list(自身.运行时请求.items()):#遍历
            if 操作['sessionId']!=会话标识:#跳过
                continue#继续
            操作['controller'].abort()#中止
            自身.运行时.取消(会话标识,请求标识)#通知
            del 自身.运行时请求[请求标识]#移除

    def 取消全部运行时请求(自身):#取消全部请求
        """取消全部请求。"""
        for 请求标识,操作 in list(自身.运行时请求.items()):#遍历
            操作['controller'].abort()#中止
            自身.运行时.取消(操作['sessionId'],请求标识)#通知
        自身.运行时请求.clear()#清空

    def 执行源请求(自身,套接字,代数,帧):#执行Sources请求
        """执行 Sources 请求并回写响应。"""
        try:#执行目录
            if 自身.源目录 is None:#无目录
                raise 客户端源目录错误('invalid-request','Client source catalog is unavailable')#拒绝
            结果封装={'ok':True,'result':自身.源目录.执行(帧['command'],取引导(自身.引导,'maxClientSourceBytes'))}#成功
        except Exception as 错误:#失败
            码=错误.code if isinstance(错误,客户端源目录错误) else 'internal-error'#码
            结果封装={'ok':False,'error':{'code':码,'message':渲染错误(错误)[:2048]}}#错误结果
        响应={'v':检查器协议版本,'t':'client-sources/response','sourceId':自身.领域源.sourceId,'generation':代数,'sessionId':帧['sessionId'],'requestId':帧['requestId'],'outcome':结果封装}#响应帧
        if not 是否json值(响应) or json字节长度(响应)>取引导(自身.引导,'maxFrameBytes'):#超限
            响应={**响应,'outcome':{'ok':False,'error':{'code':'result-too-large','message':'Client source result exceeds the source-frame byte limit'}}}#改写
        if 自身.已关闭 or 自身.套接字 is not 套接字 or 自身.代数!=代数 or getattr(套接字,'readyState',1)!=1:#过期
            return#返回
        套接字.send(json.dumps(响应,ensure_ascii=False))#发送
