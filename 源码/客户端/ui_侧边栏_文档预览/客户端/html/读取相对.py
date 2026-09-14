import re#路径校验
from urllib.parse import unquote#解码
from ..远程过程调用 import 文档文件字节#字节解码
from ..面 import 已中止#中止

__all__=['创建读取超文本相对']#仅中文公开名

_绝对路径=re.compile(r'^(?:[a-z][a-z\d+.-]*:|[/\\])',re.IGNORECASE|re.ASCII)#绝对


def 创建读取超文本相对(关联读取,地址,寿命):
    """把包读取器绑到原 HTML 文件地址。"""

    def 读取(引用,信号):
        """剥离查询/片段、解码路径并保留 Host 失败。"""
        问=引用.find('?')#查询
        井=引用.find('#')#片段
        切=-1#切点
        if 问>=0:#有查询
            切=问
        if 井>=0 and (切<0 or 井<切):#更靠前的片段
            切=井
        路径=unquote(引用 if 切<0 else 引用[:切])#路径
        if 路径=='' or _绝对路径.search(路径) is not None or '\0' in 路径 or '\\' in 路径:#非法
            raise ValueError('HTML 依赖必须使用相对文件路径')
        if 已中止(寿命) or 已中止(信号):#中止
            raise RuntimeError('已中止')
        结果=关联读取(地址,路径,信号)#RemoteResult
        if 已中止(寿命) or 已中止(信号):#中止
            raise RuntimeError('已中止')
        if not 结果['ok']:#失败
            raise RuntimeError(结果['error']['message'] if 'message' in 结果['error'] else '读取失败')
        return 文档文件字节(结果['value'])#字节

    return 读取#相对读
