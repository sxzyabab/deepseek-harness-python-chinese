from ...内核.工具 import 校验json模式值#校验参数
from ...内核.工具.异常 import 工具参数错误#非法参数

结构化输出工具='structured_output'#模型必须调用的工具名
结构化输出指令=(#子体尾部作用域提示
    'When you have your final answer, you MUST report it by calling the '
    +'`'+结构化输出工具+'` tool with arguments matching its parameter schema exactly. '
    +'Do not finish with a plain text answer: only the tool call counts as your result.'
)#指令结束

__all__=['结构化输出工具','结构化输出指令','挂上结构化运行时']#仅中文公开名

def 挂上结构化运行时(子上下文,模式,可以完成):
    '在创建窗口给子体挂上作用域捕获工具、指引与终态守卫。子体拆除会卸掉登记'
    暂存={}#本执行 → 待提交值；用执行对象身份做键
    待定=[None]#嵌套捕获，等外层传输提交
    已捕获=[None]#权威结果已接受的值

    def 执行(参数,执行元数据):
        '校验参数、确认可以完成，再按本执行暂存并结束本轮'
        违规=校验json模式值(模式,参数)#违规列表
        if len(违规)>0:#非法参数
            raise 工具参数错误(违规)#模型在同一回合内重试
        if not 可以完成():#还有子任务或待处理消息
            raise Exception('Wait for all delegated child tasks to finish and process pending messages before submitting structured output.')#还不能交
        暂存[id(执行元数据)]={'执行':执行元数据,'value':参数}#两阶段：等权威结果
        结束=执行元数据['concludeTurn'] if isinstance(执行元数据,dict) else 执行元数据.concludeTurn#结束本轮
        结束()#结束
        return {'recorded':True}#已记录

    def 渲染记录(_参数,_值):
        '渲染已记录'
        return [{'type':'text','text':'Structured output recorded.'}]#文本
    子上下文.tools.登记({#登记捕获工具
        'name':结构化输出工具,#工具名
        'description':(#描述
            'Report your final structured result. Call this exactly once, when your answer is complete; '
            +'the arguments must match this tool\'s parameter schema exactly.'
        ),#描述结束
        'parameters':dict(模式),#已断言的对象模式
        'output':{#成功返回
            'schema':{#返回模式
                'type':'object',#对象
                'properties':{'recorded':{'type':'boolean','const':True}},#已记录
                'required':['recorded'],#必填
                'additionalProperties':False,#无额外字段
            },#模式结束
            'render':渲染记录,#渲染
        },#输出结束
        'execute':执行,#执行
    })#登记结束
    子上下文.systemPrompt.段落({#尾部指引
        'name':'tool:'+结构化输出工具,#段名
        'order':子上下文.systemPrompt.获取段落顺序('STRUCTURED_OUTPUT'),#顺序
        'text':结构化输出指令,#正文
    })#段落结束

    def 守卫(执行元数据):
        '捕获之后拒绝后续调用'
        if 已捕获[0] is None and 待定[0] is None:#尚未捕获
            return None#弃权
        名=执行元数据['name'] if isinstance(执行元数据,dict) else 执行元数据.name#工具名
        return 'structured output already recorded: the run is complete, so `'+str(名)+'` is not executed'#拒绝

    子上下文.tools.守卫(守卫)#终态守卫

    def 结果到达(执行元数据,结果):
        '权威 tools/result 成功后才提交捕获'
        名=执行元数据['name'] if isinstance(执行元数据,dict) else 执行元数据.name#工具名
        是错误=结果['isError'] if isinstance(结果,dict) else 结果.isError#是否失败
        if 名==结构化输出工具:#捕获工具自己的结果
            条目=暂存.pop(id(执行元数据),None)#取出并删除暂存
            if 条目 is None:#不是这次暂存
                return#忽略
            if 是错误:#失败则丢弃并重新开放输入
                return#不提交
            父=执行元数据['parent'] if isinstance(执行元数据,dict) and 'parent' in 执行元数据 else getattr(执行元数据,'parent',None)#外层令牌
            if 父 is None:#没有外层传输
                if 已捕获[0] is None:#尚未提交
                    已捕获[0]={'value':条目['value']}#提交
            elif 已捕获[0] is None and 待定[0] is None:#等外层
                待定[0]={'parent':父,'value':条目['value']}#暂挂
            return#处理完
        if 待定[0] is None:#没有待定外层
            return#忽略
        令牌=执行元数据['token'] if isinstance(执行元数据,dict) else 执行元数据.token#本执行令牌
        if 待定[0]['parent'] is not 令牌:#不是包住捕获的那次传输
            return#忽略
        条目=待定[0]#待定值
        待定[0]=None#清掉
        if 是错误:#外层失败则丢弃
            return#重新开放
        if 已捕获[0] is None:#尚未提交
            已捕获[0]={'value':条目['value']}#提交

    子上下文.监听('tools/result',结果到达)#权威结果

    def 读取捕获():
        '已接受的值；还没有则为 None'
        return 已捕获[0]#已捕获或空
    def 接受输入():
        '从暂存到最终结果期间输入关闭'
        return len(暂存)==0 and 待定[0] is None and 已捕获[0] is None#可以再收消息
    return {'captured':读取捕获,'acceptsInput':接受输入}#附件
