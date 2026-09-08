"""本类型执行的分页读取，绑到 Client Remote。

对齐上游 `ui-sidebar-textpreview/src/client/rpc.ts`。公开面仅中文名。
内容是消费方的事：`file` 资源只带元数据，文本经此一次一页到达。
端点要会话与工作区路径，而 tab 带的是两种作用域之一的 `dsh-resource://file/` 地址，
本模块也拥有那份翻译。文件地址语法内嵌于此，以免扩大移植面。
"""
import re#盘符段
from urllib.parse import unquote,urlparse#地址语法

__all__=[#仅中文公开名
    '文本预览错误','解析文件地址','宿主文件于','创建读页',
]#公开面结束

盘符段模式=re.compile(r'^[A-Za-z]:\Z',re.ASCII)#Windows 盘符段


class 文本预览错误(Exception):
    """本包文本预览失败。"""

    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文


def 解析文件地址(地址):
    """读回 `dsh-resource://file/…` 地址；非法则 None。

    语法归属 util/workspace-path；本包内嵌解析以免扩大移植面。
    """
    try:#URL 解析
        网址=urlparse(地址)#解析 URI
        if 网址.scheme!='dsh-resource' or 网址.netloc!='file':#非本方案
            return None#拒绝
        段列表=网址.path.split('/')#['', scope, ...]
        if len(段列表)<2:#过短
            return None#拒绝
        作用域=段列表[1]#scope
        其余=段列表[2:]#rest
        if 作用域=='session':#会话
            if len(其余)==0:#无 id
                return None#拒绝
            标识=其余[0]#id 段
            路径段=其余[1:]#路径段（空路径时为 ['']）
            if 标识=='' or len(路径段)==0:#缺 id 或无路径分量
                return None#拒绝
            return {#会话地址
                'scope':'session',
                'sessionId':unquote(标识),
                'path':'/'.join(unquote(段) for 段 in 路径段),
            }#结束
        if 作用域=='absolute':#绝对
            是UNC=len(其余)>1 and 其余[0]==''#UNC 标记
            有效=其余[1:] if 是UNC else 其余#有效段
            解码=[unquote(段) for 段 in 有效]#解码
            if len(解码)==0 or 解码[0]=='':#无路径
                return None#拒绝
            if 是UNC:#UNC
                return {'scope':'absolute','path':'//'+'/'.join(解码)}#UNC 路径
            if 盘符段模式.match(解码[0]) is not None:#盘符
                return {'scope':'absolute','path':'/'.join(解码)}#C:/...
            return {'scope':'absolute','path':'/'+'/'.join(解码)}#POSIX
        return None#未知作用域
    except (TypeError,ValueError):#非 URL
        return None#拒绝


def 宿主文件于(地址,会话标识):
    """一条 `dsh-resource://file/…` 地址所命名的会话与路径。

    `session` 地址自带会话与相对路径；`absolute` 地址无会话，经席位自身会话读，
    宿主仍围栏在该会话工作区内。注册表把可解析的 `file` 地址都路由到本类型，
    故 `解析文件地址` 拒收的地址是编程错误，抛出。
    """
    解析=解析文件地址(地址)#语法
    if 解析 is None:#非法
        raise 文本预览错误('ui-sidebar-textpreview: not a file address "'+str(地址)+'"')#拒绝
    if 解析['scope']=='session':#会话作用域
        return {'sessionId':解析['sessionId'],'path':解析['path']}#自带会话
    return {'sessionId':会话标识,'path':解析['path']}#经席位会话


def 创建读页(远程):
    """把分页读绑到一份 Remote 面。页长由宿主配置上限决定，故不传 `limit`。

    远程须带 `workspaceFiles.read`；返回 (会话标识, 路径, 偏移, 信号) → RemoteResult dict。
    """

    def 读页(会话标识,路径,偏移,信号):
        """读一行页；失败原样透传。"""
        return 远程.workspaceFiles.read(会话标识,路径,{'offset':偏移},信号)#RemoteResult

    return 读页#绑定读页
