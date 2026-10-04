from ...模型后端.llm.异常 import 装备错误 as 框架错误#导入框架错误基类

class 工具错误(框架错误):
    '内核工具包的异常基类'
    def __init__(自身,消息,码='TOOL_ERROR'):
        '用消息构造'
        super().__init__(消息,码)#框架错误
        自身.name='ToolError'#类名

class 工具未找到错误(框架错误):
    '模型请求未注册工具时抛出'
    def __init__(自身,工具名,可达路径=None):
        '用名字与可选替代路径构造'
        if 可达路径 is None:
            消息='未知工具 "'+工具名+'"'
        else:
            消息='未知工具 "'+工具名+'": '+可达路径
        super().__init__(消息,'UNKNOWN_TOOL')#错误码
        自身.name='ToolNotFoundError'#类名

class 工具输出错误(框架错误):
    '工具函数体或后策略值违反其声明输出时抛出'
    def __init__(自身,工具名,违规列表):
        '用违规构造；公开属性仅 违规列表'
        super().__init__('工具 "'+工具名+'" 返回了非法输出: '+'; '.join(违规列表),'INVALID_TOOL_OUTPUT')#拼消息
        自身.name='ToolOutputError'#错误名槽
        自身.违规列表=违规列表#违规诊断列表

class 代码模式错误(Exception):
    '内核工具代码模式包的异常基类'

class 代码运行失败错误(框架错误):
    '程序运行本身失败时由 run_code 抛出'
    def __init__(自身,消息):
        '用失败消息构造'
        super().__init__(消息,'CODE_RUN_FAILED')#框架错误码
        自身.name='CodeRunFailedError'#类名

class json模式错误(框架错误):
    '原始模式落在受强制子集之外时抛出'
    def __init__(自身,违规列表):
        '用违规列表拼出不支持模式消息；公开属性仅 违规列表'
        super().__init__('unsupported JSON schema: '+'; '.join(违规列表),'UNSUPPORTED_SCHEMA')#拼消息
        自身.name='JsonSchemaError'#错误名槽（跨语言对照字面量）
        自身.违规列表=违规列表#违规诊断列表

class python类型渲染错误(Exception):
    '内核工具类型渲染包的异常基类'

class ts类型渲染错误(Exception):
    '内核工具 TypeScript 类型渲染包的异常基类'

class 工具参数错误(框架错误):
    '带类型工具上模型生成的非法参数'
    def __init__(自身,违规列表):
        '用违规列表构造；公开属性仅 违规列表'
        super().__init__('invalid arguments: '+'; '.join(违规列表),'INVALID_ARGS')#拼消息
        自身.name='ToolArgsError'#错误名槽
        自身.违规列表=违规列表#违规诊断列表
