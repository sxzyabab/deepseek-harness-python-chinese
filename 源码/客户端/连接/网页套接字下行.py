"""两条服务端到浏览器事件流的宿主侧 WebSocket 载体。

对齐上游 `connection/src/websocket-downlink.ts`。公开面仅中文名。客户端发来的消息是协议违规：上行仍走 HTTP。

完整帧泵依赖宿主 apiproxy 事件流与 WebSocket 协商实现；本模块迁入拒绝升级与下行拥有面，泵送在网关事件面可用时挂上。
"""
import json,uuid#JSON 与随机 id

__all__=['拒绝网页套接字升级','网页套接字下行']#仅中文公开名

def 拒绝网页套接字升级(套接字):#写 403 并结束套接字
    """在协议协商之前拒绝不受信任的升级。"""
    正文='\r\n'.join([#HTTP/1.1 错误响应
        'HTTP/1.1 403 Forbidden',#状态
        'Connection: close',#关连接
        'Content-Type: text/plain; charset=utf-8',#纯文本
        'Content-Length: 9',#forbidden 九字节
        '',#头与正文空行
        'forbidden',#正文
    ])#CRLF 拼接
    if hasattr(套接字,'end'):#Node Duplex 形
        套接字.end(正文)#写出并结束
        return#完
    if hasattr(套接字,'sendall'):#裸套接字
        套接字.sendall(正文.encode('utf-8'))#写出
        套接字.close()#关
        return#完
    if hasattr(套接字,'write'):#类文件
        套接字.write(正文.encode('utf-8') if isinstance(正文,str) else 正文)#写出
        if hasattr(套接字,'close'):#可关
            套接字.close()#关

class 网页套接字下行:#mux 与 host 两条下行
    """拥有连接插件两条下行的 WebSocket 协商与帧泵送。"""

    def __init__(自身,网关):#保存网关
        """@param 网关 - 提供带类型事件流的宿主 API。"""
        自身.网关=网关#ApiProxy
        自身.泵集=set()#进行中的帧泵
        自身.客户集=set()#打开的套接字

    def handleMux(自身,请求,套接字,头):#复用事件下行
        """升级一个套接字并泵送 mux 流直到任一侧关闭。"""
        自身._升级(请求,套接字,头,'mux')#打开 mux 流

    def handleHost(自身,请求,套接字,头):#宿主事件下行
        """升级一个套接字并泵送宿主流直到任一侧关闭。"""
        自身._升级(请求,套接字,头,'host')#打开 host 流

    def close(自身):#拆除全部下行
        """终止所拥有的套接字，并等待帧泵结束。"""
        for 套接字 in list(自身.客户集):#打开的套接字
            if hasattr(套接字,'terminate'):#可立刻拆
                套接字.terminate()#拆
            elif hasattr(套接字,'close'):#普通关
                套接字.close()#关
        自身.客户集.clear()#清空
        自身.泵集.clear()#清空泵

    def _升级(自身,请求,套接字,头,种类):#把 HTTP 升级变成一条帧泵
        """协商完成后泵帧。"""
        事件面=getattr(自身.网关,'events',None)#事件面
        if 事件面 is None:#网关无事件面
            拒绝网页套接字升级(套接字)#无法泵则拒绝
            return#完
        打开=getattr(事件面,种类,None)#mux 或 host
        if not callable(打开):#无该方法
            拒绝网页套接字升级(套接字)#拒绝
            return#完
        自身.客户集.add(套接字)#登记
        中止器={'aborted':False}#套接字结束则取消
        def 关闭(_事件=None):#对端或本端关闭
            """标中止。"""
            中止器['aborted']=True#中止
            自身.客户集.discard(套接字)#摘掉
        if hasattr(套接字,'once'):#事件面
            套接字.once('close',关闭)#关闭
            套接字.once('error',关闭)#出错
            def 违例(_数据=None):#客户端不该往下行发消息
                """政策违规，关掉。"""
                if hasattr(套接字,'close'):#可关
                    套接字.close(1008,'downlink only')#关掉
            套接字.once('message',违例)#违例
        rpc标识=str(uuid.uuid4())#本条流的关联 id
        try:#打开事件流
            帧们=打开({'rpcId':rpc标识,'payload':{}},中止器)#按信号打开
        except Exception:#打开失败
            拒绝网页套接字升级(套接字)#拒绝
            return#完
        泵={'frames':帧们,'abort':中止器}#泵状态
        自身.泵集.add(id(泵))#登记
        if hasattr(帧们,'__iter__'):#可迭代
            try:#泵帧
                for 帧 in 帧们:#逐帧
                    if 中止器['aborted']:#已中止
                        break#停
                    信封={#服务端请求信封
                        'type':'server-request',#判别标签
                        'rpcId':帧.get('rpcId') if isinstance(帧,dict) else rpc标识,#关联 id
                        'method':(帧.get('payload') or {}).get('type') if isinstance(帧,dict) else None,#以载荷 type 当方法名
                        'payload':帧.get('payload') if isinstance(帧,dict) else 帧,#事件载荷
                    }#结束信封
                    文本=json.dumps(信封,ensure_ascii=False)#JSON 文本
                    if hasattr(套接字,'send'):#ws 形
                        套接字.send(文本)#写出
                    elif hasattr(套接字,'write'):#流形
                        套接字.write(文本.encode('utf-8'))#写出
            except Exception:#源出错
                pass#泵结束
            finally:#无论成败
                中止器['aborted']=True#取消
                自身.泵集.discard(id(泵))#摘掉
                自身.客户集.discard(套接字)#摘掉
                if hasattr(套接字,'close'):#仍开着则关
                    套接字.close()#关
