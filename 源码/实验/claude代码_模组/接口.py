'钩子收到的 $。除了 plugin 和 ui.resolve，每个方法都是更早的模组能看见的事件'
from ...模型后端.llm.调用配置 import 冻结映射#已实现的命名空间禁止改方法
from .元素 import 界面元素#ui.resolve 不是事件
from .值 import 消息#发射失败的文案

__all__=['创建模组接口']

方法命名空间=frozenset([
    'ui','command','tool','prompt','session','state','store','clock','fs','process','http','env',
    'model','agent','config','settings','mcp','audio','telemetry','turn',
])#Claude Code 的 $ 有这些命名空间。plugin 是事实，不在这里

def 冻结命名空间(方法表):
    '方法表冻成不能替换的对象'
    方法表.__class__=冻结映射#禁止改方法
    return 方法表#原对象

class 未实现成员:
    '命名空间里没实现的成员。调用时说明缺的是哪一个'
    def __init__(自身,命名空间名,已有,模组名):
        '已有是实现了的方法对象，没有则 None'
        自身._命名空间名=命名空间名#ui、fs 这类
        自身._已有=已有#已实现的方法
        自身._模组名=模组名#错误里点名
        自身._拒绝={}#同一个缺成员始终是同一个函数

    def __getattr__(自身,成员):
        '已实现的原样给出；其余是一个调用就失败的函数'
        if 成员.startswith('_'):#内部
            raise AttributeError(成员)#没有
        已有=自身._已有#已实现
        if isinstance(已有,dict) and 成员 in 已有:#这个方法有实现
            return 已有[成员]#原方法
        if 成员 in 自身._拒绝:#已经做过
            return 自身._拒绝[成员]#同一个函数
        def 拒绝(*位置参数,**关键字参数):
            '这个宿主没有该成员'
            raise RuntimeError(自身._模组名+'：没有 '+自身._命名空间名+'.'+成员+' 的实现')#点名缺口
        自身._拒绝[成员]=拒绝#记下
        return 拒绝#调用才失败

class 模组美元:
    '$。读方法命名空间时包上一层，缺成员不会变成 AttributeError'
    def __init__(自身,已服务,模组名):
        '已服务是这个宿主实现了的部分'
        自身._已服务=已服务#实现
        自身._模组名=模组名#错误里点名
        自身._缓存={}#每个命名空间包一次

    def __getattr__(自身,名):
        'plugin 原样；方法命名空间包上未实现成员'
        if 名.startswith('_'):#内部
            raise AttributeError(名)#没有
        if 名 not in 方法命名空间:#不是方法命名空间
            return getattr(自身._已服务,名)#plugin 等
        if 名 not in 自身._缓存:#还没包
            基=getattr(自身._已服务,名,None)#已实现的命名空间
            自身._缓存[名]=未实现成员(名,基,自身._模组名)#包上
        return 自身._缓存[名]#包装

    def __setattr__(自身,名,值):
        '只允许写内部字段'
        if not 名.startswith('_'):#模组不能改 $
            raise AttributeError(名)#只读
        object.__setattr__(自身,名,值)#内部

def 创建模组接口(绑定):
    '为一次钩子调用做出 $。等待 $ 时暂停预算，$.clock.sleep 除外'
    模组=绑定['mod']#调用方模组
    时钟=绑定['clock']#钩子外面则没有
    定时器=绑定['timers']#这个模组在这次会话里的定时器

    def 调用(操作,输入):
        '引发事件并等到答案。等待期间不计这条钩子的预算'
        if 时钟 is not None:#在钩子里
            时钟.暂停()#停表
        try:#无论成败都恢复
            return 绑定['invoke'](操作,输入)#引擎回答的值
        finally:#恢复
            if 时钟 is not None:#在钩子里
                时钟.恢复()#继续计

    def 发射(操作,输入):
        '日志一类调用。失败记一行，不抛回钩子'
        try:#同步做完
            调用(操作,输入)#走链
        except Exception as 错误:#失败
            绑定['report'](模组['name']+'：$.'+操作+' 失败：'+消息(错误))#一行

    插件=冻结命名空间({'name':模组['name'],'root':模组['root']})#事实

    def 日志(文本,选项=None):
        '$.ui.log'
        去向='transcript'#默认写进记录
        if isinstance(选项,dict) and 'to' in 选项 and 选项['to'] is not None:#指定了去向
            去向=选项['to']#用指定的
        发射('ui.log',{'text':文本,'to':去向})#不等待失败

    def 提示条(文本,选项=None):
        '$.ui.toast'
        载荷={'text':文本}#文本
        if isinstance(选项,dict) and 'timeoutMs' in 选项 and 选项['timeoutMs'] is not None:#有超时
            载荷['timeoutMs']=选项['timeoutMs']#带上
        发射('ui.toast',载荷)#发射

    def 状态(文本):
        '$.ui.status'
        发射('ui.status',{'text':文本})#文本可以是 None

    def 作废(事件):
        '$.ui.invalidate'
        发射('ui.invalidate',{'event':事件})#请求重画

    def 打开(窗格):
        '$.ui.open'
        return 调用('ui.open',窗格)#这个宿主不放窗格

    def 关闭(窗格):
        '$.ui.close'
        return 调用('ui.close',{'id':窗格['id'],'origin':'plugin'})#带来源

    def 窗格列表():
        '$.ui.panes'
        return 调用('ui.panes',{})#空列表

    def 询问(问题,选项=None):
        '$.ui.ask。选项可以是字符串列表，或带 options 的对象'
        if isinstance(选项,(list,tuple)):#字符串列表
            归一={'options':list(选项)}#收成对象
        elif isinstance(选项,dict):#已经是对象
            归一=dict(选项)#拷贝
        else:#没给
            归一={}#空
        载荷={'question':问题}#问题
        载荷.update(归一)#带上选项
        return 调用('ui.ask',载荷)#人的回答

    def 解析(事件=None):
        '元素构造器。不是事件'
        return 界面元素()#Box、Text、Button

    界面=冻结命名空间({
        'log':日志,'toast':提示条,'status':状态,'invalidate':作废,
        'open':打开,'close':关闭,'panes':窗格列表,'ask':询问,'resolve':解析,
    })#ui

    def 登记命令(命令):
        '$.command.register'
        return 调用('command.register',命令)#登记

    def 运行命令(输入):
        '$.command.run'
        参数=输入['args'] if isinstance(输入,dict) and 'args' in 输入 and 输入['args'] is not None else ''#缺席当空串
        return 调用('command.run',{'command':输入['command'],'args':参数})#运行

    def 列出命令():
        '$.command.list'
        return 调用('command.list',{})#列表

    命令=冻结命名空间({'register':登记命令,'run':运行命令,'list':列出命令})#command

    def 登记工具(工具):
        '$.tool.register'
        return 调用('tool.register',工具)#登记

    def 调用工具(输入):
        '$.tool.call'
        return 调用('tool.call',输入)#参数和 tool 在同一层

    def 列出工具():
        '$.tool.list'
        return 调用('tool.list',{})#列表

    工具=冻结命名空间({'register':登记工具,'call':调用工具,'list':列出工具})#tool

    def 提交提示(输入):
        '$.prompt.submit'
        return 调用('prompt.submit',{'text':输入['text'],'asUser':输入.get('asUser') is True})#是否当成用户自己的话

    提示=冻结命名空间({'submit':提交提示})#prompt

    def 会话号():
        '$.session.id'
        return 调用('session.id',{})#会话号

    def 工作目录():
        '$.session.cwd'
        return 调用('session.cwd',{})#目录

    def 根目录():
        '$.session.root'
        return 调用('session.root',{})#根

    def 模型():
        '$.session.model'
        return 调用('session.model',{})#模型

    def 回合数():
        '$.session.turns'
        return 调用('session.turns',{})#回合

    def 消息列表():
        '$.session.messages'
        return 调用('session.messages',{})#消息

    def 用量():
        '$.session.usage'
        return 调用('session.usage',{})#用量

    def 版本():
        '$.session.version'
        return 调用('session.version',{})#接口版本

    会话=冻结命名空间({
        'id':会话号,'cwd':工作目录,'root':根目录,'model':模型,'turns':回合数,
        'messages':消息列表,'usage':用量,'version':版本,
    })#session

    def 读状态(引用):
        '$.state.get'
        return 调用('state.get',{'plugin':引用['plugin'],'key':引用['key']})#值

    def 写状态(引用,值):
        '$.state.set'
        return 调用('state.set',{'plugin':引用['plugin'],'key':引用['key'],'value':值})#写入

    状态空间=冻结命名空间({'get':读状态,'set':写状态})#state

    def 读存储(键):
        '$.store.get'
        return 调用('store.get',{'key':键})#值

    def 写存储(键,值):
        '$.store.set'
        return 调用('store.set',{'key':键,'value':值})#写入

    def 删存储(键):
        '$.store.delete'
        return 调用('store.delete',{'key':键})#删除

    def 存储键():
        '$.store.keys'
        return 调用('store.keys',{})#键

    存储=冻结命名空间({'get':读存储,'set':写存储,'delete':删存储,'keys':存储键})#store

    def 现在():
        '$.clock.now'
        return 调用('clock.now',{})#毫秒

    def 睡眠(毫秒):
        '$.clock.sleep 算作钩子自己的时间，所以不停表'
        return 绑定['invoke']('clock.sleep',{'ms':毫秒})#直接引发

    def 之后(毫秒,函数):
        '$.clock.after'
        return 定时器.之后(毫秒,函数)#可取消

    def 每隔(毫秒,函数):
        '$.clock.every'
        return 定时器.每隔(毫秒,函数)#可取消

    时钟空间=冻结命名空间({'now':现在,'sleep':睡眠,'after':之后,'every':每隔})#clock

    def 读文件(路径):
        '$.fs.read'
        return 调用('fs.read',{'path':路径,'as':'text'})#文本

    def 写文件(路径,文本):
        '$.fs.write'
        return 调用('fs.write',{'path':路径,'text':文本})#写入

    def 列文件(路径=None):
        '$.fs.list'
        return 调用('fs.list',{'path':'.' if 路径 is None else 路径})#缺席是当前目录

    def 存在(路径):
        '$.fs.exists'
        return 调用('fs.exists',{'path':路径})#是否存在

    def 文件状态(路径):
        '$.fs.stat'
        return 调用('fs.stat',{'path':路径,'resolve':True})#跟随链接

    文件=冻结命名空间({'read':读文件,'write':写文件,'list':列文件,'exists':存在,'stat':文件状态})#fs

    def 运行进程(参数列表,初始=None):
        '$.process.run'
        载荷={'argv':参数列表}#参数
        if 初始 is not None:#有选项
            载荷['init']=初始#带上
        return 调用('process.run',载荷)#跑完

    进程=冻结命名空间({'run':运行进程})#process

    def 请求(地址,初始=None):
        '$.http.fetch'
        载荷={'url':地址}#地址
        if 初始 is not None:#有选项
            载荷['init']=初始#带上
        return 调用('http.fetch',载荷)#响应

    网络=冻结命名空间({'fetch':请求})#http

    def 读环境(名字):
        '$.env.get'
        return 调用('env.get',{'name':名字})#值或 None

    def 写环境(名字,值):
        '$.env.set'
        载荷={'name':名字}#名字
        if 值 is not None:#删除时不带 value
            载荷['value']=值#新值
        return 调用('env.set',载荷)#写入

    环境=冻结命名空间({'get':读环境,'set':写环境})#env

    已服务=type('已服务',(),{})()#plugin 与各命名空间
    已服务.plugin=插件#事实
    已服务.ui=界面#界面
    已服务.command=命令#命令
    已服务.tool=工具#工具
    已服务.prompt=提示#提示
    已服务.session=会话#会话
    已服务.state=状态空间#状态
    已服务.store=存储#存储
    已服务.clock=时钟空间#时钟
    已服务.fs=文件#文件
    已服务.process=进程#进程
    已服务.http=网络#网络
    已服务.env=环境#环境
    return 模组美元(已服务,模组['name'])#$
