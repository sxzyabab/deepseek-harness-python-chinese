import builtins,json,threading,time#全局、JSON、线程与轮询
from urllib.parse import parse_qs,urlencode,urljoin#URL 拼装
import urllib.request as 请求库#标准库 HTTP
from ....依赖 import cordis#Cordis
服务=cordis.服务#服务基类
from ....工具.加密 import 字节转base64#字节转 base64
from ..协议 import 文件上传路径#上传路径
from ..类型 import 远程错误,文件上传错误,已中止,若已中止则抛出#错误与中止

__all__=[#仅中文公开名
    '文件上传工作体',
    '文件上传运行时',
]#公开面结束

def 是否精确字节(数据):#是否精确字节体
    """对齐 Uint8Array 支。"""
    return isinstance(数据,(bytes,bytearray,memoryview))#字节类

def 是否类文件(数据):#是否有 read 的正文
    """Blob/类文件臂：有 read 且非整段字节、非串、非映射。"""
    if 是否精确字节(数据) or isinstance(数据,(str,dict)):#排除
        return False#否
    try:#类文件声明 read
        数据.read#读口
    except AttributeError:#无
        return False#否
    return True#是

def 是否流式正文(数据):#是否一次性字节流
    """可迭代字节块且非精确字节、非映射、非类文件。"""
    if 是否精确字节(数据) or 是否类文件(数据):#精确或类文件
        return False#否
    if isinstance(数据,(str,dict)):#文本或映射
        return False#否
    return True#可迭代

def 物化字节(数据):#聚合成精确字节
    """流或类文件读成 bytes。"""
    if 是否精确字节(数据):#已是
        return bytes(数据)#拷贝
    if 是否类文件(数据):#类文件
        块=数据.read()#整读
        if isinstance(块,str):#文本
            return 块.encode('utf-8')#编码
        return bytes(块)#字节
    if 是否流式正文(数据):#流
        return b''.join(bytes(块) if not isinstance(块,str) else 块.encode('utf-8') for 块 in 数据)#聚合
    raise TypeError('后台上传工作线程收到非法体')#非法体

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
            自身._读=None#无 read
        elif 是否类文件(源):#类文件
            自身._迭代=None#用 read
            自身._读=源.read#读
        else:#迭代流
            自身._迭代=iter(源)#迭代器
            自身._读=None#无 read

    def read(自身,大小=-1):#读一块
        """读并报告进度；已取消则抛。"""
        若已中止则抛出(自身._信号)#已取消
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
        if 自身._进度回调 is not None and len(出)>0:#有进度
            进度={'loaded':自身._已载}#已传
            if 自身._总量 is not None:#有总量
                进度['total']=自身._总量#总量
            自身._进度回调(进度)#报告
        return 出#字节

def 默认同步fetch(网址,初始化):#urllib 投递并归一成 dict
    """标准库 HTTP，响应冻结为 dict。"""
    方法=初始化['method'] if 'method' in 初始化 else 'GET'#方法
    头=dict(初始化['headers']) if 'headers' in 初始化 and 初始化['headers'] is not None else {}#头
    正文=初始化['body'] if 'body' in 初始化 else None#正文
    请求=请求库.Request(str(网址),data=正文,headers=头,method=方法)#构造
    响应=请求库.urlopen(请求)#发出
    状态=响应.getcode()#状态
    响应正文=响应.read()#正文
    if isinstance(响应正文,bytes):#字节
        响应正文=响应正文.decode('utf-8')#解码
    return {'status':状态,'body':响应正文 or ''}#dict 响应

def 文件上传工作体(回传,创建请求=None,执行fetch=None):#Worker 语义入口
    """自包含上传体：精确字节走 urllib 带进度；流式走边读边 POST。"""
    if 执行fetch is None:#缺省
        执行fetch=默认同步fetch#标准 fetch
    def 处理启动(启动):#收到启动消息
        """对齐 Worker onmessage。"""
        网址=启动['url']#绝对 URL
        正文=启动['body']#请求体
        头=dict(启动['headers']) if 'headers' in 启动 and 启动['headers'] is not None else {}#请求头
        进度回调=启动['onProgress'] if 'onProgress' in 启动 else None#可选进度
        信号=启动['signal'] if 'signal' in 启动 else None#可选取消
        try:#传输
            if 是否精确字节(正文):#精确字节
                总量=len(正文)#Blob 有总量
                可读=进度可读(正文,进度回调,信号,总量)#带进度
                初始化={'method':'POST','headers':头,'body':可读}#请求
                响应=执行fetch(网址,初始化)#发出
                回传({'kind':'complete','status':响应['status'],'body':响应['body'] or ''})#完成
                return#Blob 支结束
            if not 是否流式正文(正文):#非法体
                回传({'kind':'error','message':'background upload worker received an invalid body'})#回传错误
                return#结束
            def 流进度(进度):#转发进度
                """无总量。"""
                回传({'kind':'progress','loaded':进度['loaded']})#报告
            可读=进度可读(正文,流进度,信号,None)#转发流
            初始化={'method':'POST','headers':头,'body':可读}#请求
            响应=执行fetch(网址,初始化)#发出
            回传({'kind':'complete','status':响应['status'],'body':响应['body'] or ''})#完成
        except Exception as 错误:#传输失败
            消息=错误.args[0] if len(错误.args)>0 else str(错误)#消息
            回传({'kind':'error','message':消息})#结束回传
    return 处理启动#入口

def 取全局钩子():#读启动前钩子
    """builtins.__DSH_FILE_UPLOAD__；宿主可选注入。"""
    try:#可选钩子
        return builtins.__DSH_FILE_UPLOAD__#钩子
    except AttributeError:#未注入
        return None#无

def 是否夹具页():#是否 fixture 页
    """URL 带 fixture 查询。"""
    try:#宿主可选 location
        页面=builtins.location#页面
    except AttributeError:#非浏览器
        return False#否
    查询=页面.search if 页面.search is not None else ''#查询串
    if 查询.startswith('?'):#带问号
        查询=查询[1:]#去掉
    return 'fixture' in parse_qs(查询)#带 fixture

def 解析网址(路径):#相对路径解析为绝对 URL
    """有页面 origin 则用，否则 http://dsh.internal。"""
    源=None#可选源
    try:#宿主可选 location
        页面=builtins.location#页面
        源=页面.origin#origin
        if not isinstance(源,str):#无
            源=None#清空
    except AttributeError:#非浏览器或无 origin
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
            'body':请求['body'],#正文
        }#基
        if 'headers' in 请求:#有头
            初始化['headers']=请求['headers']#写入
        if 'signal' in 请求:#有
            初始化['signal']=请求['signal']#写入
        if 是否流式正文(请求['body']):#流需 duplex 标记
            初始化['duplex']='half'#半双工
        响应=自定义fetch(解析网址(请求['path']),初始化)#经页面 Fetch
        状态=响应['status'] if 'status' in 响应 else 200#状态
        正文=响应['body'] if 'body' in 响应 else ''#正文
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
            'url':解析网址(请求['path']),#绝对 URL
            'body':请求['body'],#正文
            'headers':请求['headers'] if 'headers' in 请求 and 请求['headers'] is not None else {},#头
            'onProgress':请求['onProgress'] if 'onProgress' in 请求 else None,#进度
            'signal':请求['signal'] if 'signal' in 请求 else None,#取消
        }#结束 message
        错误盒={'v':None}#线程错误
        def 执行上传():#线程入口
            """跑工作体。"""
            try:#执行
                处理(启动)#启动
            except Exception as 错误:#脚本错误
                错误盒['v']=错误#记下
                回传({'kind':'error','message':str(错误) or 'background upload worker failed'})#拒绝
        线=threading.Thread(target=执行上传,daemon=True,name='dsh-file-upload')#建线程
        线.start()#启动
        信号=请求['signal'] if 'signal' in 请求 else None#取消
        若已中止则抛出(信号)#已取消
        while True:#等到完成
            若已中止则抛出(信号)#取消
            唤醒.wait(0.05)#短等
            唤醒.clear()#清
            with 锁:#持锁
                while len(出箱)>0:#排空
                    输出=出箱.pop(0)#取出
                    if 输出['kind']=='progress':#进度
                        回调=请求['onProgress'] if 'onProgress' in 请求 else None#观察者
                        if 回调 is not None:#有
                            进度={'loaded':输出['loaded']}#已传
                            if 'total' in 输出:#可选总量
                                进度['total']=输出['total']#总量
                            回调(进度)#报告
                    elif 输出['kind']=='complete':#完成
                        return {'status':输出['status'],'body':输出['body']}#兑现
                    else:#错误
                        消息=输出['message'] if 'message' in 输出 else 'background upload transport failed'#消息
                        raise 文件上传错误(消息)#拒绝
            if not 线.is_alive() and len(出箱)==0:#线程已死且无消息
                if 错误盒['v'] is not None:#有错
                    raise 错误盒['v']#抛
                raise 文件上传错误('background upload worker failed')#失败
            time.sleep(0.01)#让出
    return {'post':投递}#transport

def 是否普通对象(值):#是否普通对象
    """非 null 非数组对象。"""
    return isinstance(值,dict)#映射即记录

def 解析文件上传结果(正文):#解析 JSON 结果
    """成功 RemoteResult 或失败 RemoteError。"""
    值=json.loads(正文)#解析
    成功=值['ok'] if 是否普通对象(值) and 'ok' in 值 else None#ok
    if 是否普通对象(值) is False or isinstance(成功,bool) is False:#形态不对
        raise TypeError('文件上传传输返回了非法结果')#类型错误
    if 成功 is False:#失败支
        错误=值['error'] if 'error' in 值 else None#错误字段
        码=错误['code'] if 是否普通对象(错误) and 'code' in 错误 else None#码
        消息=错误['message'] if 是否普通对象(错误) and 'message' in 错误 else None#消息
        细节=错误['details'] if 是否普通对象(错误) and 'details' in 错误 else None#细节
        if isinstance(码,str) is False or isinstance(消息,str) is False or 是否普通对象(细节) is False:#失败形态不对
            raise TypeError('文件上传传输返回了非法失败')#类型错误
        return {#失败
            'ok':False,#失败
            'error':远程错误(码,消息,细节),#Remote 错误
        }#结束失败返回
    结果=值['value'] if 'value' in 值 else None#成功值
    文件=结果['file'] if 是否普通对象(结果) and 'file' in 结果 else None#文件字段
    字节=文件['bytes'] if 是否普通对象(文件) and 'bytes' in 文件 else None#字节数
    凭证=结果['receiptId'] if 是否普通对象(结果) and 'receiptId' in 结果 else None#凭证
    附件=文件['attachmentId'] if 是否普通对象(文件) and 'attachmentId' in 文件 else None#附件
    叶名=文件['name'] if 是否普通对象(文件) and 'name' in 文件 else None#叶名
    if (isinstance(凭证,str) is False or 是否普通对象(文件) is False
        or isinstance(附件,str) is False or isinstance(叶名,str) is False
        or isinstance(字节,bool) or isinstance(字节,int) is False or 字节<0):#凭证形态不对
        raise TypeError('文件上传传输返回了非法回执')#类型错误
    return {#成功
        'ok':True,#成功
        'value':{#值
            'receiptId':结果['receiptId'],#凭证 id
            'file':{#文件
                'attachmentId':文件['attachmentId'],#附件 id
                'name':文件['name'],#叶名
                'bytes':字节,#字节数
            },#结束 file
        },#结束 value
    }#结束成功返回

class 文件上传运行时(服务):#上传运行时
    """每次上传操作拥有一个后台载体的 Cordis 服务。"""
    def __init__(自身,上下文):#构造
        """提供方客户端上下文。"""
        super().__init__(上下文,'fileUpload')#登记服务名
        钩子=取全局钩子()#启动前钩子
        自身.可用=钩子 is not None or (not 是否夹具页())#fixture 且无钩子则不可用
        if 钩子 is None:#无钩子
            自身._载体=线程载体()#线程载体
        else:#有钩子
            自身._载体=自定义载体(钩子['fetch'])#页面载体

    def 投递(自身,请求):#投递
        """用 Cordis 启动前选定的载体投递一次请求体。"""
        if not 自身.可用:#fixture 不可用
            raise 文件上传错误('background upload is unavailable in fixture mode')#拒绝
        return 自身._载体['post'](请求)#委托载体

    def 上传(自身,会话标识,数据,名=None,信号=None,进度回调=None):#上传入口
        """为一个 Session 存储一个文件。"""
        if (not 是否精确字节(数据)) and 自身.可用:#非精确字节且有后台载体
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
            if 响应['status']!=200:#传输层失败
                raise 文件上传错误('file upload transport failed with HTTP '+str(响应['status']))#抛错
            return 解析文件上传结果(响应['body'])#解析 JSON 结果
        if (not 是否精确字节(数据)) and 是否流式正文(数据):#流却无载体
            raise 文件上传错误('stream file upload requires a background carrier')#必须有载体
        字节=物化字节(数据)#聚合成精确字节
        上传面=自身.ctx.remote.fileUploads.upload#编码 Remote 上传
        请求体={'data':字节转base64(字节)}#编码
        if 名 is not None:#可选名
            请求体['name']=名#写入
        return 上传面(会话标识,请求体,信号)#Remote 兜底
