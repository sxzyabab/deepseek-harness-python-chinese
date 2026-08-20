"""经 Perplexity 的 OpenAI 兼容 chat-completions 端点做搜索。生成的回答成为 `content`；来源优先用结构化的 `search_results[]`，否则退到只有 URL 的 `citations[]`。线上格式和原生 HTTP 客户端是提供方私有的，不使用 `ctx.llm`。"""
import json,threading#JSON编解码与中止监视线程
from http.client import HTTPSConnection as 安全连接,HTTPConnection as 明文连接#HTTP客户端
from urllib.parse import urlparse as 解析网址#拆基址
from web.类型 import 网络错误#web能力错误
编码=json.dumps#JSON编码
解码=json.loads#JSON解码
线程=threading.Thread#工作线程

提供方标识='perplexity'#本提供方注册所用的稳定 id
默认基址='https://api.perplexity.ai'#默认 Perplexity 端点；操作是 /chat/completions
默认模型='sonar'#默认搜索模型
默认最大令牌=1024#生成回答 token 的默认上限
归属头='deepseek-harness/0.0.1'#每个请求发送的归属头；随包版本递增
新近窗口=('day','week','month','year')#Perplexity 接受的 search_recency_filter 新近窗口值

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 映射Perplexity结果(结果):#一条结构化结果投影为规范化来源
    """把一条结构化 Perplexity 搜索结果映射成规范化来源；空白字段省略而不是写成空串。"""
    来源={'url':取字段(结果,'url')}#必填 URL
    标题=取字段(结果,'title')#可选标题
    if 标题 is not None and isinstance(标题,str) and len(标题)>0:#非空标题
        来源['title']=标题#带上
    摘要=取字段(结果,'snippet')#可选摘要
    if 摘要 is not None and isinstance(摘要,str) and len(摘要)>0:#非空摘要
        来源['snippet']=摘要#带上
    日期=取字段(结果,'date')#可选日期
    if 日期 is not None and isinstance(日期,str) and len(日期)>0:#非空日期
        来源['publishedAt']=日期#映射为 publishedAt
    return 来源#规范化来源

def 映射Perplexity响应(响应):#信封映射成缝结果
    """把 Perplexity 响应信封映射成规范化搜索结果。优先用结构化 search_results[]；仅在没有 search_results 时退到只有 URL 的 citations[]；回答为空时省略 content。"""
    选择们=取字段(响应,'choices')#生成回答列表
    内容=None#第一条选择的回答
    if 选择们 is not None and len(选择们)>0:#有选择
        消息=取字段(选择们[0],'message')#第一条消息
        内容=取字段(消息,'content') if 消息 is not None else None#回答正文
    结构化=取字段(响应,'search_results')#结构化引用
    if 结构化 is not None:#有结构化结果则用它
        来源们=[映射Perplexity结果(条目) for 条目 in 结构化]#结构化投影
    else:#否则 URL-only citations
        引用们=取字段(响应,'citations')#仅 URL 引用
        if 引用们 is None:#缺 citations 当空
            引用们=[]#空
        来源们=[{'url':网址} for 网址 in 引用们]#URL-only 来源
    结果={'sources':来源们,'truncated':False}#截断由 web 服务做
    if 内容 is not None and isinstance(内容,str) and len(内容)>0:#非空回答
        结果['content']=内容#带上
    return 结果#缝结果

def 基址合法(基址):#基址是否可解析为绝对 URL
    """baseURL 能解析为绝对 URL 则为真（廉价的本地配置检查）。"""
    if not isinstance(基址,str) or len(基址)==0:#空串非法
        return False#非法
    try:#urlparse 不抛对大多数字串；用 scheme+netloc 判定绝对 URL
        解析=解析网址(基址)#拆 URL
        return len(解析.scheme)>0 and len(解析.netloc)>0#有协议与主机
    except Exception:#畸形输入
        return False#非法

def 是正整数(值):#是否可发给 Perplexity 的正整数上限
    """可以发给 Perplexity 的请求上限（正整数）则为真。"""
    if type(值) is int:#纯整数
        return 值>0#正
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return 值>0#正
    return False#非正整数

def 是否中止错误(错误):#是否 AbortError
    """fetch/AbortSignal 中止则为真，表现为 WEB_ABORTED。"""
    if 错误 is None:#无错误
        return False#不是
    if getattr(错误,'name',None)=='AbortError':#显式 AbortError 名
        return True#中止
    return False#其它错误

def 信号已中止(信号):#信号是否已中止
    """英文 aborted 或中文 已中止 任一为真则视为已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if getattr(信号,'aborted',False):#英文旗标
        return True#已中止
    if getattr(信号,'已中止',False):#中文旗标
        return True#已中止
    return False#未中止

def 等待信号(信号):#阻塞到信号中止
    """阻塞到信号中止；优先走等待方法。"""
    等待=getattr(信号,'等待',None)#中文等待
    if 等待 is not None:#有中文
        等待()#阻塞
        return#完成
    等待英=getattr(信号,'wait',None)#英文等待
    if 等待英 is not None:#有英文
        等待英()#阻塞
        return#完成
    while not 信号已中止(信号):#无等待则轮询
        pass#忙等

class Perplexity搜索提供方:#Perplexity 支持的搜索提供方；HTTP 重定向以 WEB_PROVIDER_ERROR 失败
    """Perplexity 支持的搜索提供方；HTTP 重定向以 WEB_PROVIDER_ERROR 失败。"""
    def __init__(自身,选项):#保存已解析选项
        """收下已解析的提供方选项（插件的 apply 提供环境变量与常量默认值）。"""
        自身.选项=选项#已解析选项
        自身.id=提供方标识#注册 id
        自身.标识=提供方标识#中文别名

    def 可用(自身):#当前选项是否足以发起搜索
        """当前选项是否足以发起搜索。"""
        密钥=自身.选项['apiKey']#API 密钥
        if not isinstance(密钥,str) or len(密钥)==0:#空密钥
            return False#不可用
        if not 基址合法(自身.选项['baseURL']):#基址不可解析
            return False#不可用
        if not 是正整数(自身.选项['maxTokens']):#maxTokens 非法
            return False#不可用
        return True#可用

    available=可用#协议字段

    def 搜索(自身,请求,信号=None):#执行一次搜索
        """执行一次搜索；查询作为用户消息发出。"""
        体={#请求体
            'model':自身.选项['model'],#模型
            'max_tokens':自身.选项['maxTokens'],#生成上限
            'messages':[{'role':'user','content':取字段(请求,'query')}],#查询作用户消息
        }#体骨架
        新近=自身.选项.get('searchRecency')#可选新近窗口
        if 新近 is not None:#有新近窗口才带
            体['search_recency_filter']=新近#发给 Perplexity
        网址=自身.选项['baseURL'].rstrip('/')+'/chat/completions'#拼 /chat/completions
        解析=解析网址(网址)#拆主机路径
        载荷=编码(体,ensure_ascii=False,separators=(',',':')).encode('utf-8')#JSON 正文
        头={#请求头
            'authorization':'Bearer '+自身.选项['apiKey'],#Bearer 密钥
            'content-type':'application/json',#JSON 体
            'accept':'application/json',#要 JSON
            'user-agent':归属头,#归属头
        }#headers 结束
        try:#发 POST；http.client 不跟随重定向，3xx 走 HTTP 错误路径
            if 解析.scheme=='https':#HTTPS
                客户端=安全连接(解析.hostname,解析.port)#安全连接
            else:#HTTP
                客户端=明文连接(解析.hostname,解析.port)#明文连接
            if 信号 is not None:#有取消信号
                def 监视中止():#信号中止时关掉套接字
                    """信号中止时关掉套接字。"""
                    等待信号(信号)#阻塞到中止
                    客户端.close()#拆传输
                线程(target=监视中止,daemon=True).start()#监视中止
                if 信号已中止(信号):#已经中止则立刻关掉
                    客户端.close()#关掉
                    raise 网络错误('Perplexity search aborted','WEB_ABORTED')#取消
            路径=解析.path or '/'#路径
            if 解析.query:#有查询串
                路径=路径+'?'+解析.query#拼上
            客户端.request('POST',路径,body=载荷,headers=头)#发出 POST
            响应=客户端.getresponse()#上游响应
        except 网络错误:#已是 web 错误
            raise#原样抛
        except Exception as 错误:#网络或中止
            if 是否中止错误(错误) or 信号已中止(信号):#取消
                raise 网络错误('Perplexity search aborted','WEB_ABORTED',{'cause':错误})#取消
            raise 网络错误('Perplexity search request failed: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#网络失败
        if not (200<=响应.status<300):#HTTP 错误（含未跟随的重定向）
            状态=响应.status#状态码
            消息='Perplexity API error (HTTP '+str(状态)+')'#默认消息
            try:#尝试读错误体
                原文=响应.read()#原始字节
                解析错=解码(原文.decode('utf-8'))#解析 JSON
                错误字段=取字段(解析错,'error')#错误字段
                if isinstance(错误字段,str):#字符串错误
                    详情=错误字段#直接用
                elif 错误字段 is not None:#嵌套对象
                    详情=取字段(错误字段,'message')#嵌套 message
                    if 详情 is None:#没有嵌套 message
                        详情=取字段(解析错,'message')#顶层文案
                else:#没有 error
                    详情=取字段(解析错,'message')#顶层文案
                if 详情 is not None and isinstance(详情,str) and len(详情)>0:#有详情则替换
                    消息=详情#提供方消息
            except Exception as 错误:#读错误体失败
                if 是否中止错误(错误) or 信号已中止(信号):#读到一半被取消必须报 WEB_ABORTED，不能吞进泛化 HTTP 错误——取消不是提供方错误（缝的取消约定）
                    raise 网络错误('Perplexity search aborted','WEB_ABORTED',{'cause':错误})#取消
                #否则：HTTP 状态已记在上面的 message 里；畸形/非 JSON 错误体（网关 5xx/429 常见）最多丢掉更丰富的提供方消息，不会丢掉真正的错误。
            raise 网络错误(消息,'WEB_PROVIDER_ERROR')#以提供方错误抛出
        try:#解析并映射成功体
            原文=响应.read()#原始字节
            载荷体=解码(原文.decode('utf-8'))#解析 JSON
            return 映射Perplexity响应(载荷体)#映射成缝结果
        except Exception as 错误:#解析失败
            if 是否中止错误(错误) or 信号已中止(信号):#取消
                raise 网络错误('Perplexity search aborted','WEB_ABORTED',{'cause':错误})#取消
            raise 网络错误('Perplexity returned an unprocessable response body: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#无法处理的正文

    search=搜索#协议字段
