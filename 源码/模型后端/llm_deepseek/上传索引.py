'耐久的 DeepSeek 附件到文件标识索引'
import os,re
from hashlib import sha256 as 哈希256#SHA-256 摘要，用于派生作用域
from json import loads as 解码,dumps as 编码,JSONDecodeError as JSON解析错误#索引文件的 JSON 编解码与解析失败异常
from ...工具.原子写入 import 带文件锁,原子写文件#跨进程写锁与原子写盘
from ...工具.主目录路径 import 解析主目录#DSH 主目录位置
from ...附件.附件 import 图像变体标识#变体标识的品牌构造
from .文件标识 import 深求文件标识,深求文件作用域#提供方文件标识与作用域的品牌构造
from .异常 import 非法上传索引错误#索引内容损坏

__all__=['深求文件作用域摘要','深求上传索引']#仅中文公开名

格式版本=3#索引文件格式版本，读写两侧都必须是它
作用域正则=re.compile(r'^[0-9a-f]{64}\Z')#作用域是 64 位小写十六进制；行尾用 \Z 对齐 JS 的 $，不放过结尾换行
附件标识正则=re.compile(r'^sha256:[0-9a-f]{64}\Z')#附件标识与变体标识都是 sha256: 加 64 位小写十六进制

def 深求文件作用域摘要(基址,密钥):
    '由端点与密钥派生不含机密的稳定命名空间摘要，认证头只作哈希输入，不落盘不写日志'
    摘要=哈希256()#新建 SHA-256 状态
    摘要.update(基址.rstrip('/').encode('utf-8'))#端点去掉全部结尾斜杠，同一端点不同写法得到同一作用域
    摘要.update(b'\0')#NUL 分隔端点与密钥，避免两段拼接后产生歧义
    摘要.update(密钥.encode('utf-8'))#序列化后的认证头
    return 深求文件作用域(摘要.hexdigest())#打上作用域品牌后返回

def 解析记录(值):
    '校验并构造一条耐久映射，任一字段不合法就抛非法上传索引错误'
    if not isinstance(值,dict):#记录必须是 JSON 对象
        raise 非法上传索引错误('llm-deepseek: 上传索引含有非对象记录')
    for 字段,格式 in (('scope',作用域正则),('attachmentId',附件标识正则),('variantId',附件标识正则)):#三个哈希字段逐个校验
        if 字段 not in 值 or not isinstance(值[字段],str) or 格式.match(值[字段]) is None:#缺字段、非字符串、格式不符都算非法
            raise 非法上传索引错误('llm-deepseek: 上传索引含有非法记录')
    if 'fileId' not in 值 or not isinstance(值['fileId'],str) or len(值['fileId'])==0:#文件标识必须是非空字符串
        raise 非法上传索引错误('llm-deepseek: 上传索引含有非法记录')
    for 字段 in ('bytes','createdAt','expiresAt'):#三个数值字段是外来 JSON，必须是非负安全整数
        if 字段 not in 值 or isinstance(值[字段],bool) or not isinstance(值[字段],int) or not 0<=值[字段]<=9007199254740991:#bool 是 int 子类要先排除；上限是 JS 安全整数上限，上游以它为界
            raise 非法上传索引错误('llm-deepseek: 上传索引含有非法记录')
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
    '解析整份索引文本，校验格式版本、逐条记录以及 scope 加 variantId 的唯一性'
    try:
        值=解码(文本)#整份文本必须是合法 JSON
    except JSON解析错误 as 错误:
        raise 非法上传索引错误('llm-deepseek: 上传索引不是合法 JSON') from 错误
    if not isinstance(值,dict):#顶层必须是 JSON 对象
        raise 非法上传索引错误('llm-deepseek: 上传索引不是对象')
    if 'formatVersion' not in 值 or 值['formatVersion']!=格式版本 or 'records' not in 值 or not isinstance(值['records'],list):#版本不符或缺记录列表
        raise 非法上传索引错误('llm-deepseek: 不支持的上传索引格式')
    记录表=[解析记录(项) for 项 in 值['records']]#逐条校验并构造
    已见键=set()#已出现的作用域与变体组合
    for 记录 in 记录表:#同一作用域同一变体只允许一条映射
        键=记录['scope']+'\0'+记录['variantId']#作用域与变体用 NUL 连接成唯一键
        if 键 in 已见键:
            raise 非法上传索引错误('llm-deepseek: 上传索引含有重复映射')
        已见键.add(键)
    return {'formatVersion':格式版本,'records':记录表}

def 可复用(记录,现在,刷新边距毫秒):
    '记录剩余寿命是否仍大于刷新边距，单位都是毫秒'
    return 记录['expiresAt']-现在>刷新边距毫秒

class 深求上传索引:
    '本 DSH 主目录内各 DeepSeek 会话共享的原子本地索引'
    def __init__(自身,路径=None):
        '省略路径则用主目录下 llm-deepseek/files-v3.json，显式路径供测试使用'
        if 路径 is None:#调用方没有指定路径
            路径=os.path.join(解析主目录(),'llm-deepseek','files-v3.json')#默认索引位置
        自身.路径=路径#仅属主可读写的 JSON 索引文件路径

    def 加载(自身):
        '读盘并解析；文件不存在或内容损坏时按上游行为当作空索引，其余读盘错误原样抛出'
        try:
            with open(自身.路径,'r',encoding='utf-8',errors='replace') as 文件:#非法字节替换成 U+FFFD，对齐 Node 的 utf8 解码，不因编码报错
                文本=文件.read()
            return 解析索引(文本)
        except (FileNotFoundError,非法上传索引错误):#只吞这两类，权限等其它错误仍然上抛
            return {'formatVersion':格式版本,'records':[]}

    def 保存(自身,索引):
        '原子写回整份索引，文件仅属主可读写，新建目录仅属主可进入'
        原子写文件(自身.路径,编码(索引,ensure_ascii=False,indent=2)+'\n',{'mode':0o600,'dirMode':0o700})

    def 取(自身,作用域,变体标识,现在,刷新边距毫秒):
        '读取一条仍可复用的映射，剩余寿命不足或不存在时返回 None'
        for 记录 in 自身.加载()['records']:#按文件顺序找
            if 记录['scope']==作用域 and 记录['variantId']==变体标识:#只看第一条命中的记录
                return 记录 if 可复用(记录,现在,刷新边距毫秒) else None
        return None

    def 提交(自身,候选,现在,刷新边距毫秒):
        '发布已完成的上传；别的进程已发布可复用映射时不写入。返回 {record,accepted}'
        os.makedirs(os.path.dirname(自身.路径) or '.',mode=0o700,exist_ok=True)#锁文件建在索引同目录，父目录必须先存在
        def 在锁内():
            '持跨进程写锁，读改写索引'
            索引=自身.加载()#锁内重新读盘，才能看到其它进程刚发布的内容
            for 记录 in 索引['records']:
                if 记录['scope']==候选['scope'] and 记录['variantId']==候选['variantId'] and 可复用(记录,现在,刷新边距毫秒):#别的进程已发布同键且可复用的映射
                    return {'record':记录,'accepted':False}
            记录表=[记录 for 记录 in 索引['records'] if 可复用(记录,现在,刷新边距毫秒) and not (记录['scope']==候选['scope'] and 记录['variantId']==候选['variantId'])]#顺带丢掉已过期记录与同键旧记录
            记录表.append(候选)#候选放在末尾
            自身.保存({'formatVersion':格式版本,'records':记录表})
            return {'record':候选,'accepted':True}
        return 带文件锁(自身.路径,在锁内)

    def 移除(自身,作用域,变体标识,文件号):
        '精确移除一条映射，不删并发装上的后继（文件号不同就不删）'
        os.makedirs(os.path.dirname(自身.路径) or '.',mode=0o700,exist_ok=True)#锁文件建在索引同目录，父目录必须先存在
        def 在锁内():
            '持跨进程写锁，过滤掉精确命中的一条'
            索引=自身.加载()#锁内重新读盘
            记录表=[记录 for 记录 in 索引['records'] if not (记录['scope']==作用域 and 记录['variantId']==变体标识 and 记录['fileId']==文件号)]
            if len(记录表)!=len(索引['records']):#确有记录被移除才写盘，避免无谓改写
                自身.保存({'formatVersion':格式版本,'records':记录表})
        带文件锁(自身.路径,在锁内)

    def 清空(自身,作用域):
        '移除一个远程命名空间的全部本地映射'
        os.makedirs(os.path.dirname(自身.路径) or '.',mode=0o700,exist_ok=True)#锁文件建在索引同目录，父目录必须先存在
        def 在锁内():
            '持跨进程写锁，按作用域过滤'
            索引=自身.加载()#锁内重新读盘
            记录表=[记录 for 记录 in 索引['records'] if 记录['scope']!=作用域]
            if len(记录表)!=len(索引['records']):#确有记录被移除才写盘
                自身.保存({'formatVersion':格式版本,'records':记录表})
        带文件锁(自身.路径,在锁内)
