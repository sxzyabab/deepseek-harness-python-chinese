'工作区文件：只读预览、工作区目录列举，以及按目标的文件观察流'
import ntpath,posixpath,re#按执行世界选择路径库，并识别路径里的方案
from urllib.parse import unquote as 百分号解码,urlparse as 解析网址#file URI 还原工作区相对路径
from ...依赖.schemastery import 正整数字段#部署上限
from ...基础设施.通用工具 import utf8字节数#页的 UTF-8 字节
from ...类型化远程调用.协议 import 远程,远程服务#Remote 标记与服务基类
from . import 变更,类型,异常,客户端#同目录模块。客户端只作为包导出
from .异常 import 远程错误#本包失败
from .变更 import 工作区变更供给#changes 的生产者

__all__=['工作区文件','默认','变更','类型','异常','客户端']#不转发客户端里的类

安全整数上限=9007199254740991#JSON 能精确表示的最大整数
空字节=chr(0)#页里出现就视为二进制
方案模式=re.compile(r'^[a-z][a-z\d+.-]*:',re.IGNORECASE)#带方案的路径


def 至少整数(值,最小,名):
    '拒绝线协议承认、但窗口不能用来索引文件的数'
    if isinstance(值,bool) or not isinstance(值,int) or 值<最小 or 值>安全整数上限:#非安全整数或太小
        raise 远程错误('gateway/bad-request',名+' must be a safe integer of at least '+str(最小),{})#拒绝
    return 值#整数


def 目录条目(子项):
    '剥掉子目标，线路只留名字和元数据'
    条目={'name':子项['name'],'type':子项['type']}#基名和种类
    if 'size' in 子项 and 子项['size'] is not None:#后端报了大小
        条目['size']=子项['size']#带上
    return 条目#条目


class 工作区文件配置:
    '一页、一整文件、一行窗和一次列举的部署上限'
    def __init__(自身):
        '四个上限都是正整数，整文件另有安全整数上界'
        自身.字段={#键到字段
            'maxBytes':正整数字段(默认值=2*1024*1024,最小=1),#单页和单窗字节，含上限
            'maxFileBytes':正整数字段(默认值=32*1024*1024,最小=1,最大=安全整数上限-1),#整文件字节，含上限
            'maxLines':正整数字段(默认值=5000,最小=1),#页行数的缺省和上限
            'maxEntries':正整数字段(默认值=2000,最小=1),#目录条目上限
        }#字段结束

    def 校验数据(自身,数据=None):
        '缺的键填缺省。不是整数或超出上限就拒绝，并交回四个数字'
        if 数据 is None:#没给配置
            数据={}#全用缺省
        if not isinstance(数据,dict):#不是对象
            raise TypeError('workspace-files config must be an object')#拒绝
        结果={}#归一化后的上限
        for 键,字段 in 自身.字段.items():#逐项
            if 键 in 数据:#调用方给了
                值=数据[键]#用给的
            else:#省略
                值=字段.默认值#缺省
            if isinstance(值,bool) or not isinstance(值,int) or 值<字段.最小 or 值>安全整数上限:#不是可用整数
                raise TypeError(键+' must be an integer within its cap')#拒绝
            if 字段.最大 is not None and 值>字段.最大:#超过该字段上界
                raise TypeError(键+' must be an integer within its cap')#拒绝
            结果[键]=值#收下
        return 结果#交给构造


class 工作区文件(远程服务):
    '经组合文件系统做宿主远程读取，以及工作区目录观察'
    inject=['fs','sandboxPolicy','sessions','typert']#文件系统、沙箱回落根、会话、查找
    Config=工作区文件配置()#加载器先校验再构造
    name='workspace-files'#插件显示名
    def __init__(自身,上下文,配置):
        '挂上 workspaceFiles，并在会话与查找就绪后登记 workspaceFileScope'
        super().__init__(上下文,'workspaceFiles')#服务键即命名空间
        自身._配置=配置#已填好缺省的上限
        自身._供给=工作区变更供给(上下文)#按目标的变更流

        def 登记查找(子上下文,*位置参数):
            '等 sessions 和 typert 之后登记查找'
            def 解析(会话标识):
                '解析会话的工作区根，不读事件正文，也不激活智能体'
                存活=子上下文.sessions.获取(会话标识)#在线会话
                头=存活.header if 存活 is not None else None#在线头
                if 头 is None:#不在线
                    持久化=子上下文.获取服务('sessionPersistence',False)#可选持久化
                    快照=None if 持久化 is None else 持久化.观察(会话标识)#轻量观察
                    头=None if 快照 is None else 快照['header']#冷头
                if 头 is None:#没有这份会话
                    return None#查找缺席
                if 'cwd' in 头 and 头['cwd'] is not None:#头里有工作目录
                    根=头['cwd']#用它
                else:#没有 cwd
                    根=子上下文.sandboxPolicy.workspaceRoot#部署回落根
                return {'sessionId':会话标识,'workspaceRoot':根}#作用域
            子上下文.typert.lookups.register('workspaceFileScope',{#查找
                'parameter':'workspaceFileScope',#参数名
                'wire':'workspaceFileScopeId',#线路字段
                'resource':'session',#资源种类
                'hostTypeSymbol':'@deepseek-ai/dsh-api-workspace-files#WorkspaceFileScope',#宿主类型
                'wireTypeSymbol':'@deepseek-ai/dsh-session/types#SessionId',#线路类型
                'resolve':解析,#解析
            })#登记结束
        上下文.依赖启动(['sessions','typert'],登记查找)#等这两项

    @远程
    def read(自身,工作区文件作用域,路径,范围,信号):
        '读 UTF-8 文件的一页行。工作区外的文件也可以读'
        页窗=自身._解析页(范围)#行窗
        目标,信息=自身._定位文件(工作区文件作用域,路径,信号)#普通文件
        页=自身._切页(目标,页窗['offset'],页窗['limit'],信号,路径)#切页
        if 空字节 in 页['text']:#含 NUL
            raise 远程错误('workspace-file/not-text','"'+路径+'" contains NUL bytes',{'path':路径})#不是文本
        结果=自身._状态于(目标,信息)#版本和大小
        结果['offset']=页窗['offset']#请求的起始行
        结果['text']=页['text']#页文本
        结果['lines']=页['lines']#行数
        结果['eof']=页['eof']#是否含最后一行
        return 结果#一页

    @远程
    def readBytes(自身,工作区文件作用域,路径,选项,信号):
        '读原始字节。给了 range 就读窗口，否则按整文件上限读完'
        if 'range' in 选项:#有窗口
            窗口=自身._解析窗(选项['range'],路径)#字节窗
        else:#整文件
            窗口=None#用整文件上限
        if 'baseFile' in 选项:#相对另一个文件的目录
            已解析=自身._相对路径(工作区文件作用域,选项['baseFile'],路径,信号)#绝对路径
        else:#路径自己就是目标
            已解析=路径#原样
        目标,信息=自身._定位文件(工作区文件作用域,已解析,信号)#普通文件
        if 窗口 is not None:#窗口
            偏移=窗口['offset']#起点
            长度=窗口['length']#请求长度
            数据=自身.ctx.fs.读取字节范围(目标,窗口,信号)#至多 length 字节
            if 'size' not in 信息 or 信息['size'] is None:#后端没报大小
                到末=len(数据)<长度#短于请求则到末
            else:#有大小
                到末=偏移+len(数据)>=信息['size']#含最后一字节
            结果=自身._状态于(目标,信息)#版本和大小
            结果['offset']=偏移#起点
            结果['data']=数据#原始字节
            结果['eof']=到末#是否到末
            return 结果#窗口
        上限=自身._配置['maxFileBytes']#整文件上限
        try:#整文件
            数据=自身.ctx.fs.读取字节(目标,信号,上限)#不超过上限
        except BaseException as 原因:#后端拒绝
            if getattr(原因,'code',None)=='FS_TOO_LARGE':#超过整文件上限
                raise 远程错误(
                    'workspace-file/too-large',
                    '"'+路径+'" exceeds the '+str(上限)+' byte full-file cap',
                    {'path':路径,'limit':上限},
                    原因=原因,
                )#拒绝，不截断
            raise#其他原样
        结果=自身._状态于(目标,信息)#版本和大小
        结果['offset']=0#从文件头
        结果['data']=数据#全部字节
        结果['eof']=True#整文件
        return 结果#整文件

    @远程
    def stat(自身,工作区文件作用域,路径,信号):
        '报告普通文件的绝对路径、版本和大小，不含内容'
        目标,信息=自身._定位文件(工作区文件作用域,路径,信号)#定位
        return 自身._状态于(目标,信息)#状态

    @远程
    def list(自身,工作区文件作用域,路径,信号):
        '列举会话工作区里一个目录的直接子项。符号链接要解析成目录才列'
        根,工作区根,条目=自身._检视(工作区文件作用域,路径,信号)#路径自身
        if 条目['type']!='directory' and 条目['type']!='symlink':#不能列
            raise 远程错误(
                'workspace-file/not-directory',
                '"'+路径+'" is a '+str(条目['type']),
                {'path':路径,'kind':条目['type']},
            )#拒绝
        目标=自身._围栏(根,工作区根,路径,信号)#必须在工作区内
        if 条目['type']=='symlink':#末段是链接
            信息=自身.ctx.fs.状态(目标,信号)#跟随之后的种类
            if 信息 is None or 信息['type']!='directory':#不是目录
                raise 远程错误(
                    'workspace-file/not-directory',
                    '"'+路径+'" does not resolve to a directory',
                    {'path':路径,'kind':'symlink'},
                )#拒绝
        子项列表=自身.ctx.fs.列目录(目标,信号)#稳定名字顺序
        上限=自身._配置['maxEntries']#条目上限
        根网址=自身.ctx.fs.文件网址(根)#根的 file URI
        目标网址=自身.ctx.fs.文件网址(目标)#目录的 file URI
        根路径名=解析网址(根网址).path.rstrip('/')#去掉尾部斜杠
        目标路径名=解析网址(目标网址).path#目标路径
        if 目标路径名==根路径名:#就是根
            相对=''#空路径
        else:#根下
            片段=目标路径名[len(根路径名)+1:]#去掉根和分隔斜杠
            相对='/'.join(百分号解码(段) for 段 in 片段.split('/'))#按段解码
        return {#列举
            'path':相对,#工作区相对路径
            'entries':list(map(目录条目,子项列表[:上限])),#截到上限
            'truncated':len(子项列表)>上限,#是否丢掉了后面的
        }#结束

    @远程({'mode':'stream'})
    def changes(自身,工作区文件作用域,路径,信号):
        '监视一个文件，或一个目录的直接子项。目录仍限制在工作区内'
        return 自身._供给.跟随(工作区文件作用域['workspaceRoot'],路径,信号)#帧迭代器

    def _相对路径(自身,作用域,基准文件,路径,信号):
        '有 baseFile 时，路径必须是相对它目录的路径'
        相对=路径.replace('\\','/')#统一斜杠
        if 相对=='' or 相对.startswith('/') or 方案模式.match(相对) is not None or 空字节 in 相对:#不是相对路径
            raise 远程错误('gateway/bad-request','path must be relative when baseFile is provided',{})#拒绝
        目标,_信息=自身._定位文件(作用域,基准文件,信号)#基准文件
        绝对=自身.ctx.fs.进程路径(目标)#基准的绝对路径
        路径库=posixpath if 绝对.startswith('/') else ntpath#执行世界的路径库
        return 路径库.normpath(路径库.join(路径库.dirname(绝对),相对))#解析后的绝对路径

    def _解析页(自身,范围):
        '补上页的缺省，并拒绝超过 maxLines 的请求'
        if 'offset' in 范围:#给了起点
            偏移=至少整数(范围['offset'],1,'offset')#至少 1
        else:#省略
            偏移=1#第一行
        if 'limit' in 范围:#给了行数
            限额=至少整数(范围['limit'],1,'limit')#至少 1
        else:#省略
            限额=自身._配置['maxLines']#缺省即上限
        if 限额>自身._配置['maxLines']:#超过配置
            raise 远程错误('gateway/bad-request','limit must be at most '+str(自身._配置['maxLines']),{})#拒绝
        return {'offset':偏移,'limit':限额}#页窗

    def _解析窗(自身,范围,路径):
        '补上字节窗的缺省。超过 maxBytes 的窗口拒绝，不截短'
        if 'offset' in 范围:#给了起点
            偏移=至少整数(范围['offset'],0,'offset')#可以为 0
        else:#省略
            偏移=0#文件头
        if 'length' in 范围:#给了长度
            长度=至少整数(范围['length'],1,'length')#至少 1
        else:#省略
            长度=自身._配置['maxBytes']#缺省即上限
        if 偏移+长度>安全整数上限:#和不再是安全整数
            raise 远程错误('gateway/bad-request','offset plus length must stay a safe integer',{})#拒绝
        if 长度>自身._配置['maxBytes']:#超过单窗上限
            raise 远程错误(
                'workspace-file/too-large',
                str(长度)+' bytes of "'+路径+'" exceed the '+str(自身._配置['maxBytes'])+' byte cap',
                {'path':路径,'limit':自身._配置['maxBytes']},
            )#拒绝
        return {'offset':偏移,'length':长度}#窗口

    def _检视(自身,工作区文件作用域,路径,信号):
        '在跟随最后一段之前，先看路径自己的种类'
        if len(路径)==0:#空路径
            raise 远程错误('gateway/bad-request','path is required',{})#拒绝
        工作区根=工作区文件作用域['workspaceRoot']#会话根
        根=自身.ctx.fs.解析(工作区根,{'signal':信号})#根目标
        条目=自身.ctx.fs.链接状态(路径,{'cwd':工作区根},信号)#不跟随末段
        if 条目 is None:#没有
            raise 远程错误('workspace-file/not-found','no entry at "'+路径+'"',{'path':路径})#拒绝
        return 根,工作区根,条目#后续使用

    def _围栏(自身,根,工作区根,路径,信号):
        '解析路径。工作区不含它就拒绝'
        目标=自身.ctx.fs.解析(路径,{'cwd':工作区根,'signal':信号})#目标
        if not 自身.ctx.fs.包含(根,目标):#根外
            raise 远程错误('workspace-file/outside-workspace','"'+路径+'" is outside the workspace',{'path':路径})#拒绝
        return 目标#目标

    def _定位文件(自身,工作区文件作用域,路径,信号):
        '确认是普通文件，再 stat 一次拿到版本和大小。允许工作区外'
        _根,工作区根,条目=自身._检视(工作区文件作用域,路径,信号)#先看路径自身
        if 条目['type']!='file':#不是普通文件
            raise 远程错误(
                'workspace-file/not-regular-file',
                '"'+路径+'" is a '+str(条目['type']),
                {'path':路径,'kind':条目['type']},
            )#拒绝
        目标=自身.ctx.fs.解析(路径,{'cwd':工作区根,'signal':信号})#允许根外
        信息=自身.ctx.fs.状态(目标,信号)#再确认
        if 信息 is None:#两次之间消失了
            raise 远程错误('workspace-file/not-found','no entry at "'+路径+'"',{'path':路径})#拒绝
        if 信息['type']!='file':#种类变了
            raise 远程错误(
                'workspace-file/not-regular-file',
                '"'+路径+'" is a '+str(信息['type']),
                {'path':路径,'kind':信息['type']},
            )#拒绝
        return 目标,信息#定位结果

    def _状态于(自身,目标,信息):
        '收成线路上的 stat。没有大小就不带 bytes'
        状态={'absolutePath':自身.ctx.fs.进程路径(目标),'version':信息['version']}#必有
        if 'size' in 信息 and 信息['size'] is not None:#后端报了大小
            状态['bytes']=信息['size']#整文件字节
        return 状态#状态

    def _切页(自身,目标,偏移,限额,信号,路径):
        '流式读文本并切出这一页。后端拒绝非 UTF-8 时改成 not-text'
        try:#读和切
            块序列=自身.ctx.fs.流文本(目标,信号)#已解码块
            末行=偏移+限额-1#本页最后一行
            行列表=[]#页内行
            当前=''#尚未换行的一段
            字节数=0#本页 UTF-8 字节
            行号=1#文件中的行号

            def 验收(增量):
                '加上这段字节。超过 maxBytes 就失败，不截短'
                nonlocal 字节数#累计
                字节数=字节数+增量#加上
                if 字节数>自身._配置['maxBytes']:#超限
                    raise 远程错误(
                        'workspace-file/too-large',
                        'lines '+str(偏移)+'-'+str(末行)+' of "'+路径+'" exceed the '+str(自身._配置['maxBytes'])+' byte cap',
                        {'path':路径,'limit':自身._配置['maxBytes']},
                    )#拒绝

            def 完成一行():
                '收下当前行。行与行之间的换行也算一个字节'
                nonlocal 当前#缓冲
                if len(行列表)>0:#不是页内第一行
                    验收(1)#连接用的换行
                行列表.append(当前)#收下
                当前=''#清空

            for 块 in 块序列:#逐块
                位置=0#块内位置
                while 位置<len(块):#扫这块
                    if 行号>末行:#页已经满
                        return {'text':'\n'.join(行列表),'lines':len(行列表),'eof':False}#还没到文件尾
                    换行=块.find('\n',位置)#下一个换行
                    if 换行==-1:#这块剩余没有换行
                        片段=块[位置:]#剩下部份
                    else:#有换行
                        片段=块[位置:换行]#换行之前
                    if 行号>=偏移:#落在页内
                        验收(utf8字节数(片段))#这段的字节
                        当前=当前+片段#接上
                    if 换行==-1:#块用完了
                        break#下一块
                    if 行号>=偏移:#页内的一行结束
                        完成一行()#收下
                    行号=行号+1#下一行
                    位置=换行+1#越过换行
            if len(当前)>0:#文件末尾没有换行
                完成一行()#收下最后一行
            return {'text':'\n'.join(行列表),'lines':len(行列表),'eof':True}#读到文件尾
        except BaseException as 错误:#读或切失败
            if getattr(错误,'code',None)=='FS_NOT_TEXT':#后端拒绝非文本
                raise 远程错误('workspace-file/not-text','"'+路径+'" is not UTF-8 text',{'path':路径},原因=错误)#改码
            raise#页超限和其他失败原样


默认=工作区文件#插件类
default=默认#框架槽
