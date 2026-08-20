"""通过 Anthropic 兼容的 Messages 模型调用，使用原生 web_search_20250305 服务端工具做 DeepSeek 搜索。每次搜索消耗一轮模型，但返回结构化结果块；没有这些块是错误，而不是去刮散文的退路。线上格式和原生 HTTP 客户端是提供方私有的，不使用 ctx.llm。"""
import json,threading#JSON 编解码与可取消赛跑线程
from urllib.parse import urlparse as 解析网址#基址可解析判定
from urllib.request import (
    Request as 请求构造,#构造请求
    build_opener as 构建打开器,#自定义打开器
    HTTPRedirectHandler as HTTP重定向处理器,#重定向处理
    HTTPErrorProcessor as HTTP错误处理器,#非 2xx 处理
)#原生 HTTP
from web import 网络错误#web 能力错误
from cordis.工具 import 是否thenable#可等待判定

编码=json.dumps#JSON 编码
解码=json.loads#JSON 解码
线程=threading.Thread#工作线程
事件=threading.Event#中止赛跑事件

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

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 信号已中止(信号):#英文 aborted 或中文 已中止
    """调用方信号是否已中止。"""
    if 信号 is None:#没有信号
        return False#未中止
    if getattr(信号,'aborted',False) is True:#英文旗标
        return True#已中止
    if getattr(信号,'已中止',False) is True:#中文旗标
        return True#已中止
    return False#未中止

def 信号原因(信号,回退=None):#优先用信号原因
    """构造取消错误时保留的原因。"""
    if 信号已中止(信号):#已中止优先信号原因
        原因=getattr(信号,'reason',None)#英文原因
        if 原因 is None:#无英文
            原因=getattr(信号,'原因',None)#中文原因
        return 原因#信号原因
    return 回退#回退原因

def 是否正整数(值):#可以发给 Messages API 的上限
    """整数且大于 0 则为真。"""
    if isinstance(值,bool):#布尔不是整数
        return False#拒绝
    if isinstance(值,int):#整型
        return 值>0#正
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return 值>0#正
    return False#非正整数

def 可解析网址(文字):#对齐 URL.canParse
    """基址可解析则为真（须有 scheme 与 netloc）。"""
    if not isinstance(文字,str) or len(文字)==0:#空或非串
        return False#不可解析
    try:#解析
        结果=解析网址(文字)#拆 URL
    except Exception:#解析失败
        return False#不可解析
    return len(结果.scheme)>0 and len(结果.netloc)>0#有协议与主机

def 是否中止错误(错误):#fetch/AbortSignal 中止
    """表现为 WEB_ABORTED 的中止错误则为真。"""
    if 错误 is None:#无错误
        return False#不是
    if getattr(错误,'name',None)=='AbortError':#DOM/自建名
        return True#是中止
    return type(错误).__name__=='AbortError'#类名兜底

def 搜索已取消(信号=None,回退=None):#构造提供方稳定的取消错误
    """构造提供方稳定的取消错误，同时保留调用方原因。"""
    return 网络错误('DeepSeek search aborted','WEB_ABORTED',{'cause':信号原因(信号,回退)})#稳定消息与码

def 若已取消则抛(信号=None):#已取消则抛稳定错误
    """调用方已经中止时，抛出提供方稳定的取消错误。"""
    if 信号已中止(信号):#已中止
        raise 搜索已取消(信号)#稳定 WEB_ABORTED

def 可取消(操作,信号=None):#同进程异步预检与调用方取消赛跑
    """把同进程可等待预检与调用方取消赛跑。挂上的结算在中止后仍观察不配合的操作，使稍后的拒绝不会变成未处理拒绝。"""
    if 信号 is None:#没有信号
        return 解开(操作)#原样结算
    if 信号已中止(信号):#已取消
        raise 搜索已取消(信号)#立即拒绝
    if not 是否thenable(操作):#同步值无需赛跑
        若已取消则抛(信号)#再查一次
        return 操作#同步结果
    完成=事件()#结算门闩
    盒子={'值':None,'错':None,'成':False}#结果盒
    def 跑操作():#观察原操作
        """观察原操作并写入结果盒。"""
        try:#等待原操作
            盒子['值']=操作.等待()#兑现
            盒子['成']=True#成功
        except Exception as 错误:#失败
            盒子['错']=错误#记下
        完成.set()#开门
    工作=线程(target=跑操作)#后台观察
    工作.daemon=True#不挡退出
    工作.start()#启动
    while not 完成.wait(0.05):#短等轮询
        if 信号已中止(信号):#中止胜出
            def 吞掉():#中止后仍观察，避免未处理拒绝
                """中止后仍等原操作结束。"""
                try:#等完
                    操作.等待()#吞掉稍后拒绝
                except Exception:#稍后拒绝
                    pass#已由取消路径拥有
            盯=线程(target=吞掉)#后台吞
            盯.daemon=True#不挡退出
            盯.start()#启动
            raise 搜索已取消(信号)#取消胜出
    if 盒子['成']:#成功
        return 盒子['值']#兑现值
    错=盒子['错']#失败
    文案=str(错)#剥前缀用
    if 文案.startswith('Error: '):#对齐 TS replace(/^Error: /u,'')
        文案=文案[7:]#去掉重复 Error:
    raise Exception(文案) from 错#带 cause 的新错误

def 引用摘要映射(块们):#从每个 text 块的 citations[] 建 url→cited_text
    """从每个 text 块的 citations[] 建 url → cited_text 映射。这是摘要来源：Anthropic web_search_result 项带 url/title/page_age，但通常没有行内摘要——摘录在另一个 text 块的 citation 里，按 url 键控（先出现的赢）。"""
    映射={}#url 到 cited_text
    for 块 in (块们 if 块们 is not None else []):#遍历内容块
        if 取字段(块,'type')!='text':#只看文本块
            continue#跳过
        for 引用 in (取字段(块,'citations') or []):#该块的 citations
            网址=取字段(引用,'url')#引用 URL
            摘录=取字段(引用,'cited_text')#被引文本
            if 网址 is not None and len(网址)>0 and 摘录 is not None and len(摘录)>0 and 网址 not in 映射:#有 url 与摘录且尚未记录
                映射[网址]=摘录#先出现的赢
    return 映射#摘要映射

def 映射人机响应(响应):#把 Messages 响应映射成规范化搜索结果
    """把 DeepSeek Anthropic Messages 响应映射成规范化搜索结果。遍历 web_search_tool_result 块里可引用的 web_search_result 项，把每条接到其 citation 摘录作为 snippet，并按 url 去重（max_uses > 1 的请求可能在多次搜索里冒出同一 URL）。web 服务拥有最终的 maxResults 截断，因此这里的 truncated 始终为 false。"""
    块们=取字段(响应,'content') or []#内容块，缺省空列表
    结果块们=[]#只留搜索工具结果块
    for 块 in 块们:#过滤
        if 取字段(块,'type')=='web_search_tool_result':#类型匹配
            结果块们.append(块)#收下
    if len(结果块们)==0:#没有原生搜索结果块
        raise 网络错误(
            'DeepSeek returned no web_search_tool_result blocks; the request may not have triggered native web search',#字面量不改
            'WEB_PROVIDER_ERROR',#提供方错误
        )#这是错误，不去刮散文
    摘要们=引用摘要映射(块们)#url 到摘录
    已见=set()#已收 url
    来源们=[]#规范化来源
    for 块 in 结果块们:#每个工具结果块
        for 条目 in (取字段(块,'content') or []):#块内条目
            if 取字段(条目,'type')!='web_search_result':#非结果
                continue#跳过
            网址=取字段(条目,'url') or ''#结果 URL
            if len(网址)==0 or 网址 in 已见:#空 url 或重复
                continue#跳过
            已见.add(网址)#记下 url
            来源={'url':网址}#一条来源
            标题=取字段(条目,'title')#可选标题
            if 标题 is not None and len(标题)>0:#非空标题
                来源['title']=标题#带上
            摘录=摘要们.get(网址)#对应摘录
            if 摘录 is not None and len(摘录)>0:#非空摘要
                来源['snippet']=摘录#带上
            页面新旧=取字段(条目,'page_age')#页面新旧
            if 页面新旧 is not None and len(页面新旧)>0:#非空日期
                来源['publishedAt']=页面新旧#映射到 publishedAt
            来源们.append(来源)#收下
    return {'sources':来源们,'truncated':False}#截断由 web 服务做

class DeepSeek搜索提供方:#DeepSeek 支持的搜索提供方；HTTP 重定向以 WEB_PROVIDER_ERROR 失败
    """DeepSeek 搜索提供方。resolveOptions 在每次操作入口快照一次，使一次搜索不会混用两段配置。用 thunk 而不是值，因为插件的设置段可能在两次搜索之间变化；为换端点而重新注册提供方会让缝的选择对用户表现为闪烁。"""
    def __init__(自身,解析选项):#保存选项解析器
        """收下下一次操作的选项 thunk。"""
        自身.解析选项=解析选项#选项解析器
        自身.id=提供方标识#注册 id

    def 可用(自身):#当前快照是否足以发起搜索
        """廉价的本地可用性检查；不得发起网络调用。"""
        选项=自身.解析选项()#读当前选项
        字面量=取字段(选项,'apiKey')#字面量密钥
        有密钥=((字面量 is not None and len(字面量)>0) or 取字段(选项,'resolveApiKey') is not None)#有字面量或解析器
        return 有密钥 and 可解析网址(取字段(选项,'baseURL')) and 是否正整数(取字段(选项,'maxTokens')) and 是否正整数(取字段(选项,'maxUses'))#四条件

    def 搜索(自身,请求,信号=None):#执行一次搜索
        """跑一次搜索；用信号接受取消。整次操作一份快照：凭证解析会等待，那段等待里若写入设置，不得把旧段解析出的密钥发到新段点名的端点。"""
        选项=自身.解析选项()#操作入口快照
        密钥=自身.取密钥(选项,信号)#解析密钥，不留在提供方上
        若已取消则抛(信号)#解析后若已取消则停
        端点=取字段(选项,'baseURL')+'/messages'#Messages 端点
        查询=取字段(请求,'query')#查询字符串
        体={#不含密钥的请求体
            'model':取字段(选项,'model'),#模型
            'max_tokens':取字段(选项,'maxTokens'),#生成上限
            'messages':[{#用户消息
                'role':'user',#角色
                'content':[{'type':'text','text':'Perform a web search for the query: '+查询}],#查询文本，字面量不改
            }],#messages 结束
            'tools':[{'type':'web_search_20250305','name':'web_search','max_uses':取字段(选项,'maxUses')}],#原生搜索工具
        }#body 结束
        记请求=取字段(选项,'recordRequest')#日志钩子
        if 记请求 is not None:#派发前先记日志；抛错则不派发
            记请求({#不含密钥的精确请求
                'endpoint':端点,#端点
                'apiVersion':取字段(选项,'apiVersion'),#API 版本
                'body':体,#请求体
            })#recordRequest 结束
        若已取消则抛(信号)#记日志后若已取消则停
        头={#请求头：官方 DeepSeek 要 x-api-key；Anthropic 兼容代理可能要 Authorization: Bearer——两个都发，谁认谁用
            'x-api-key':密钥,#官方密钥头
            'authorization':'Bearer '+密钥,#Bearer 形式
            'anthropic-version':取字段(选项,'apiVersion'),#API 版本
            'content-type':'application/json',#JSON 体
            'accept':'application/json',#要 JSON
            'user-agent':用户代理,#归属头
        }#headers 结束
        请求对象=请求构造(端点,data=编码(体).encode('utf-8'),headers=头,method='POST')#POST Messages
        try:#发 POST，重定向当错误
            响应=打开器.open(请求对象)#原生打开
        except Exception as 错误:#网络或中止
            if 信号已中止(信号) or 是否中止错误(错误):#取消
                raise 搜索已取消(信号,错误)#取消
            raise 网络错误('DeepSeek search request failed: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#网络失败
        状态=getattr(响应,'status',None) or 响应.getcode()#状态码
        if 状态<200 or 状态>=300:#HTTP 错误（含未跟随的重定向）
            消息='DeepSeek API error (HTTP '+str(状态)+')'#默认消息
            try:#尝试读错误体
                原文=响应.read().decode('utf-8')#读正文
                解析=解码(原文)#解析 JSON
                错误字段=取字段(解析,'error')#error 字段
                if isinstance(错误字段,str):#字符串错误
                    详情=错误字段#详情
                else:
                    详情=取字段(错误字段,'message') if 错误字段 is not None else 取字段(解析,'message')#嵌套或顶层
                if 详情 is not None and len(详情)>0:#有详情则替换
                    消息=详情#替换
            except Exception as 错误:#读错误体失败
                if 信号已中止(信号) or 是否中止错误(错误):#读到一半被取消必须报 WEB_ABORTED
                    raise 搜索已取消(信号,错误)#取消不是提供方错误
                #否则：HTTP 状态已记在上面的消息里；畸形/非 JSON 错误体最多丢掉更丰富的提供方消息
            finally:
                try:#关掉响应
                    响应.close()#清理
                except Exception:#关闭失败
                    pass#状态已在消息里
            raise 网络错误(消息,'WEB_PROVIDER_ERROR')#以提供方错误抛出
        try:#解析并映射成功体
            原文=响应.read().decode('utf-8')#读正文
            载荷=解码(原文)#解析 JSON
            return 映射人机响应(载荷)#映射成缝结果
        except Exception as 错误:#解析或映射失败
            if 信号已中止(信号) or 是否中止错误(错误):#取消
                raise 搜索已取消(信号,错误)#取消
            if isinstance(错误,网络错误):#已是网络错误（例如没有结果块）则原样抛
                raise 错误#原样
            raise 网络错误('DeepSeek returned an unprocessable response body: '+str(错误),'WEB_PROVIDER_ERROR',{'cause':错误})#无法处理的正文
        finally:
            try:#关掉响应
                响应.close()#清理
            except Exception:#关闭失败
                pass#映射路径已拥有结果或错误

    def 取密钥(自身,选项,信号=None):#解析一次操作的凭证，不把它留在提供方上
        """解析一次操作的凭证。调用方快照使密钥与发往的端点来自同一段配置。"""
        若已取消则抛(信号)#已取消则停
        字面量=取字段(选项,'apiKey')#字面量密钥
        if 字面量 is not None and len(字面量)>0:#字面量优先
            return 字面量#字面量
        解析器=取字段(选项,'resolveApiKey')#异步/同步解析器
        try:#跑解析器，可被取消；无解析器则得到 None（仍先查取消）
            if 解析器 is None:#没有解析器
                若已取消则抛(信号)#对齐 abortable(Promise.resolve(undefined))
                已解析=None#无解析器
            else:
                已解析=可取消(解析器(),信号)#可取消包装
        except Exception as 错误:#解析失败或取消
            if 信号已中止(信号) or 是否中止错误(错误):#取消
                raise 搜索已取消(信号,错误)#取消
            if isinstance(错误,网络错误) and 取字段(错误,'code')=='WEB_ABORTED':#已是取消
                raise 错误#原样
            raise 网络错误(
                'DeepSeek search credential resolution failed: '+str(错误),#字面量不改
                'WEB_PROVIDER_ERROR',#提供方错误
                {'cause':错误},#保留原因
            )#凭证解析失败
        if 已解析 is not None and len(已解析)>0:#解析出非空密钥
            return 已解析#密钥
        引用=取字段(选项,'apiKeyEnv') or 'DEEPSEEK_API_KEY'#诊断用的引用名
        raise 网络错误(
            'DeepSeek search has no API key for "'+str(引用)+'"; store it through the credentials service'
            +' (the web Models page writes it), export it in the launching environment, or set a literal'
            +' "apiKey" in the web-search-deepseek config',#字面量不改
            'WEB_PROVIDER_CREDENTIAL_MISSING',#缺凭证
        )#缺密钥

    available=可用#协议字段
    search=搜索#协议字段
