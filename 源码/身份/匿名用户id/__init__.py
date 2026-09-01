"""每个 harness 主目录共享的匿名用户 id，供遥测与反馈使用。

id 是随机 UUID，以裸行写入主目录下 `.anonymous-user-id` 文件；从不从主机名、网络地址、git 远程或其它识别源推导。作用域是 harness 主目录而非机器：共享同一 `$DSH_HOME` 的进程报告同一 id，删除文件后下次启动会铸造新身份。

读写同步以便启动时与命令消费方使用同一 API。结果按已解析文件路径记忆：单进程只触盘一次，运行中删除文件仍保留本进程 id 直到下次启动。
"""
import os,re#路径、读写与 UUID 形态
from uuid import uuid4 as 随机uuid#UUID 生成
from ...工具.品牌 import 带品牌#名义类型
from ...工具.工作区路径 import 解析主目录#解析 harness 主目录
__all__=['匿名用户id类型','匿名用户id文件名','获取或创建匿名用户id']#仅中文公开名

匿名用户id类型=带品牌#匿名用户 id 品牌别名
匿名用户id文件名='.anonymous-user-id'#主目录内 id 文件
UUID形态=re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',re.I)#UUID v4 形态

记忆={}#按文件路径的过程记忆

def 读取持久id(文件):#读有效持久 id
    """从文件读取有效持久 id；缺席或损坏为 None。"""
    try:#读文件
        文本=open(文件,'r',encoding='utf-8').read()#读全文
    except OSError:#缺席或不可读
        return None#由调用方铸造
    值=文本.strip()#去空白
    if UUID形态.fullmatch(值) is None:#非法
        return None#损坏
    return 带品牌(值)#品牌化

def 获取或创建匿名用户id(选项=None):#获取或创建 id
    """返回 harness 主目录的匿名用户 id，首次使用时创建并尽力持久化。"""
    if 选项 is None:#默认选项
        选项={}#空映射
    环境=选项.get('env',os.environ)#环境映射
    主目录=解析主目录(None,环境)#解析主目录
    文件=os.path.join(主目录,匿名用户id文件名)#id 文件路径
    缓存=记忆.get(文件)#查记忆
    if 缓存 is not None:#已记忆
        return 缓存#直接返回
    标识=读取持久id(文件)#读持久
    if 标识 is None:#需要铸造
        生成=选项.get('randomUUID',随机uuid)#UUID 生成器
        新建=带品牌(str(生成()))#新 id
        try:#独占创建
            os.makedirs(os.path.dirname(文件),exist_ok=True)#确保父目录
            描述符=os.open(文件,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)#wx 创建
            try:#写入
                os.write(描述符,(str(新建)+'\n').encode('utf-8'))#写一行
            finally:#关闭
                os.close(描述符)#关掉
            标识=新建#采用新建
        except OSError:#竞态或只读
            标识=读取持久id(文件)#重读赢家
            if 标识 is None:#仍无有效 id
                try:#尽力覆盖写
                    open(文件,'w',encoding='utf-8').write(str(新建)+'\n')#覆盖写
                except OSError:#只读主目录
                    pass#尽力失败可接受
                标识=新建#本进程仍用新建
    记忆[文件]=标识#写入记忆
    return 标识#返回 id

getOrCreateAnonymousUserId=获取或创建匿名用户id#Cordis 英文名
ANONYMOUS_USER_ID_FILE_NAME=匿名用户id文件名#Cordis 常量名
