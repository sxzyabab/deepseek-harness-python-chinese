"""通过 Anthropic 兼容的 Messages 模型调用，使用原生 web_search_20250305 服务端工具做 DeepSeek 搜索。每次搜索消耗一轮模型，但返回结构化结果块；没有这些块是错误，而不是去刮散文的退路。线上格式和原生 HTTP 客户端是提供方私有的，不使用 ctx.llm。"""
import json#JSON 编解码
from json import JSONDecodeError as JSON解码错误#线协议 JSON 解析失败
from urllib.error import URLError as 网址错误#urlopen 网络失败
from urllib.parse import urlparse as 解析网址#基址可解析判定
from urllib.request import (
    Request as 请求构造,#构造请求
    build_opener as 构建打开器,#自定义打开器
    HTTPRedirectHandler as HTTP重定向处理器,#重定向处理
    HTTPErrorProcessor as HTTP错误处理器,#非 2xx 处理
)#原生 HTTP
from ..web import 网络错误#web 能力错误

提供方标识='deepseek-official'#本提供方注册所用的稳定 id
默认基址='https://api.deepseek.com/anthropic/v1'#默认 Messages 基址（含 /v1，再拼 /messages）；不是 chat-completions 的 DEEPSEEK_BASE_URL
默认模型='deepseek-v4-flash'#默认 Anthropic 格式模型名
默认接口版本='2023-06-01'#默认 anthropic-version 头
默认最大令牌=4096#Messages 请求生成 token 默认上限
默认最大使用次数=5#每次请求默认最多使用几次 web_search 服务端工具
用户代理='deepseek-harness/0.0.1'#每个请求发送的归属头；随包版本递增

class 禁止重定向(HTTP重定向处理器):#HTTP 重定向以提供方错误失败，不跟随
    """redirect:error：不跟随重定向，把 3xx 原样交给上层按非 ok 处理。"""
    def redirect_request(自身,请求,文件句柄,码,消息,头,新网址):#拒绝跟随
        """返回 None 使 urlopen 交出 3xx 响应本身。"""
        return None#不跟随

class 保留非成功(HTTP错误处理器):#对齐 fetch：非 2xx 不抛，读 status 与正文
    """不把非 2xx 抬成异常，留给调用方读状态码与错误体。"""
    def http_response(自身,请求,响应):#HTTP 响应原样返回
        """HTTP 路径原样返回响应。"""
        return 响应#不抛

    https_response=http_response#HTTPS 同路径

打开器=构建打开器(禁止重定向,保留非成功)#禁止重定向且保留非成功体

def 已中止(信号):#调用方 Event 是否已置位
    """调用方中止信号是否已置位。信号是 threading.Event，缺席视为未中止。"""
    if 信号 is None:#没有信号
        return False#未中止
    return 信号.is_set()#Event 置位即中止

def 可解析网址(文字):#对齐 URL.canParse
    """基址可解析则为真（须有 scheme 与 netloc）。urlparse 对字串不抛。"""
    if not isinstance(文字,str) or len(文字)==0:#判 length：空或非串
        return False#不可解析
    结果=解析网址(文字)#拆 URL
    return len(结果.scheme)>0 and len(结果.netloc)>0#有协议与主机

def 搜索已取消(回退=None):#构造提供方稳定的取消错误
    """构造提供方稳定的取消错误。中止原因用异常对象承载，不在信号上挂字段。"""
    if 回退 is None:#没有原因
        return 网络错误('DeepSeek search aborted','WEB_ABORTED')#稳定消息与码
    return 网络错误('DeepSeek search aborted','WEB_ABORTED',{'cause':回退})#带原因

def 若已中止则抛出(信号=None):#已取消则抛稳定错误
    """调用方已经中止时，抛出提供方稳定的取消错误。"""
    if 已中止(信号):#已中止
        raise 搜索已取消()#稳定 WEB_ABORTED

def 引用摘要映射(块列表):#从每个 text 块的 citations[] 建 url→cited_text
    """从每个 text 块的 citations[] 建 url → cited_text 映射。响应块为 dict。摘录在 text 块的 citation 里，按 url 键控（先出现的赢）。"""
    映射={}#url 到 cited_text
    if 块列表 is None:#缺 content
        return 映射#空映射
    for 块 in 块列表:#遍历内容块
        if 'type' not in 块 or 块['type']!='text':#只看文本块
            continue#跳过
        引用列表=块['citations'] if 'citations' in 块 else []#该块的 citations，缺席当空列表
        for 引用 in 引用列表:#逐条引用
            网址=引用['url'] if 'url' in 引用 else None#引用 URL
            摘录=引用['cited_text'] if 'cited_text' in 引用 else None#被引文本
            if 网址 is not None and len(网址)>0 and 摘录 is not None and len(摘录)>0 and 网址 not in 映射:#判 length：有 url 与摘录且尚未记录
                映射[网址]=摘录#先出现的赢
    return 映射#摘要映射

def 映射人机响应(响应):#把 Messages 响应映射成规范化搜索结果
    """把 DeepSeek Anthropic Messages 响应映射成规范化搜索结果。响应为 dict。web 服务拥有最终的 maxResults 截断，因此这里的 truncated 始终为 false。"""
    块列表=响应['content'] if 'content' in 响应 else []#内容块，缺席当空列表
    结果块列表=[]#只留搜索工具结果块
    for 块 in 块列表:#过滤
        if 'type' in 块 and 块['type']=='web_search_tool_result':#类型匹配
            结果块列表.append(块)#收下
    if len(结果块列表)==0:#判 length：没有原生搜索结果块
        raise 网络错误(
            'DeepSeek returned no web_search_tool_result blocks; the request may not have triggered native web search',#字面量不改
            'WEB_PROVIDER_ERROR',#提供方错误
        )#这是错误，不去刮散文
    摘要表=引用摘要映射(块列表)#url 到摘录
    已见=set()#已收 url
    来源列表=[]#规范化来源
    for 块 in 结果块列表:#每个工具结果块
        条目表=块['content'] if 'content' in 块 else []#块内条目，缺席当空
        for 条目 in 条目表:#逐条
            if 'type' not in 条目 or 条目['type']!='web_search_result':#非结果
                continue#跳过
            网址=条目['url'] if 'url' in 条目 else ''#结果 URL，缺席当空串
            if len(网址)==0 or 网址 in 已见:#判 length：空 url 或重复
                continue#跳过
            已见.add(网址)#记下 url
            来源={'url':网址}#一条来源
            if 'title' in 条目:#可选标题
                标题=条目['title']#标题
                if 标题 is not None and len(标题)>0:#判 length：非空标题
                    来源['title']=标题#带上
            if 网址 in 摘要表:#对应摘录
                摘录=摘要表[网址]#摘录
                if 摘录 is not None and len(摘录)>0:#判 length：非空摘要
                    来源['snippet']=摘录#带上
            if 'page_age' in 条目:#页面新旧
                页面新旧=条目['page_age']#日期
                if 页面新旧 is not None and len(页面新旧)>0:#判 length：非空日期
                    来源['publishedAt']=页面新旧#映射到 publishedAt
            来源列表.append(来源)#收下
    return {'sources':来源列表,'truncated':False}#截断由 web 服务做

class DeepSeek搜索提供方:#DeepSeek 支持的搜索提供方；HTTP 重定向以 WEB_PROVIDER_ERROR 失败
    """DeepSeek 搜索提供方。选项与请求为 dict。协议槽 available/search/id 按字面量留给缝读取。"""
    def __init__(自身,解析选项):#保存选项解析器
        """收下下一次操作的选项 thunk。"""
        自身.解析选项=解析选项#选项解析器
        自身.id=提供方标识#协议槽 id

    def available(自身):#当前快照是否足以发起搜索
        """廉价的本地可用性检查；不得发起网络调用。选项为 dict。正整数校验写在本入口，先排除 bool。"""
        选项=自身.解析选项()#读当前选项
        字面量=选项['apiKey'] if 'apiKey' in 选项 else None#字面量密钥
        有密钥=((字面量 is not None and len(字面量)>0) or ('resolveApiKey' in 选项 and 选项['resolveApiKey'] is not None))#判 length：有字面量或解析器
        令牌=选项['maxTokens'] if 'maxTokens' in 选项 else None#生成上限
        次数=选项['maxUses'] if 'maxUses' in 选项 else None#使用次数
        令牌合格=(not isinstance(令牌,bool)) and isinstance(令牌,int) and 令牌>0#正整数，先排除 bool
        次数合格=(not isinstance(次数,bool)) and isinstance(次数,int) and 次数>0#正整数，先排除 bool
        return 有密钥 and 可解析网址(选项['baseURL'] if 'baseURL' in 选项 else None) and 令牌合格 and 次数合格#四条件

    def search(自身,请求,信号=None):#执行一次搜索
        """跑一次搜索；用信号接受取消。请求与选项为 dict。整次操作一份快照。"""
        选项=自身.解析选项()#操作入口快照
        密钥=自身.取密钥(选项,信号)#解析密钥，不留在提供方上
        若已中止则抛出(信号)#解析后若已取消则停
        端点=选项['baseURL']+'/messages'#Messages 端点
        查询=请求['query']#查询字符串
        体={#不含密钥的请求体；键名是线协议
            'model':选项['model'],#模型
            'max_tokens':选项['maxTokens'],#生成上限
            'messages':[{#用户消息
                'role':'user',#角色
                'content':[{'type':'text','text':'Perform a web search for the query: '+查询}],#查询文本，字面量不改
            }],#messages 结束
            'tools':[{'type':'web_search_20250305','name':'web_search','max_uses':选项['maxUses']}],#原生搜索工具
        }#body 结束
        记请求=选项['recordRequest'] if 'recordRequest' in 选项 else None#日志钩子
        if 记请求 is not None:#派发前先记日志；抛错则不派发
            记请求({#不含密钥的精确请求
                'endpoint':端点,#端点
                'apiVersion':选项['apiVersion'],#API 版本
                'body':体,#请求体
            })#recordRequest 结束
        若已中止则抛出(信号)#记日志后若已取消则停
        头={#请求头：官方 DeepSeek 要 x-api-key；Anthropic 兼容代理可能要 Authorization: Bearer
            'x-api-key':密钥,#官方密钥头
            'authorization':'Bearer '+密钥,#Bearer 形式
            'anthropic-version':选项['apiVersion'],#API 版本
            'content-type':'application/json',#JSON 体
            'accept':'application/json',#要 JSON
            'user-agent':用户代理,#归属头
        }#headers 结束
        载荷=json.dumps(体,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')#锁三参数
        请求对象=请求构造(端点,data=载荷,headers=头,method='POST')#POST Messages
        try:#发 POST，重定向当错误
            响应=打开器.open(请求对象)#原生打开
        except 网络错误:#已是取消
            raise#原样抛
        except (网址错误,OSError,TimeoutError) as 错误:#网络或中止拆套接字
            if 已中止(信号):#取消
                raise 搜索已取消(错误)#取消
            raise 网络错误('DeepSeek search request failed: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#网络失败
        状态=响应.status#HTTP 状态码，int
        if 状态<200 or 状态>=300:#HTTP 错误（含未跟随的重定向）
            消息='DeepSeek API error (HTTP '+str(状态)+')'#默认消息
            try:#尝试读错误体
                原文=响应.read().decode('utf-8')#读正文
                解析=json.loads(原文)#解析 JSON
                if 'error' in 解析:#有 error 字段
                    错误字段=解析['error']#error 字段
                    if isinstance(错误字段,str):#字符串错误
                        详情=错误字段#详情
                    elif 错误字段 is not None and 'message' in 错误字段:#嵌套对象
                        详情=错误字段['message']#嵌套
                    elif 'message' in 解析:#顶层
                        详情=解析['message']#顶层
                    else:#没有文案
                        详情=None#无详情
                elif 'message' in 解析:#顶层 message
                    详情=解析['message']#顶层
                else:#没有
                    详情=None#无详情
                if 详情 is not None and len(详情)>0:#判 length：有详情则替换
                    消息=详情#替换
            except (JSON解码错误,UnicodeDecodeError,OSError) as 错误:#读错误体失败
                if 已中止(信号):#读到一半被取消必须报 WEB_ABORTED
                    raise 搜索已取消(错误)#取消不是提供方错误
                #否则：HTTP 状态已记在上面的消息里；畸形/非 JSON 错误体最多丢掉更丰富的提供方消息
            finally:
                try:#关掉响应
                    响应.close()#清理
                except OSError:#关闭失败
                    pass#状态已在消息里
            raise 网络错误(消息,'WEB_PROVIDER_ERROR')#以提供方错误抛出
        try:#解析并映射成功体
            原文=响应.read().decode('utf-8')#读正文
            载荷体=json.loads(原文)#解析 JSON
            return 映射人机响应(载荷体)#映射成缝结果
        except 网络错误:#已是网络错误（例如没有结果块）则原样抛
            raise#原样
        except (JSON解码错误,UnicodeDecodeError,OSError,KeyError,TypeError) as 错误:#解析或映射失败
            if 已中止(信号):#取消
                raise 搜索已取消(错误)#取消
            raise 网络错误('DeepSeek returned an unprocessable response body: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#无法处理的正文
        finally:
            try:#关掉响应
                响应.close()#清理
            except OSError:#关闭失败
                pass#映射路径已拥有结果或错误

    def 取密钥(自身,选项,信号=None):#解析一次操作的凭证，不把它留在提供方上
        """解析一次操作的凭证。调用方快照使密钥与发往的端点来自同一段配置。解析器已是同步。"""
        若已中止则抛出(信号)#已取消则停
        字面量=选项['apiKey'] if 'apiKey' in 选项 else None#字面量密钥
        if 字面量 is not None and len(字面量)>0:#判 length：字面量优先
            return 字面量#字面量
        解析器=选项['resolveApiKey'] if 'resolveApiKey' in 选项 else None#同步解析器
        try:#跑解析器；无解析器则得到 None（仍先查取消）
            if 解析器 is None:#没有解析器
                若已中止则抛出(信号)#对齐 abortable(Promise.resolve(undefined))
                已解析=None#无解析器
            else:
                若已中止则抛出(信号)#调用前再查
                已解析=解析器()#同步解析
                若已中止则抛出(信号)#调用后再查
        except 网络错误 as 错误:#已是网络错误
            if 错误.code=='WEB_ABORTED':#已是取消
                raise 错误#原样
            raise 网络错误(
                'DeepSeek search credential resolution failed: '+str(错误),#字面量不改
                'WEB_PROVIDER_ERROR',#提供方错误
                {'cause':错误},#保留原因
            )#凭证解析失败
        if 已解析 is not None and len(已解析)>0:#判 length：解析出非空密钥
            return 已解析#密钥
        引用=选项['apiKeyEnv'] if 'apiKeyEnv' in 选项 else None#诊断用的引用名
        if 引用 is None or len(引用)==0:#判 length：原意是 ||，空串回退默认名
            引用='DEEPSEEK_API_KEY'#默认引用名
        raise 网络错误(
            'DeepSeek search has no API key for "'+str(引用)+'"; store it through the credentials service'
            +' (the web Models page writes it), export it in the launching environment, or set a literal'
            +' "apiKey" in the web-search-deepseek config',#字面量不改
            'WEB_PROVIDER_CREDENTIAL_MISSING',#缺凭证
        )#缺密钥
