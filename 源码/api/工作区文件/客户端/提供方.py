"""`file` 协议提供方：工作区文件元数据作为 `RemoteResult` 帧流。

对齐上游 `workspace-files/src/client/provider.ts`。公开面仅中文名。
地址两种作用域：`session/...` 把相对路径原样交给宿主；`absolute/...` 经当前 Session 授权。
首帧为 `stat`；宿主写入标 `changed`；消失或失败后的写入会再 `stat`；刷新再 `stat` 并清旗。
失败以 `ok: false` 帧表达，不抛；编程异常不捕获。
"""
import re#盘符段
from urllib.parse import unquote,urlparse#地址语法
from ..类型 import 远程错误,已中止#远程错误与中止

__all__=['会话查找字段','创建文件资源提供方']#仅中文公开名

会话查找字段=('current',)#当前 Session：可调用 → 会话标识或 None

盘符段模式=re.compile(r'^[A-Za-z]:\Z',re.ASCII)#Windows 盘符段


def 创建文件资源提供方(远程,变更供给,会话表):
    """在 Remote 面、变更供给与 Session 查找上建造 `file` 提供方。

    远程为本包 Remote 面；变更供给为 变更供给；会话表为 dict，含 current 可调用。
    返回供 `ctx.resources.登记` 的提供方 dict。
    """

    def 打开(地址,上下文):
        """产出 RemoteResult 帧直至中止或结束。上下文为 dict，含 signal。"""
        信号=上下文['signal']#中止
        解析结果=_解析地址(地址,会话表)#解析
        if not 解析结果['ok']:#失败
            yield 解析结果#失败帧
            return#停
        宿主文件=解析结果['value']#HostFile dict
        会话标识=宿主文件['sessionId']#会话
        路径=宿主文件['path']#路径
        通告=变更供给.跟随(会话标识,地址,信号)#跟随
        try:
            if (not 通告.就绪()) or 已中止(信号):#未就绪或已中止
                return#停
            首次=远程.workspaceFiles.stat(会话标识,路径,信号)#首 stat；RemoteResult dict
            if 已中止(信号):#取消
                return#停
            当前=None#资源值
            if 首次['ok']:#成功
                通告.绑定(首次['value']['absolutePath'])#绑定路径
                当前=_元数据于(首次['value'],False)#元数据
                yield {'ok':True,'value':当前}#成功帧
            else:
                yield 首次#失败帧
            for 通知 in 通告:#后续通知
                if 当前 is None:#尚无成功绑定
                    if 通知['kind']=='absent':#仍缺失
                        continue#忽略
                elif 通知['kind']=='changed':#版本写入
                    if 通知['version']==当前['version']:#重复版本
                        continue#忽略
                    更新={'absolutePath':当前['absolutePath'],'version':通知['version'],'changed':True}#新版本
                    if 'bytes' in 当前:#保留最近字节大小
                        更新['bytes']=当前['bytes']#拷贝
                    当前=更新#挂上
                    yield {'ok':True,'value':当前}#帧
                    continue#下一条
                # restat，或已有 current 时的 absent，或未绑定后的写入：再 stat
                再次=远程.workspaceFiles.stat(会话标识,路径,信号)#再 stat
                if 已中止(信号):#取消
                    return#停
                if not 再次['ok']:#失败
                    当前=None#清除
                    yield 再次#失败帧
                    continue#下一条
                通告.绑定(再次['value']['absolutePath'])#重绑
                当前=_元数据于(再次['value'],通知['kind']!='restat')#刷新清旗
                yield {'ok':True,'value':当前}#帧
        finally:
            通告.拆除()#注销

    def 刷新(地址):
        """请求该地址再次 stat。"""
        解析结果=_解析地址(地址,会话表)#解析
        if 解析结果['ok']:#成功
            变更供给.请求重stat(解析结果['value']['sessionId'],地址)#催

    return {'protocol':'file','open':打开,'reload':刷新}#提供方


def _解析地址(地址,会话表):
    """解析地址为宿主调用，或 unsupported-address / unknown-workspace 失败帧。"""
    解析=_解析文件地址(地址)#语法
    if 解析 is None:#非本语法
        return {'ok':False,'error':_不支持地址(地址)}#失败
    if 解析['scope']=='session':#会话作用域
        return {'ok':True,'value':{'sessionId':解析['sessionId'],'path':解析['path']}}#相对路径原样
    会话标识=会话表['current']()#当前 Session
    if 会话标识 is None:#无当前
        return {'ok':False,'error':_未知工作区(地址)}#失败
    return {'ok':True,'value':{'sessionId':会话标识,'path':解析['path']}}#绝对路径


def _不支持地址(地址):
    """本提供方不服务的地址。"""
    return 远程错误(
        'workspace-file/unsupported-address',
        地址+' is not a dsh-resource://file/session/<sessionId>/<path> or dsh-resource://file/absolute/<path> address',
        {'address':地址},
    )#错误


def _未知工作区(地址):
    """绝对地址无当前 Session。"""
    return 远程错误(
        'workspace-file/unknown-workspace',
        地址+' requires a current Session',
        {'address':地址},
    )#错误


def _元数据于(状态,已变更):
    """一次 stat 对应的资源值。状态为跨线 dict。"""
    值={'absolutePath':状态['absolutePath'],'version':状态['version'],'changed':已变更}#基础
    if 'bytes' in 状态:#有大小
        值['bytes']=状态['bytes']#带上
    return 值#元数据


def _解析文件地址(地址):
    """读回 `dsh-resource://file/…` 地址；非法则 None。

    语法归属 util/workspace-path；本包内嵌解析以免扩大移植面。
    """
    try:
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
