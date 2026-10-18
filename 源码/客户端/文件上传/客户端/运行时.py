'后台浏览器上传。Blob 和字节流留在页面里传，精确字节读出来再走远程'
from ...模块.客户端.通告 import 取握手窗口
import json#解析上传结果
import threading#等 Worker 回传
from urllib.parse import urlencode as 编码查询#与 URLSearchParams 相同的查询编码
from pywebbridge.基础 import JavaScript对象,undefined as 未定义
from pywebbridge.异常 import DOM异常
from ....依赖.cordis.服务 import 服务#服务基类
from ....工具.加密 import 字节转base64#精确字节的远程兜底
from ....类型化远程调用.协议 import 远程错误#失败回执
from ..协议 import 文件上传路由#文档相对上传路径

def 浏览器类名(值):
    '页面对象的 constructor.name。普通 Python 值没有'
    if not isinstance(值,JavaScript对象):#不是页面对象
        return None#没有类名
    构造=getattr(值,'constructor',None)#构造函数
    if 构造 is None or 构造 is 未定义:#页面上没有
        return None#没有类名
    名称=getattr(构造,'name',None)#constructor.name
    if 名称 is None or 名称 is 未定义:#没有名字
        return None#没有类名
    return 名称#页面上的类名

def 等落定(值):
    '期约则等到落定，普通值原样返回'
    if hasattr(值,'等待'):#期约
        return 值.等待()#同步结果
    return 值#已经是结果

def 是否记录(值):
    '非空且不是数组的对象'
    return isinstance(值,dict)#JSON 对象

def 文件上传工作体(作用域=None,创建请求=None,执行fetch=None):
    '自包含上传体。Blob 走 XMLHttpRequest，字节流走 fetch。脚本文本是 Worker 里实际运行的脚本'
    窗口=取握手窗口()#当前页
    if 作用域 is None:#没给工作线程全局
        作用域=窗口#页面上直接调用时用窗口
    请求工厂=创建请求#调用方给的 XMLHttpRequest 工厂
    if 请求工厂 is None:#没给就用页面上的
        def 默认创建请求():
            '用页面的 XMLHttpRequest'
            return 窗口.XMLHttpRequest()#原生请求
        请求工厂=默认创建请求#默认工厂
    页面fetch=执行fetch#调用方给的 fetch
    if 页面fetch is None:#没给就用页面上的
        def 默认fetch(输入,初始化):
            '这个网页引擎不再通过浏览器请求宿主'
            raise RuntimeError('这个网页引擎不再通过浏览器请求宿主 '+str(输入))
        页面fetch=默认fetch#默认 fetch
    def 收到(事件):
        '处理一条启动消息'
        请求=事件['data'] if isinstance(事件,dict) else 事件.data#启动数据
        def 取(键):
            '从启动数据取值'
            if isinstance(请求,dict):#映射
                return 请求[键] if 键 in 请求 else None#有则取
            return getattr(请求,键)#对象属性
        网址=取('url')#绝对地址
        正文=取('body')#Blob 或流
        头=取('headers') or {}#请求头
        if 浏览器类名(正文)=='Blob':#文件体
            请求对象=请求工厂()#这一次的请求
            请求对象.open('POST',网址)#打开
            请求对象.withCredentials=True#带上凭据
            for 名,值 in 头.items():#逐个请求头
                请求对象.setRequestHeader(名,值)#写入
            def 进度(进度事件):
                '报告已上传字节。总量只有算得出来才带'
                载荷={'kind':'progress','loaded':进度事件.loaded}#已上传
                if 进度事件.lengthComputable:#总量已知
                    载荷['total']=进度事件.total#带上总量
                作用域.postMessage(载荷)#回给页面
            请求对象.upload.onprogress=进度#上传进度
            def 载入(_事件=None):
                '请求完成'
                作用域.postMessage({'kind':'complete','status':请求对象.status,'body':请求对象.responseText})#状态和正文
            请求对象.onload=载入#完成
            def 出错(_事件=None):
                '传输失败'
                作用域.postMessage({'kind':'error','message':'background upload transport failed'})#固定失败句
            请求对象.onerror=出错#失败
            请求对象.send(正文)#发出，字节仍留在页面
            return#Blob 支结束
        if 浏览器类名(正文)!='ReadableStream':#不是一次性字节流
            作用域.postMessage({'kind':'error','message':'background upload worker received an invalid body'})#非法体
            return#停
        阅读器=正文.getReader()#锁住源
        已载={'n':0}#已消费字节
        def 拉取(控制器):
            '拉一块，报告进度，再送进给 fetch 的流'
            项=等落定(阅读器.read())#下一块
            完成=项['done'] if isinstance(项,dict) else 项.done#是否结束
            if 完成:#源结束
                控制器.close()#关闭输出流
                return#停
            值=项['value'] if isinstance(项,dict) else 项.value#这一块
            if 浏览器类名(值)!='Uint8Array' and not isinstance(值,(bytes,bytearray)):#不是字节块
                raise TypeError('background upload stream produced a non-Uint8Array chunk')#拒绝
            if isinstance(值,(bytes,bytearray)):#已经是字节
                长度=len(值)#长度
            else:#页面上的 Uint8Array
                长度=值.byteLength#字节长度
            已载['n']=已载['n']+长度#累加
            作用域.postMessage({'kind':'progress','loaded':已载['n']})#无总量
            控制器.enqueue(值)#交给 fetch
        def 取消(原因=None):
            '取消时把原因交还给源'
            等落定(阅读器.cancel(原因))#取消源
        体=窗口.ReadableStream({'pull':拉取,'cancel':取消})#给 fetch 的半双工流
        try:#传输失败收成错误消息
            响应=等落定(页面fetch(网址,{#发出
                'method':'POST',#方法
                'headers':头,#请求头
                'credentials':'include',#凭据
                'body':体,#流
                'duplex':'half',#半双工
            }))#响应
            文本=等落定(响应.text())#正文字符串
            作用域.postMessage({'kind':'complete','status':响应.status,'body':文本})#完成
        except Exception as 错误:#fetch 或块类型失败
            if isinstance(getattr(错误,'message',None),str):#带消息
                消息=错误.message#用消息
            else:#其余
                消息=str(错误)#转成文本
            作用域.postMessage({'kind':'error','message':消息})#回给页面
    作用域.onmessage=收到#等待启动消息

文件上传工作体.脚本文本=(
    'function fileUploadWorker(scope=self,createXhr=()=>new XMLHttpRequest(),'
    'doFetch=(input,init)=>fetch(input,init)){'
    'scope.onmessage=(event)=>{'
    'const request=event.data;'
    'if(request.body instanceof Blob){'
    'const xhr=createXhr();'
    'xhr.open("POST",request.url);'
    'xhr.withCredentials=true;'
    'for(const [name,value] of Object.entries(request.headers))xhr.setRequestHeader(name,value);'
    'xhr.upload.onprogress=(progress)=>{'
    'const message={kind:"progress",loaded:progress.loaded};'
    'if(progress.lengthComputable)message.total=progress.total;'
    'scope.postMessage(message);'
    '};'
    'xhr.onload=()=>{scope.postMessage({kind:"complete",status:xhr.status,body:xhr.responseText});};'
    'xhr.onerror=()=>{scope.postMessage({kind:"error",message:"background upload transport failed"});};'
    'xhr.send(request.body);'
    'return;'
    '}'
    'if(!(request.body instanceof ReadableStream)){'
    'scope.postMessage({kind:"error",message:"background upload worker received an invalid body"});'
    'return;'
    '}'
    'const source=request.body;'
    'void (async()=>{'
    'const reader=source.getReader();'
    'let loaded=0;'
    'const body=new ReadableStream({'
    'async pull(controller){'
    'const item=await reader.read();'
    'if(item.done){controller.close();return;}'
    'if(!(item.value instanceof Uint8Array)){'
    'throw new TypeError("background upload stream produced a non-Uint8Array chunk");'
    '}'
    'loaded+=item.value.byteLength;'
    'scope.postMessage({kind:"progress",loaded});'
    'controller.enqueue(item.value);'
    '},'
    'async cancel(reason){await reader.cancel(reason);}'
    '});'
    'const response=await doFetch(request.url,{'
    'method:"POST",headers:request.headers,credentials:"include",body,duplex:"half"'
    '});'
    'scope.postMessage({kind:"complete",status:response.status,body:await response.text()});'
    '})().catch((error)=>{'
    'scope.postMessage({kind:"error",message:error instanceof Error?error.message:String(error)});'
    '});'
    '}'
    '}'
)#Worker 里运行的脚本，对应函数 toString

class 文件上传运行时(服务):
    '每次上传使用启动前选定的一个后台载体'
    def __init__(自身,上下文,配置=None):
        '没有页面钩子就用 Worker，有钩子就用页面自己的 fetch'
        super().__init__(上下文,'fileUpload')#服务名
        窗口=取握手窗口()#当前页
        钩子=窗口['__DSH_FILE_UPLOAD__']#启动前注入的钩子
        if 钩子 is 未定义:#没有钩子
            def 投递(请求):
                '为这一次上传开一个 Worker，等它回传后关掉'
                工作者类=窗口['Worker']#页面上的构造器
                if 工作者类 is 未定义:#没有 Worker
                    raise RuntimeError('background upload requires Web Worker support')#必须有
                脚本='('+文件上传工作体.脚本文本+')()'#自调用，默认参数用 Worker 全局
                块=窗口.Blob([脚本],{'type':'text/javascript'})#脚本块
                地址=窗口.URL.createObjectURL(块)#临时地址
                工作者=窗口.Worker(地址,{'name':'dsh-file-upload'})#后台上传
                窗口.URL.revokeObjectURL(地址)#地址只用一次
                完成=threading.Event()#回传或失败时放开
                盒子={'值':None,'错误':None,'已结算':False}#只结算一次
                信号=请求['signal'] if 'signal' in 请求 else None#可选取消
                锁=threading.Lock()#回传和取消可能不在同一线程
                def 结束(落实):
                    '关掉 Worker 并记下这一次的结果'
                    with 锁:#只进一次
                        if 盒子['已结算']:#已经结束
                            return#停
                        盒子['已结算']=True#占住
                    if 信号 is not None:#曾可能登记过取消
                        信号.removeEventListener('abort',中止)#卸下
                    工作者.terminate()#停掉后台
                    落实()#写入结果或错误
                    完成.set()#放开等待
                def 中止(_事件=None):
                    '调用方取消'
                    def 拒绝():
                        '记成 AbortError'
                        错误=DOM异常('The operation was aborted.')#与浏览器同一句
                        错误.name='AbortError'#调用方按这个名字识别
                        盒子['错误']=错误#拒绝
                    结束(拒绝)#结算
                def 收到(事件):
                    '转发进度，或在完成和失败时结算'
                    输出=事件['data'] if isinstance(事件,dict) else 事件.data#回传
                    if not isinstance(输出,dict):#页面对象
                        输出={'kind':输出.kind,'loaded':getattr(输出,'loaded',None),'total':getattr(输出,'total',未定义),'status':getattr(输出,'status',None),'body':getattr(输出,'body',None),'message':getattr(输出,'message',None)}#收成映射
                    if 输出['kind']=='progress':#进度
                        回调=请求['onProgress'] if 'onProgress' in 请求 else None#观察者
                        if 回调 is not None:#有观察者
                            进度={'loaded':输出['loaded']}#已上传
                            if 'total' in 输出 and 输出['total'] is not 未定义 and 输出['total'] is not None:#有总量
                                进度['total']=输出['total']#带上
                            回调(进度)#报告
                    elif 输出['kind']=='complete':#完成
                        def 兑现():
                            '记下状态和正文'
                            盒子['值']={'status':输出['status'],'body':输出['body']}#结果
                        结束(兑现)#结算
                    else:#失败
                        def 拒绝():
                            '用回传的消息拒绝'
                            盒子['错误']=RuntimeError(输出['message'])#失败句
                        结束(拒绝)#结算
                def 工作失败(事件):
                    'Worker 自己报错'
                    消息=None#错误句
                    if isinstance(事件,dict):#映射
                        消息=事件['message'] if 'message' in 事件 else None#消息
                    else:#事件对象
                        消息=getattr(事件,'message',None)#消息
                    if not isinstance(消息,str) or 消息=='':#没有消息
                        消息='background upload worker failed'#固定句
                    def 拒绝():
                        '记下 Worker 失败'
                        盒子['错误']=RuntimeError(消息)#失败
                    结束(拒绝)#结算
                工作者.onmessage=收到#回传
                工作者.onerror=工作失败#脚本失败
                if 信号 is not None and getattr(信号,'aborted',None) is True:#发出前已经取消
                    中止()#不再投递
                else:#还没取消
                    if 信号 is not None:#有信号
                        信号.addEventListener('abort',中止,{'once':True})#取消时停
                    消息={'url':窗口.URL(请求['path'],窗口.document.baseURI).href,'body':请求['body'],'headers':请求['headers'] if 'headers' in 请求 and 请求['headers'] is not None else {}}#Worker 的地址必须是绝对的
                    if 浏览器类名(请求['body'])=='ReadableStream':#流要转移所有权
                        工作者.postMessage(消息,[请求['body']])#转移
                    else:#Blob
                        工作者.postMessage(消息)#复制消息
                if not 盒子['已结算']:#还在传
                    完成.wait()#等到回传
                if 盒子['错误'] is not None:#失败或取消
                    raise 盒子['错误']#抛出
                return 盒子['值']#状态和正文
            自身._载体={'post':投递}#Worker 载体
        else:#页面自己的 fetch
            自定义fetch=钩子.fetch if not isinstance(钩子,dict) else 钩子['fetch']#钩子上的 fetch
            def 投递(请求):
                '把文档相对地址交给页面自己的 fetch'
                初始化={'method':'POST','body':请求['body']}#方法与正文
                if 'headers' in 请求 and 请求['headers'] is not None:#有请求头
                    初始化['headers']=请求['headers']#写入
                if 浏览器类名(请求['body'])=='ReadableStream':#流
                    初始化['duplex']='half'#半双工
                if 'signal' in 请求 and 请求['signal'] is not None:#有取消
                    初始化['signal']=请求['signal']#写入
                响应=等落定(自定义fetch(请求['path'],初始化))#文档相对地址，由钩子自己解析
                文本=等落定(响应.text())#正文字符串
                return {'status':响应.status,'body':文本}#状态和正文
            自身._载体={'post':投递}#页面载体

    def 投递(自身,请求):
        '用启动前选定的载体发出一次请求体'
        return 自身._载体['post'](请求)#委托

    def 上传(自身,会话标识,数据,名=None,信号=None,进度回调=None):
        '为一个会话存储一个文件。Blob 和流走后台，精确字节走远程'
        精确=isinstance(数据,(bytes,bytearray,memoryview)) or 浏览器类名(数据)=='Uint8Array'#精确字节
        if not 精确:#后台载体
            查询={'sessionId':str(会话标识)}#会话
            if 名 is not None:#有显示名
                查询['name']=名#写入，空格和 & 按表单编码
            请求={'path':文件上传路由+'?'+编码查询(查询),'body':数据,'headers':{'content-type':'application/octet-stream'}}#原始字节
            if 信号 is not None:#可选取消
                请求['signal']=信号#写入
            if 进度回调 is not None:#可选进度
                请求['onProgress']=进度回调#写入
            响应=自身.投递(请求)#发出
            if 响应['status']!=200:#传输层失败
                raise RuntimeError('file upload transport failed with HTTP '+str(响应['status']))#带状态码
            值=json.loads(响应['body'])#解析 JSON
            if not 是否记录(值) or not isinstance(值.get('ok'),bool):#不是结果
                raise TypeError('file upload transport returned an invalid result')#非法结果
            if not 值['ok']:#业务失败
                错误=值.get('error')#错误字段
                if (not 是否记录(错误) or not isinstance(错误.get('code'),str)
                        or not isinstance(错误.get('message'),str) or not 是否记录(错误.get('details'))):#失败形态不对
                    raise TypeError('file upload transport returned an invalid failure')#非法失败
                return {'ok':False,'error':远程错误(错误['code'],错误['message'],错误['details'])}#远程失败
            结果值=值.get('value')#成功值
            文件=结果值.get('file') if 是否记录(结果值) else None#文件
            字节数=文件.get('bytes') if 是否记录(文件) else None#字节数
            凭证=结果值.get('receiptId') if 是否记录(结果值) else None#凭证
            if (not 是否记录(结果值) or not isinstance(凭证,str) or not 是否记录(文件)
                    or not isinstance(文件.get('attachmentId'),str) or not isinstance(文件.get('name'),str)
                    or isinstance(字节数,bool) or not isinstance(字节数,int) or 字节数<0
                    or 字节数>9007199254740991):#回执形态不对
                raise TypeError('file upload transport returned an invalid receipt')#非法回执
            return {'ok':True,'value':{'receiptId':凭证,'file':{'attachmentId':文件['attachmentId'],'name':文件['name'],'bytes':字节数}}}#回执
        if isinstance(数据,(bytes,bytearray,memoryview)):#本进程字节
            原始=bytes(数据)#拷贝
        else:#页面上的 Uint8Array，这里才读回
            长度=数据.byteLength#字节数
            片段=[]#逐字节
            索引=0#下标
            while 索引<长度:#桥没有整段拷贝
                片段.append(数据[索引])#一个字节
                索引=索引+1#前进
            原始=bytes(片段)#拼成字节
        请求体={'data':字节转base64(原始)}#规范 base64
        if 名 is not None:#有显示名
            请求体['name']=名#写入
        return 等落定(自身.ctx.remote.fileUploads.upload(会话标识,请求体,信号))#远程兜底
