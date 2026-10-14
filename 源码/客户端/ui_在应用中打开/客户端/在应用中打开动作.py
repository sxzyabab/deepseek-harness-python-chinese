'目录打开适配：会话头与文件页动作共用分体按钮，不拥有文件树'
from ....基础设施.js特性 import PromiseEX as 期约#中文别名的期约
from .应用列表 import 应用标签键#目录 id → 词典键
from .打开目标按钮 import 打开目标按钮#共享分体按钮

__all__=['在应用中打开动作','会话头打开动作','应用标签键']#仅中文公开名

def 接上(产出,成功,失败):#期约或上游 then
    '本层期约走 然后，上游 then 走 then；已是值则直接成功'
    if hasattr(产出,'然后'):#本层期约
        产出.然后(成功,失败)#接上
        return
    if hasattr(产出,'then'):#上游期约
        产出.then(成功,失败)#接上
        return
    成功(产出)#已是值

def 读钩(属性,钩名,选择器名):#hooks 或 use*
    '选择器优先，否则读注入的快照'
    用=属性.get(选择器名)#渲染器绑定的钩子
    if callable(用):#有
        return 用(lambda 值:值)#投影
    钩=属性.get('hooks')#注入 hooks
    if not isinstance(钩,dict):#没有
        return None#缺
    存=钩.get(钩名)#快照源
    if 存 is not None and hasattr(存,'getSnapshot'):#可观察
        return 存.getSnapshot()#快照
    return None#缺

def 目录键齐(属性):#目录按钮能否画
    '绝对路径、文案、启动和图标都在才画'
    if not isinstance(属性,dict):#不是映射
        return False#缺
    路径=属性.get('absolutePath')#目录
    if not isinstance(路径,str) or 路径=='':#没有路径
        return False#缺
    if not callable(属性.get('t')):#没有文案
        return False#缺
    if not callable(属性.get('launch')):#没有启动
        return False#缺
    if not callable(属性.get('iconUrl')):#没有图标
        return False#缺
    return True#齐

class 在应用中打开动作:#目录分体按钮
    '把已安装目录应用接到共享打开控件。没有可命名应用时不画，空槽回退留给主人。'
    def __init__(自身,属性):#构造
        '记下 props。槽位只调用构造，键齐才画。按钮构造时不画。'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成
        自身._按钮=None#共享控件
        if 目录键齐(自身.属性):#键齐
            自身.渲染()#末尾画一次

    def 更新(自身,属性):#刷新 props
        '换上最新注入面。不在这里再画。'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 渲染(自身):#结构树或 None
        '无可命名应用时返回 None，不另画替代控件'
        if not 目录键齐(自身.属性):#键未齐
            return None#空
        属性=自身.属性#props
        可用=读钩(属性,'openInAppApps','useOpenInAppApps')#已装 id
        选择=读钩(属性,'openInAppChoice','useOpenInAppChoice')#上次
        操作=读钩(属性,'openInAppLaunch','useOpenInAppLaunch')#启动阶段
        目录=读钩(属性,'shortcuts','useShortcuts')#快捷键目录
        快捷=None#打开工作区那条
        if isinstance(目录,(list,tuple)):#有目录
            for 行 in 目录:#找命令
                if isinstance(行,dict) and 行.get('id')=='workspace.openLocal':#命中
                    快捷=行#记下
                    break#停
        应用表=[]#可命名行
        源=可用 if isinstance(可用,(list,tuple)) else []#空则空表
        for 标识 in 源:#逐 id
            标签键=应用标签键.get(标识)#词典键
            if 标签键 is None:#不能命名
                continue#跳过
            应用表.append({#行
                'id':标识,#id
                'name':属性['t'](标签键),#显示名
                'icon':属性['iconUrl'](标识),#图标
            })#行结束
        偏好=None#记住的或第一项
        for 应用 in 应用表:#找记住的
            if 应用['id']==选择:#命中
                偏好=应用#记下
                break#停
        if 偏好 is None and len(应用表)>0:#没有记住的
            偏好=应用表[0]#第一项
        if 偏好 is None:#没有可命名应用
            return None#空槽留给主人
        路径=属性['absolutePath']#目录
        def 执行(操作):#手势
            '启动后才记住菜单点名的应用。失败交给共享控件。'
            标识=操作['id'] if isinstance(操作,dict) and 操作.get('kind')=='application' else 偏好['id']#应用
            def 成功(_值):#宿主确认
                '菜单点名才改记住的应用'
                if isinstance(操作,dict) and 操作.get('kind')=='application':#点名
                    选定=属性.get('choose')#注入
                    if callable(选定):#有
                        选定(标识)#记住
                return None#无失败键
            try:#发出
                产出=属性['launch'](标识,路径)#期约或值
            except Exception:#同步失败
                return 'openError'#共享控件宣告
            if hasattr(产出,'然后') or hasattr(产出,'then'):#期约
                结算=期约()#本次手势
                def 已成(值):#确认
                    '解决为空'
                    成功(值)#可能记住
                    结算.解决(None)#无失败键
                def 已败(_错误):#拒绝
                    '解决为打开失败键'
                    结算.解决('openError')#共享控件宣告
                接上(产出,已成,已败)#接上
                return 结算#期约
            成功(产出)#同步确认
            return None#无失败键
        阶段='idle'#默认空闲
        if isinstance(操作,dict) and 'phase' in 操作:#字典阶段
            阶段=操作['phase']#阶段
        elif 操作 is not None and hasattr(操作,'phase'):#对象阶段
            阶段=操作.phase#阶段
        面={#按钮 props
            'kind':'directory',#目录
            'applications':应用表,#应用
            'defaultId':偏好['id'],#主钮
            'failed':False,#目录菜单没有查询失败
            't':属性['t'],#文案
            'busy':阶段=='busy',#在飞
            'shortcut':快捷,#键位提示
            'execute':执行,#手势
        }#面结束
        if 自身._按钮 is None:#初建
            自身._按钮=打开目标按钮(面)#构造不画
        else:#已有
            自身._按钮.更新(面)#刷新
        return 自身._按钮.渲染()#画一次

    def __call__(自身,属性=None):#组件调用形
        '刷新后渲染'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染

def 会话目录(属性):#会话头上的工作区目录
    '只读 useSessions 投影出的 cwd。不读文件树。'
    会话标识=属性.get('sessionId')#会话
    用会话=属性.get('useSessions')#钩子
    if not callable(用会话):#没有
        return None#缺
    def 取(状态):#选择器
        'byId 上的 cwd'
        if isinstance(状态,dict):#字典
            表=状态.get('byId')#表
        else:#对象
            表=getattr(状态,'byId',None)#表
        if not isinstance(表,dict) or 会话标识 not in 表:#没有这一条
            return None#缺
        条目=表[会话标识]#会话行
        if isinstance(条目,dict):#字典
            return 条目.get('cwd')#目录
        return getattr(条目,'cwd',None)#目录
    return 用会话(取)#投影

class 会话头打开动作:#会话头 utilities
    '从会话行取出 cwd 再交给目录按钮。没有目录时不画。'
    def __init__(自身,属性):#构造
        '记下 props。槽位只调用构造，键齐才画。目录按钮在自己的构造里画，这里不再画。'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成
        自身._内=None#目录按钮
        if 'sessionId' in 自身.属性 and callable(自身.属性.get('useSessions')):#键齐
            自身.渲染()#末尾交接一次

    def 更新(自身,属性):#刷新
        '换上最新会话行。不在这里再画。'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 渲染(自身):#结构树或 None
        '没有 cwd 时返回 None。第一次构造出的按钮已经画过，这里不再画。'
        目录=会话目录(自身.属性)#cwd
        if not isinstance(目录,str) or 目录=='':#没有目录
            return None#空槽留给主人
        面=dict(自身.属性)#拷贝
        面['absolutePath']=目录#交给目录按钮
        if 自身._内 is None:#初建
            自身._内=在应用中打开动作(面)#键齐时它自己画
            return None#不要再画
        自身._内.更新(面)#刷新
        return 自身._内.渲染()#后续更新才由这里画

    def __call__(自身,属性=None):#组件调用形
        '刷新后渲染'
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
