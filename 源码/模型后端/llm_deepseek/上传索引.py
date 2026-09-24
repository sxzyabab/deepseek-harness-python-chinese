"""耐久的 DeepSeek 附件到文件标识索引。"""
import os,json,re,errno
from hashlib import sha256 as 哈希256
from ...工具.原子写入 import 带文件锁,原子写文件
from ...工具.主目录路径 import 解析主目录
from ...附件.附件 import 图像变体标识
from .文件标识 import 深求文件标识,深求文件作用域

__all__=['深求文件作用域摘要','深求上传索引']

作用域形=re.compile(r'^[0-9a-f]{64}$')
附件形=re.compile(r'^sha256:[0-9a-f]{64}$')

class 非法上传索引错误(Exception):
    """本地索引损坏。"""

def 深求文件作用域摘要(基址,密钥):
    """由端点与密钥派生非机密命名空间摘要。"""
    摘要=哈希256()
    摘要.update(基址.rstrip('/').encode('utf-8'))
    摘要.update(b'\0')
    摘要.update(密钥.encode('utf-8'))
    return 深求文件作用域(摘要.hexdigest())

def 缺席(错误):
    """路径不存在。"""
    return isinstance(错误,OSError) and 错误.errno==errno.ENOENT

def 解析记录(值):
    """校验一条耐久映射。"""
    if not isinstance(值,dict):
        raise 非法上传索引错误('llm-deepseek: upload index contains a non-object record')
    if (not isinstance(值.get('scope'),str) or not 作用域形.match(值['scope'])
        or not isinstance(值.get('attachmentId'),str) or not 附件形.match(值['attachmentId'])
        or not isinstance(值.get('variantId'),str) or not 附件形.match(值['variantId'])
        or not isinstance(值.get('fileId'),str) or 值['fileId']==''
        or not isinstance(值.get('bytes'),int) or isinstance(值.get('bytes'),bool) or 值['bytes']<0
        or not isinstance(值.get('createdAt'),int) or isinstance(值.get('createdAt'),bool) or 值['createdAt']<0
        or not isinstance(值.get('expiresAt'),int) or isinstance(值.get('expiresAt'),bool) or 值['expiresAt']<0):
        raise 非法上传索引错误('llm-deepseek: upload index contains an invalid record')
    return {
        'scope':深求文件作用域(值['scope']),
        'attachmentId':值['attachmentId'],
        'variantId':图像变体标识(值['variantId']),
        'fileId':深求文件标识(值['fileId']),
        'bytes':值['bytes'],
        'createdAt':值['createdAt'],
        'expiresAt':值['expiresAt'],
    }

def 解析索引(文本):
    """解析整份索引。"""
    try:
        值=json.loads(文本)
    except Exception as 错误:
        raise 非法上传索引错误('llm-deepseek: upload index is not valid JSON') from 错误
    if not isinstance(值,dict) or 值.get('formatVersion')!=3 or not isinstance(值.get('records'),list):
        raise 非法上传索引错误('llm-deepseek: unsupported upload index format')
    记录表=[解析记录(项) for 项 in 值['records']]
    键表=set()
    for 记录 in 记录表:
        键=记录['scope']+'\0'+记录['variantId']
        if 键 in 键表:
            raise 非法上传索引错误('llm-deepseek: upload index contains duplicate mappings')
        键表.add(键)
    return {'formatVersion':3,'records':记录表}

def 可复用(记录,现在,刷新边距毫秒):
    """剩余寿命是否够复用。"""
    return 记录['expiresAt']-现在>刷新边距毫秒

class 深求上传索引:
    """本 DSH 主目录内各 DeepSeek 会话共享的原子本地索引。"""
    def __init__(自身,路径=None):
        """省略路径则用主目录下 llm-deepseek/files-v3.json。"""
        if 路径 is None:
            路径=os.path.join(解析主目录(),'llm-deepseek','files-v3.json')
        自身.路径=路径

    def 加载(自身):
        """读盘；缺席或损坏当空表。"""
        try:
            文件=open(自身.路径,'r',encoding='utf-8')
            try:
                文本=文件.read()
            finally:
                文件.close()
            return 解析索引(文本)
        except Exception as 错误:
            if 缺席(错误) or isinstance(错误,非法上传索引错误):
                return {'formatVersion':3,'records':[]}
            raise 错误

    def 保存(自身,索引):
        """原子写回。"""
        原子写文件(自身.路径,json.dumps(索引,ensure_ascii=False,indent=2)+'\n',{'mode':0o600,'dirMode':0o700})

    def 取(自身,作用域,变体标识,现在,刷新边距毫秒):
        """读一条可复用映射。"""
        记录=None
        for 候选 in 自身.加载()['records']:
            if 候选['scope']==作用域 and 候选['variantId']==变体标识:
                记录=候选
                break
        if 记录 is not None and 可复用(记录,现在,刷新边距毫秒):
            return 记录
        return None

    def 提交(自身,候选,现在,刷新边距毫秒):
        """发布完成上传，除非别的进程已发布可复用映射。"""
        os.makedirs(os.path.dirname(自身.路径) or '.',mode=0o700,exist_ok=True)
        def 在锁内():
            """持锁读写。"""
            索引=自身.加载()
            已有=None
            for 记录 in 索引['records']:
                if 记录['scope']==候选['scope'] and 记录['variantId']==候选['variantId'] and 可复用(记录,现在,刷新边距毫秒):
                    已有=记录
                    break
            if 已有 is not None:
                return {'record':已有,'accepted':False}
            记录表=[记录 for 记录 in 索引['records'] if 可复用(记录,现在,刷新边距毫秒) and not (记录['scope']==候选['scope'] and 记录['variantId']==候选['variantId'])]
            记录表.append(候选)
            自身.保存({'formatVersion':3,'records':记录表})
            return {'record':候选,'accepted':True}
        return 带文件锁(自身.路径,在锁内)

    def 移除(自身,作用域,变体标识,文件号):
        """去掉精确映射，不删并发装上的后继。"""
        os.makedirs(os.path.dirname(自身.路径) or '.',mode=0o700,exist_ok=True)
        def 在锁内():
            """持锁删精确项。"""
            索引=自身.加载()
            记录表=[记录 for 记录 in 索引['records'] if not (记录['scope']==作用域 and 记录['variantId']==变体标识 and 记录['fileId']==文件号)]
            if len(记录表)!=len(索引['records']):
                自身.保存({'formatVersion':3,'records':记录表})
        带文件锁(自身.路径,在锁内)

    def 清空(自身,作用域):
        """去掉一个远程命名空间的全部本地映射。"""
        os.makedirs(os.path.dirname(自身.路径) or '.',mode=0o700,exist_ok=True)
        def 在锁内():
            """持锁按作用域过滤。"""
            索引=自身.加载()
            记录表=[记录 for 记录 in 索引['records'] if 记录['scope']!=作用域]
            if len(记录表)!=len(索引['records']):
                自身.保存({'formatVersion':3,'records':记录表})
        带文件锁(自身.路径,在锁内)
