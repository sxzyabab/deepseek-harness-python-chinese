"""内容寻址、仅所有者本地附件存储。对齐上游 attachment-local/src/store.ts。"""
import hashlib,os,uuid#摘要、路径与临时名
from ..附件 import 附件错误,附件标识,若已中止则抛出#附件缝
from .图像 import 检测图像,探测图像#图像检查
from .规范化 import 规范化图像#规范化
__all__=[#仅中文公开名
    '已准备图像文件字段','规范化图像路径','校验图像文件',
    '准备图像文件','提交已准备图像文件','保存图像文件','读取图像文件',
]#公开面结束

已准备图像文件字段=('data','ref')#已准备对象
标识模式=__import__('re').compile(r'^sha256:([a-f0-9]{64})$')#引用形态
耐久主目录=set()#进程内已证明耐久的主目录

def _摘要(数据):#sha256 十六进制
    """计算字节 sha256 十六进制摘要。"""
    return hashlib.sha256(数据).hexdigest()#十六进制

def _显示名(值):#剥离路径信息
    """剥离本地路径信息并清理控制字符。"""
    if 值 is None:#无名字
        return None#缺席
    叶=值[max(值.rfind('/'),值.rfind('\\'))+1:]#最后一段
    清理=''.join(字符 for 字符 in 叶 if ord(字符)>=32 and ord(字符)!=127).strip()[:255]#清理
    return None if 清理=='' else 清理#空则缺席

def _确保引用(引用):#解析引用中的 sha256
    """从引用解析 sha256 十六进制，非法则抛错。"""
    匹配=标识模式.match(str(引用['attachmentId']))#匹配形态
    if 匹配 is None:#非法
        raise 附件错误('Attachment reference is invalid.','INVALID_ATTACHMENT_REF')#拒绝
    return 匹配.group(1)#十六进制

def 规范化图像路径(根,引用):#不可变对象绝对路径
    """推导一条规范化附件的绝对不可变对象路径。"""
    摘要=_确保引用(引用)#sha256
    return os.path.join(根,'objects',摘要[:2],摘要)#分桶路径

def _检查元数据(数据,声明媒体类型,限额):#准入元数据检查
    """检查单图元数据并验证声明媒体类型。"""
    if len(数据)==0:#空图
        raise 附件错误('Image is empty.','INVALID_IMAGE')#拒绝
    已检测=检测图像(数据,{'maxPixels':限额['maxImagePixels'],'maxDimension':限额['maxImageDimension']})#全解码
    if 已检测['mediaType']!=声明媒体类型:#类型不符
        raise 附件错误('Declared image type does not match its bytes.','IMAGE_TYPE_MISMATCH')#拒绝
    return 已检测#通过

def 校验图像文件(输入,限额,策略):#全准入策略不落盘
    """运行完整准入策略含规范化，但不触盘。"""
    准备图像文件(输入,限额,策略)#与准备相同

def 准备图像文件(输入,限额,策略):#解码规范化但不触盘
    """解码、规范化并验证单条提交图像，不触盘。"""
    数据=输入['data']#字节
    if len(数据)>限额['maxImageBytes']:#单图字节过大
        raise 附件错误('Image exceeds the configured byte limit.','IMAGE_TOO_LARGE')#拒绝
    已检测=_检查元数据(数据,输入['mediaType'],限额)#元数据
    规范化=规范化图像(数据,已检测,策略)#规范化
    摘要=_摘要(规范化['data'])#内容摘要
    名字=_显示名(输入.get('name'))#显示名
    已缩小=已检测['width']!=规范化['width'] or 已检测['height']!=规范化['height']#是否缩小
    引用={#耐久引用事实
        'attachmentId':附件标识(f'sha256:{摘要}'),
        'mediaType':规范化['mediaType'],
        'width':规范化['width'],
        'height':规范化['height'],
        'bytes':len(规范化['data']),
    }#引用结束
    if 名字 is not None:#可选名
        引用['name']=名字#带上
    if 已缩小:#记录原始尺寸
        引用['originalDimensions']={'width':已检测['width'],'height':已检测['height']}#原始
    return {'data':规范化['data'],'ref':引用}#已准备

def _同步目录(路径):#POSIX 目录 fsync
    """使目录项耐久；Windows 跳过。"""
    if os.name=='nt':#Windows
        return#NTFS 日志负责
    描述符=os.open(路径,os.O_RDONLY)#只读打开目录
    try:#同步
        os.fsync(描述符)#刷目录项
    finally:#关闭
        os.close(描述符)#关掉

def _确保耐久目录(路径,边界):#创建并同步祖先
    """创建私有目录树并同步到调用方担保的耐久边界。"""
    目标=os.path.abspath(路径)#绝对目标
    停止=os.path.abspath(边界)#绝对边界
    os.makedirs(目标,mode=0o700,exist_ok=True)#递归创建
    os.chmod(目标,0o700)#收紧权限
    层级=目标#从目标向上
    while 层级!=停止:#未到边界
        父=os.path.dirname(层级)#父目录
        _同步目录(父)#同步父项
        if 父==层级:#到根
            return#结束
        层级=父#上移

def _确保耐久主目录(路径):#证明主目录耐久
    """建立本进程对 DSH_HOME 入口及祖先的耐久证明。"""
    主目录=os.path.abspath(路径)#绝对主目录
    if 主目录 not in 耐久主目录:#尚未证明
        根=os.path.splitdrive(主目录)[0]+os.sep if os.name=='nt' else os.sep#文件系统根
        _确保耐久目录(主目录,根)#同步到根
        耐久主目录.add(主目录)#记下
    return 主目录#返回

def 提交已准备图像文件(根,已准备):#发布已验证对象
    """在版本化附件根下发布已验证规范化图像。"""
    字节=已准备['data']#规范化字节
    摘要=_确保引用(已准备['ref'])#引用摘要
    if _摘要(字节)!=摘要 or len(字节)!=已准备['ref']['bytes']:#字节与引用不符
        raise 附件错误('Prepared attachment bytes do not match their reference.','ATTACHMENT_CORRUPT')#损坏
    桶=os.path.join(根,'objects',摘要[:2])#分桶目录
    暂存=os.path.join(根,'tmp')#暂存目录
    边界=_确保耐久主目录(os.path.dirname(os.path.dirname(os.path.abspath(根))))#DSH_HOME 边界
    _确保耐久目录(桶,边界)#桶目录
    _确保耐久目录(暂存,边界)#暂存目录
    临时=os.path.join(暂存,str(uuid.uuid4()))#随机暂存名
    目标=规范化图像路径(根,已准备['ref'])#最终对象路径
    try:#写暂存再硬链
        描述符=os.open(临时,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)#独占创建
        try:#写入
            os.write(描述符,字节)#写完整内容
            os.fsync(描述符)#刷文件
        finally:#关闭
            os.close(描述符)#关掉
        try:#硬链提交
            os.link(临时,目标)#同 inode 多硬链名
        except OSError as 错误:#争用
            if not (isinstance(错误,OSError) and 错误.errno==getattr(__import__('errno'),'EEXIST',17)):#非已存在
                raise 错误#原样
            现有=open(目标,'rb').read()#读已有
            if _摘要(现有)!=摘要:#内容不一致
                raise 附件错误('Stored attachment failed integrity verification.','ATTACHMENT_CORRUPT')#损坏
        try:#删暂存名
            os.unlink(临时)#去掉暂存链接
        except OSError:#可能已删
            pass#尽力
        os.chmod(目标,0o400)#只读
        _同步目录(桶)#同步桶
        _同步目录(os.path.join(根,'objects'))#同步 objects
    except 附件错误:#已是附件错误
        raise#原样
    except BaseException as 错误:#其他失败
        try:#清理暂存
            os.unlink(临时)#删暂存
        except OSError:#可能未建成
            pass#吞掉
        raise 附件错误('Unable to persist image attachment.','ATTACHMENT_WRITE_FAILED',{'cause':错误})#包装
    return 已准备['ref']#耐久引用

def 保存图像文件(根,输入,限额,策略):#一次解码规范化并发布
    """解码规范化一次并发布已准备对象。"""
    return 提交已准备图像文件(根,准备图像文件(输入,限额,策略))#准备后提交

def 读取图像文件(根,引用,信号=None):#读取并校验
    """读取并校验一条内容寻址图像。"""
    若已中止则抛出(信号)#取消优先
    摘要=_确保引用(引用)#期望摘要
    try:#读文件
        with open(规范化图像路径(根,引用),'rb') as 文件:#打开对象
            数据=文件.read()#读字节
    except FileNotFoundError:#缺失
        raise 附件错误('Attachment object is missing.','ATTACHMENT_NOT_FOUND')#未找到
    except OSError as 错误:#其他 IO 失败
        若已中止则抛出(信号)#取消再检
        raise 附件错误('Unable to read image attachment.','ATTACHMENT_READ_FAILED',{'cause':错误})#读取失败
    若已中止则抛出(信号)#读后再检
    if _摘要(数据)!=摘要:#摘要不符
        raise 附件错误('Stored attachment failed integrity verification.','ATTACHMENT_CORRUPT')#损坏
    元数据=探测图像(数据)#仅头探测
    若已中止则抛出(信号)#探测后再检
    if (元数据['mediaType']!=引用['mediaType'] or len(数据)!=引用['bytes']
        or 元数据['width']!=引用['width'] or 元数据['height']!=引用['height']):#元数据不符
        raise 附件错误('Stored attachment metadata does not match its reference.','ATTACHMENT_CORRUPT')#损坏
    return {'ref':引用,'data':数据}#已验证
