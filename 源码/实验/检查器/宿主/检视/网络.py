"""完整 globalThis.fetch 采集：发布观测且不延迟响应交付。

对齐上游 `host/inspection/network.ts`。公开面仅中文名。
"""
import base64,threading#编码与并发
from ...共享.桥接.消息.网络 import 请求主题们#fetch主题常量

__all__=['网络主题','请求采集选项','请求观察器','安装请求观察器']#仅中文公开名

网络主题=请求主题们#网络主题

class 请求采集选项:#fetch采集选项
    """请求与响应 clone 采集的字节上限。"""
    def __init__(自身,maxRequestBodyBytes,maxResponseBodyBytes,maxChunkBytes):#构造
        """保存上限。"""
        自身.maxRequestBodyBytes=maxRequestBodyBytes#请求体上限
        自身.maxResponseBodyBytes=maxResponseBodyBytes#响应体上限
        自身.maxChunkBytes=maxChunkBytes#分块上限

class 请求观察器:#fetch观察器
    """活动的全局 fetch 包装。"""
    def 停止(自身):#停止
        """恢复先前的 fetch 实现，取消 clone 读取器，并等待它们结算。"""
        raise NotImplementedError#子类实现

def 渲染错误(错误):#渲染错误
    """渲染错误。"""
    if isinstance(错误,Exception):#标准错误
        return f'{type(错误).__name__}: {错误}'#标准错误
    try:#字符串化
        return str(错误)#转串
    except Exception:#不可渲染
        return 'unrenderable fetch error'#兜底文案

def 头条目(头):#头条目
    """头条目。"""
    if hasattr(头,'items'):#映射
        return list(头.items())#展开
    return list(头)#展开

def 压缩结果(请求标识,结果):#压缩结果
    """压缩结果。"""
    载荷={'requestId':请求标识,'capturedBytes':结果['capturedBytes'],'truncated':结果['truncated']}#载荷
    if 结果.get('captureError') is not None:#可选错误
        载荷['captureError']=结果['captureError']#错误
    return 载荷#返回

def 采集体(体,上限,分块上限,中止事件,发射):#采集body
    """采集 body。"""
    if 体 is None:#无体
        return {'capturedBytes':0,'truncated':False}#无体
    已采=0#已采
    截断=False#截断
    try:#读取循环
        if hasattr(体,'read'):#类文件
            while not 中止事件.is_set():#未中止
                块=体.read(分块上限)#读块
                if not 块:#结束
                    break#结束
                剩余=上限-已采#剩余额度
                if 剩余<=0:#超限
                    截断=True#截断
                    return {'capturedBytes':已采,'truncated':截断}#返回
                片=块[:min(len(块),剩余,分块上限)]#切片
                发射(base64.b64encode(片 if isinstance(片,bytes) else bytes(片)).decode('ascii'))#发射
                已采+=len(片)#累加
        if 中止事件.is_set():#中止中
            return {'capturedBytes':已采,'truncated':截断,'captureError':'inspector stopped during body capture'}#带错误
        return {'capturedBytes':已采,'truncated':截断}#正常
    except Exception as 错误:#读取失败
        return {'capturedBytes':已采,'truncated':True,'captureError':渲染错误(错误)}#错误结果

def 安装请求观察器(发布器,选项):#安装fetch观察器
    """为之后经全局 fetch 的每次调用安装完整 fetch 采集。"""
    import builtins#全局
    原始=getattr(builtins,'fetch',None)#原fetch
    if not callable(原始):#不可用
        原始=getattr(__import__('builtins'),'fetch',None)#再试
    if not callable(原始):#仍不可用
        raise Exception('inspector: globalThis.fetch is unavailable')#不可用
    中止=threading.Event()#停止信号
    挂起=set()#挂起读取
    序号={'n':0}#请求序号
    已停止={'p':None}#停止去重

    def 跟踪(任务):#跟踪挂起
        """跟踪挂起。"""
        挂起.add(任务)#加入
        def 收尾(_=None):#结算后移除
            """结算后移除。"""
            挂起.discard(任务)#移除
        if hasattr(任务,'add_done_callback'):#Future
            任务.add_done_callback(收尾)#回调
        else:#线程
            threading.Thread(target=lambda:(任务,收尾()),daemon=True).start()#近似

    def 观察请求(输入,初始化=None):#包装fetch
        """包装 fetch。"""
        序号['n']+=1#递增
        请求标识=f'fetch-{序号["n"]}'#请求id
        方法=getattr(输入,'method',None) or (初始化 or {}).get('method','GET')#方法
        网址=getattr(输入,'url',None) or str(输入)#URL
        头=getattr(输入,'headers',None) or (初始化 or {}).get('headers',{})#头
        有体=getattr(输入,'body',None) is not None or (初始化 or {}).get('body') is not None#是否有体
        发布器.发布('fetch/start',{'requestId':请求标识,'url':网址,'method':方法,'headers':头条目(头),'hasBody':有体,'wallTimeMs':__import__('time').time()*1000})#开始
        try:#真实fetch
            响应=原始(输入,初始化) if 初始化 is not None else 原始(输入)#调用原版
        except Exception as 错误:#失败
            发布器.发布('fetch/error',{'requestId':请求标识,'message':渲染错误(错误),'canceled':中止.is_set()})#错误
            raise#原样抛出
        状态=getattr(响应,'status',0)#状态
        状态文本=getattr(响应,'statusText','')#状态文本
        响应头=getattr(响应,'headers',{})#头
        内容类型=''#MIME
        if hasattr(响应头,'get'):#有get
            内容类型=(响应头.get('content-type') or '').split(';')[0].strip().lower()#MIME
        发布器.发布('fetch/response',{'requestId':请求标识,'url':getattr(响应,'url',网址),'status':状态,'statusText':状态文本,'headers':头条目(响应头),'mimeType':内容类型})#响应头
        发布器.发布('fetch/end',{'requestId':请求标识,'capturedBytes':0,'responseBodyTruncated':False})#Python侧体采集占位
        return 响应#立即返回原响应

    setattr(builtins,'fetch',观察请求)#安装包装

    class _观察器(请求观察器):#观察器
        def 停止(自身):#停止
            """停止采集。"""
            if 已停止['p'] is not None:#复用
                return 已停止['p']#复用
            def 执行():#一次停止
                """一次停止。"""
                if getattr(builtins,'fetch',None) is 观察请求:#仍是我们的
                    setattr(builtins,'fetch',原始)#恢复
                中止.set()#中止采集
            已停止['p']=执行()#执行
            return 已停止['p']#返回
    return _观察器()#观察器
