"""面向模型的文件系统发现工具套件（`glob`、`grep`），跑在打包的 ripgrep 二进制上。本插件一次注册两个工具；二进制随依赖附带，因此不需要系统安装 `rg`，也不经过 shell 层。

## 由 spawn 支撑，不是 `ctx.fs` 提供方方法

本地工作区发现是进程支撑的 `rg` 工作流，因此这些工具通过 `ctx.subprocess.spawn()` 以固定的 ripgrep argv 模板执行——绝不用 `ctx.shell`，绝不用 `ctx.shell.start()`，也绝不是模型可见的后台任务。工具层拥有模式、参数校验、argv 构造、结果解析、保留、格式化结果溢出与超时声明；子进程 seam 拥有 spawn 执行、进程树终止、环境擦洗与原始输出捕获。本包注入 `tools`、`systemPrompt` 与 `subprocess`——故意不注入 `fs`；`ctx.spillStore` 用 `ctx.get()` 机会性读取，因为格式化结果溢出是可选的。

返回路径相对已解析工作目录展示，且仅在工作目录与文件系统 `read` 根是同一工作区的共置部署中可跟进读取——这是已文档化的 v1 部署要求，不是运行时校验。
"""
from ...依赖 import cordis#外部依赖胶水
from ...依赖 import schemastery#配置字段
布尔字段=schemastery.布尔字段#配置字段
数字字段=schemastery.数字字段#配置字段
from ...工具.超时 import 定时器延迟上限毫秒#导入定时器延迟上限
from .通配 import (#再导出glob公开面
    通配最大结果数,#内联路径默认上限
    通配版本控制排除,#VCS排除名
    应用通配工具,#注册glob工具
    构造通配命令,#构造rg --files argv
    格式化通配输出,#格式化抽样页
    解析通配参数,#校验glob参数
    呈现通配调用,#调用中卡片
    呈现通配结果,#完成后卡片
    跨顶层抽样,#跨顶层轮询抽样
)#glob再导出结束
from .检索 import (#再导出grep公开面
    检索最大行字节,#单行预览字节上限
    检索最大命中数,#内联命中上限
    应用检索工具,#注册grep工具
    构造检索命令,#构造rg --json argv
    格式化检索命中,#按文件分组格式化命中
    格式化检索输出,#格式化面向模型的grep结果
    解析检索参数,#校验grep参数
    解析检索命中,#解析rg --json stdout
    呈现检索调用,#调用中卡片
    呈现检索结果,#完成后卡片
)#grep再导出结束
from .搜索核心 import (#再导出search-core公开面
    原始输出最大字节,#原始stdout字节上限
    搜索宽限毫秒,#终止宽限期
    搜索元最大字节,#presentationMeta字节上限
    搜索标准错误最大字节,#stderr诊断尾上限
    搜索超时毫秒,#协作超时预算
    搜索错误,#搜索失败类型
    预览行,#单行预览截断
    解析rg路径,#解析打包的rg路径
    跑ripgrep,#跑打包的ripgrep
    改成工作目录相对,#展示为工作目录相对路径
    尽力保存格式化结果,#尽力保存完整格式化结果
    保留grep命中,#内联截断grep命中
    保留glob路径,#内联截断glob路径
)#search-core再导出结束

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '名称','注入','配置','应用','默认',
    '通配最大结果数','通配版本控制排除','应用通配工具','构造通配命令','格式化通配输出',
    '解析通配参数','呈现通配调用','呈现通配结果','跨顶层抽样',
    '检索最大行字节','检索最大命中数','应用检索工具','构造检索命令','格式化检索命中',
    '格式化检索输出','解析检索参数','解析检索命中','呈现检索调用','呈现检索结果',
    '原始输出最大字节','搜索宽限毫秒','搜索元最大字节','搜索标准错误最大字节',
]#公开面结束

名称='tool-fs-search'#加载器诊断使用的Cordis插件名
注入=['tools','systemPrompt','subprocess']#搜索工具套件所需的服务（spillStore可选，经ctx.get读取）
name=名称#Cordis插件名
inject=注入#Cordis依赖声明

配置={#插件配置；超额glob抽样是显式部署选择，其余字段有默认值
    'sampleOverCapGlobResults':布尔字段(可空=False),#超额glob是否跨顶层抽样，必填
    'globMaxResults':数字字段(默认值=通配最大结果数),#glob内联路径上限
    'grepMaxMatches':数字字段(默认值=检索最大命中数),#grep内联命中上限
    'grepMaxLineBytes':数字字段(默认值=检索最大行字节),#单行预览字节上限
    'searchMetaMaxBytes':数字字段(默认值=搜索元最大字节),#presentationMeta字节上限
    'rawOutputMaxBytes':数字字段(默认值=原始输出最大字节),#原始stdout字节上限
    'graceMs':数字字段(默认值=搜索宽限毫秒),#终止宽限期
    'stderrMaxBytes':数字字段(默认值=搜索标准错误最大字节),#stderr诊断尾上限
    'timeoutMs':数字字段(默认值=搜索超时毫秒),#协作超时预算
}#配置模式结束
Config=配置#Cordis配置模式

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否整数(值):#对齐Number.isInteger
    """整数判定（排除布尔）；浮点整值也接受。"""
    if isinstance(值,bool):#布尔不是整数
        return False#非法
    if isinstance(值,int):#整型
        return True#合法
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return True#合法
    return False#其余非法

def 断言正整数(名,值):#断言配置项为正整数
    """每项搜索上限计的是条数/字节/毫秒——必须是正整数，否则保留与超时算术会静默出错。"""
    if (not 是否整数(值)) or 值<1:#非整数或小于1
        raise Exception('tool-fs-search: '+名+' must be a positive integer')#加载时大声失败

def 应用(上下文,配置值):#注册glob与grep工具套件
    """注册 glob/grep 文件系统发现工具套件。打包的 ripgrep 二进制始终可用（依赖附带），因此注册无条件进行。

    @param 上下文 插件上下文；注册都是作用域在本插件上的 effect
    @param 配置值 schemastery 解析后的插件配置
    """
    #schemastery（Config）已填好每个有默认值的字段。
    断言正整数('globMaxResults',取字段(配置值,'globMaxResults'))#校验glob内联上限
    断言正整数('grepMaxMatches',取字段(配置值,'grepMaxMatches'))#校验grep内联上限
    断言正整数('grepMaxLineBytes',取字段(配置值,'grepMaxLineBytes'))#校验单行预览上限
    断言正整数('searchMetaMaxBytes',取字段(配置值,'searchMetaMaxBytes'))#校验meta字节上限
    断言正整数('rawOutputMaxBytes',取字段(配置值,'rawOutputMaxBytes'))#校验原始stdout上限
    断言正整数('graceMs',取字段(配置值,'graceMs'))#校验宽限期为正整数
    if 取字段(配置值,'graceMs')>定时器延迟上限毫秒:#宽限期超过定时器可表示范围
        raise Exception('tool-fs-search: graceMs must be no greater than '+str(定时器延迟上限毫秒))#加载时拒绝过大宽限期
    断言正整数('stderrMaxBytes',取字段(配置值,'stderrMaxBytes'))#校验stderr尾上限
    断言正整数('timeoutMs',取字段(配置值,'timeoutMs'))#校验超时预算
    应用通配工具(上下文,{#注册glob工具
        'sampleOverCapGlobResults':取字段(配置值,'sampleOverCapGlobResults'),#超额是否跨顶层抽样
        'maxResults':取字段(配置值,'globMaxResults'),#内联路径上限
        'maxMetaBytes':取字段(配置值,'searchMetaMaxBytes'),#卡片meta字节上限
        'rawOutputMaxBytes':取字段(配置值,'rawOutputMaxBytes'),#原始stdout上限
        'graceMs':取字段(配置值,'graceMs'),#终止宽限期
        'stderrMaxBytes':取字段(配置值,'stderrMaxBytes'),#stderr尾上限
        'timeoutMs':取字段(配置值,'timeoutMs'),#协作超时
    })#glob上限交给应用通配工具
    应用检索工具(上下文,{#注册grep工具
        'maxMatches':取字段(配置值,'grepMaxMatches'),#内联命中上限
        'maxLineBytes':取字段(配置值,'grepMaxLineBytes'),#单行预览上限
        'maxMetaBytes':取字段(配置值,'searchMetaMaxBytes'),#卡片meta字节上限
        'rawOutputMaxBytes':取字段(配置值,'rawOutputMaxBytes'),#原始stdout上限
        'graceMs':取字段(配置值,'graceMs'),#终止宽限期
        'stderrMaxBytes':取字段(配置值,'stderrMaxBytes'),#stderr尾上限
        'timeoutMs':取字段(配置值,'timeoutMs'),#协作超时
    })#grep上限交给应用检索工具
    return 已兑现(None)#保持async使加载时配置拒绝成为rejection而非同步抛出

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
