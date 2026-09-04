"""Worker 拥有的规范化 fetch 观测与捕获正文仓库。"""
#对齐上游 worker/inspection/network-store.ts 段1

import base64,re,time#解码与时间

__all__=['网络存储']#仅中文公开名

抓取主题=frozenset([#FETCH_TOPICS 占位
    'fetch/start','fetch/request-body-chunk','fetch/request-body-end',#请求
    'fetch/response','fetch/response-body-chunk','fetch/end','fetch/error',#响应
])#主题结束

class 网络存储:#网络存储
    """与 CDP 连接状态无关的已校验 Network 观测存储。"""
    def __init__(自身,选项):#构造
        """保存选项。"""
        自身.选项=选项#选项
        自身.topics=set(抓取主题)#主题
        自身._请求={}#请求表
        自身._日志=[]#日志
        自身._已完成=[]#已完成键
        自身._监听=set()#监听
        自身._日志字节=0#日志字节

    def 替换(自身,源,记录们):#替换
        """先关旧再追加。"""
        自身.关闭(源,'source state replaced')#先关旧
        自身.追加(源,记录们)#再追加

    def 追加(自身,源,记录们):#追加
        """摄入主题匹配记录。"""
        for 记录 in 记录们:#扫记录
            if 记录.get('topic') not in 自身.topics:#非主题
                continue#跳过
            try:#摄入
                自身._摄入(源,记录)#摄入一条
            except Exception:#畸形载荷
                pass#畸形域载荷仅丢失该次观测

    def 关闭(自身,源,原因):#关闭源
        """未完成请求记失败。"""
        for 请求 in list(自身._请求.values()):#扫请求
            if 请求['sourceId']!=源['sourceId'] or 请求['completed']:#跳过
                continue#跳过
            请求['completed']=True#置完成
            自身._发布({#发布失败
                'type':'request-failed','requestKey':请求['key'],'requestId':请求['requestId'],#身份
                'timestampMs':time.time()*1000,'errorText':原因,'canceled':True,#取消
            })#publish结束
            自身._已完成.append(请求['key'])#记完成
        自身._强制保留()#强制保留

    def 回放(自身):#回放日志
        """读取保留的请求生命周期事件。"""
        return list(自身._日志)#日志

    def 订阅(自身,监听):#订阅
        """订阅实时请求变更与逐出。"""
        自身._监听.add(监听)#加入
        return lambda:自身._监听.discard(监听)#释放

    def 请求体(自身,请求id):#请求体
        """读取一个保留的请求体。"""
        请求=自身._按id取请求(请求id)#取请求
        return _组装正文(请求['requestBody'],请求['requestBodyTruncated'],请求.get('requestCaptureError'),请求['completed'])#组装

    def 响应体(自身,请求id):#响应体
        """在响应头到达后读取一个保留的响应体。"""
        请求=自身._按id取请求(请求id)#取请求
        if not 请求['responseSeen']:#未见响应
            raise RuntimeError('response headers have not arrived')#未见响应
        return _组装正文(请求['responseBody'],请求['responseBodyTruncated'],请求.get('responseCaptureError'),请求['completed'])#组装

    def 释放(自身):#释放
        """释放订阅者与全部保留请求数据。"""
        自身._监听.clear()#清监听
        自身._请求.clear()#清请求
        自身._日志.clear()#清日志
        自身._已完成.clear()#清完成
        自身._日志字节=0#清字节

    def _摄入(自身,源,记录):#摄入记录
        """按主题更新请求。"""
        载荷=_要求载荷(记录.get('payload'))#载荷
        本地id=_字符串字段(载荷,'requestId')#本地id
        键=f"{源['sourceId']}:{源['generation']}:{本地id}"#复合键
        时间戳=源.get('timeOriginMs',0)+记录.get('monotonicMs',0)#时间戳
        if 记录['topic']=='fetch/start':#开始
            if 键 in 自身._请求:#重复id
                raise RuntimeError('fetch observation reused an active request id')#抛错
            请求={#新请求
                'key':键,'requestId':键,'sourceId':源['sourceId'],#身份
                'requestBody':[],'responseBody':[],#体块
                'requestBodyBytes':0,'responseBodyBytes':0,#字节
                'requestBodyTruncated':False,'responseBodyTruncated':False,#截断
                'responseSeen':False,'completed':False,#状态
                'eventSourceParser':None,'nextEventSourceId':0,#SSE
            }#request结束
            自身._请求[键]=请求#登记
            自身._发布({#发布开始
                'type':'request-started','requestKey':键,'requestId':请求['requestId'],'timestampMs':时间戳,#身份
                'wallTimeMs':_数字字段(载荷,'wallTimeMs'),'url':_字符串字段(载荷,'url'),#URL
                'method':_字符串字段(载荷,'method'),'headers':_头字段(载荷,'headers'),#头
                'hasBody':_布尔字段(载荷,'hasBody'),#有体
            })#publish结束
            自身._强制保留()#保留
            return#返回
        请求=自身._请求.get(键)#取请求
        if 请求 is None:#未知
            return#返回
        自身._按主题继续(源,记录,载荷,键,请求,时间戳)#继续

    def _按主题继续(自身,源,记录,载荷,键,请求,时间戳):#按主题继续
        """处理非 start 主题。"""
        主题=记录['topic']#主题
        if 主题=='fetch/request-body-chunk':#请求体块
            自身._追加正文(请求,'request',_字符串字段(载荷,'data'))#追加
            return#返回
        if 主题=='fetch/request-body-end':#请求体结束
            请求['requestBodyTruncated']=请求['requestBodyTruncated'] or _布尔字段(载荷,'truncated')#截断
            捕获错=_可选字符串字段(载荷,'captureError')#捕获错
            if 捕获错 is not None:#写入
                请求['requestCaptureError']=捕获错#写入
            return#返回
        if 主题=='fetch/response':#响应头
            请求['responseSeen']=True#已见
            mime=_字符串字段(载荷,'mimeType').lower()#MIME
            请求['eventSourceParser']=[] if mime=='text/event-stream' else None#SSE占位缓冲
            自身._发布({#发布响应
                'type':'response-received','requestKey':键,'requestId':请求['requestId'],'timestampMs':时间戳,#身份
                'url':_字符串字段(载荷,'url'),'status':_数字字段(载荷,'status'),#状态
                'statusText':_字符串字段(载荷,'statusText'),'headers':_头字段(载荷,'headers'),'mimeType':mime,#MIME
            })#publish结束
            return#返回
        if 主题=='fetch/response-body-chunk':#响应体块
            数据=_字符串字段(载荷,'data')#数据
            字节=自身._追加正文(请求,'response',数据)#追加
            自身._发出({'type':'response-data','requestKey':键,'requestId':请求['requestId'],'timestampMs':时间戳,'data':数据,'byteLength':len(字节)})#实时数据
            return#返回
        if 主题=='fetch/end':#结束
            请求['responseBodyTruncated']=请求['responseBodyTruncated'] or _布尔字段(载荷,'responseBodyTruncated')#截断
            捕获错=_可选字符串字段(载荷,'responseCaptureError')#捕获错
            if 捕获错 is not None:#写入
                请求['responseCaptureError']=捕获错#写入
            自身._完成(请求,{#完成
                'type':'request-finished','requestKey':键,'requestId':请求['requestId'],'timestampMs':时间戳,#身份
                'encodedDataLength':请求['responseBodyBytes'],'truncated':请求['responseBodyTruncated'],#截断
            })#complete结束
            return#返回
        if 主题=='fetch/error':#错误
            if 请求['completed']:#已完成
                return#返回
            错误文本=_字符串字段(载荷,'message')#错误文本
            if 请求['responseSeen']:#已见响应
                请求['responseBodyTruncated']=True#截断
                请求['responseCaptureError']=错误文本#捕获错
            自身._完成(请求,{#完成失败
                'type':'request-failed','requestKey':键,'requestId':请求['requestId'],'timestampMs':时间戳,#身份
                'errorText':错误文本,'canceled':_布尔字段(载荷,'canceled'),#取消
            })#complete结束

    def _追加正文(自身,请求,侧,编码):#追加正文
        """解码并保留正文块。"""
        字节=_解码base64(编码)#解码
        自身._为新字节逐出已完成(len(字节),请求['key'])#为新字节腾空间
        可留=字节[:max(0,自身.选项['maxJournalBytes']-自身._日志字节)]#可保留
        if 侧=='request':#请求侧
            if 可留:#推块
                请求['requestBody'].append(可留)#推块
            请求['requestBodyBytes']+=len(可留)#累加
            请求['requestBodyTruncated']=请求['requestBodyTruncated'] or len(可留)<len(字节)#截断
        else:#响应侧
            if 可留:#推块
                请求['responseBody'].append(可留)#推块
            请求['responseBodyBytes']+=len(可留)#累加
            请求['responseBodyTruncated']=请求['responseBodyTruncated'] or len(可留)<len(字节)#截断
        自身._日志字节+=len(可留)#日志字节
        自身._强制保留()#保留
        return 字节#返回原字节

    def _完成(自身,请求,事件):#完成请求
        """幂等完成。"""
        if 请求['completed']:#幂等
            return#返回
        请求['completed']=True#置位
        自身._发布(事件)#发布
        自身._已完成.append(请求['key'])#记完成
        自身._强制保留()#保留

    def _发布(自身,事件):#发布到日志
        """入日志并发出。"""
        自身._日志.append(事件)#入日志
        自身._发出(事件)#发出

    def _发出(自身,事件):#发出事件
        """隔离监听。"""
        for 监听 in list(自身._监听):#扫监听
            try:#隔离
                监听(事件)#回调
            except Exception:#故障
                pass#一个展示适配器不能中断仓库摄入

    def _强制保留(自身):#强制保留上限
        """超限则逐出。"""
        while len(自身._请求)>自身.选项['maxRetainedRequests'] or 自身._日志字节>自身.选项['maxJournalBytes']:#超限
            键=自身._已完成.pop(0) if 自身._已完成 else next(iter(自身._请求))#逐出键
            请求=自身._请求[键]#取请求
            if not 请求['completed']:#未完成则失败
                请求['completed']=True#置完成
                自身._发布({#发布失败
                    'type':'request-failed','requestKey':请求['key'],'requestId':请求['requestId'],#身份
                    'timestampMs':time.time()*1000,'errorText':'Inspector retained-request limit exceeded','canceled':True,#取消
                })#publish结束
            自身._逐出(请求)#逐出

    def _为新字节逐出已完成(自身,字节数,保护键):#为新字节逐出已完成
        """腾出日志字节。"""
        while 自身._日志字节+字节数>自身.选项['maxJournalBytes']:#仍超
            索引=next((i for i,k in enumerate(自身._已完成) if k!=保护键),-1)#找可逐
            if 索引<0:#无可逐
                return#返回
            键=自身._已完成.pop(索引)#取出键
            自身._逐出(自身._请求[键])#逐出

    def _逐出(自身,请求):#逐出请求
        """删除请求与日志条目。"""
        自身._日志字节-=请求['requestBodyBytes']+请求['responseBodyBytes']#减字节
        自身._请求.pop(请求['key'],None)#删请求
        自身._日志=[项 for 项 in 自身._日志 if 项.get('requestKey')!=请求['key']]#删条目
        自身._发出({'type':'request-evicted','requestKey':请求['key']})#逐出事件

    def _按id取请求(自身,值):#按id取请求
        """公开请求 id 查找。"""
        if not isinstance(值,str):#类型
            raise ValueError('Network requestId must be a string')#类型
        for 请求 in 自身._请求.values():#查找
            if 请求['requestId']==值:#命中
                return 请求#返回
        raise RuntimeError(f'No resource with given identifier: {值}')#未找到

def _组装正文(块们,截断,捕获错,完整):#组装捕获正文
    """合并块。"""
    结果={'bytes':b''.join(块们),'truncated':截断,'complete':完整}#对象
    if 捕获错 is not None:#可选错误
        结果['captureError']=捕获错#写入
    return 结果#返回

def _解码base64(值):#解码base64
    """规范 base64。"""
    if 值=='' or len(值)%4!=0 or not re.fullmatch(r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?',值):#非规范
        raise ValueError('fetch payload body chunk must be canonical base64')#抛错
    字节=base64.b64decode(值)#解码
    if base64.b64encode(字节).decode('ascii')!=值:#再校验
        raise ValueError('fetch payload body chunk must be canonical base64')#抛错
    return 字节#返回

def _要求载荷(值):#要求载荷对象
    """必须为映射。"""
    if not isinstance(值,dict):#非对象
        raise ValueError('fetch payload must be an object')#非对象
    return 值#返回

def _字符串字段(值,名):#字符串字段
    """要求字符串。"""
    字段=值.get(名)#取值
    if not isinstance(字段,str):#类型
        raise ValueError(f'fetch payload {名} must be a string')#类型
    return 字段#返回

def _可选字符串字段(值,名):#可选字符串
    """可选字符串。"""
    字段=值.get(名)#取值
    if 字段 is not None and not isinstance(字段,str):#类型
        raise ValueError(f'fetch payload {名} must be a string')#类型
    return 字段#返回

def _数字字段(值,名):#数字字段
    """有限数字。"""
    字段=值.get(名)#取值
    if not isinstance(字段,(int,float)) or isinstance(字段,bool) or 字段!=字段:#类型
        raise ValueError(f'fetch payload {名} must be finite')#类型
    return 字段#返回

def _布尔字段(值,名):#布尔字段
    """要求布尔。"""
    字段=值.get(名)#取值
    if not isinstance(字段,bool):#类型
        raise ValueError(f'fetch payload {名} must be boolean')#类型
    return 字段#返回

def _头字段(值,名):#头字段
    """头列表。"""
    字段=值.get(名)#取值
    if not isinstance(字段,list):#类型
        raise ValueError(f'fetch payload {名} must be a header list')#类型
    结果=[]#列表
    for 项 in 字段:#映射
        if not isinstance(项,(list,tuple)) or len(项)!=2 or not isinstance(项[0],str) or not isinstance(项[1],str):#无效项
            raise ValueError(f'fetch payload {名} contains an invalid header')#抛错
        结果.append((项[0],项[1]))#头对
    return 结果#返回
