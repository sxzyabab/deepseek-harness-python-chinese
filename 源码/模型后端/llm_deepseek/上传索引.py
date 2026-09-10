"""持久 DeepSeek 附件到文件 id 索引。

对齐上游 `llm-deepseek/src/upload-index.ts`。公开面仅中文名；无英文别名。
"""
import hashlib,json,os,re#哈希、JSON、路径与校验
from ...工具.原子写入 import 带文件锁,原子写文件#文件锁与原子写
from ...工具.工作区路径 import 解析主目录#DSH 主目录
from ...附件.附件 import 图像变体标识#变体 id
from .文件标识 import 深求文件标识,深求文件作用域#文件 id 与作用域

__all__=('深求文件作用域摘要','深求上传索引',)#仅中文公开名

作用域形态=re.compile(r'^[0-9a-f]{64}$')#作用域摘要
附件形态=re.compile(r'^sha256:[0-9a-f]{64}$')#附件 id
变体形态=re.compile(r'^sha256:[0-9a-f]{64}$')#变体 id

class 非法上传索引错误(Exception):#非法上传索引
    """上传索引 JSON 形态非法。"""

def 深求文件作用域摘要(基址,接口密钥):#文件作用域
    """派生非秘密稳定索引命名空间，不持久化或记录 API 密钥。"""
    摘要=hashlib.sha256()#哈希
    摘要.update(基址.rstrip('/').encode('utf-8'))#基址
    摘要.update(b'\0')#分隔
    摘要.update(接口密钥.encode('utf-8'))#密钥
    return 深求文件作用域(摘要.hexdigest())#品牌摘要

def 缺文件(错误):#是否缺文件
    """是否 ENOENT。"""
    return isinstance(错误,OSError) and getattr(错误,'errno',None)==getattr(__import__('errno'),'ENOENT')#缺文件

def 解析记录(值):#解析记录
    """校验并拆离一条上传记录。"""
    if 值 is None or not isinstance(值,dict):#非对象
        raise 非法上传索引错误('llm-deepseek: upload index contains a non-object record')#非法
    作用域=值.get('scope')#作用域
    附件=值.get('attachmentId')#附件
    变体=值.get('variantId')#变体
    文件=值.get('fileId')#文件
    字节=值.get('bytes')#字节
    创建=值.get('createdAt')#创建
    过期=值.get('expiresAt')#过期
    if (not isinstance(作用域,str) or not 作用域形态.match(作用域)
        or not isinstance(附件,str) or not 附件形态.match(附件)
        or not isinstance(变体,str) or not 变体形态.match(变体)
        or not isinstance(文件,str) or len(文件)==0
        or isinstance(字节,bool) or not isinstance(字节,int) or 字节<0
        or isinstance(创建,bool) or not isinstance(创建,int) or 创建<0
        or isinstance(过期,bool) or not isinstance(过期,int) or 过期<0):#非法
        raise 非法上传索引错误('llm-deepseek: upload index contains an invalid record')#非法
    return {
        'scope':深求文件作用域(作用域),#作用域
        'attachmentId':附件,#附件 id（品牌在上游为 AttachmentId）
        'variantId':图像变体标识(变体),#变体
        'fileId':深求文件标识(文件),#文件 id
        'bytes':字节,#字节
        'createdAt':创建,#创建
        'expiresAt':过期,#过期
    }#记录

def 解析索引(文本):#解析索引
    """解析整份索引 JSON。"""
    try:#JSON
        值=json.loads(文本)#解析
    except Exception as 错误:#非法 JSON
        raise 非法上传索引错误('llm-deepseek: upload index is not valid JSON') from 错误#非法
    if 值 is None or not isinstance(值,dict):#非对象
        raise 非法上传索引错误('llm-deepseek: upload index is not an object')#非法
    if 值.get('formatVersion')!=3 or not isinstance(值.get('records'),list):#版本
        raise 非法上传索引错误('llm-deepseek: unsupported upload index format')#不支持
    记录列表=[解析记录(项) for 项 in 值['records']]#记录
    键集=set()#去重
    for 记录 in 记录列表:#逐条
        键=记录['scope']+'\0'+记录['variantId']#键
        if 键 in 键集:#重复
            raise 非法上传索引错误('llm-deepseek: upload index contains duplicate mappings')#重复
        键集.add(键)#记下
    return {'formatVersion':3,'records':记录列表}#索引

def 可复用(记录,现在,刷新边距毫秒):#是否可复用
    """剩余寿命是否足够。"""
    return 记录['expiresAt']-现在>刷新边距毫秒#可复用

class 深求上传索引:#上传索引
    """本 DSH 主目录下每个 DeepSeek 会话共享的原子本地索引。"""
    def __init__(自身,路径=None):#构造
        """显式测试路径；省略则用 DSH_HOME/llm-deepseek/files-v3.json。"""
        if 路径 is None:#默认
            路径=os.path.join(解析主目录(),'llm-deepseek','files-v3.json')#默认路径
        自身.path=路径#路径

    def 加载(自身):#加载
        """读盘；缺文件或非法则空索引。"""
        try:#读
            with open(自身.path,'r',encoding='utf-8') as 文件:#读
                return 解析索引(文件.read())#解析
        except Exception as 错误:#失败
            if 缺文件(错误) or isinstance(错误,非法上传索引错误):#可恢复
                return {'formatVersion':3,'records':[]}#空
            raise#其余上抛

    def 保存(自身,索引):#保存
        """原子写盘。"""
        原子写文件(自身.path,json.dumps(索引,ensure_ascii=False,indent=2)+'\n',{'mode':0o600,'dirMode':0o700})#原子写

    def 获取(自身,作用域,变体标识,现在,刷新边距毫秒):#获取
        """读一条可复用映射。"""
        记录=None#候选
        for 候选 in 自身.加载()['records']:#逐条
            if 候选['scope']==作用域 and 候选['variantId']==变体标识:#命中
                记录=候选#记下
                break#找到
        if 记录 is not None and 可复用(记录,现在,刷新边距毫秒):#可复用
            return 记录#返回
        return None#无

    def 提交(自身,候选,现在,刷新边距毫秒):#提交
        """发布一次已完成上传，除非另一进程已发布可复用映射。"""
        os.makedirs(os.path.dirname(自身.path),exist_ok=True,mode=0o700)#父目录
        def 持锁():#锁内
            """读改写。"""
            索引=自身.加载()#加载
            for 记录 in 索引['records']:#已有
                if (记录['scope']==候选['scope'] and 记录['variantId']==候选['variantId']
                    and 可复用(记录,现在,刷新边距毫秒)):#可复用获胜
                    return {'record':记录,'accepted':False}#拒绝候选
            记录列表=[]#过滤
            for 记录 in 索引['records']:#逐条
                if not 可复用(记录,现在,刷新边距毫秒):#过期丢掉
                    continue#跳过
                if 记录['scope']==候选['scope'] and 记录['variantId']==候选['variantId']:#同键
                    continue#替换
                记录列表.append(记录)#保留
            记录列表.append(候选)#压入
            自身.保存({'formatVersion':3,'records':记录列表})#写盘
            return {'record':候选,'accepted':True}#接受
        return 带文件锁(自身.path,持锁)#持锁

    def 移除(自身,作用域,变体标识,文件标识):#移除
        """移除一条精确映射。"""
        os.makedirs(os.path.dirname(自身.path),exist_ok=True,mode=0o700)#父目录
        def 持锁():#锁内
            """过滤精确映射。"""
            索引=自身.加载()#加载
            记录列表=[记录 for 记录 in 索引['records'] if not (
                记录['scope']==作用域 and 记录['variantId']==变体标识 and 记录['fileId']==文件标识
            )]#过滤
            if len(记录列表)!=len(索引['records']):#有变
                自身.保存({'formatVersion':3,'records':记录列表})#写盘
        带文件锁(自身.path,持锁)#持锁

    def 清空(自身,作用域):#清空
        """移除一个远程命名空间的每条本地映射。"""
        os.makedirs(os.path.dirname(自身.path),exist_ok=True,mode=0o700)#父目录
        def 持锁():#锁内
            """按作用域过滤。"""
            索引=自身.加载()#加载
            记录列表=[记录 for 记录 in 索引['records'] if 记录['scope']!=作用域]#过滤
            if len(记录列表)!=len(索引['records']):#有变
                自身.保存({'formatVersion':3,'records':记录列表})#写盘
        带文件锁(自身.path,持锁)#持锁
