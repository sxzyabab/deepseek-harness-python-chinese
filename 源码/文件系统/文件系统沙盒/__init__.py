"""`沙箱文件系统`（`SandboxedFileSystem`）：`@deepseek-ai/dsh-fs` 服务定义的沙箱强制实现。它扩展 `本地文件系统`（`LocalFileSystem`），因此全部文本存储机制——resolve、stat、读/流、列举、原子写以及读-匹配-写编辑临界区——都是本地实现的原文；本包只在两次变更上加每调用的策略围栏。读取原样穿过：每种模式都允许读。

围栏是受信任代码里对模型控制路径的策略检查，不是内核边界——操作为 seam 自有（open、rename），只有目标路径不受信任，因此先规范化再做包含判定就是此面上的完整答案。不受信任代码的内核级隔离仍是 ctx.shell 的工作（bash-sandbox）。这与 code-runtime 立场一致：包含，不是安全边界。残余 TOCTOU（包含复查与系统调用之间祖先符号链接被替换）通过委托前立即再规范化收窄，并被此威胁模型接受。

每调用策略：read-only 拒绝一切变更；workspace-write 仅当目标规范化后落在策略的 workspace 根或平台临时区之下才允许变更（与 Seatbelt 授予的同一可写根集合，由同一个 writableRoots 函数导出，避免 bash 与 fs 漂移）；danger-full-access 无围栏委托。拒绝抛出结构化的 FS_SANDBOX_DENIED——不需要文本推断（不像 bash 的内核 stderr），因为进程内围栏确切知道自己拒绝了什么。升级重试在工具层（tool-fs），与 bash 相同。"""
from ..本地文件系统 import 本地文件系统,Config#本地文件系统后端与配置
from ..文件系统 import 文件系统错误#文件系统错误类
from ...沙盒.沙盒 import 可写根#可写根计算
from .包含 import 是否路径位于下#路径包含判定

配置=Config#沙箱后端配置与本地后端配置相同（cwd、diffBasisMaxBytes）

__all__=['配置','沙箱文件系统','默认']#仅中文公开名；Cordis 槽英文别名不入表

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

class 沙箱文件系统(本地文件系统):#沙箱强制文件系统后端
    """沙箱强制文件系统后端。注册为 ctx.fs（加载它以代替 fs-local，并配合 ctx.sandboxPolicy，就是全部替换——面向模型的工具不动）。其已配置默认模式是 sandboxMode 暴露的能力事实；tool-fs 把每个会话的模式与 cwd 解析成每次变更的策略，已批准的升级可为一次调用盖上严格更宽的模式。"""
    inject=['sandboxPolicy']#构造前需要sandboxPolicy服务
    注入=inject#中文别名
    Config=配置#Cordis配置模式
    def __init__(自身,上下文对象,配置对象):#用上下文与本地配置构造沙箱文件系统
        """用上下文与本地配置构造沙箱文件系统。沙箱默认（模式 + workspace-write 回退根）不在这里——ctx.sandboxPolicy 为每个强制能力解析每次调用会话。"""
        super().__init__(上下文对象,配置对象)#交给本地后端完成存储机制
        自身.默认模式=上下文对象.sandboxPolicy.defaultMode#记下部署默认模式

    @property#只读属性
    def 沙箱模式(自身):#覆盖报告默认沙箱模式
        """部署默认模式——工具层读取以广告升级的能力事实。"""
        return 自身.默认模式#返回构造时记下的部署默认模式

    def 写文本(自身,目标,内容,期望=None,信号=None,沙箱政策=None):#围栏后再原子写入
        """按每调用策略围栏写入，再委托给继承的原子写。见检查目标。"""
        return super().写文本(自身.检查目标(目标,沙箱政策),内容,期望,信号)#先检查目标再委托本地原子写

    def 编辑文本(自身,目标,编辑,期望=None,信号=None,沙箱政策=None):#围栏后再原子编辑
        """按每调用策略围栏编辑，再委托给继承的原子编辑。见检查目标。"""
        return super().编辑文本(自身.检查目标(目标,沙箱政策),编辑,期望,信号)#先检查目标再委托本地原子编辑

    def 检查目标(自身,目标,沙箱政策=None):#按策略检查并返回实际变更目标
        """对目标强制每调用策略，并返回变更必须使用的精确目标，使被检查身份就是被变更身份（没有检查此处写入彼处的 TOCTOU）。read-only 拒绝；workspace-write 此刻再规范化（resolve 对最深已存在祖先做 realpath，反映并发被替换的符号链接），要求包含在可写根下，并返回该新鲜目标；danger-full-access 无围栏返回调用方目标。拒绝时抛出结构化的 FS_SANDBOX_DENIED——工具层把它映射为面向模型的 [sandbox: …] 标记与升级提示。"""
        政策=沙箱政策 if 沙箱政策 is not None else 自身.ctx.sandboxPolicy.resolve()#每调用策略，缺省则解析部署回退
        模式=取字段(政策,'mode')#取出沙箱模式
        if 模式=='danger-full-access':#全权限则不围栏
            return 目标#原样返回调用方目标
        展示路径=取字段(目标,'displayPath')#取出展示路径
        if 模式=='read-only':#只读模式拒绝一切变更
            raise 文件系统错误(f'cannot write "{展示路径}": file access denied under read-only mode','FS_SANDBOX_DENIED')#抛出沙箱拒绝错误
        # workspace-write：在新鲜规范路径上做包含判定（捕获工具解析此目标之后被替换的符号链接祖先），变更用此新鲜目标委托——绝不用过期目标。
        新鲜=自身.解析(展示路径)#按展示路径重新解析得到新鲜目标
        已包含=False#是否落在某一可写根下
        for 根 in 可写根(政策):#遍历策略给出的可写根
            if 是否路径位于下(取字段(新鲜,'targetKey'),根):#新鲜目标键是否位于该根下
                已包含=True#已包含
                break#不必再看其余根
        if not 已包含:#不在任何可写根下则拒绝
            raise 文件系统错误(f'cannot write "{展示路径}": file access denied under workspace-write mode','FS_SANDBOX_DENIED')#抛出workspace-write拒绝
        return 新鲜#返回新鲜目标供后续变更使用

Config=配置#配置别名
默认=沙箱文件系统#默认导出
default=沙箱文件系统#Cordis默认导出
