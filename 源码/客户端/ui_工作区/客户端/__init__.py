"""工作区插件的浏览器半边。两次注册：浏览区填侧栏，选择器填会话英雄。

对齐上游 `ui-workspace/src/client/index.ts`。公开面仅中文名。
"""
import threading#后台观察
from .文案 import 中文,英文,工作区文案键#再导出文案
from .存储 import 扁平会话顺序键,创建工作区查看存储#再导出 store
from .树 import (#再导出树派生
    未分组键,
    未分组标签,
    工作区标签,
    索引子智能体后代,
    派生分组,
    派生扁平,
    派生检索结果,
    相对时间,
)#树导出结束
from .约定.槽位 import 侧栏目录流槽,英雄目录流槽,目录流槽名表#再导出槽名
from .浏览区 import 工作区浏览区#侧栏浏览区
from .选择器 import 工作区选择器#英雄选择器

__all__=[#仅中文公开名
    '注入',
    '应用',
    '工作区错误',
    '中文',
    '英文',
    '工作区文案键',
    '扁平会话顺序键',
    '创建工作区查看存储',
    '未分组键',
    '未分组标签',
    '工作区标签',
    '索引子智能体后代',
    '派生分组',
    '派生扁平',
    '派生检索结果',
    '相对时间',
    '侧栏目录流槽',
    '英雄目录流槽',
    '目录流槽名表',
    '工作区浏览区',
    '工作区选择器',
]#公开面结束

注入=['slots','sessions','workspaces','locale']#槽位、会话、工作区、文案
命名空间='workspace'#字典命名空间

class 工作区错误(Exception):
    """本包工作区浏览器失败。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

def 流占用源(上下文,洞名):#某洞是否已填
    """目录流子洞已填时为真的可观察源。"""
    def 快照():#条目数
        """大于 0 即为占用。"""
        return len(上下文.slots.entries(洞名))>0#占用
    def 订阅(监听):#订阅
        """该洞变化。"""
        return 上下文.slots.subscribe(洞名,监听)#订阅
    return {#宿主可观察源
        'getSnapshot':快照,#条目数大于 0 即为占用
        'subscribe':订阅,#订阅该洞变化
    }#源结束

def 应用(上下文):#注册浏览区与选择器
    """槽位声明入账后注册浏览区与选择器。"""
    def 登记词典():#挂载词典
        """中英文字典。"""
        return 上下文.locale.register(命名空间,{'zh':中文,'en':英文})#登记
    上下文.副作用(登记词典,'ui-workspace: dictionaries')#挂载中英文字典

    def 检索会话(查询,信号):#按查询检索会话
        """转发会话检索；失败抛出错误信息。"""
        结果=上下文.sessions.search(查询,信号).等待()#转发
        if not 结果['ok']:#失败
            错=结果['error'] if 'error' in 结果 else None#错误
            消息=错['message'] if 错 is not None and 'message' in 错 else None#文案
            raise 工作区错误(消息)#抛出
        return 结果['value']#命中列表

    侧栏流源=流占用源(上下文,侧栏目录流槽)#侧栏目录流占用源
    选择器流源=流占用源(上下文,英雄目录流槽)#选择器目录流占用源

    def 浏览区注入():#侧栏浏览区注入
        """浏览区驱动的 Host 动作。"""
        def 重命名会话(会话标识,标题):#按会话 id 改标题
            """改名是会话动词。"""
            绑定=上下文.sessions.binding(会话标识)#解析绑定
            会话=绑定.session if 绑定 is not None else None#会话面
            if 会话 is None:#未绑定
                raise 工作区错误('unknown session "'+str(会话标识)+'"')#失败
            结果=会话.rename(标题).等待()#改名
            if not 结果['ok']:#失败
                错=结果['error'] if 'error' in 结果 else None#错误
                消息=错['message'] if 错 is not None and 'message' in 错 else None#文案
                raise 工作区错误(消息)#抛出
        def 分叉会话(会话标识):#分叉会话
            """分叉并打开子会话；失败保持当前选中。"""
            def 成功(子标识):#打开子会话
                """成功则打开。"""
                上下文.sessions.open(子标识)#打开
            任务=上下文.sessions.fork({'sessionId':会话标识,'increaseTitle':True})#分叉
            def 观察():#观察分叉结果
                """成功打开；失败保持选中。"""
                try:#成功臂
                    成功(任务.等待())#打开子会话
                except BaseException:#失败臂
                    pass#保持当前选中
            线=threading.Thread(target=观察)#挂观察
            线.daemon=True#不挡退出
            线.start()#启动
        def 开会话(工作区标识=None):#开新会话
            """startSession。"""
            return 上下文.workspaces.startSession(工作区标识)#开
        def 打开会话(会话标识):#打开
            """open。"""
            return 上下文.sessions.open(会话标识)#打开
        def 重命名工作区(工作区标识,标题):#重命名
            """rename。"""
            return 上下文.workspaces.rename(工作区标识,标题).等待()#等待
        def 删除工作区(工作区标识):#删除
            """delete。"""
            return 上下文.workspaces.delete(工作区标识).等待()#等待
        def 插工作区(工作区标识,锚点=None):#插
            """insertBefore。"""
            return 上下文.workspaces.insertBefore(工作区标识,锚点).等待()#等待
        def 归档会话(会话标识):#归档
            """archiveSession。"""
            return 上下文.workspaces.archiveSession(会话标识).等待()#等待
        def 插会话(工作区标识,会话标识,锚点=None):#插会话
            """insertSessionBefore。"""
            return 上下文.workspaces.insertSessionBefore(工作区标识,会话标识,锚点).等待()#等待
        def 创建工作区(输入):#创建
            """create。"""
            return 上下文.workspaces.create(输入)#创建
        return {#注入面
            'startSession':开会话,#开新会话
            'open':打开会话,#打开会话
            'searchSessions':检索会话,#检索
            'searchResultLimit':上下文.sessions.searchResultLimit,#检索上限
            'renameSession':重命名会话,#改名
            'forkSession':分叉会话,#分叉
            'renameWorkspace':重命名工作区,#重命名工作区
            'deleteWorkspace':删除工作区,#删除工作区
            'insertWorkspaceBefore':插工作区,#插工作区
            'archiveSession':归档会话,#归档
            'insertSessionBefore':插会话,#插会话
            'createWorkspace':创建工作区,#创建工作区
            'hooks':{'directoryFlow':侧栏流源},#侧栏目录流占用源
        }#注入结束

    def 选择器注入():#会话英雄选择器注入
        """挑选器私有注入份额。"""
        def 创建工作区(输入):#创建
            """create。"""
            return 上下文.workspaces.create(输入)#创建
        return {#注入面
            'createWorkspace':创建工作区,#创建工作区
            'hooks':{'directoryFlow':选择器流源},#选择器目录流占用源
        }#注入结束

    def 登记浏览区():#侧栏工作区洞
        """洞就绪后再注册。"""
        return 上下文.slots.register({#侧栏工作区洞就绪后再注册
            'name':'sidebar.workspaces',#侧栏工作区洞名
            'children':{侧栏目录流槽:{'kind':'single','scope':'root'}},#单例目录流子洞
            'store':创建工作区查看存储(),#浏览区视图存储
            'inject':浏览区注入,#浏览区注入工厂
            'locale':命名空间,#文案命名空间
        },工作区浏览区)#浏览区组件
    上下文.slots.inject('sidebar.workspaces',登记浏览区)#浏览区

    def 登记选择器():#英雄工作区洞
        """洞就绪后再注册。"""
        return 上下文.slots.register({#英雄工作区洞就绪后再注册
            'name':'conversation.hero.workspace',#会话英雄工作区洞名
            'children':{英雄目录流槽:{'kind':'single','scope':'root'}},#单例目录流子洞
            'inject':选择器注入,#选择器注入工厂
            'locale':命名空间,#文案命名空间
        },工作区选择器)#选择器组件
    上下文.slots.inject('conversation.hero.workspace',登记选择器)#选择器

inject=注入#框架槽
apply=应用#框架槽
