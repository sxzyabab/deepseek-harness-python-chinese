import json

__all__=['定义卡片','运行卡片','动作卡片']

def 首行(文本):
    '折叠成一行，给错误摘要用'
    位置=文本.find('\n')#第一个换行
    if 位置==-1:#没有换行
        return 文本#整段
    return 文本[:位置]#第一行

def 串字段(源,键):
    '读非空字符串。空串和别的类型都当没有'
    值=源.get(键)#字段
    if isinstance(值,str) and 值!='':#非空串
        return 值#用它
    return None#没有

def 解析参数(原文):
    '解析调用参数。截断的 JSON 当没有'
    try:#运行中的参数可能还不是完整 JSON
        解析=json.loads(原文)#对象
    except Exception:#截断或不是 JSON
        return None#当没有
    if isinstance(解析,dict):#对象
        return 解析#参数
    return None#数组和标量不当参数

def 结果文本(块):
    '把结果内容压成一段。没有正文时用错误名和码'
    段=[]#各段
    for 项 in 块['content']:#逐段
        if isinstance(项,dict) and 项.get('type')=='text':#文本段
            段.append(项['text'])#原文
        else:#别的段
            段.append(json.dumps(项,ensure_ascii=False,indent=2))#整段 JSON
    文本='\n'.join(段)#拼起来
    if 文本!='':#有正文
        return 文本#正文
    错误=块.get('error')#错误对象
    if 错误 is None:#没有错误
        return None#没有结果文本
    return str(错误['name'])+': '+str(错误['code'])#名和码

def 调用状态(块):
    'running、ok、error 或 stopped'
    if 'kind' not in 块:#还没落定
        return 'running'#进行中
    错误=块.get('error')#错误
    if isinstance(错误,dict) and 错误.get('code')=='interrupted':#被打断
        return 'stopped'#已中断
    if 块.get('isError'):#失败
        return 'error'#错误
    return 'ok'#成功

def 元对象(块):
    '成功落定且 meta 是对象时返回它'
    if 'kind' not in 块 or 块.get('isError'):#未落定或失败
        return None#不读 meta
    元=块.get('meta')#元数据
    if isinstance(元,dict):#对象
        return 元#用它
    return None#没有

def 参数原文(块,已落定):
    '落定从 call 取，进行中从块上取。缺了是空串'
    if 已落定:#已有结果
        调用=块.get('call')#调用头
        原文=调用.get('argsRaw') if isinstance(调用,dict) else None#参数原文
    else:#进行中
        原文=块.get('argsRaw')#参数原文
    if isinstance(原文,str):#字符串
        return 原文#用它
    return ''#缺席

def 定义卡片(块):
    '从定义调用的参数和结果做出一张卡片'
    已落定='kind' in 块#是否已有结果
    原文=参数原文(块,已落定)#参数原文
    参数=解析参数(原文)#参数对象
    代码=None#代码对象
    if 参数 is not None:#有参数
        代码值=参数.get('code')#code 字段
        if isinstance(代码值,dict):#对象
            代码=代码值#宿主和客户端源码
    状态=调用状态(块)#调用状态
    输出=结果文本(块) if 已落定 else None#结果文本
    元=元对象(块)#成功时的元数据
    原始名=None if 原文=='' else 首行(原文)#还没有名字时用参数首行
    if 参数 is None:#参数还不可读
        名称=原始名#首行
    else:#读 name
        读名=串字段(参数,'name')#声明的名字
        名称=原始名 if 读名 is None else 读名#空名回退首行
    return {
        'pluginId':None if 元 is None else 串字段(元,'pluginId'),#插件
        'packageId':None if 元 is None else 串字段(元,'packageId'),#包
        'name':名称,#名字
        'purpose':None if 参数 is None else 串字段(参数,'purpose'),#用途
        'hostCode':None if 代码 is None else 串字段(代码,'host'),#宿主半
        'clientCode':None if 代码 is None else 串字段(代码,'client'),#客户端半
        'output':输出,#结果
        'errorSummary':首行(输出) if 状态=='error' and 输出 is not None else None,#错误首行
        'state':状态,#状态
    }

def 运行卡片(块):
    '从运行调用的参数和结果做出一张卡片'
    已落定='kind' in 块#是否已有结果
    原文=参数原文(块,已落定)#参数原文
    参数=解析参数(原文)#参数对象
    元=元对象(块)#成功时的元数据
    状态=调用状态(块)#调用状态
    输出=结果文本(块) if 已落定 else None#结果文本
    模式原文=None if 参数 is None else 串字段(参数,'mode')#run 或 update
    参数插件=None if 参数 is None else 串字段(参数,'pluginId')#参数里的插件
    参数包=None if 参数 is None else 串字段(参数,'packageId')#参数里的包
    if 元 is None:#没有元数据
        插件=参数插件#用参数
        包=参数包#用参数
    else:#元数据优先
        元插件=串字段(元,'pluginId')#元数据插件
        元包=串字段(元,'packageId')#元数据包
        插件=参数插件 if 元插件 is None else 元插件#空则回退
        包=参数包 if 元包 is None else 元包#空则回退
    if 模式原文=='run' or 模式原文=='update':#两种模式
        模式=模式原文#留下
    else:#别的值
        模式=None#不认
    return {
        'pluginId':插件,#插件
        'packageId':包,#包
        'pluginRunId':None if 元 is None else 串字段(元,'pluginRunId'),#这次激活
        'mode':模式,#模式
        'seq':块.get('seq') if 已落定 else None,#日志序号
        'output':输出,#结果
        'errorSummary':首行(输出) if 状态=='error' and 输出 is not None else None,#错误首行
        'state':状态,#状态
    }

def 动作卡片(块):
    '从停止或移除调用做出一张卡片'
    已落定='kind' in 块#是否已有结果
    原文=参数原文(块,已落定)#参数原文
    参数=解析参数(原文)#参数对象
    状态=调用状态(块)#调用状态
    输出=结果文本(块) if 已落定 else None#结果文本
    插件=None#插件
    if 参数 is not None:#有参数
        插件=串字段(参数,'pluginId')#pluginId
        if 插件 is None:#有的调用写 id
            插件=串字段(参数,'id')#id
    return {
        'pluginId':插件,#插件
        'output':输出,#结果
        'errorSummary':首行(输出) if 状态=='error' and 输出 is not None else None,#错误首行
        'state':状态,#状态
    }
