"""会话列骨架：英雄铬、composer 定位与会话链。

对齐上游 `ui-conversation/src/client/skeleton/ConversationRoot.tsx`。公开面仅中文名。
席位高度经回调引用写入滚动体 `--dsh-composer-height`。
"""

__all__=['会话根','工作区标签','派生阶段']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 工作区标签(工作目录):#芯片 basename
    """分隔符-only 路径回显原 cwd。"""
    if not 工作目录:#空
        return 工作目录#原样
    段=工作目录.replace('\\','/').rstrip('/').split('/')#分段
    基=段[-1] if 段 else ''#末段
    return 基 if 基!='' else 工作目录#空则原路径

def 派生阶段(会话标识,作曲阶段,打开态,摘要空白):#hero/settling/active
    """沉降：有会话且 blank+loading 且摘要未证 blank。"""
    沉降=(
        会话标识 is not None
        and 作曲阶段=='blank'
        and 打开态=='loading'
        and 摘要空白 is not True
    )#沉降
    英雄=(
        会话标识 is None
        or (作曲阶段=='blank' and (打开态=='open' or 摘要空白 is True))
    )#英雄
    if 沉降:#沉降优先
        return 'settling'#沉降
    if 英雄:#英雄
        return 'hero'#英雄
    return 'active'#活动

class 会话根:#常驻会话骨架
    """英雄铬、composer 定位与会话链同树挂载。"""

    def __init__(自身,属性=None):#记下 props
        """记下合成 props 与本地选择器态。"""
        自身.属性=属性 or {}#合成
        自身.选择器开=False#工作区菜单
        自身.待选工作区标识=None#刚挑的工作区
        自身.席位高度=0#composer 席高度

    def 更新(自身,属性):#刷新 props
        """刷新合成 props。"""
        自身.属性=属性 or {}#新

    def 切换选择器(自身):#菜单开合
        """翻转工作区选择器。"""
        自身.选择器开=not 自身.选择器开#翻转

    def 关闭选择器(自身):#关菜单
        """关闭。"""
        自身.选择器开=False#关

    def 挑选工作区(自身,工作区标识):#选工作区
        """关菜单、记下待选并调用 selectWorkspace。"""
        自身.选择器开=False#关
        自身.待选工作区标识=工作区标识#待选
        选定=取字段(自身.属性,'selectWorkspace')#回调
        if callable(选定):#有
            选定(工作区标识)#打开空白会话

    def 清理待选(自身,会话工作区标识,工作区相位,待选仍在):#清 pending
        """会话落盘或列表就绪且已删则清。"""
        if 自身.待选工作区标识 is None:#无待选
            return#无事
        if 会话工作区标识==自身.待选工作区标识 or (工作区相位=='ready' and not 待选仍在):#已落或消失
            自身.待选工作区标识=None#清

    def 记录席位高度(自身,高度):#席高度
        """供回到底部按钮 clearance。"""
        自身.席位高度=高度#记下

    def 渲染(自身):#结构树
        """与上游 JSX 同构的阶段/区/栏调度。"""
        属性=自身.属性#props
        翻译=取字段(属性,'t',lambda 键,**_:键)#文案
        用会话=取字段(属性,'useSession')#会话钩
        用会话们=取字段(属性,'useSessions')#列表钩
        用工作区=取字段(属性,'useWorkspaces')#工作区钩
        用输入=取字段(属性,'useInput')#输入钩
        用阻断=取字段(属性,'useComposerBlock')#阻断钩
        渲染槽=取字段(属性,'renderSlot',lambda *a,**k:None)#单槽
        渲染链=取字段(属性,'renderSlotChain',lambda *a,**k:None)#链
        会话标识=取字段(属性,'sessionId')#会话 id

        def 选(钩,选择器,缺省=None):#读快照
            """钩可缺席。"""
            if not callable(钩):#无钩
                return 缺省#缺
            return 钩(选择器)#选

        打开态=选(用会话,lambda s:取字段(s,'openState'))#打开态
        作曲阶段=选(用会话,lambda s:取字段(s,'composerPhase'))#composer 相位
        未决=选(用会话,lambda s:取字段(s,'pending') or [],[])#未决交互
        会话=选(用会话,lambda s:s)#整快照
        输入态=选(用输入,lambda s:s)#输入机
        工作目录=选(用会话们,lambda s:None if 会话标识 is None else 取字段(取字段(取字段(s,'byId'),会话标识),'cwd'))#cwd
        摘要空白=选(用会话们,lambda s:None if 会话标识 is None else 取字段(取字段(取字段(s,'byId'),会话标识),'blank'))#blank
        工作区=选(用工作区,lambda s:s,{'items':[],'phase':'loading'})#工作区表
        作曲阻断=选(用阻断,lambda b:b)#阻断值

        条目=取字段(工作区,'items') or []#工作区列表
        会话工作区=None#所属
        if 会话标识 is not None:#有会话
            for 项 in 条目:#找所属
                if 会话标识 in (取字段(项,'sessionIds') or []):#命中
                    会话工作区=项#记下
                    break#停
        待选工作区=None#待选对象
        for 项 in 条目:#找待选
            if 取字段(项,'workspaceId')==自身.待选工作区标识:#命中
                待选工作区=项#记下
                break#停
        自身.清理待选(取字段(会话工作区,'workspaceId'),取字段(工作区,'phase'),待选工作区 is not None)#清 pending

        阶段=派生阶段(会话标识,作曲阶段,打开态,摘要空白)#相位
        英雄=阶段=='hero'#是否英雄
        区=None if 会话 is None or 输入态 is None else {'session':会话,'input':输入态}#InputZone

        芯片标题=取字段(待选工作区,'title')#优先待选
        if 芯片标题 is None and 会话标识 is not None:#非冷启动
            芯片标题=取字段(会话工作区,'title')#所属标题
            if 芯片标题 is None and 取字段(工作区,'phase')!='ready' and 工作目录:#列表未就绪用 cwd
                芯片标题=工作区标签(工作目录) if 工作目录!='' else None#桥接

        惰性=会话标识 is None or (英雄 and 芯片标题 is None)#无工作区
        阻断中=not 惰性 and 作曲阻断 is not None#阻断
        栏属主={'variant':'hero' if 英雄 else 'composer'}#变体
        if 惰性:#无工作区触发
            栏属主.update({'disabled':True,'placeholder':翻译('placeholder.workspace'),'workspacePickerOpen':自身.选择器开,'onRequestWorkspace':自身.切换选择器})#惰性
        elif 阻断中:#阻断
            栏属主.update({'blocked':作曲阻断,'placeholder':取字段(作曲阻断,'reason')})#阻断原因
        elif 英雄:#英雄占位
            栏属主['placeholder']=翻译('placeholder.hero')#英雄
        栏属主['overlay']=渲染槽('conversation.input.overlay',{})#浮动层
        栏属主['leftItems']=None if 区 is None else 渲染槽('conversation.input.left',区)#左
        栏属主['rightItems']=None if 区 is None else 渲染槽('conversation.input.right',区)#右
        栏属主['footer']=None if 英雄 or 区 is None else 渲染槽('conversation.composer.dock',区)#统计带

        英雄工作区行=None#英雄行
        if 英雄:#英雄才画
            英雄工作区行={#结构
                'className':'heroWorkspaceRow',#行
                'chip':{'label':芯片标题,'menuOpen':自身.选择器开,'onClick':自身.切换选择器,'t':翻译},#芯片
                'workspaceSlot':渲染槽('conversation.hero.workspace',{#选择器
                    'open':自身.选择器开,#开
                    'selectedId':自身.待选工作区标识 or 取字段(会话工作区,'workspaceId'),#选中
                    'onPick':自身.挑选工作区,#挑
                    'onClose':自身.关闭选择器,#关
                }),#结束选择器
                'agentPreset':渲染槽('conversation.hero.agentPreset',{}),#预设
            }#结束行

        输入栏=渲染槽('conversation.composer.bar',栏属主)#栏
        作曲栈={#栈
            'className':('composerStack','composerHero') if 英雄 else ('composerStack',),#类
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
