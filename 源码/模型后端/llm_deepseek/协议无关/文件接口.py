"""DeepSeek Files API 传输，覆盖对话补全与消息端点。"""
import json,re,time,uuid#JSON、配额正则、时钟与 multipart 边界
from http.client import HTTPSConnection as 安全连接,HTTPConnection as 明文连接,HTTPException as 超文本异常#HTTP
from urllib.parse import quote as 百分编码,urlparse as 解析网址,urlencode as 编码查询#URL
from ...llm import 归属头,大模型错误#归属头与 LLM 错误
from .文件标识 import 深求文件标识#文件 id
from .消息接口 import 消息文件测试版头 as 消息文件测试版,消息接口根#Messages API

__all__=(#仅中文公开名
    '消息文件测试版','最小文件过期秒','最大文件过期秒','最大文件上传字节',
    '最大存储文件数','最大存储文件字节',
    '深求文件错误','是否文件配额错误','深求文件客户端',
)#公开面结束

最小文件过期秒=3600#最小过期秒
最大文件过期秒=2592000#最大过期秒
最大文件上传字节=128*1024*1024#最大上传字节
最大存储文件数=10000#最大存储文件数
最大存储文件字节=25*1024*1024*1024#最大存储字节
配额措辞=re.compile(r'(?:quota|storage|stored files|file count|too many files)',re.I|re.ASCII)#配额措辞

class 深求文件错误(大模型错误):#Files API 错误
    """保留 HTTP 状态供恢复策略使用的 Files API 操作失败。"""
    def __init__(自身,消息,状态,细节):#构造
        """记下用户可读失败、HTTP 状态与分类细节。"""
        if 状态==401 or 状态==403:#认证
            码='AUTH'#认证
        elif 状态==429:#限流
            码='RATE_LIMIT'#限流
        elif 状态>=500:#服务端
            码='SERVER'#服务端
        else:#其余 Files
            码='FILES_API'#Files
        super().__init__(消息,码,{'status':状态})#基类
        自身.name='DeepSeekFilesError'#类名
        自身.detail=细节#细节

def 是否文件配额错误(错误):#是否配额错误
    """上传失败是否报告提供方存储或文件数配额。"""
    return isinstance(错误,深求文件错误) and 配额措辞.search(错误.detail or '') is not None#配额

def 非法响应(操作):#非法响应
    """构造非法响应错误。"""
    return 大模型错误('DeepSeek Files API returned an invalid '+操作+' response.','INVALID_RESPONSE')#非法

def 解析文件对象(值,操作):#解析文件对象
    """校验并拆离对话补全线路文件对象。"""
    if 值 is None or not isinstance(值,dict):#形态
        raise 非法响应(操作)#非法
    标识=值.get('id')#id
    字节=值.get('bytes')#字节
    创建=值.get('created_at')#创建
    文件名=值.get('filename')#文件名
    用途=值.get('purpose')#用途
    过期=值.get('expires_at')#过期
    if (not isinstance(标识,str) or len(标识)==0
        or 值.get('object')!='file'
        or isinstance(字节,bool) or not isinstance(字节,int) or 字节<0
        or isinstance(创建,bool) or not isinstance(创建,int) or 创建<0
        or not isinstance(文件名,str) or len(文件名)==0
        or 用途!='user_data'
        or (过期 is not None and (isinstance(过期,bool) or not isinstance(过期,int) or 过期<0))):#非法
        raise 非法响应(操作)#非法
    结果={
        'id':深求文件标识(标识),#文件 id
        'bytes':字节,#字节
        'createdAt':创建,#创建时间
        'filename':文件名,#文件名
        'purpose':'user_data',#用途
    }#基
    if 过期 is not None:#有过期
        结果['expiresAt']=过期#过期
    return 结果#文件对象

def 解析消息文件(值,操作):#解析消息线路文件
    """归一化消息线路对象，不把省略过期解读成永久。"""
    if 值 is None or not isinstance(值,dict):#形态
        raise 非法响应(操作)#非法
    创建原文=值.get('created_at')#创建
    if not isinstance(创建原文,str):#必须是 ISO 串
        raise 非法响应(操作)#非法
    try:#解析
        创建=int(time.mktime(time.strptime(创建原文[:19],'%Y-%m-%dT%H:%M:%S')))#秒
    except (ValueError,OverflowError,TypeError):#无法解析
        raise 非法响应(操作)#非法
    if 值.get('type')!='file' or not isinstance(值.get('mime_type'),str):#形态
        raise 非法响应(操作)#非法
    return 解析文件对象({
        'id':值.get('id'),'object':'file','bytes':值.get('size_bytes'),'created_at':创建,
        'filename':值.get('filename'),'purpose':'user_data',
    },操作)#按对话补全形状再校验

def 提供方错误细节(值):#提供方错误细节
    """从错误体抽出 message 与拼接 detail。"""
    if 值 is None or not isinstance(值,dict):#非对象
        return {'detail':''}#空
    错误=值.get('error')#错误字段
    if 错误 is None or not isinstance(错误,dict):#非对象
        return {'detail':''}#空
    消息=错误.get('message') if isinstance(错误.get('message'),str) else None#消息
    片段=[]#字段
    for 键 in ('code','type','message'):#顺序
        字段=错误.get(键)#字段
        if isinstance(字段,str):#字符串
            片段.append(字段)#收下
    结果={'detail':' '.join(片段)}#细节
    if 消息 is not None:#有消息
        结果['message']=消息#消息
    return 结果#结果

def 组multipart(字段,文件字段):#组 multipart 体
    """组装 multipart/form-data 字节与 Content-Type。"""
    边界='----dsh'+uuid.uuid4().hex#边界
    块=[]#部件
    for 名,值 in 字段:#普通字段
        块.append(('--'+边界+'\r\nContent-Disposition: form-data; name="'+名+'"\r\n\r\n'+str(值)+'\r\n').encode('utf-8'))#字段
    名,数据,媒体类型,文件名=文件字段#文件
    头='--'+边界+'\r\nContent-Disposition: form-data; name="'+名+'"; filename="'+文件名+'"\r\nContent-Type: '+媒体类型+'\r\n\r\n'#文件头
    块.append(头.encode('utf-8'))#头
    块.append(bytes(数据) if not isinstance(数据,bytes) else 数据)#数据
    块.append(b'\r\n')#换行
    块.append(('--'+边界+'--\r\n').encode('utf-8'))#收尾
    return b''.join(块),'multipart/form-data; boundary='+边界#体与类型

class 深求文件客户端:#Files 客户端
    """按已配置 URL 根发 Files 请求，拒绝重定向以免凭证离源。"""
    def __init__(自身,选项):#构造
        """记下端点、API 密钥快照、协议与可选传输。"""
        自身.接口密钥=选项['apiKey']#密钥
        自身.协议=选项['protocol']#线路协议
        if 自身.协议=='messages':#消息
            自身.基址=消息接口根(选项['baseURL'])#Messages API 根
        else:#对话补全
            自身.基址=选项['baseURL'].rstrip('/')#去尾斜杠
        自身.路径='/files'#资源路径
        自身.取传输=选项.get('fetch')#可选自定义；缺省用 http.client

    def 解析文件(自身,值,操作):#按协议解析
        """按当前协议解析文件对象。"""
        if 自身.协议=='messages':#消息
            return 解析消息文件(值,操作)#消息形状
        return 解析文件对象(值,操作)#对话补全形状

    def 请求(自身,路径,方法,体=None,头覆盖=None,信号=None):#请求
        """发一次 Files API 请求并返回已读正文与状态。"""
        if 信号 is not None and 信号.is_set():#已中止
            原因=getattr(信号,'原因',None)#原因
            if callable(getattr(信号,'取原因',None)):#本包信号
                原因=信号.取原因()#读取
            if isinstance(原因,BaseException):#异常
                raise 原因#原样
            raise 大模型错误(str(原因) if 原因 is not None else 'aborted','ABORTED')#中止
        网址=自身.基址+路径#完整 URL
        解析=解析网址(网址)#拆
        头=dict(归属头())#归属
        if 自身.协议=='messages':#消息认证
            头['x-api-key']=自身.接口密钥#密钥
            头['anthropic-version']='2023-06-01'#版本
            头['anthropic-beta']=消息文件测试版#测试版
        else:#对话补全
            头['authorization']='Bearer '+自身.接口密钥#bearer
        if 头覆盖:#覆盖
            头.update(头覆盖)#合并
        try:#传输
            if 解析.scheme=='https':#安全
                客户端=安全连接(解析.hostname,解析.port)#HTTPS
            else:#明文
                客户端=明文连接(解析.hostname,解析.port)#HTTP
            请求路径=解析.path+(('?'+解析.query) if 解析.query else '')#路径
            if not 请求路径:#空
                请求路径='/'#根
            客户端.request(方法,请求路径,body=体,headers=头)#发
            响应=客户端.getresponse()#收
            原文=响应.read()#体
            状态=响应.status#状态
            客户端.close()#关
        except (OSError,超文本异常,大模型错误,RuntimeError) as 错误:#传输失败
            if 信号 is not None and 信号.is_set():#中止
                raise 错误#原样
            raise 大模型错误('DeepSeek Files API request to '+自身.基址+' failed','TRANSPORT',{'cause':错误}) from 错误#传输
        if 状态>=200 and 状态<300:#成功
            return 状态,原文#正文
        解析体=None#可选 JSON
        try:#解析错误体
            解析体=json.loads(原文.decode('utf-8'))#JSON
        except (json.JSONDecodeError,UnicodeDecodeError,TypeError,ValueError):#非 JSON
            pass#状态仍够
        细节=提供方错误细节(解析体)#细节
        raise 深求文件错误(
            细节.get('message') or 'DeepSeek Files API error (HTTP '+str(状态)+')',#消息
            状态,#状态
            细节['detail'],#细节
        )#抛出

    def 上传(自身,输入):#上传
        """上传一张带显式过期的图。"""
        数据=输入['data']#字节
        if len(数据)>最大文件上传字节:#超限
            raise 大模型错误('DeepSeek Files API upload exceeds 128 MiB.','INVALID_REQUEST')#超限
        过期秒=输入['expiresAfterSeconds']#过期秒
        if (isinstance(过期秒,bool) or not isinstance(过期秒,int)
            or 过期秒<最小文件过期秒 or 过期秒>最大文件过期秒):#非法寿命
            raise 大模型错误('DeepSeek file expiry must be between 3600 and 2592000 seconds.','INVALID_REQUEST')#非法
        字段=[
            ('expires_after[anchor]','created_at'),#锚点
            ('expires_after[seconds]',str(过期秒)),#秒
        ]#字段
        if 自身.协议=='chat-completions':#对话补全才带用途
            字段.insert(0,('purpose','user_data'))#用途
        体,类型=组multipart(字段,('file',数据,输入['mediaType'],输入['filename']))#multipart
        _,原文=自身.请求(自身.路径,'POST',体,{'content-type':类型},输入.get('signal'))#上传
        try:#解析
            文件=自身.解析文件(json.loads(原文.decode('utf-8')),'upload')#文件
        except 大模型错误:#原样
            raise#原样
        except (json.JSONDecodeError,UnicodeDecodeError,TypeError,ValueError,KeyError):#非法
            raise 非法响应('upload')#非法
        if 自身.协议=='messages':#消息省略过期
            文件['expiresAt']=文件['createdAt']+过期秒#按请求寿命合成
            return 文件#含合成过期
        if 'expiresAt' not in 文件:#必须有过期
            raise 非法响应('upload')#非法
        return 文件#含 expiresAt

    def 列出(自身,选项=None):#列出
        """列出一页文件。排序仅对话补全生效。"""
        if 选项 is None:#缺省
            选项={}#空
        if 自身.协议=='messages':#消息
            查询={}#消息自有页序
            if 'after' in 选项 and 选项['after'] is not None:#分页
                查询['after_id']=选项['after']#after_id
        else:#对话补全
            查询={'purpose':'user_data'}#用途
            if 'after' in 选项 and 选项['after'] is not None:#分页
                查询['after']=选项['after']#after
            if 'order' in 选项 and 选项['order'] is not None:#顺序
                查询['order']=选项['order']#order
        if 'limit' in 选项 and 选项['limit'] is not None:#上限
            查询['limit']=str(选项['limit'])#limit
        _,原文=自身.请求(自身.路径+'?'+编码查询(查询),'GET',信号=选项.get('signal'))#GET
        try:#解析
            值=json.loads(原文.decode('utf-8'))#JSON
        except (json.JSONDecodeError,UnicodeDecodeError,TypeError,ValueError):#非法
            raise 非法响应('list')#非法
        if 值 is None or not isinstance(值,dict):#形态
            raise 非法响应('list')#非法
        数据=值.get('data')#数据
        首页=值.get('first_id')#首页
        末页=值.get('last_id')#末页
        if 自身.协议=='messages':#消息把 null 当省略
            if 首页 is None:#省略
                首页=None#省略
            if 末页 is None:#省略
                末页=None#省略
        if ((自身.协议=='chat-completions' and 值.get('object')!='list')
            or not isinstance(数据,list)
            or not isinstance(值.get('has_more'),bool)
            or (首页 is not None and not isinstance(首页,str))
            or (末页 is not None and not isinstance(末页,str))):#非法
            raise 非法响应('list')#非法
        页={
            'data':[自身.解析文件(项,'list') for 项 in 数据],#文件表
            'hasMore':值['has_more'],#是否还有
        }#页
        if isinstance(首页,str):#首页 id
            页['firstId']=深求文件标识(首页)#品牌
        if isinstance(末页,str):#末页 id
            页['lastId']=深求文件标识(末页)#品牌
        return 页#页

    def 取回(自身,文件标识,信号=None):#取回
        """取回一个文件对象。"""
        _,原文=自身.请求(自身.路径+'/'+百分编码(文件标识,safe=''),'GET',信号=信号)#GET
        try:#解析
            return 自身.解析文件(json.loads(原文.decode('utf-8')),'retrieve')#文件
        except 大模型错误:#原样
            raise#原样
        except (json.JSONDecodeError,UnicodeDecodeError,TypeError,ValueError,KeyError):#非法
            raise 非法响应('retrieve')#非法

    def 删除(自身,文件标识,信号=None):#删除
        """删除一个提供方文件。"""
        _,原文=自身.请求(自身.路径+'/'+百分编码(文件标识,safe=''),'DELETE',信号=信号)#DELETE
        try:#解析
            值=json.loads(原文.decode('utf-8'))#JSON
        except (json.JSONDecodeError,UnicodeDecodeError,TypeError,ValueError):#非法
            raise 非法响应('delete')#非法
        if 值 is None or not isinstance(值,dict) or 值.get('id')!=文件标识:#非法
            raise 非法响应('delete')#非法
        if 自身.协议=='messages':#消息
            if 值.get('type')!='file_deleted':#必须是删除事件
                raise 非法响应('delete')#非法
        else:#对话补全
            if 值.get('object')!='file' or 值.get('deleted') is not True:#必须确认删除
                raise 非法响应('delete')#非法
