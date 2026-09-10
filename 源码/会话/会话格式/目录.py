"""编译构建静态物理编解码器与相邻迁移目录。"""
from ...工具.值 import 深冻结#深冻结
from .链 import 创建会话格式链#导入创建链
from .上下文 import 会话格式事件收集器#导入事件收集器
from .错误 import 会话格式错误,会话格式不支持迁移错误#导入错误
from .json import (#从json导入
    检查会话格式版本,#检查版本
    快照会话格式头,#快照头
    会话格式版本,#版本校验
)#json工具

def _取(对象,键):#取字段
    """支持映射或属性风格的编解码器与选项。"""
    if isinstance(对象,dict):#映射
        return 对象[键]#键取
    return getattr(对象,键)#属性取

def 畸形结果(目标版本,错误,已存版本=None):#畸形结果
    """构造畸形头读结果。"""
    结果={'status':'malformed','targetVersion':目标版本,'reason':str(错误)}#基结果
    if 已存版本 is not None:#可选已存版本
        结果['storedVersion']=已存版本#已存版本
    return 深冻结(结果)#冻结

def 恒等产物(产物):#恒等产物
    """原样返回产物。"""
    return 产物#原样

def 完成解码器(解码器,上下文,源继承事件数):#完成解码器
    """完成行校验并校验预声明切口。"""
    继承事件数=解码器.finish(上下文)#完成
    if 源继承事件数 is not None and 继承事件数!=源继承事件数:#切口变了
        raise 会话格式错误('streaming decoder changed its predeclared inherited cut')#错误
    return 继承事件数#返回

def 恢复当代版本(产物,当代版本):#恢复当代版本
    """断言恢复器返回当代版本产物。"""
    if 产物['header']['version']!=当代版本:#版本不符
        raise 会话格式错误(#错误
            f"current Session restorer returned v{产物['header']['version']}; expected v{当代版本}",#消息
        )#Error结束
    return 产物#返回

def 创建会话格式目录(选项):#创建目录
    """编译构建静态物理编解码器与相邻迁移目录。"""
    return 已编译会话格式目录(选项)#编译实例

class 已编译会话格式目录:#已编译目录
    """不可变物理分发与迁移操作。"""
    def __init__(自身,选项):#构造
        """记下链、编解码器映射与当代编码器。"""
        自身.链=创建会话格式链(选项)#创建链
        自身.当前版本=自身.链.当前版本#当代版本
        自身.恢复当前版本=_取(选项,'restoreCurrent')#恢复当代
        自身.恢复转换当代=_取(选项,'restoreTransformedCurrent')#恢复转换当代
        自身.当代编码器=_取(选项,'currentEncoder')#当代编码器
        编解码器映射={}#编解码器映射
        for 编解码器 in _取(选项,'codecs'):#遍历编解码器
            版本=会话格式版本(_取(编解码器,'version'),'Session format codec version')#校验版本
            if 版本 in 编解码器映射:#重复
                raise 会话格式错误(f'Session format codec v{版本} is duplicated')#重复
            if isinstance(编解码器,dict):#映射则冻结副本
                编解码器映射[版本]=深冻结(dict(编解码器))#冻结入库
            else:#对象原样
                编解码器映射[版本]=编解码器#入库
        for 版本 in range(自身.当前版本+1):#检查完整
            if 版本 not in 编解码器映射:#缺失
                raise 会话格式错误(f'Session format codec v{版本} is missing')#缺失
        if len(编解码器映射)!=自身.当前版本+1:#有多余
            无效=None#越界版本
            for 版本 in 编解码器映射.keys():#找越界
                if 版本>自身.当前版本:#越界
                    无效=版本#记下
                    break#找到
            raise 会话格式错误(f'Session format codec v{无效} is newer than current v{自身.当前版本}')#错误
        自身.编解码器表=编解码器映射#记下映射

    def 读头(自身,头值):#读头
        """不读事件行地分类并翻译一头。"""
        已存版本=None#已存版本
        try:#尝试检查版本
            已存版本=检查会话格式版本(头值)#检查
        except BaseException as 错误:#失败
            return 畸形结果(自身.当前版本,错误)#畸形
        if 已存版本>自身.当前版本:#更新
            return 深冻结({#冻结结果
                'status':'unsupported',#不支持
                'storedVersion':已存版本,#已存
                'targetVersion':自身.当前版本,#目标
                'reason':f'stored Session uses newer format v{已存版本}; this build writes v{自身.当前版本}',#原因
            })#freeze结束
        编解码器=自身.编解码器表.get(已存版本)#取编解码器
        if 编解码器 is None:#无编解码器
            return 深冻结({#冻结结果
                'status':'unsupported',#不支持
                'storedVersion':已存版本,#已存
                'targetVersion':自身.当前版本,#目标
                'reason':f'this build has no Session format codec for v{已存版本}',#原因
            })#freeze结束
        try:#尝试解码迁移
            已解码=快照会话格式头(_取(编解码器,'decodeHeader')(头值),'format v'+str(已存版本)+' header')#解码头
            头=自身.链.迁移头(已解码)#迁移头
            return 深冻结({#冻结结果
                'status':'current' if 已存版本==自身.当前版本 else 'migration-required',#状态
                'storedVersion':已存版本,#已存
                'targetVersion':自身.当前版本,#目标
                'header':头,#头
            })#freeze结束
        except BaseException as 错误:#失败
            if isinstance(错误,会话格式不支持迁移错误):#不支持迁移
                return 深冻结({#冻结结果
                    'status':'unsupported',#不支持
                    'storedVersion':已存版本,#已存
                    'targetVersion':自身.当前版本,#目标
                    'reason':str(错误),#原因
                })#freeze结束
            return 畸形结果(自身.当前版本,错误,已存版本)#畸形

    def 产物编解码器(自身,头值):#产物编解码器
        """解析已存版本与对应编解码器。"""
        已存版本=检查会话格式版本(头值)#检查版本
        if 已存版本>自身.当前版本:#更新
            raise 会话格式不支持迁移错误(#不支持
                f'stored Session uses newer format v{已存版本}; this build writes v{自身.当前版本}',#消息
            )#Error结束
        编解码器=自身.编解码器表.get(已存版本)#取编解码器
        if 编解码器 is None:#无
            raise 会话格式不支持迁移错误(f'this build has no Session format codec for v{已存版本}')#不支持
        return 已存版本,编解码器#返回

    def 创建恢复(自身,头值,恢复选项):#创建恢复
        """创建一次单遍物理行恢复为当代逻辑事件。"""
        已存版本,编解码器=自身.产物编解码器(头值)#取编解码器
        解码器=_取(编解码器,'createDecoder')(头值,_取(恢复选项,'recovery'))#创建解码器
        源切口=getattr(解码器,'headerInheritedEventCount',None)#源切口
        if 已存版本==自身.当前版本:#已是当代
            恢复器=自身.恢复当前版本 if _取(恢复选项,'validation')=='current' else 恒等产物#恢复器
            return 当代会话格式恢复(解码器,源切口,恢复器,自身.当前版本)#当代恢复
        收集器=会话格式事件收集器()#收集器
        迁移=自身.链.创建流(#创建迁移流
            解码器.header,#头
            源切口,#源切口
            收集器,#收集器
        )#createStream结束
        恢复器=自身.恢复当前版本 if _取(恢复选项,'validation')=='current' else 自身.恢复转换当代#恢复器
        return 迁移会话格式恢复(#迁移恢复
            解码器,#解码器
            源切口,#源切口
            迁移,#迁移流
            收集器,#收集器
            恢复器,#恢复器
            _取(恢复选项,'validation'),#校验
            已存版本,#源版本
            自身.当前版本,#当代版本
        )#Migrating结束

    def 编码当代头(自身,头,继承事件数):#编码当代头
        """编码一条当代物理头记录。"""
        if 检查会话格式版本(头)!=自身.当前版本:#非当代
            raise 会话格式错误(f'encodeCurrent requires Session format v{自身.当前版本}')#错误
        已编码=_取(自身.当代编码器,'encodeHeader')(头,继承事件数)#编码
        if 检查会话格式版本(已编码)!=自身.当前版本:#头非当代
            raise 会话格式错误('current Session codec returned a non-current header')#错误
        return 已编码#返回

    def 编码当代事件(自身,事件):#编码当代事件
        """编码一条当代物理事件记录。"""
        return _取(自身.当代编码器,'encodeEvent')(事件)#编码

    #上游英文字段名别名（线协议/对照调用面）
    @property#当代版本
    def currentVersion(自身):#当代版本
        """当代版本。"""
        return 自身.当前版本#返回
    def readHeader(自身,头值):#读头
        """不读事件行地分类并翻译一头。"""
        return 自身.读头(头值)#委托
    def createRestore(自身,头值,恢复选项):#创建恢复
        """创建一次单遍物理行恢复为当代逻辑事件。"""
        return 自身.创建恢复(头值,恢复选项)#委托
    def encodeCurrentHeader(自身,头,继承事件数):#编码当代头
        """编码一条当代物理头记录。"""
        return 自身.编码当代头(头,继承事件数)#委托
    def encodeCurrentEvent(自身,事件):#编码当代事件
        """编码一条当代物理事件记录。"""
        return 自身.编码当代事件(事件)#委托

class 当代会话格式恢复:#当代恢复
    """已是当代输入的物理行恢复。"""
    def __init__(自身,解码器,源继承事件数,恢复产物,当代版本):#构造
        """记下解码器与恢复器。"""
        自身.解码器=解码器#解码器
        自身.源继承事件数=源继承事件数#源继承数
        自身.恢复产物=恢复产物#恢复产物
        自身.当代版本=当代版本#当代版本
        自身.header=解码器.header#取头
        自身.收集器=会话格式事件收集器()#收集器

    def decodeRow(自身,行值):#解码行
        """委托解码。"""
        自身.解码器.decodeRow(行值,自身.收集器)#委托解码

    def finish(自身):#完成
        """完成解码并恢复当代产物。"""
        继承事件数=完成解码器(#完成解码器
            自身.解码器,#解码器
            自身.收集器,#收集器
            自身.源继承事件数,#源继承数
        )#finishDecoder结束
        return 恢复当代版本(自身.恢复产物({#恢复当代版本
            'header':自身.header,#头
            'inheritedEventCount':继承事件数,#继承数
            'events':tuple(自身.收集器.values),#事件
        }),自身.当代版本)#restore结束

class 迁移会话格式恢复:#迁移恢复
    """经相邻迁移链恢复为当代逻辑产物。"""
    def __init__(自身,解码器,源继承事件数,迁移,收集器,恢复产物,校验,源版本,当代版本):#构造
        """记下解码器、迁移流与恢复器。"""
        自身.解码器=解码器#解码器
        自身.源继承事件数=源继承事件数#源继承数
        自身.迁移=迁移#迁移流
        自身.收集器=收集器#收集器
        自身.恢复产物=恢复产物#恢复产物
        自身.校验=校验#校验
        自身.源版本=源版本#源版本
        自身.当代版本=当代版本#当代版本
        自身.header=迁移.header#取迁移头

    def decodeRow(自身,行值):#解码行
        """经本上下文解码。"""
        自身.解码器.decodeRow(行值,自身)#经本上下文解码

    def emitEvent(自身,事件):#发出事件
        """委托迁移。"""
        自身.迁移.emitEvent(事件)#委托迁移

    def emitRun(自身,游程):#发出游程
        """委托迁移。"""
        自身.迁移.emitRun(游程)#委托迁移

    def finish(自身):#完成
        """完成解码与迁移并恢复当代产物。"""
        完成解码器(自身.解码器,自身,自身.源继承事件数)#完成解码器
        产物={#产物
            'header':自身.header,#头
            'inheritedEventCount':自身.迁移.finish(),#继承数
            'events':tuple(自身.收集器.values),#事件
        }#artifact结束
        try:#尝试恢复
            已恢复=自身.恢复产物(产物)#恢复
        except BaseException as 错误:#失败
            if 自身.校验=='current' or isinstance(错误,会话格式不支持迁移错误):#已是则原样
                raise 错误#原样
            细节=str(错误)#细节
            raise 会话格式不支持迁移错误(#包装拒绝
                f'Session migration from v{自身.源版本} to v{自身.当代版本} refuses the transformed artifact: {细节}',#消息
                错误,#原因
            )#Error结束
        return 恢复当代版本(已恢复,自身.当代版本)#恢复当代版本
