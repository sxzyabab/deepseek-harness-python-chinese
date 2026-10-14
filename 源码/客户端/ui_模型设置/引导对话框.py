from nicegui import ui as 界面
from .存储 import 引导就绪度#就绪度投影
from .提供方编辑器 import 提供方编辑器#密钥编辑器
from .模型分区 import _读样式,挂到根#样式挂到引导根

__all__=['欢迎通知','官方引导对话框']

界面.add_css(挂到根(_读样式('欢迎通知.module.css'),'欢迎通知根'),shared=True)
界面.add_css(挂到根(_读样式('官方引导.module.css'),'官方引导根'),shared=True)

class 欢迎通知:#产品级版本化内测声明
    '未确认当前文案版本前渲染；已确认则 complete'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性
        自身.已结束=False#是否已 complete
        if isinstance(属性,dict) and 't' in 属性:#有文案才画
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 读状态(自身):#读欢迎快照
        '经 hooks.welcome 存储'
        钩=自身.属性['hooks'] if 'hooks' in 自身.属性 and 自身.属性['hooks'] is not None else {}#hooks
        存储=钩['welcome'] if 'welcome' in 钩 else None#存储
        if 存储 is not None:
            return 存储.getSnapshot()#快照
        控制器=自身.属性['controller'] if 'controller' in 自身.属性 else None#控制器
        return 控制器.存储.getSnapshot() if 控制器 is not None else {'status':'idle','acknowledged':False}#默认

    def 结束(自身):#完成本步
        '幂等 complete'
        if 自身.已结束:#已结束
            return#跳过
        自身.已结束=True#标记
        完成=自身.属性['complete'] if 'complete' in 自身.属性 else None#协调器
        if 完成 is not None:
            完成()#移交

    def 渲染(自身):#结构化视图
        'idle/loading/已确认返回 None'
        翻译=自身.属性['t']#文案
        控制器=自身.属性['controller'] if 'controller' in 自身.属性 else None#控制器
        状态=自身.读状态()#状态
        态名=状态['status'] if 'status' in 状态 else None#状态名
        if 态名=='idle' and 控制器 is not None:#尚未拉
            控制器.load()#首读
            状态=自身.读状态()#再读
            态名=状态['status'] if 'status' in 状态 else None#再读名
        已确认='acknowledged' in 状态 and 状态['acknowledged']#已确认
        if 已确认:#已确认
            自身.结束()#移交
            return None#不渲染
        if 态名 in ('idle','loading') or 已确认:#仍决定中
            return None#不渲染
        def 确认():#点继续
            '写入确认后 complete'
            if 控制器 is not None and 控制器.acknowledge():#接受
                自身.结束()#移交
        段落=翻译('welcomeBody').split('\n\n')#分段
        有错='error' in 状态 and 状态['error'] is not None#有错误
        with 界面.dialog() as 对话框:
            with 界面.card().classes('welcome-notice 欢迎通知根'):
                界面.label(翻译('welcomeTitle')).props('autofocus')
                with 界面.column().classes('copy'):#正文
                    for 段 in 段落:
                        if 段!='':
                            界面.label(段)
                if 有错:
                    界面.label(翻译('welcomeError')).classes('error')
                with 界面.row().classes('actions'):#动作
                    钮=界面.button(翻译('welcomeContinue'), on_click=确认).classes('primary')
                    if 态名=='saving':
                        钮.disable()
        对话框.open()

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 调用'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

class 官方引导对话框:#官方 DeepSeek 首次引导
    '无可用提供方且官方路由缺密钥时提示'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性
        自身.编辑器=None#内嵌编辑器
        if isinstance(属性,dict) and 't' in 属性:#有文案才画
            自身.渲染()#槽位只调用构造

    def 更新(自身,属性):#props 变更
        '刷新'
        自身.属性=属性#最新

    def 读状态(自身):#读模型拼合快照
        '经 hooks.models 存储'
        钩=自身.属性['hooks'] if 'hooks' in 自身.属性 and 自身.属性['hooks'] is not None else {}#hooks
        存储=钩['models'] if 'models' in 钩 else None#存储
        if 存储 is not None:
            return 存储.getSnapshot()#快照
        控制器=自身.属性['controller'] if 'controller' in 自身.属性 else None#控制器
        return 控制器.存储.getSnapshot() if 控制器 is not None else {'status':'idle','rows':[]}#默认

    def 渲染(自身):#结构化视图
        '按就绪度决定是否渲染；缺密钥时嵌提供方编辑器'
        翻译=自身.属性['t']#文案
        控制器=自身.属性['controller'] if 'controller' in 自身.属性 else None#控制器
        完成=自身.属性['complete'] if 'complete' in 自身.属性 else None#协调器
        接口=自身.属性['api'] if 'api' in 自身.属性 else None#api
        状态=自身.读状态()#状态
        态名=状态['status'] if 'status' in 状态 else None#状态名
        if 态名=='idle' and 控制器 is not None:#尚未拉
            控制器.load()#首读
            状态=自身.读状态()#再读
        就绪=引导就绪度(状态)#就绪度
        种=就绪['kind'] if 'kind' in 就绪 else None#分支
        if 种 in ('adapter-absent','provider-ready','unavailable'):#无需干预
            if 完成 is not None:
                完成()#移交
            return None#不渲染
        if 种=='loading':#仍加载
            return None#不渲染
        if 种!='credential-missing':#意外
            return None#不渲染
        官方=None#官方行
        行列表=状态['rows'] if 'rows' in 状态 and 状态['rows'] is not None else []#行
        for 候选 in 行列表:#找官方
            条目=候选['entry'] if 'entry' in 候选 and 候选['entry'] is not None else {}#条目
            路径=条目['settingsPath'] if 'settingsPath' in 条目 and 条目['settingsPath'] is not None else []#路径
            if ('provider' in 条目 and 条目['provider']=='deepseek-official'
                and 'settingsNs' in 条目 and 条目['settingsNs']=='llm-deepseek'
                and len(路径)==0):#官方
                官方=候选
                break#找到
        命名空间图=状态['namespaces'] if 'namespaces' in 状态 and 状态['namespaces'] is not None else {}#ns 图
        命名空间=命名空间图['llm-deepseek'] if 'llm-deepseek' in 命名空间图 else None#官方 ns
        if 官方 is None or 命名空间 is None:#推导不一致
            return None#不渲染
        条目=官方['entry'] if 'entry' in 官方 and 官方['entry'] is not None else {}#条目
        def 结束密钥(已变):#编辑器关闭
            '未变更则 complete；变更则 reload'
            if not 已变:#稍后
                if 完成 is not None:
                    完成()#移交
                return
            if 控制器 is not None:
                控制器.load()#刷新
        自身.编辑器=提供方编辑器({#仅密钥装卡
            'provider':条目['provider'] if 'provider' in 条目 else None,#路由
            'displayName':条目['displayName'] if 'displayName' in 条目 else None,#显示名
            'namespace':命名空间,#ns
            'settingsPath':条目['settingsPath'] if 'settingsPath' in 条目 and 条目['settingsPath'] is not None else [],#路径
            'api':接口,#api
            't':翻译,#文案
            'readOnly':False,#可写
            'hideTitle':True,#藏标题
            'credentialOnly':True,#仅密钥
            'credentialRequired':True,#必填
            'autoFocusCredential':True,#聚焦
            'cancelLabel':'onboardingLater',#稍后
            'submitLabel':'onboardingSave',#保存
            'submitBusyLabel':'onboardingSaving',#保存中
            'onClose':结束密钥,#关闭
        })#编辑器结束
        with 界面.dialog() as 对话框:
            with 界面.card().classes('deepseek-onboarding 官方引导根'):
                界面.label(翻译('onboardingTitle'))
                界面.label(翻译('onboardingDescription')).classes('description')
                自身.编辑器.渲染()
        对话框.open()

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 调用'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
