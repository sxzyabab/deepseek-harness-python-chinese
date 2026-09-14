import json#解析结果/参数
from .调用模型 import 派生工具行#行模型

__all__=['提问行','待办行','已答摘要','待办摘要','提问工具视图','待办工具视图']#仅中文公开名

会话命名空间='conversation'#会话词典命名空间

def 缺省翻译(键,_插值=None):#无文案
    """原样返回键。"""
    return 键#键

def 是答案(值):#答案条目形
    """对象即为答案条目候选。"""
    return isinstance(值,dict)#对象

def 已答摘要(文本,翻译):#已答计数摘要
    """从结果 JSON 计已答数；无效则 None。"""
    try:#解析
        解析=json.loads(文本)#JSON
    except (TypeError,ValueError,json.JSONDecodeError):#失败
        return None#无效
    if not isinstance(解析,dict):#非对象
        return None#无效
    答案列表=解析['answers'] if 'answers' in 解析 else None#答案表
    if not isinstance(答案列表,list) or not all(是答案(a) for a in 答案列表):#形不对
        return None#无效
    已答=0#计数
    for a in 答案列表:#逐题
        选=a['selected'] if 'selected' in a else None#选中
        自=a['custom'] if 'custom' in a else None#自定义
        if (isinstance(选,list) and len(选)>0) or (isinstance(自,str) and 自!=''):#已答
            已答+=1#加
    return 翻译('ask.answered',{'answered':已答,'total':len(答案列表)})#摘要

def 计划摘要(条目表):#待办计数
    """done/total/activeContent/activeExtra。"""
    完成=0#完成
    活跃内容=None#活跃正文
    活跃额外=0#并行活跃额外
    for 项 in 条目表:#逐项
        态=项['status'] if 'status' in 项 else None#状态
        if 态=='completed':#完成
            完成+=1#加
        elif 态=='in_progress':#进行
            if 活跃内容 is None:#首个
                活跃内容=项['content'] if 'content' in 项 else None#内容
            else:#并行
                活跃额外+=1#额外
    return {'done':完成,'total':len(条目表),'activeContent':活跃内容,'activeExtra':活跃额外}#摘要

def 待办摘要(参数原文,翻译):#待办行摘要拆分
    """text 可截断；extra 为并行活跃数。"""
    try:#解析
        解析=json.loads(参数原文)#JSON
    except (TypeError,ValueError,json.JSONDecodeError):#失败
        return None#回退
    if not isinstance(解析,dict):#非对象
        return None#回退
    表=解析['todos'] if 'todos' in 解析 else None#todos
    if not isinstance(表,list) or not all(isinstance(i,dict) for i in 表):#形
        return None#回退
    计=计划摘要(表)#计数
    头=翻译('todo.completed',{'done':计['done'],'total':计['total']})#头
    if 计['activeContent'] is None:#无活跃
        return {'text':头,'extra':计['activeExtra']}#仅头
    return {'text':头+' · '+str(计['activeContent']),'extra':计['activeExtra']}#带头+活跃

class 提问行:#ask_user_question 行
    """提问交互一行摘要。"""
    def __init__(自身,属性):#props
        """记下 props。"""
        自身.属性=属性#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性#新

    def 渲染(自身):#结构树
        """派生摘要与状态。"""
        p=自身.属性#props
        块=p['block']#块
        翻译=p['t'] if 't' in p else 缺省翻译#文案
        工具名=p['toolName'] if 'toolName' in p and p['toolName'] else 'ask_user_question'#名
        切片=dict(块)#拷贝
        if 'toolName' not in 切片 and 'name' not in 切片:#缺名
            切片['toolName']=工具名#写入
        模型=派生工具行(切片)#模型
        已结算='kind' in 块#已结算
        错=块['error'] if 已结算 and 'error' in 块 else None#错误
        码=错['code'] if 错 is not None and 'code' in 错 else None#错误码
        摘要=模型['summary']#摘要
        状态=模型['state']#状态
        if 码=='ASK_CANCELLED':#取消
            摘要=翻译('ask.cancelled')#取消文案
        elif 码=='ASK_ABORTED':#中断
            摘要=翻译('ask.interrupted')#中断
            状态='stopped'#停止
        elif 模型['state']=='running':#等待
            摘要=翻译('ask.waiting')#等待
        elif 已结算 and 模型['state']=='ok':#已答
            内容=块['content'] if 'content' in 块 and 块['content'] is not None else []#内容
            文本=''.join((b['text'] if 'text' in b and b['text'] is not None else '') for b in 内容 if isinstance(b,dict) and 'type' in b and b['type']=='text')#拼文本
            计=已答摘要(文本,翻译)#已答
            摘要=计 if 计 is not None else 模型['summary']#已答或回退
        return {#结构树
            'type':'ask-question-row',#类型
            'variant':模型['variant'],#变体
            'title':翻译('ask.rowTitle'),#标题
            'summary':摘要,#摘要
            'body':模型['body'],#正文
            'output':模型['output'],#输出
            'state':状态,#状态
            'inspect':p['inspect'] if 'inspect' in p else None,#检查
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷新
        return 自身.渲染()#渲

class 待办行:#todo_write 行
    """计划更新一行摘要。"""
    def __init__(自身,属性):#props
        """记下 props。"""
        自身.属性=属性#合成

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性#新

    def 渲染(自身):#结构树
        """派生摘要。"""
        p=自身.属性#props
        块=p['block']#块
        翻译=p['t'] if 't' in p else 缺省翻译#文案
        工具名=p['toolName'] if 'toolName' in p and p['toolName'] else 'todo_write'#名
        已结算='kind' in 块#已结算
        if 已结算:#已结算
            调用=块['call'] if 'call' in 块 else None#调用
            参数原文=调用['argsRaw'] if 调用 is not None and 'argsRaw' in 调用 and 调用['argsRaw'] is not None else ''#参数
        else:#进行中
            参数原文=块['argsRaw'] if 'argsRaw' in 块 and 块['argsRaw'] is not None else ''#参数
        切片={'toolName':工具名,'argsRaw':参数原文}#切片
        if 'kind' in 块:#kind
            切片['kind']=块['kind']#写入
        if 'content' in 块:#content
            切片['content']=块['content']#写入
        if 'error' in 块:#error
            切片['error']=块['error']#写入
        if 'isError' in 块:#isError
            切片['isError']=块['isError']#写入
        if 'call' in 块:#call
            切片['call']=块['call']#写入
        模型=派生工具行(切片)#模型
        两半=待办摘要(参数原文,翻译)#摘要
        摘要=两半 if 两半 is not None else {'text':模型['summary'],'extra':0}#摘要
        return {#结构树
            'type':'todo-row',#类型
            'variant':模型['variant'],#变体
            'title':翻译('todo.rowTitle'),#标题
            'summary':摘要['text'],#摘要
            'summarySuffix':('+'+str(摘要['extra'])) if 摘要['extra']>0 else None,#后缀
            'body':模型['body'],#正文
            'output':模型['output'],#输出
            'errorSummary':模型['errorSummary'],#错误
            'state':模型['state'],#状态
            'inspect':p['inspect'] if 'inspect' in p else None,#检查
        }#结束

    def __call__(自身,属性=None):#调用形
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷新
        return 自身.渲染()#渲

def 提问工具视图应用(上下文):#登记提问行
    """登记 ask_user_question toolview。"""
    def 登记():#登记
        """按键条目。"""
        return 上下文.slots.register({#登记
            'name':'tool.call.toolview','key':'ask_user_question','locale':会话命名空间,#选项
        },提问行)#组件
    上下文.slots.inject('tool.call.toolview',登记)#等槽

提问工具视图={'name':'ask-question-toolview','inject':['slots'],'apply':提问工具视图应用}#插件形

def 待办工具视图应用(上下文):#登记待办行
    """登记 todo_write toolview。"""
    def 登记():#登记
        """按键条目。"""
        return 上下文.slots.register({#登记
            'name':'tool.call.toolview','key':'todo_write','locale':会话命名空间,#选项
        },待办行)#组件
    上下文.slots.inject('tool.call.toolview',登记)#等槽

待办工具视图={'name':'todo-toolview','inject':['slots'],'apply':待办工具视图应用}#插件形
