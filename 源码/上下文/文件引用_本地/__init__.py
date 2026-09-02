"""`ctx.fileReferences` 的本地文件系统实现。

对齐上游 `@deepseek-ai/dsh-file-reference-local`。公开面仅中文名。
"""
import os#路径
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 自然数字段,列表字段,字符串字段#配置字段
光纤状态=cordis.纤程状态#纤程状态
from ..文件引用 import 文件引用服务,文件引用提示#基类与提示
from ..文件引用.词法 import 光标处活动令牌,格式化文件提及#再导出词法
from .搜索 import (#搜索默认值与实现
    默认最大结果数,默认最大条目数,默认排除目录,工作区文件搜索,
)#搜索面

__all__=[#仅中文公开名
    '配置模式','本地文件引用服务','默认',
    '默认最大结果数','默认最大条目数','默认排除目录',
    '文件引用提示','光标处活动令牌','格式化文件提及',
]#公开面结束

配置模式={#插件配置
    'maxResults':自然数字段(最小=1,默认值=默认最大结果数),#单次最多候选
    'maxEntries':自然数字段(最小=1,默认值=默认最大条目数),#索引上限
    'excludedDirectories':列表字段(字符串字段(),默认值=list(默认排除目录)),#排除目录
}#配置结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
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
        return 值.等待()#等待
    return 值#同步值

def 校验配置(配置):#启动前校验配置
    """非法配置让插件激活失败。"""
    最大结果=取字段(配置,'maxResults',默认最大结果数)#结果上限
    最大条目=取字段(配置,'maxEntries',默认最大条目数)#索引上限
    if 最大结果<=0 or 最大条目<=0:#非正
        raise Exception('file-reference-local: maxResults and maxEntries must be positive')#拒绝
    for 名称 in 取字段(配置,'excludedDirectories',默认排除目录):#逐个排除名
        if 名称=='' or '/' in 名称 or '\\' in 名称:#非法目录基名
            raise Exception('file-reference-local: excludedDirectories entries must be non-empty directory basenames')#拒绝

class 本地文件引用服务(文件引用服务):#本地实现
    """按智能体会话 cwd 索引工作区并提供 @ 补全。"""
    Config=配置模式#Cordis 配置
    inject=['agents']#依赖智能体
    注入=['agents']#中文别名

    def __init__(自身,上下文,配置=None):#构造服务
        """为每个智能体懒建索引，并在工具结果后失效。"""
        super().__init__(上下文)#登记 fileReferences
        配置=配置 or {}#默认空
        自身.配置={#解析后配置
            'maxResults':取字段(配置,'maxResults',默认最大结果数),#结果上限
            'maxEntries':取字段(配置,'maxEntries',默认最大条目数),#索引上限
            'excludedDirectories':list(取字段(配置,'excludedDirectories',默认排除目录)),#排除目录
        }#配置结束
        校验配置(自身.配置)#启动前校验
        自身.搜索表={}#智能体→搜索索引
        自身.提示纤程={}#智能体→提示纤程
        自身.提示拆除们=set()#在途提示拆除

        def 安装提示(智能体):#为智能体挂系统提示段
            """read 工具存在时才注入文件引用指引。"""
            if 智能体 in 自身.提示纤程:#已安装
                return#跳过
            def 挂段(作用域):#纤程体内挂段
                """按工具可用性决定是否展示指引。"""
                有读=作用域.tools.get('read',智能体) is not None#是否有 read
                作用域.systemPrompt.section({#挂段
                    'name':'context:file-reference',#段名
                    'order':作用域.systemPrompt.getSectionOrder('FILE_REFERENCE'),#顺序
                    'text':lambda:文件引用提示 if 有读 else '',#动态正文
                })#section结束
            纤程=智能体.ctx.inject(['systemPrompt','tools'],挂段)#子纤程
            自身.提示纤程[智能体]=纤程#记住

        def 拆除提示(智能体):#拆除提示纤程
            """失败只记日志，不阻断主流程。"""
            纤程=自身.提示纤程.pop(智能体,None)#取出
            if 纤程 is None:#无纤程
                return#跳过
            try:#拆除
                任务=纤程.dispose()#异步拆除
                自身.提示拆除们.add(任务)#跟踪
                def 收尾(_):自身.提示拆除们.discard(任务)#完成后摘掉
                if 是否thenable(任务):任务.等待() if hasattr(任务,'wait') else 任务.等待()#同步等待
            except Exception as 错误:#拆除失败
                上下文.logger.warn('file-reference-local: prompt cleanup failed: '+str(错误))#记日志

        for 智能体 in 上下文.agents.list():安装提示(智能体)#已有智能体
        上下文.on('agent/created',lambda 载荷,*_:安装提示(取字段(载荷,'agent')))#新建
        上下文.on('agent/disposed',lambda 载荷,*_:(自身.搜索表.pop(取字段(载荷,'agent'),None) and None,拆除提示(取字段(载荷,'agent'))))#销毁
        def 会话事件(会话,事件,*_):#工具结果后失效索引
            """文件系统变更后让索引过时。"""
            if 取字段(事件,'type')!='tool/result':#只看工具结果
                return#放过
            智能体=上下文.agents.get(取字段(会话,'id'))#按会话找智能体
            if 智能体 is not None:#命中
                搜索=自身.搜索表.get(智能体)#取索引
                if 搜索 is not None:#有索引
                    搜索.失效()#失效
        上下文.on('session/event',会话事件)#监听会话事件
        def 装寿命():#复合 effect
            """拆除时释放全部索引与提示纤程。"""
            def 拆():#拆除闭包
                """清空搜索与提示。"""
                for 搜索 in 自身.搜索表.values():搜索.拆除()#拆索引
                自身.搜索表.clear()#清表
                纤程们=list(自身.提示纤程.values())#拷贝纤程
                自身.提示纤程.clear()#清表
                for 纤程 in 纤程们:#逐个拆除
                    try:解开(纤程.dispose())#等待拆除
                    except Exception:pass#吞掉
            return 拆#返回拆除器
        上下文.effect(装寿命,'file-reference-local: search cache')#登记 effect

    def 列举(自身,智能体,查询,信号):#列举候选
        """按智能体 cwd 根建索引并搜索。"""
        搜索=自身.搜索表.get(智能体)#已有索引
        if 搜索 is None:#首次
            工作目录=取字段(取字段(取字段(智能体,'session'),'header'),'cwd')#会话 cwd
            if 工作目录 is None:#缺 cwd
                工作目录=os.getcwd()#进程 cwd
            搜索=工作区文件搜索(工作目录,自身.配置)#新建索引
            自身.搜索表[智能体]=搜索#缓存
        return 搜索.列举(查询,信号)#搜索

Config=配置模式#Cordis 配置别名
默认=本地文件引用服务#默认导出
default=本地文件引用服务#Cordis 默认导出
