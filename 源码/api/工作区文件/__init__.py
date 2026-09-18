"""工作区文件服务：只读预览、工作区目录列举与观察变更流。

对齐上游 `@deepseek-ai/dsh-api-workspace-files`。公开面仅中文名。
文件读取跟随组合文件系统读权限（可含工作区外）；目录与变更观察仍限定工作区内。
"""
import base64#字节窗线路编码
import os#路径解析
import re#相对路径校验
from urllib.parse import unquote,urlparse#工作区相对路径
from ...依赖.schemastery import 正整数字段#配置字段
from ...typert.协议 import 远程服务,远程 as _远程#Remote 基类
from .变更 import 工作区变更供给#changes 供给
from .类型 import 远程错误,已中止#远程错误与中止

__all__=['名称','注入','配置','工作区文件','应用']#仅中文公开名

名称='workspace-files'#插件名
注入=['fs','sandboxPolicy','sessions','typert']#依赖

配置={#部署页/列举上限
    'maxBytes':正整数字段(默认值=2*1024*1024,最小=1),#单页与单窗字节上限（含）
    'maxFileBytes':正整数字段(默认值=32*1024*1024,最小=1),#整文件字节上限（含）
    'maxLines':正整数字段(默认值=5000,最小=1),#页行数缺省与上限
    'maxEntries':正整数字段(默认值=2000,最小=1),#目录条目上限
}#配置结束

空字节=chr(0)#页上出现则视为二进制
安全整数上限=9007199254740991#JSON 入口安全整数
绝对或方案模式=re.compile(r'^[a-z][a-z\d+.-]*:',re.IGNORECASE|re.UNICODE)#URL 方案前缀


def _至少整数(值,最小,名):
    """拒绝线协议承认但窗口不能用的数：仅安全整数可索引文件。"""
    if isinstance(值,bool) or not isinstance(值,(int,float)):#非数
        raise 远程错误('gateway/bad-request',名+' must be a safe integer of at least '+str(最小),{})#拒绝
    if 值!=int(值) or 值<最小 or 值>安全整数上限 or 值<-安全整数上限:#非安全整数
        raise 远程错误('gateway/bad-request',名+' must be a safe integer of at least '+str(最小),{})#拒绝
    return int(值)#整数


def _切页(块序列,偏移,限额,最大字节,路径):
    """从已解码块切出行窗 `偏移`..`偏移+限额-1`，在页后首字符处停，使文件其余部分永不读入。"""
    末行=偏移+限额-1#末行号
    行列表=[]#页内行
    当前=''#未完成行
    字节数=0#页累计 UTF-8 字节
    行号=1#当前行

    def 验收(增量):
        """页字节超上限则失败，不截短。"""
        nonlocal 字节数#累计
        字节数+=增量#加
        if 字节数>最大字节:#超限
            raise 远程错误(
                'workspace-file/too-large',
                'lines '+str(偏移)+'-'+str(末行)+' of "'+路径+'" exceed the '+str(最大字节)+' byte cap',
                {'path':路径,'limit':最大字节},
            )#拒绝

    def 完成一行():
        """收一行；行间换行计入字节。"""
        nonlocal 当前#缓冲
        if len(行列表)>0:#非首行
            验收(1)#`\n` 连接字节
        行列表.append(当前)#收下
        当前=''#清空

    for 块 in 块序列:#逐块
        位置=0#块内游标
        while 位置<len(块):#扫块
            if 行号>末行:#页已满
                return {'text':'\n'.join(行列表),'lines':len(行列表),'eof':False}#未到 EOF
            换行=块.find('\n',位置)#下一换行
            片段=块[位置:] if 换行==-1 else 块[位置:换行]#本段
            if 行号>=偏移:#页内
                验收(len(片段.encode('utf-8')))#UTF-8 字节
                当前+=片段#追加
            if 换行==-1:#块尽
                break#下一块
            if 行号>=偏移:#页内成行
                完成一行()#收行
            行号+=1#下一行
            位置=换行+1#越过 `\n`
    if len(当前)>0:#尾部无换行的页内行
        完成一行()#收行
    return {'text':'\n'.join(行列表),'lines':len(行列表),'eof':True}#到 EOF


def _工作区相对路径(根网址,目标网址):
    """由两条规范 `file:` URI 推导相对工作区路径；根自身为空串。"""
    根=urlparse(根网址).path.rstrip('/')#去尾斜杠
    目标=urlparse(目标网址).path#目标 path
    if 目标==根:#即根
        return ''#空
    return '/'.join(unquote(段) for 段 in 目标[len(根)+1:].split('/'))#解码拼接


def _目录条目(子项):
    """剥离子目标：线路只带名与元数据。子项为跨包 dict。"""
    条目={'name':子项['name'],'type':子项['type']}#基础
    if 'size' in 子项:#有大小
        条目['size']=子项['size']#带上
    return 条目#条目


def _是否非文本拒绝(错误):
    """按 code 识别后端非文本拒绝；类身份不跨包边界共享。"""
    return getattr(错误,'code',None)=='FS_NOT_TEXT'#结构化码


def _读字节窗口(文件系统,目标,偏移,长度,信号):
    """读普通文件的原始字节窗。"""
    if 已中止(信号):#取消
        raise 远程错误('gateway/cancelled','aborted',{})#取消
    if hasattr(文件系统,'读字节范围'):#后端有缝
        return 文件系统.读字节范围(目标,{'offset':偏移,'length':长度},信号)#委托
    if 长度==0:#空窗
        return b''#空
    键=目标['targetKey']#稳定键即本地绝对路径
    with open(键,'rb') as 文件:#二进制
        文件.seek(偏移)#定位
        数据=文件.read(长度)#至多 length
    if 已中止(信号):#读后
        raise 远程错误('gateway/cancelled','aborted',{})#取消
    return 数据#窗口


class 工作区文件(远程服务):
    """经组合文件系统的宿主 Remote 文件读取与工作区目录观察。"""
    inject=注入#框架槽：类级注入
    Config=配置#框架槽：Cordis 配置

    def __init__(自身,上下文,配置值=None):
        """挂载 `workspaceFiles` 命名空间、变更供给与 workspaceFileScope 查找。配置值为 dict。"""
        super().__init__(上下文,'workspaceFiles')#服务键即命名空间
        if 配置值 is None:#缺省
            配置值={}#空
        自身._配置={#合并缺省
            'maxBytes':配置值['maxBytes'] if 'maxBytes' in 配置值 and 配置值['maxBytes'] is not None else 2*1024*1024,
            'maxFileBytes':配置值['maxFileBytes'] if 'maxFileBytes' in 配置值 and 配置值['maxFileBytes'] is not None else 32*1024*1024,
            'maxLines':配置值['maxLines'] if 'maxLines' in 配置值 and 配置值['maxLines'] is not None else 5000,
            'maxEntries':配置值['maxEntries'] if 'maxEntries' in 配置值 and 配置值['maxEntries'] is not None else 2000,
        }#配置结束
        自身._供给=工作区变更供给(上下文)#变更供给
        def 登记查找(子上下文):
            """登记 workspaceFileScope 查找。"""
            def 解析(会话标识):
                """解析 Session 工作区根，不激活 Agent。"""
                存活=子上下文.sessions.get(会话标识)#存活会话
                头=存活.header if 存活 is not None else None#存活头
                if 头 is None:#冷读
                    持久化=子上下文.获取服务('sessionPersistence')#可选持久化
                    快照=持久化.观察(会话标识) if 持久化 is not None else None#轻量观察
                    头=快照['header'] if isinstance(快照,dict) and 'header' in 快照 else None#冷头
                if 头 is None:#无会话
                    return None#缺席
                根=头['cwd'] if isinstance(头,dict) and 'cwd' in 头 and 头['cwd'] is not None else 子上下文.sandboxPolicy.workspaceRoot#根
                return {'sessionId':会话标识,'workspaceRoot':根}#作用域
            子上下文.typert.lookups.register('workspaceFileScope',{
                'parameter':'workspaceFileScope',#参数名
                'wire':'workspaceFileScopeId',#线路字段
                'hostTypeSymbol':'@deepseek-ai/dsh-api-workspace-files#WorkspaceFileScope',#宿主类型
                'wireTypeSymbol':'@deepseek-ai/dsh-session/types#SessionId',#线路类型
                'resolve':解析,#解析
            })#登记结束
        上下文.依赖启动(['sessions','typert'],登记查找)#等依赖

    @_远程
    def read(自身,工作区文件作用域,路径,范围,信号):
        """读 UTF-8 文本文件的一行页。作用域与范围为线协议 dict。"""
        偏移,限额=自身._解析页(范围 if 范围 is not None else {})#页窗
        目标,信息=自身._定位文件(工作区文件作用域,路径,信号)#定位
        页=自身._切页于(目标,偏移,限额,信号,路径)#切页
        if 空字节 in 页['text']:#NUL
            raise 远程错误('workspace-file/not-text','"'+路径+'" contains NUL bytes',{'path':路径})#拒绝
        结果=自身._状态于(目标,信息)#stat
        结果['offset']=偏移#窗起点
        结果['text']=页['text']#正文
        结果['lines']=页['lines']#行数
        结果['eof']=页['eof']#是否到末行
        return 结果#页

    @_远程
    def readBytes(自身,工作区文件作用域,路径,范围,信号):
        """读普通文件的原始字节窗；不解码、不拒二进制。范围为 dict。"""
        偏移,长度=自身._解析窗(范围 if 范围 is not None else {},路径)#字节窗
        目标,信息=自身._定位文件(工作区文件作用域,路径,信号)#定位
        数据=_读字节窗口(自身.ctx.fs,目标,偏移,长度,信号)#字节窗
        if 'size' not in 信息:#后端未报大小
            到末=len(数据)<长度#短于请求则到末
        else:
            到末=偏移+len(数据)>=信息['size']#含末字节
        结果=自身._状态于(目标,信息)#stat
        结果['offset']=偏移#窗起点
        结果['data']=base64.b64encode(数据).decode('ascii')#base64
        结果['eof']=到末#是否到末字节
        return 结果#窗

    @_远程
    def readAll(自身,工作区文件作用域,路径,信号):
        """按整文件上限读完整常规文件字节。"""
        目标,信息=自身._定位文件(工作区文件作用域,路径,信号)#定位
        上限=自身._配置['maxFileBytes']#上限
        try:
            数据=自身.ctx.fs.读字节(目标,信号,上限)#整文件
        except BaseException as 原因:
            if getattr(原因,'code',None)=='FS_TOO_LARGE':#过大
                raise 远程错误('workspace-file/too-large','"'+路径+'" exceeds the '+str(上限)+' byte full-file cap',{'path':路径,'limit':上限},原因=原因)#拒绝
            raise#原样
        结果=自身._状态于(目标,信息)#stat
        结果['offset']=0#起点
        结果['data']=base64.b64encode(bytes(数据)).decode('ascii')#base64
        结果['eof']=True#整文件
        return 结果#窗

    @_远程
    def readRelated(自身,工作区文件作用域,路径,相对路径,信号):
        """相对另一文件目录读完整相关文件。"""
        相对=相对路径.replace('\\','/')#归一
        if 相对=='' or 相对.startswith('/') or 绝对或方案模式.match(相对) is not None or 空字节 in 相对:#非法
            raise 远程错误('gateway/bad-request','relativePath must be a relative filesystem path',{})#拒绝
        目标,_信息=自身._定位文件(工作区文件作用域,路径,信号)#定位基准
        绝对=自身.ctx.fs.进程路径(目标)#绝对路径
        相关=os.path.normpath(os.path.join(os.path.dirname(绝对),相对.replace('/',os.sep)))#解析相关
        return 自身.readAll(工作区文件作用域,相关,信号)#读整文件

    @_远程
    def stat(自身,工作区文件作用域,路径,信号):
        """报告普通文件身份、版本与大小，不含内容。"""
        目标,信息=自身._定位文件(工作区文件作用域,路径,信号)#定位
        return 自身._状态于(目标,信息)#stat

    @_远程
    def list(自身,工作区文件作用域,路径,信号):
        """列举 Session 工作区内一目录的直接子项。"""
        根,工作区根,条目=自身._检视(工作区文件作用域,路径,信号)#检视
        if 条目['type']!='directory':#非目录
            raise 远程错误(
                'workspace-file/not-directory',
                '"'+路径+'" is a '+str(条目['type']),
                {'path':路径,'kind':条目['type']},
            )#拒绝
        目标=自身._围栏(根,工作区根,路径,信号)#包含判定
        子项列表=自身.ctx.fs.列目录(目标,信号)#列举
        上限=自身._配置['maxEntries']#条目上限
        return {#列举
            'path':_工作区相对路径(自身.ctx.fs.文件网址(根),自身.ctx.fs.文件网址(目标)),#相对路径
            'entries':[_目录条目(项) for 项 in 子项列表[:上限]],#截断
            'truncated':len(子项列表)>上限,#是否截断
        }#结束

    @_远程
    def changes(自身,工作区文件作用域,信号):
        """流式推送工作区内每一次 `fs/observed` 观察。"""
        yield from 自身._供给.跟随(工作区文件作用域['workspaceRoot'],信号)#委托供给

    def _解析页(自身,范围):
        """应用页缺省与上限；请求不得隐式携带它们。范围为 dict。"""
        偏移=1 if 'offset' not in 范围 else _至少整数(范围['offset'],1,'offset')#缺省 1
        限额=自身._配置['maxLines'] if 'limit' not in 范围 else _至少整数(范围['limit'],1,'limit')#缺省 maxLines
        if 限额>自身._配置['maxLines']:#超上限
            raise 远程错误('gateway/bad-request','limit must be at most '+str(自身._配置['maxLines']),{})#拒绝
        return 偏移,限额#页窗

    def _解析窗(自身,范围,路径):
        """应用字节窗缺省与上限；更大窗口拒绝而非截短。范围为 dict。"""
        偏移=0 if 'offset' not in 范围 else _至少整数(范围['offset'],0,'offset')#缺省 0
        长度=自身._配置['maxBytes'] if 'length' not in 范围 else _至少整数(范围['length'],1,'length')#缺省 maxBytes
        if 偏移+长度>安全整数上限:#和越界
            raise 远程错误('gateway/bad-request','offset plus length must stay a safe integer',{})#拒绝
        if 长度>自身._配置['maxBytes']:#超上限
            raise 远程错误(
                'workspace-file/too-large',
                str(长度)+' bytes of "'+路径+'" exceed the '+str(自身._配置['maxBytes'])+' byte cap',
                {'path':路径,'limit':自身._配置['maxBytes']},
            )#拒绝
        return 偏移,长度#字节窗

    def _检视(自身,工作区文件作用域,路径,信号):
        """门禁到路径自身类型已知为止。"""
        if len(路径)==0:#空路径
            raise 远程错误('gateway/bad-request','path is required',{})#拒绝
        工作区根=工作区文件作用域['workspaceRoot']#根路径
        根=自身.ctx.fs.解析(工作区根,{'signal':信号})#解析根目标
        条目=自身.ctx.fs.链接状态(路径,{'cwd':工作区根},信号)#路径级 lstat
        if 条目 is None:#不存在
            raise 远程错误('workspace-file/not-found','no entry at "'+路径+'"',{'path':路径})#拒绝
        return 根,工作区根,条目#三元组

    def _围栏(自身,根,工作区根,路径,信号):
        """解析已检视路径；工作区不含则拒绝。"""
        目标=自身.ctx.fs.解析(路径,{'cwd':工作区根,'signal':信号})#解析
        if not 自身.ctx.fs.包含(根,目标):#根外
            raise 远程错误('workspace-file/outside-workspace','"'+路径+'" is outside the workspace',{'path':路径})#拒绝
        return 目标#目标

    def _定位文件(自身,工作区文件作用域,路径,信号):
        """普通文件的全部关，止于命名版本与大小的那次 stat；读路径允许根外。"""
        _根,工作区根,条目=自身._检视(工作区文件作用域,路径,信号)#检视
        if 条目['type']!='file':#非普通文件
            raise 远程错误(
                'workspace-file/not-regular-file',
                '"'+路径+'" is a '+str(条目['type']),
                {'path':路径,'kind':条目['type']},
            )#拒绝
        目标=自身.ctx.fs.解析(路径,{'cwd':工作区根,'signal':信号})#解析（允许根外）
        信息=自身.ctx.fs.状态(目标,信号)#再 stat
        if 信息 is None:#已消失
            raise 远程错误('workspace-file/not-found','no entry at "'+路径+'"',{'path':路径})#拒绝
        if 信息['type']!='file':#种类变了
            raise 远程错误(
                'workspace-file/not-regular-file',
                '"'+路径+'" is a '+str(信息['type']),
                {'path':路径,'kind':信息['type']},
            )#拒绝
        return 目标,信息#定位结果

    def _状态于(自身,目标,信息):
        """投影为线路 stat。信息为跨包 dict。"""
        状态={'absolutePath':自身.ctx.fs.进程路径(目标),'version':信息['version']}#必填
        if 'size' in 信息:#有大小
            状态['bytes']=信息['size']#带上
        return 状态#stat

    def _切页于(自身,目标,偏移,限额,信号,路径):
        """流式读文本并切页；把后端非文本拒绝归类。"""
        try:
            return _切页(自身.ctx.fs.流文本(目标,信号),偏移,限额,自身._配置['maxBytes'],路径)#切页
        except 远程错误:
            raise#本包错误原样
        except BaseException as 错误:
            if _是否非文本拒绝(错误):#后端非文本
                raise 远程错误('workspace-file/not-text','"'+路径+'" is not UTF-8 text',{'path':路径},原因=错误)#映射
            raise#其他原样


def 应用(上下文,配置值=None):
    """挂载工作区文件 Remote 拥有者。"""
    工作区文件(上下文,配置值)#构造即登记


# changes 为 stream 模式 Remote（对齐 @Remote({ mode: 'stream' })）
_变更标记=getattr(工作区文件.changes,'_typert_remote_marker',None)#装饰器标记
if isinstance(_变更标记,dict):#有标记
    _变更标记['mode']='stream'#流式交付


name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=工作区文件#框架槽：默认导出
