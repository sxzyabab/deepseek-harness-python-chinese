__all__=['会话根','工作区标签','派生阶段']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键

def 空渲染槽(*位置参数,**关键字参数):
    """未注入槽渲染时不画。"""
    return None#不画

def 工作区标签(工作目录):
    """分隔符-only 路径回显原 cwd。"""
    if 工作目录 is None or 工作目录=='':#空
        return 工作目录#原样
    段=工作目录.replace('\\','/').rstrip('/').split('/')#分段
    基=段[-1] if len(段)>0 else ''#末段；判 length
    return 基 if 基!='' else 工作目录#空则原路径

def 派生阶段(会话标识,作曲阶段,打开态,摘要空白):
    """沉降：有会话且 blank+loading 且摘要未证 blank。"""
    沉降=会话标识 is not None and 作曲阶段=='blank' and 打开态=='loading' and 摘要空白 is not True#沉降
    英雄=会话标识 is None or (作曲阶段=='blank' and (打开态=='open' or 摘要空白 is True))#英雄
    if 沉降 is True:#沉降优先
        return 'settling'#沉降
    if 英雄 is True:#英雄
        return 'hero'#英雄
    return 'active'#活动

def 取打开态(快照):
    """openState。"""
    return 快照['openState'] if 'openState' in 快照 else None#打开

def 取作曲阶段(快照):
    """composerPhase。"""
    return 快照['composerPhase'] if 'composerPhase' in 快照 else None#相位

def 取未决(快照):
    """pending。空列表保留。"""
    列=快照['pending'] if 'pending' in 快照 else None#未决
    return 列 if 列 is not None else []#空则空表

def 取自身(快照):
    """快照原样。"""
    return 快照#原样

def 取阻断(值):
    """阻断原样。"""
    return 值#原样

class 会话根:#常驻会话骨架
    """英雄铬、composer 定位与会话链同树挂载。"""
    def __init__(自身,属性=None):
        """记下合成 props 与本地选择器态。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.选择器开=False#工作区菜单
        自身.待选工作区标识=None#刚挑的工作区
        自身.席位高度=0#composer 席高度

    def 更新(自身,属性):
        """刷新合成 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换选择器(自身):
        """翻转工作区选择器。"""
        自身.选择器开=not 自身.选择器开#翻转

    def 关闭选择器(自身):
        """关闭。"""
        自身.选择器开=False#关

    def 挑选工作区(自身,工作区标识):
        """关菜单、记下待选并调用 selectWorkspace。"""
        自身.选择器开=False#关
        自身.待选工作区标识=工作区标识#待选
        选定=自身.属性['selectWorkspace'] if 'selectWorkspace' in 自身.属性 else None#回调
        if 选定 is not None:#有
            选定(工作区标识)#打开空白会话

    def 清理待选(自身,会话工作区标识,工作区相位,待选仍在):
        """会话落盘或列表就绪且已删则清。"""
        if 自身.待选工作区标识 is None:#无待选
            return#无事
        if 会话工作区标识==自身.待选工作区标识 or (工作区相位=='ready' and 待选仍在 is False):#已落或消失
            自身.待选工作区标识=None#清

    def 记录席位高度(自身,高度):
        """供回到底部按钮 clearance。"""
        自身.席位高度=高度#记下

    def 渲染(自身):
        """与上游 JSX 同构的阶段/区/栏调度。"""
        属性=自身.属性#props
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话钩
        取会话列表=属性['useSessions'] if 'useSessions' in 属性 else None#列表钩
        用工作区=属性['useWorkspaces'] if 'useWorkspaces' in 属性 else None#工作区钩
        用输入=属性['useInput'] if 'useInput' in 属性 else None#输入钩
        用阻断=属性['useComposerBlock'] if 'useComposerBlock' in 属性 else None#阻断钩
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#单槽
        渲染链=属性['renderSlotChain'] if 'renderSlotChain' in 属性 else 空渲染槽#链
        会话标识=属性['sessionId'] if 'sessionId' in 属性 else None#会话 id
        打开态=用会话(取打开态) if 用会话 is not None else None#打开态
        作曲阶段=用会话(取作曲阶段) if 用会话 is not None else None#composer 相位
        未决=用会话(取未决) if 用会话 is not None else []#未决交互
        会话=用会话(取自身) if 用会话 is not None else None#整快照
        输入态=用输入(取自身) if 用输入 is not None else None#输入机
        def 取cwd(表):
            """byId[sessionId].cwd。表为 dict。"""
            if 会话标识 is None:#无会话
                return None#无
            册=表['byId'] if 'byId' in 表 else None#byId
            摘要=册[会话标识] if 册 is not None and 会话标识 in 册 else None#摘要
            return 摘要['cwd'] if 摘要 is not None and 'cwd' in 摘要 else None#cwd
        def 取blank(表):
            """byId[sessionId].blank。"""
            if 会话标识 is None:#无会话
                return None#无
            册=表['byId'] if 'byId' in 表 else None#byId
            摘要=册[会话标识] if 册 is not None and 会话标识 in 册 else None#摘要
            return 摘要['blank'] if 摘要 is not None and 'blank' in 摘要 else None#blank
        工作目录=取会话列表(取cwd) if 取会话列表 is not None else None#cwd
        摘要空白=取会话列表(取blank) if 取会话列表 is not None else None#blank
        工作区=用工作区(取自身) if 用工作区 is not None else {'items':[],'phase':'loading'}#工作区表
        作曲阻断=用阻断(取阻断) if 用阻断 is not None else None#阻断值
        条目=工作区['items'] if 'items' in 工作区 and 工作区['items'] is not None else []#工作区列表
        会话工作区=None#所属
        if 会话标识 is not None:#有会话
            for 项 in 条目:#找所属
                标识列表=项['sessionIds'] if 'sessionIds' in 项 and 项['sessionIds'] is not None else []#会话集
                if 会话标识 in 标识列表:#命中
                    会话工作区=项#记下
                    break#停
        待选工作区=None#待选对象
        for 项 in 条目:#找待选
            if ('workspaceId' in 项) and 项['workspaceId']==自身.待选工作区标识:#命中
                待选工作区=项#记下
                break#停
        会话工作区标识=会话工作区['workspaceId'] if 会话工作区 is not None and 'workspaceId' in 会话工作区 else None#属主
        工作区相位=工作区['phase'] if 'phase' in 工作区 else None#相位
        自身.清理待选(会话工作区标识,工作区相位,待选工作区 is not None)#清 pending
        阶段=派生阶段(会话标识,作曲阶段,打开态,摘要空白)#相位
        英雄=阶段=='hero'#是否英雄
        区=None if 会话 is None or 输入态 is None else {'session':会话,'input':输入态}#InputZone
        芯片标题=待选工作区['title'] if 待选工作区 is not None and 'title' in 待选工作区 else None#优先待选
        if 芯片标题 is None and 会话标识 is not None:#非冷启动
            芯片标题=会话工作区['title'] if 会话工作区 is not None and 'title' in 会话工作区 else None#所属标题
            if 芯片标题 is None and 工作区相位!='ready' and 工作目录 is not None and 工作目录!='':#列表未就绪用 cwd
                芯片标题=工作区标签(工作目录)#桥接
        惰性=会话标识 is None or (英雄 is True and 芯片标题 is None)#无工作区
        阻断中=惰性 is False and 作曲阻断 is not None#阻断
        栏属主={'variant':'hero' if 英雄 is True else 'composer'}#变体
        if 惰性 is True:#无工作区触发
            栏属主.update({'disabled':True,'placeholder':翻译('placeholder.workspace'),'workspacePickerOpen':自身.选择器开,'onRequestWorkspace':自身.切换选择器})#惰性
        elif 阻断中 is True:#阻断
            栏属主.update({'blocked':作曲阻断,'placeholder':作曲阻断['reason'] if 'reason' in 作曲阻断 else None})#阻断原因
        elif 英雄 is True:#英雄占位
            栏属主['placeholder']=翻译('placeholder.hero')#英雄
        栏属主['overlay']=渲染槽('conversation.input.overlay',{})#浮动层
        栏属主['leftItems']=None if 区 is None else 渲染槽('conversation.input.left',区)#左
        栏属主['rightItems']=None if 区 is None else 渲染槽('conversation.input.right',区)#右
        栏属主['footer']=None if 英雄 is True or 区 is None else 渲染槽('conversation.composer.dock',区)#统计带
        英雄工作区行=None#英雄行
        if 英雄 is True:#英雄才画
            选中标识=自身.待选工作区标识 if 自身.待选工作区标识 is not None else 会话工作区标识#选中
            英雄工作区行={#结构
                'className':'heroWorkspaceRow',#行
                'chip':{'label':芯片标题,'menuOpen':自身.选择器开,'onClick':自身.切换选择器,'t':翻译},#芯片
                'workspaceSlot':渲染槽('conversation.hero.workspace',{#选择器
                    'open':自身.选择器开,#开
                    'selectedId':选中标识,#选中
                    'onPick':自身.挑选工作区,#挑
                    'onClose':自身.关闭选择器,#关
                }),#结束选择器
                'agentPreset':渲染槽('conversation.hero.agentPreset',{}),#预设
            }#结束行
        输入栏=渲染槽('conversation.composer.bar',栏属主)#栏
        作曲栈={#栈
            'className':('composerStack','composerHero') if 英雄 is True else ('composerStack',),#类
            'glow':英雄,#辉光
            'shell':英雄,#英雄壳
            'workspaceRow':英雄工作区行,#工作区行
            'dock':None if 区 is None else 渲染槽('conversation.input.dock',区),#停靠
            'bar':输入栏,#栏
        }#结束栈
        作曲=渲染链('conversation.composer',{'interactions':未决,'session':会话},{'fallback':作曲栈,'overlay':True})#链
        return {#根结构
            'className':'root',#根
            'data-phase':阶段,#相位
            'composerHeight':自身.席位高度,#席高
            'header':渲染槽('conversation.session.header',{}),#页眉
            'scrollBody':{#滚动体
                'data-conversation-scroll':'',#滚动口
                'session':渲染槽('conversation.session',{}),#主体
                'composerSeat':{'data-composer-seat':'','composer':作曲},#席
            },#结束滚动体
        }#结束根

    def __call__(自身,属性=None):
        """对齐 React。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
