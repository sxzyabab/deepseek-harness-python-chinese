"""Remote 贡献制品的运行时编解码辅助。

对齐上游 typert 生成面中的 `mode:'strict'` 编解码形状。无 TypeScript 编译器时用手写边界模式；
schema 必须实现 parse(value)。公开面仅中文名。
"""

__all__=['透传模式','严格编解码','调用描述符','远程贡献']#公开面

class 透传模式:#边界透传解析
    """把线路值原样交回；结构校验由宿主方法边界负责。"""
    def parse(自身,值):#解析
        """原样返回。"""
        return 值#透传

def 严格编解码(类型符号,模式=None):#构造严格编解码
    """mode=strict + typeSymbol + schema。"""
    if 模式 is None:#缺省透传
        模式=透传模式()#透传
    return {'mode':'strict','typeSymbol':类型符号,'schema':模式}#编解码

def 调用描述符(#组装一条 InvocationDescriptor
    标识,服务,命名空间,方法,参数们,结果编解码,源码位置,
    实现=None,调用=None,作用域=None,取消=None,
):#结束签名
    """拼一条可挂载的调用描述符。"""
    if 调用 is None:#缺省直接调用
        调用={'kind':'direct'}#直接
    描述符={#描述符主体
        'id':标识,#稳定 id
        'service':服务,#服务键
        'namespace':命名空间,#命名空间
        'method':方法,#方法名
        'invocation':调用,#调用约定
        'parameters':list(参数们),#参数表
        'result':结果编解码,#结果编解码
        'sourceLocation':源码位置,#源码位置
    }#主体结束
    if 实现 is not None:#有实现别名
        描述符['implementation']=实现#实现名
    if 作用域 is not None:#有 scope
        描述符['scope']=作用域#作用域
    if 取消 is not None:#有取消
        描述符['cancellation']=取消#取消
    return 描述符#描述符

def 远程贡献(包名,描述符们):#组装 TYPERT_REMOTE
    """package + descriptors。"""
    return {'package':包名,'descriptors':list(描述符们)}#贡献
