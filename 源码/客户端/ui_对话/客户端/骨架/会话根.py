
__all__=['会话根','工作区标签','派生相位','芯片标题']#仅中文公开名

def 恒等翻译(键,参数=None):
    """无文案表时返回键本身。"""
    return 键#键

def 空渲染槽(*位置参数,**关键字参数):
    """未注入槽渲染时不画。"""
    return None#不画

def 工作区标签(工作目录):
    """仅分隔符路径回显原 cwd。"""
    if 工作目录 is None or 工作目录=='':#空
        return ''#空
    规范化=工作目录.replace('\\','/').rstrip('/')#统一
    if 规范化=='' or 规范化.endswith(':'):#根或盘符
        return 工作目录#原样
    基=规范化.rsplit('/',1)[-1]#末段
    return 基 if 基!='' else 工作目录#基名或原样

def 派生相位(会话标识,撰写相位,打开态,摘要空白):
    """settling / hero / active。"""
    落定中=会话标识 is not None and 撰写相位=='blank' and 打开态=='loading' and 摘要空白 is not True#落定
    英雄=会话标识 is None or (撰写相位=='blank' and (打开态=='open' or 摘要空白 is True))#英雄
    if 落定中 is True:#落定
        return 'settling'#落定
    if 英雄 is True:#英雄
        return 'hero'#英雄
    return 'active'#活跃

def 芯片标题(待选工作区,会话标识,会话工作区,工作区快照,工作目录):
    """pending → 无会话占位 → 会话工作区 → cwd 桥 → 占位。工作区为 dict。"""
    if 待选工作区 is not None:#刚选
        return 待选工作区['title'] if 'title' in 待选工作区 else None#标题
    if 会话标识 is None:#冷启动
        return None#占位
    if 会话工作区 is not None:#列表有属主
        return 会话工作区['title'] if 'title' in 会话工作区 else None#标题
    相位=工作区快照['phase'] if 工作区快照 is not None and 'phase' in 工作区快照 else None#列表相位
    if 相位=='ready' or 工作目录 is None or 工作目录=='':#就绪或无 cwd
        return None#占位
    return 工作区标签(工作目录)#cwd 桥

def 取自身(快照):
    """快照原样。"""
    return 快照#原样

def 取阻断(值):
    """阻断原样。"""
    return 值#原样

class 会话根:#常驻会话骨架
    """推导相位、惰性撰写与座位结构树。"""
    def __init__(自身,属性=None):
        """记下合成 props 与挑选态。"""
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.挑选打开=False#挑选菜单
        自身.待定工作区=None#刚选工作区

    def 更新(自身,属性):
        """刷新 props。"""
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换挑选(自身):
        """翻转工作区菜单。"""
        自身.挑选打开=not 自身.挑选打开#翻

    def 渲染(自身):
        """产出根结构：相位、英雄行、撰写座位。"""
        属性=自身.属性#props
        会话标识=属性['sessionId'] if 'sessionId' in 属性 else None#会话
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话钩
        取会话列表=属性['useSessions'] if 'useSessions' in 属性 else None#列表钩
        用工作区=属性['useWorkspaces'] if 'useWorkspaces' in 属性 else None#工作区钩
        用输入=属性['useInput'] if 'useInput' in 属性 else None#输入钩
        用阻断=属性['useComposerBlock'] if 'useComposerBlock' in 属性 else None#阻断钩
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#单槽
        渲染链=属性['renderSlotChain'] if 'renderSlotChain' in 属性 else 空渲染槽#链槽
        选工作区=属性['selectWorkspace'] if 'selectWorkspace' in 属性 else None#选工作区
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        会话=用会话(取自身) if 用会话 is not None else None#会话快照
        打开态=会话['openState'] if 会话 is not None and 'openState' in 会话 else None#打开
        撰写相位=会话['composerPhase'] if 会话 is not None and 'composerPhase' in 会话 else None#撰写
        待审列=会话['pending'] if 会话 is not None and 'pending' in 会话 else None#待审
        待审=待审列 if 待审列 is not None else []#空则空表
        输入态=用输入(取自身) if 用输入 is not None else None#输入
        工作目录=None#cwd
        摘要空白=None#blank
        if 取会话列表 is not None and 会话标识 is not None:#有列表
            def 取cwd(表):
                """byId[sessionId].cwd。表为 dict。"""
                册=表['byId'] if 'byId' in 表 else None#byId
                摘要=册[会话标识] if 册 is not None and 会话标识 in 册 else None#摘要
                return 摘要['cwd'] if 摘要 is not None and 'cwd' in 摘要 else None#cwd
            def 取blank(表):
                """byId[sessionId].blank。"""
                册=表['byId'] if 'byId' in 表 else None#byId
                摘要=册[会话标识] if 册 is not None and 会话标识 in 册 else None#摘要
                return 摘要['blank'] if 摘要 is not None and 'blank' in 摘要 else None#blank
            工作目录=取会话列表(取cwd)#cwd
            摘要空白=取会话列表(取blank)#blank
        工作区快照=用工作区(取自身) if 用工作区 is not None else {'items':[],'phase':'ready'}#工作区
        阻断=用阻断(取阻断) if 用阻断 is not None else None#阻断
        条目列=工作区快照['items'] if 'items' in 工作区快照 else None#列表
        条目=条目列 if 条目列 is not None else []#空则空表
        会话工作区=None#属主
        if 会话标识 is not None:#有会话
            for 项 in 条目:#找属主
                标识列表=项['sessionIds'] if 'sessionIds' in 项 and 项['sessionIds'] is not None else []#会话集
                if 会话标识 in 标识列表:#命中
                    会话工作区=项#记下
                    break#停
        待选=None#待定项
        if 自身.待定工作区 is not None:#有待定
            for 项 in 条目:#找
                if ('workspaceId' in 项) and 项['workspaceId']==自身.待定工作区:#命中
                    待选=项#记下
                    break#停
            属主标识=会话工作区['workspaceId'] if 会话工作区 is not None and 'workspaceId' in 会话工作区 else None#属主
            相位名=工作区快照['phase'] if 'phase' in 工作区快照 else None#相位
            if 属主标识==自身.待定工作区:#已落地
                自身.待定工作区=None#清
                待选=None#清
            elif 相位名=='ready' and 待选 is None:#已删
                自身.待定工作区=None#清
        相位=派生相位(会话标识,撰写相位,打开态,摘要空白)#相位
        英雄=相位=='hero'#是否英雄
        标题=芯片标题(待选,会话标识,会话工作区,工作区快照,工作目录)#芯片
        区域=None#输入区
        if 会话 is not None and 输入态 is not None:#双有
            区域={'session':会话,'input':输入态}#区
        惰性=会话标识 is None or (英雄 is True and 标题 is None)#无工作区
        阻塞=惰性 is False and 阻断 is not None#阻断
        栏属性={'variant':'hero' if 英雄 is True else 'composer'}#栏
        if 惰性 is True:#无工作区触发
            栏属性.update({'disabled':True,'placeholder':翻译('placeholder.workspace'),'workspacePickerOpen':自身.挑选打开,'onRequestWorkspace':自身.切换挑选})#触发
        elif 阻塞 is True:#阻断
            栏属性.update({'blocked':阻断,'placeholder':阻断['reason'] if 'reason' in 阻断 else None})#阻断
        elif 英雄 is True:#英雄占位
            栏属性['placeholder']=翻译('placeholder.hero')#占位
        栏属性['overlay']=渲染槽('conversation.input.overlay',{})#覆盖
        栏属性['leftItems']=渲染槽('conversation.input.left',区域) if 区域 is not None else None#左
        栏属性['rightItems']=渲染槽('conversation.input.right',区域) if 区域 is not None else None#右
        栏属性['footer']=渲染槽('conversation.composer.dock',区域) if (英雄 is False and 区域 is not None) else None#脚
        输入栏=渲染槽('conversation.composer.bar',栏属性)#栏
        栈={'type':'composerStack','hero':英雄,'inputBar':输入栏,'glow':英雄,'shell':英雄,'workspaceRow':英雄,'dock':渲染槽('conversation.input.dock',区域) if 区域 is not None else None,'chipTitle':标题,'pickerOpen':自身.挑选打开}#栈
        撰写=渲染链('conversation.composer',{'interactions':待审,'session':会话},{'fallback':栈,'overlay':True})#链
        return {#根
            'type':'conversationRoot',#类型
            'phase':相位,#相位
            'composer':撰写,#撰写
            'cssModule':'骨架/会话根.module.css',#样式
            'selectWorkspace':选工作区,#挑选
            'pendingWorkspaceId':自身.待定工作区,#待定
        }#结束

    def __call__(自身,属性=None):
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
