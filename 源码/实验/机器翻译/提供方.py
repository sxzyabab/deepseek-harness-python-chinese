'匿名端点协议、有界 JSON 读取和中文语言标签'
import json
import threading
from http import client as 超文本
from urllib.parse import parse_qsl,urlencode,urlsplit,urlunsplit
from ...基础设施.通用工具 import 启动守护线程,紧凑json编码,摘要十六进制
from ...工具.值 import 断言永不
from .异常 import 翻译错误
from .类型 import 已中止,截止,取信号超时,取原因,若已中止则抛出

__all__=['匿名配方','翻译文本']

def 匿名配方(提供方,配置):
    '协议修订加上去掉本提供方自有查询键之后的端点指纹'
    地址=配置['googleEndpoint'] if 提供方=='google' else 配置['bingEndpoint']
    拥有=('client','sl','tl','dt','q') if 提供方=='google' else ('from','to','isEnterpriseClient')
    剩余=改查询(地址,删除=拥有)
    协议='google-form-v1' if 提供方=='google' else 'bing-edge-v1'
    return 紧凑json编码([协议,摘要十六进制(剩余)])

def 语言标签(标签,提供方):
    '常见中文地区标签按端点改写，其余原样'
    小写=标签.lower()
    if 小写 in ('zh','zh-cn','zh-sg','zh-hans'):
        return 'zh-CN' if 提供方=='google' else 'zh-Hans'
    if 小写 in ('zh-tw','zh-hk','zh-mo','zh-hant'):
        return 'zh-TW' if 提供方=='google' else 'zh-Hant'
    return 标签

def 改查询(地址,删除=(),设置=()):
    '删掉指定查询键，再按给定顺序写入；路径为空时补成根路径'
    拆开=urlsplit(地址)
    删除集=set(删除)
    项=[(键,值) for 键,值 in parse_qsl(拆开.query,keep_blank_values=True) if 键 not in 删除集]
    设置表=dict(设置)
    已见=set()
    新项=[]
    for 键,值 in 项:
        if 键 in 设置表:
            if 键 not in 已见:
                新项.append((键,设置表[键]))
                已见.add(键)
        else:
            新项.append((键,值))
    for 键,值 in 设置:
        if 键 not in 已见:
            新项.append((键,值))
            已见.add(键)
    路径=拆开.path if len(拆开.path)>0 else '/'
    return urlunsplit((拆开.scheme,拆开.netloc,路径,urlencode(新项),''))

def 请求之(规格,配置):
    '拼出不带凭据的匿名请求；谷歌走表单，必应走 JSON 数组'
    来源=语言标签(规格['sourceLanguage'],规格['provider'])
    目标=语言标签(规格['targetLanguage'],规格['provider'])
    提供方=规格['provider']
    if 提供方=='google':
        地址=改查询(配置['googleEndpoint'],删除=('client','sl','tl','dt','q'))
        体=urlencode((('client','gtx'),('sl',来源),('tl',目标),('dt','t'),('q',规格['text']))).encode('utf-8')
        头={'content-type':'application/x-www-form-urlencoded'}
        return 地址,体,头
    if 提供方=='bing':
        设置=(('to',目标),('isEnterpriseClient','false'))
        if 来源!='auto':
            设置=(('from',来源),)+设置
        地址=改查询(配置['bingEndpoint'],删除=('from',) if 来源=='auto' else (),设置=设置)
        体=紧凑json编码([规格['text']]).encode('utf-8')
        头={'content-type':'application/json'}
        return 地址,体,头
    return 断言永不(提供方)

def 无效响应(提供方):
    '响应结构不符合该端点'
    return 翻译错误('TRANSLATION_INVALID_RESPONSE',提供方+' 返回了无效的翻译响应')

def 译文之(载荷,提供方):
    '从谷歌分段或必应 translations[0].text 取出译文'
    if not isinstance(载荷,list):
        raise 无效响应(提供方)
    if len(载荷)==0:
        raise 无效响应(提供方)
    第一=载荷[0]
    if 提供方=='google':
        if not isinstance(第一,list) or len(第一)==0:
            raise 无效响应(提供方)
        片段=[]
        for 段 in 第一:
            if not isinstance(段,list):
                raise 无效响应(提供方)
            文本=段[0] if len(段)>0 else None
            if not isinstance(文本,str):
                raise 无效响应(提供方)
            片段.append(文本)
        return ''.join(片段)
    if 提供方=='bing':
        if not isinstance(第一,dict) or not isinstance(第一.get('translations'),list):
            raise 无效响应(提供方)
        if len(第一['translations'])==0:
            raise 无效响应(提供方)
        已译=第一['translations'][0]
        if not isinstance(已译,dict) or not isinstance(已译.get('text'),str):
            raise 无效响应(提供方)
        return 已译['text']
    return 断言永不(提供方)

def 监视关闭(连接,信号,已关):
    '上游中止时关掉套接字，使阻塞读取返回'
    while not 已关.is_set():
        if 已中止(信号):
            try:
                连接.close()
            except OSError as 关闭错误:
                del 关闭错误
            return
        已关.wait(0.05)

def 发送(地址,体,头,信号,上限,提供方):
    '不跟随重定向、不带 Cookie；3xx 当请求失败，超限在读完之前关掉'
    拆开=urlsplit(地址)
    连接类=超文本.HTTPSConnection if 拆开.scheme=='https' else 超文本.HTTPConnection
    连接=连接类(拆开.hostname,拆开.port,timeout=None)
    已关=threading.Event()
    启动守护线程(监视关闭,连接,信号,已关)
    try:
        路径=拆开.path if len(拆开.path)>0 else '/'
        if len(拆开.query)>0:
            路径=路径+'?'+拆开.query
        连接.request('POST',路径,body=体,headers=dict(头))
        响应=连接.getresponse()
        状态=响应.status
        if 300<=状态<400:
            响应.close()
            raise OSError('redirect refused')
        if 状态<200 or 状态>=300:
            响应.close()
            raise 翻译错误('TRANSLATION_HTTP_ERROR',提供方+' 翻译失败（HTTP '+str(状态)+'）')
        块列表=[]
        字节数=0
        while True:
            若已中止则抛出(信号)
            块=响应.read(8192)
            if len(块)==0:
                break
            字节数=字节数+len(块)
            if 字节数>上限:
                响应.close()
                raise 翻译错误('TRANSLATION_RESPONSE_LIMIT',提供方+' 翻译响应超过 '+str(上限)+' 字节')
            块列表.append(块)
        return b''.join(块列表)
    finally:
        已关.set()
        try:
            连接.close()
        except OSError as 关闭错误:
            del 关闭错误

def 翻译文本(规格,配置,信号):
    '不带 Cookie、凭据和回退；空文本直接返回空串'
    with 截止(信号,配置['timeoutMs'],'TRANSLATION_TIMEOUT') as 时限:
        try:
            若已中止则抛出(时限.信号)
            if 规格['text']=='':
                return ''
            地址,体,头=请求之(规格,配置)
            原始=发送(地址,体,头,时限.信号,配置['maxResponseBytes'],规格['provider'])
            try:
                载荷=json.loads(原始.decode('utf-8','replace'))
            except (UnicodeError,json.JSONDecodeError,ValueError):
                raise 翻译错误('TRANSLATION_INVALID_RESPONSE',规格['provider']+' 返回了无效的翻译 JSON')
            若已中止则抛出(时限.信号)
            return 译文之(载荷,规格['provider'])
        except Exception as 错误:
            到期=取信号超时(时限.信号,'TRANSLATION_TIMEOUT')
            if 到期 is not None and 到期 is not 取原因(信号):
                raise 翻译错误('TRANSLATION_TIMEOUT',规格['provider']+' 翻译在 '+str(到期.timeoutMs)+' 毫秒后超时')
            若已中止则抛出(时限.信号)
            if isinstance(错误,翻译错误):
                raise
            raise 翻译错误('TRANSLATION_REQUEST_FAILED',规格['provider']+' 翻译请求失败')
