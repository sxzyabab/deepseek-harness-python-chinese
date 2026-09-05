"""耐久会话 JSON 边界与相邻迁移目录的类型约定。"""
from typing import Literal,NotRequired,Protocol,TypedDict#字面量、可选字段、协议与结构类型

会话格式json原始量=None|bool|int|float|str#耐久会话 JSON 边界接纳的标量值

class 会话格式头(TypedDict):#受支持历史与当代格式共享的逻辑会话元数据
    version:int#版本
    id:str#id
    createdAt:int#创建时间
    cwd:NotRequired[str]#可选工作目录
    parentSession:NotRequired[str]#可选父会话
    isSeeded:bool#是否种子
    origin:NotRequired[Literal['subagent']]#可选出处
    delegationDepth:int#委派深度
    agentPreset:NotRequired[str]#可选智能体预设

class 会话格式事件(TypedDict):#一条已解码逻辑会话事件
    type:str#类型
    seq:int#序号
    time:int#时间
    data:object#数据（会话格式json值）

会话格式产物字段=('header','inheritedEventCount','events')#一份分离的完整逻辑会话产物
会话格式迁移字段=('name','fromVersion','toVersion','migrateHeader','migrate','validateTarget','validateTargetHeader')#一个独立维护的相邻整产物迁移
会话格式链选项字段=('currentVersion','migrations','restoreCurrent','restoreCurrentHeader')#编译唯一完整迁移链的输入
会话格式链字段=('currentVersion','plan','migrate','migrateHeader')#纯相邻规划器与整产物迁移运行器（键名对齐上游）
已编码会话格式产物字段=('header','rows')#一个格式特定编解码器发出的物理 JSON 记录
会话格式编码选项字段=('packChunks',)#仅影响物理行布局、从不影响逻辑内容的选项
会话格式编解码器字段=('version','decodeHeader','decodeArtifact','decodeRecoverableArtifact')#与一个已发布会话格式冻结的纯物理 JSON 编解码器
会话格式目录选项字段=('currentVersion','migrations','restoreCurrent','restoreCurrentHeader','codecs','encodeCurrentArtifact')#构建静态物理编解码器与迁移目录的输入
会话格式目录字段=('currentVersion','readHeader','decodeArtifact','decodeRecoverableArtifact','migrate','encodeCurrent')#构建静态物理分发与相邻迁移目录（键名对齐上游）

class 会话格式迁移(Protocol):#一个独立维护的相邻整产物迁移
    """命名的精确相邻转换；成员名对齐上游英文字段。"""
    @property#名称
    def name(自身):#迁移名
        """迁移名。"""
        ...#协议桩
    @property#源版本
    def fromVersion(自身):#源版本
        """源版本。"""
        ...#协议桩
    @property#目标版本
    def toVersion(自身):#目标版本
        """目标版本。"""
        ...#协议桩
    def migrateHeader(自身,头):#不读事件体地转换一头
        """不读事件体地转换一头。"""
        ...#协议桩
    def migrate(自身,产物):#把一份分离完整产物转为恰好 toVersion
        """把一份分离完整产物转为恰好目标版本。"""
        ...#协议桩
    def validateTarget(自身,产物):#拒绝相邻目标写者无法发出的任何产物
        """拒绝相邻目标写者无法发出的任何产物。"""
        ...#协议桩
    def validateTargetHeader(自身,头):#拒绝相邻目标写者无法发出的任何头
        """拒绝相邻目标写者无法发出的任何头。"""
        ...#协议桩

class 会话格式编解码器(Protocol):#与一个已发布会话格式冻结的纯物理 JSON 编解码器
    """格式特定物理 JSON 编解码器；成员名对齐上游。"""
    @property#版本
    def version(自身):#版本
        """版本。"""
        ...#协议桩
    def decodeHeader(自身,值):#把一个物理头解码为与体无关的逻辑元数据
        """把一个物理头解码为与体无关的逻辑元数据。"""
        ...#协议桩
    def decodeArtifact(自身,头值,行值们):#把完整物理头与行序列解码为逻辑事件
        """把完整物理头与行序列解码为逻辑事件。"""
        ...#协议桩
    def decodeRecoverableArtifact(自身,头值,行值们):#解码崩溃尾修复使用的行原子可恢复前缀
        """解码崩溃尾修复使用的行原子可恢复前缀。"""
        ...#协议桩

class 会话格式链(Protocol):#纯相邻规划器与整产物迁移运行器
    """纯相邻规划器与整产物迁移运行器。"""
    @property#当代版本
    def 当代版本(自身):#当代版本
        """当代版本。"""
        ...#协议桩
    def 计划(自身,源版本):#返回从一个受支持已存版本起的完整有序计划
        """返回从一个受支持已存版本起的完整有序计划。"""
        ...#协议桩
    def 迁移(自身,产物):#直接恢复当代输入或在内存中完整迁移旧输入
        """直接恢复当代输入或在内存中完整迁移旧输入。"""
        ...#协议桩
    def 迁移头(自身,头):#仅把受支持头转为当代逻辑表示
        """仅把受支持头转为当代逻辑表示。"""
        ...#协议桩

class 会话格式目录(Protocol):#构建静态物理分发与相邻迁移目录
    """构建静态物理分发与相邻迁移目录。"""
    @property#当代版本
    def 当代版本(自身):#当代版本
        """当代版本。"""
        ...#协议桩
    def 读头(自身,头值):#不读事件行地分类并翻译一头
        """不读事件行地分类并翻译一头。"""
        ...#协议桩
    def 解码产物(自身,头值,行值们):#经其冻结版本编解码器分发一份完整物理 JSON 产物
        """经其冻结版本编解码器分发一份完整物理 JSON 产物。"""
        ...#协议桩
    def 解码可恢复产物(自身,头值,行值们):#经其已发布行前缀恢复规则分发一份物理产物
        """经其已发布行前缀恢复规则分发一份物理产物。"""
        ...#协议桩
    def 迁移(自身,产物):#直接恢复当代输入或在内存中运行全部所需相邻迁移
        """直接恢复当代输入或在内存中运行全部所需相邻迁移。"""
        ...#协议桩
    def 编码当代(自身,产物):#编码 migrate 返回或活会话产出的当代产物；此处不再校验
        """编码当代产物；此处不再校验。"""
        ...#协议桩
