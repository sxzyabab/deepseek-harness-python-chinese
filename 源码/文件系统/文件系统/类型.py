"""文件系统服务定义（`ctx.fs`）的词汇表：不透明的目标/版本身份、`stat` 返回的元数据、写意图与结果形态、字面量编辑的请求/结果，以及带类型的错误分类。"""
from llm import 装备错误#从LLM包导入HarnessError基类

def 目标键(原始键):#把字符串打成目标键品牌，仅供后端使用
    """把字符串打成目标键品牌。过期守卫与目标查找用的不透明键。本地后端使用类似 realpath 的字符串；远程后端可能使用 workspace URI 或文件 id。消费方不得解析它，也不得假定它是本地绝对路径。仅供后端使用——消费方从不自己造键，只从解析接收。不做校验。"""
    return 原始键#原样返回并打成目标键，不做校验

def 版本令牌(原始版本):#把字符串打成版本令牌品牌，仅供后端使用
    """把字符串打成版本令牌品牌。不透明的文件版本令牌——写/编辑用来防过期的新鲜度令牌。本地后端从高分辨率 stat 身份与新鲜度字段推导；远程后端可能使用修订 id。策略层记录它做过期检查；消费方可展示相关元数据，但不得解释此令牌。仅供后端使用——消费方从不自己造版本，只从状态或写编辑结果接收。不做校验。"""
    return 原始版本#原样返回并打成版本令牌，不做校验

#对目标的一次权威观察。存在观察携带受守卫替换所用的版本；缺失观察只授权受守卫的创建，绝不授权编辑。
#present：{'kind':'present','version':版本令牌}；absent：{'kind':'absent'}。
文件系统观察种类=('present','absent')#观察种类判别：存在或确认缺失
文件系统观察存在字段=('kind','version')#存在观察：kind 固定为 present，version 为当前版本令牌
文件系统观察缺失字段=('kind',)#缺失观察：kind 固定为 absent，无版本

文件系统目标字段=('targetKey','displayPath')#已解析目标：不透明键 + 面向模型/UI 的展示路径
"""后端把路径解析成的稳定身份。解析产出此对象；其余操作都接收它。targetKey 用于过期守卫与目标查找；displayPath 按后端可能是本地绝对路径、workspace 相对路径或远程 URI。"""

文件系统信息字段=('version','type','size')#stat 元数据：版本、类型、可选字节大小
"""目标元数据——状态的返回值。type 为 file/directory/other。让策略层在读取前拒绝目录/特殊文件，并凭 size 在读文本与流文本之间选择。stat 返回 None 表示目标不存在。"""

文件系统信息类型=('file','directory','other')#目标级条目类型（不含 symlink）

文件系统路径信息字段=('version','type','size')#lstat 路径级元数据：版本、类型、可选字节大小
"""不跟随最后一段符号链接时的路径元数据。与信息不同，此路径级探测可报告 symlink，以便带信任边界规则的消费方在解析目标前拒绝仓库自有链接。"""

文件系统路径信息类型=('file','directory','symlink','other')#路径级条目类型（含 symlink）

文件系统目录项字段=('name','type','target','version','size')#listDir 直接子项：基名、类型、已解析子目标、可选版本与大小
"""列举返回的一个直接子项。列举只返回元数据与已解析目标，不得读取文件内容。"""

文件系统目录项类型=('file','directory','other')#目录子项类型

#受守卫的写意图。createIfAbsent 在目标已存在时以 FS_NOT_OBSERVED 拒绝；replaceIfVersion 在缺失或不匹配时以 FS_STALE_VERSION 拒绝。
#从写文本省略意图表示无条件创建或覆盖，不是联合的第三臂。
#createIfAbsent：{'kind':'createIfAbsent'}；replaceIfVersion：{'kind':'replaceIfVersion','version':版本令牌}。
文件系统写意图种类=('createIfAbsent','replaceIfVersion')#写意图判别臂
文件系统写意图创建字段=('kind',)#仅创建缺失目标
文件系统写意图替换字段=('kind','version')#按版本替换

文件系统写结果字段=('operation','version','before','after')#整文件写入结果：操作种类、新版本、前后文本
"""整文件写入的结果。operation 为 create 或 update。before 在创建或后端拒绝提供上下文基准时为 None；after 为写入后 LF 规范化文本。"""

文件系统写操作=('create','update')#写入操作种类：新建或替换

文件系统编辑请求字段=('oldString','newString','replaceAll')#字面量查找/替换请求
"""字面量替换编辑请求。oldString 必须非空且精确匹配（经行尾规范化之后）；newString 可为空表示删除；replaceAll 为真则替换每一处匹配。"""

文件系统编辑结果字段=('version','before','after')#字面量编辑结果：新版本与前后完整文本
"""字面量编辑的结果。before/after 是原始存储文本（后端做 LF 规范化），绝不是 diff——消费方从前后文本计算结果时上下文 diff。"""

文件系统错误码=(#文件系统失败的稳定、可机器路由的错误码
    'FS_NOT_FOUND',#目标未找到
    'FS_NOT_DIRECTORY',#目标不是目录
    'FS_NOT_TEXT',#目标不是文本
    'FS_NOT_REGULAR_FILE',#目标不是普通文件
    'FS_TOO_LARGE',#目标过大
    'FS_PERMISSION_DENIED',#权限被拒绝
    'FS_SANDBOX_DENIED',#沙箱拒绝
    'FS_IO_ERROR',#输入输出错误
    'FS_STALE_VERSION',#版本过期
    'FS_NOT_OBSERVED',#未经观察
    'FS_AMBIGUOUS_EDIT',#编辑匹配不唯一
    'FS_EDIT_NOT_FOUND',#编辑未找到匹配
    'FS_ABORTED',#操作已中止
)#文件系统错误码结束

class 文件系统错误(装备错误):#文件系统带类型错误
    """带类型的文件系统错误。扩展装备错误，因此携带稳定错误码并链接 cause。dsh-fs 拥有此词汇，使后端与策略层抛出同一套错误码，而不是各自发明消息字符串。工具注册表在 isError 结果上暴露 {name, code}，以便重试/权限/UI 层无需解析消息即可分支。"""
    def __init__(自身,消息,码,选项=None):#构造文件系统错误
        """构造文件系统错误。记下稳定 code，并把 cause 链到本错误。"""
        装备错误.__init__(自身,消息,码,选项)#交给装备错误保存消息、错误码与cause
        自身.code=码#再写下本类的错误码字段
        自身.name='FsError'#对齐源码子类名
