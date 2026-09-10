"""命令界面运行时（`ctx.commandUi`）。

对齐上游 `ui-commands/src/client/service.ts`。公开面仅中文名。
会话键目录 + 「/」源 + 贡献登记 + 每会话弹出控制器。
Action 种类裸调用消费令牌并跑回调，不提交，故带附件草稿不拒收。
目录缓存与弹出控制器的完整实现分属未在本批配额内的模块；此处以可替换钩
提供最小可运行面，宿主可后续挂接。
"""
import threading#寿命

__all__=['命令UI运行时']#仅中文公开名


def _已提交命令名(行):
    """从宿主确认已执行的一行取出命令名（去前导斜杠）。"""
    修剪=行.strip()#去空白
    空=None#空白下标
    for 序,字 in enumerate(修剪):#找空白
        if 字.isspace():#空白
            空=序#记
            break#止
    段=修剪 if 空 is None else 修剪[:空]#令牌
    return 段[1:] if 段.startswith('/') else 段#去斜杠


宿主说明键={#第一方宿主命令说明文案键
    'compact':'description.compact',
    'export':'description.export',
    'feedback':'description.feedback',
    'goal':'description.goal',
    'permission':'description.permission',
    'plan':'description.plan',
}#键表结束


class _最小弹出控制器:#popupSelect 最小面
    """目录/弹出完整实现到位前的占位控制器。"""

    def __init__(自身,消费,聚焦):
        """记下消费与聚焦回调。"""
        自身.consume=消费#消费令牌
        自身.focusComposer=聚焦#聚焦
        自身._开=False#是否打开

    def open(自身,名,规格,会话,片段):
        """打开弹出；无 UI 时仅记录。"""
        自身._开=True#开
        自身._名=名#名
        自身._规格=规格#规格
        自身._会话=会话#会话
        自身._片段=片段#片段

    def dispose(自身):
        """拆除。"""
        自身._开=False#关


class _最小目录:#会话键目录最小面
    """ensureReady / resolve / warm / invalidate / reset 的空实现。"""

    def __init__(自身,拉列表):
        """记下按会话拉宿主目录的回调。"""
        自身.拉列表=拉列表#拉
        自身.缓存={}#sessionId → list

    def ensureReady(自身,会话标识,信号=None):
        """强等到目录就绪。"""
        if 会话标识 in 自身.缓存:#已有
            return 自身.缓存[会话标识]#表
        任务=自身.拉列表(会话标识)#拉
        表=任务.等待() if hasattr(任务,'等待') else 任务#等
        自身.缓存[会话标识]=表#记
        return 表#表

    def resolve(自身,会话标识,名):
        """按名解析描述符。"""
        表=自身.缓存[会话标识] if 会话标识 in 自身.缓存 else ()#表
        for 项 in 表:#找
            if 项.get('name')==名:#命中
                return 项#描述符
        return None#无

    def warm(自身,会话标识):
        """预热。"""
        自身.ensureReady(会话标识)#拉

    def invalidateAll(自身):
        """软失效全部。"""
        自身.缓存.clear()#清

    def resetSession(自身,会话标识):
        """重置一场。"""
        自身.缓存.pop(会话标识,None)#删

    def resetConnected(自身):
        """重连硬重置。"""
        自身.缓存.clear()#清


class 命令UI运行时:#CommandUiRuntime
    """命令面：目录 + 「/」源 + 贡献/装饰 + 每会话弹出。"""

    inject=['inputTriggers','sessions','remote','remote.commands']#所需服务

    def __init__(自身,上下文):
        """挂上 commandUi 并登记斜杠源。"""
        自身.ctx=上下文#上下文
        if hasattr(上下文,'provide'):#可提供
            上下文.provide('commandUi',自身)#提供
        文案=上下文.get('locale') if hasattr(上下文,'get') else getattr(上下文,'locale',None)#文案
        if 文案 is None:#无
            raise Exception('ui-commands: locale service unavailable')#失败
        自身.t=文案.bind('command') if hasattr(文案,'bind') else (lambda 键,**_:键)#翻译
        自身.贡献={}#名 → 贡献
        自身.装饰={}#名 → 装饰
        自身.弹出={}#sessionId → 控制器
        自身.聚焦钩={}#sessionId → focus
        自身.寿命=threading.Event()#中止

        def 拉目录(会话标识):
            """RPC 列命令；子智能体会话空表。"""
            会话面=自身.sessions()#会话
            if hasattr(会话面,'subagentAddress') and 会话面.subagentAddress(会话标识) is not None:#子
                return []#空
            结果=上下文.remote.commands.list(会话标识)#列
            结果=结果.等待() if hasattr(结果,'等待') else 结果#等
            if not 结果['ok']:#失败
                错=结果['error']#错
                raise Exception('command.list failed: '+str(错.get('code',''))+': '+str(错.get('message',错)))#抛
            return 结果['value']#表

        自身.目录=_最小目录(拉目录)#目录
        触发=上下文.get('inputTriggers') if hasattr(上下文,'get') else getattr(上下文,'inputTriggers',None)#斜杠
        if 触发 is None:#无
            raise Exception('ui-commands: slash service unavailable')#失败

        def 登记源():
            """登记 '/' 源。"""
            return 触发.registerSource({#源
                'trigger':'/',#触发
                'name':'command',#名
                'candidates':自身.候选,#候选
                'onPick':自身.派发,#点选
                'matchSpace':自身.匹配空格,#空格
                'matchEnter':自身.匹配回车,#回车
                'warm':lambda 会话:自身.目录.warm(会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId),#预热
            })#源结束

        if hasattr(上下文,'副作用'):#effect
            上下文.副作用(登记源,'command: slash source')#挂源
        if hasattr(上下文.remote,'$on'):#远程事件
            上下文.remote.$on('commands/change',lambda *a:自身.目录.invalidateAll())#目录变更
            上下文.remote.$on('agent-preset/selected',lambda 标识,*a:自身.目录.resetSession(标识))#预设
        if hasattr(上下文,'on'):#本地事件
            上下文.on('connection/reset',lambda *a:自身.目录.resetConnected())#重连

    def sessions(自身):
        """取会话服务。"""
        return 自身.ctx.get('sessions') if hasattr(自身.ctx,'get') else 自身.ctx.sessions#会话

    def register(自身,贡献):
        """登记客户端贡献；重名抛。"""
        名=贡献['name']#名
        def 挂():
            """挂上。"""
            if 名 in 自身.贡献:#重
                raise Exception('ui-commands: duplicate contribution for /'+名)#抛
            自身.贡献[名]=贡献#记
            return lambda:自身.贡献.pop(名,None)#拆
        if hasattr(自身.ctx,'副作用'):#effect
            拆=自身.ctx.副作用(挂,'command.register()')#挂
            return lambda:拆() if callable(拆) else None#拆
        return 挂()#直接

    def decorate(自身,装饰):
        """挂宿主装饰；重名抛。"""
        名=装饰['name']#名
        def 挂():
            """挂上。"""
            if 名 in 自身.装饰:#重
                raise Exception('ui-commands: duplicate decoration for /'+名)#抛
            自身.装饰[名]=装饰#记
            return lambda:自身.装饰.pop(名,None)#拆
        if hasattr(自身.ctx,'副作用'):#effect
            拆=自身.ctx.副作用(挂,'command.decorate()')#挂
            return lambda:拆() if callable(拆) else None#拆
        return 挂()#直接

    def popupFor(自身,作用域):
        """解析每会话弹出控制器。"""
        会话=自身.sessions()#会话
        标识=会话.scopeOf(作用域) if hasattr(会话,'scopeOf') else None#id
        if 标识 is None:#非会话
            raise Exception('command.popupFor requires a session scope')#抛
        if 标识 in 自身.弹出:#已有
            return 自身.弹出[标识]#复用
        def 消费(片段):
            """消费打开时令牌。"""
            守卫={'kind':'span','span':片段['span']} if 片段.get('via')=='menu' else {'kind':'bare-token','token':片段['token']}#守卫
            return 作用域.bail(作用域,'slash/input-consume-token',{'guard':守卫}) is True#成败
        控制器=_最小弹出控制器(消费,lambda:自身.聚焦钩.get(标识,lambda:None)())#控
        自身.弹出[标识]=控制器#挂
        if hasattr(作用域,'副作用'):#寿命
            def 拆会话():
                """会话拆除。"""
                控制器.dispose()#拆
                自身.弹出.pop(标识,None)#摘
                自身.聚焦钩.pop(标识,None)#摘
                return lambda:None#空
            作用域.副作用(拆会话,'command: session popup')#挂
        return 控制器#交

    def bindComposerFocus(自身,标识,聚焦):
        """绑定编写器聚焦钩。"""
        自身.聚焦钩[标识]=聚焦#挂
        def 解绑():
            """仍同一钩才摘。"""
            if 自身.聚焦钩.get(标识) is 聚焦:#同
                自身.聚焦钩.pop(标识,None)#摘
        return 解绑#拆

    def 候选(自身,会话,请求):
        """菜单候选：宿主 + 贡献，撞名大声失败。"""
        信号=请求['signal'] if isinstance(请求,dict) and 'signal' in 请求 else None#信号
        表=自身.目录.ensureReady(会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId,信号)#目录
        行=[]#行
        已见=set()#名
        for 项 in 表:#宿主
            已见.add(项['name'])#记
            行.append({'name':项['name'],'description':项.get('description',''),'source':'host'})#行
        for 名,贡献 in 自身.贡献.items():#贡献
            可用=贡献['available'](会话)#过滤
            if not 可用:#跳
                continue#下
            if 名 in 已见:#撞
                raise Exception('ui-commands: contribution /'+名+' collides with a host command')#抛
            行.append({'name':名,'description':贡献['description'](),'source':'contribution'})#行
        return 行#候选

    def 派发(自身,点选):
        """菜单点选：贡献 invoke 或宿主路径。"""
        名=点选['name'] if isinstance(点选,dict) else getattr(点选,'name',None)#名
        会话=点选['session'] if isinstance(点选,dict) else getattr(点选,'session',None)#会话
        片段={'via':'menu','token':'/'+名,'span':点选.get('span') if isinstance(点选,dict) else None}#片段
        if 名 in 自身.贡献:#贡献
            自身.invoke(名,自身.贡献[名]['ui'],会话,片段)#调用
            return 'handled'#已处理
        return None#交其它

    def 匹配空格(自身,会话,令牌):
        """空格裁决：有参认领则 claim。"""
        if not 令牌.startswith('/'):#非命令
            return None#无
        名=令牌[1:]#名
        表=自身.目录.ensureReady(会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId)#目录
        描=自身.目录.resolve(会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId,名)#描
        if 描 is None or 描.get('input') is None:#无参
            return None#无
        return {'claim':自身.前缀认领(描,会话)}#认领

    def 匹配回车(自身,会话,行,信号,信封):
        """回车裁决；action 不因附件拒收。"""
        修剪=行.strip()#修剪
        if not 修剪.startswith('/'):#非
            return None#无
        空=None#空白
        for 序,字 in enumerate(修剪):#找
            if 字.isspace():#空白
                空=序#记
                break#止
        令牌=修剪 if 空 is None else 修剪[:空]#令牌
        裸=空 is None#裸
        名=令牌[1:]#名
        if 名=='':#空名
            return None#无
        附件数=信封['attachments'] if isinstance(信封,dict) and 'attachments' in 信封 else 0#附件

        def 拒附件():
            """拒收附件提交。"""
            raise Exception(自身.t('notice.attachmentsUnsupported',command=名))#拒

        if 名 in 自身.贡献 and 自身.贡献[名]['available'](会话):#贡献可用
            if not 裸:#有参
                return None#无
            规格=自身.贡献[名]['ui']#UI
            if 附件数>0 and 规格.get('kind')!='action':#非 action
                拒附件()#拒
            自身.invoke(名,规格,会话,{'via':'enter','token':令牌})#调用
            return 'handled'#已处理
        自身.目录.ensureReady(会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId,信号)#目录
        描=自身.目录.resolve(会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId,名)#描
        if 描 is None:#无
            return None#无
        if 裸 and 名 in 自身.装饰 and 自身.装饰[名]['available'](会话):#装饰
            规格=自身.装饰[名]['ui']#UI
            if 附件数>0 and 规格.get('kind')!='action':#非 action
                拒附件()#拒
            自身.invoke(名,规格,会话,{'via':'enter','token':令牌})#调用
            return 'handled'#已处理
        if 描.get('input') is not None:#有参面
            if 附件数>0 and 描['input'].get('attachments') is not True:#未声明
                拒附件()#拒
            return {'claim':自身.前缀认领(描,会话)}#认领
        if not 裸:#有参无认领
            return None#无
        if 附件数>0:#裸 execute
            拒附件()#拒
        自身.经片段消费(会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId,{'via':'enter','token':令牌})#消费
        自身.跑分离(描,会话,修剪)#分离执行
        return 'handled'#已处理

    def invoke(自身,名,规格,会话,片段):
        """贡献/装饰裸调用：action 消费令牌并 run；否则开弹出。"""
        if 规格.get('kind')=='action':#动作
            自身.经片段消费(会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId,片段)#消费
            规格['run'](会话)#跑
            return#止
        标识=会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId#id
        作用=自身.sessions().scope(标识) if hasattr(自身.sessions(),'scope') else None#作用域
        if 作用 is None:#无
            return#止
        自身.popupFor(作用).open(名,规格,会话,片段)#开弹出

    def 前缀认领(自身,描,会话):
        """leadingInput 认领。"""
        令牌='/'+描['name']+' '#令牌
        认领={'token':令牌}#面
        输入=描.get('input')#输入
        if 输入 is not None and 'hint' in 输入:#提示
            认领['hint']=输入['hint']#hint
        if 输入 is not None and 输入.get('attachments') is True:#附件
            认领['attachments']=True#接受
        def 提交(参数,_作用=None,附件=()):
            """提交 execute。"""
            return 自身.执行(会话,令牌+参数,附件)#执行
        认领['submit']=提交#提交
        return 认领#认领

    def 执行(自身,会话,行,附件=()):
        """command.execute 事务。"""
        标识=会话['sessionId'] if isinstance(会话,dict) else 会话.sessionId#id
        结果=自身.ctx.remote.commands.execute(标识,行,附件)#RPC
        结果=结果.等待() if hasattr(结果,'等待') else 结果#等
        if not 结果['ok']:#拒
            错=结果['error']#错
            raise Exception(str(错.get('message',错) if isinstance(错,dict) else 错))#抛
        值=结果['value']#值
        if len(附件)>0 and 值.get('result',{}).get('kind')=='error':#附件失败
            raise Exception(值['result'].get('message','command error'))#保留草稿
        名=_已提交命令名(行)#名
        if hasattr(自身.ctx,'emit'):#本地回执
            自身.ctx.emit('command/executed',标识,名,值.get('result'))#回执
        return {'ok':True}#成功

    def 经片段消费(自身,标识,片段):
        """消费打开时令牌。"""
        作用=自身.sessions().scope(标识) if hasattr(自身.sessions(),'scope') else None#作用域
        if 作用 is None:#无
            return#止
        守卫={'kind':'span','span':片段['span']} if 片段.get('via')=='menu' else {'kind':'bare-token','token':片段['token']}#守卫
        作用.bail(作用,'slash/input-consume-token',{'guard':守卫})#消费

    def 跑分离(自身,描,会话,行):
        """裸宿主命令分离执行。"""
        自身.执行(会话,行,())#执行
