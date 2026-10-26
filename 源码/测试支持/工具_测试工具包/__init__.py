'测试用的内容工具夹具，以及单次工具执行'
import json
from ...内核.工具 import 定义工具

__all__=['定义内容工具夹具','执行工具夹具','执行模型工具夹具']

内容值模式={'type':'array','items':{'type':'json'}}


def 定义内容工具夹具(选项):
    '把内容块当成规范 JSON 值。产品工具要声明自己的输出'
    用户执行=选项['execute']
    定义选项=dict(选项)

    def 渲染(_参数,值):
        '规范值就是内容块'
        return 值

    def 执行包装(参数,执行上下文):
        '把夹具产出的内容块交回'
        return 用户执行(参数,执行上下文)

    定义选项['output']={
        'schema':内容值模式,
        'render':渲染,
    }
    定义选项['execute']=执行包装
    return 定义工具(定义选项)


def 执行工具夹具(上下文,输入):
    '直接走准备、派发和收尾。完整单次批次用执行模型工具夹具'
    工具=上下文.tools
    已准备=工具.准备调度执行(输入)
    return 工具.执行完已准备(已准备)


def 执行模型工具夹具(上下文,输入):
    '把一次调用交给工具运行时，不写根会话日志'
    try:
        参数文本=json.dumps(输入['arguments'])
    except (TypeError,ValueError) as 编码错误:
        raise TypeError('Model tool fixture arguments must encode as JSON') from 编码错误
    if 参数文本 is None:
        raise TypeError('Model tool fixture arguments must encode as JSON')
    执行输入={
        'callId':输入['callId'],
        'name':输入['name'],
        'arguments':json.loads(参数文本),
    }
    if 'signal' in 输入:
        执行输入['signal']=输入['signal']
    if 'agent' in 输入 and 输入['agent'] is not None:
        执行输入['agent']=输入['agent']
    if 'toolSet' in 输入 and 输入['toolSet'] is not None:
        执行输入['toolSet']=输入['toolSet']
    return 上下文.tools.执行(执行输入)
