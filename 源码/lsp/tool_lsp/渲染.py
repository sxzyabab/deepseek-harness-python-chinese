"""`lsp` 工具的纯格式化与坐标换算：一基↔零基 UTF-16 光标换算、按工作区分组的位置渲染（解析 `file:` URI）、完整结果封顶，以及 UI 展示。无 I/O——UI 可能在实时流式与回放上都调用展示器，因此它只依赖工具参数。
"""
import ntpath#Windows 路径相对规则
import posixpath#POSIX 路径相对规则
import re#盘符路径探测
from urllib.parse import urlparse#解析 file URI

语言服务器操作=('goToDefinition','findReferences','goToImplementation','hover')#四种操作的运行时元组
默认最大位置数=100#渲染位置在追加省略标记前的默认上限
默认最大结果字符=16000#完整渲染工具结果（含截断元数据）的默认字符上限
盘符路径=re.compile(r'^/[a-z](?::|%3A)',re.I)#前导 /X: 或 /X%3A 视为 Windows 盘符段

def 是否整数(值):#对齐 JS Number.isInteger
    """对齐 JS Number.isInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return True#整数
    if isinstance(值,float):#浮点
        return 值.is_integer()#整值浮点
    return False#其它类型

def 是否操作(值):#收窄为四种操作之一
    """字符串是否为四种操作之一。"""
    return 值 in 语言服务器操作#查运行时元组

def 一基(值,名称):#校验一基正整数坐标
    """校验一基坐标为正整数。"""
    if not 是否整数(值) or 值<1:#不是正整数
        raise Exception(名称+' must be a positive integer (one-based)')#拒绝非法坐标
    return int(值)#返回已校验整值

def 解析语言服务器参数(参数):#校验参数并换算成零基位置
    """校验并转换模型参数：operation 必须是四种之一；line/character 是正的一基整数，转换成 seam 的零基位置。
    @param 参数 - schema 已校验的原始参数（映射或对象）
    @returns 带零基位置的已校验输入
    @throws Exception 操作未知或坐标不是正整数时
    """
    操作=参数['operation'] if isinstance(参数,dict) else getattr(参数,'operation')#取出操作名
    文件路径=参数['file_path'] if isinstance(参数,dict) else getattr(参数,'file_path')#取出源路径
    行=参数['line'] if isinstance(参数,dict) else getattr(参数,'line')#取出一基行号
    列=参数['character'] if isinstance(参数,dict) else getattr(参数,'character')#取出一基列
    if not 是否操作(操作):#操作不在四种之中
        raise Exception('operation must be one of '+', '.join(语言服务器操作))#拒绝未知操作
    if str(文件路径).strip()=='':#空路径
        raise Exception('file_path must be a non-empty string')#拒绝空路径
    行号=一基(行,'line')#校验一基行号
    列号=一基(列,'character')#校验一基列
    return {#组装已校验输入
        'operation':操作,#四种操作之一
        'filePath':文件路径,#源文件路径
        # 模型从1计数；seam（以及协议）从0计数。
        'position':{'line':行号-1,'character':列号-1},#零基查询光标
    }#已校验输入结束

def 封顶结果(文本,最大字符,标签):#按字符上限截断完整结果
    """封顶完整渲染结果，截断通知本身也计入上限。"""
    if len(文本)<=最大字符:#未超限则原样
        return 文本#原样
    通知='\n… '+标签+' truncated (limit '+str(最大字符)+' characters).'#截断通知
    if len(通知)>=最大字符:#通知本身已超限则只留通知前缀
        return 通知[:最大字符]#截到上限
    return 文本[:最大字符-len(通知)]+通知#正文截到能放下通知

def 百分号解码路径(路径名,禁止反斜杠):#对齐 Node 对 pathname 的百分号解码约束
    """解码 pathname；拒绝 NUL、编码的 `/`，以及（Windows 世界）编码的 `\\`。"""
    片段=[]#原文片段与已解码字节交错缓冲
    字节串=bytearray()#连续百分号字节
    索引=0#扫描下标
    长度=len(路径名)#总长
    def 冲刷字节():#把已积字节按 UTF-8 冲成文本
        """把积下的百分号字节按 UTF-8 解码并并入片段。"""
        nonlocal 字节串#改外层缓冲
        if len(字节串)==0:#无积压
            return#无事
        try:#UTF-8 解码
            片段.append(字节串.decode('utf-8'))#收下文本
        except UnicodeDecodeError:#畸形 UTF-8
            raise Exception('URI malformed')#对齐解码失败
        字节串=bytearray()#清空积压
    while 索引<长度:#逐字符扫描
        字符=路径名[索引]#当前字符
        if 字符!='%':#普通字符
            冲刷字节()#先冲掉积压百分号字节
            片段.append(字符)#原样收下
            索引+=1#前进一步
            continue#下一字符
        if 索引+2>=长度:#不完整百分号序列
            raise Exception('URI malformed')#对齐解码失败
        十六=路径名[索引+1:索引+3]#两位十六进制
        if 十六.upper()=='2F':#编码的正斜杠
            raise Exception('Path must not include encoded / characters')#拒绝编码分隔符
        if 禁止反斜杠 and 十六.upper()=='5C':#Windows 世界拒绝编码反斜杠
            raise Exception('Path must not include encoded \\ characters')#拒绝编码分隔符
        try:#解析字节
            字节=int(十六,16)#十六进制字节
        except ValueError:#非法十六进制
            raise Exception('URI malformed')#对齐解码失败
        if 字节==0:#NUL
            raise Exception('Path must not include encoded NUL characters')#拒绝 NUL
        字节串.append(字节)#积入 UTF-8 字节
        索引+=3#跳过 %XX
    冲刷字节()#收尾冲刷
    return ''.join(片段)#拼回路径

def 视窗文件路径(主机名,路径名):#按 Windows 世界解码 file URL
    """对齐 Node fileURLToPath(..., { windows: true })。"""
    解码=百分号解码路径(路径名,True)#Windows 禁止编码反斜杠
    if 主机名:#UNC：\\host\share\...
        if 解码=='' or 解码=='/':#只有斜杠不够成份额
            路径='\\\\'+主机名+'\\'#UNC 根
        else:#带份额路径
            路径='\\\\'+主机名+解码.replace('/','\\')#正斜杠改反斜杠
        return 路径#UNC 路径
    if len(解码)>=3 and 解码[0]=='/' and 解码[2]==':' and (('a'<=解码[1]<='z') or ('A'<=解码[1]<='Z')):# /C:/...
        路径=解码[1:].replace('/','\\')#去掉前导斜杠并改反斜杠
        return 路径#盘符路径
    if 解码.startswith('/'):#无盘符的绝对形
        return 解码.replace('/','\\')#改反斜杠
    raise Exception('File URL path must be absolute')#拒绝相对形

def 可移植操作系统接口文件路径(主机名,路径名):#按 POSIX 世界解码 file URL
    """对齐 Node fileURLToPath(..., { windows: false })。"""
    if 主机名:#POSIX 不允许 authority
        raise Exception('File URL host must be empty')#拒绝带主机
    解码=百分号解码路径(路径名,False)#POSIX 允许字面反斜杠经 %5C
    if not 解码.startswith('/'):#必须绝对
        raise Exception('File URL path must be absolute')#拒绝相对形
    return 解码#POSIX 路径

def 文件路径(网址,视作视窗):#解码 file URL 为路径
    """按执行世界解码 file URL，同时吞掉畸形 URL 失败。"""
    try:#按世界解码
        主机=网址.hostname if 网址.hostname is not None else ''#authority 主机
        路径名=网址.path if 网址.path is not None else ''#pathname
        if 视作视窗:#Windows 世界
            路径=视窗文件路径(主机,路径名)#Windows 解码
        else:#POSIX 世界
            路径=可移植操作系统接口文件路径(主机,路径名)#POSIX 解码
        if '\0' in 路径:#含 NUL 则视为无效
            return None#交回原 URI
        return 路径#解码路径
    except Exception:#畸形转义、authority 或编码分隔符
        # fileURLToPath 会拒绝畸形转义、authority 以及编码过的路径分隔符。
        return None#解码失败则交回原 URI

def 解析网址(原文):#对齐 new URL，失败则抛出
    """解析绝对 URI；明显畸形则抛出。"""
    if 原文.startswith('file://['):#未闭合 IPv6 形 authority
        raise Exception('Invalid URL')#对齐 URL 构造失败
    解析=urlparse(原文)#拆 URI
    if 解析.scheme=='':#没有 scheme
        raise Exception('Invalid URL')#对齐 URL 构造失败
    return 解析#ParseResult

def 渲染网址(网址,工作区网址):#把位置 URI 转成显示路径
    """解析位置 URI，不套用 harness 宿主的路径规则。合法 file: URI 若落在提供方规范工作区 URI 下则变成工作区相对路径，否则变成由 URI 推导的绝对路径；畸形与非 file: URI 原样保留。
    @param 网址 - seam 给出的目标 URI
    @param 工作区网址 - 提供方的规范工作区 file: URI
    @returns 显示路径或原样 URI
    """
    if not 网址.startswith('file:'):#非 file URI 原样
        return 网址#原样
    try:#解析两端 URI
        目标=解析网址(网址)#解析目标
        工作区=解析网址(工作区网址)#解析工作区
    except Exception:#URI 畸形
        return 网址#解析失败则原样
    if 工作区.scheme!='file':#工作区不是 file 则原样
        return 网址#原样
    # file: URI 不携带其世界的操作系统，因此前导 /X: 段被读成 Windows 盘符。字面根在 /c:/... 的 POSIX 工作区会渲染错（仅显示；编辑与读取仍用精确 URI）。
    工作区主机=工作区.hostname if 工作区.hostname is not None else ''#工作区主机
    目标主机=目标.hostname if 目标.hostname is not None else ''#目标主机
    视窗世界=len(工作区主机)>0 or 盘符路径.search(工作区.path or '') is not None#工作区是否 Windows 世界
    目标视窗世界=视窗世界 and (len(目标主机)>0 or 盘符路径.search(目标.path or '') is not None)#目标是否同一 Windows 世界
    工作区路径=文件路径(工作区,视窗世界)#解码工作区路径
    目标路径=文件路径(目标,目标视窗世界)#解码目标路径
    if 工作区路径 is None or 目标路径 is None:#解码失败则原样
        return 网址#原样
    if 视窗世界!=目标视窗世界:#世界不一致则给绝对路径
        return 目标路径#绝对显示路径
    规则=ntpath if 视窗世界 else posixpath#按世界选路径规则
    try:#相对工作区
        相对=规则.relpath(目标路径,工作区路径)#相对路径
    except ValueError:#跨盘等无法相对
        相对=目标路径#退回绝对
    分隔=规则.sep#路径分隔符
    区外=(相对=='..' or 相对.startswith('..'+分隔) or 规则.isabs(相对))#是否落在工作区外
    渲染='.' if 相对=='' else (目标路径 if 区外 else 相对)#根则点，区外则绝对，否则相对
    if 视窗世界:#Windows 显示统一用正斜杠
        return 渲染.replace('\\','/')#正斜杠化
    return 渲染#POSIX 原样

def 格式化位置(位置们,工作区网址,最大位置数,最大结果字符):#按文件分组渲染位置列表
    """按文件分组渲染位置结果，把每个零基位置换回一基 path:line:character 条目。工作区内的 file: URI 变成工作区相对路径；工作区外变成由 URI 推导的绝对路径；非 file: URI 原样保留。先应用 maxLocations，按条数截断时追加省略标记，再应用完整结果上限。
    @param 位置们 - seam 的位置列表（可能为空）
    @param 工作区网址 - 提供方的规范工作区 file: URI
    @param 最大位置数 - 截断前的条数上限
    @param 最大结果字符 - 完整渲染文本上限，含截断元数据
    @returns 渲染文本；没有任何位置时为一条独立的无结果行
    """
    if len(位置们)==0:#无结果
        return 封顶结果('No results.',最大结果字符,'locations')#无结果走封顶
    展示=位置们[:最大位置数]#先按条数截取
    省略=len(位置们)-len(展示)#被省略的条数
    分组={}#按显示路径分组（插入序）
    顺序=[]#分组键插入序
    for 位置 in 展示:#逐条换算显示路径与一基坐标
        网址=位置['uri'] if isinstance(位置,dict) else getattr(位置,'uri')#位置 URI
        范围=位置['range'] if isinstance(位置,dict) else getattr(位置,'range')#范围
        起点=范围['start'] if isinstance(范围,dict) else getattr(范围,'start')#起点
        行=(起点['line'] if isinstance(起点,dict) else getattr(起点,'line'))+1#零基行转一基
        列=(起点['character'] if isinstance(起点,dict) else getattr(起点,'character'))+1#零基列转一基
        路径=渲染网址(网址,工作区网址)#URI 转显示路径
        if 路径 not in 分组:#新路径
            分组[路径]=[]#新建条目表
            顺序.append(路径)#记下插入序
        分组[路径].append(路径+':'+str(行)+':'+str(列))#追加 path:line:character
    行们=[]#展平后的行
    for 路径 in 顺序:#按分组顺序展平
        行们.extend(分组[路径])#追加该路径全部条目
    if 省略>0:#有按条数省略
        单位='location' if 省略==1 else 'locations'#单复数
        行们.append('… '+str(省略)+' more '+单位+' omitted (limit '+str(最大位置数)+').')#追加省略标记
    return 封顶结果('\n'.join(行们),最大结果字符,'locations')#再按完整字符上限封顶

def 格式化悬停(悬停,最大结果字符):#渲染悬停并封顶
    """渲染悬停结果，最后应用 maxResultChars，并保证其标记落在上限内。
    @param 悬停 - 归一化悬停；无悬停为 None
    @param 最大结果字符 - 完整渲染文本上限，含截断元数据
    @returns 渲染后的悬停文本；None 时为一条独立的无结果行
    """
    if 悬停 is None:#无悬停
        文本='No hover information.'#固定文案
    else:#有悬停
        文本=悬停['contents'] if isinstance(悬停,dict) else getattr(悬停,'contents')#悬停正文
    return 封顶结果(文本,最大结果字符,'hover')#按字符上限封顶

def 呈现语言服务器调用(参数):#把参数映射成通用搜索卡片
    """待处理 lsp 调用的 UI 展示。使用通用搜索卡片；标题携带操作与一基光标，locations 聚焦被查询的行。共享位置形态没有列，因此标题保留列。
    @param 参数 - 原始工具参数
    @returns 通用调用视图
    """
    操作=参数['operation'] if isinstance(参数,dict) else getattr(参数,'operation')#操作名
    文件路径=参数['file_path'] if isinstance(参数,dict) else getattr(参数,'file_path')#源路径
    行=参数['line'] if isinstance(参数,dict) else getattr(参数,'line')#一基行
    列=参数['character'] if isinstance(参数,dict) else getattr(参数,'character')#一基列
    return {#组装展示
        'card':'generic',#通用卡片
        'kind':'search',#搜索种类
        'title':'LSP '+str(操作)+' '+str(文件路径)+':'+str(行)+':'+str(列),#操作与一基光标标题
        'locations':[{'path':文件路径,'line':行}],#聚焦被查询行
    }#通用调用视图结束
