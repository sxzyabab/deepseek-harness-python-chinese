from ....依赖.cordis.服务 import 服务
from ....基础设施.通用工具 import 获取内部数据
from ....工具.值 import 带值弱映射
from ...ui_基础界面组件.按名排序 import 按名排序
from .文案 import 中文
from .呈现 import 分区行名,宿主面
from .解析 import 第一方命令名
from .目录 import 命令目录
from .弹出层 import 等返回,弹出选定控制器

__all__=['命令界面运行时']

依赖=['inputTriggers','sessions','remote','remote.commands']

def 空白下标(文本):
    '第一个空白的下标。没有则 -1'
    序=0
    while 序<len(文本):
        if 文本[序].isspace():
            return 序
        序+=1
    return -1

def 会话标识(会话):
    '触发源传来的投影是 dict，会话面是对象'
    if isinstance(会话,dict):
        return 会话['sessionId']
    return 会话.sessionId

class 命令界面运行时(服务):
    '斜杠命令面：按会话的目录、客户端贡献、宿主装饰，以及每场会话的弹出'
    def __init__(自身,上下文,配置=None):
        '以 commandUi 挂上，并登记斜杠源'
        super().__init__(上下文,'commandUi')
        文案服务=上下文.获取服务('locale')
        if 文案服务 is None:
            raise Exception('ui-commands: locale service unavailable')
        自身.贡献={}
        自身.装饰={}
        自身.弹出=带值弱映射()
        def 拉目录(会话标识值):
            '向这场会话的宿主要命令目录。子智能体给空表'
            会话面=自身.会话面()
            if 会话面.subagentAddress(会话标识值) is not None:
                return []
            if 会话面.binding(会话标识值) is None:
                raise Exception('command catalog requires a retained session "'+str(会话标识值)+'"')
            def 读取(引用):
                '历史已经打开才列命令'
                状态=引用.binding['session'].getSnapshot()
                if 状态['openState']!='open':
                    if 状态.get('openError') is not None:
                        raise 状态['openError']
                    raise Exception('session "'+str(会话标识值)+'" is not open')
                结果=等返回(上下文.remote.commands.list(会话标识值))
                if 结果['ok'] is not True:
                    错误体=结果['error']
                    raise Exception('command.list failed: '+str(错误体['code'])+': '+str(错误体['message']))
                return 结果['value']
            return 会话面.using(会话标识值,{'source':'commandCatalog'},读取)
        自身.目录=命令目录(拉目录)
        触发=上下文.获取服务('inputTriggers')
        if 触发 is None:
            raise Exception('ui-commands: slash service unavailable')
        def 登记源():
            '登记 / 命令源'
            def 预热(会话):
                '会话作用域出现时预热目录'
                自身.目录.预热(会话标识(会话))
            return 触发.registerSource({
                'trigger':'/',
                'name':'command',
                'candidates':自身.候选,
                'onPick':自身.派发,
                'matchSpace':自身.匹配空格,
                'matchClaim':自身.匹配认领,
                'matchEnter':自身.匹配回车,
                'warm':预热,
            })
        上下文.副作用(登记源,'command: slash source')
        def 订目录变更():
            '宿主目录变了就软失效'
            def 目录变更(*位置参数):
                '重拉已碰过的会话'
                自身.目录.全部失效()
            return getattr(上下文.remote,'$on')('commands/change',目录变更)
        上下文.副作用(订目录变更,'command: commands/change')
        def 订预设():
            '这场会话的预设变了就丢掉旧目录'
            def 预设选定(标识,*位置参数):
                '重置这一场'
                自身.目录.重置会话(标识)
            return getattr(上下文.remote,'$on')('agent-preset/selected',预设选定)
        上下文.副作用(订预设,'command: agent-preset/selected')
        def 连接重置(*位置参数):
            '重连后丢掉全部快照'
            自身.目录.重置已连接()
        上下文.监听('connection/reset',连接重置)

    def 会话面(自身):
        '取会话服务'
        会话=自身.ctx.获取服务('sessions')
        if 会话 is None:
            raise Exception('ui-commands: sessions service unavailable')
        return 会话

    def register(自身,贡献):
        '登记一条客户端命令。重名抛出'
        名=贡献['name']
        def 挂():
            '写进贡献表，拆除时摘掉'
            if 名 in 自身.贡献:
                raise Exception('ui-commands: duplicate contribution for /'+名)
            自身.贡献[名]=贡献
            def 摘():
                '摘掉这条贡献'
                自身.贡献.pop(名,None)
            return 摘
        拆=自身.ctx.副作用(挂,'command.register()')
        def 拆贡献():
            '拆掉这次登记'
            拆()
        return 拆贡献

    def decorate(自身,装饰):
        '给一条宿主命令挂上裸调用界面。重名抛出'
        名=装饰['name']
        def 挂():
            '写进装饰表，拆除时摘掉'
            if 名 in 自身.装饰:
                raise Exception('ui-commands: duplicate decoration for /'+名)
            自身.装饰[名]=装饰
            def 摘():
                '摘掉这条装饰'
                自身.装饰.pop(名,None)
            return 摘
        拆=自身.ctx.副作用(挂,'command.decorate()')
        def 拆装饰():
            '拆掉这次装饰'
            拆()
        return 拆装饰

    def dismiss(自身,名):
        '关掉这个命令已经打开的弹出，草稿留着，焦点还给编写器'
        for 弹出 in 自身.弹出.values:
            if 弹出.state.getSnapshot()['command']==名:
                弹出.dismiss({'focusComposer':True})

    def popupFor(自身,作用域):
        '这场会话的弹出控制器。作用域必须还指着保留中的那一代'
        会话面=自身.会话面()
        会话=会话面.sessionOf(作用域)
        绑定=None if 会话 is None else 会话面.binding(会话.sessionId)
        if 绑定 is None or 绑定['session'] is not 会话:
            raise Exception('command.popupFor requires a retained Session scope')
        键=绑定['ctx']
        已有=自身.弹出.get(键)
        if 已有 is not None:
            return 已有
        def 消费(片段):
            '选中成功后消费打开时的令牌'
            if 片段['via']=='menu':
                守卫={'kind':'span','span':片段['span']}
            else:
                守卫={'kind':'bare-token','token':片段['token']}
            return 键.首个结果(键,'slash/input-consume-token',{'guard':守卫}) is True
        def 聚焦():
            '把焦点还给这场会话的编写器'
            对话=键.获取服务('conversation')
            if 对话 is None:
                return
            对话.input.按作用域取门面(键).focus()
        控制器=弹出选定控制器({'consume':消费,'focusComposer':聚焦})
        自身.弹出.set(键,控制器)
        def 拆会话():
            '会话作用域拆除时丢掉控制器'
            def 清():
                '取消在途弹出并从弱表摘掉'
                控制器.dispose()
                自身.弹出.delete(键)
            return 清
        键.副作用(拆会话,'command: session popup')
        return 控制器

    def 候选(自身,会话,请求):
        '宿主目录加上还能用的贡献。空查询按添加、指令分区'
        表=自身.目录.确保就绪(会话标识(会话),请求['signal'])
        行=[]
        已见=set()
        for 项 in 表:
            已见.add(项['name'])
            行项={'name':项['name']}
            方名=第一方命令名(项)
            面=None if 方名 is None else 宿主面.get(方名)
            if 面 is None:
                if 'description' in 项:
                    行项['description']=项['description']
            else:
                行项['label']=中文[面['label']]
                行项['description']=中文[面['description']]
                if 面['icon'] is not None:
                    行项['icon']=面['icon']
            if 'input' in 项 and 项['input'] is not None and 'hint' in 项['input']:
                行项['hint']=项['input']['hint']
            行.append(行项)
        for 贡献 in 自身.贡献.values():
            if not 贡献['available'](会话):
                continue
            if 贡献['name'] in 已见:
                raise Exception('ui-commands: contribution /'+贡献['name']+' collides with a host command')
            行项={'name':贡献['name']}
            if 'label' in 贡献 and 贡献['label'] is not None:
                行项['label']=贡献['label']()
            if 'description' in 贡献 and 贡献['description'] is not None:
                行项['description']=贡献['description']()
            if 'icon' in 贡献 and 贡献['icon'] is not None:
                行项['icon']=贡献['icon']
            行.append(行项)
        可见=[]
        for 项 in 行:
            提示=项['hint'] if 'hint' in 项 else None
            if 请求['position']=='leading' or 提示 is None:
                可见.append(项)
        if 请求['query']!='':
            return 按名排序(可见,请求['query'])
        已列=set(分区行名['add'])|set(分区行名['commands'])
        按名={}
        for 项 in 可见:
            按名[项['name']]=项
        def 挑出(名表):
            '按分区名单挑出仍可见的行'
            选出=[]
            for 名 in 名表:
                if 名 in 按名:
                    选出.append(按名[名])
            return 选出
        添加=[]
        for 项 in 挑出(分区行名['add']):
            拷=dict(项)
            拷['section']='添加'
            添加.append(拷)
        指令=[]
        for 项 in 挑出(分区行名['commands']):
            拷=dict(项)
            拷['section']='指令'
            指令.append(拷)
        for 项 in 可见:
            if 项['name'] not in 已列:
                拷=dict(项)
                拷['section']='指令'
                指令.append(拷)
        return 添加+指令

    def 派发(自身,点选):
        '菜单点选：贡献或装饰走弹出或动作，宿主带参数的认领，裸宿主命令直接执行'
        名=点选['candidate']['name']
        会话=点选['session']
        片段={'via':'menu','span':点选['span']}
        贡献=自身.贡献.get(名)
        if 贡献 is not None and 贡献['available'](会话):
            自身.调用(名,贡献['ui'],会话,片段)
            return 'handled'
        描=自身.目录.解析(会话标识(会话),名)
        if 描 is None:
            return None
        装饰=自身.装饰.get(名)
        if 装饰 is not None and 装饰['available'](会话):
            自身.调用(名,装饰['ui'],会话,片段)
            return 'handled'
        if 'input' in 描 and 描['input'] is not None:
            方名=第一方命令名(描)
            展示=描['name'] if 方名 is None else 中文['token.'+方名]
            return {'claim':自身.前缀认领(描,会话,展示)}
        自身.经片段消费(会话标识(会话),片段)
        自身.分离执行(描,会话,'/'+名)
        return 'handled'

    def 匹配空格(自身,会话,令牌):
        '空格只让宿主的带参数命令认领'
        认领=自身.认领于(会话,令牌)
        if 认领 is None:
            return None
        return {'claim':认领}

    def 匹配认领(自身,会话,令牌,信号):
        '目录就绪后再回答空格那一列。只解析，不执行'
        自身.目录.确保就绪(会话标识(会话),信号)
        return 自身.认领于(会话,令牌)

    def 认领于(自身,会话,令牌):
        '这个令牌如果是宿主的带参数命令，就交出认领'
        if 令牌.startswith('/') is False:
            return None
        键入=令牌[1:]
        if 键入 in 自身.贡献:
            return None
        描=自身.目录.解析(会话标识(会话),键入)
        if 描 is None or 'input' not in 描 or 描['input'] is None:
            return None
        return 自身.前缀认领(描,会话,键入)

    def 匹配回车(自身,会话,行,信号,信封):
        '回车：贡献和装饰只认裸令牌，带参数的宿主命令认领，其余裸命令直接执行'
        修剪=行.strip()
        if 修剪.startswith('/') is False:
            return None
        空=空白下标(修剪)
        令牌=修剪 if 空==-1 else 修剪[:空]
        裸=空==-1
        键入名=令牌[1:]
        if 键入名=='':
            return None
        def 拒附件():
            '这条命令不收附件'
            raise Exception('/'+键入名+' 不接受附件，请先移除附件')
        贡献=自身.贡献.get(键入名)
        if 贡献 is not None and 贡献['available'](会话):
            if 裸 is False:
                return None
            if 信封['attachments']>0 and 贡献['ui']['kind']!='action':
                拒附件()
            自身.调用(键入名,贡献['ui'],会话,{'via':'enter','token':令牌})
            return 'handled'
        自身.目录.确保就绪(会话标识(会话),信号)
        描=自身.目录.解析(会话标识(会话),键入名)
        if 描 is None:
            return None
        名=描['name']
        规范='/'+名+修剪[len(令牌):]
        if 裸 is True:
            装饰=自身.装饰.get(名)
            if 装饰 is not None and 装饰['available'](会话):
                if 信封['attachments']>0 and 装饰['ui']['kind']!='action':
                    拒附件()
                自身.调用(名,装饰['ui'],会话,{'via':'enter','token':令牌})
                return 'handled'
        if 'input' in 描 and 描['input'] is not None:
            if 信封['attachments']>0 and 描['input'].get('attachments') is not True:
                拒附件()
            return {'claim':自身.前缀认领(描,会话,令牌[1:])}
        if 裸 is False:
            return None
        if 信封['attachments']>0:
            拒附件()
        自身.经片段消费(会话标识(会话),{'via':'enter','token':令牌})
        自身.分离执行(描,会话,规范)
        return 'handled'

    def 调用(自身,名,界面,会话,片段):
        '动作先消费令牌再跑。弹出则打开这场会话的壳'
        if 界面['kind']=='action':
            自身.经片段消费(会话标识(会话),片段)
            界面['run'](会话)
            return
        作用=自身.作用域于(会话标识(会话))
        if 作用 is None:
            return
        自身.popupFor(作用).open(名,界面,会话,片段)

    def 前缀认领(自身,描,会话,展示):
        '草稿里留展示拼写。提交时换成目录名'
        令牌='/'+展示+' '
        行='/'+描['name']+' '
        认领={'name':描['name'],'token':令牌}
        输入=描['input'] if 'input' in 描 else None
        if 输入 is not None and 'hint' in 输入:
            认领['hint']=输入['hint']
        if 输入 is not None and 输入.get('attachments') is True:
            认领['attachments']=True
        def 提交(参数,作用域=None,附件=()):
            '把参数拼到目录名后面再执行'
            return 自身.执行(会话,行+参数,附件)
        认领['submit']=提交
        return 认领

    def 执行(自身,会话,行,附件=()):
        '向这场会话执行一行。拒绝抛出。未匹配或处理失败把草稿留在编写器'
        标识=会话标识(会话)
        结果=等返回(自身.ctx.remote.commands.execute(标识,行,附件))
        if 结果['ok'] is not True:
            错误体=结果['error']
            raise Exception('command.execute failed: '+str(错误体['code'])+': '+str(错误体['message']))
        if 结果['value'] is None:
            return {'kind':'error','text':'unknown or malformed command: '+行}
        修剪=行.strip()
        分隔=空白下标(修剪)
        段=修剪 if 分隔==-1 else 修剪[:分隔]
        自身.通知已执行(标识,段[1:],结果['value']['result'])
        if len(附件)>0 and 结果['value']['result']['kind']=='error':
            return {'kind':'error','text':结果['value']['result']['text']}
        return {'kind':'success'}

    def 通知已执行(自身,会话标识值,名,结果):
        '发出本地回执。单个监听失败不改变这次接纳'
        参数列表=['command/executed',会话标识值,名,结果]
        事件总线=自身.ctx.事件
        解析监听=获取内部数据(事件总线,'解析监听器')
        for 监听 in 解析监听(事件总线,'emit',参数列表):
            try:
                返回=监听(会话标识值,名,结果)
                if 返回 is not None and callable(getattr(返回,'then',None)):
                    def 失败(错误,命令名=名):
                        '异步监听失败只记警告'
                        自身.警告监听失败(命令名,错误)
                    返回.then(None,失败)
            except Exception as 错误:
                自身.警告监听失败(名,错误)

    def 警告监听失败(自身,名,错误):
        '记下一条 command/executed 监听失败'
        自身.ctx.日志.警告('client command: a command/executed listener for "%s" failed',名)
        自身.ctx.日志.警告(错误)

    def 分离执行(自身,描,会话,行):
        '裸命令在后台执行。只有没进处理函数的接纳失败才提示编写器'
        try:
            结局=自身.执行(会话,行)
        except Exception as 错误:
            自身.提示(会话标识(会话),'error',str(错误))
            return
        if 结局['kind']=='error':
            if 'text' in 结局 and 结局['text'] is not None:
                文=结局['text']
            else:
                文='/'+描['name']+' failed'
            自身.提示(会话标识(会话),'error',文)

    def 经片段消费(自身,标识,片段):
        '让这场会话消费打开时的令牌'
        作用=自身.作用域于(标识)
        if 作用 is None:
            return
        if 片段['via']=='menu':
            守卫={'kind':'span','span':片段['span']}
        else:
            守卫={'kind':'bare-token','token':片段['token']}
        作用.首个结果(作用,'slash/input-consume-token',{'guard':守卫})

    def 提示(自身,标识,级别,文本):
        '把接纳失败送到这场会话的编写器'
        作用=自身.作用域于(标识)
        if 作用 is None:
            return
        对话=作用.获取服务('conversation')
        if 对话 is None:
            return
        对话.input.按作用域取门面(作用).notify(级别,文本)

    def 作用域于(自身,标识):
        '会话标识换成作用域。没有则 None'
        return 自身.会话面().scope(标识)

命令界面运行时.inject=依赖
inject=依赖
