"""`ExaSearchProvider`：由 Exa 搜索 API 支持的 `WebSearchProvider`（`POST /search`，带 highlight 内容）。把第一条非空白 highlight 映射为 `snippet`，把 `publishedDate` 映射为 `publishedAt`，丢掉没有摘要的条目，并省略 `content`，因为 Exa 不返回生成的回答。"""
import json,threading#JSON编解码与中止监视线程
from http.client import HTTPSConnection as 安全连接,HTTPConnection as 明文连接#HTTP客户端
from urllib.parse import urlparse as 解析网址#拆基址
from web.类型 import 网络错误#web能力错误
编码=json.dumps#JSON编码
解码=json.loads#JSON解码
线程=threading.Thread#工作线程

提供方标识='exa'#本提供方注册所用的稳定 id
默认基址='https://api.exa.ai'#默认 Exa 搜索端点；操作是 /search
默认检索模式='auto'#默认检索模式：让 Exa 在关键词与神经搜索之间挑选
默认每条高亮数=1#每条结果默认请求的 highlight 句子数
归属头='deepseek-harness/0.0.1'#每个请求发送的归属头；随包版本递增

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 映射Exa结果(结果):#一条 Exa 结果投影为规范化来源
    """把一条 Exa 结果映射成规范化来源；没有可移植摘要时为 None（没有 highlight 的条目丢掉——缝没有其它字段可推导摘要，编造会撒谎）。"""
    高亮们=取字段(结果,'highlights')#可选高亮句子
    摘要=None#第一条非空白 highlight
    if 高亮们 is not None:#有高亮列表
        for 高亮 in 高亮们:#逐条找
            if isinstance(高亮,str) and len(高亮.strip())>0:#非空白
                摘要=高亮#收下
                break#只用第一条
    if 摘要 is None:#没有摘要则丢掉
        return None#无法移植
    来源={'url':取字段(结果,'url'),'snippet':摘要}#必填 URL 与摘要
    标题=取字段(结果,'title')#可选标题
    if 标题 is not None and isinstance(标题,str) and len(标题)>0:#非空标题
        来源['title']=标题#带上
    发布=取字段(结果,'publishedDate')#可选发布日期
    if 发布 is not None and isinstance(发布,str) and len(发布)>0:#非空发布日期
        来源['publishedAt']=发布#映射为 publishedAt
    return 来源#规范化来源

def 映射Exa响应(响应):#信封映射成缝结果
    """把 Exa 响应信封映射成规范化搜索结果；无摘要的条目已丢掉。"""
    原始=取字段(响应,'results')#扁平结果列表
    if 原始 is None:#缺 results 当空数组
        原始=[]#空
    来源们=[]#过滤后的来源
    for 条目 in 原始:#逐条投影
        来源=映射Exa结果(条目)#投影
        if 来源 is not None:#有摘要才留
            来源们.append(来源)#收下
    return {'sources':来源们,'truncated':False}#Exa 不返回生成回答，故省略 content；最终 maxResults 截断由 web 服务拥有，本提供方报 truncated: false

def 基址合法(基址):#基址是否可解析为绝对 URL
    """`baseURL` 能解析为绝对 URL 则为真（廉价的本地配置检查）。"""
    if not isinstance(基址,str) or len(基址)==0:#空串非法
        return False#非法
    try:#urlparse 不抛对大多数字串；用 scheme+netloc 判定绝对 URL
        解析=解析网址(基址)#拆 URL
        return len(解析.scheme)>0 and len(解析.netloc)>0#有协议与主机
    except Exception:#畸形输入
        return False#非法

def 是正整数(值):#是否可发给 Exa 的正整数上限
    """可以发给 Exa 的请求上限（正整数）则为真。"""
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

class Exa搜索提供方:#Exa 支持的搜索提供方；HTTP 重定向以 WEB_PROVIDER_ERROR 失败
    """Exa 支持的搜索提供方；HTTP 重定向以 WEB_PROVIDER_ERROR 失败。"""
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
        if not 是正整数(自身.选项['highlightsPerResult']):#highlight 数非法
            return False#不可用
        条数=自身.选项.get('numResults')#可选默认条数
        if 条数 is not None and not 是正整数(条数):#条数设了但非法
            return False#不可用
        return True#可用

    available=可用#协议字段

    def 搜索(自身,请求,信号=None):#执行一次搜索
        """执行一次搜索；请求层 maxResults 优先于配置默认 numResults；二者都可以缺席。"""
        条数=取字段(请求,'maxResults')#每次请求的上限
        if 条数 is None:#请求未带
            条数=自身.选项.get('numResults')#配置默认
        体={#请求体
            'query':取字段(请求,'query'),#查询
            'type':自身.选项['searchType'],#检索模式
            'contents':{'highlights':{'highlightsPerUrl':自身.选项['highlightsPerResult']}},#要 highlight
        }#体骨架
        if 条数 is not None:#有条数才带
            体['numResults']=条数#发给 Exa
        网址=自身.选项['baseURL'].rstrip('/')+'/search'#拼 /search
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
                    raise 网络错误('Exa search aborted','WEB_ABORTED')#取消
            路径=解析.path or '/'#路径
            if 解析.query:#有查询串
                路径=路径+'?'+解析.query#拼上
            客户端.request('POST',路径,body=载荷,headers=头)#发出 POST
            响应=客户端.getresponse()#上游响应
        except 网络错误:#已是 web 错误
            raise#原样抛
        except Exception as 错误:#网络或中止
            if 是否中止错误(错误) or 信号已中止(信号):#取消
                raise 网络错误('Exa search aborted','WEB_ABORTED',{'cause':错误})#取消
            raise 网络错误('Exa search request failed: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#网络失败
        if not (200<=响应.status<300):#HTTP 错误（含未跟随的重定向）
            状态=响应.status#状态码
            消息='Exa API error (HTTP '+str(状态)+')'#默认消息
            try:#尝试读错误体
                原文=响应.read()#原始字节
                解析错=解码(原文.decode('utf-8'))#解析 JSON
                详情=取字段(解析错,'error')#错误字段
                if 详情 is None:#没有 error
                    详情=取字段(解析错,'message')#文案字段
                if 详情 is not None and isinstance(详情,str) and len(详情)>0:#有详情则替换
                    消息=详情#提供方消息
            except Exception as 错误:#读错误体失败
                if 是否中止错误(错误) or 信号已中止(信号):#读到一半被取消必须报 WEB_ABORTED，不能吞进泛化 HTTP 错误——取消不是提供方错误（缝的取消约定）
                    raise 网络错误('Exa search aborted','WEB_ABORTED',{'cause':错误})#取消
                #否则：HTTP 状态已记在上面的 message 里；畸形/非 JSON 错误体（网关 5xx/429 常见）最多丢掉更丰富的提供方消息，不会丢掉真正的错误。
            raise 网络错误(消息,'WEB_PROVIDER_ERROR')#以提供方错误抛出
        try:#解析并映射成功体
            原文=响应.read()#原始字节
            载荷体=解码(原文.decode('utf-8'))#解析 JSON
            return 映射Exa响应(载荷体)#映射成缝结果
        except Exception as 错误:#解析失败
            if 是否中止错误(错误) or 信号已中止(信号):#取消
                raise 网络错误('Exa search aborted','WEB_ABORTED',{'cause':错误})#取消
            raise 网络错误('Exa returned an unprocessable response body: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#无法处理的正文

    search=搜索#协议字段
