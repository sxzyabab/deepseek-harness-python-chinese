"""`ExaSearchProvider`：由 Exa 搜索 API 支持的 `WebSearchProvider`（`POST /search`，带 highlight 内容）。把第一条非空白 highlight 映射为 `snippet`，把 `publishedDate` 映射为 `publishedAt`，丢掉没有摘要的条目，并省略 `content`，因为 Exa 不返回生成的回答。"""
import json,threading#JSON编解码与中止监视线程
from json import JSONDecodeError as JSON解码错误#线协议 JSON 解析失败
from http.client import HTTPSConnection as 安全连接,HTTPConnection as 明文连接,HTTPException as HTTP异常#HTTP客户端
from urllib.parse import urlparse as 解析网址#拆基址
from ..web.类型 import 网络错误#web能力错误

提供方标识='exa'#本提供方注册所用的稳定 id
默认基址='https://api.exa.ai'#默认 Exa 搜索端点；操作是 /search
默认检索模式='auto'#默认检索模式：让 Exa 在关键词与神经搜索之间挑选
默认每条高亮数=1#每条结果默认请求的 highlight 句子数
归属头='deepseek-harness/0.0.1'#每个请求发送的归属头；随包版本递增
线程=threading.Thread#工作线程

def 已中止(信号):#调用方 Event 是否已置位
    """调用方中止信号是否已置位。信号是 threading.Event，缺席视为未中止。"""
    if 信号 is None:#没有信号
        return False#未中止
    return 信号.is_set()#Event 置位即中止

def 等待信号(信号):#阻塞到信号中止
    """阻塞到 threading.Event 置位。"""
    信号.wait()#标准库 Event.wait

def 映射Exa结果(结果):#一条 Exa 结果投影为规范化来源
    """把一条 Exa 结果映射成规范化来源；没有可移植摘要时为 None。结果为 dict。"""
    高亮列表=结果['highlights'] if 'highlights' in 结果 else None#可选高亮句子
    摘要=None#第一条非空白 highlight
    if 高亮列表 is not None:#有高亮列表
        for 高亮 in 高亮列表:#逐条找
            if isinstance(高亮,str) and len(高亮.strip())>0:#判 length：非空白
                摘要=高亮#收下
                break#只用第一条
    if 摘要 is None:#没有摘要则丢掉
        return None#无法移植
    来源={'url':结果['url'],'snippet':摘要}#必填 URL 与摘要
    if 'title' in 结果:#可选标题
        标题=结果['title']#标题
        if 标题 is not None and isinstance(标题,str) and len(标题)>0:#判 length：非空标题
            来源['title']=标题#带上
    if 'publishedDate' in 结果:#可选发布日期
        发布=结果['publishedDate']#发布
        if 发布 is not None and isinstance(发布,str) and len(发布)>0:#判 length：非空发布日期
            来源['publishedAt']=发布#映射为 publishedAt
    return 来源#规范化来源

def 映射Exa响应(响应):#信封映射成缝结果
    """把 Exa 响应信封映射成规范化搜索结果；无摘要的条目已丢掉。响应为 dict。"""
    原始=响应['results'] if 'results' in 响应 else []#扁平结果列表，缺席当空
    if 原始 is None:#显式 null 当空数组
        原始=[]#空
    来源列表=[]#过滤后的来源
    for 条目 in 原始:#逐条投影
        来源=映射Exa结果(条目)#投影
        if 来源 is not None:#有摘要才留
            来源列表.append(来源)#收下
    return {'sources':来源列表,'truncated':False}#Exa 不返回生成回答，故省略 content

def 基址合法(基址):#基址是否可解析为绝对 URL
    """`baseURL` 能解析为绝对 URL 则为真。urlparse 对字串不抛。"""
    if not isinstance(基址,str) or len(基址)==0:#判 length：空串非法
        return False#非法
    解析=解析网址(基址)#拆 URL
    return len(解析.scheme)>0 and len(解析.netloc)>0#有协议与主机

class Exa搜索提供方:#Exa 支持的搜索提供方；HTTP 重定向以 WEB_PROVIDER_ERROR 失败
    """Exa 支持的搜索提供方。选项与请求为 dict。协议槽 available/search/id 按字面量留给缝读取。"""
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
        高亮=自身.选项['highlightsPerResult']#highlight 数
        if isinstance(高亮,bool) or not isinstance(高亮,int) or 高亮<1:#先排除 bool
            return False#不可用
        if 'numResults' in 自身.选项:#可选默认条数
            条数=自身.选项['numResults']#条数
            if 条数 is not None and (isinstance(条数,bool) or not isinstance(条数,int) or 条数<1):#设了但非法
                return False#不可用
        return True#可用

    def search(自身,请求,信号=None):#执行一次搜索
        """执行一次搜索；请求层 maxResults 优先于配置默认 numResults；二者都可以缺席。请求为 dict。"""
        if 'maxResults' in 请求:#请求层优先
            条数=请求['maxResults']#每次请求的上限
        elif 'numResults' in 自身.选项:#配置默认
            条数=自身.选项['numResults']#配置默认
        else:#都缺席
            条数=None#不带 numResults 键
        体={#请求体；键名是线协议
            'query':请求['query'],#查询
            'type':自身.选项['searchType'],#检索模式
            'contents':{'highlights':{'highlightsPerUrl':自身.选项['highlightsPerResult']}},#要 highlight
        }#体骨架
        if 条数 is not None:#有条数才带；0 会发出，不按 || 吞
            体['numResults']=条数#发给 Exa
        网址=自身.选项['baseURL'].rstrip('/')+'/search'#拼 /search
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
                    raise 网络错误('Exa search aborted','WEB_ABORTED')#取消
            路径=解析.path if len(解析.path)>0 else '/'#路径；判 length
            if len(解析.query)>0:#判 length：有查询串
                路径=路径+'?'+解析.query#拼上
            客户端.request('POST',路径,body=载荷,headers=头)#发出 POST
            响应=客户端.getresponse()#上游响应
        except 网络错误:#已是 web 错误
            raise#原样抛
        except (OSError,HTTP异常,TimeoutError) as 错误:#网络或中止
            if 已中止(信号):#取消
                raise 网络错误('Exa search aborted','WEB_ABORTED',{'cause':错误})#取消
            raise 网络错误('Exa search request failed: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#网络失败
        if not (200<=响应.status<300):#HTTP 错误（含未跟随的重定向）
            状态=响应.status#状态码
            消息='Exa API error (HTTP '+str(状态)+')'#默认消息
            try:#尝试读错误体
                原文=响应.read()#原始字节
                解析错=json.loads(原文.decode('utf-8'))#解析 JSON
                if 'error' in 解析错 and 解析错['error'] is not None:#有 error
                    详情=解析错['error']#错误字段
                elif 'message' in 解析错:#文案字段
                    详情=解析错['message']#文案
                else:#没有
                    详情=None#无详情
                if 详情 is not None and isinstance(详情,str) and len(详情)>0:#判 length：有详情则替换
                    消息=详情#提供方消息
            except (JSON解码错误,UnicodeDecodeError,OSError) as 错误:#读错误体失败
                if 已中止(信号):#读到一半被取消必须报 WEB_ABORTED
                    raise 网络错误('Exa search aborted','WEB_ABORTED',{'cause':错误})#取消
                #否则：HTTP 状态已记在上面的 message 里；畸形/非 JSON 错误体最多丢掉更丰富的提供方消息
            raise 网络错误(消息,'WEB_PROVIDER_ERROR')#以提供方错误抛出
        try:#解析并映射成功体
            原文=响应.read()#原始字节
            载荷体=json.loads(原文.decode('utf-8'))#解析 JSON
            return 映射Exa响应(载荷体)#映射成缝结果
        except 网络错误:#映射路径若抛网络错误
            raise#原样
        except (JSON解码错误,UnicodeDecodeError,OSError,KeyError,TypeError) as 错误:#解析失败
            if 已中止(信号):#取消
                raise 网络错误('Exa search aborted','WEB_ABORTED',{'cause':错误})#取消
            raise 网络错误('Exa returned an unprocessable response body: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#无法处理的正文
