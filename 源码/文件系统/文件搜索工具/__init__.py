"""登记面向模型的文件系统发现工具（glob、grep）；以前台 argv 跑打包 ripgrep，不经 shell；本包负责模式校验、argv、解析、保留与超时。"""
from ...依赖.schemastery import 布尔字段,数字字段#配置字段
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
from .搜索管道 import (#再导出search-core公开面
    原始输出最大字节,#原始stdout字节上限
    搜索宽限毫秒,#终止宽限期
    搜索元最大字节,#presentationMeta字节上限
    搜索标准错误最大字节,#stderr诊断尾上限
    搜索超时毫秒,#协作超时预算
    搜索错误,#搜索失败类型
    搜索工具错误,#入参校验失败
    预览行,#单行预览截断
    解析rg路径,#解析打包的rg路径
    执行ripgrep,#执行打包的ripgrep
    改成工作目录相对,#展示为工作目录相对路径
    尽力保存格式化结果,#尽力保存完整格式化结果
    保留grep命中,#内联截断grep命中
    保留glob路径,#内联截断glob路径
)#search-core再导出结束

__all__=[#仅中文公开名；Cordis 槽英文别名不入表
    '名称','依赖','配置','应用',
    '通配最大结果数','通配版本控制排除','应用通配工具','构造通配命令','格式化通配输出',
    '解析通配参数','呈现通配调用','呈现通配结果','跨顶层抽样',
    '检索最大行字节','检索最大命中数','应用检索工具','构造检索命令','格式化检索命中',
    '格式化检索输出','解析检索参数','解析检索命中','呈现检索调用','呈现检索结果',
    '原始输出最大字节','搜索宽限毫秒','搜索元最大字节','搜索标准错误最大字节',
]#公开面结束

名称='tool-fs-search'#加载器诊断使用的Cordis插件名
依赖=['tools','systemPrompt','subprocess']#搜索工具套件所需的服务（spillStore可选，经获取服务读取）

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

def 断言正整数(名,值):#断言配置项为正整数
    """每项搜索上限计的是条数/字节/毫秒——必须是正整数，否则保留与超时算术会静默出错。配置入口收成 int。"""
    if isinstance(值,bool):#布尔不是整数
        raise 搜索工具错误('tool-fs-search: '+名+' must be a positive integer')#加载时大声失败
    if isinstance(值,float) and 值.is_integer():#配置入口整值浮点
        值=int(值)#收成int
    if not isinstance(值,int) or 值<1:#非整数或小于1
        raise 搜索工具错误('tool-fs-search: '+名+' must be a positive integer')#加载时大声失败
    return 值#已收成的正整数

def 应用(上下文,配置值):#注册glob与grep工具套件
    """注册 glob/grep 文件系统发现工具套件。打包的 ripgrep 二进制始终可用（依赖附带），因此注册无条件进行。

    @param 上下文 插件上下文；注册都是作用域在本插件上的 effect
    @param 配置值 schemastery 解析后的插件配置，形态是 dict
    """
    通配最大=断言正整数('globMaxResults',配置值['globMaxResults'])#校验glob内联上限
    检索命中=断言正整数('grepMaxMatches',配置值['grepMaxMatches'])#校验grep内联上限
    检索行字节=断言正整数('grepMaxLineBytes',配置值['grepMaxLineBytes'])#校验单行预览上限
    元字节=断言正整数('searchMetaMaxBytes',配置值['searchMetaMaxBytes'])#校验meta字节上限
    原始字节=断言正整数('rawOutputMaxBytes',配置值['rawOutputMaxBytes'])#校验原始stdout上限
    宽限=断言正整数('graceMs',配置值['graceMs'])#校验宽限期为正整数
    if 宽限>定时器延迟上限毫秒:#宽限期超过定时器可表示范围
        raise 搜索工具错误('tool-fs-search: graceMs must be no greater than '+str(定时器延迟上限毫秒))#加载时拒绝过大宽限期
    标准误字节=断言正整数('stderrMaxBytes',配置值['stderrMaxBytes'])#校验stderr尾上限
    超时=断言正整数('timeoutMs',配置值['timeoutMs'])#校验超时预算
    应用通配工具(上下文,{#注册glob工具
        'sampleOverCapGlobResults':配置值['sampleOverCapGlobResults'],#超额是否跨顶层抽样
        'maxResults':通配最大,#内联路径上限
        'maxMetaBytes':元字节,#卡片meta字节上限
        'rawOutputMaxBytes':原始字节,#原始stdout上限
        'graceMs':宽限,#终止宽限期
        'stderrMaxBytes':标准误字节,#stderr尾上限
        'timeoutMs':超时,#协作超时
    })#glob上限交给应用通配工具
    应用检索工具(上下文,{#注册grep工具
        'maxMatches':检索命中,#内联命中上限
        'maxLineBytes':检索行字节,#单行预览上限
        'maxMetaBytes':元字节,#卡片meta字节上限
        'rawOutputMaxBytes':原始字节,#原始stdout上限
        'graceMs':宽限,#终止宽限期
        'stderrMaxBytes':标准误字节,#stderr尾上限
        'timeoutMs':超时,#协作超时
    })#grep上限交给应用检索工具

name=名称#Cordis插件名
inject=依赖#Cordis依赖声明
Config=配置#Cordis配置模式
apply=应用#Cordis插件入口
default=应用#框架槽
