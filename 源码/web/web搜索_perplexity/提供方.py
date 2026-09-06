"""经 Perplexity 的 OpenAI 兼容 chat-completions 端点做搜索。生成的回答成为 `content`；来源优先用结构化的 `search_results[]`，否则退到只有 URL 的 `citations[]`。线上格式和原生 HTTP 客户端是提供方私有的，不使用 `ctx.llm`。"""
import json,threading#JSON编解码与中止监视线程
from json import JSONDecodeError as JSON解码错误#线协议 JSON 解析失败
from http.client import HTTPSConnection as 安全连接,HTTPConnection as 明文连接,HTTPException as HTTP异常#HTTP客户端
from urllib.parse import urlparse as 解析网址#拆基址
from ..web.类型 import 网络错误#web能力错误

提供方标识='perplexity'#本提供方注册所用的稳定 id
默认基址='https://api.perplexity.ai'#默认 Perplexity 端点；操作是 /chat/completions
默认模型='sonar'#默认搜索模型
默认最大令牌=1024#生成回答 token 的默认上限
归属头='deepseek-harness/0.0.1'#每个请求发送的归属头；随包版本递增
新近窗口=('day','week','month','year')#Perplexity 接受的 search_recency_filter 新近窗口值
线程=threading.Thread#工作线程

def 已中止(信号):#调用方 Event 是否已置位
    """调用方中止信号是否已置位。信号是 threading.Event，缺席视为未中止。"""
    if 信号 is None:#没有信号
        return False#未中止
    return 信号.is_set()#Event 置位即中止

def 等待信号(信号):#阻塞到信号中止
    """阻塞到 threading.Event 置位。"""
    信号.wait()#标准库 Event.wait

def 映射Perplexity结果(结果):#一条结构化结果投影为规范化来源
    """把一条结构化 Perplexity 搜索结果映射成规范化来源；空白字段省略而不是写成空串。结果为 dict。"""
    来源={'url':结果['url']}#必填 URL
    if 'title' in 结果:#可选标题
        标题=结果['title']#标题
        if 标题 is not None and isinstance(标题,str) and len(标题)>0:#判 length：非空标题
            来源['title']=标题#带上
    if 'snippet' in 结果:#可选摘要
        摘要=结果['snippet']#摘要
        if 摘要 is not None and isinstance(摘要,str) and len(摘要)>0:#判 length：非空摘要
            来源['snippet']=摘要#带上
    if 'date' in 结果:#可选日期
        日期=结果['date']#日期
        if 日期 is not None and isinstance(日期,str) and len(日期)>0:#判 length：非空日期
            来源['publishedAt']=日期#映射为 publishedAt
    return 来源#规范化来源

def 映射Perplexity响应(响应):#信封映射成缝结果
    """把 Perplexity 响应信封映射成规范化搜索结果。响应为 dict。优先用结构化 search_results[]；仅在没有 search_results 键时退到 citations[]；回答为空时省略 content。"""
    选择列表=响应['choices'] if 'choices' in 响应 else None#生成回答列表
    内容=None#第一条选择的回答
    if 选择列表 is not None and len(选择列表)>0:#判 length：有选择
        消息=选择列表[0]['message'] if 'message' in 选择列表[0] else None#第一条消息
        if 消息 is not None and 'content' in 消息:#回答正文
            内容=消息['content']#正文
    if 'search_results' in 响应:#有结构化结果键则用它（含空列表）
        来源列表=[映射Perplexity结果(条目) for 条目 in 响应['search_results']]#结构化投影
    else:#否则 URL-only citations
        引用列表=响应['citations'] if 'citations' in 响应 else []#仅 URL 引用，缺席当空
        if 引用列表 is None:#显式 null 当空
            引用列表=[]#空
        来源列表=[{'url':网址} for 网址 in 引用列表]#URL-only 来源
    结果={'sources':来源列表,'truncated':False}#截断由 web 服务做
    if 内容 is not None and isinstance(内容,str) and len(内容)>0:#判 length：非空回答才带 content
        结果['content']=内容#带上
    return 结果#缝结果

def 基址合法(基址):#基址是否可解析为绝对 URL
    """baseURL 能解析为绝对 URL 则为真。urlparse 对字串不抛。"""
    if not isinstance(基址,str) or len(基址)==0:#判 length：空串非法
        return False#非法
    解析=解析网址(基址)#拆 URL
    return len(解析.scheme)>0 and len(解析.netloc)>0#有协议与主机

class Perplexity搜索提供方:#Perplexity 支持的搜索提供方；HTTP 重定向以 WEB_PROVIDER_ERROR 失败
    """Perplexity 支持的搜索提供方。选项与请求为 dict。协议槽 available/search/id 按字面量留给缝读取。"""
    def __init__(自身,选项):#保存已解析选项
        """收下已解析的提供方选项（插件的 apply 提供环境变量与常量默认值）。"""
        自身.选项=选项#已解析选项
        自身.id=提供方标识#协议槽 id

    def available(自身):#当前选项是否足以发起搜索
        """当前选项是否足以发起搜索。正整数校验写在本入口，先排除 bool。"""
        密钥=自身.选项['apiKey']#API 密钥
        if not isinstance(密钥,str) or len(密钥)==0:#判 length：空密钥
            return False#不可用
        if not 基址合法(自身.选项['baseURL']):#基址不可解析
            return False#不可用
        令牌=自身.选项['maxTokens']#maxTokens
        if isinstance(令牌,bool) or not isinstance(令牌,int) or 令牌<1:#先排除 bool
            return False#不可用
        return True#可用

    def search(自身,请求,信号=None):#执行一次搜索
        """执行一次搜索；查询作为用户消息发出。请求与选项为 dict。"""
        体={#请求体；键名是线协议
            'model':自身.选项['model'],#模型
            'max_tokens':自身.选项['maxTokens'],#生成上限
            'messages':[{'role':'user','content':请求['query']}],#查询作用户消息
        }#体骨架
        if 'searchRecency' in 自身.选项 and 自身.选项['searchRecency'] is not None:#有新近窗口才带
            体['search_recency_filter']=自身.选项['searchRecency']#发给 Perplexity
        网址=自身.选项['baseURL'].rstrip('/')+'/chat/completions'#拼 /chat/completions
        解析=解析网址(网址)#拆主机路径
        载荷=json.dumps(体,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')#锁三参数
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
                if 已中止(信号):#已经中止则立刻关掉
                    客户端.close()#关掉
                    raise 网络错误('Perplexity search aborted','WEB_ABORTED')#取消
            路径=解析.path if len(解析.path)>0 else '/'#路径；判 length
            if len(解析.query)>0:#判 length：有查询串
                路径=路径+'?'+解析.query#拼上
            客户端.request('POST',路径,body=载荷,headers=头)#发出 POST
            响应=客户端.getresponse()#上游响应
        except 网络错误:#已是 web 错误
            raise#原样抛
        except (OSError,HTTP异常,TimeoutError) as 错误:#网络或中止
            if 已中止(信号):#取消
                raise 网络错误('Perplexity search aborted','WEB_ABORTED',{'cause':错误})#取消
            raise 网络错误('Perplexity search request failed: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#网络失败
        if not (200<=响应.status<300):#HTTP 错误（含未跟随的重定向）
            状态=响应.status#状态码
            消息='Perplexity API error (HTTP '+str(状态)+')'#默认消息
            try:#尝试读错误体
                原文=响应.read()#原始字节
                解析错=json.loads(原文.decode('utf-8'))#解析 JSON
                if 'error' in 解析错:#有 error
                    错误字段=解析错['error']#错误字段
                    if isinstance(错误字段,str):#字符串错误
                        详情=错误字段#直接用
                    elif 错误字段 is not None and 'message' in 错误字段:#嵌套对象
                        详情=错误字段['message']#嵌套 message
                    elif 'message' in 解析错:#顶层文案
                        详情=解析错['message']#顶层
                    else:#没有
                        详情=None#无详情
                elif 'message' in 解析错:#顶层文案
                    详情=解析错['message']#顶层
                else:#没有
                    详情=None#无详情
                if 详情 is not None and isinstance(详情,str) and len(详情)>0:#判 length：有详情则替换
                    消息=详情#提供方消息
            except (JSON解码错误,UnicodeDecodeError,OSError) as 错误:#读错误体失败
                if 已中止(信号):#读到一半被取消必须报 WEB_ABORTED
                    raise 网络错误('Perplexity search aborted','WEB_ABORTED',{'cause':错误})#取消
                #否则：HTTP 状态已记在上面的 message 里；畸形/非 JSON 错误体最多丢掉更丰富的提供方消息
            raise 网络错误(消息,'WEB_PROVIDER_ERROR')#以提供方错误抛出
        try:#解析并映射成功体
            原文=响应.read()#原始字节
            载荷体=json.loads(原文.decode('utf-8'))#解析 JSON
            return 映射Perplexity响应(载荷体)#映射成缝结果
        except 网络错误:#映射若抛
            raise#原样
        except (JSON解码错误,UnicodeDecodeError,OSError,KeyError,TypeError) as 错误:#解析失败
            if 已中止(信号):#取消
                raise 网络错误('Perplexity search aborted','WEB_ABORTED',{'cause':错误})#取消
            raise 网络错误('Perplexity returned an unprocessable response body: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#无法处理的正文
