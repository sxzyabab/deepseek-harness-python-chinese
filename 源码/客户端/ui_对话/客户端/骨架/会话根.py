"""常驻会话骨架：英雄相位、撰写座位与会话滚动体。

对齐上游 `ui-conversation/src/client/skeleton/ConversationRoot.tsx`。
公开面仅中文名。DOM/ResizeObserver 半由宿主渲染；本模块落盘相位与座位推导。
"""

__all__=['会话根','工作区标签','派生相位','芯片标题']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """映射或对象。"""
    if 对象 is None:#空
        return 缺省#缺
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 工作区标签(工作目录):#芯片 basename
    """仅分隔符路径回显原 cwd。"""
    if not 工作目录:#空
        return ''#空
    规范化=工作目录.replace('\\','/').rstrip('/')#统一
    if 规范化=='' or 规范化.endswith(':'):#根或盘符
        return 工作目录#原样
    基=规范化.rsplit('/',1)[-1]#末段
    return 基 if 基!='' else 工作目录#基名或原样

def 派生相位(会话标识,撰写相位,打开态,摘要空白):#根 data-phase
    """settling / hero / active。"""
    落定中=(会话标识 is not None and 撰写相位=='blank' and 打开态=='loading' and 摘要空白 is not True)#落定
    英雄=(会话标识 is None or (撰写相位=='blank' and (打开态=='open' or 摘要空白 is True)))#英雄
    if 落定中:#落定
        return 'settling'#落定
    if 英雄:#英雄
        return 'hero'#英雄
    return 'active'#活跃

def 芯片标题(待选工作区,会话标识,会话工作区,工作区们,工作目录):#芯片展示标题
    """pending → 无会话占位 → 会话工作区 → cwd 桥 → 占位。"""
    if 待选工作区 is not None:#刚选
        return 取字段(待选工作区,'title')#标题
    if 会话标识 is None:#冷启动
        return None#占位
    if 会话工作区 is not None:#列表有属主
        return 取字段(会话工作区,'title')#标题
    相位=取字段(工作区们,'phase')#列表相位
    if 相位=='ready' or 工作目录 is None or 工作目录=='':#就绪或无 cwd
        return None#占位
    return 工作区标签(工作目录)#cwd 桥

class 会话根:#常驻会话骨架
    """推导相位、惰性撰写与座位结构树。"""

    def __init__(自身,属性=None):#记下 props
        """记下合成 props 与挑选态。"""
        自身.属性=属性 or {}#合成
        自身.挑选打开=False#挑选菜单
        自身.待定工作区=None#刚选工作区

    def 更新(自身,属性):#刷新
        """刷新 props。"""
        自身.属性=属性 or {}#新

    def 切换挑选(自身):#开合挑选
        """翻转工作区菜单。"""
        自身.挑选打开=not 自身.挑选打开#翻

    def 渲染(自身):#结构树
        """产出根结构：相位、英雄行、撰写座位。"""
        p=自身.属性#props
        会话标识=取字段(p,'sessionId')#会话
        用会话=取字段(p,'useSession')#会话钩
        用会话们=取字段(p,'useSessions')#列表钩
        用工作区=取字段(p,'useWorkspaces')#工作区钩
        用输入=取字段(p,'useInput')#输入钩
        用阻断=取字段(p,'useComposerBlock')#阻断钩
        渲染槽=取字段(p,'renderSlot')#单槽
        渲染链=取字段(p,'renderSlotChain')#链槽
        选工作区=取字段(p,'selectWorkspace')#选工作区
        翻译=取字段(p,'t') or (lambda 键,*_a,**_k:键)#文案
        会话=用会话(lambda s:s) if callable(用会话) else None#会话快照
        打开态=取字段(会话,'openState') if 会话 else None#打开
        撰写相位=取字段(会话,'composerPhase') if 会话 else None#撰写
        待审=取字段(会话,'pending') or [] if 会话 else []#待审
        输入态=用输入(lambda s:s) if callable(用输入) else None#输入
        工作目录=None#cwd
        摘要空白=None#blank
        if callable(用会话们) and 会话标识 is not None:#有列表
            工作目录=用会话们(lambda s:取字段(取字段(取字段(s,'byId'),会话标识),'cwd'))#cwd
            摘要空白=用会话们(lambda s:取字段(取字段(取字段(s,'byId'),会话标识),'blank'))#blank
        工作区们=用工作区(lambda s:s) if callable(用工作区) else {'items':[],'phase':'ready'}#工作区
        阻断=用阻断(lambda b:b) if callable(用阻断) else None#阻断
        条目=取字段(工作区们,'items') or []#列表
        会话工作区=None#属主
        if 会话标识 is not None:#有会话
            for 项 in 条目:#找属主
                标识们=取字段(项,'sessionIds') or []#会话集
                if 会话标识 in 标识们:#命中
                    会话工作区=项#记下
                    break#停
        待选=None#待定项
        if 自身.待定工作区 is not None:#有待定
            for 项 in 条目:#找
                if 取字段(项,'workspaceId')==自身.待定工作区:#命中
                    待选=项#记下
                    break#停
            if 会话工作区 is not None and 取字段(会话工作区,'workspaceId')==自身.待定工作区:#已落地
                自身.待定工作区=None#清
                待选=None#清
            elif 取字段(工作区们,'phase')=='ready' and 待选 is None:#已删
                自身.待定工作区=None#清
        相位=派生相位(会话标识,撰写相位,打开态,摘要空白)#相位
        英雄=相位=='hero'#是否英雄
        标题=芯片标题(待选,会话标识,会话工作区,工作区们,工作目录)#芯片
        区域=None#输入区
        if 会话 is not None and 输入态 is not None:#双有
            区域={'session':会话,'input':输入态}#区
        惰性=会话标识 is None or (英雄 and 标题 is None)#无工作区
        阻塞=not 惰性 and 阻断 is not None#阻断
        栏属性={'variant':'hero' if 英雄 else 'composer'}#栏
        if 惰性:#无工作区触发
            栏属性.update({'disabled':True,'placeholder':翻译('placeholder.workspace'),
                'workspacePickerOpen':自身.挑选打开,'onRequestWorkspace':自身.切换挑选})#触发
        elif 阻塞:#阻断
            栏属性.update({'blocked':阻断,'placeholder':取字段(阻断,'reason')})#阻断
        elif 英雄:#英雄占位
            栏属性['placeholder']=翻译('placeholder.hero')#占位
        if callable(渲染槽):#有槽
            栏属性['overlay']=渲染槽('conversation.input.overlay',{})#覆盖
            栏属性['leftItems']=渲染槽('conversation.input.left',区域) if 区域 else None#左
            栏属性['rightItems']=渲染槽('conversation.input.right',区域) if 区域 else None#右
            栏属性['footer']=渲染槽('conversation.composer.dock',区域) if (not 英雄 and 区域) else None#脚
            输入栏=渲染槽('conversation.composer.bar',栏属性)#栏
        else:#无槽
            输入栏=栏属性#结构
        栈={'type':'composerStack','hero':英雄,'inputBar':输入栏,#栈
            'glow':英雄,'shell':英雄,'workspaceRow':英雄,#英雄件
            'dock':渲染槽('conversation.input.dock',区域) if (callable(渲染槽) and 区域) else None,#停靠
            'chipTitle':标题,'pickerOpen':自身.挑选打开}#芯片
        if callable(渲染链):#链
            撰写=渲染链('conversation.composer',{'interactions':待审,'session':会话},
                {'fallback':栈,'overlay':True})#链输出
        else:#无链
            撰写=栈#栈即撰写
        return {#根
            'type':'conversationRoot','phase':相位,'composer':撰写,#相位与撰写
            'cssModule':'骨架/会话根.module.css',#样式
            'selectWorkspace':选工作区,'pendingWorkspaceId':自身.待定工作区,#挑选
        }#结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
