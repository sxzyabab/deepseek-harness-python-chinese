"""工作区命令登记，以及浏览器拥有的瞬时打开请求。
命令只改 controls 状态；实际开检索/加目录/重命名由浏览器侧消费。
"""
from ...存储 import 创建快照存储#快照仓库

__all__=['创建工作区快捷键控件','安装工作区快捷键']#仅中文公开名

def 创建工作区快捷键控件():
    """创建命令与控件共用的私有浏览器请求源。
    返回可观察状态及其完整变更回调。
    """
    状态=创建快照存储({#瞬时请求初值
        'searchRequest':0,#检索触发序号
        'addRequested':False,#请求打开加目录
        'directoryBusy':False,#目录流忙碌
        'renameTarget':None,#重命名目标
        'forkError':None,#分叉失败提示
    })#初值结束
    分叉错误序号=[0]#可变盒：失败提示序号
    def 检索():
        """递增检索触发序号。"""
        快照=状态.getSnapshot()#当前
        状态.set({**快照,'searchRequest':快照['searchRequest']+1})#+1
    def 添加():
        """目录忙碌时不动；否则请求打开加目录。"""
        快照=状态.getSnapshot()#当前
        if 快照['directoryBusy']:#忙碌
            状态.set(快照)#原样
        else:#可开
            状态.set({**快照,'addRequested':True})#请求
    def 关闭添加():
        """清加目录请求。"""
        状态.set({**状态.getSnapshot(),'addRequested':False})#关
    def 目录忙碌(忙碌):
        """写入目录流忙碌标志。"""
        状态.set({**状态.getSnapshot(),'directoryBusy':忙碌})#写
    def 重命名(会话标识,当前标题):
        """记下重命名目标。"""
        状态.set({**状态.getSnapshot(),'renameTarget':{'sessionId':会话标识,'currentTitle':当前标题}})#目标
    def 关闭重命名():
        """清重命名目标。"""
        状态.set({**状态.getSnapshot(),'renameTarget':None})#清
    def 分叉失败(原因):
        """推一条分叉失败提示。"""
        分叉错误序号[0]+=1#序号
        状态.set({**状态.getSnapshot(),'forkError':{'reason':原因,'seq':分叉错误序号[0]}})#提示
    def 关闭分叉错误():
        """清分叉失败提示。"""
        状态.set({**状态.getSnapshot(),'forkError':None})#清
    return {#控件面
        'state':状态,#可观察
        'search':检索,#开检索
        'add':添加,#加目录
        'closeAdd':关闭添加,#关加目录
        'directoryBusy':目录忙碌,#忙碌标志
        'rename':重命名,#重命名
        'closeRename':关闭重命名,#关重命名
        'forkFailed':分叉失败,#分叉失败
        'dismissForkError':关闭分叉错误,#关失败提示
    }#面结束

def 安装工作区快捷键(上下文,导航,控件,归档会话):
    """在既有工作区拥有方上登记导航命令。
    上下文含快捷键、locale 与模型服务；导航含 startSession/forkSession；
    控件为浏览器拥有的打开请求；归档会话为共享归档动作。
    """
    译=上下文.locale.bind('workspace')#工作区词表
    def 当前():
        """主视图占用的会话摘要，无则 None。"""
        for 行 in 上下文.sessions.list.getSnapshot()['byId'].values():#逐摘要
            占用=行['retainedBy'] if 'retainedBy' in 行 else {}#占用
            if (占用['mainView'] if 'mainView' in 占用 else 0)>0:#主视图
                return 行#命中
        return None#无
    def 添加原因():
        """不可加目录时的阻断文案，可加则 None。"""
        if len(上下文.slots.entries('sidebar.workspaces.directoryFlow'))==0:#无挑选器
            return 译('shortcut.noPicker')#无挑选
        if 控件['state'].getSnapshot()['directoryBusy']:#忙碌
            return 译('shortcut.directoryBusy')#忙
        return None#可加
    def 登记(标识,标签,别名,码,修饰,网页修饰,解析):
        """登记一条跨平台默认绑定。"""
        def 装():
            """注册本条命令。"""
            return 上下文.shortcuts.register({#命令
                'id':标识,#命令 id
                'label':标签,#标签
                'aliases':别名,#别名
                'defaults':{#各平台默认
                    'desktop:macos':{'code':码,'modifiers':修饰},
                    'desktop:windows':{'code':码,'modifiers':修饰},
                    'desktop:linux':{'code':码,'modifiers':修饰},
                    'web:macos':{'code':码,'modifiers':网页修饰},
                    'web:windows':{'code':码,'modifiers':网页修饰},
                },#默认结束
                'regions':['page','editable'],#区域
                'modals':[],#模态
                'resolve':解析,#解析
            })#登记结束
        上下文.副作用(装,'ui-workspace: '+标识)#效应寿命
    def 新会话标签():
        """新会话标签。"""
        return 译('session.new')#标签
    def 新会话解析(_面=None):
        """新建会话。"""
        def 跑():
            """开新会话。"""
            导航.startSession()#开
        return {'status':'handled','run':跑}#已处理
    登记('session.new',新会话标签,['new session','new chat'],'KeyN',['primary'],['primary','alt'],新会话解析)
    def 检索标签():
        """检索标签。"""
        return 译('search.sessions.aria')#标签
    def 检索解析(_面=None):
        """开检索。"""
        return {'status':'handled','run':控件['search']}#已处理
    登记('session.search',检索标签,['search sessions'],'KeyK',['primary'],['primary','alt'],检索解析)
    def 加工作区标签():
        """加工作区标签。"""
        return 译('workspace.add')#标签
    def 加工作区解析(_面=None):
        """加工作区；不可用则阻断。"""
        原因=添加原因()#阻断
        if 原因 is None:#可加
            return {'status':'handled','run':控件['add']}#已处理
        return {'status':'blocked','reason':原因}#阻断
    登记('workspace.add',加工作区标签,['add workspace','open folder'],'KeyO',['primary'],['primary','alt'],加工作区解析)
    def 重命名标签():
        """重命名标签。"""
        return 译('rename.session.title')#标签
    def 重命名解析(_面=None):
        """重命名当前主视图会话。"""
        目标=当前()#当前
        if 目标 is None:#无会话
            return {'status':'blocked','reason':译('shortcut.noSession')}#阻断
        def 跑():
            """打开重命名。"""
            控件['rename'](目标['id'],目标['displayTitle'])#重命名
        return {'status':'handled','run':跑}#已处理
    登记('session.rename',重命名标签,['rename session'],'KeyR',['primary','alt'],['primary','shift'],重命名解析)
    def 分叉标签():
        """分叉标签。"""
        return 译('menu.fork')#标签
    def 分叉解析(_面=None):
        """分叉当前主视图会话。"""
        目标=当前()#当前
        if 目标 is None:#无会话
            return {'status':'blocked','reason':译('shortcut.noSession')}#阻断
        if 目标['blank']:#空白无完成回合
            return {'status':'blocked','reason':译('shortcut.noCompletedTurn')}#阻断
        def 跑():
            """发起分叉；失败写入控件提示。"""
            try:#发起
                导航.forkSession(目标['id'])#分叉
            except Exception as 错误:#客户端插件包不共享错误类身份，按 name + rpc 码判定
                rpc=getattr(错误,'rpcError',None)#rpc
                码=rpc['code'] if isinstance(rpc,dict) and 'code' in rpc else getattr(rpc,'code',None)#码
                不可用=getattr(错误,'name',None)=='SessionForkError' and 码=='session/fork-unavailable'#不可用
                控件['forkFailed']('unavailable' if 不可用 else 'failed')#提示
                if not 不可用:#非不可用
                    print('session fork rejected:',错误)#警告
        return {'status':'handled','run':跑}#已处理
    登记('session.fork',分叉标签,['fork session'],'KeyF',['primary','alt'],['primary','shift'],分叉解析)
    def 归档标签():
        """归档标签。"""
        return 译('menu.archiveSession')#标签
    def 归档解析(_面=None):
        """归档当前主视图会话。"""
        目标=当前()#当前
        if 目标 is None:#无会话
            return {'status':'blocked','reason':译('shortcut.noSession')}#阻断
        def 跑():
            """归档。"""
            归档会话(目标['id'])#归档
        return {'status':'handled','run':跑}#已处理
    登记('session.archive',归档标签,['archive session'],'KeyA',['primary','shift'],['primary','alt'],归档解析)
