"""为配置面的「获取可用模型」动作回答这个提供方能服务哪些模型。

公开面仅中文名；无英文别名。
"""
import json,math#JSON 与有限数
from json import JSONDecodeError#JSON 解析失败
from urllib.error import HTTPError,URLError#HTTP 错误
from urllib.request import Request,urlopen#发出请求
from .. import llm#语言模型服务
from .目录 import 目录模型#已安装目录模型

__all__=('发现模型','可询问协议','回复字节上限')#仅中文公开名

可询问协议=frozenset(['openai-completions','openai-responses'])#可询问的协议
回复字节上限=4*1024*1024#回复字节上限

def 容量(*候选列表):
    """列表条目上的正整数字段，缺席或不可用则为 None。入口处排除 bool。"""
    for 候选 in 候选列表:#按参数顺序取第一个能当容量的值，后面的字段只是回落
        if isinstance(候选,bool):#布尔是 int 子类不能当窗口
            continue#跳过布尔
        if isinstance(候选,int) and 候选>0:#零与负数不可用
            return 候选#第一个正整数立刻收下，不再看后续候选
        if isinstance(候选,float) and 候选>0 and 候选.is_integer():#JSON 数字可能是整值浮点，按容量收下
            return int(候选)#收成整数后再返回，避免窗口/上限带着小数
    return None#所有候选都缺席或不可用，调用方按缺席处理

def 标签(*候选列表):
    """列表条目上的非空字符串字段，或 None。"""
    for 候选 in 候选列表:#按参数顺序取第一个能当展示名的值，id 失败再试 name/display_name
        if isinstance(候选,str) and len(候选)>0:#非字符串与空串都不能当标签
            return 候选#第一个非空字符串立刻收下
    return None#没有可用标签，列表条目没有 id 时整条丢掉

def 列表网址(基址):
    """把端点基址与列表路径拼起来。"""
    去尾=基址
    while 去尾.endswith('/'):#去掉尾斜杠，避免拼出双斜杠 /models
        去尾=去尾[:-1]#每次只剥一层，直到不再以 / 结尾
    return 去尾+'/models'#接 OpenAI 兼容列表路径

def 已中止(信号):
    """调用方是否已中止。信号是 threading.Event 或 None。"""
    if 信号 is None:#发现请求可以不带取消信号，没有信号就不算中止
        return False#无信号则继续询问端点
    return 信号.is_set()#Event 置位则中止

def 有界读取(响应,网址):
    """读回复正文，拒绝超出上限的。响应是 urllib HTTPResponse。"""
    def 超限():
        """超限错误。"""
        return llm.大模型错误(f'{网址} answered with more than {回复字节上限} bytes','DISCOVERY_FAILED')#超限失败
    头=响应.headers#响应头；http.client 的 HTTPMessage
    if 'Content-Length' in 头:#规范头名优先
        声明原文=头['Content-Length']#声明长度原文
    elif 'content-length' in 头:#有的栈只给小写
        声明原文=头['content-length']#小写头
    else:#未知长度
        声明原文=None#下面按块读再卡上限
    try:#声明长度必须能当成数字，非数字不得当 0
        声明=float(声明原文) if 声明原文 is not None else float('nan')#有原文才解析；缺席用 NaN 表示未知
    except (TypeError,ValueError):#缺席或非数字一律当未知长度，继续按块读再卡上限
        声明=float('nan')#无法解析则不当成已声明超限
    if math.isfinite(声明) and 声明>回复字节上限:#头里已经声明超限则不必再读正文
        raise 超限()#拒绝，避免把超大回复读进内存
    块列表=[]#已读块
    合计=0#累计字节
    try:#按块读取，读完或超限都要关掉响应
        while True:#直到对端合上或累计超限
            块=响应.read(65536)#下一块；空块表示对端合上
            if len(块)==0:#空块表示读完，不是超限
                break#正文收齐，离开循环去做解码
            合计+=len(块)#累加后再判上限，避免先收下再超
            if 合计>回复字节上限:#累计字节超过上限立刻停，避免吃完整份超大回复
                raise 超限()#累计超限；finally 仍会关响应
            块列表.append(块)#记下块，未超限才保留
    finally:#无论成败都关掉套接字，避免泄漏
        响应.close()#清理
    return b''.join(块列表).decode('utf-8')#解码为文本

def 读列表(正文):
    """读一份 OpenAI 兼容列表回复。正文是 JSON 对象 dict。"""
    if 'data' not in 正文:#没有 data 键则无法自动发现
        raise llm.大模型错误(
            'the endpoint\'s model listing has no "data" array; enter this provider\'s models by hand',
            'DISCOVERY_FAILED',
        )#无法解析
    数据=正文['data']#只认 data；其它包装字段不当列表
    if not isinstance(数据,list):#data 必须是数组
        raise llm.大模型错误(
            'the endpoint\'s model listing has no "data" array; enter this provider\'s models by hand',
            'DISCOVERY_FAILED',
        )#无法解析
    模型列表=[]#候选
    for 原始 in 数据:#逐条列表条目，没有 id 的丢掉，不中断整份列表
        if not isinstance(原始,dict):#非对象条目没有字段可取
            continue#丢掉
        标识=标签(原始['id'] if 'id' in 原始 else None)#可用id；空串与缺席都不是模型
        if 标识 is None:#没有可用 id 则这条不是模型，整条丢掉
            continue#没有id则跳过，不把无名条目写进发现结果
        名字=标签(
            原始['name'] if 'name' in 原始 else None,
            原始['display_name'] if 'display_name' in 原始 else None,
        )#展示名；先 name 再 display_name；线协议字段名原样
        窗口=容量(
            原始['context_window'] if 'context_window' in 原始 else None,
            原始['context_length'] if 'context_length' in 原始 else None,
        )#窗口；两个字段名都认
        上限=容量(
            原始['max_output_tokens'] if 'max_output_tokens' in 原始 else None,
            原始['max_tokens'] if 'max_tokens' in 原始 else None,
        )#上限；两个字段名都认
        候选={'id':标识}#一条候选；id 是唯一必填
        if 名字 is not None:#有展示名才带上，缺席则配置面只用 id
            候选['name']=名字#有名字才带上，不拿 id 冒充 name
        if 窗口 is not None:#有窗口才带上，缺席留给配置面默认
            候选['contextWindow']=窗口#有窗口才带上
        if 上限 is not None:#有输出上限才带上，缺席留给配置面默认
            候选['maxTokens']=上限#有上限才带上
        模型列表.append(候选)#写入
    return 模型列表#候选列表

def 可用探测密钥(原始):
    """接受一把探测密钥，或在头造出之前拒绝它。规范化密钥返回 dict。"""
    判定=llm.规范化密钥(原始)#判定已提供密钥；形态为 {'ok','value'/'reason'}
    if 判定['ok']:#通过则交出修剪后的密钥，失败再按原因写文案
        return 判定['value']#通过则返回修剪后的，头里只带这一把
    原因=判定['reason']#拒绝原因，用来选中文案
    if 原因=='empty':#空密钥：提示去模型页填写，或清空后走未认证探测
        文案='this provider\'s API key is blank; enter it on the Models page, or clear it to probe unauthenticated'#空密钥
    else:#其余拒绝都是头无法携带的字符，不能静默丢掉再发未认证请求
        文案='this provider\'s API key contains characters no HTTP header can carry; paste the raw key only'#非法字符
    raise llm.大模型错误(文案,llm.非法凭证码)#拒绝；未通过不得把原串写进 Authorization

def 发现模型(请求,已存密钥=None):
    """询问一个草稿提供方端点它所通告的模型。请求为配置面发现 dict。"""
    提供方=请求['provider'] if 'provider' in 请求 else None#点名的路由
    if 提供方 is not None:#点名了路由才查已安装目录；未点名则只能问端点
        已安装=目录模型(提供方)#已安装目录；未运来的路由得到空表
        if len(已安装)>0:#目录已有模型则不必询问端点，配置面直接用目录
            结果=[]#从目录回答
            for 模型 in 已安装.values():#把目录条目投影成发现结果，不改目录原件
                结果.append({
                    'id':模型['id'],#模型id
                    'name':模型['name'],#展示名
                    'contextWindow':模型['contextWindow'],#窗口
                    'maxTokens':模型['maxTokens'],#上限
                    'inputModalities':list(模型['input']),#输入模态
                })#目录条目
            return 结果#目录答案，后面的 HTTP 列表不再走
    基址=请求['baseURL'] if 'baseURL' in 请求 else None#端点
    if 基址 is None or len(基址)==0:#没有目录又没有端点，无法自动发现
        路由文案='' if 提供方 is None else 提供方#诊断用路由
        raise llm.大模型错误(
            'pi-ai ships no catalog for provider "'+路由文案+'", so its models can only come from its'
            +" endpoint; set a baseURL, or enter this provider's models by hand",
            'DISCOVERY_FAILED',
        )#无法询问
    协议=请求['api'] if 'api' in 请求 else None#协议
    if 协议 is None:#草稿没写协议则默认 Completions 列表，与手声明路由默认一致
        协议='openai-completions'#默认Completions
    if 协议 not in 可询问协议:#本构建读不了该协议的列表，交给人手填
        raise llm.大模型错误(
            'pi-ai protocol "'+协议+'" has no model listing this build can read; enter this provider\'s models by hand',
            'DISCOVERY_UNSUPPORTED',
        )#无法询问
    网址=列表网址(基址)#列表URL
    供给=请求['apiKey'] if 'apiKey' in 请求 else None#草稿密钥
    if 供给 is None and 已存密钥 is not None:#草稿没给密钥则回落到已存闭包；闭包缺席则走未认证探测
        供给=已存密钥()#调用已存密钥闭包；仍可能得到 None
    密钥=None if 供给 is None else 可用探测密钥(供给)#无供给不造头；有供给必须先过规范化
    头={'accept':'application/json'}#请求头
    if 密钥 is not None:#有密钥才带 bearer，未认证探测则不带
        头['authorization']='Bearer '+密钥#有密钥才带bearer
    头.update(llm.归属头())#产品归属
    信号=请求['signal'] if 'signal' in 请求 else None#取消信号；缺席则 已中止 恒为假
    请求对象=Request(网址,headers=头,method='GET')#GET列表
    try:#发出列表请求
        响应=urlopen(请求对象)#发出请求
    except HTTPError as 错误:#端点用 HTTP 状态拒绝，与达不到端点分开报
        状态=错误.code#HTTP状态
        后缀='; check the API key' if 状态==401 or 状态==403 else ''#401/403点名密钥；其它状态只报码
        raise llm.大模型错误(网址+' answered '+str(状态)+后缀,'DISCOVERY_FAILED')#端点拒绝
    except URLError as 错误:#达不到端点；若调用方已中止则改报中止
        if 已中止(信号):#调用方先取消则不报达不到端点，避免把取消当成网络故障
            raise llm.大模型错误('model discovery aborted by caller','ABORTED',{'cause':错误})#中止
        raise llm.大模型错误('could not reach '+网址,'DISCOVERY_FAILED',{'cause':错误})#达不到端点
    状态=响应.status#urllib HTTPResponse.status
    if 状态<200 or 状态>=300:#非成功状态同样拒绝，401/403 点名密钥
        后缀='; check the API key' if 状态==401 or 状态==403 else ''#401/403点名密钥
        响应.close()#非成功也要关掉，避免套接字泄漏
        raise llm.大模型错误(网址+' answered '+str(状态)+后缀,'DISCOVERY_FAILED')#端点拒绝
    try:#有界读取正文
        文本=有界读取(响应,网址)#有界读取；内部 finally 会关响应
    except (OSError,UnicodeDecodeError) as 错误:#读取或解码失败；调用方中止则改报中止
        if 已中止(信号):#调用方先取消则不把读失败当发现错误
            raise llm.大模型错误('model discovery aborted by caller','ABORTED',{'cause':错误})#中止
        raise 错误#其余原样抛，保留超限或解码错误
    try:#按 JSON 查看
        正文=json.loads(文本)#按未知查看
    except JSONDecodeError as 错误:#不是 JSON 则无法读列表
        raise llm.大模型错误(网址+' did not answer with JSON','DISCOVERY_FAILED',{'cause':错误})#不是JSON
    if not isinstance(正文,dict):#根必须是对象
        raise llm.大模型错误(网址+' did not answer with JSON','DISCOVERY_FAILED')#不是对象
    return 读列表(正文)#解析列表
