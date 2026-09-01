"""进程内一次性子智能体结构化输出运行时（对齐 upstream structured.ts）。"""
结构化输出工具名='structured_output'#工具名
结构化输出指令=(
    'When you have your final answer, you MUST report it by calling the '
    +'`'+结构化输出工具名+'` tool with arguments matching its parameter schema exactly. '
    +'Do not finish with a plain text answer: only the tool call counts as your result.'
)#指令

def 附着结构化运行时(子上下文,模式):#attachStructuredRuntime
    """在子体创建窗口挂上捕获工具、指令与守卫。"""
    已暂存={}#ToolExecution→值
    待定=None#PTC 父 token
    已捕获=None#最终值
    def 执行(参数,执行上下文):#capture tool
        from ...内核.工具 import 工具参数错误,校验json模式值#惰性导入
        违规=校验json模式值(模式,参数)#校验
        if len(违规)>0:#非法
            raise 工具参数错误(违规)#拒绝
        已暂存[id(执行上下文)]={'value':参数}#暂存
        执行上下文.concludeTurn()#结束回合
        return {'recorded':True}#成功
    子上下文.tools.register({#注册工具
        'name':结构化输出工具名,
        'description':'Report your final structured result. Call this exactly once, when your answer is complete.',
        'parameters':模式,
        'output':{'schema':{'type':'object','properties':{'recorded':{'type':'boolean','const':True}},'required':['recorded'],'additionalProperties':False},
                  'render':lambda _参数,值:[{'type':'text','text':'Structured output recorded.'}]},
        'execute':执行,
    })#注册结束
    子上下文.systemPrompt.section({
        'name':'tool:'+结构化输出工具名,
        'order':子上下文.systemPrompt.getSectionOrder('STRUCTURED_OUTPUT'),
        'text':结构化输出指令,
    })#指令段
    def 守卫(执行):#工具守卫
        if 已捕获 is None and 待定 is None:#未完成
            return None#放行
        return 'structured output already recorded: the run is complete, so `'+执行.name+'` is not executed'#拒绝
    子上下文.tools.guard(守卫)#挂守卫
    def 结果监听(执行,结果):#tools/result
        if 执行.name==结构化输出工具名:#捕获工具
            项=已暂存.pop(id(执行),None)#取暂存
            if 项 is None or 结果.get('isError'):#失败
                return#跳过
            nonlocal 已捕获,待定#状态
            if getattr(执行,'parent',None) is None:#直接
                if 已捕获 is None:#首次
                    已捕获={'value':项['value']}#记下
            else:#PTC
                if 已捕获 is None and 待定 is None:#首次
                    待定={'parent':执行.parent,'value':项['value']}#待定
            return#结束
        if 待定 is None or 待定.get('parent')!=getattr(执行,'token',None):#非父
            return#跳过
        项=待定#取待定
        待定=None#清
        if 结果.get('isError'):#失败
            return#跳过
        if 已捕获 is None:#首次
            已捕获={'value':项['value']}#记下
    子上下文.on('tools/result',结果监听)#监听
    return {'captured':lambda:已捕获}#句柄

__all__=['结构化输出工具名','结构化输出指令','附着结构化运行时']#公开面
