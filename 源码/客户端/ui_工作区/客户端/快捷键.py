'工作区命令和浏览区上的打开请求。改名要求主对话非空，且没有模态挡住'
from ...存储 import 创建快照存储
from ..异常 import 错误名,远程码
from .文案 import 中文

__all__=['创建工作区快捷控制','安装工作区快捷键']

def 创建工作区快捷控制():
    '命令和浏览区共用的打开请求。搜索次数只增，添加在目录忙时不响'
    状态=创建快照存储({
        'searchRequest':0,#搜索请求次数
        'addRequested':False,#要打开添加
        'directoryBusy':False,#目录交互进行中
        'renameTarget':None,#要改名的会话
    })#状态
    def 搜索():
        '再请求一次搜索'
        现在=状态.getSnapshot()#当前
        状态.set({**现在,'searchRequest':现在['searchRequest']+1})#加一
    def 添加():
        '目录不忙时请求添加工作区'
        现在=状态.getSnapshot()#当前
        if 现在['directoryBusy']:#忙
            状态.set(现在)#保持
            return#不打开
        状态.set({**现在,'addRequested':True})#请求
    def 关闭添加():
        '用掉添加请求'
        状态.set({**状态.getSnapshot(),'addRequested':False})#关掉
    def 目录忙(忙):
        '目录交互是否占着表面'
        状态.set({**状态.getSnapshot(),'directoryBusy':忙})#写入
    def 改名(会话号,当前标题):
        '打开改名，带上当前标题'
        状态.set({**状态.getSnapshot(),'renameTarget':{'sessionId':会话号,'currentTitle':当前标题}})#请求
    def 关闭改名():
        '用掉改名请求'
        状态.set({**状态.getSnapshot(),'renameTarget':None})#关掉
    return {
        'state':状态,#可观察状态
        'search':搜索,#搜索
        'add':添加,#添加
        'closeAdd':关闭添加,#关掉添加
        'directoryBusy':目录忙,#忙
        'rename':改名,#改名
        'closeRename':关闭改名,#关掉改名
    }

def 安装工作区快捷键(上下文,导航,控制,归档会话,报告分叉失败):
    '登记新建、搜索、添加、改名、分叉、归档。标签用中文表原文'
    def 当前():
        '主视图留着的那条会话'
        for 行 in 上下文.sessions.list.getSnapshot()['byId'].values():#逐条
            保留=行.get('retainedBy') or {}#保留
            if (保留.get('mainView') or 0)>0:#主视图
                return 行#这条
        return None#没有
    def 添加原因():
        '没有目录流或目录正忙时，添加命令被挡住'
        if len(上下文.slots.entries('sidebar.workspaces.directoryFlow'))==0:#没人填洞
            return 中文['shortcut.noPicker']#选择器不可用
        if 控制['state'].getSnapshot()['directoryBusy']:#忙
            return 中文['shortcut.directoryBusy']#正在选择
        return None#可以
    def 登记(标识,标签,别名,码,修饰,网页修饰,解析):
        '四个桌面和网页目标用同一套键位'
        def 登记体():
            '卸下时由快捷键服务拆除'
            return 上下文.shortcuts.register({
                'id':标识,#命令
                'label':标签,#中文标签
                'aliases':别名,#英文别名
                'defaults':{#默认键位
                    'desktop:macos':{'code':码,'modifiers':修饰},
                    'desktop:windows':{'code':码,'modifiers':修饰},
                    'desktop:linux':{'code':码,'modifiers':修饰},
                    'web:macos':{'code':码,'modifiers':网页修饰},
                    'web:windows':{'code':码,'modifiers':网页修饰},
                },
                'regions':['page','editable'],#区域
                'modals':[],#不在模态里
                'resolve':解析,#解析
            })
        上下文.副作用(登记体,'ui-workspace: '+标识)#登记
    def 新会话标签():
        '新建会话'
        return 中文['session.new']#新会话
    def 解析新建():
        '直接新建'
        def 跑():
            '不指定工作区'
            导航.startSession()#新建
        return {'status':'handled','run':跑}#处理
    登记('session.new',新会话标签,['new session','new chat'],'KeyN',['primary'],['primary','alt'],解析新建)#新建
    def 搜索标签():
        '搜索会话'
        return 中文['search.sessions.aria']#搜索会话
    def 解析搜索():
        '打开浏览区搜索'
        return {'status':'handled','run':控制['search']}#处理
    登记('session.search',搜索标签,['search sessions'],'KeyK',['primary'],['primary','alt'],解析搜索)#搜索
    def 添加标签():
        '添加工作区'
        return 中文['workspace.add']#添加工作区
    def 解析添加():
        '没有选择器或正在选择时挡住'
        原因=添加原因()#原因
        if 原因 is None:#可以
            return {'status':'handled','run':控制['add']}#打开
        return {'status':'blocked','reason':原因}#挡住
    登记('workspace.add',添加标签,['add workspace','open folder'],'KeyO',['primary'],['primary','alt'],解析添加)#添加
    def 改名标签():
        '重命名会话'
        return 中文['rename.session.title']#重命名会话
    def 解析改名(场面):
        '空白会话、有模态或有面板时不改名'
        目标=当前()#当前
        模态=场面.get('modal') if isinstance(场面,dict) else getattr(场面,'modal',None)#模态
        面板=上下文.layout.panelInfo.getSnapshot().get('activePanelId')#活动面板
        if 目标 is None or 目标.get('blank') or 模态 is not None or 面板 is not None:#不能改
            return {'status':'blocked','reason':中文['shortcut.noSession']}#先选会话
        def 跑():
            '用去掉空白后的标题'
            标题=目标.get('title')#标题
            文本=标题.strip() if isinstance(标题,str) else ''#去空白
            控制['rename'](目标['id'],文本)#请求
        return {'status':'handled','run':跑}#处理
    登记('session.rename',改名标签,['rename session'],'KeyG',['primary','alt'],['primary','alt'],解析改名)#改名
    def 分叉标签():
        '分叉会话'
        return 中文['menu.fork']#分叉会话
    def 解析分叉():
        '空白会话不能分叉'
        目标=当前()#当前
        if 目标 is None:#没有
            return {'status':'blocked','reason':中文['shortcut.noSession']}#先选
        if 目标.get('blank'):#空白
            return {'status':'blocked','reason':中文['shortcut.noCompletedTurn']}#没有结束的轮次
        def 跑():
            '分叉失败按码分成不可用或普通失败'
            try:#分叉
                导航.forkSession(目标['id'])#分叉
            except Exception as 错误:#失败
                不可用=错误名(错误)=='SessionForkError' and 远程码(错误)=='session/fork-unavailable'#不可用
                报告分叉失败('unavailable' if 不可用 else 'failed')#提示
                if not 不可用:#不是不可用
                    print('session fork rejected:',错误)#日志
        return {'status':'handled','run':跑}#处理
    登记('session.fork',分叉标签,['fork session'],'KeyF',['primary','alt'],['primary','shift'],解析分叉)#分叉
    def 归档标签():
        '归档会话'
        return 中文['menu.archiveSession']#归档会话
    def 解析归档():
        '归档当前会话'
        目标=当前()#当前
        if 目标 is None:#没有
            return {'status':'blocked','reason':中文['shortcut.noSession']}#先选
        def 跑():
            '走共享的归档，运行中的会先确认'
            归档会话(目标['id'])#归档
        return {'status':'handled','run':跑}#处理
    登记('session.archive',归档标签,['archive session'],'KeyA',['primary','shift'],['primary','alt'],解析归档)#归档
