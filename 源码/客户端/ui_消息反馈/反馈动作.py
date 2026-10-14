import importlib.resources as 包资源
from nicegui import ui as 界面
from .异常 import 页面失败文案

def _读样式():
    '读同目录样式。失败时异常文案只有样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath('反馈动作.module.css').read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None

样式表=_读样式()
界面.add_css(样式表,shared=True)

__all__=['消息反馈动作']#仅中文公开名

def 缺省翻译(键,_插值=None):#无文案函数
    '原样返回键'
    return 键#键

def 反馈键齐(属性):
    '赞踩要消息身份、四个动词，以及反馈钩子。缺一不画'
    if not isinstance(属性,dict):#不是合成 props
        return False#不齐
    for 键 in ('messageId','ensure','current','retract','openDialog'):#动词与身份
        if 键 not in 属性 or 属性[键] is None:#缺键
            return False#不齐
    if 'useFeedback' in 属性 and 属性['useFeedback'] is not None:#选择器
        return True#齐
    钩=属性['hooks'] if 'hooks' in 属性 else None#钩子表
    if isinstance(钩,dict) and 'feedback' in 钩 and 钩['feedback'] is not None:#对象源
        return True#齐
    return False#没有视图

class 消息反馈动作:#一条消息的反馈控件
    '赞/踩。记录走对话框，不改会话日志的结构'
    def __init__(自身,属性):#按合成 props 构造
        '记下 props 并画出赞踩'
        自身.进行中=False#动作进行中
        自身.失败=None#失败文案
        自身.已播种=False#是否已 ensure
        自身.存活=True#实例是否仍挂载
        自身.已订=False#反馈钩子只订一次
        自身.画面失败=None
        自身.属性=属性 if isinstance(属性,dict) else {}#合成 props
        if 反馈键齐(自身.属性):#键齐
            自身.渲染()#构造末尾才画

    def 更新(自身,属性):#props 变更
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 卸载(自身):#卸载
        '标死'
        自身.存活=False#死

    def 播种(自身):#首次交互加载
        'Session 反馈只读一次'
        if 自身.已播种:#已播种
            return#跳过
        自身.已播种=True#记下
        确保=自身.属性['ensure'] if 'ensure' in 自身.属性 else None#ensure
        if 确保 is not None:#有
            确保()#加载；控制器.ensure 已等待

    def 结算(自身,结果):#动作结算
        '更新进行中与失败文案'
        if not 自身.存活:#已死
            return#丢弃
        自身.进行中=False
        if 结果['ok']:#成功
            自身.失败=None
            return
        翻译=自身.属性['t'] if 't' in 自身.属性 else 缺省翻译#文案
        错=结果['error'] if 'error' in 结果 else None#错误
        码=错['code'] if 错 is not None and 'code' in 错 else None#错误码
        自身.失败=翻译('error.conflict') if 码=='version-conflict' else 翻译('error.generic')#文案

    def 视图(自身):#读视图模型
        '赞/踩状态与说明编辑器'
        用反馈=自身.属性['useFeedback'] if 'useFeedback' in 自身.属性 else None#选择器
        消息标识=自身.属性['messageId'] if 'messageId' in 自身.属性 else None#消息 id
        翻译=自身.属性['t'] if 't' in 自身.属性 and callable(自身.属性['t']) else 缺省翻译#文案
        if 消息标识 is None:#无消息
            项=None#无条目
            加载失败=False#无
        elif 用反馈 is None:#走钩子对象
            项,加载失败=自身.钩上条目(消息标识)#条目
        else:#有
            def 选条目(视):#选该消息条目
                '从 items 取本消息'
                表=视['items']#条目表
                return 表[消息标识] if 消息标识 in 表 else None#条目
            def 选失败(视):#选加载失败
                'status 是否 error'
                return 视['status']=='error'#失败
            项=用反馈(选条目)#条目
            加载失败=用反馈(选失败)#加载失败
        评价=项['rating'] if 项 is not None and 'rating' in 项 else None#评价
        说明=项['note'] if 项 is not None and 'note' in 项 else None#已存说明
        return {#视图
            'rating':评价,#评价
            'pending':自身.进行中,#进行中
            'failure':自身.失败 if 自身.失败 is not None else (翻译('error.load') if 加载失败 else None),#失败
            'likeLabel':翻译('action.likeActive') if 评价=='positive' else 翻译('action.like'),#赞标签
            'dislikeLabel':翻译('action.dislikeActive') if 评价=='negative' else 翻译('action.dislike'),#踩标签
            'note':说明,#已存说明，只读
        }#视图结束

    def 钩上条目(自身,消息标识):
        'hooks.feedback 要带 getSnapshot 的对象'
        钩=自身.属性['hooks'] if 'hooks' in 自身.属性 else None#钩子表
        源=None#源
        if isinstance(钩,dict) and 'feedback' in 钩:#字典面
            源=钩['feedback']#源
        elif 钩 is not None:#对象面
            源=getattr(钩,'feedback',None)#源
        读=getattr(源,'getSnapshot',None)#读
        if not callable(读):#没有方法
            return None,False#空
        视=读()#快照
        if not isinstance(视,dict):#不是视图
            return None,False#空
        表=视['items'] if 'items' in 视 else None#条目表
        项=表[消息标识] if isinstance(表,dict) and 消息标识 in 表 else None#条目
        return 项,视.get('status')=='error'#条目与加载失败

    def 订反馈(自身):
        '评分视图变了就重画；列拆掉则停'
        if 自身.已订:#已订
            return#一次
        自身.已订=True#记下
        用=自身.属性['useFeedback'] if 'useFeedback' in 自身.属性 else None#选择器
        订=getattr(用,'_subscribe',None) if 用 is not None else None#框架订阅
        if not callable(订):#没有
            钩=自身.属性['hooks'] if 'hooks' in 自身.属性 else None#钩子表
            源=钩['feedback'] if isinstance(钩,dict) and 'feedback' in 钩 else (getattr(钩,'feedback',None) if 钩 is not None else None)#源
            订=getattr(源,'subscribe',None)#对象方法
        if not callable(订):#仍没有
            return#不订
        def 重画():
            '再画赞踩'
            if 自身.存活 is not True:#已卸
                return#停
            根=getattr(自身,'根',None)#列
            if 根 is None:#还没有
                return#不画
            槽=getattr(根,'parent_slot',None)#父槽
            if 槽 is not None and getattr(槽,'parent',None) is None:#已从页面拆掉
                return#不画
            自身.渲染()#重画
        订(重画)#订上

    def 选择(自身,下一):
        '同一已记录评分则撤回，否则打开对话框'
        if 'messageId' not in 自身.属性:#无消息
            return#不动作
        自身.进行中=True
        自身.失败=None
        确保=自身.属性['ensure'] if 'ensure' in 自身.属性 else None
        已载={'ok':True}
        if 确保 is not None:
            待=确保()
            已载=待.等待() if 待 is not None and hasattr(待,'等待') else 待
        if not 自身.存活:
            return
        当前=自身.属性['current'] if 'current' in 自身.属性 else None
        消息标识=自身.属性['messageId']
        现=当前(消息标识) if 当前 is not None else None
        现评价=现['rating'] if isinstance(现,dict) and 'rating' in 现 else None
        成功=isinstance(已载,dict) and ('ok' in 已载 and 已载['ok'] is True)
        if not 成功 or 现评价!=下一:
            自身.进行中=False
            打开=自身.属性['openDialog'] if 'openDialog' in 自身.属性 else None#对话框
            if 打开 is not None:#记录留在对话框提交
                打开(消息标识,下一)#打开
            return#不在按钮上改日志
        撤回=自身.属性['retract'] if 'retract' in 自身.属性 else None
        待撤=撤回(消息标识,下一) if 撤回 is not None else {'ok':True}
        结果=待撤.等待() if 待撤 is not None and hasattr(待撤,'等待') else 待撤
        if not isinstance(结果,dict):
            结果={'ok':True}
        自身.结算(结果)

    def 渲染(自身):
        '赞、踩与失败提示'
        视=自身.视图()
        旧=getattr(自身,'根',None)
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:
                自身.根=None
                自身.画面失败=页面失败文案(错误)
        if getattr(自身,'根',None) is None:
            自身.根=界面.row().classes('message-feedback')
        def 点赞():
            '选赞'
            自身.选择('positive')
            自身.渲染()
        def 点踩():
            '选踩'
            自身.选择('negative')
            自身.渲染()
        with 自身.根:
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败).classes('failure')
            赞图标='thumb_up' if 视['rating']=='positive' else 'o_thumb_up'
            踩图标='thumb_down' if 视['rating']=='negative' else 'o_thumb_down'
            赞词='icon='+赞图标+' flat round'
            踩词='icon='+踩图标+' flat round'
            if 视['rating']=='positive':
                赞词+=' aria-pressed=true data-active'
            if 视['rating']=='negative':
                踩词+=' aria-pressed=true data-active'
            赞=界面.button(on_click=点赞).props(赞词).classes('action')
            赞.tooltip(视['likeLabel'])
            踩=界面.button(on_click=点踩).props(踩词).classes('action')
            踩.tooltip(视['dislikeLabel'])
            赞.on('mouseenter',lambda _e:自身.播种())
            踩.on('mouseenter',lambda _e:自身.播种())
            if 视['pending'] is True:
                赞.disable()
                踩.disable()
            失败=视['failure']
            if isinstance(失败,str) and 失败!='':
                界面.label(失败).classes('failure')
        自身.订反馈()

    def __call__(自身,属性=None):#组件调用形
        '组件调用形'
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()
