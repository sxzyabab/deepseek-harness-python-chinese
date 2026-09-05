"""字节与流式请求体的后台上传实现。

对齐上游 `file-upload/src/client/runtime.ts`。
浏览器 Worker/XHR/Blob 在 Python 侧用线程或同步 urllib/自定义 fetch 钩子表达；fixture 与钩子逻辑保留。
"""
import json,threading,time#JSON、线程与轮询
from urllib.parse import urlencode,urljoin#URL 拼装
import urllib.request as 请求库#标准库 HTTP
from ....依赖 import cordis#Cordis
服务=cordis.服务#服务基类
from ....工具.加密 import 字节转base64#字节转 base64
from ..协议 import 文件上传路径#上传路径
from ..类型 import 远程错误#Remote 错误

__all__=[#仅中文公开名
    '文件上传工作体',
    '文件上传运行时',
    '默认',
]#公开面结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性

def 取已中止(信号):#读 aborted
    """映射或对象。"""
    if 信号 is None:#无
        return False#未
    if isinstance(信号,dict):#映射
        return bool(信号.get('aborted'))#旗
    return bool(getattr(信号,'aborted',False) or getattr(信号,'已中止',False))#属性

def 是否精确字节(数据):#是否精确字节体
    """对齐 Uint8Array 支。"""
    return isinstance(数据,(bytes,bytearray,memoryview))#字节类

def 是否流式正文(数据):#是否一次性字节流
    """可迭代字节块且非精确字节、非映射。"""
    if 是否精确字节(数据):#精确字节
        return False#否
    if isinstance(数据,(str,dict)):#文本或映射
        return False#否
    return hasattr(数据,'__iter__')#可迭代

def 物化字节(数据):#聚合成精确字节
    """流或类文件读成 bytes。"""
    if 是否精确字节(数据):#已是
        return bytes(数据)#拷贝
    if hasattr(数据,'read') and callable(数据.read):#类文件
        块=数据.read()#整读
        if isinstance(块,str):#文本
            return 块.encode('utf-8')#编码
        return bytes(块)#字节
    if 是否流式正文(数据):#流
        return b''.join(bytes(块) if not isinstance(块,str) else 块.encode('utf-8') for 块 in 数据)#聚合
    raise TypeError('background upload worker received an invalid body')#非法体

class 进度可读:#带进度的类文件正文
    """供 urllib 边读边报进度。"""
    def __init__(自身,源,进度回调=None,信号=None,总量=None):#绑定源
        """记下源与观察者。"""
        自身._源=源#源
        自身._进度回调=进度回调#进度
        自身._信号=信号#取消
        自身._总量=总量#可选总量
        自身._已载=0#已消费
        自身._缓冲=b''#内部缓冲
        自身._结束=False#是否结束
        if 是否精确字节(源):#精确字节
            自身._缓冲=bytes(源)#整段
            自身._总量=len(自身._缓冲) if 总量 is None else 总量#总量
            自身._迭代=None#无迭代
        elif hasattr(源,'read') and callable(源.read):#类文件
            自身._迭代=None#用 read
            自身._读=源.read#读
        else:#迭代流
            自身._迭代=iter(源)#迭代器
            自身._读=None#无 read

    def read(自身,大小=-1):#读一块
        """读并报告进度；已取消则抛。"""
        if 取已中止(自身._信号):#已取消
            raise Exception('The operation was aborted.')#AbortError 文案近似
        if 自身._结束 and not 自身._缓冲:#已空
            return b''#结束
        if 自身._迭代 is not None and not 自身._缓冲:#从流补缓冲
            try:#下一块
                块=next(自身._迭代)#取
            except StopIteration:#结束
                自身._结束=True#标记
                块=b''#空
            if 块:#有块
                if isinstance(块,str):#文本
                    块=块.encode('utf-8')#编码
                自身._缓冲+=bytes(块)#追加
        elif 自身._读 is not None and not 自身._缓冲 and not 自身._结束:#类文件补
            块=自身._读(65536 if 大小<0 else 大小)#读
            if not 块:#结束
                自身._结束=True#标记
            else:#有
                if isinstance(块,str):#文本
                    块=块.encode('utf-8')#编码
                自身._缓冲+=bytes(块)#追加
        if 大小 is None or 大小<0:#全读缓冲
            出=自身._缓冲#整段
            自身._缓冲=b''#清空
        else:#有上限
            出=自身._缓冲[:大小]#切片
            自身._缓冲=自身._缓冲[大小:]#剩余
        自身._已载+=len(出)#累计
        if 自身._进度回调 is not None and 出:#有进度
            进度={'loaded':自身._已载}#已传
            if 自身._总量 is not None:#有总量
                进度['total']=自身._总量#总量
            自身._进度回调(进度)#报告
        return 出#字节

def 文件上传工作体(回传,创建请求=None,执行fetch=None):#Worker 语义入口
    """自包含上传体：Blob/精确字节走 urllib 带进度；流式走边读边 POST。"""
    if 创建请求 is None:#缺省
        创建请求=lambda 方法,网址,数据,头:请求库.Request(网址,data=数据,headers=头,method=方法)#标准 Request
    if 执行fetch is None:#缺省
        def 执行fetch(网址,初始化):#默认同步 fetch
            """urllib 投递。"""
            方法=取字段(初始化,'method','GET')#方法
            头=dict(取字段(初始化,'headers') or {})#头
            正文=取字段(初始化,'body')#正文
            请求=创建请求(方法,str(网址),正文,头)#构造
            return 请求库.urlopen(请求)#发出
    def 处理启动(启动):#收到启动消息
        """对齐 Worker onmessage。"""
        网址=取字段(启动,'url')#绝对 URL
        正文=取字段(启动,'body')#请求体
        头=dict(取字段(启动,'headers') or {})#请求头
        进度回调=取字段(启动,'onProgress')#可选进度
        信号=取字段(启动,'signal')#可选取消
        try:#传输
            if 是否精确字节(正文) or (hasattr(正文,'read') and not 是否流式正文(正文)):#精确或类文件
                总量=len(正文) if 是否精确字节(正文) else None#Blob 有总量
                可读=进度可读(正文,进度回调,信号,总量)#带进度
                初始化={'method':'POST','headers':头,'body':可读}#请求
                响应=执行fetch(网址,初始化)#发出
                状态=取字段(响应,'status') if not hasattr(响应,'getcode') else 响应.getcode()#状态
                响应正文=取字段(响应,'body')#正文
                if 响应正文 is None and hasattr(响应,'read'):#urllib 响应
                    响应正文=响应.read()#读
                if isinstance(响应正文,bytes):#字节
                    响应正文=响应正文.decode('utf-8')#解码
                回传({'kind':'complete','status':状态,'body':响应正文 or ''})#完成
                return#Blob 支结束
            if not 是否流式正文(正文):#非法体
                回传({'kind':'error','message':'background upload worker received an invalid body'})#回传错误
                return#结束
            已载=[0]#已消费字节
            def 流进度(进度):#转发进度
                """无总量。"""
                已载[0]=进度['loaded']#记下
                回传({'kind':'progress','loaded':进度['loaded']})#报告
            可读=进度可读(正文,流进度,信号,None)#转发流
            初始化={'method':'POST','headers':头,'body':可读}#请求
            响应=执行fetch(网址,初始化)#发出
            状态=取字段(响应,'status') if not hasattr(响应,'getcode') else 响应.getcode()#状态
            响应正文=取字段(响应,'body')#正文
            if 响应正文 is None and hasattr(响应,'read'):#urllib
                响应正文=响应.read()#读
            if isinstance(响应正文,bytes):#字节
                响应正文=响应正文.decode('utf-8')#解码
            回传({'kind':'complete','status':状态,'body':响应正文 or ''})#完成
        except BaseException as 错误:#异步失败
            回传({#错误
                'kind':'error',#错误
                'message':错误.args[0] if isinstance(错误,Exception) and 错误.args else str(错误),#消息
            })#结束回传
    return 处理启动#入口

fileUploadWorker=文件上传工作体#上游名

def 取全局钩子():#读启动前钩子
    """builtins.__DSH_FILE_UPLOAD__。"""
    try:#取全局
        import builtins#全局
        return getattr(builtins,'__DSH_FILE_UPLOAD__',None)#可选
    except Exception:#无
        return None#无

def 是否夹具页():#是否 fixture 页
    """URL 带 fixture 查询。"""
    try:#取 location
        import builtins#全局
        页面=getattr(builtins,'location',None)#可能缺
    except Exception:#无
        页面=None#无
    if 页面 is None:#非浏览器
        return False#否
    查询=getattr(页面,'search','') or ''#查询串
    if 查询.startswith('?'):#带问号
        查询=查询[1:]#去掉
    from urllib.parse import parse_qs#解析
    return 'fixture' in parse_qs(查询)#带 fixture

def 解析网址(路径):#相对路径解析为绝对 URL
    """有页面 origin 则用，否则 http://dsh.internal。"""
    try:#取 location
        import builtins#全局
        页面=getattr(builtins,'location',None)#可能缺
    except Exception:#无
        页面=None#无
    源=None#可选源
    if 页面 is not None:#有页面
        源=getattr(页面,'origin',None)#origin
        if not isinstance(源,str):#无
            源=None#清空
    if 源 is None or 源=='null':#缺源
        基='http://dsh.internal'#内部基
    else:#有源
        基=源#用页面源
    return urljoin(基.rstrip('/')+'/',路径.lstrip('/') if 路径.startswith('/') else 路径)#解析

def 自定义载体(自定义fetch):#页面自有载体
    """经页面 Fetch 钩子投递。"""
    def 投递(请求):#发 POST
        """返回 status 与正文文本。"""
        初始化={#请求初始化
            'method':'POST',#方法
            'body':取字段(请求,'body'),#正文
        }#基
        头=取字段(请求,'headers')#可选头
        if 头 is not None:#有头
            初始化['headers']=头#写入
        信号=取字段(请求,'signal')#可选取消
        if 信号 is not None:#有
            初始化['signal']=信号#写入
        if 是否流式正文(取字段(请求,'body')):#流需 duplex 标记
            初始化['duplex']='half'#半双工
        响应=自定义fetch(解析网址(取字段(请求,'path')),初始化)#经页面 Fetch
        状态=取字段(响应,'status',200)#状态
        正文=取字段(响应,'body')#正文
        if 正文 is None:#尝试 text
            取文本=getattr(响应,'text',None)#方法
            if callable(取文本):#有
                正文=取文本()#读
                if hasattr(正文,'wait'):#承诺
                    正文=正文.wait()#等待
            elif hasattr(响应,'read'):#可读
                正文=响应.read()#读
        if isinstance(正文,bytes):#字节
            正文=正文.decode('utf-8')#解码
        return {'status':状态,'body':正文 or ''}#状态与正文
    return {'post':投递}#transport

def 线程载体():#专用线程载体（对齐 Worker）
    """在后台线程跑上传工作体。"""
    def 投递(请求):#发 POST
        """包装线程与取消。"""
        出箱=[]#输出消息
        锁=threading.Lock()#互斥
        唤醒=threading.Event()#有消息
        def 回传(消息):#Worker 回传
            """入队并唤醒。"""
            with 锁:#持锁
                出箱.append(消息)#放入
            唤醒.set()#唤醒
        处理=文件上传工作体(回传)#工作体
        启动={#启动消息
            'url':解析网址(取字段(请求,'path')),#绝对 URL
            'body':取字段(请求,'body'),#正文
            'headers':取字段(请求,'headers') or {},#头
            'onProgress':取字段(请求,'onProgress'),#进度
            'signal':取字段(请求,'signal'),#取消
        }#结束 message
        错误盒={'v':None}#线程错误
        def 跑():#线程入口
            """跑工作体。"""
            try:#执行
                处理(启动)#启动
            except BaseException as 错误:#脚本错误
                错误盒['v']=错误#记下
                回传({'kind':'error','message':str(错误) or 'background upload worker failed'})#拒绝
        线=threading.Thread(target=跑,daemon=True,name='dsh-file-upload')#建线程
        线.start()#启动
        信号=取字段(请求,'signal')#取消
        if 取已中止(信号):#已取消
            raise Exception('The operation was aborted.')#AbortError
        while True:#等到完成
            if 取已中止(信号):#取消
                raise Exception('The operation was aborted.')#AbortError
            唤醒.wait(0.05)#短等
            唤醒.clear()#清
            with 锁:#持锁
                while 出箱:#排空
                    输出=出箱.pop(0)#取出
                    if 输出['kind']=='progress':#进度
                        回调=取字段(请求,'onProgress')#观察者
                        if 回调 is not None:#有
                            进度={'loaded':输出['loaded']}#已传
                            if 'total' in 输出:#可选总量
                                进度['total']=输出['total']#总量
                            回调(进度)#报告
                    elif 输出['kind']=='complete':#完成
                        return {'status':输出['status'],'body':输出['body']}#兑现
                    else:#错误
                        raise Exception(输出.get('message') or 'background upload transport failed')#拒绝
            if not 线.is_alive() and not 出箱:#线程已死且无消息
                if 错误盒['v'] is not None:#有错
                    raise 错误盒['v']#抛
                raise Exception('background upload worker failed')#失败
            time.sleep(0.01)#让出
    return {'post':投递}#transport

def 是否普通对象(值):#是否普通对象
    """非 null 非数组对象。"""
    return isinstance(值,dict)#映射即记录

def 解析文件上传结果(正文):#解析 JSON 结果
    """成功 RemoteResult 或失败 RemoteError。"""
    值=json.loads(正文)#解析
    if not 是否普通对象(值) or not isinstance(值.get('ok'),bool):#形态不对
        raise TypeError('file upload transport returned an invalid result')#类型错误
    if not 值['ok']:#失败支
        错误=值.get('error')#错误字段
        if (not 是否普通对象(错误) or not isinstance(错误.get('code'),str)
            or not isinstance(错误.get('message'),str) or not 是否普通对象(错误.get('details'))):#失败形态不对
            raise TypeError('file upload transport returned an invalid failure')#类型错误
        return {#失败
            'ok':False,#失败
            'error':远程错误(错误['code'],错误['message'],错误['details']),#Remote 错误
        }#结束失败返回
    结果=值.get('value')#成功值
    文件=结果.get('file') if 是否普通对象(结果) else None#文件字段
    if (not 是否普通对象(结果) or not isinstance(结果.get('receiptId'),str) or not 是否普通对象(文件)
        or not isinstance(文件.get('attachmentId'),str) or not isinstance(文件.get('name'),str)
        or not isinstance(文件.get('bytes'),(int,float)) or int(文件['bytes'])!=文件['bytes'] or 文件['bytes']<0):#凭证形态不对
        raise TypeError('file upload transport returned an invalid receipt')#类型错误
    return {#成功
        'ok':True,#成功
        'value':{#值
            'receiptId':结果['receiptId'],#凭证 id
            'file':{#文件
                'attachmentId':文件['attachmentId'],#附件 id
                'name':文件['name'],#叶名
                'bytes':int(文件['bytes']),#字节数
            },#结束 file
        },#结束 value
    }#结束成功返回

class 文件上传运行时(服务):#上传运行时
    """每次上传操作拥有一个后台载体的 Cordis 服务。"""
    def __init__(自身,上下文):#构造
        """提供方客户端上下文。"""
        super().__init__(上下文,'fileUpload')#登记服务名
        钩子=取全局钩子()#启动前钩子
        自身.available=钩子 is not None or (not 是否夹具页())#fixture 且无钩子则不可用
        if 钩子 is None:#无钩子
            自身._载体=线程载体()#线程载体
        else:#有钩子
            取fetch=取字段(钩子,'fetch')#Fetch 载体
            自身._载体=自定义载体(取fetch)#页面载体

    @property
    def 可用(自身):#中文别名
        """本页是否有 Host 支撑的后台上传载体。"""
        return 自身.available#转发

    def 投递(自身,请求):#投递
        """用 Cordis 启动前选定的载体投递一次请求体。"""
        if not 自身.available:#fixture 不可用
            raise Exception('background upload is unavailable in fixture mode')#拒绝
        return 自身._载体['post'](请求)#委托载体

    post=投递#上游名

    def 上传(自身,会话标识,数据,名=None,信号=None,进度回调=None):#上传入口
        """为一个 Session 存储一个文件。"""
        if (not 是否精确字节(数据)) and 自身.available:#非精确字节且有后台载体
            查询={'sessionId':str(会话标识)}#会话查询
            if 名 is not None:#可选名
                查询['name']=名#写入
            路径=文件上传路径+'?'+urlencode(查询)#带查询路径
            请求={#经后台载体
                'path':路径,#路径
                'body':数据,#字节或流
                'headers':{'content-type':'application/octet-stream'},#原始字节
            }#基
            if 信号 is not None:#可选取消
                请求['signal']=信号#写入
            if 进度回调 is not None:#可选进度
                请求['onProgress']=进度回调#写入
            响应=自身.投递(请求)#投递
            if 取字段(响应,'status')!=200:#传输层失败
                raise Exception('file upload transport failed with HTTP '+str(取字段(响应,'status')))#抛错
            return 解析文件上传结果(取字段(响应,'body'))#解析 JSON 结果
        if (not 是否精确字节(数据)) and 是否流式正文(数据):#流却无载体
            raise Exception('stream file upload requires a background carrier')#必须有载体
        字节=物化字节(数据)#聚合成精确字节
        远程面=取字段(自身.ctx,'remote')#remote
        上传面=取字段(取字段(远程面,'fileUploads'),'upload')#编码 Remote 上传
        请求体={'data':字节转base64(字节)}#编码
        if 名 is not None:#可选名
            请求体['name']=名#写入
        return 上传面(会话标识,请求体,信号)#Remote 兜底

    upload=上传#上游名

默认=文件上传运行时#默认导出
FileUploadRuntime=文件上传运行时#上游名
