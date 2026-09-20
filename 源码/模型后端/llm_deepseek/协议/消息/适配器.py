"""直接消息协议传输，每次模型请求一条可取消寿命。"""
import json#错误体
from http.client import HTTPSConnection as 安全连接,HTTPConnection as 明文连接,HTTPException as 超文本异常#HTTP
from urllib.parse import urlparse as 解析网址
from ....llm import 归属头,大模型适配器,大模型错误#归属、基类与错误
from .....工具.超时 import 空闲看门狗,取超时,中止控制器,合成信号#空闲看门狗与中止
from ...协议无关.模型信息 import 目录模型信息,模型信息#模型信息
from ...协议无关.消息接口 import 消息文件测试版头 as 消息文件测试版,消息接口根#Messages API
from ...协议无关.请求文件 import 文件解析失败,请求文件#Files
from ...协议无关.请求扩展 import 准备请求扩展#扩展
from .图片 import 图片定价,内联图片,准备文件标识,准备图片#图
from .序列化 import 序列化#序列化
from .事件流 import 解析服务推送#SSE
from .翻译 import 翻译#翻译
from .传输 import 提供方错误,提供方错误细节#错误

__all__=('深求消息适配器',)#仅中文公开名

空闲码='MESSAGES_IDLE'#空闲码

def 空扩展准备(请求):
    """无插件贡献时的空扩展。"""
    def 接纳():#空接纳
        """无贡献可提交。"""
        return None#空
    return {'fields':{},'accept':接纳}#空扩展

class 深求消息适配器(大模型适配器):
    """使用消息内容与原生思考回放的 DeepSeek 提供方。"""
    def __init__(自身,依赖):
        """记下请求局部依赖。"""
        自身.依赖=依赖#依赖

    def 提供方简介(自身,提供方):
        """提供方展示。"""
        return {'id':提供方,'name':'DeepSeek'}#展示

    def 提供方重试政策(自身,提供方):
        """提供方政策。"""
        return 自身.依赖['connection']()['retryPolicy']#政策

    def 列出模型(自身,提供方):
        """建议目录。"""
        连接=自身.依赖['connection']()#本代
        return [目录模型信息(提供方,模型) for 模型 in 连接['models']]#目录

    def 解析模型(自身,提供方,模型,信号=None):
        """解析精确模型。"""
        return 模型信息(自身.依赖['connection'](),提供方,模型)#能力

    def 图片请求定价(自身,提供方,模型):
        """图请求定价。"""
        return 图片定价(自身.依赖['connection'](),模型,自身.依赖.get('imageAccess'))#定价

    def 准备调用(自身,提供方,模型,信号=None):
        """把元数据与派发绑到同一代。"""
        连接=自身.依赖['connection']()#本代
        def 流(选项):#派发
            """用冻结连接生成。"""
            return 自身.生成(选项,连接)#生成
        return {'model':模型信息(连接,提供方,模型),'stream':流}#已准备

    def 流式(自身,选项):
        """流式调用。"""
        return 自身.生成(选项,自身.依赖['connection']())#当前代

    def 生成(自身,选项,连接):
        """用看门狗消费一次请求。"""
        消费者=中止控制器()#消费方
        上游=选项.get('signal')#调用方
        信号=消费者.信号 if 上游 is None else 合成信号(消费者.信号,上游)#融合
        看门狗=空闲看门狗(信号,连接['streamIdleTimeoutMs'],空闲码)#空闲
        def 活动():#传输活动
            """无值时重置空闲计时。"""
            看门狗.脉冲()#脉冲
        迭代器=自身.请求(选项,连接,看门狗.信号,活动)#请求
        try:#消费
            while True:#逐步
                结果=看门狗.下一步(迭代器)#下一步
                if 结果['done']:#结束
                    return
                yield 结果['value']#让出
        except Exception as 错误:#失败
            if 取超时(看门狗.信号,空闲码) is not None:#空闲
                raise 大模型错误('DeepSeek Messages stream idle timeout','TIMEOUT',{'cause':错误}) from 错误#超时
            if 上游 is not None and 上游.is_set():#调用方中止
                raise 大模型错误('DeepSeek Messages request aborted','ABORTED',{'cause':错误}) from 错误#中止
            if isinstance(错误,大模型错误):#已是
                raise 错误#原样
            raise 大模型错误('DeepSeek Messages transport failed','TRANSPORT',{'cause':错误}) from 错误#传输
        finally:#收尾
            消费者.中止()#停
            看门狗.释放()#释放
            try:#关闭
                迭代器.close()#关闭
            except Exception:#拆除
                pass#已结算

    def 请求(自身,选项,连接,信号,活动):
        """发 /v1/messages 并翻译事件。"""
        if 信号 is not None and 信号.is_set():#已中止
            raise 大模型错误('aborted','ABORTED')#中止
        准备=准备图片(选项['messages'],连接,选项['model'],自身.依赖['attachments'](),自身.依赖.get('imageAccess'),信号)#图
        消息=准备['messages']#投影历史
        版本=准备['versions']#版本
        密钥=自身.依赖['apiKey'](连接)#密钥
        文件=请求文件(自身.依赖['files'](),{'baseURL':连接['baseURL'],'apiKey':密钥,'protocol':'messages'},连接['filePolicy'],连接['filesApiTimeoutMs'],信号,活动)#Files
        内联=False#是否内联
        准备扩展=自身.依赖.get('prepareExtensions')#扩展
        if 准备扩展 is None:#无
            准备扩展=空扩展准备#空
        while True:#尝试
            if 信号 is not None and 信号.is_set():#已中止
                raise 大模型错误('aborted','ABORTED')#中止
            文件.开始尝试()#重置
            文件标识=None#可选
            if not 内联:#先文件
                try:#解析
                    文件标识=准备文件标识(消息,版本,文件)#id
                except 文件解析失败:#失败
                    内联=True#回落
                    continue#再试
            历史=内联图片(消息,版本,连接) if 内联 else 消息#历史
            def 降级(原因):#回放降级
                """报告丢弃的回放元数据。"""
                回调=自身.依赖.get('回放降级')#回调
                if 回调 is not None:#有
                    回调({'provider':选项['provider'],'model':选项['model'],'reason':原因})#报告
            体=序列化(选项,连接,历史,版本,自身.依赖.get('imageAccess'),降级,None if 内联 else 文件标识)#序列化
            扩展选项={'signal':信号}#身份
            if 选项.get('sessionId') is not None:#会话
                扩展选项['sessionId']=str(选项['sessionId'])#会话
            if 选项.get('purpose') is not None:#用途
                扩展选项['purpose']=选项['purpose']#用途
            扩展=准备请求扩展(体,扩展选项,准备扩展)#合并
            if 信号 is not None and 信号.is_set():#已中止
                raise 大模型错误('aborted','ABORTED')#中止
            头=dict(归属头())#归属
            头['content-type']='application/json'#JSON
            头['accept']='text/event-stream'#SSE
            头['x-api-key']=密钥#密钥
            头['anthropic-version']='2023-06-01'#版本
            if 文件标识 is not None and len(文件标识)>0:#有文件
                头['anthropic-beta']=消息文件测试版#测试版
            头['x-deepseek-harness-user-id']=str(自身.依赖['userId']())#用户
            if 选项.get('sessionId') is not None:#会话
                头['x-deepseek-harness-session-id']=str(选项['sessionId'])#会话
            if 选项.get('purpose')=='compaction':#压缩
                头['x-deepseek-harness-compact']='1'#压缩
            网址=消息接口根(连接['baseURL'])+'/messages'#Messages 端点
            解析=解析网址(网址)
            载荷=扩展['payload']#JSON
            if isinstance(载荷,str):#文本
                载荷=载荷.encode('utf-8')#字节
            try:#传输
                if 解析.scheme=='https':#安全
                    客户端=安全连接(解析.hostname,解析.port)#HTTPS
                else:#明文
                    客户端=明文连接(解析.hostname,解析.port)#HTTP
                请求路径=解析.path+(('?'+解析.query) if 解析.query else '')#路径
                if not 请求路径:#空
                    请求路径='/'#根
                客户端.request('POST',请求路径,body=载荷,headers=头)#发
                响应=客户端.getresponse()
            except (OSError,超文本异常,RuntimeError) as 错误:#传输
                if 信号 is not None and 信号.is_set():#中止
                    raise 错误#原样
                raise 大模型错误('DeepSeek Messages transport failed','TRANSPORT',{'cause':错误}) from 错误#传输
            if 响应.status<200 or 响应.status>=300:#失败
                原文=响应.read()#体
                文本=原文.decode('utf-8',errors='replace')#文本
                原始=None#JSON
                try:#解析
                    原始=json.loads(文本)#JSON
                except (json.JSONDecodeError,TypeError,ValueError,UnicodeDecodeError):#非 JSON
                    原始=None#状态仍够
                细节=提供方错误细节(原始)#细节
                if 文件.重试(细节):#陈旧
                    客户端.close()#关
                    continue#再发
                失败=提供方错误(原始,响应.status,响应)#分类
                消息文案=文件.错误消息(响应.status,失败.message,细节)#诊断
                选项体=dict(失败.failure)#事实
                选项体['cause']=Exception(文本)#原因
                客户端.close()#关
                raise 大模型错误(消息文案,失败.code,选项体)#抛出
            扩展['accept']()#接纳
            try:#翻译
                yield from 翻译(解析服务推送(响应,活动),选项['model'])#翻译
            finally:#关
                客户端.close()#关
            return#成功
