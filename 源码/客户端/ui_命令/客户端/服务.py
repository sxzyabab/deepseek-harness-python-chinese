from ...ui_基础界面组件.按名排序 import 按名排序#名与标签排序
from .约定 import 命令错误#本包异常
from .目录 import 命令目录#按会话键目录
from .呈现 import 内置行面,分区行#内置行面与分区
from .解析 import 认领令牌#菜单点选拼写

__all__=['命令UI运行时']#仅中文公开名

def 已提交命令名(行):
    """从宿主确认已执行的一行取出命令名（去前导斜杠）。"""
    修剪=行.strip()#去空白
    空=None#空白下标
    序=0#扫描
    while 序<len(修剪):#找空白
        if 修剪[序].isspace():#空白
            空=序#记
            break#止
        序+=1#前进
    段=修剪 if 空 is None else 修剪[:空]#令牌
    return 段[1:] if 段.startswith('/') else 段#去斜杠

class 弹出选定控制器:#每会话弹出控制器
    """consume / focusComposer / open / dispose。完整选项壳在 popup.ts。"""
    def __init__(自身,消费,聚焦):
        """记下消费与聚焦回调。"""
        自身.consume=消费#消费令牌
        自身.focusComposer=聚焦#聚焦
        自身.已开=False#是否打开
        自身.命令=None#当前命令名

    def open(自身,名,规格,会话,片段):
        """打开弹出；记下打开时载荷。"""
        自身.已开=True#开
        自身.命令=名#名
        自身.规格=规格#规格
        自身.会话=会话#会话
        自身.片段=片段#片段

    def dispose(自身):
        """拆除。"""
        自身.已开=False#关
        自身.命令=None#清

    def dismiss(自身):
        """关掉弹出，不消费草稿。"""
        自身.已开=False#关
        自身.命令=None#清

class 命令UI运行时:#CommandUiRuntime
    """命令面：目录 + 「/」源 + 贡献/装饰 + 每会话弹出。"""
    inject=['inputTriggers','sessions','remote','remote.commands']#所需服务

    def __init__(自身,上下文):
        """挂上 commandUi 并登记斜杠源。"""
        自身.ctx=上下文#上下文
        上下文.provide('commandUi',自身)#提供
        文案=上下文.get('locale')#文案
        if 文案 is None:#无
            raise 命令错误('ui-commands: locale 服务不可用')#失败
        自身.t=文案.bind('command')#翻译
        自身.贡献={}#名 → 贡献 dict
        自身.装饰={}#名 → 装饰 dict
        自身.弹出={}#sessionId → 控制器
        自身.聚焦钩={}#sessionId → focus
        def 拉目录(会话标识):
            """RPC 列命令；子智能体会话空表。"""
            if 自身.sessions().subagentAddress(会话标识) is not None:#子
                return []#空
            结果=上下文.remote.commands.list(会话标识)#列
            if 结果['ok'] is not True:#失败
                错误体=结果['error']#错误体
                raise 命令错误('command.list 失败: '+str(错误体['code'])+': '+str(错误体['message']))#抛
            return 结果['value']#表
        自身.目录=命令目录(拉目录)#目录
        触发=上下文.get('inputTriggers')#斜杠
        if 触发 is None:#无
            raise 命令错误('ui-commands: 斜杠服务不可用')#失败
        def 登记源():
            """登记 '/' 源。"""
            def 预热(会话):
                """预热该会话目录。会话为 dict。"""
                自身.目录.warm(会话['sessionId'])#预热
            return 触发.registerSource({#源
                'trigger':'/',#触发
                'name':'command',#名
                'candidates':自身.候选,#候选
                'onPick':自身.派发,#点选
                'matchSpace':自身.匹配空格,#空格
                'matchEnter':自身.匹配回车,#回车
                'warm':预热,#预热
            })#源结束
        上下文.副作用(登记源,'command: slash source')#挂源
        def 目录变更(*位置参数):
            """宿主目录变更。"""
            自身.目录.invalidateAll()#软失效
        def 预设选定(标识,*位置参数):
            """智能体预设切换。"""
            自身.目录.resetSession(标识)#重置该会话
        def 连接重置(*位置参数):
            """重连硬重置。"""
            自身.目录.resetConnected()#重置已连接
        上下文.remote.$on('commands/change',目录变更)#目录变更
        上下文.remote.$on('agent-preset/selected',预设选定)#预设
        上下文.on('connection/reset',连接重置)#重连

    def sessions(自身):
        """取会话服务。"""
        会话=自身.ctx.get('sessions')#会话
        if 会话 is None:#无
            raise 命令错误('ui-commands: sessions 服务不可用')#失败
        return 会话#会话

    def register(自身,贡献):
        """登记客户端贡献；重名抛。贡献为 dict。"""
        名=贡献['name']#名
        def 挂():
            """挂上。"""
            if 名 in 自身.贡献:#重
                raise 命令错误('ui-commands: 重复贡献 /'+名)#抛
            自身.贡献[名]=贡献#记
            def 摘贡献():
                """摘掉该贡献。"""
                自身.贡献.pop(名,None)#摘
            return 摘贡献#拆
        拆=自身.ctx.副作用(挂,'command.register()')#挂
        def 拆贡献():
            """拆副作用。"""
            拆()#拆
        return 拆贡献#拆

    def decorate(自身,装饰):
        """挂宿主装饰；重名抛。装饰为 dict。"""
        名=装饰['name']#名
        def 挂():
            """挂上。"""
            if 名 in 自身.装饰:#重
                raise 命令错误('ui-commands: 重复装饰 /'+名)#抛
            自身.装饰[名]=装饰#记
            def 摘装饰():
                """摘掉该装饰。"""
                自身.装饰.pop(名,None)#摘
            return 摘装饰#拆
        拆=自身.ctx.副作用(挂,'command.decorate()')#挂
        def 拆装饰():
            """拆副作用。"""
            拆()#拆
        return 拆装饰#拆

    def 解散(自身,名):
        """关掉该命令已打开的弹出，不消费草稿。"""
        for 控制器 in list(自身.弹出.values()):#逐会话
            if 控制器.命令==名:#同名
                控制器.dismiss()#关

    def popupFor(自身,作用域):
        """解析每会话弹出控制器。"""
        标识=自身.sessions().scopeOf(作用域)#id
        if 标识 is None:#非会话
            raise 命令错误('command.popupFor 需要会话作用域')#抛
        if 标识 in 自身.弹出:#已有
            return 自身.弹出[标识]#复用
        def 消费(片段):
            """消费打开时令牌。片段为 dict。"""
            守卫={'kind':'span','span':片段['span']} if 片段['via']=='menu' else {'kind':'bare-token','token':片段['token']}#守卫
            return 作用域.bail(作用域,'slash/input-consume-token',{'guard':守卫}) is True#成败
        def 聚焦():
            """调用该会话聚焦钩。"""
            if 标识 not in 自身.聚焦钩:#无
                return None#停
            return 自身.聚焦钩[标识]()#聚焦
        控制器=弹出选定控制器(消费,聚焦)#控
        自身.弹出[标识]=控制器#挂
        def 拆会话():
            """会话拆除。"""
            控制器.dispose()#拆
            自身.弹出.pop(标识,None)#摘
            自身.聚焦钩.pop(标识,None)#摘
            def 空拆():
                """副作用约定的拆除器。"""
                return None#无事
            return 空拆#空
        作用域.副作用(拆会话,'command: session popup')#挂
        return 控制器#交

    def bindComposerFocus(自身,标识,聚焦):
        """绑定编写器聚焦钩。"""
        自身.聚焦钩[标识]=聚焦#挂
        def 解绑():
            """仍同一钩才摘。"""
            if 标识 in 自身.聚焦钩 and 自身.聚焦钩[标识] is 聚焦:#同
                自身.聚焦钩.pop(标识,None)#摘
        return 解绑#拆

    def 候选(自身,会话,请求):
        """菜单候选：宿主 + 贡献，内置行本地化；空查询分区。"""
        表=自身.目录.ensureReady(会话['sessionId'],请求['signal'] if 'signal' in 请求 else None)#目录
        行=[]#行
        已见=set()#名
        for 项 in 表:#宿主
            已见.add(项['name'])#记
            面=内置行面(项,自身.t)#内置面
            行项={'name':项['name']}#行
            if 面 is None:#非内置
                if 'description' in 项:#有目录说明
                    行项['description']=项['description']#保留
            else:#内置
                行项.update(面)#标签说明图标
            if 'input' in 项 and 项['input'] is not None and 'hint' in 项['input']:#hint
                行项['hint']=项['input']['hint']#带上
            行.append(行项)#收下
        for 名,贡献 in 自身.贡献.items():#贡献
            if 贡献['available'](会话) is False:#不可用
                continue#下
            if 名 in 已见:#撞
                raise 命令错误('ui-commands: 贡献 /'+名+' 与宿主命令冲突')#抛
            行项={'name':名}#行
            if 'label' in 贡献 and 贡献['label'] is not None:#标题
                行项['label']=贡献['label']()#解析
            if 'description' in 贡献 and 贡献['description'] is not None:#说明
                行项['description']=贡献['description']()#解析
            if 'icon' in 贡献:#图标
                行项['icon']=贡献['icon']#字形
            行.append(行项)#收下
        可见=[]#过滤
        for 项 in 行:#逐行
            if 请求['position']=='leading' or ('hint' not in 项):#行首位或无 hint
                可见.append(项)#收下
        if 请求['query']=='':#空查询
            return 分区行(可见,自身.t)#分区
        return 按名排序(可见,请求['query'])#名与标签排序

    def 派发(自身,点选):
        """菜单点选：贡献 invoke 或宿主路径。点选为 dict。"""
        名=点选['candidate']['name']#命令名
        会话=点选['session']#会话
        if 名 in 自身.贡献 and 自身.贡献[名]['available'](会话):#贡献可用
            自身.invoke(名,自身.贡献[名]['ui'],会话,{'via':'menu','span':点选['span']})#调用
            return 'handled'#已处理
        描=自身.目录.resolve(会话['sessionId'],名)#宿主
        if 描 is None:#快照换过
            return None#未命中
        if 名 in 自身.装饰 and 自身.装饰[名]['available'](会话):#装饰可用
            自身.invoke(名,自身.装饰[名]['ui'],会话,{'via':'menu','span':点选['span']})#调用
            return 'handled'#已处理
        if 'input' in 描 and 描['input'] is not None:#认领
            return {'claim':自身.前缀认领(描,会话,认领令牌(描,自身.t))}#本地化拼写
        自身.经片段消费(会话['sessionId'],{'via':'menu','span':点选['span']})#消费
        自身.分离执行(描,会话,'/'+名)#分离执行
        return 'handled'#已处理

    def 匹配空格(自身,会话,令牌):
        """空格裁决：只有宿主 leadingInput 认领。"""
        if 令牌.startswith('/') is False:#非命令
            return None#无
        键入=令牌[1:]#名
        if 键入 in 自身.贡献:#弹出与动作从不空格认领
            return None#无
        描=自身.目录.resolve(会话['sessionId'],键入)#描
        if 描 is None or ('input' not in 描) or 描['input'] is None:#无参
            return None#无
        return {'claim':自身.前缀认领(描,会话,键入)}#认领

    def 匹配回车(自身,会话,行,信号,信封):
        """回车裁决；键入令牌经本地化拼写解析。"""
        修剪=行.strip()#修剪
        if 修剪.startswith('/') is False:#非
            return None#无
        空=None#空白
        序=0#扫描
        while 序<len(修剪):#找
            if 修剪[序].isspace():#空白
                空=序#记
                break#止
            序+=1#前进
        令牌=修剪 if 空 is None else 修剪[:空]#令牌
        裸=空 is None#裸
        键入名=令牌[1:]#键入名
        if 键入名=='':#空名
            return None#无
        附件数=信封['attachments'] if 'attachments' in 信封 else 0#附件
        def 拒附件():
            """拒收附件提交。"""
            raise 命令错误(自身.t('notice.attachmentsUnsupported',command=键入名))#拒
        if 键入名 in 自身.贡献 and 自身.贡献[键入名]['available'](会话):#贡献可用
            if 裸 is False:#有参
                return None#无
            规格=自身.贡献[键入名]['ui']#UI
            if 附件数>0 and 规格['kind']!='action':#非 action
                拒附件()#拒
            自身.invoke(键入名,规格,会话,{'via':'enter','token':令牌})#调用
            return 'handled'#已处理
        自身.目录.ensureReady(会话['sessionId'],信号)#目录
        描=自身.目录.resolve(会话['sessionId'],键入名)#描
        if 描 is None:#无
            return None#无
        名=描['name']#目录名
        规范='/'+名+修剪[len(令牌):]#规范行
        if 裸 is True and 名 in 自身.装饰 and 自身.装饰[名]['available'](会话):#装饰
            规格=自身.装饰[名]['ui']#UI
            if 附件数>0 and 规格['kind']!='action':#非 action
                拒附件()#拒
            自身.invoke(名,规格,会话,{'via':'enter','token':令牌})#调用
            return 'handled'#已处理
        if 'input' in 描 and 描['input'] is not None:#有参面
            if 附件数>0 and (('attachments' not in 描['input']) or 描['input']['attachments'] is not True):#未声明
                拒附件()#拒
            return {'claim':自身.前缀认领(描,会话,令牌[1:])}#认领
        if 裸 is False:#有参无认领
            return None#无
        if 附件数>0:#裸 execute
            拒附件()#拒
        自身.经片段消费(会话['sessionId'],{'via':'enter','token':令牌})#消费
        自身.分离执行(描,会话,规范)#分离执行
        return 'handled'#已处理

    def invoke(自身,名,规格,会话,片段):
        """贡献/装饰裸调用：action 消费令牌并 run；否则开弹出。"""
        if 规格['kind']=='action':#动作
            自身.经片段消费(会话['sessionId'],片段)#消费
            规格['run'](会话)#跑
            return#止
        作用=自身.sessions().scope(会话['sessionId'])#作用域
        if 作用 is None:#无
            return#止
        自身.popupFor(作用).open(名,规格,会话,片段)#开弹出

    def 前缀认领(自身,描,会话,展示):
        """leadingInput 认领。展示为草稿拼写；提交用目录名。"""
        令牌='/'+展示+' '#展示令牌
        行='/'+描['name']+' '#提交行
        认领={'name':描['name'],'token':令牌}#面
        输入=描['input'] if 'input' in 描 else None#输入
        if 输入 is not None and 'hint' in 输入:#提示
            认领['hint']=输入['hint']#hint
        if 输入 is not None and 'attachments' in 输入 and 输入['attachments'] is True:#附件
            认领['attachments']=True#接受
        def 提交(参数,_作用=None,附件=()):
            """提交 execute。"""
            return 自身.执行(会话,行+参数,附件)#执行
        认领['submit']=提交#提交
        return 认领#认领

    def 执行(自身,会话,行,附件=()):
        """command.execute 事务。"""
        标识=会话['sessionId']#id
        结果=自身.ctx.remote.commands.execute(标识,行,附件)#RPC
        if 结果['ok'] is not True:#拒
            错误体=结果['error']#错误体
            raise 命令错误('command.execute 失败: '+str(错误体['code'])+': '+str(错误体['message']))#抛
        值=结果['value']#值
        if 值 is None:#未匹配
            return {'kind':'error','text':'未知或格式错误的命令: '+行}#错误
        自身.通知已执行(标识,已提交命令名(行),值['result'])#回执
        if len(附件)>0 and 值['result']['kind']=='error':#带附件且处理失败
            return {'kind':'error','text':值['result']['text']}#报错误
        return {'kind':'success'}#成功

    def 通知已执行(自身,会话标识,名,结果):
        """发布本地回执，不嗅探 thenable。"""
        自身.ctx.emit('command/executed',会话标识,名,结果)#回执

    def 经片段消费(自身,标识,片段):
        """消费打开时令牌。"""
        作用=自身.sessions().scope(标识)#作用域
        if 作用 is None:#无
            return#止
        守卫={'kind':'span','span':片段['span']} if 片段['via']=='menu' else {'kind':'bare-token','token':片段['token']}#守卫
        作用.bail(作用,'slash/input-consume-token',{'guard':守卫})#消费

    def 分离执行(自身,描,会话,行):
        """裸宿主命令分离执行。"""
        try:#跑
            结局=自身.执行(会话,行,())#执行
        except 命令错误 as 错误:#调用失败
            自身.提示(会话['sessionId'],'error',错误.args[0] if len(错误.args)>0 else str(错误))#提示
            return#止
        if 结局['kind']=='error':#准入失败
            文=结局['text'] if 'text' in 结局 else '/'+描['name']+' 失败'#文案
            自身.提示(会话['sessionId'],'error',文)#提示

    def 提示(自身,标识,级别,文本):
        """编写器提示。"""
        作用=自身.sessions().scope(标识)#作用域
        if 作用 is None:#无
            return#止
        会话=作用.get('conversation')#对话
        if 会话 is None:#无
            return#止
        会话.input.按作用域取门面(作用).notify(级别,文本)#抛提示
