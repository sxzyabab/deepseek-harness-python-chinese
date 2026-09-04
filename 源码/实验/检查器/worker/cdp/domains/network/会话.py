"""在 Worker 拥有的规范化网络存储之上的 CDP Network 投影。"""
#对齐上游 worker/cdp/domains/network/session.ts

import base64#正文编码

__all__=['网络域']#仅中文公开名

class 网络域:#Network域
    """将已保留与实时网络观测投影为连接本地的 CDP 状态。"""
    def __init__(自身,存储):#构造
        """订阅存储。"""
        自身._存储=存储#网络存储
        自身._已启用=set()#已启用会话
        自身._流式请求={}#流式请求
        自身._待发开始={}#待发开始
        自身._请求类型={}#请求类型
        自身._取消订阅=存储.订阅(自身._接收)#订阅存储

    def 启用(自身,会话):#启用
        """为一个 DevTools 连接启用 Network，并回放已保留的生命周期事件。"""
        if 会话 in 自身._已启用:#已启用
            return#返回
        自身._已启用.add(会话)#加入
        自身._待发开始[id(会话)]={}#待发表
        自身._请求类型[id(会话)]={}#类型表
        for 事件 in 自身._存储.回放():#回放
            自身._发送(会话,事件)#回放

    def 禁用(自身,会话):#禁用
        """停止某个 DevTools 连接的 Network 事件。"""
        自身._已启用.discard(会话)#移除启用
        自身._流式请求.pop(id(会话),None)#清流式
        自身._待发开始.pop(id(会话),None)#清待发
        自身._请求类型.pop(id(会话),None)#清类型

    def 分离(自身,会话):#分离
        """忘记一个已关闭的 DevTools 连接。"""
        自身.禁用(会话)#禁用

    def 关闭(自身):#关闭
        """释放仓库订阅与全部连接本地状态。"""
        自身._取消订阅()#取消订阅
        自身._已启用.clear()#清空启用
        自身._流式请求.clear()#清空流式
        自身._待发开始.clear()#清空待发
        自身._请求类型.clear()#清空类型

    def 处理(自身,方法,参数,会话):#处理方法
        """处理一个 Worker 本地 Network 方法。"""
        if 方法=='Network.enable':#启用
            自身.启用(会话)#启用会话
            return {}#空结果
        if 方法=='Network.disable':#禁用
            自身.禁用(会话)#禁用会话
            return {}#空结果
        if 方法=='Network.getResponseBody':#取响应体
            正文=自身._存储.响应体(参数.get('requestId'))#正文
            结果={'body':base64.b64encode(正文['bytes']).decode('ascii'),'base64Encoded':True,'dshInspectorTruncated':正文['truncated']}#结果
            if 正文.get('captureError') is not None:#捕获错
                结果['dshInspectorCaptureError']=正文['captureError']#写入
            return 结果#返回
        if 方法=='Network.getRequestPostData':#取请求体
            正文=自身._存储.请求体(参数.get('requestId'))#正文
            结果={'postData':正文['bytes'].decode('utf-8','replace'),'dshInspectorTruncated':正文['truncated']}#结果
            if 正文.get('captureError') is not None:#捕获错
                结果['dshInspectorCaptureError']=正文['captureError']#写入
            return 结果#返回
        if 方法=='Network.streamResourceContent':#流式资源
            请求id=参数.get('requestId')#请求id
            正文=自身._存储.响应体(请求id)#正文
            if not isinstance(请求id,str):#类型
                raise ValueError('Network requestId must be a string')#类型
            if not 正文.get('complete'):#未完成
                集合=自身._流式请求.setdefault(id(会话),set())#流式集
                集合.add(请求id)#登记
            return {'bufferedData':base64.b64encode(正文['bytes']).decode('ascii')}#缓冲数据
        if 方法 in ('Network.setCacheDisabled','Network.setBypassServiceWorker','Network.setExtraHTTPHeaders','Network.clearBrowserCache','Network.clearBrowserCookies'):#空结果族
            return {}#空结果
        raise RuntimeError(f'unsupported Network method {方法}')#抛错

    def _接收(自身,事件):#接收存储事件
        """广播或清理逐出。"""
        if 事件['type']=='request-evicted':#逐出
            键=事件['requestKey']#键
            for 会话键,请求们 in list(自身._流式请求.items()):#扫流式
                请求们.discard(键)#删除键
                if not 请求们:#空则移除
                    del 自身._流式请求[会话键]#移除
            for 表 in 自身._待发开始.values():#清待发
                表.pop(键,None)#删除
            for 表 in 自身._请求类型.values():#清类型
                表.pop(键,None)#删除
            return#返回
        for 会话 in list(自身._已启用):#广播
            自身._发送(会话,事件)#发送

    def _发送(自身,会话,事件):#发送事件
        """按类型投影 CDP 事件。"""
        import time#时间
        时间戳=(事件.get('timestampMs',time.time()*1000)-getattr(time,'timeOrigin',0))/1000#相对秒占位
        类型=事件['type']#类型
        if 类型=='request-started':#开始
            自身._待发开始.get(id(会话),{})[事件['requestKey']]=事件#记待发
            return#返回
        if 类型=='response-received':#收到响应
            资源类型='EventSource' if 事件.get('mimeType')=='text/event-stream' else 'Fetch'#资源类型
            自身._发送请求开始(会话,事件['requestKey'],资源类型)#先发开始
            会话.发送事件('Network.responseReceived',{#响应事件
                'requestId':事件['requestId'],'loaderId':'dsh-inspector-loader','frameId':'dsh-inspector-host-frame',#身份
                'timestamp':时间戳,'type':资源类型,#类型
                'response':{#响应
                    'url':事件['url'],'status':事件['status'],'statusText':事件['statusText'],#状态
                    'headers':_cdp头(事件['headers']),'mimeType':事件['mimeType'],#头
                    'connectionReused':False,'connectionId':0,#连接
                    'encodedDataLength':-1 if 资源类型=='EventSource' else 0,'securityState':'neutral',#编码
                },#response结束
            })#sendEvent结束
            return#返回
        if 类型=='event-source-message':#SSE消息
            会话.发送事件('Network.eventSourceMessageReceived',{#SSE事件
                'requestId':事件['requestId'],'timestamp':时间戳,#时间戳
                'eventName':事件['eventName'],'eventId':事件['eventId'],'data':事件['data'],#数据
            })#sendEvent结束
            return#返回
        if 类型=='response-data':#响应数据
            参数={'requestId':事件['requestId'],'timestamp':时间戳,'dataLength':事件['byteLength'],'encodedDataLength':事件['byteLength']}#数据事件
            if 事件['requestKey'] in 自身._流式请求.get(id(会话),set()):#流式体
                参数['data']=事件['data']#写入
            会话.发送事件('Network.dataReceived',参数)#发送
            return#返回
        if 类型=='request-finished':#完成
            自身._发送请求开始(会话,事件['requestKey'],'Fetch')#补开始
            会话.发送事件('Network.loadingFinished',{#完成事件
                'requestId':事件['requestId'],'timestamp':时间戳,#时间戳
                'encodedDataLength':事件['encodedDataLength'],'dshInspectorTruncated':事件['truncated'],#截断
            })#sendEvent结束
            自身._停止请求(会话,事件['requestKey'])#停止跟踪
            return#返回
        if 类型=='request-failed':#失败
            自身._发送请求开始(会话,事件['requestKey'],'Fetch')#补开始
            资源类型=自身._请求类型.get(id(会话),{}).get(事件['requestKey'],'Fetch')#类型
            会话.发送事件('Network.loadingFailed',{#失败事件
                'requestId':事件['requestId'],'timestamp':时间戳,'type':资源类型,#类型
                'errorText':事件['errorText'],'canceled':事件['canceled'],#错误
            })#sendEvent结束
            自身._停止请求(会话,事件['requestKey'])#停止跟踪

    def _发送请求开始(自身,会话,请求键,资源类型):#发送请求开始
        """冲刷待发 requestWillBeSent。"""
        待发=自身._待发开始.get(id(会话))#待发表
        事件=None if 待发 is None else 待发.pop(请求键,None)#事件
        if 事件 is None:#无待发
            return#返回
        自身._请求类型.setdefault(id(会话),{})[请求键]=资源类型#记类型
        import time#时间
        会话.发送事件('Network.requestWillBeSent',{#将发请求
            'requestId':事件['requestId'],'loaderId':'dsh-inspector-loader','documentURL':'dsh://host',#身份
            'request':{'url':事件['url'],'method':事件['method'],'headers':_cdp头(事件['headers']),'hasPostData':事件['hasBody']},#请求
            'timestamp':(事件['timestampMs']-getattr(time,'timeOrigin',0))/1000,#相对秒
            'wallTime':事件['wallTimeMs']/1000,#墙上秒
            'initiator':{'type':'other'},'type':资源类型,#类型
        })#sendEvent结束

    def _停止请求(自身,会话,请求键):#停止请求跟踪
        """清理会话本地跟踪。"""
        流式=自身._流式请求.get(id(会话))#流式集
        if 流式 is not None:#有
            流式.discard(请求键)#删除
            if not 流式:#空则移除
                del 自身._流式请求[id(会话)]#移除
        表=自身._待发开始.get(id(会话))#待发
        if 表 is not None:#清待发
            表.pop(请求键,None)#删除
        类型表=自身._请求类型.get(id(会话))#类型
        if 类型表 is not None:#清类型
            类型表.pop(请求键,None)#删除

def _cdp头(条目们):#头转CDP
    """合并同名头。"""
    头={}#空对象
    for 名,值 in 条目们:#扫头
        头[名]=值 if 名 not in 头 else f'{头[名]}\n{值}'#合并同名
    return 头#返回
