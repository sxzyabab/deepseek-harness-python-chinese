'DeepSeek Messages 直接传输，每次模型请求一条可取消生命周期'
import threading
from requests import request as 发请求
from ..llm.异常 import 语言模型错误 as 大模型错误#大模型错误
from ..llm import 大模型适配器,归属头
from ...工具.超时 import 空闲看门狗,取超时
from .模型信息 import 目录模型信息,模型信息
from .文件仓 import 深求文件仓
from .消息接口 import 消息文件测试通道,消息工具变更测试通道,消息接口根
from .异常 import 文件解析失败#上传失败，整请求可回退内联
from .请求文件 import 请求文件
from .请求扩展 import 准备请求扩展
from .图片 import 图片定价,内联图片,准备文件标识,准备图片
from .序列化 import 序列化
from .事件流 import 解析sse
from .翻译 import 翻译
from .传输 import 提供方错误,提供方错误详情

__all__=('深求适配器',)

class 中止信号:
    'threading.Event 取消通道'
    def __init__(自身):
        '创建一条取消通道'
        自身._事件=threading.Event()
        自身._异常=None

    def 触发(自身,原因=None):
        '标记中止'
        if 自身._事件.is_set():
            return
        if isinstance(原因,BaseException):
            自身._异常=原因
        elif 原因 is not None:
            自身._异常=大模型错误(str(原因),'ABORTED')
        自身._事件.set()

class 中止控制器:
    '发出中止的控制器'
    def __init__(自身):
        '创建配套信号'
        自身.信号=中止信号()

    def 中止(自身,原因=None):
        '中止配套信号'
        自身.信号.触发(原因)

def 已中止(信号):
    '信号是否已中止。无信号视为未中止'
    if 信号 is None:
        return False
    return 信号._事件.is_set()

def 若已中止则抛出(信号):
    '已中止则抛出信号上承载的异常'
    if not 已中止(信号):
        return
    原因=信号._异常
    if 原因 is None:
        raise 大模型错误('DeepSeek Messages request aborted','ABORTED')
    raise 原因

def 合成信号(左,右):
    '先中止的一路获胜'
    融合=中止信号()
    for 源 in (左,右):
        if 源 is not None and 已中止(源):
            融合.触发(源._异常)
            return 融合
    def 转发中止(来源):
        '等到来源置位后转发'
        来源._事件.wait()
        融合.触发(来源._异常)
    for 源 in (左,右):
        if 源 is None:
            continue
        threading.Thread(target=转发中止,args=(源,),daemon=True).start()
    return 融合

class 深求适配器(大模型适配器):
    '使用 Messages 内容与原生思考回放的 DeepSeek 提供方'
    def __init__(自身,配置):
        '保存插件拥有的操作局部解析钩子'
        自身.配置=配置
        if '解析文件仓' in 配置:
            自身.文件仓=配置['解析文件仓']()
        else:
            自身.文件仓=深求文件仓()

    def 图片访问(自身,引用):
        '解析当前执行世界里的图片访问'
        附件=自身.配置['解析附件']() if '解析附件' in 自身.配置 else None
        if 附件 is None:
            return None
        if '解析图片访问' not in 自身.配置:
            return None
        return 自身.配置['解析图片访问'](附件,引用)

    def 提供方简介(自身,提供方):
        '提供方展示'
        名=自身.配置['提供方名'] if '提供方名' in 自身.配置 and 自身.配置['提供方名'] is not None else 'DeepSeek'
        return {'id':提供方,'name':名}

    def 提供方重试政策(自身,提供方):
        '提供方政策'
        return 自身.配置['选项']()['retryPolicy']

    def 列出模型(自身,提供方):
        '建议目录；有发现钩子时由插件决定，缺凭证则可以返回空'
        if '发现模型' in 自身.配置:
            return 自身.配置['发现模型'](提供方)
        连接=自身.配置['选项']()
        return [目录模型信息(提供方,模型) for 模型 in 连接['models']]

    def 解析模型(自身,提供方,模型,信号=None):
        '解析精确模型'
        return 模型信息(自身.配置['选项'](),提供方,模型)

    def 图片请求定价(自身,提供方,模型):
        '图请求定价'
        return 图片定价(自身.配置['选项'](),模型,自身.图片访问)

    def 准备调用(自身,提供方,模型,信号=None):
        '把元数据与派发绑到同一代'
        连接=自身.配置['选项']()
        def 流(选项):
            '用本代连接发流'
            return 自身.生成(选项,连接)
        return {'model':模型信息(连接,提供方,模型),'stream':流}

    def 流式(自身,选项):
        '流式调用'
        return 自身.生成(选项,自身.配置['选项']())

    def 生成(自身,选项,连接):
        '看门狗包裹的可取消 Messages 流'
        消费=中止控制器()
        if 'signal' in 选项 and 选项['signal'] is not None:
            信号=合成信号(消费.信号,选项['signal'])
        else:
            信号=消费.信号
        看门狗=空闲看门狗(信号,连接['streamIdleTimeoutMs'],'MESSAGES_IDLE')
        迭代=自身.请求(选项,连接,看门狗.信号,看门狗.脉冲)
        try:
            while True:
                下一步=看门狗.下一步(迭代)
                if 下一步['done']:
                    return
                yield 下一步['value']
        except Exception as 错误:
            if 取超时(看门狗.信号,'MESSAGES_IDLE') is not None:
                raise 大模型错误('DeepSeek Messages stream idle timeout','TIMEOUT',{'cause':错误})
            if 'signal' in 选项 and 已中止(选项['signal']):
                raise 大模型错误('DeepSeek Messages request aborted','ABORTED',{'cause':错误})
            if isinstance(错误,大模型错误):
                raise 错误
            raise 大模型错误('DeepSeek Messages transport failed','TRANSPORT',{'cause':错误})
        finally:
            消费.中止()
            看门狗.释放()
            try:
                迭代.close()
            except Exception:
                pass

    def 请求(自身,选项,连接,信号,活动):
        '一次 Messages 请求，必要时回退内联图'
        若已中止则抛出(信号)
        附件=自身.配置['解析附件']() if '解析附件' in 自身.配置 else None
        消息列表,版本=准备图片(选项['messages'],连接,选项['model'],附件,自身.图片访问,信号)
        鉴权=自身.配置['解析鉴权'](连接) if '解析鉴权' in 自身.配置 else None
        if 鉴权 is None:
            账号令牌=自身.配置['解析账号令牌'](连接) if '解析账号令牌' in 自身.配置 else None
            密钥=账号令牌 if 账号令牌 is not None else 自身.配置['解析接口密钥'](连接)
            文件头={'baseURL':连接['baseURL'],'apiKey':密钥,'accountCredential':账号令牌 is not None}
        else:
            账号令牌=None
            密钥=鉴权['headers'].get('x-api-key') or 鉴权['headers'].get('x-dsh-auth-token')
            文件头={'baseURL':连接['baseURL'],'apiKey':密钥,'accountCredential':'x-dsh-auth-token' in 鉴权['headers']}
        try:
            yield from 自身._请求体(选项,连接,信号,活动,消息列表,版本,文件头,鉴权)
        except Exception as 错误:
            映射器=鉴权.get('onRequestError') if 鉴权 is not None else None
            if 映射器 is not None:
                try:
                    映射=映射器(错误)
                except Exception:
                    raise 错误
                raise 映射
            raise

    def _请求体(自身,选项,连接,信号,活动,消息列表,版本,文件头,鉴权):
        '一次 Messages 请求，必要时回退内联图'
        文件=请求文件(自身.文件仓,文件头,连接['filePolicy'],连接['filesApiTimeoutMs'],信号,活动)
        内联=False
        while True:
            若已中止则抛出(信号)
            文件.开始尝试()
            文件标识表=None
            if not 内联:
                try:
                    文件标识表=准备文件标识(消息列表,版本,文件)
                except 文件解析失败:
                    内联=True
                    continue
            历史=内联图片(消息列表,版本,连接) if 内联 else 消息列表
            def 降级(原因):
                '回放降级'
                if '回放降级' in 自身.配置:
                    自身.配置['回放降级']({'provider':选项['provider'],'model':选项['model'],'reason':原因})
            体=序列化(选项,连接,历史,版本,自身.图片访问,降级,文件标识表)
            会话号=str(选项['sessionId']) if 'sessionId' in 选项 and 选项['sessionId'] is not None else None
            用途=选项['purpose'] if 'purpose' in 选项 else None
            扩展选项={'signal':信号}
            if 会话号 is not None:
                扩展选项['sessionId']=会话号
            if 用途 is not None:
                扩展选项['purpose']=用途
            def 扩展被省略(字段列表,错误):
                '序列化失败则省略扩展字段'
                if '扩展被省略' in 自身.配置:
                    自身.配置['扩展被省略']({'provider':选项['provider'],'model':选项['model'],'fields':字段列表,'error':错误})
            def 扩展未接纳(错误):
                'HTTP 成功后接纳失败只报告'
                if '扩展未接纳' in 自身.配置:
                    自身.配置['扩展未接纳']({'provider':选项['provider'],'model':选项['model'],'error':错误})
            扩展=准备请求扩展(体,扩展选项,自身.配置['准备扩展'],扩展被省略,扩展未接纳)
            若已中止则抛出(信号)
            头=dict(归属头())
            头['content-type']='application/json'
            头['accept']='text/event-stream'
            if 鉴权 is not None:
                头.update(鉴权['headers'])
            elif 文件头.get('accountCredential'):
                头['x-dsh-auth-token']=文件头['apiKey']
            else:
                头['x-api-key']=文件头['apiKey']
            头['anthropic-version']='2023-06-01'
            测试通道=[]
            if 文件标识表 is not None and len(文件标识表)>0:
                测试通道.append(消息文件测试通道)
            if any(any(块.get('type') in ('tool_addition','tool_removal') for 块 in 消息.get('content') or []) for 消息 in 体['messages']):
                测试通道.append(消息工具变更测试通道)
            if len(测试通道)>0:
                头['anthropic-beta']=','.join(测试通道)
            头['x-deepseek-harness-user-id']=自身.配置['解析用户标识']()
            if 会话号 is not None:
                头['x-deepseek-harness-session-id']=会话号
            if 用途=='compaction':
                头['x-deepseek-harness-compact']='1'
            响应=发请求('POST',消息接口根(连接['baseURL'])+'/messages',headers=头,data=扩展['payload'],stream=True,allow_redirects=False,timeout=None)
            if 响应.status_code<200 or 响应.status_code>=300:
                文本=响应.text
                原始=None
                try:
                    import json as _json
                    原始=_json.loads(文本)
                except Exception:
                    pass
                详情=提供方错误详情(原始)
                if 文件.重试(详情):
                    continue
                失败=提供方错误(原始,响应.status_code,响应.headers)
                消息=文件.错误消息(响应.status_code,失败['message'],详情)
                失败信息=dict(失败['failure']) if 'failure' in 失败 else {}
                失败信息['cause']=RuntimeError(文本)
                raise 大模型错误(消息,失败['code'],失败信息)
            扩展['accept']()
            if 响应.raw is None:
                raise 大模型错误('DeepSeek Messages returned no response body','EMPTY_RESPONSE')
            yield from 翻译(解析sse(响应,活动),选项['model'])
            return
