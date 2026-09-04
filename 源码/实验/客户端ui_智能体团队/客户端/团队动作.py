"""渲染 live Team roster 与 compare-and-set 任务板（无头结构树）。

对齐上游 `client-ui-agent-team/src/client/TeamAction.tsx`。公开面仅中文名。
无真 React：返回结构树字典；状态机驻留在实例上。
"""
from ....内核.智能体循环.辅助 import 解开#等待承诺

__all__=['团队动作','任务表单','拆分项','失败文案']#仅中文公开名

空草稿={'subject':'','description':'','blockers':'','scopes':''}#空草稿

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 拆分项(值):#逗号拆分去重
    """逗号拆分去重。"""
    return list(dict.fromkeys(项.strip() for 项 in 值.split(',') if 项.strip()))#拆分去重

def 失败文案(错误):#失败文案
    """任一种载体的一行失败文案。"""
    return str(取字段(错误,'message'))+' ('+str(取字段(错误,'code'))+')'#拼接码

def 任务状态键(状态):#任务状态键
    """任务状态 → 文案键。"""
    if 状态=='pending':#待处理
        return 'status.pending'#键
    if 状态=='in_progress':#进行中
        return 'status.in_progress'#键
    if 状态=='completed':#已完成
        return 'status.completed'#键
    return 'status.completed'#删除当完成键

def 成员状态键(状态):#成员状态键
    """成员状态 → 文案键。"""
    表={#映射
        'running':'memberStatus.running',#运行中
        'idle':'memberStatus.idle',#空闲
        'inactive':'memberStatus.inactive',#未运行
        'provisioning':'memberStatus.provisioning',#准备中
        'failed':'memberStatus.failed',#失败
    }#表结束
    return 表.get(状态,状态)#键

class 任务表单:#任务表单结构树
    """标题/详情/依赖/写范围四字段表单。"""
    def __init__(自身,草稿,进行中,保存,取消,翻译):#构造
        """记下草稿与回调。"""
        自身.draft=草稿#草稿
        自身.pending=进行中#进行中
        自身.onSave=保存#保存
        自身.onCancel=取消#取消
        自身.t=翻译#翻译

    def 改字段(自身,键,值):#改字段
        """写回草稿字段。"""
        自身.draft[键]=值#写字段

    def 渲染(自身):#结构树
        """表单树。"""
        翻译=自身.t if callable(自身.t) else (lambda 键,_=None:键)#文案
        禁用保存=自身.pending or 自身.draft['subject'].strip()=='' or 自身.draft['description'].strip()==''#禁用
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
            'onSubject':lambda 值:自身.改字段('subject',值),#改标题
            'onDescription':lambda 值:自身.改字段('description',值),#改详情
            'onBlockers':lambda 值:自身.改字段('blockers',值),#改依赖
            'onScopes':lambda 值:自身.改字段('scopes',值),#改写范围
            'onSave':自身.onSave,#保存
            'onCancel':自身.onCancel,#取消
            'cssModule':'团队动作.module.css',#样式
        }#视图结束

class 团队动作:#标题栏 Team 动作
    """渲染 live Team roster 与 compare-and-set 任务板。"""
    def __init__(自身,属性=None):#构造
        """记下 props 与初始状态。"""
        自身.属性=属性 or {}#合成
        自身.打开=False#面板是否打开
        自身.加载中=False#加载中
        自身.视图=None#当前视图
        自身.错误=None#错误行
        自身.创建中=False#是否在创建
        自身.创建草稿=dict(空草稿)#创建草稿
        自身.编辑中=None#编辑中任务 id
        自身.编辑草稿=dict(空草稿)#编辑草稿
        自身.进行中任务=set()#进行中任务
        自身._会话引用=取字段(自身.属性,'sessionId')#当前会话
        自身._刷新代数=0#刷新代数

    def 更新(自身,属性):#刷新 props
        """会话切换则重置面板状态。"""
        新会话=取字段(属性,'sessionId')#新会话
        旧会话=自身._会话引用#旧会话
        自身.属性=属性 or {}#新 props
        自身._会话引用=新会话#同步
        if 新会话!=旧会话:#会话切换
            自身._重置状态()#重置

    def _重置状态(自身):#重置状态
        """会话切换重置。"""
        自身._刷新代数+=1#推进代
        自身.打开=False#关面板
        自身.加载中=False#清加载
        自身.视图=None#清视图
        自身.错误=None#清错误
        自身.创建中=False#清创建
        自身.创建草稿=dict(空草稿)#清空创建草稿
        自身.编辑中=None#清编辑
        自身.编辑草稿=dict(空草稿)#清空编辑草稿
        自身.进行中任务=set()#清进行中

    def _翻译(自身):#取翻译
        """取翻译函数。"""
        return 取字段(自身.属性,'t',lambda 键,_=None:键)#文案

    def 刷新(自身):#刷新视图
        """拉取总览；代数过期则丢弃。"""
        会话=取字段(自身.属性,'sessionId')#请求时会话
        自身._刷新代数+=1#推进代
        代数=自身._刷新代数#本代
        自身.加载中=True#进入加载
        加载=取字段(自身.属性,'load')#加载动作
        结果=解开(加载(会话)) if callable(加载) else {'ok':False,'error':{'code':'missing','message':'no load'}}#拉总览
        if 自身._会话引用!=会话 or 自身._刷新代数!=代数:#过期
            return False#过期
        自身.加载中=False#结束加载
        if 取字段(结果,'ok'):#成功
            自身.视图=取字段(结果,'value')#写入视图
            自身.错误=None#清错误
            return True#成功
        自身.错误=失败文案(取字段(结果,'error'))#写错误
        return False#失败

    def _使刷新失效(自身):#使在途刷新失效
        """推进代数并清加载。"""
        自身._刷新代数+=1#推进代
        自身.加载中=False#清加载

    def 结算任务(自身,任务键,操作):#结算一次任务操作
        """跑任务变更并处理冲突/拒绝。"""
        会话=取字段(自身.属性,'sessionId')#请求时会话
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
        """结算任务操作主体。"""
        结果=解开(操作())#跑操作
        if 自身._会话引用!=会话:#会话已变
            return None#空
        if not 取字段(结果,'ok'):#传输失败
            自身.错误=失败文案(取字段(结果,'error'))#写错误
            return None#空
        值=取字段(结果,'value')#业务值
        if not 取字段(值,'ok'):#业务拒绝
            return 自身._处理业务拒绝(会话,值)#拒绝路径
        自身.错误=None#清错误
        自身.刷新()#成功后刷新
        if 自身._会话引用!=会话:#会话已变
            return None#空
        return 取字段(值,'value')#返回任务

    def _处理业务拒绝(自身,会话,值):#业务拒绝
        """冲突则重载；其它拒绝写错误行。"""
        错误=取字段(值,'error')#错误体
        if 取字段(错误,'code')=='team-task-conflict':#冲突
            已重载=自身.刷新()#冲突则重载
            if 自身._会话引用!=会话:#会话已变
                return None#空
            if 已重载:#提示冲突
                自身.错误=自身._翻译()('conflict')#冲突文案
        else:#其它拒绝
            自身.错误=失败文案(错误)#业务拒绝文案
        return None#空

    def 提交创建(自身):#提交创建
        """提交新建任务。"""
        标题=自身.创建草稿['subject'].strip()#标题
        描述=自身.创建草稿['description'].strip()#描述
        if 标题=='' or 描述=='':#空则跳过
            return#跳过
        会话=取字段(自身.属性,'sessionId')#会话
        创建=取字段(自身.属性,'createTask')#创建动作
        def 操作():#操作
            """建任务 RPC。"""
            return 创建(会话,{#建任务
                'subject':标题,#标题
                'description':描述,#描述
                'blockedBy':拆分项(自身.创建草稿['blockers']),#依赖
                'writeScopes':拆分项(自身.创建草稿['scopes']),#写范围
            })#RPC 结束
        已创建=自身.结算任务('create',操作)#结算
        if 已创建 is None:#失败
            return#返回
        自身.创建草稿=dict(空草稿)#清空草稿
        自身.创建中=False#退出创建

    def 开始编辑(自身,任务):#开始编辑
        """填入编辑草稿。"""
        自身.编辑中=取字段(任务,'id')#编辑目标
        自身.编辑草稿={#填草稿
            'subject':取字段(任务,'subject'),#标题
            'description':取字段(任务,'description'),#详情
            'blockers':', '.join(取字段(任务,'blockedBy') or []),#依赖串
            'scopes':', '.join(取字段(任务,'writeScopes') or []),#写范围串
        }#草稿结束

    def 提交编辑(自身,任务):#提交编辑
        """先编辑文本，必要时再改依赖。"""
        会话=取字段(自身.属性,'sessionId')#请求时会话
        更新=取字段(自身.属性,'updateTask')#更新动作
        def 编辑操作():#编辑文本
            """编辑 RPC。"""
            return 更新(会话,{#编辑
                'taskId':取字段(任务,'id'),#任务 id
                'expectedRevision':取字段(任务,'revision'),#期望版本
                'action':'edit',#编辑动作
                'subject':自身.编辑草稿['subject'].strip(),#新标题
                'description':自身.编辑草稿['description'].strip(),#新详情
                'writeScopes':拆分项(自身.编辑草稿['scopes']),#新写范围
            })#RPC 结束
        已编辑=自身.结算任务(取字段(任务,'id'),编辑操作)#结算
        if 已编辑 is None:#失败
            return#返回
        依赖=拆分项(自身.编辑草稿['blockers'])#新依赖
        旧依赖=取字段(已编辑,'blockedBy') or []#旧依赖
        if len(依赖)==len(旧依赖) and all(依赖[下标]==旧依赖[下标] for 下标 in range(len(依赖))):#依赖未变
            自身.编辑中=None#退出编辑
            return#结束
        def 依赖操作():#再改依赖
            """改依赖 RPC。"""
            return 更新(会话,{#改依赖
                'taskId':取字段(任务,'id'),#任务 id
                'expectedRevision':取字段(已编辑,'revision'),#新版本
                'action':'set_dependencies',#改依赖
                'blockedBy':依赖,#依赖列表
            })#RPC 结束
        依赖任务=自身.结算任务(取字段(任务,'id'),依赖操作)#结算
        if 依赖任务 is None:#失败
            return#返回
        自身.编辑中=None#退出编辑

    def 切换面板(自身):#切换面板
        """打开或关闭面板；打开时刷新。"""
        自身.打开=not 自身.打开#切换
        if 自身.打开:#打开时刷新
            自身.刷新()#刷新

    def 渲染(自身):#结构树
        """Team 动作根树。"""
        翻译=自身._翻译()#文案
        视图=自身.视图#当前视图
        成员们=取字段(视图,'members') or [] if 视图 is not None else []#成员
        队友们=[成员 for 成员 in 成员们 if 取字段(成员,'role')=='teammate']#teammate 列表
        return {#根
            'type':'team-action',#类型
            'open':自身.打开,#是否打开
            'triggerLabel':翻译('trigger'),#触发文案
            'teammateCount':len(队友们),#队友数
            'onToggle':自身.切换面板,#切换
            'panel':自身._渲染面板(翻译,视图,成员们) if 自身.打开 else None,#面板
            'cssModule':'团队动作.module.css',#样式
        }#根结束

    def _渲染面板(自身,翻译,视图,成员们):#渲染面板
        """对话框面板树。"""
        return {#面板
            'type':'team-panel',#类型
            'title':翻译('trigger'),#标题
            'refreshLabel':翻译('refresh'),#刷新
            'closeLabel':翻译('close'),#关闭
            'onRefresh':自身.刷新,#刷新
            'onClose':lambda:setattr(自身,'打开',False),#关闭
            'error':自身.错误,#错误行
            'loadingNotice':翻译('loading') if 自身.加载中 and 视图 is None else None,#加载提示
            'body':自身._渲染正文(翻译,视图,成员们) if 视图 is not None else None,#正文
        }#面板结束

    def _渲染正文(自身,翻译,视图,成员们):#渲染正文
        """roster + 任务板。"""
        可分配=[成员 for 成员 in 成员们 if 取字段(成员,'status') not in ('failed','provisioning')]#可分配
        任务们=取字段(视图,'tasks') or []#任务
        return {#正文
            'rosterTitle':翻译('roster'),#成员区标题
            'members':[自身._渲染成员(翻译,成员) for 成员 in 成员们],#成员们
            'tasksTitle':翻译('tasks'),#任务区标题
            'createLabel':翻译('create'),#新建
            'onStartCreate':lambda:setattr(自身,'创建中',True),#开始创建
            'createForm':自身._创建表单(翻译) if 自身.创建中 else None,#创建表单
            'emptyNotice':翻译('empty') if len(任务们)==0 and not 自身.创建中 else None,#空提示
            'tasks':[自身._渲染任务(翻译,任务,可分配) for 任务 in 任务们],#任务们
        }#正文结束

    def _创建表单(自身,翻译):#创建表单
        """新建任务表单。"""
        return 任务表单(#表单
            自身.创建草稿,#草稿
            'create' in 自身.进行中任务,#进行中
            自身.提交创建,#保存
            lambda:setattr(自身,'创建中',False),#取消
            翻译,#翻译
        ).渲染()#渲染

    def _渲染成员(自身,翻译,成员):#渲染成员
        """成员行。"""
        会话=取字段(自身.属性,'sessionId')#会话
        打开=取字段(自身.属性,'openTeammate')#打开动作
        模型=取字段(成员,'model')#模型
        副文=翻译(成员状态键(取字段(成员,'status')))#状态文案
        if 模型 is not None:#有模型
            副文=副文+' · '+翻译('model')+': '+str(模型)#拼模型
        禁用=取字段(成员,'role')=='lead' or 取字段(成员,'status') in ('failed','provisioning')#禁用
        def 点击():#打开 teammate
            """打开子会话。"""
            if not callable(打开):#无动作
                return#返回
            try:#试开
                解开(打开(会话,成员))#打开
            except Exception as 错误:#写错误
                自身.错误=str(错误)#错误行
        return {#成员行
            'id':取字段(成员,'id'),#id
            'name':取字段(成员,'name'),#名
            'status':取字段(成员,'status'),#状态
            'statusLabel':副文,#副文
            'diagnostics':list(取字段(成员,'diagnostics') or []),#诊断
            'disabled':禁用,#禁用
            'openTitle':翻译('open') if 取字段(成员,'role')=='teammate' else None,#打开提示
            'onOpen':点击,#点击
        }#行结束

    def _渲染任务(自身,翻译,任务,可分配):#渲染任务
        """一条任务或编辑表单。"""
        标识=取字段(任务,'id')#任务 id
        if 自身.编辑中==标识:#编辑中
            return 任务表单(#表单
                自身.编辑草稿,#草稿
                标识 in 自身.进行中任务,#进行中
                lambda:自身.提交编辑(任务),#保存
                lambda:setattr(自身,'编辑中',None),#取消
                翻译,#翻译
            ).渲染()#渲染
        return 自身._任务卡片(翻译,任务,可分配)#卡片

    def _任务卡片(自身,翻译,任务,可分配):#任务卡片
        """只读任务卡片与动作。"""
        标识=取字段(任务,'id')#任务 id
        状态=取字段(任务,'status')#状态
        进行中=标识 in 自身.进行中任务#进行中
        元数据=[str(标识)]#元数据行
        if 状态=='pending':#待处理
            元数据.append(翻译('ready') if 取字段(任务,'ready') else 翻译('blocked'))#就绪/阻塞
        依赖=取字段(任务,'blockedBy') or []#依赖
        if len(依赖)>0:#有依赖
            元数据.append(翻译('blockedBy')+': '+', '.join(依赖))#依赖
        范围=取字段(任务,'writeScopes') or []#写范围
        if len(范围)>0:#有写范围
            元数据.append(翻译('writeScopes')+': '+', '.join(范围))#写范围
        return {#卡片
            'type':'team-task',#类型
            'id':标识,#id
            'subject':取字段(任务,'subject'),#标题
            'statusLabel':翻译(任务状态键(状态)),#状态
            'description':取字段(任务,'description'),#详情
            'meta':元数据,#元数据
            'warnings':list(取字段(任务,'writeScopeWarnings') or []),#警告
            'ownerLabel':翻译('owner'),#owner 标签
            'ownerValue':取字段(任务,'ownerName') or '',#当前 owner
            'unownedLabel':翻译('unowned'),#无主
            'assignable':[{'id':取字段(成员,'id'),'name':取字段(成员,'name')} for 成员 in 可分配],#可分配
            'ownerDisabled':进行中 or 状态=='completed',#禁用改派
            'onOwner':lambda 所有者:自身._改派(任务,所有者),#改派
            'editLabel':翻译('edit'),#编辑
            'onEdit':lambda:自身.开始编辑(任务),#开始编辑
            'editDisabled':进行中,#禁用编辑
            'completeLabel':翻译('complete') if 状态=='in_progress' else None,#完成
            'onComplete':(lambda:自身._动作(任务,'complete')) if 状态=='in_progress' else None,#完成
            'reopenLabel':翻译('reopen') if 状态=='completed' else None,#重开
            'onReopen':(lambda:自身._动作(任务,'reopen')) if 状态=='completed' else None,#重开
            'deleteLabel':翻译('delete'),#删除
            'onDelete':lambda:自身._动作(任务,'delete'),#删除
            'actionDisabled':进行中,#动作禁用
        }#卡片结束

    def _改派(自身,任务,所有者):#改派
        """改派或清空 owner。"""
        会话=取字段(自身.属性,'sessionId')#会话
        更新=取字段(自身.属性,'updateTask')#更新
        def 操作():#操作
            """改派 RPC。"""
            请求={#请求
                'taskId':取字段(任务,'id'),#任务 id
                'expectedRevision':取字段(任务,'revision'),#期望版本
                'action':'reassign',#改派
            }#骨架
            if 所有者!='':#有 owner
                请求['owner']=所有者#展开
            return 更新(会话,请求)#RPC
        自身.结算任务(取字段(任务,'id'),操作)#结算

    def _动作(自身,任务,动作):#简单动作
        """complete / reopen / delete。"""
        会话=取字段(自身.属性,'sessionId')#会话
        更新=取字段(自身.属性,'updateTask')#更新
        def 操作():#操作
            """动作 RPC。"""
            return 更新(会话,{#更新
                'taskId':取字段(任务,'id'),#任务 id
                'expectedRevision':取字段(任务,'revision'),#期望版本
                'action':动作,#动作
            })#RPC
        自身.结算任务(取字段(任务,'id'),操作)#结算
