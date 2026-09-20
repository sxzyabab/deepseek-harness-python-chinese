"""`ctx.fileReferences` 的本地文件系统实现。"""
import os#路径
from ...依赖.schemastery import 自然数字段,列表字段,字符串字段
from ..文件引用 import 文件引用服务,文件引用提示#基类与提示
from ..文件引用.词法 import 光标处活动令牌,格式化文件提及#再导出词法
from .搜索 import (#搜索默认值与实现
    默认最大结果数,默认最大条目数,默认排除目录,工作区文件搜索,文件引用本地错误,
)#搜索面

__all__=[
    '包名','名称','依赖','默认','配置模式','本地文件引用服务',
    '默认最大结果数','默认最大条目数','默认排除目录',
    '文件引用提示','光标处活动令牌','格式化文件提及','文件引用本地错误',
]

配置模式={#插件配置
    'maxResults':自然数字段(最小=1,默认值=默认最大结果数),#单次最多候选
    'maxEntries':自然数字段(最小=1,默认值=默认最大条目数),#索引上限
    'excludedDirectories':列表字段(字符串字段(),默认值=list(默认排除目录)),#排除目录
}
包名='@deepseek-ai/dsh-file-reference-local'
名称='file-reference-local'
依赖=['agents']

def 校验配置(配置):
    """非法配置让插件激活失败。"""
    最大结果=配置['maxResults'] if 'maxResults' in 配置 else 默认最大结果数#结果上限
    最大条目=配置['maxEntries'] if 'maxEntries' in 配置 else 默认最大条目数#索引上限
    if 最大结果<=0 or 最大条目<=0:#非正
        raise 文件引用本地错误('file-reference-local: maxResults and maxEntries must be positive')#拒绝
    排除=配置['excludedDirectories'] if 'excludedDirectories' in 配置 else 默认排除目录#排除名
    for 名称 in 排除:#逐个排除名
        if 名称=='' or '/' in 名称 or '\\' in 名称:#非法目录基名
            raise 文件引用本地错误('file-reference-local: excludedDirectories entries must be non-empty directory basenames')#拒绝

class 本地文件引用服务(文件引用服务):
    """按智能体会话 cwd 索引工作区并提供 @ 补全。"""

    def __init__(自身,上下文,配置=None):
        """为每个智能体懒建索引，并在工具结果后失效。"""
        super().__init__(上下文)#登记 fileReferences
        if 配置 is None:#默认空
            配置={}#空配置
        自身.配置={#解析后配置
            'maxResults':配置['maxResults'] if 'maxResults' in 配置 else 默认最大结果数,#结果上限
            'maxEntries':配置['maxEntries'] if 'maxEntries' in 配置 else 默认最大条目数,#索引上限
            'excludedDirectories':list(配置['excludedDirectories'] if 'excludedDirectories' in 配置 else 默认排除目录),#排除目录
        }
        校验配置(自身.配置)#启动前校验
        自身.搜索表={}#智能体→搜索索引
        自身.提示纤程={}#智能体→提示纤程
        自身.提示拆除器表=set()#在途提示拆除

        def 安装提示(智能体):
            """read 工具存在时才注入文件引用指引。"""
            if 智能体 in 自身.提示纤程:#已安装
                return#跳过
            def 挂段(作用域):
                """按工具可用性决定是否展示指引。"""
                有读=作用域.tools.获取('read',智能体) is not None#是否有 read
                def 提示正文():
                    """read 工具存在时才给出指引。"""
                    return 文件引用提示 if 有读 else ''#动态正文
                作用域.systemPrompt.section({#挂段
                    'name':'context:file-reference',#段名
                    'order':作用域.systemPrompt.getSectionOrder('FILE_REFERENCE'),#顺序
                    'text':提示正文,#动态正文
                })#section结束
            纤程=智能体.ctx.依赖启动(['systemPrompt','tools'],挂段)#子纤程
            自身.提示纤程[智能体]=纤程#记住

        def 拆除提示(智能体):
            """失败只记日志，不阻断主流程。"""
            纤程=自身.提示纤程.pop(智能体,None)#取出
            if 纤程 is None:#无纤程
                return#跳过
            try:#拆除
                纤程.拆除()#同步拆除
            except (OSError,RuntimeError,AttributeError) as 错误:
                上下文.日志.警告('file-reference-local: prompt cleanup failed: '+str(错误))#记日志

        def 智能体已创建(载荷,*_位置参数):
            """新建智能体时挂提示。"""
            安装提示(载荷['agent'])#安装

        def 智能体已拆除(载荷,*_位置参数):
            """销毁智能体时清索引与提示。"""
            智能体=载荷['agent']#被拆智能体
            自身.搜索表.pop(智能体,None)#清索引
            拆除提示(智能体)#拆提示

        for 智能体 in 上下文.agents.列出():#已有智能体
            安装提示(智能体)#安装
        上下文.监听('agent/created',智能体已创建)#新建
        上下文.监听('agent/disposed',智能体已拆除)#销毁
        def 会话事件(会话,事件,*_位置参数):
            """文件系统变更后让索引过时。"""
            if 事件['type']!='tool/result':#只看工具结果
                return#放过
            智能体=上下文.agents.获取(会话.id)#按会话找智能体
            if 智能体 is not None:#命中
                搜索=自身.搜索表.get(智能体)#取索引
                if 搜索 is not None:#有索引
                    搜索.失效()#失效
        上下文.监听('session/event',会话事件)#监听会话事件
        def 装寿命():
            """拆除时释放全部索引与提示纤程。"""
            def 拆():
                """清空搜索与提示。"""
                for 搜索 in 自身.搜索表.values():#逐个索引
                    搜索.拆除()#拆索引
                自身.搜索表.clear()#清表
                纤程列表=list(自身.提示纤程.values())#拷贝纤程
                自身.提示纤程.clear()#清表
                for 纤程 in 纤程列表:#逐个拆除
                    try:#拆除
                        纤程.拆除()#同步拆除
                    except (OSError,RuntimeError,AttributeError):
                        pass#吞掉
            return 拆#返回拆除器
        上下文.副作用(装寿命,'file-reference-local: search cache')#登记 effect

    def 列举(自身,智能体,查询,信号):
        """按智能体 cwd 根建索引并搜索。"""
        搜索=自身.搜索表.get(智能体)#已有索引
        if 搜索 is None:#首次
            头=智能体.session.header#会话头
            工作目录=头['cwd'] if 'cwd' in 头 else None#会话 cwd
            if 工作目录 is None:#缺 cwd
                工作目录=os.getcwd()#进程 cwd
            搜索=工作区文件搜索(工作目录,自身.配置)#新建索引
            自身.搜索表[智能体]=搜索#缓存
        return 搜索.列举(查询,信号)#搜索

默认=本地文件引用服务
name=名称#框架槽
inject=依赖#框架槽
Config=配置模式#框架槽
default=默认#框架槽
本地文件引用服务.inject=依赖#框架槽
