"""页面侧 postMessage 隧道半端。
将类 fetch 调用转成 `req` 帧，并从 worker 的 `res` /
`res-head`+`res-chunk`+`res-end` 帧重建 Response，
使启动载荷、包传输、ApiClient、Typert RPC 等消费方都只说普通 HTTP。

对齐上游 `webworker-runtime/src/client/client.ts`。公开面仅中文名。
"""
import base64 as _基64#Base64编码
import re#源映射尾注

__all__=['工作线程隧道']#仅中文公开名

拒绝状态=500#拒绝状态门槛
源映射尾注=re.compile(r'//# sourceMappingURL=([^\r\n]+)\s*$')#源映射尾注正则
基64分块字节=32*1024#Base64分块字节数
空体状态={101,204,205,304}#空体状态码

def 文本转基64(值):#文本转Base64
    """将 UTF-8 文本编码为内联 data URL 用的 Base64，避免调用栈级展开。"""
    字节=值.encode('utf-8')#编码为字节
    return _基64.b64encode(字节).decode('ascii')#Base64编码

def 本地化源映射(源,束网址,拉取):#本地化源映射
    """将隧道专用 map 引用替换为自包含的 Base64 data URL。"""
    匹配=源映射尾注.search(源)#匹配尾注
    if 匹配 is None:#无映射则原样返回
        return 源#原样
    try:#尝试拉取映射
        响应=拉取(匹配.group(1))#请求映射文件
        成功=响应.get('ok') if isinstance(响应,dict) else getattr(响应,'ok',False)#是否成功
        if not 成功:#失败则剥掉尾注
            return 源映射尾注.sub('',源)#剥掉
        取text=响应.get('text') if isinstance(响应,dict) else getattr(响应,'text',None)#text面
        正文=取text() if callable(取text) else str(响应)#映射正文
        数据网址=f'data:application/json;charset=utf-8;base64,{文本转基64(正文)}'#内联data URL
        return 源映射尾注.sub(f'//# sourceMappingURL={数据网址}',源)#替换为data URL
    except Exception:#传输失败兜底
        return 源映射尾注.sub('',源)#剥掉尾注

def 转正文缓冲(正文):#请求体转缓冲
    """将 RequestInit 体规范化为可转移的字节。"""
    if 正文 is None:#无体
        return None#无体
    if isinstance(正文,str):#字符串体
        return 正文.encode('utf-8')#编码
    if isinstance(正文,(bytes,bytearray,memoryview)):#已是缓冲
        return bytes(正文)#规范字节
    raise Exception(f'web-preview tunnel: unsupported request body {type(正文)}')#不支持的体

class 隧道逻辑流错误(Exception):#隧道逻辑流错误
    """跨独立打包的 Client 代码携带流语义的错误。"""

    def __init__(自身,失败,原因=None):#构造错误
        """按失败种类填充远程流失败标记。"""
        super().__init__(失败.get('message') if isinstance(失败,dict) else str(失败))#基类
        自身.name='TunnelLogicalStreamError'#错误名
        if isinstance(失败,dict) and 失败.get('kind')=='remote':#远程失败
            自身.dshRemoteStreamFailure={'kind':'remote','code':失败.get('code'),'details':失败.get('details')}#远程标记
        else:#载体失败
            自身.dshRemoteStreamFailure={'kind':'carrier'}#载体标记
        if 原因 is not None:#带cause
            自身.__cause__=原因#cause

class 逻辑流入箱:#逻辑流入箱
    """逻辑流帧入箱：推入、失败、取下一帧。"""

    def __init__(自身):#构造
        """空队列。"""
        自身._帧们=[]#待取帧队列
        自身._唤醒=None#等待唤醒回调
        自身._已失败=False#是否已失败
        自身._失败=None#失败原因

    def 推入(自身,帧):#推入一帧
        """入队并唤醒等待者。"""
        if 自身._已失败:#已失败则忽略
            return#忽略
        自身._帧们.append(帧)#入队
        if 自身._唤醒 is not None:#有等待者
            唤醒=自身._唤醒#取回调
            自身._唤醒=None#清空
            唤醒()#唤醒

    def 失败(自身,原因):#标记失败
        """标记失败并清空队列。"""
        if 自身._已失败:#已失败则忽略
            return#忽略
        自身._已失败=True#置失败
        自身._失败=原因#记录原因
        自身._帧们.clear()#清空队列
        if 自身._唤醒 is not None:#有等待者
            唤醒=自身._唤醒#取回调
            自身._唤醒=None#清空
            唤醒()#唤醒

    def 下一帧(自身):#取下一帧
        """取下一帧；队列空且已失败则抛出。"""
        if len(自身._帧们)==0:#队列空
            if 自身._已失败:#失败则抛出
                raise 自身._失败#抛出
            raise Exception('web-preview tunnel: logical stream inbox is empty; host must pump frames')#需宿主泵帧
        return 自身._帧们.pop(0)#取出队首

class 工作线程隧道:#Worker隧道
    """隧道的页面半端：在 postMessage 上提供一个类 fetch 面。"""

    def __init__(自身,工作线程):#构造隧道
        """附着到已启动的 worker 并开始消费响应帧。"""
        自身._工作线程=工作线程#保存worker
        自身._下一号=1#下一请求号
        自身._一元={}#一元请求挂起表 id->{resolve,reject}
        自身._体流={}#体流控制器表
        自身._逻辑流={}#逻辑流入箱表
        自身._进行中={}#进行中请求描述
        自身._释放们={}#中止释放表
        def 收消息(事件):#监听消息
            """分发响应帧。"""
            数据=事件.get('data') if isinstance(事件,dict) else getattr(事件,'data',事件)#载荷
            自身._接收(数据)#分发帧
        def 收错误(事件):#监听worker错误
            """拒绝全部挂起并清空表。"""
            消息=事件.get('message') if isinstance(事件,dict) else getattr(事件,'message',str(事件))#错误消息
            原因=Exception(f'web-preview tunnel: worker failed: {消息}')#错误原因
            for 标识 in list(自身._进行中.keys()):#逐条告警
                自身._告警拒绝(标识,f'worker failed: {消息}')#告警
            自身._进行中.clear()#清空进行中
            for 挂起 in list(自身._一元.values()):#拒绝一元
                挂起['reject'](原因)#拒绝
            自身._一元.clear()#清空一元表
            for 控制器 in list(自身._体流.values()):#体流出错
                出错=控制器.get('error') if isinstance(控制器,dict) else getattr(控制器,'error',None)#error面
                if callable(出错):#可调用
                    出错(原因)#出错
            自身._体流.clear()#清空体流表
            失败=隧道逻辑流错误({'kind':'carrier','message':f'web-preview tunnel: worker failed: {消息}'},原因)#逻辑流载体失败
            for 入箱 in list(自身._逻辑流.values()):#入箱失败
                入箱.失败(失败)#失败
            自身._逻辑流.clear()#清空逻辑流表
            for 释放 in list(自身._释放们.values()):#释放监听
                释放()#释放
            自身._释放们.clear()#清空释放表
        if hasattr(工作线程,'addEventListener'):#有监听API
            工作线程.addEventListener('message',收消息)#message监听
            工作线程.addEventListener('error',收错误)#error监听

    def 初始化(自身,镜像,覆盖层=None):#初始化隧道
        """打开隧道：worker 从此帧组装其宿主。"""
        if 覆盖层 is None:#缺省
            覆盖层=[]#空
        自身._工作线程.postMessage({'t':'init','image':镜像,'overlays':list(覆盖层)})#发送init帧

    def 拉取(自身,输入,初始化=None):#隧道fetch
        """类 fetch 入口：一请求帧，一 Response（worker 流式时则流式）。"""
        if 初始化 is None:#缺省
            初始化={}#空
        信号=初始化.get('signal')#中止信号
        if 信号 is not None and getattr(信号,'aborted',False) is True:#已中止则抛
            raise Exception('The operation was aborted.')#AbortError
        标识=自身._下一号#分配请求号
        自身._下一号+=1#递增
        正文=初始化.get('body')#请求体
        帧={'t':'req','id':标识,'method':初始化.get('method') or 'GET','url':str(输入),#组装请求帧
            'headers':dict(初始化.get('headers') or {})}#请求头
        if 正文 is not None:#有体
            帧['body']=转正文缓冲(正文)#附缓冲
        结果盒={'response':None,'error':None}#挂起结果
        def 兑现(响应):#成功回调
            """记下响应。"""
            结果盒['response']=响应#响应
        def 拒绝(原因):#失败回调
            """记下错误。"""
            结果盒['error']=原因#错误
        自身._一元[标识]={'resolve':兑现,'reject':拒绝}#登记一元
        自身._进行中[标识]=f"{帧['method']} {帧['url']}"#记录进行中描述
        自身._工作线程.postMessage(帧)#发送请求帧
        if 结果盒['error'] is not None:#同步失败
            raise 结果盒['error']#抛出
        return 结果盒['response']#返回结算结果（宿主泵帧后）

    def 打开(自身,端点,载荷,信号):#打开逻辑流
        """在 worker 本地载体上打开一条已解码的 Gateway Remote 流。"""
        if getattr(信号,'aborted',False):#已中止则抛
            raise Exception('The operation was aborted.')#AbortError
        标识=自身._下一号#分配流号
        自身._下一号+=1#递增
        入箱=逻辑流入箱()#新建入箱
        已打开=False#是否已打开
        终态=False#是否已终态
        def 中止时():#中止时失败入箱
            """入箱失败。"""
            入箱.失败(getattr(信号,'reason',Exception('aborted')))#失败
        自身._逻辑流[标识]=入箱#登记入箱
        自身._进行中[标识]=f'STREAM {端点}'#记录进行中
        try:#流生命周期
            帧={'t':'stream-open','id':标识,'endpoint':端点,'payload':载荷}#打开帧
            try:#尝试postMessage
                自身._工作线程.postMessage(帧)#发送打开帧
                已打开=True#标记已打开
            except Exception as 原因:#发送失败
                raise 隧道逻辑流错误({'kind':'carrier','message':f'web-preview tunnel: failed to open Remote stream {端点}'},原因)#抛载体错误
            while True:#消费入箱
                响应=入箱.下一帧()#取下一帧
                if getattr(信号,'aborted',False):#检查中止
                    raise Exception('The operation was aborted.')#AbortError
                if 响应.get('t')=='stream-item':#数据项
                    yield 响应.get('value')#产出值
                    continue#继续取
                终态=True#进入终态
                if 响应.get('t')=='stream-error':#错误则抛
                    raise 隧道逻辑流错误(响应['failure'])#抛错
                return#正常结束
        finally:#清理
            自身._逻辑流.pop(标识,None)#删除入箱
            自身._进行中.pop(标识,None)#删除进行中
            if 已打开 and not 终态:#未终态则中止worker
                自身._中止worker操作(标识)#中止

    def boot载荷(自身):#获取启动载荷
        """读取 pre-cordis 启动载荷（注入表）。"""
        响应=自身.拉取('/__boot__')#请求引导路由
        成功=响应.get('ok') if isinstance(响应,dict) else getattr(响应,'ok',True)#是否成功
        if not 成功:#非成功
            状态=响应.get('status') if isinstance(响应,dict) else getattr(响应,'status','?')#状态
            取text=响应.get('text') if isinstance(响应,dict) else getattr(响应,'text',lambda: '')#text
            正文=取text() if callable(取text) else ''#正文
            raise Exception(f'web-preview tunnel: boot payload failed with HTTP {状态}: {正文}')#抛错
        取json=响应.get('json') if isinstance(响应,dict) else getattr(响应,'json',None)#json面
        if callable(取json):#有json
            return 取json()#解析为载荷
        return 响应#已是载荷

    def 加载束(自身,网址):#加载客户端包
        """经隧道取一个客户端包并以经典脚本执行。"""
        响应=自身.拉取(网址)#经隧道拉取
        成功=响应.get('ok') if isinstance(响应,dict) else getattr(响应,'ok',True)#是否成功
        if not 成功:#非成功
            状态=响应.get('status') if isinstance(响应,dict) else getattr(响应,'status','?')#状态
            raise Exception(f'web-preview tunnel: bundle {网址} failed with HTTP {状态}')#抛错
        取text=响应.get('text') if isinstance(响应,dict) else getattr(响应,'text',lambda: '')#text
        源文本=取text() if callable(取text) else str(响应)#源文本
        源=本地化源映射(源文本,网址,自身.拉取)#本地化源映射
        全局=globals()#全局
        文档=全局.get('document')#document
        if 文档 is None:#无document则仅返回源
            return 源#返回源供宿主执行
        #上游用blob URL+script标签；此处执行注入由宿主document承担。
        return 源#返回源

    def _中止worker操作(自身,标识):#中止worker操作
        """尽力取消：已失败的 worker 反正收不到帧。"""
        try:#尽力发送
            自身._工作线程.postMessage({'t':'abort','id':标识})#发送中止
        except Exception:#发送失败忽略
            pass#忽略

    def _告警拒绝(自身,标识,结果):#告警拒绝
        """在页面控制台报告拒绝。"""
        描述=自身._进行中.get(标识,'(unknown request)')#描述
        print(f'web-preview tunnel: request {标识} {描述} → {结果}')#控制台警告

    def _接收(自身,帧):#接收响应帧
        """按帧类型分发。"""
        种类=帧.get('t') if isinstance(帧,dict) else None#帧类型
        if 种类=='res':#一元完整响应
            挂起=自身._一元.get(帧['id'])#取挂起
            if 挂起 is None:#无挂起则忽略
                return#忽略
            if 帧.get('status',0)>=拒绝状态:#达到拒绝门槛
                文案=帧.get('message')#消息
                自身._告警拒绝(帧['id'],f"HTTP {帧.get('status')}"+(f': {文案}' if 文案 else ''))#告警
            自身._一元.pop(帧['id'],None)#删一元
            自身._进行中.pop(帧['id'],None)#删进行中
            正文=None if 帧.get('status') in 空体状态 else 帧.get('body',帧.get('message'))#体
            挂起['resolve']({'ok':帧.get('status',0)<400,'status':帧.get('status'),'headers':帧.get('headers') or {},'body':正文,#兑现Response面
                'json':(lambda b=正文: __import__('json').loads(b.decode('utf-8') if isinstance(b,(bytes,bytearray)) else b) if b is not None else None),#json
                'text':(lambda b=正文: b.decode('utf-8') if isinstance(b,(bytes,bytearray)) else (b or '')),#text
            })#兑现结束
            return#结束
        if 种类=='res-head':#流式响应头
            挂起=自身._一元.get(帧['id'])#取挂起
            if 挂起 is None:#无挂起则忽略
                return#忽略
            自身._一元.pop(帧['id'],None)#删一元
            控制器={'chunks':[],'closed':False,'error':None}#体流控制器
            自身._体流[帧['id']]=控制器#存控制器
            挂起['resolve']({'ok':帧.get('status',0)<400,'status':帧.get('status'),'headers':帧.get('headers') or {},'body':控制器,'stream':True})#兑现流式
            return#结束
        if 种类=='res-chunk':#流式分块
            控制器=自身._体流.get(帧['id'])#取控制器
            if 控制器 is not None:#有控制器
                控制器['chunks'].append(bytes(帧['chunk']))#入队分块
            return#结束
        if 种类=='res-end':#流式结束
            控制器=自身._体流.pop(帧['id'],None)#取控制器
            if 控制器 is None:#无则忽略
                return#忽略
            自身._进行中.pop(帧['id'],None)#删进行中
            自身._释放们.pop(帧['id'],None)#释放监听
            控制器['closed']=True#关闭流
            return#结束
        if 种类=='res-err':#响应错误
            原因=Exception(f"web-preview tunnel: {帧.get('message')}")#错误原因
            自身._告警拒绝(帧['id'],f"res-err: {帧.get('message')}")#告警
            自身._进行中.pop(帧['id'],None)#删进行中
            挂起=自身._一元.pop(帧['id'],None)#取一元挂起
            if 挂起 is not None:#头未结算
                挂起['reject'](原因)#拒绝
                return#结束
            控制器=自身._体流.pop(帧['id'],None)#取体流
            if 控制器 is None:#无则忽略
                return#忽略
            自身._释放们.pop(帧['id'],None)#释放监听
            控制器['error']=原因#体流出错
            return#结束
        if 种类 in ('stream-item','stream-end','stream-error'):#逻辑流帧
            入箱=自身._逻辑流.get(帧['id'])#取入箱
            if 入箱 is not None:#有入箱
                入箱.推入(帧)#推入
            return#结束
        raise Exception(f'web-preview tunnel: unknown frame {帧!r}')#未知帧
