"""进程内一次性子智能体结构化输出运行时（对齐 upstream structured.ts）。"""
from ...内核.工具 import 工具参数错误,校验json模式值#参数校验
结构化输出工具名='structured_output'#工具名
结构化输出指令=(
    'When you have your final answer, you MUST report it by calling the '
    +'`'+结构化输出工具名+'` tool with arguments matching its parameter schema exactly. '
    +'Do not finish with a plain text answer: only the tool call counts as your result.'
)#指令
结构化输出段落顺序=9900#对齐 system-prompt STRUCTURED_OUTPUT

def 渲染结构化记录(_参数,值):#渲染捕获确认
    """渲染结构化输出已记录的文本块。"""
    return [{'type':'text','text':'Structured output recorded.'}]#确认文案

def 附着结构化运行时(子上下文,模式):#attachStructuredRuntime
    """在子体创建窗口挂上捕获工具、指令与守卫。执行与结果均为 dict。"""
    已暂存={}#执行身份→值
    待定=None#PTC 父 token
    已捕获=None#最终值
    def 执行(参数,执行上下文):#capture tool
        """校验参数、暂存值并终止本轮。"""
        违规=校验json模式值(模式,参数)#校验
        if len(违规)>0:#非法
            raise 工具参数错误(违规)#拒绝
        已暂存[id(执行上下文)]={'value':参数}#暂存
        执行上下文['concludeTurn']()#结束回合
        return {'recorded':True}#成功
    子上下文.tools.登记({#注册工具
        'name':结构化输出工具名,#工具名
        'description':'Report your final structured result. Call this exactly once, when your answer is complete.',#描述
        'parameters':模式,#参数模式
        'output':{#输出
            'schema':{#模式
                'type':'object',#对象
                'properties':{'recorded':{'type':'boolean','const':True}},#recorded
                'required':['recorded'],#必填
                'additionalProperties':False,#禁止额外
            },#schema 结束
            'render':渲染结构化记录,#渲染
        },#output 结束
        'execute':执行,#执行
    })#登记结束
    子上下文.systemPrompt.段落({#指令段
        'name':'tool:'+结构化输出工具名,#段名
        'order':结构化输出段落顺序,#顺序
        'text':结构化输出指令,#正文
    })#段落结束
    def 守卫(执行对象):#工具守卫
        """捕获完成后拒绝后续工具。执行对象为 dict。"""
        if 已捕获 is None and 待定 is None:#未完成
            return None#放行
        return 'structured output already recorded: the run is complete, so `'+执行对象['name']+'` is not executed'#拒绝
    子上下文.tools.守卫(守卫)#挂守卫
    def 结果监听(执行对象,结果):#tools/result
        """权威结果到达后提交捕获。执行与结果均为 dict。"""
        nonlocal 已捕获,待定#状态
        if 执行对象['name']==结构化输出工具名:#捕获工具
            项=已暂存.pop(id(执行对象),None)#取暂存
            if 项 is None:#无暂存
                return#跳过
            if 'isError' in 结果 and 结果['isError']:#失败
                return#跳过
            if 'parent' not in 执行对象 or 执行对象['parent'] is None:#直接
                if 已捕获 is None:#首次
                    已捕获={'value':项['value']}#记下
            else:#PTC
                if 已捕获 is None and 待定 is None:#首次
                    待定={'parent':执行对象['parent'],'value':项['value']}#待定
            return#结束
        if 待定 is None:#无待定
            return#跳过
        if 执行对象['token']!=待定['parent']:#非父
            return#跳过
        项=待定#取待定
        待定=None#清
        if 'isError' in 结果 and 结果['isError']:#失败
            return#跳过
        if 已捕获 is None:#首次
            已捕获={'value':项['value']}#记下
    子上下文.监听('tools/result',结果监听)#监听
    def 取已捕获():#读捕获
        """读已提交的结构化值。"""
        return 已捕获#当前捕获
    return {'captured':取已捕获}#句柄

__all__=['结构化输出工具名','结构化输出指令','结构化输出段落顺序','附着结构化运行时']#公开面
