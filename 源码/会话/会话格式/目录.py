"""编译构建静态物理编解码器与相邻迁移目录。"""
from ...工具.值 import 深冻结#深冻结
from .链 import 创建会话格式链,取字段#导入创建链与取字段
from .错误 import 会话格式错误,会话格式不支持迁移错误#导入错误
from .json import (#从json导入
    检查会话格式版本,#检查版本
    快照会话格式产物,#快照产物
    快照会话格式头,#快照头
    快照会话格式json,#快照JSON
    会话格式版本,#版本校验
)#json工具

def 畸形结果(目标版本,错误,已存版本=None):#畸形结果
    """构造畸形头读结果。"""
    结果={'status':'malformed','targetVersion':目标版本,'reason':str(错误)}#基结果
    if 已存版本 is not None:#可选已存版本
        结果['storedVersion']=已存版本#已存版本
    return 深冻结(结果)#冻结

def 创建会话格式目录(选项):#创建目录
    """编译构建静态物理编解码器与相邻迁移目录。"""
    return 已编译会话格式目录(选项)#编译实例

class 已编译会话格式目录:#已编译目录
    """不可变物理分发与迁移操作。"""
    def __init__(自身,选项):#构造
        """记下链、编解码器映射与当代编码器。"""
        自身.链=创建会话格式链(选项)#创建链
        自身.当代版本=自身.链.当代版本#当代版本
        自身.currentVersion=自身.当代版本#上游别名
        自身.编码当代产物=取字段(选项,'encodeCurrentArtifact')#编码当代
        编解码器映射={}#编解码器映射
        for 编解码器 in 取字段(选项,'codecs'):#遍历编解码器
            版本=会话格式版本(取字段(编解码器,'version'),'Session format codec version')#校验版本
            if 版本 in 编解码器映射:#重复
                raise 会话格式错误(f'Session format codec v{版本} is duplicated')#重复
            if isinstance(编解码器,dict):#映射则冻结副本
                编解码器映射[版本]=深冻结(dict(编解码器))#冻结入库
            else:#对象原样
                编解码器映射[版本]=编解码器#入库
        for 版本 in range(自身.当代版本+1):#检查完整
            if 版本 not in 编解码器映射:#缺失
                raise 会话格式错误(f'Session format codec v{版本} is missing')#缺失
        if len(编解码器映射)!=自身.当代版本+1:#有多余
            无效=None#越界版本
            for 版本 in 编解码器映射.keys():#找越界
                if 版本>自身.当代版本:#越界
                    无效=版本#记下
                    break#找到
            raise 会话格式错误(f'Session format codec v{无效} is newer than current v{自身.当代版本}')#错误
        自身.编解码器们=编解码器映射#记下映射

    def 读头(自身,头值):#读头
        """不读事件行地分类并翻译一头。"""
        已存版本=None#已存版本
        try:#尝试检查版本
            已存版本=检查会话格式版本(头值)#检查
        except BaseException as 错误:#失败
            return 畸形结果(自身.当代版本,错误)#畸形
        if 已存版本>自身.当代版本:#更新
            return 深冻结({#冻结结果
                'status':'unsupported',#不支持
                'storedVersion':已存版本,#已存
                'targetVersion':自身.当代版本,#目标
                'reason':f'stored Session uses newer format v{已存版本}; this build writes v{自身.当代版本}',#原因
            })#freeze结束
        编解码器=自身.编解码器们.get(已存版本)#取编解码器
        if 编解码器 is None:#无编解码器
            return 深冻结({#冻结结果
                'status':'unsupported',#不支持
                'storedVersion':已存版本,#已存
                'targetVersion':自身.当代版本,#目标
                'reason':f'this build has no Session format codec for v{已存版本}',#原因
            })#freeze结束
        try:#尝试解码迁移
            已解码=快照会话格式头(取字段(编解码器,'decodeHeader')(头值),f'format v{已存版本} header')#解码头
            头=自身.链.迁移头(已解码)#迁移头
            return 深冻结({#冻结结果
                'status':'current' if 已存版本==自身.当代版本 else 'migration-required',#状态
                'storedVersion':已存版本,#已存
                'targetVersion':自身.当代版本,#目标
                'header':头,#头
            })#freeze结束
        except BaseException as 错误:#失败
            if isinstance(错误,会话格式不支持迁移错误):#不支持迁移
                return 深冻结({#冻结结果
                    'status':'unsupported',#不支持
                    'storedVersion':已存版本,#已存
                    'targetVersion':自身.当代版本,#目标
                    'reason':str(错误),#原因
                })#freeze结束
            return 畸形结果(自身.当代版本,错误,已存版本)#畸形

    def 产物编解码器(自身,头值):#产物编解码器
        """解析已存版本与对应编解码器。"""
        已存版本=检查会话格式版本(头值)#检查版本
        if 已存版本>自身.当代版本:#更新
            raise 会话格式不支持迁移错误(#不支持
                f'stored Session uses newer format v{已存版本}; this build writes v{自身.当代版本}',#消息
            )#Error结束
        编解码器=自身.编解码器们.get(已存版本)#取编解码器
        if 编解码器 is None:#无
            raise 会话格式不支持迁移错误(f'this build has no Session format codec for v{已存版本}')#不支持
        return 已存版本,编解码器#返回

    def 解码产物(自身,头值,行值们):#解码产物
        """经其冻结版本编解码器分发一份完整物理 JSON 产物。"""
        已存版本,编解码器=自身.产物编解码器(头值)#取编解码器
        return 快照会话格式产物(#快照
            取字段(编解码器,'decodeArtifact')(头值,行值们),#解码
            f'format v{已存版本} decoded artifact',#标签
        )#snapshot结束

    def 解码可恢复产物(自身,头值,行值们):#解码可恢复
        """经其已发布行前缀恢复规则分发一份物理产物。"""
        已存版本,编解码器=自身.产物编解码器(头值)#取编解码器
        return 快照会话格式产物(#快照
            取字段(编解码器,'decodeRecoverableArtifact')(头值,行值们),#解码
            f'format v{已存版本} recoverable artifact',#标签
        )#snapshot结束

    def 迁移(自身,产物):#迁移
        """直接恢复当代输入或在内存中运行全部所需相邻迁移。"""
        return 自身.链.迁移(产物)#委托链

    def 编码当代(自身,产物):#编码当代
        """编码 migrate 返回或活会话产出的当代产物；此处不再校验。"""
        if 检查会话格式版本(取字段(产物,'header'))!=自身.当代版本:#非当代
            raise 会话格式错误(f'encodeCurrent requires Session format v{自身.当代版本}')#错误
        已编码=自身.编码当代产物(产物)#编码
        头=快照会话格式json(取字段(已编码,'header'),'encoded current Session header')#快照头
        行们=[]#行快照
        for 下标,行 in enumerate(取字段(已编码,'rows')):#逐行
            行们.append(快照会话格式json(行,f'encoded current Session row {下标}'))#行快照
        if 检查会话格式版本(头)!=自身.当代版本:#头非当代
            raise 会话格式错误('current Session codec returned a non-current header')#错误
        return 深冻结({'header':头,'rows':tuple(行们)})#冻结返回
