"""`credentials` Remote 命名空间宿主拥有者。

对齐上游 `settings-controller/src/credentials.ts`。公开面仅中文名。
"""
import re#引用语法
from ...typert.协议 import 远程服务,远程 as _远程#Remote 基类
from .工具 import 取字段,解开,远程错误,远程错误消息#辅助

__all__=['凭据控制器','最大描述引用数']#仅中文公开名

最大描述引用数=64#单次 describe 批上限
引用形态=re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')#引用语法

def 解析请求(方法,模式,值):#解析请求
    """比生成编解码更严的域约束。"""
    if 模式=='describe':#describe
        引用们=取字段(值,'refs') if isinstance(值,dict) else 值#refs
        if not isinstance(引用们,list) or len(引用们)>最大描述引用数:#形态
            raise 远程错误('gateway/bad-request','invalid payload for '+方法,{'issues':[{'message':'refs invalid'}]})#拒绝
        for 引用 in 引用们:#逐条
            if not isinstance(引用,str) or 引用形态.match(引用) is None:#语法
                raise 远程错误('gateway/bad-request','invalid payload for '+方法,{'issues':[{'message':'ref grammar'}]})#拒绝
        return {'refs':引用们}#成功
    if 模式=='set':#set
        引用=取字段(值,'ref') if isinstance(值,dict) else None#ref
        秘密=取字段(值,'value') if isinstance(值,dict) else None#value
        if not isinstance(引用,str) or 引用形态.match(引用) is None or not isinstance(秘密,str) or 秘密=='':#形态
            raise 远程错误('gateway/bad-request','invalid payload for '+方法,{'issues':[{'message':'set invalid'}]})#拒绝
        return {'ref':引用,'value':秘密}#成功
    if 模式=='unset':#unset
        引用=取字段(值,'ref') if isinstance(值,dict) else 值#ref
        if not isinstance(引用,str) or 引用形态.match(引用) is None:#形态
            raise 远程错误('gateway/bad-request','invalid payload for '+方法,{'issues':[{'message':'unset invalid'}]})#拒绝
        return {'ref':引用}#成功
    raise 远程错误('gateway/bad-request','invalid payload for '+方法,{})#未知

def 投影凭据信息(信息):#字段投影
    """只复制 CredentialInfo 声明字段。"""
    视图={'configured':取字段(信息,'configured'),'writable':取字段(信息,'writable')}#基础
    if 取字段(信息,'source') is not None:#来源
        视图['source']=取字段(信息,'source')#来源
    return 视图#返回

class 凭据控制器(远程服务):#凭据 Remote 服务
    """把 ctx.credentials 投影到配置页可读写的 wire 面。"""
    def __init__(自身,上下文):#构造
        """登记 credentialsController 命名空间。"""
        super().__init__(上下文,'credentialsController',{'namespace':'credentials'})#注册

    @_远程
    def describe(自身,引用们):#批量描述
        """描述多个引用。"""
        请求=解析请求('credentials.describe','describe',{'refs':引用们})#解析
        凭据=自身._提供方()#提供方
        条目={}#结果
        for 引用 in 请求['refs']:#逐条
            品牌引用=凭据.credentialRef(引用) if hasattr(凭据,'credentialRef') else 引用#品牌化
            信息=解开(凭据.describe(品牌引用))#描述
            条目[引用]=投影凭据信息(信息)#投影
        return 条目#映射

    @_远程
    def set(自身,引用,值):#写入
        """写入秘密值（单向）。"""
        请求=解析请求('credentials.set','set',{'ref':引用,'value':值})#解析
        品牌引用=自身._提供方().credentialRef(请求['ref']) if hasattr(自身._提供方(),'credentialRef') else 请求['ref']#品牌
        自身._写入(请求['ref'],lambda:自身._提供方().set(品牌引用,请求['value']))#写

    @_远程
    def unset(自身,引用):#清除
        """移除引用。"""
        请求=解析请求('credentials.unset','unset',{'ref':引用})#解析
        品牌引用=自身._提供方().credentialRef(请求['ref']) if hasattr(自身._提供方(),'credentialRef') else 请求['ref']#品牌
        自身._写入(请求['ref'],lambda:自身._提供方().unset(品牌引用))#写

    def _提供方(自身):#解析提供方
        """取凭据提供方或报告如何挂载。"""
        凭据=自身.ctx.get('credentials')#可选服务
        if 凭据 is None:#缺席
            raise 远程错误('gateway/internal','credentials service is absent: this deployment does not mount a credential provider (e.g. @deepseek-ai/dsh-credentials-local) in its composition',{})#拒绝
        return 凭据#提供方

    def _写入(自身,引用,写入):#执行写入
        """把 seam 拒绝映射为 credential/rejected。"""
        try:#写
            解开(写入())#执行
        except Exception as 错误:#失败
            raise 远程错误('credential/rejected',远程错误消息(错误),{'ref':引用},cause=错误)#拒绝
