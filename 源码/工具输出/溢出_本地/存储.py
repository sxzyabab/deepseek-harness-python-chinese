"""本地溢出后端的无 Cordis 存储机制：私有会话作用域目录选择、安全名派生、路径穿越防护，以及独占仅所有者写入。从服务类拆出（同 dsh-bash-local 的 run），使文件系统行为可在没有 ctx、也不依赖 OS 临时目录的情况下做单元测试。"""
import os,hashlib,secrets,tempfile,re#路径、哈希、随机前缀、临时目录与安全字符判定

默认根=None#惰性私有溢出根，进程内单例
安全字符=re.compile(r'^[A-Za-z0-9._-]$')#字面量安全且不含波浪号的单码元

# 保存文本选项：已解析的根，以及存储所需的请求字段。
保存文本选项字段=(#保存文本选项字段元组
    'root',#溢出根目录（配置值或惰性私有默认）
    'sessionId',#所属会话 id（限定目录作用域）
    'suggestedName',#调用方建议的基名；使用前清洗成一个安全段
    'content',#要持久的全文
)#保存文本选项字段结束

# 已写入的溢出文件。
已保存文本字段=(#已保存文本字段元组
    'path',#文件路径
    'bytes',#字节数
)#已保存文本字段结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 私有根():#默认私有溢出根
    """默认溢出根：OS 临时目录下惰性创建的私有（0700）每进程目录。可预测的全世界可读路径会让其他本地用户读到溢出的工具输出，或预先植入符号链接；mkdtemp 给出不可预测后缀和 0700 语义。"""
    global 默认根#改进程内单例
    if 默认根 is None:#首次调用
        默认根=tempfile.mkdtemp(prefix='dsh-spill-')#创建0700临时目录
    return 默认根#返回已缓存根

def 编码段(原始):#编码安全路径段
    """把任意字符串编码成一个安全路径段，对全部 JS（UTF-16）字符串单射。会话 id / 建议名是未信任输入，因此在任何文件系统使用前中和 ../、绝对路径、NUL 和分隔符。每个码元要么保持字面量（[A-Za-z0-9._-]，去掉 ~），要么转义成 ~XXXX；~ 自身也转义，因此映射可逆且不同输入永不碰撞。整段记号 . / .. 被转义，使它们永远不能穿越。空字符串编码成 ~（永不产生空段）。（镜像 JSONL 持久化后端的 encodeSegment。）"""
    if len(原始)==0:#空串
        return '~'#编成~
    if 原始=='.':#单独的点
        return '~002E'#转义点
    if 原始=='..':#双点
        return '~002E~002E'#转义双点
    输出=''#编码结果
    字节=原始.encode('utf-16-le')#按 UTF-16 码元对齐 JS charCodeAt
    下标=0#字节下标
    while 下标<len(字节):#逐码元
        码=字节[下标]|(字节[下标+1]<<8)#小端拼成码元值
        片=chr(码) if 码<0xD800 or 码>0xDFFF else None#BMP 可成字符；代理只走转义
        if 片 is not None and 片!='~' and 安全字符.match(片):#安全且不是波浪号
            输出+=片#保持字面量
        else:#需转义
            输出+='~'+format(码,'04X')#写成~XXXX
        下标+=2#下一码元
    return 输出#返回编码段

def 会话目录(根,会话标识):#会话作用域目录
    """会话作用域目录：<root>/session-<hash(sessionId)>，短而稳定的哈希。"""
    哈希=hashlib.sha256(会话标识.encode('utf-8')).hexdigest()[:12]#会话id的短哈希
    return os.path.join(根,'session-'+哈希)#拼成session-<hash>

def 保存文本文件(选项):#写入溢出文本文件
    """把 content 写入会话作用域目录下的新文件，并返回其路径与字节长度。文件名是随机十六进制前缀加上已清洗的 suggestedName，因此不可预测（挫败共享根下的符号链接植入）且仍可读。打开是独占 + 仅所有者（wx, 0o600）：任何已存在路径都会失败——无论是否符号链接——因此预先植入的目标无法重定向写入。"""
    目录=会话目录(取字段(选项,'root'),取字段(选项,'sessionId'))#会话作用域目录
    os.makedirs(目录,mode=0o700,exist_ok=True)#确保私有目录存在
    安全名=编码段(取字段(选项,'suggestedName'))#清洗建议名
    路径=os.path.join(目录,secrets.token_hex(6)+'-'+安全名)#随机前缀加安全名
    内容=取字段(选项,'content')#全文
    字节数=len(内容.encode('utf-8'))#UTF-8字节长度
    标志=os.O_CREAT|os.O_EXCL|os.O_WRONLY#独占创建
    if os.name=='nt':#Windows
        标志|=os.O_BINARY#Windows二进制
    描述符=os.open(路径,标志,0o600)#独占仅所有者创建
    try:#写入正文
        os.write(描述符,内容.encode('utf-8'))#把全文写入
    finally:#无论成败都关句柄
        os.close(描述符)#关闭文件
    return {'path':路径,'bytes':字节数}#返回路径与字节数
