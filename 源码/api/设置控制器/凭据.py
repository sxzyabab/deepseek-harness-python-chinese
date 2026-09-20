"""`credentials` Remote 命名空间宿主拥有者。"""
import re#引用语法
from ...typert.协议 import 远程服务,远程 as _远程#Remote 基类
from ...凭据.凭据 import 凭证引用#品牌化引用
from .远程错误与中止 import 远程错误,远程错误消息#远程错误

__all__=['凭据控制器','最大描述引用数']#仅中文公开名

最大描述引用数=64#单次 describe 批上限
引用形态=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*\Z',re.ASCII)#引用语法

def 解析请求(方法,模式,值):#解析请求
    """比生成编解码更严的域约束。值是线协议 dict。"""
    if 模式=='describe':#describe
        引用列表=值['refs']#refs
        if not isinstance(引用列表,list) or len(引用列表)>最大描述引用数:#形态
            raise 远程错误('gateway/bad-request','invalid payload for '+方法,{'issues':[{'message':'refs invalid'}]})#拒绝
        for 引用 in 引用列表:#逐条
            if not isinstance(引用,str) or 引用形态.match(引用) is None:#语法
                raise 远程错误('gateway/bad-request','invalid payload for '+方法,{'issues':[{'message':'ref grammar'}]})#拒绝
        return {'refs':引用列表}#成功
    if 模式=='set':#set
        引用=值['ref']#ref
        秘密=值['value']#value
        if not isinstance(引用,str) or 引用形态.match(引用) is None or not isinstance(秘密,str) or 秘密=='':#形态
            raise 远程错误('gateway/bad-request','invalid payload for '+方法,{'issues':[{'message':'set invalid'}]})#拒绝
        return {'ref':引用,'value':秘密}#成功
    if 模式=='unset':#unset
        引用=值['ref']#ref
        if not isinstance(引用,str) or 引用形态.match(引用) is None:#形态
            raise 远程错误('gateway/bad-request','invalid payload for '+方法,{'issues':[{'message':'unset invalid'}]})#拒绝
        return {'ref':引用}#成功
    raise 远程错误('gateway/bad-request','invalid payload for '+方法,{})#未知

def 投影凭据信息(信息):#字段投影
    """只复制 CredentialInfo 声明字段。信息为 dict。"""
    视图={'configured':信息['configured'],'writable':信息['writable']}#基础
    if 'source' in 信息:#来源
        视图['source']=信息['source']#来源
    return 视图#返回

class 凭据控制器(远程服务):#凭据 Remote 服务
    """把 ctx.credentials 投影到配置页可读写的 wire 面。"""
    def __init__(自身,上下文):#构造
        """登记 credentialsController 命名空间。"""
        super().__init__(上下文,'credentialsController',{'namespace':'credentials'})#注册

    @_远程
    def describe(自身,引用列表):#批量描述
        """描述多个引用。"""
        请求=解析请求('credentials.describe','describe',{'refs':引用列表})#解析
        凭据=自身._提供方()#提供方
        条目={}#结果
        for 引用 in 请求['refs']:#逐条
            品牌引用=凭证引用(引用)#品牌化
            信息=凭据.描述(品牌引用)#描述
            条目[引用]=投影凭据信息(信息)#投影
        return 条目#映射

    @_远程
    def set(自身,引用,值):#写入
        """写入秘密值（单向）。"""
        请求=解析请求('credentials.set','set',{'ref':引用,'value':值})#解析
        品牌引用=凭证引用(请求['ref'])#品牌
        def 写入():#执行设置
            """调用提供方写入。"""
            自身._提供方().设置(品牌引用,请求['value'])#写
        自身._写入(请求['ref'],写入)#写

    @_远程
    def unset(自身,引用):#清除
        """移除引用。"""
        请求=解析请求('credentials.unset','unset',{'ref':引用})#解析
        品牌引用=凭证引用(请求['ref'])#品牌
        def 写入():#执行移除
            """调用提供方移除。"""
            自身._提供方().移除(品牌引用)#移除
        自身._写入(请求['ref'],写入)#写

    def _提供方(自身):#解析提供方
        """取凭据提供方或报告如何挂载。"""
        凭据=自身.ctx.获取服务('credentials')#可选服务
        if 凭据 is None:#缺席
            raise 远程错误('gateway/internal','credentials service is absent: this deployment does not mount a credential provider (e.g. @deepseek-ai/dsh-credentials-local) in its composition',{})#拒绝
        return 凭据#提供方

    def _写入(自身,引用,写入):#执行写入
        """把 seam 拒绝映射为 credential/rejected。"""
        try:#写
            写入()#执行
        except OSError as 错误:
            raise 远程错误('credential/rejected',远程错误消息(错误),{'ref':引用},原因=错误)#拒绝
        except ValueError as 错误:
            raise 远程错误('credential/rejected',远程错误消息(错误),{'ref':引用},原因=错误)#拒绝
        except TypeError as 错误:
            raise 远程错误('credential/rejected',远程错误消息(错误),{'ref':引用},原因=错误)#拒绝
