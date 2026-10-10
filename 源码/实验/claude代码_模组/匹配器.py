'事件名图案和字段匹配器。事件名保持 Claude Code 原文'
import re#字段正则
__all__=['引擎事件','已知事件','是事件图案','事件命中','匹配器命中','描述匹配器']

引擎事件=frozenset([
    'tool.call','tool.check','tool.describe',
    'prompt.submit','prompt.fill','prompt.suggest','prompt.edit','prompt.compose','prompt.section',
    'prompt.context','prompt.attachment','skill.prompt','attribution.text',
    'command.run','command.describe','config.set','config.describe',
    'turn.start','turn.step','turn.complete',
    'session.start','session.end','session.compact','session.receive','session.send','session.append',
    'session.attach','session.detach','session.measure',
    'agent.offer','agent.spawn',
    'ui.render','ui.resolve','ui.press','ui.input','ui.select','ui.focus','ui.scroll','ui.close','ui.message',
    'plugin.register','engine.create',
    'telemetry.log','telemetry.mark',
])#引擎自己引发的事件

已知事件=frozenset(list(引擎事件)+[
    'ui.log','ui.toast','ui.status','ui.notice','ui.invalidate','ui.open','ui.panes','ui.blit','ui.ask','ui.copy',
    'command.register','command.list',
    'tool.register','tool.list',
    'agent.register','agent.list',
    'model.complete','model.fork','model.classify',
    'prompt.read',
    'turn.abort',
    'session.messages','session.cwd','session.root','session.model','session.turns','session.id','session.repo',
    'session.surface','session.surfaces','session.usage','session.version','session.authorize',
    'config.list',
    'settings.read',
    'env.get','env.set',
    'fs.read','fs.write','fs.list','fs.exists','fs.stat','fs.ancestors',
    'store.get','store.set','store.delete','store.keys',
    'state.get','state.set',
    'clock.now','clock.sleep','clock.after','clock.every',
    'http.fetch',
    'process.run','process.spawn',
    'mcp.call','mcp.connect',
    'audio.play','audio.speak',
])#on 接受的全部事件名

def 是事件图案(图案):
    '精确事件名、*，或某个已知命名空间的 .*'
    if 图案=='*':#全部
        return True#接受
    if 图案.endswith('.*'):#命名空间通配
        命名空间=图案[:-2]#去掉 .*
        if 命名空间=='':#空命名空间
            return False#不接受
        前缀=命名空间+'.'#命名空间点
        for 事件 in 已知事件:#必须真有这个命名空间
            if 事件.startswith(前缀):#有
                return True#接受
        return False#没有这个命名空间
    return 图案 in 已知事件#精确名

def 事件命中(图案,事件):
    '* 选中除 telemetry. 以外的事件。telemetry 只能按名或 telemetry.* 挂上'
    if 图案==事件:#精确
        return True#命中
    if 图案=='*':#全选
        return not 事件.startswith('telemetry.')#遥测除外
    return 图案.endswith('.*') and 事件.startswith(图案[:-1])#命名空间前缀，含点

def 严格相等(甲,乙):
    '对齐 ===：布尔不跟数字混，整数不跟浮点混'
    if isinstance(甲,bool) or isinstance(乙,bool):#布尔
        return type(甲) is bool and type(乙) is bool and 甲==乙#只有布尔相等
    if isinstance(甲,(int,float)) and isinstance(乙,(int,float)):#数字
        return type(甲) is type(乙) and 甲==乙#类型也要一致
    return 甲==乙#其余按值

def 值命中(期望,实际):
    '标量按相等，列表按成员，正则按测试。每次从开头测'
    if isinstance(期望,re.Pattern):#正则
        if not isinstance(实际,(str,int,float)) or isinstance(实际,bool):#只测字符串和数字
            return False#类型不对
        return 期望.search(str(实际)) is not None#从开头搜索
    if isinstance(期望,(list,tuple)):#成员列表
        for 候选 in 期望:#逐个
            if 严格相等(候选,实际):#命中
                return True#在列表里
        return False#不在
    return 严格相等(期望,实际)#标量相等

def 匹配器命中(匹配器,输入):
    '每个字段都接受事件同名字段时，钩子才跑'
    if not isinstance(输入,dict):#没有字段
        return False#不跑
    for 字段,期望 in 匹配器.items():#逐字段
        实际=输入[字段] if 字段 in 输入 else None#缺席当 None
        if not 值命中(期望,实际):#这一字段不行
            return False#整份不命中
    return True#全部字段都过

def 描述正则(表达式):
    '打印成 /图案/旗标'
    旗=''#旗标
    if 表达式.flags & re.IGNORECASE:#忽略大小写
        旗+='i'#i
    if 表达式.flags & re.MULTILINE:#多行
        旗+='m'#m
    if 表达式.flags & re.DOTALL:#点匹配换行
        旗+='s'#s
    return '/'+表达式.pattern+'/'+旗#源码形式

def 描述匹配器(匹配器):
    '按 claude plugin validate 的样子打印匹配器'
    if 匹配器 is None:#没有匹配器
        return ''#空
    字段们=[]#一段一段
    for 字段,值 in 匹配器.items():#逐字段
        if isinstance(值,re.Pattern):#正则
            渲染=描述正则(值)#源码
        elif isinstance(值,(list,tuple)):#列表
            渲染='|'.join(str(项) for 项 in 值)#用竖线连
        else:#标量
            渲染=str(值)#文本
        字段们.append(字段+'='+渲染)#字段=值
    return '{'+','.join(字段们)+'}'#花括号
