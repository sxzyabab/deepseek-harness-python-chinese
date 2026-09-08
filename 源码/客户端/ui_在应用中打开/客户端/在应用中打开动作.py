"""会话头部「在应用中打开」分体按钮的控制器面。

对齐上游 `ui-open-in-app/src/client/OpenInAppAction.tsx`。公开面仅中文名。
像素级 React/CSS 渲染延后；本模块完整移植状态机、标签映射、启动与菜单动作，
经 渲染() 产出与上游 JSX 同构的结构树。
"""
import threading#忙碌/错误定时器
from .文案 import 命名空间#locale 命名空间（inject 契约）

__all__=['在应用中打开动作','应用图标','应用标签键','忙碌装扮延迟毫秒']#仅中文公开名

# 目录 id → 词典键：浏览器只渲染能命名的 id；主机目录扩展若无匹配词条则保持不可见。
应用标签键={#catalog id → OpenInAppKey
    'finder':'app.finder',
    'explorer':'app.explorer',
    'filemanager':'app.filemanager',
    'cursor':'app.cursor',
    'vscode':'app.vscode',
    'vscodeinsiders':'app.vscodeinsiders',
    'windsurf':'app.windsurf',
    'zed':'app.zed',
    'sublimetext':'app.sublimetext',
    'xcode':'app.xcode',
    'androidstudio':'app.androidstudio',
    'intellij':'app.intellij',
    'pycharm':'app.pycharm',
    'webstorm':'app.webstorm',
    'phpstorm':'app.phpstorm',
    'goland':'app.goland',
    'rider':'app.rider',
    'rustrover':'app.rustrover',
    'fork':'app.fork',
    'sourcetree':'app.sourcetree',
    'github':'app.github',
    'tower':'app.tower',
    'gitkraken':'app.gitkraken',
    'smartgit':'app.smartgit',
    'sublimemerge':'app.sublimemerge',
    'ghostty':'app.ghostty',
    'warp':'app.warp',
    'iterm':'app.iterm',
    'kitty':'app.kitty',
    'terminal':'app.terminal',
    'windowsterminal':'app.windowsterminal',
    'gitbash':'app.gitbash',
    'gnometerminal':'app.gnometerminal',
    'konsole':'app.konsole',
}#标签键结束

失败图标集=set()#本页图标已失败的应用 id；404 图标每页只取一次

忙碌装扮延迟毫秒=250#快速启动不闪忙碌态
错误持续毫秒=2000#失败描边与 tooltip 时长

样式表='''#对齐 OpenInAppAction.module.css 核心；像素级挂载延后
.split{display:inline-flex;align-items:stretch;box-sizing:border-box;height:26px;border:0.5px solid var(--dsw-alias-border-l4);border-radius:13px;overflow:hidden;font-family:var(--dsw-font-family)}
.main,.chevron{display:inline-flex;align-items:center;gap:5px;border:0;background:none;color:var(--dsw-alias-label-primary);font-size:11px;font-weight:400;line-height:16px;cursor:pointer;white-space:nowrap}
.main{padding:5px 6px 5px 7px}
.main:disabled{color:var(--dsw-alias-label-dimmed);cursor:wait}
.main[data-state="error"]{color:var(--dsw-alias-state-error-primary);box-shadow:inset 0 0 0 1px var(--dsw-alias-state-error-primary)}
.chevron{padding:5px 6px 5px 4px;border-left:0.5px solid var(--dsw-alias-border-l4);color:var(--dsw-alias-label-secondary)}
.icon{flex:none}
'''#样式表结束

class 应用图标:#一条应用的真图标或占位
    """主机提供的 PNG；失败则落到通用方块占位。"""
    def __init__(自身,标识,网址,尺寸):#构造
        """记下目录 id、图标 URL 与边长。"""
        自身.标识=标识#catalog id
        自身.网址=网址#主机图标 URL
        自身.尺寸=尺寸#渲染边长
        自身.已失败=标识 in 失败图标集#本页已失败

    def 标记失败(自身):#图标 onError
        """记入失败集并切占位。"""
        失败图标集.add(自身.标识)#登记
        自身.已失败=True#切占位

    def 渲染(自身):#结构树
        """真图或占位 SVG 描述。"""
        if 自身.已失败:#占位
            return {#通用方块
                'type':'app-icon-fallback',#种类
                'size':自身.尺寸,#边长
                'className':'icon',#样式
            }#占位结束
        return {#真图
            'type':'app-icon',#种类
            'id':自身.标识,#id
            'src':自身.网址,#URL
            'size':自身.尺寸,#边长
            'className':'icon',#样式
            'onError':自身.标记失败,#失败回调
        }#真图结束

class 在应用中打开动作:#会话头部 utilities 贡献
    """分体按钮：主钮打开记住的应用，箭头打开已装应用菜单。

    主机尚未报告至少一个可命名应用、或会话无已知工作区目录时，渲染为 None。
    """
    def __init__(自身,属性):#构造
        """记下 props 与本地交互态。"""
        自身.属性=属性#合成 props
        自身.打开=False#菜单开合
        自身.阶段='idle'#idle|busy|error
        自身.是否在飞=False#启动在飞守卫
        自身.忙碌定时=None#threading.Timer
        自身.错误定时=None#threading.Timer

    def 更新(自身,属性):#刷新 props
        """换上最新注入面。"""
        自身.属性=属性#最新

    def 拆除(自身):#对齐 useEffect cleanup
        """清掉未触发的定时器。"""
        自身._清忙碌定时()#清忙碌
        自身._清错误定时()#清错误

    def _清忙碌定时(自身):#取消忙碌定时
        """幂等。"""
        if 自身.忙碌定时 is not None:#有
            自身.忙碌定时.cancel()#取消
            自身.忙碌定时=None#清空

    def _清错误定时(自身):#取消错误定时
        """幂等。"""
        if 自身.错误定时 is not None:#有
            自身.错误定时.cancel()#取消
            自身.错误定时=None#清空

    def 读工作目录(自身):#会话 cwd
        """经 useSessions 或 hooks.session 投影。"""
        会话标识=自身.属性['sessionId'] if 'sessionId' in 自身.属性 else None#会话 id
        用会话=自身.属性['useSessions'] if 'useSessions' in 自身.属性 else None#选择器钩子
        if 用会话 is not None:#有钩子
            def 取目录(状态):#选择器
                """按会话读 cwd。"""
                if 状态 is None or 'byId' not in 状态:#无
                    return None#缺席
                条目=状态['byId'][会话标识] if 会话标识 in 状态['byId'] else None#条目
                if 条目 is None:#无
                    return None#缺席
                return 条目['cwd'] if 'cwd' in 条目 else None#目录
            return 用会话(取目录)#投影
        return None#无钩子

    def 读可用应用(自身):#可用性快照
        """经 useOpenInAppApps 或 hooks.openInAppApps。"""
        用=自身.属性['useOpenInAppApps'] if 'useOpenInAppApps' in 自身.属性 else None#钩子
        if 用 is not None:#有
            return 用(lambda 应用表:应用表)#原样
        钩=自身.属性['hooks'] if 'hooks' in 自身.属性 and 自身.属性['hooks'] is not None else {}#hooks
        存储=钩['openInAppApps'] if 'openInAppApps' in 钩 else None#存储
        if 存储 is not None:#有
            return 存储.getSnapshot()#快照
        return None#缺席

    def 读选择(自身):#上次选择
        """经 useOpenInAppChoice 或 hooks.openInAppChoice。"""
        用=自身.属性['useOpenInAppChoice'] if 'useOpenInAppChoice' in 自身.属性 else None#钩子
        if 用 is not None:#有
            return 用(lambda 标识:标识)#原样
        钩=自身.属性['hooks'] if 'hooks' in 自身.属性 and 自身.属性['hooks'] is not None else {}#hooks
        存储=钩['openInAppChoice'] if 'openInAppChoice' in 钩 else None#存储
        if 存储 is not None:#有
            return 存储.getSnapshot()#快照
        return ''#空选择

    def 可命名应用(自身):#过滤后的应用行
        """只留词典能命名的 id。"""
        可用=自身.读可用应用()#可用性
        源=[] if 可用 is None else list(可用)#空则空表
        行列表=[]#累积
        for 标识 in 源:#逐 id
            标签键=应用标签键[标识] if 标识 in 应用标签键 else None#词典键
            if 标签键 is not None:#可命名
                行列表.append({'id':标识,'labelKey':标签键})#行
        return 行列表#全部

    def 启动应用(自身,应用标识,工作目录):#启动一次
        """在飞时重复点击整体忽略；忙碌装扮延迟后才亮。"""
        if 自身.是否在飞:#在飞
            return#忽略
        自身.是否在飞=True#占位
        自身._清错误定时()#待衰减错误不得中途翻回 idle
        自身._清忙碌定时()#重开忙碌窗
        def 标忙碌():#延迟忙碌
            """超过阈值才变暗。"""
            自身.阶段='busy'#忙碌
            自身.忙碌定时=None#已触发
        自身.忙碌定时=threading.Timer(忙碌装扮延迟毫秒/1000.0,标忙碌)#定时
        自身.忙碌定时.daemon=True#守护
        自身.忙碌定时.start()#启动定时
        启动=自身.属性['launch'] if 'launch' in 自身.属性 else None#注入启动
        try:#同步启动
            if 启动 is not None:#有
                启动(应用标识,工作目录)#POST
            自身.是否在飞=False#结束
            自身._清忙碌定时()#清
            自身.阶段='idle'#空闲
        except Exception:#启动失败；launch 契约可为任意异常
            自身.是否在飞=False#结束
            自身._清忙碌定时()#清
            自身.阶段='error'#错误态
            自身._清错误定时()#重开错误窗
            def 回空闲():#两秒后回
                """错误态衰减。"""
                自身.阶段='idle'#空闲
                自身.错误定时=None#已触发
            自身.错误定时=threading.Timer(错误持续毫秒/1000.0,回空闲)#定时
            自身.错误定时.daemon=True#守护
            自身.错误定时.start()#启动定时

    def 切换菜单(自身):#翻转开合
        """箭头按钮。"""
        自身.打开=not 自身.打开#翻

    def 关菜单(自身):#关闭菜单
        """onClose。"""
        自身.打开=False#关

    def 菜单选定(自身,标识,工作目录):#菜单挑一项
        """在飞时整段忽略（否则会持久化未打开的选择）。"""
        自身.打开=False#关菜单
        if 自身.是否在飞:#在飞
            return#忽略
        选定=自身.属性['choose'] if 'choose' in 自身.属性 else None#注入选定
        if 选定 is not None:#有
            选定(标识)#持久化
        自身.启动应用(标识,工作目录)#再启动

    def 图标网址(自身,应用标识):#拼图标 URL
        """经注入 iconUrl。"""
        拼=自身.属性['iconUrl'] if 'iconUrl' in 自身.属性 else None#注入
        if 拼 is not None:#有
            return 拼(应用标识)#URL
        return ''#空

    def 渲染(自身):#结构树或 None
        """无可提供时返回 None。"""
        翻译=自身.属性['t'] if 't' in 自身.属性 else (lambda 键,参数=None:键)#文案
        工作目录=自身.读工作目录()#cwd
        行列表=自身.可命名应用()#可命名
        选择=自身.读选择()#上次
        当前行=None#当前条目
        for 行 in 行列表:#找记住的
            if 行['id']==选择:#命中
                当前行=行#记下
                break#停
        if 当前行 is None and len(行列表)>0:#回退首项
            当前行=行列表[0]#首个
        if 当前行 is None or 工作目录 is None or 工作目录=='':#无可提供
            return None#不渲染
        当前=当前行['id']#当前 id
        当前标签=翻译(当前行['labelKey'])#应用名
        if 自身.阶段=='error':#错误标题
            标题=翻译('open.error')#失败
        else:#正常
            标题=翻译('open.title',{'app':当前标签})#带应用名
        提示=翻译('open.error') if 自身.阶段=='error' else 翻译('open.tooltip')#tooltip
        图标拼=lambda 标识:自身.图标网址(标识)#闭包
        项列表=[]#菜单项
        for 行 in 行列表:#逐行
            项列表.append({#菜单项
                'id':行['id'],#id
                'label':翻译(行['labelKey']),#标签
                'icon':应用图标(行['id'],图标拼(行['id']),18).渲染(),#图标
            })#项结束
        return {#分体按钮视图
            'type':'open-in-app-action',#种类
            'locale':命名空间,#词表
            'open':自身.打开,#菜单
            'phase':自身.阶段,#阶段
            'title':标题,#aria
            'tooltip':提示,#tooltip
            'menuToggle':翻译('menu.toggle'),#箭头文案
            'selectedId':当前,#选中
            'items':项列表,#菜单
            'mainIcon':应用图标(当前,图标拼(当前),15).渲染(),#主钮图标
            'disabled':自身.阶段=='busy',#忙碌禁用
            'cssModule':'在应用中打开动作.module.css',#样式模块名
            'styleSheet':样式表,#内联样式字符串（像素挂载延后）
            'onMainClick':lambda:自身.启动应用(当前,工作目录),#主钮
            'onToggle':自身.切换菜单,#箭头
            'onClose':自身.关菜单,#关菜单
            'onSelect':lambda 标识:自身.菜单选定(标识,工作目录),#菜单选定
            'onDispose':自身.拆除,#对齐 effect cleanup
        }#视图结束

    def __call__(自身,属性=None):#对齐 React 调用
        """刷新 props 后渲染。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
