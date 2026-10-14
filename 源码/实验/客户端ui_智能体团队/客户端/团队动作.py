from nicegui import ui as 界面

__all__=['团队动作','任务表单','拆分项','失败文案']#仅中文公开名

def 失败说明(错误):
    '失败句去掉绝对路径，其余原文保留'
    if isinstance(错误,BaseException) and len(错误.args)>0:
        原文=str(错误.args[0])
    else:
        原文=str(错误)
    留下=[]
    for 词 in 原文.split():
        去引=词.strip('\'"()[]{}<>')
        统一=去引.replace('\\','/')
        if 统一.startswith('/') or 统一.startswith('~'):
            continue
        if len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/':
            continue
        留下.append(词)
    说明=' '.join(留下).strip()
    if 说明!='':
        return 说明
    if isinstance(错误,BaseException):
        return type(错误).__name__
    return '失败'

空草稿={'subject':'','description':'','blockers':'','scopes':''}#空草稿

def 恒等键(键,_缺省=None):#无翻译时返回键
    '无翻译函数时原样返回键'
    return 键#原样

def 读团队投影(属性,会话标识):#读 agentTeam 投影
    '从槽运行时 useSession/useSessions 读 Lead 的 agentTeam 投影'
    用单会话=属性['useSession'] if 'useSession' in 属性 else None#单会话钩
    用会话表=属性['useSessions'] if 'useSessions' in 属性 else None#会话表钩
    领导=会话标识#默认当前会话即 Lead
    if 用单会话 is not None:
        def 选父(快照):#选 parentSessionId
            '子会话映射到 Lead'
            if 快照 is None or 'subagent' not in 快照:#无子
                return None#无
            子=快照['subagent']#子智能体
            if 子 is None or 'address' not in 子:#无地址
                return None#无
            地址=子['address']#地址
            if 地址 is None or 'parentSessionId' not in 地址:#无父
                return None#无
            return 地址['parentSessionId']#父
        父=用单会话(选父)#投影
        if 父 is not None:
            领导=父#改用 Lead
    if 用会话表 is None:#无表钩
        return None#无投影
    def 选团队(状态):#选 agentTeam
        '按 Lead 会话读投影'
        if 状态 is None or 'projectionsBySession' not in 状态:#无表
            return None#无
        投影表=状态['projectionsBySession']#投影表
        条目=投影表[领导] if 领导 in 投影表 else None#条目
        if 条目 is None or 'values' not in 条目:#无值
            return None#无
        值=条目['values']#值
        return 值['agentTeam'] if 'agentTeam' in 值 else None#投影
    return 用会话表(选团队)#投影

def 拆分项(值):#逗号拆分去重
    '逗号拆分去重'
    return list(dict.fromkeys(项.strip() for 项 in 值.split(',') if 项.strip()!=''))#拆分去重

def 失败文案(错误):#失败文案
    'RPC 错误 dict 的一行失败文案'
    return 失败说明(str(错误['message'])+' ('+str(错误['code'])+')')#拼接码

def 任务状态键(状态):#任务状态键
    '任务状态 → 文案键'
    if 状态=='pending':#待处理
        return 'status.pending'#键
    if 状态=='in_progress':#进行中
        return 'status.in_progress'#键
    if 状态=='completed':#已完成
        return 'status.completed'#键
    return 'status.completed'#删除当完成键

def 成员状态键(状态):#成员状态键
    '成员状态 → 文案键'
    表={#映射
        'running':'memberStatus.running',#运行中
        'idle':'memberStatus.idle',#空闲
        'inactive':'memberStatus.inactive',#未运行
        'provisioning':'memberStatus.provisioning',#准备中
        'failed':'memberStatus.failed',#失败
    }#表结束
    return 表[状态] if 状态 in 表 else 状态#键

class 任务表单:#任务表单结构树
    '标题/详情/依赖/写范围四字段表单'
    def __init__(自身,草稿,进行中,保存,取消,翻译):#构造
        '记下草稿与回调'
        自身.draft=草稿#草稿
        自身.pending=进行中#进行中
        自身.onSave=保存#保存
        自身.onCancel=取消#取消
        自身.t=翻译#翻译

    def 改字段(自身,键,值):#改字段
        '写回草稿字段'
        自身.draft[键]=值#写字段

    def 改标题(自身,值):#改标题
        '写回标题'
        自身.改字段('subject',值)#写标题

    def 改详情(自身,值):#改详情
        '写回详情'
        自身.改字段('description',值)#写详情

    def 改依赖(自身,值):#改依赖
        '写回依赖串'
        自身.改字段('blockers',值)#写依赖

    def 改范围(自身,值):#改写范围
        '写回写范围串'
        自身.改字段('scopes',值)#写范围

    def 渲染(自身):#结构树
        '表单树'
        翻译=自身.t#文案
        禁用保存=自身.pending is True or 自身.draft['subject'].strip()=='' or 自身.draft['description'].strip()==''#禁用
        with 界面.column().classes('团队表单'):
            界面.input(placeholder=翻译('subject'), value=自身.draft['subject'], on_change=lambda 事件:自身.改标题(事件.value))
            界面.textarea(placeholder=翻译('description'), value=自身.draft['description'], on_change=lambda 事件:自身.改详情(事件.value))
            界面.input(placeholder=翻译('blockers'), value=自身.draft['blockers'], on_change=lambda 事件:自身.改依赖(事件.value))
            界面.input(placeholder=翻译('scopes'), value=自身.draft['scopes'], on_change=lambda 事件:自身.改范围(事件.value))
            保存钮=界面.button(翻译('save'), on_click=自身.onSave).props('flat no-caps')
            if 禁用保存:
                保存钮.disable()
            取消钮=界面.button(翻译('cancel'), on_click=自身.onCancel).props('flat no-caps')
            if 自身.pending:
                取消钮.disable()
        return {#表单
            'type':'team-task-form',#类型
            'subject':自身.draft['subject'],#标题
            'description':自身.draft['description'],#详情
            'blockers':自身.draft['blockers'],#依赖
            'scopes':自身.draft['scopes'],#写范围
            'subjectPlaceholder':翻译('subject'),#标题占位
            'descriptionPlaceholder':翻译('description'),#详情占位
            'blockersPlaceholder':翻译('blockers'),#依赖占位
            'scopesPlaceholder':翻译('scopes'),#写范围占位
            'saveLabel':翻译('save'),#保存
            'cancelLabel':翻译('cancel'),#取消
            'saveDisabled':禁用保存,#禁用保存
            'cancelDisabled':自身.pending,#禁用取消
            'onSubject':自身.改标题,#改标题
            'onDescription':自身.改详情,#改详情
            'onBlockers':自身.改依赖,#改依赖
            'onScopes':自身.改范围,#改写范围
            'onSave':自身.onSave,#保存
            'onCancel':自身.onCancel,#取消
            'cssModule':'团队动作.module.css',#样式
        }#视图结束

class 团队动作:#标题栏 Team 动作
    '渲染 live Team roster 与 compare-and-set 任务板'
    def __init__(自身,属性=None):#构造
        '记下 props 与初始状态'
        自身.属性={} if 属性 is None else 属性#合成
        自身.打开=False#面板是否打开
        自身.加载中=False#加载中
        自身.视图=None#当前视图
        自身.错误=None#错误行
        自身.创建中=False#是否在创建
        自身.创建草稿=dict(空草稿)#创建草稿
        自身.编辑中=None#编辑中任务 id
        自身.编辑草稿=dict(空草稿)#编辑草稿
        自身.进行中任务=set()#进行中任务
        自身._会话引用=自身.属性['sessionId'] if 'sessionId' in 自身.属性 else None#当前会话
        自身._刷新代数=0#刷新代数
        if ('t' in 自身.属性 and 'sessionId' in 自身.属性 and 'openTeammate' in 自身.属性
                and 'useSession' in 自身.属性 and 'useSessions' in 自身.属性):
            自身.渲染()

    def 更新(自身,属性):#刷新 props
        '会话切换则重置面板状态'
        新会话=属性['sessionId'] if 属性 is not None and 'sessionId' in 属性 else None#新会话
        旧会话=自身._会话引用#旧会话
        自身.属性={} if 属性 is None else 属性#新 props
        自身._会话引用=新会话#同步
        if 新会话!=旧会话:#会话切换
            自身._重置状态()#重置

    def _重置状态(自身):#重置状态
        '会话切换重置'
        自身._刷新代数+=1#推进代
        自身.打开=False#关面板
        自身.加载中=False
        自身.视图=None
        自身.错误=None
        自身.创建中=False
        自身.创建草稿=dict(空草稿)
        自身.编辑中=None
        自身.编辑草稿=dict(空草稿)
        自身.进行中任务=set()

    def _翻译(自身):#取翻译
        '取翻译函数'
        return 自身.属性['t'] if 't' in 自身.属性 else 恒等键#文案

    def 刷新(自身):#刷新视图
        '拉取总览；代数过期则丢弃'
        会话=自身.属性['sessionId'] if 'sessionId' in 自身.属性 else None#请求时会话
        自身._刷新代数+=1#推进代
        代数=自身._刷新代数#本代
        自身.加载中=True#进入加载
        加载=自身.属性['load'] if 'load' in 自身.属性 else None#加载动作
        if 加载 is not None:#仍有 RPC 则走 RPC
            结果=加载(会话)#拉总览
            if 自身._会话引用!=会话 or 自身._刷新代数!=代数:#过期
                return False#过期
            自身.加载中=False#结束加载
            if 结果['ok'] is True:#成功
                自身.视图=结果['value']#写入视图
                自身.错误=None
                return True#成功
            自身.错误=失败文案(结果['error'])#写错误
            return False#失败
        投影=读团队投影(自身.属性,会话)#读投影
        if 自身._会话引用!=会话 or 自身._刷新代数!=代数:#过期
            return False#过期
        自身.加载中=False#结束加载
        自身.视图=投影#写入视图
        if 投影 is None:#暂不可用
            return False#无视图
        if 'failure' in 投影 and 投影['failure'] is not None:#持久失败
            自身.错误=自身._翻译()('failure').replace('{message}',失败说明(投影['failure']))#失败文案
        else:#无失败
            自身.错误=None
        return True#成功

    def _使刷新失效(自身):#使在途刷新失效
        '推进代数并清加载'
        自身._刷新代数+=1#推进代
        自身.加载中=False

    def 结算任务(自身,任务键,操作):#结算一次任务操作
        '跑任务变更并处理冲突/拒绝'
        会话=自身.属性['sessionId'] if 'sessionId' in 自身.属性 else None#请求时会话
        自身._使刷新失效()#失效在途刷新
        自身.进行中任务=set(自身.进行中任务)#拷贝
        自身.进行中任务.add(任务键)#标记进行中
        try:#执行
            return 自身._结算任务体(会话,操作)#体
        finally:#收尾
            if 自身._会话引用==会话:#仍同会话
                下一=set(自身.进行中任务)#拷贝
                下一.discard(任务键)#删除键
                自身.进行中任务=下一#更新

    def _结算任务体(自身,会话,操作):#结算体
        '结算任务操作主体'
        结果=操作()#跑操作已同步
        if 自身._会话引用!=会话:#会话已变
            return None#空
        if 结果['ok'] is not True:#传输失败
            自身.错误=失败文案(结果['error'])#写错误
            return None#空
        值=结果['value']#业务值
        if 值['ok'] is not True:#业务拒绝
            return 自身._处理业务拒绝(会话,值)#拒绝路径
        自身.错误=None
        自身.刷新()#成功后刷新
        if 自身._会话引用!=会话:#会话已变
            return None#空
        return 值['value']#返回任务

    def _处理业务拒绝(自身,会话,值):#业务拒绝
        '冲突则重载；其它拒绝写错误行'
        错误=值['error']#错误体
        if 错误['code']=='team-task-conflict':#冲突
            已重载=自身.刷新()#冲突则重载
            if 自身._会话引用!=会话:#会话已变
                return None#空
            if 已重载 is True:#提示冲突
                自身.错误=自身._翻译()('conflict')#冲突文案
        else:#其它拒绝
            自身.错误=失败文案(错误)#业务拒绝文案
        return None#空

    def 提交创建(自身):#提交创建
        '提交新建任务'
        标题=自身.创建草稿['subject'].strip()#标题
        描述=自身.创建草稿['description'].strip()#描述
        if 标题=='' or 描述=='':#空则跳过
            return#跳过
        会话=自身.属性['sessionId'] if 'sessionId' in 自身.属性 else None#会话
        创建=自身.属性['createTask'] if 'createTask' in 自身.属性 else None#创建动作
        if 创建 is None:#无 RPC
            return#跳过
        def 操作():#操作
            '建任务 RPC'
            return 创建(会话,{#建任务
                'subject':标题,#标题
                'description':描述,#描述
                'blockedBy':拆分项(自身.创建草稿['blockers']),#依赖
                'writeScopes':拆分项(自身.创建草稿['scopes']),#写范围
            })#RPC 结束
        已创建=自身.结算任务('create',操作)#结算
        if 已创建 is None:#失败
            return#返回
        自身.创建草稿=dict(空草稿)
        自身.创建中=False#退出创建

    def 开始编辑(自身,任务):#开始编辑
        '填入编辑草稿'
        自身.编辑中=任务['id']#编辑目标
        自身.编辑草稿={#填草稿
            'subject':任务['subject'],#标题
            'description':任务['description'],#详情
            'blockers':', '.join(任务['blockedBy']),#依赖串
            'scopes':', '.join(任务['writeScopes']),#写范围串
        }#草稿结束

    def 提交编辑(自身,任务):#提交编辑
        '先编辑文本，必要时再改依赖'
        更新=自身.属性['updateTask'] if 'updateTask' in 自身.属性 else None#更新动作
        if 更新 is None:#无 RPC
            return#跳过
        def 编辑操作():#编辑文本
            '编辑 RPC'
            return 更新(自身.属性['sessionId'],{#编辑
                'taskId':任务['id'],#任务 id
                'expectedRevision':任务['revision'],#期望版本
                'action':'edit',#编辑动作
                'subject':自身.编辑草稿['subject'].strip(),#新标题
                'description':自身.编辑草稿['description'].strip(),#新详情
                'writeScopes':拆分项(自身.编辑草稿['scopes']),#新写范围
            })#RPC 结束
        已编辑=自身.结算任务(任务['id'],编辑操作)#结算
        if 已编辑 is None:#失败
            return#返回
        依赖=拆分项(自身.编辑草稿['blockers'])#新依赖
        旧依赖=已编辑['blockedBy']#旧依赖
        if len(依赖)==len(旧依赖) and all(依赖[下标]==旧依赖[下标] for 下标 in range(len(依赖))):#依赖未变
            自身.编辑中=None#退出编辑
            return
        def 依赖操作():#再改依赖
            '改依赖 RPC'
            return 更新(自身.属性['sessionId'],{#改依赖
                'taskId':任务['id'],#任务 id
                'expectedRevision':已编辑['revision'],#新版本
                'action':'set_dependencies',#改依赖
                'blockedBy':依赖,#依赖列表
            })#RPC 结束
        依赖任务=自身.结算任务(任务['id'],依赖操作)#结算
        if 依赖任务 is None:#失败
            return#返回
        自身.编辑中=None#退出编辑

    def 切换面板(自身):#切换面板
        '打开或关闭面板；打开时刷新'
        自身.打开=not 自身.打开#切换
        if 自身.打开 is True:#打开时刷新
            自身.刷新()#刷新

    def 关闭面板(自身):#关闭面板
        '关闭面板'
        自身.打开=False#关闭

    def 开始创建(自身):#开始创建
        '进入创建表单'
        自身.创建中=True#开始创建

    def 取消创建(自身):#取消创建
        '退出创建表单'
        自身.创建中=False#取消

    def 取消编辑(自身):#取消编辑
        '退出编辑表单'
        自身.编辑中=None#取消

    def 渲染(自身):#结构树
        'Team 动作根树'
        翻译=自身._翻译()#文案
        视图=自身.视图#当前视图
        成员列表=视图['members'] if 视图 is not None else []#成员
        队友列表=[成员 for 成员 in 成员列表 if 成员['role']=='teammate']#teammate 列表
        界面.button(翻译('trigger')+' · '+str(len(队友列表)), on_click=自身.切换面板).props('flat no-caps')
        if 自身.打开 is True:
            面板=自身._渲染面板(翻译,视图,成员列表)
            with 界面.column().classes('团队面板'):
                界面.label(面板['title'])
                界面.button(面板['refreshLabel'], on_click=面板['onRefresh']).props('flat no-caps')
                界面.button(面板['closeLabel'], on_click=面板['onClose']).props('flat no-caps')
                if 面板['error']:
                    界面.label(str(面板['error']))
                if 面板['loadingNotice']:
                    界面.label(面板['loadingNotice'])
                正文=面板['body']
                if isinstance(正文,dict):
                    界面.label(正文['rosterTitle'])
                    for 成员行 in 正文['members']:
                        if not isinstance(成员行,dict):
                            continue
                        钮=界面.button(str(成员行.get('name') or '')+' · '+str(成员行.get('statusLabel') or ''), on_click=成员行.get('onOpen')).props('flat no-caps')
                        if 成员行.get('disabled'):
                            钮.disable()
                        if 成员行.get('openTitle'):
                            钮.tooltip(str(成员行['openTitle']))
                        for 诊断 in 成员行.get('diagnostics') or []:
                            界面.label(str(诊断))
                    界面.label(正文['tasksTitle'])
                    界面.button(正文['createLabel'], on_click=正文['onStartCreate']).props('flat no-caps')
                    创建表=正文.get('createForm')
                    if 创建表 is not None and hasattr(创建表,'渲染'):
                        创建表.渲染()
                    if 正文.get('emptyNotice'):
                        界面.label(正文['emptyNotice'])
                    for 任务行 in 正文['tasks']:
                        if not isinstance(任务行,dict):
                            continue
                        if 任务行.get('type')=='team-task-editing' and hasattr(任务行.get('form'),'渲染'):
                            任务行['form'].渲染()
                            continue
                        if 任务行.get('type')!='team-task':
                            continue
                        with 界面.column().classes('团队任务'):
                            界面.label(str(任务行.get('subject') or '')+' · '+str(任务行.get('statusLabel') or ''))
                            if 任务行.get('description'):
                                界面.label(str(任务行['description']))
                            for 行文 in 任务行.get('meta') or []:
                                界面.label(str(行文))
                            for 警告 in 任务行.get('warnings') or []:
                                界面.label(str(警告))
                            所有者=任务行.get('ownerValue') or ''
                            界面.label(str(任务行.get('ownerLabel') or '')+'：'+(所有者 or str(任务行.get('unownedLabel') or '')))
                            if not 任务行.get('ownerDisabled'):
                                人选={'':任务行.get('unownedLabel') or ''}
                                for 人 in 任务行.get('assignable') or []:
                                    if isinstance(人,dict):
                                        人选[人.get('id') or '']=人.get('name') or ''
                                def 改派(事件,回调=任务行.get('onOwner')):
                                    '写回所选 owner'
                                    if callable(回调):
                                        回调(事件.value)
                                界面.select(人选, value=所有者 if 所有者 in 人选 else '', on_change=改派).props('dense options-dense')
                            if 任务行.get('onEdit') is not None:
                                编辑钮=界面.button(任务行['editLabel'], on_click=任务行['onEdit']).props('flat no-caps')
                                if 任务行.get('editDisabled'):
                                    编辑钮.disable()
                            动作禁用=任务行.get('actionDisabled') is True
                            if 任务行.get('onComplete') is not None:
                                完成钮=界面.button(任务行['completeLabel'], on_click=任务行['onComplete']).props('flat no-caps')
                                if 动作禁用:
                                    完成钮.disable()
                            if 任务行.get('onReopen') is not None:
                                重开钮=界面.button(任务行['reopenLabel'], on_click=任务行['onReopen']).props('flat no-caps')
                                if 动作禁用:
                                    重开钮.disable()
                            if 任务行.get('onDelete') is not None:
                                删除钮=界面.button(任务行['deleteLabel'], on_click=任务行['onDelete']).props('flat no-caps')
                                if 动作禁用:
                                    删除钮.disable()
        return {#根
            'type':'team-action',#类型
            'open':自身.打开,#是否打开
            'triggerLabel':翻译('trigger'),#触发文案
            'teammateCount':len(队友列表),#队友数
            'onToggle':自身.切换面板,#切换
            'panel':自身._渲染面板(翻译,视图,成员列表) if 自身.打开 is True else None,#面板
            'cssModule':'团队动作.module.css',#样式
        }#根结束

    def _渲染面板(自身,翻译,视图,成员列表):
        '对话框面板树'
        return {#面板
            'type':'team-panel',#类型
            'title':翻译('trigger'),#标题
            'refreshLabel':翻译('refresh'),#刷新
            'closeLabel':翻译('close'),#关闭
            'onRefresh':自身.刷新,#刷新
            'onClose':自身.关闭面板,#关闭
            'error':自身.错误,#错误行
            'loadingNotice':翻译('loading') if 自身.加载中 is True and 视图 is None else None,#加载提示
            'body':自身._渲染正文(翻译,视图,成员列表) if 视图 is not None else None,#正文
        }#面板结束

    def _渲染正文(自身,翻译,视图,成员列表):
        'roster + 任务板'
        可分配=[成员 for 成员 in 成员列表 if 成员['status'] not in ('failed','provisioning')]#可分配
        任务列表=视图['tasks']#任务
        return {#正文
            'rosterTitle':翻译('roster'),#成员区标题
            'members':[自身._渲染成员(翻译,成员) for 成员 in 成员列表],#成员列表
            'tasksTitle':翻译('tasks'),#任务区标题
            'createLabel':翻译('create'),#新建
            'onStartCreate':自身.开始创建,#开始创建
            'createForm':自身._创建表单(翻译) if 自身.创建中 is True else None,#创建表单
            'emptyNotice':翻译('empty') if len(任务列表)==0 and 自身.创建中 is not True else None,#空提示
            'tasks':[自身._渲染任务(翻译,任务,可分配) for 任务 in 任务列表],#任务列表
        }#正文结束

    def _创建表单(自身,翻译):#创建表单
        '新建任务表单；由面板在列里调用渲染，构造时不画'
        return 任务表单(#表单
            自身.创建草稿,#草稿
            'create' in 自身.进行中任务,#进行中
            自身.提交创建,#保存
            自身.取消创建,#取消
            翻译,#翻译
        )

    def _打开成员(自身,成员):#打开 teammate
        '打开子会话'
        打开=自身.属性['openTeammate'] if 'openTeammate' in 自身.属性 else None#打开动作
        if 打开 is None:#无动作
            return#返回
        try:#试开
            打开(自身.属性['sessionId'],成员['id'])#打开已同步
        except Exception as 错误:#写 inbox/会话可能抛持久化/校验错误，契约未定所以收不窄
            自身.错误=失败说明(错误)#错误行

    def _渲染成员(自身,翻译,成员):
        '成员行'
        模型=成员['model'] if 'model' in 成员 else None#模型
        副文=翻译(成员状态键(成员['status']))#状态文案
        if 模型 is not None:
            副文=副文+' · '+翻译('model')+': '+str(模型)#拼模型
        禁用=成员['role']=='lead' or 成员['status'] in ('failed','provisioning')#禁用
        return {#成员行
            'id':成员['id'],#id
            'name':成员['name'],#名
            'status':成员['status'],#状态
            'statusLabel':副文,#副文
            'diagnostics':list(成员['diagnostics']),#诊断
            'disabled':禁用,#禁用
            'openTitle':翻译('open') if 成员['role']=='teammate' else None,#打开提示
            'onOpen':自身._打开成员绑定(成员),#点击
        }#行结束

    def _打开成员绑定(自身,成员):#绑定打开
        '返回打开该成员的回调'
        def 点击():#打开 teammate
            '打开子会话'
            自身._打开成员(成员)#打开
        return 点击#回调

    def _渲染任务(自身,翻译,任务,可分配):
        '一条任务或编辑表单'
        标识=任务['id']#任务 id
        if 自身.编辑中==标识:#编辑中
            return {#交给面板再画，避免构造时先画到列外
                'type':'team-task-editing',#编辑
                'form':任务表单(#表单
                    自身.编辑草稿,#草稿
                    标识 in 自身.进行中任务,#进行中
                    自身._提交编辑绑定(任务),#保存
                    自身.取消编辑,#取消
                    翻译,#翻译
                ),#实例
            }
        return 自身._任务卡片(翻译,任务,可分配)#卡片

    def _提交编辑绑定(自身,任务):#绑定提交编辑
        '返回提交该任务编辑的回调'
        def 保存():#保存
            '提交编辑'
            自身.提交编辑(任务)#提交
        return 保存#回调

    def _任务卡片(自身,翻译,任务,可分配):#任务卡片
        '只读任务卡片与动作'
        标识=任务['id']#任务 id
        状态=任务['status']#状态
        进行中=标识 in 自身.进行中任务#进行中
        元数据=[str(标识)]#元数据行
        if 状态=='pending':#待处理
            元数据.append(翻译('ready') if 任务['ready'] is True else 翻译('blocked'))#就绪/阻塞
        依赖=任务['blockedBy']#依赖
        if len(依赖)>0:
            元数据.append(翻译('blockedBy')+': '+', '.join(依赖))#依赖
        范围=任务['writeScopes']#写范围
        if len(范围)>0:
            元数据.append(翻译('writeScopes')+': '+', '.join(范围))#写范围
        所有者名=任务['ownerName'] if 'ownerName' in 任务 else ''#当前 owner
        if 所有者名 is None:#显式空
            所有者名=''#空串
        return {#卡片
            'type':'team-task',#类型
            'id':标识,#id
            'subject':任务['subject'],#标题
            'statusLabel':翻译(任务状态键(状态)),#状态
            'description':任务['description'],#详情
            'meta':元数据,#元数据
            'warnings':list(任务['writeScopeWarnings']),#警告
            'ownerLabel':翻译('owner'),#owner 标签
            'ownerValue':所有者名,#当前 owner
            'unownedLabel':翻译('unowned'),#无主
            'assignable':[{'id':成员['id'],'name':成员['name']} for 成员 in 可分配],#可分配
            'ownerDisabled':进行中 is True or 状态=='completed',#禁用改派
            'onOwner':自身._改派绑定(任务),#改派
            'editLabel':翻译('edit'),#编辑
            'onEdit':自身._开始编辑绑定(任务),#开始编辑
            'editDisabled':进行中,#禁用编辑
            'completeLabel':翻译('complete') if 状态=='in_progress' else None,#完成
            'onComplete':自身._动作绑定(任务,'complete') if 状态=='in_progress' else None,#完成
            'reopenLabel':翻译('reopen') if 状态=='completed' else None,#重开
            'onReopen':自身._动作绑定(任务,'reopen') if 状态=='completed' else None,#重开
            'deleteLabel':翻译('delete'),#删除
            'onDelete':自身._动作绑定(任务,'delete'),#删除
            'actionDisabled':进行中,#动作禁用
        }#卡片结束

    def _改派绑定(自身,任务):#绑定改派
        '返回改派回调'
        def 改派(所有者):#改派
            '改派或清空 owner'
            自身._改派(任务,所有者)#改派
        return 改派#回调

    def _开始编辑绑定(自身,任务):#绑定开始编辑
        '返回开始编辑回调'
        def 开始():#开始编辑
            '填入编辑草稿'
            自身.开始编辑(任务)#开始
        return 开始#回调

    def _动作绑定(自身,任务,动作):#绑定简单动作
        '返回 complete / reopen / delete 回调'
        def 执行():#执行动作
            '跑简单动作'
            自身._动作(任务,动作)#动作
        return 执行#回调

    def _改派(自身,任务,所有者):#改派
        '改派或清空 owner'
        会话=自身.属性['sessionId']#会话
        更新=自身.属性['updateTask'] if 'updateTask' in 自身.属性 else None#更新
        if 更新 is None:#无 RPC
            return#跳过
        def 操作():#操作
            '改派 RPC'
            请求={#请求
                'taskId':任务['id'],#任务 id
                'expectedRevision':任务['revision'],#期望版本
                'action':'reassign',#改派
            }#骨架
            if 所有者!='':
                请求['owner']=所有者#展开
            return 更新(会话,请求)#RPC
        自身.结算任务(任务['id'],操作)#结算

    def _动作(自身,任务,动作):#简单动作
        'complete / reopen / delete'
        会话=自身.属性['sessionId']#会话
        更新=自身.属性['updateTask'] if 'updateTask' in 自身.属性 else None#更新
        if 更新 is None:#无 RPC
            return#跳过
        def 操作():#操作
            '动作 RPC'
            return 更新(会话,{#更新
                'taskId':任务['id'],#任务 id
                'expectedRevision':任务['revision'],#期望版本
                'action':动作,#动作
            })#RPC
        自身.结算任务(任务['id'],操作)#结算
