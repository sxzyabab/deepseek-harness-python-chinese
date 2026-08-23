"""LSP 能力缝（`ctx.lsp`）的服务定义：语言服务器提供方注册表，以及对归一化 goToDefinition/findReferences/goToImplementation/hover 查询按次、与顺序无关的选择。

提供方原子预留一个品牌 id 与一组独占文件扩展名：`登记提供方` 在变更前校验并做冲突检查，因此无效或冲突的注册什么也不发布，其拆除器一并释放全部预留。选择按文件的最终扩展名路由；从不依赖注册顺序。本缝只暴露四种操作，没有 JSON-RPC 逃生口。

对齐上游 `@deepseek-ai/dsh-lsp`。公开面仅中文名。服务槽键、错误 code 与诊断英文字面量保持上游。
"""
import re#扩展名形态校验
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#导入 Cordis 服务基类
是否thenable=cordis.工具.是否thenable#可等待判定
from ..llm import 装备错误#导入带稳定 code 的 HarnessError
from .品牌 import 语言服务器提供方标识#再导出提供方 id 工厂
from .类型 import (#再导出缝公开词汇
    语言服务器操作,#四种语义操作
    语言服务器位置字段,#零基光标
    语言服务器范围字段,#半开范围
    语言服务器查询请求字段,#调用方查询
    语言服务器提供方查询字段,#提供方查询
    语言服务器定位字段,#归一化位置
    语言服务器悬停字段,#归一化悬停
    语言服务器查询结果种类,#结果 kind
    语言服务器提供方字段,#提供方词汇
    语言服务器服务字段,#服务词汇
)#类型面结束

__all__=[#仅中文公开名
    '语言服务器提供方标识','语言服务器错误','最终扩展名','语言服务器','默认',
    '语言服务器操作','语言服务器位置字段','语言服务器范围字段',
    '语言服务器查询请求字段','语言服务器提供方查询字段',
    '语言服务器定位字段','语言服务器悬停字段','语言服务器查询结果种类',
    '语言服务器提供方字段','语言服务器服务字段',
]#公开面结束

扩展名形态=re.compile(r'^\.[^./\\]+$')#形态良好的归一化扩展名：一个点后跟一个或多个非点、非分隔符字符

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

class 语言服务器错误(装备错误):#结构化 LSP 失败
    """结构化 LSP 失败。扩展 HarnessError，带稳定 code（LSP_INVALID_PROVIDER、LSP_CONFLICT、LSP_UNAVAILABLE、LSP_DISPOSED、LSP_UNSUPPORTED_OPERATION、LSP_MALFORMED_RESPONSE、…），调用方按 code 路由而不是解析 message。"""
    def __init__(自身,消息,码,选项=None):#记下稳定 code 并把 cause 链到本错误
        """记下稳定 code，并把 cause 链到本错误。"""
        装备错误.__init__(自身,消息,码,选项)#交给装备错误基类
        自身.name='LspError'#与公开类名一致（协议字段字面量）

def 最终扩展名(文件路径):#取文件最终扩展名
    """提取文件最终扩展名为归一化、小写、带前导点的键（例如 Foo.TS → .ts，foo.d.ts → .ts）。无扩展名或前导点点文件（.bashrc）返回 ''，没有任何路由会匹配。同时按 / 与 \\ 分割，调用方路径分隔符不改变结果。"""
    斜杠=文件路径.rfind('/')#找最后正斜杠
    反斜杠=文件路径.rfind('\\')#找最后反斜杠
    最后分隔=斜杠 if 斜杠>反斜杠 else 反斜杠#两者取更靠后的
    基名=文件路径[最后分隔+1:] if 最后分隔>=0 else 文件路径#取出基名
    点=基名.rfind('.')#找最后一个点
    # 点<=0同时覆盖“无点”(-1)与前导点点文件(0)：两者都没有扩展名。
    if 点<=0:#无扩展名则返回空串
        return ''#空串
    return 基名[点:].lower()#返回小写带点扩展名

def 归一化扩展名(扩展):#把扩展名转小写并确保带前导点
    """把扩展名转小写并确保带前导点；其余由扩展名形态拒绝。"""
    小写=扩展.lower()#先转小写
    if 小写.startswith('.'):#已有前导点
        return 小写#原样
    return '.'+小写#缺前导点则补上

class 语言服务器(服务):#ctx.lsp 服务实现
    """ctx.lsp。持有 id 预留与扩展→路由表；两者按提供方一起填充与清空，因此路由始终对应活着的提供方。"""
    def __init__(自身,ctx):#构造 LSP 服务
        """以 lsp 服务名挂到上下文。"""
        super().__init__(ctx,'lsp')#以 lsp 服务名挂到上下文
        自身.提供方标识们=set()#已预留的提供方 id
        自身.路由表={}#扩展名到路由（插入序无关选择）

    def 登记提供方(自身,提供方):#注册提供方，失败则什么也不发布
        """注册一个提供方，原子预留其 id 与每一个归一化扩展。任何冲突或无效输入都不发布并抛出语言服务器错误；返回的拆除器释放全部预留。随调用光纤拆除。"""
        # 任何变更前先校验并做冲突检查：无效或冲突的注册必须什么也不发布（大声失败、全有或全无）。
        标识=取字段(提供方,'id')#取出提供方 id
        if 标识 is None or str(标识).strip()=='':#id 为空
            raise 语言服务器错误('an LSP provider id must be a non-empty string','LSP_INVALID_PROVIDER')#拒绝空 id
        if 标识 in 自身.提供方标识们:#id 已被占用
            raise 语言服务器错误('an LSP provider with id "'+str(标识)+'" is already registered','LSP_CONFLICT')#拒绝重复 id
        扩展映射=取字段(提供方,'extensionToLanguage')#扩展到语言 id 映射
        if 扩展映射 is None:#缺映射
            条目们=[]#空条目
        elif isinstance(扩展映射,dict):#映射
            条目们=list(扩展映射.items())#展开条目
        else:#对象属性表
            条目们=list(vars(扩展映射).items()) if hasattr(扩展映射,'__dict__') else []#尽力展开
        if len(条目们)==0:#没有任何扩展
            raise 语言服务器错误('LSP provider "'+str(标识)+'" registers no file extensions','LSP_INVALID_PROVIDER')#拒绝空映射
        # 先归一进本提供方的路由集，捕获提供方内部重复（例如 .TS 与 .ts），再检查跨提供方冲突。
        待提交={}#待提交的本提供方路由
        for 原始扩展,语言标识 in 条目们:#逐条校验扩展映射
            扩展=归一化扩展名(str(原始扩展))#归一化扩展名
            if not 扩展名形态.match(扩展):#扩展名形态无效
                raise 语言服务器错误('LSP provider "'+str(标识)+'" maps an invalid extension "'+str(原始扩展)+'"','LSP_INVALID_PROVIDER')#拒绝无效扩展
            if 语言标识 is None or str(语言标识).strip()=='':#语言 id 为空
                raise 语言服务器错误('LSP provider "'+str(标识)+'" maps extension "'+扩展+'" to an empty language id','LSP_INVALID_PROVIDER')#拒绝空语言 id
            if 扩展 in 待提交:#本提供方内重复扩展
                raise 语言服务器错误('LSP provider "'+str(标识)+'" maps extension "'+扩展+'" more than once','LSP_INVALID_PROVIDER')#拒绝内部重复
            待提交[扩展]={'provider':提供方,'languageId':语言标识}#记下待提交路由
        for 扩展 in 待提交.keys():#再检查跨提供方冲突
            if 扩展 in 自身.路由表:#该扩展已被其他提供方占用
                raise 语言服务器错误('extension "'+扩展+'" is already handled by another LSP provider','LSP_CONFLICT')#拒绝跨提供方冲突
        # 全部检查通过：在同一个生命周期控制器里预留 id 与每个扩展，拆除时一并释放。
        def 挂上():#用 effect 绑定注册生命周期
            """预留 id 与全部扩展路由，拆除时一并释放。"""
            自身.提供方标识们.add(标识)#预留提供方 id
            for 扩展,路由 in 待提交.items():#写入全部扩展路由
                自身.路由表[扩展]=路由#写入路由
            def 拆除():#拆除时释放全部预留
                """释放提供方 id 与本提供方全部路由。"""
                自身.提供方标识们.discard(标识)#释放提供方 id
                for 扩展 in 待提交.keys():#删除本提供方全部路由
                    自身.路由表.pop(扩展,None)#删除路由
            return 拆除#拆除回调
        释放=自身.ctx.effect(挂上,'lsp.registerProvider()')#绑定 effect 并标记标签
        def 同步拆除():#对外返回同步拆除函数
            """ctx.effect 的拆除器可能返回可等待；本拆除器 API 是同步即发即忘。"""
            释放()#丢掉（始终已决议的）承诺
        return 同步拆除#对外拆除器

    def 查询(自身,请求,信号=None):#按最终扩展名选择提供方并查询
        """按文件扩展名选择提供方并运行一次查询。选择按查询、与注册顺序无关；无匹配则抛出语言服务器错误 LSP_UNAVAILABLE。"""
        文件路径=取字段(请求,'filePath')#源文件路径
        路由=自身.路由表.get(最终扩展名(文件路径 if 文件路径 is not None else ''))#按文件最终扩展名取路由
        if 路由 is None:#没有任何提供方处理该扩展
            raise 语言服务器错误('no LSP provider handles "'+str(文件路径)+'"','LSP_UNAVAILABLE')#抛出不可用
        提供方查询=dict(请求) if isinstance(请求,dict) else {#拷贝调用方请求
            'operation':取字段(请求,'operation'),#语义操作
            'filePath':取字段(请求,'filePath'),#源路径
            'position':取字段(请求,'position'),#光标
            'workspaceRoot':取字段(请求,'workspaceRoot'),#工作区根
        }#请求骨架
        提供方查询['languageId']=取字段(路由,'languageId')#把推导出的语言 id 交给选中提供方
        查询入口=取字段(取字段(路由,'provider'),'query')#提供方查询入口
        return 解开(查询入口(提供方查询,信号))#执行并解开承诺

默认=语言服务器#默认导出 LSP 服务类
