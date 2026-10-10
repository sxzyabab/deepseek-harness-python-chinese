'日志驱动会话标题服务、确定性回退与提供方契约'
import threading#推迟的提供方调用
from ...依赖.cordis.服务 import 服务#服务基类
from ...依赖.cordis.纤程 import 纤程状态#服务是否仍在运行
from ...依赖.schemastery import 字典字段,数字字段#配置
from ...模型后端.llm import 深冻结#冻结配置
from ...模型后端.llm.调用配置 import 是否循环请求#主循环请求
from .异常 import 会话标题错误,会话标题无效错误#本包异常
from .归一 import 归一化会话标题,回退会话标题#标题归一

安全整数上限=9007199254740991#与 JS 安全整数一致

class _中止源:
    '可置位的取消源，记下第一次原因'
    def __init__(自身):
        自身._事件=threading.Event()#置位即取消
        自身.原因=None#第一次原因
    def is_set(自身):
        '是否已取消'
        return 自身._事件.is_set()#已置位
    def abort(自身,原因):
        '置位并保留第一次原因'
        if 自身.原因 is None:#尚未记下
            自身.原因=原因#保留
        自身._事件.set()#置位

class _组合信号:
    '任一源置位即视为取消'
    def __init__(自身,*信号):
        自身._信号=信号#组成源
    def is_set(自身):
        '任一源已取消'
        for 项 in 自身._信号:#逐源
            if 项.is_set():#已取消
                return True#组合取消
        return False#都未取消
    def 原因(自身):
        '第一个已取消源的原因'
        for 项 in 自身._信号:#逐源
            if 项.is_set():#已取消
                return getattr(项,'原因',None)#原因
        return None#未取消

def _用户消息(事件):
    '提取一条合格的人类文本消息'
    if 事件['type']!='user/message':
        return None#跳过
    数据=事件['data']#载荷
    来源=数据['source'] if 'source' in 数据 else None#来源
    if 来源 is None or 来源['kind']!='user':
        return None#跳过
    内容=数据['content'] if 'content' in 数据 and 数据['content'] is not None else []#内容块
    文本块=[]#文本
    for 块 in 内容:
        if isinstance(块,dict) and 块['type']=='text':
            文本块.append(块['text'] if 'text' in 块 else '')#拼文本
    文本='\n'.join(文本块)#拼文本
    if len(归一化会话标题(文本,安全整数上限))==0:
        return None#跳过
    return {'seq':事件['seq'],'text':文本}#消息

def _收集标题消息(事件列表,截止序号=None):
    '按序号收集合格人类消息，可选含截止序号'
    消息列表=[]#结果
    for 事件 in 事件列表:#按日志顺序
        if 截止序号 is not None and 事件['seq']>截止序号:#超过水位
            break#停止
        消息=_用户消息(事件)#提取
        if 消息 is not None:#合格
            消息列表.append(消息)#收集
    return 消息列表#结果

def _复制标题来源(来源):
    '快照不得别名日志里的来源对象'
    种类=来源['kind'] if isinstance(来源,dict) else None#种类
    if 种类=='fallback':#回退
        return {'kind':'fallback'}#拷贝
    if 种类=='user':#用户
        return {'kind':'user'}#拷贝
    if 种类=='provider':#提供方
        结果={'kind':'provider','provider':来源['provider']}#身份
        if 'model' in 来源 and 来源['model'] is not None:#带模型
            模型=来源['model']#模型
            结果['model']={'provider':模型['provider'],'model':模型['model']}#拷贝
        return 结果#拷贝
    raise 会话标题错误('SessionTitleSource')#未知种类

def 折叠会话标题(事件列表):
    '从日志折叠最新标题快照'
    for 事件 in reversed(list(事件列表)):
        if 事件['type']!='session/title':
            continue#继续
        数据=事件['data']#载荷
        序列=数据['messageSeqs'] if 'messageSeqs' in 数据 and 数据['messageSeqs'] is not None else []#序列
        return 深冻结({'title':数据['title'],'messageSeqs':list(序列),'source':_复制标题来源(数据['source']),'eventSeq':事件['seq'],'updatedAt':事件['time']})#快照
    return None#无标题

def 标题状态校验(状态):
    'title 投影只接受非空字符串或空'
    if 状态 is None:#无标题
        return None#空
    if not isinstance(状态,str) or len(状态)==0:#非法
        raise ValueError('title view must be a non-empty string or null')#拒绝
    return 状态#原样

def _标题消息校验(消息):
    '校验一条标题输入消息'
    if not isinstance(消息,dict) or set(消息.keys())!={'seq','text'}:#字段不符
        raise ValueError('title input message is invalid')#拒绝
    序号=消息['seq']#序号
    if isinstance(序号,bool) or not isinstance(序号,int) or 序号<0 or 序号>安全整数上限:#序号非法
        raise ValueError('title input message seq is invalid')#拒绝
    if not isinstance(消息['text'],str):#文本非法
        raise ValueError('title input message text is invalid')#拒绝
    return 消息#原样

def 标题输入校验(状态):
    '计数必须与首尾序号成对'
    if not isinstance(状态,dict) or set(状态.keys())!={'first','count','lastSeq'}:#字段不符
        raise ValueError('title input state must pair its count with first and last message seqs')#拒绝
    首条=状态['first']#首消息
    次数=状态['count']#计数
    末序号=状态['lastSeq']#末序号
    if isinstance(次数,bool) or not isinstance(次数,int) or 次数<0:#计数非法
        raise ValueError('title input state must pair its count with first and last message seqs')#拒绝
    if 末序号 is not None and (isinstance(末序号,bool) or not isinstance(末序号,int) or 末序号<0 or 末序号>安全整数上限):#末序号非法
        raise ValueError('title input state must pair its count with first and last message seqs')#拒绝
    if 首条 is not None:#有首消息
        _标题消息校验(首条)#校验
    空=首条 is None and 末序号 is None and 次数==0#空状态
    有=首条 is not None and 末序号 is not None and 次数>0 and 首条['seq']<=末序号#成对
    if not 空 and not 有:#不成对
        raise ValueError('title input state must pair its count with first and last message seqs')#拒绝
    return 状态#原样

def 标题初始(头):
    'title 投影初值'
    return None#无标题

def 标题应用(状态,事件):
    'title 投影折叠'
    if 事件['type']=='session/title':
        return 事件['data']['title']#新标题
    return 状态#原样

def 标题视图(状态):
    'title 投影视图'
    return 状态#原样

标题投影定义={
    'key':'title','stateVersion':1,'stateSchema':标题状态校验,
    'init':标题初始,
    'apply':标题应用,
    'wire':{'viewSchema':None,'view':标题视图},
}#title 投影

空标题输入={'first':None,'count':0,'lastSeq':None}#titleInput 初始

def _标题输入应用(状态,事件):
    '折叠 titleInput 状态'
    消息=_用户消息(事件)#提取
    if 消息 is None:
        return 状态#原样
    首条=状态['first'] if 'first' in 状态 and 状态['first'] is not None else 消息#首消息
    次数=状态['count'] if 'count' in 状态 else 0#计数
    return {'first':首条,'count':次数+1,'lastSeq':消息['seq']}#更新

def 标题输入初始(头):
    'titleInput 投影初值'
    return dict(空标题输入)#拷贝初值

标题输入投影定义={
    'key':'titleInput','stateVersion':3,'stateSchema':标题输入校验,
    'init':标题输入初始,
    'apply':_标题输入应用,
}#无 wire

包名='@deepseek-ai/dsh-session-title'
名称='session-title'
依赖=['sessions','sessionProjections']#依赖常量
配置模式=字典字段(字典结构={
    'fallbackMaxWords':数字字段(默认值=8),#回退词数
    'fallbackMaxBytes':数字字段(默认值=80),#回退字节
    'maxTitleBytes':数字字段(默认值=200),#标题字节上限
})
__all__=['包名','名称','依赖','应用','默认','会话标题服务','会话标题错误','会话标题无效错误','折叠会话标题','标题投影定义']

class 会话标题服务(服务):
    '日志驱动标题与可选提供方'
    def __init__(自身,上下文,配置值):
        '以 sessionTitle 名安装服务'
        super().__init__(上下文,'sessionTitle')#服务名
        if 配置值 is None or not isinstance(配置值,dict):#配置必须是对象
            raise 会话标题错误('session-title: configuration is required')#拒绝
        for 键 in ('fallbackMaxWords','fallbackMaxBytes','maxTitleBytes'):
            值=配置值[键]#读配置
            if not isinstance(值,int) or isinstance(值,bool) or 值<=0:
                raise 会话标题错误('session-title: '+键+' must be a positive integer')#拒绝
        if 配置值['fallbackMaxBytes']>配置值['maxTitleBytes']:
            raise 会话标题错误('session-title: fallbackMaxBytes must not exceed maxTitleBytes')#拒绝
        自身._配置=深冻结(dict(配置值))#冻结配置
        自身._登记=None#当前提供方登记
        自身._工作={}#每会话工作状态
        自身._在途=set()#拆除时要等的完成事件
        自身._锁=threading.Lock()#工作表
        自身._生命周期=_中止源()#拆除后置位
        上下文.sessionProjections.登记(标题投影定义)#title 单元
        上下文.sessionProjections.登记(标题输入投影定义)#titleInput 单元
        上下文.监听('session/event',自身._路由事件)#事件路由
        def 主请求(选项,下一步):
            '主循环请求到达时启动待处理标题'
            自身._处理主请求(选项)#先看待处理
            return 下一步()#再往下走
        上下文.监听('llm/stream',主请求,{'全局':True,'前置':True})#插到瀑布最前
        上下文.监听('session/disposed',自身._会话已拆除)#会话离开
        def 拆除效果():
            '服务拆除'
            def 拆除():
                '中止在途工作并等它们停'
                自身._生命周期.abort(会话标题错误('session-title service disposed'))#标记拆除
                if 自身._登记 is not None:#有登记
                    自身._登记['closing']=True#晚到结果不得提交
                自身._登记=None#清登记
                for 状态 in list(自身._工作.values()):#逐会话
                    状态['pending']=None#丢掉待处理
                    活动=状态.get('active')#在途
                    if 活动 is not None:#有在途
                        活动['controller'].abort(会话标题错误('session-title service disposed'))#取消
                自身._排空(自身._在途)#等停
                自身._工作.clear()#清工作表
            return 拆除#拆除器
        上下文.副作用(拆除效果,'sessionTitle lifecycle')#生命周期

    def _服务仍活动(自身):
        '所属插件仍在运行'
        if 自身._生命周期.is_set():#已拆除
            return False#停
        纤程=自身.ctx.纤程#所属纤程
        return 纤程.编号 is not None and 纤程.状态==纤程状态.已激活#仍激活

    def _断言服务活动(自身):
        '已卸载则拒绝'
        if not 自身._服务仍活动():#已停
            raise 会话标题错误('session-title service disposed')#拒绝

    def _路由事件(自身,会话,事件):
        '按类型分发'
        if not 自身._服务仍活动():#已停
            return#忽略
        类型=事件['type']#类型
        if 类型=='user/message':
            自身._处理用户消息(会话,事件)#处理
        elif 类型=='request/header':
            自身._处理请求头(会话,事件)#处理

    def 获取(自身,会话):
        '读折叠标题'
        return 折叠会话标题(会话.snapshotEvents())#折叠快照

    def 重命名(自身,会话,标题):
        '接受显式用户标题，并钉住后续自动生成'
        自身._断言服务活动()#仍在运行
        if 自身.ctx.sessions.get(会话.id) is not 会话:
            raise 会话标题错误('session "'+str(会话.id)+'" is not live in this store')#拒绝
        归一=归一化会话标题(标题,自身._配置['maxTitleBytes'])#归一
        if len(归一)==0:
            raise 会话标题无效错误('session title must contain visible characters')#拒绝
        状态=自身._工作状态(会话)#工作状态
        自身._取代(状态,'user rename superseded automatic title generation')#取消在途
        会话.append('session/title',{'title':归一,'messageSeqs':[],'source':{'kind':'user'}})#追加
        结果=自身.获取(会话)#再读
        if 结果 is None:
            raise 会话标题错误('renamed title failed to fold')
        return 结果#快照

    def 刷新(自身,会话,信号=None):
        '显式重试提供方；没有提供方时改写回退，从而解开用户钉住'
        if 信号 is not None and 信号.is_set():#调用方已取消
            raise 会话标题错误('aborted')#拒绝
        自身._断言服务活动()#仍在运行
        if 自身.ctx.sessions.get(会话.id) is not 会话:
            raise 会话标题错误('session "'+str(会话.id)+'" is not live in this store')#拒绝
        登记=自身._登记#当前登记
        输入=自身._标题输入(会话)#输入
        末序号=输入['lastSeq'] if 输入 is not None else None#末条
        if 登记 is None or 登记['closing'] or 末序号 is None:#无提供方或无输入
            当前=自身.获取(会话)#当前标题
            首条=输入['first'] if 输入 is not None else None#首条
            if 当前 is not None and 当前['source']['kind']=='user' and 首条 is not None:#解开钉住
                自身._追加回退(会话,首条)#覆盖回退
                if 信号 is not None and 信号.is_set():#调用方已取消
                    raise 会话标题错误('aborted')#拒绝
                return 自身.获取(会话)#再读
            回退=自身._确保回退(会话)#补回退
            if 信号 is not None and 信号.is_set():#调用方已取消
                raise 会话标题错误('aborted')#拒绝
            return 回退#回退或已有标题
        状态=自身._工作状态(会话)#工作状态
        修订=自身._取代(状态,'explicit title refresh superseded older generation')#新修订
        工作=自身._激活({'registration':登记,'revision':修订,'throughSeq':末序号},状态,信号)#激活
        头=会话.请求头()#当前头
        路由=None#默认无路由
        if isinstance(头,dict) and isinstance(头.get('config'),dict):#有配置
            路由={'provider':头['config']['provider'],'model':头['config']['model']}#记下
        return 自身._跟踪(lambda:自身._运行提供方(会话,工作,路由),登记)#同步跑完

    def 登记提供方(自身,提供方):
        '登记唯一可选提供方；关闭中的登记可以被替换'
        自身._校验提供方(提供方)#先校验
        if 自身._登记 is not None and not 自身._登记['closing']:#仍有活动登记
            raise 会话标题错误('session-title provider "'+str(自身._登记['provider']['id'])+'" is already registered')#拒绝的是已有 id
        登记={'provider':提供方,'active':set(),'closing':False}#新一代
        def 效果():
            '登记并在拆除时取消它的工作'
            自身._登记=登记#发布
            def 拆除():
                '取消这一代并等它停'
                登记['closing']=True#晚到结果不得提交
                for 状态 in list(自身._工作.values()):#逐会话
                    待处理=状态.get('pending')#待处理
                    if 待处理 is not None and 待处理['registration'] is 登记:#属于这一代
                        状态['pending']=None#丢掉
                    活动=状态.get('active')#在途
                    if 活动 is not None and 活动['registration'] is 登记:#属于这一代
                        活动['controller'].abort(会话标题错误('session-title provider "'+str(提供方['id'])+'" was disposed'))#取消
                自身._排空(登记['active'])#等停
                if 自身._登记 is 登记:#仍是这一代
                    自身._登记=None#清掉
            return 拆除#拆除器
        return 自身.ctx.副作用(效果,'sessionTitle.register()')#绑定寿命

    def _处理用户消息(自身,会话,事件):
        '用户钉住则跳过；否则按提供方节奏挂起，并推迟回退'
        if not 自身._服务仍活动():#已停
            return#忽略
        来源=事件['data']['source'] if 'source' in 事件['data'] else None#来源
        if 来源 is None or 来源['kind']!='user' or _用户消息(事件) is None:#不合格
            return#跳过
        当前=自身.获取(会话)#当前标题
        if 当前 is not None and 当前['source']['kind']=='user':#用户钉住
            return#不自动改
        登记=自身._登记#当前登记
        if 登记 is not None and not 登记['closing']:#有活动提供方
            次数=自身._标题输入(会话)['count']#已折叠条数
            无父='parentSession' not in 会话.header#不是子会话
            应调度=登记['provider']['automatic']=='all-prompts' or (无父 and 次数==1 and 自身.获取(会话) is None)#节奏
            if 应调度:#需要自动标题
                状态=自身._工作状态(会话)#工作状态
                修订=自身._取代(状态,'newer user message superseded title generation')#取消旧的
                状态['pending']={'registration':登记,'revision':修订,'throughSeq':事件['seq']}#等请求头
        def 回退任务():
            '失败只记警告'
            try:#回退
                自身._确保回退(会话)#补标题
            except Exception as 错误:#失败
                if not 自身._服务仍活动():#已停
                    return#忽略
                自身.ctx.日志.警告('session "'+str(会话.id)+'": fallback title update failed: '+str(错误))#警告
        自身._推迟(回退任务)#脱离事件处理

    def _处理请求头(自身,会话,事件):
        '请求头序号晚于待处理水位时，用头里的路由启动'
        if not 自身._服务仍活动():#已停
            return#忽略
        状态=自身._工作.get(会话)#工作状态
        待处理=状态.get('pending') if 状态 is not None else None#待处理
        if 状态 is None or 待处理 is None or 待处理['throughSeq']>=事件['seq']:#没有更晚的头
            return#跳过
        配置=事件['data']['header']['config']#头配置
        自身._开始待处理(会话,状态,待处理,{'provider':配置['provider'],'model':配置['model']})#启动

    def _处理主请求(自身,选项):
        '路由未变的主循环请求，在步骤已开始且头已对齐时启动'
        if not 自身._服务仍活动() or not isinstance(选项,dict) or 'sessionId' not in 选项 or 选项['sessionId'] is None or not 是否循环请求(选项):#不是主循环
            return#跳过
        会话=自身.ctx.sessions.get(选项['sessionId'])#会话
        状态=自身._工作.get(会话) if 会话 is not None else None#工作状态
        待处理=状态.get('pending') if 状态 is not None else None#待处理
        if 会话 is None or 状态 is None or 待处理 is None:#没有待处理
            return#跳过
        边界状态=自身.ctx.sessionProjections.状态(会话,'turnBoundary')#步骤边界
        边界=边界状态.get('lastStepBoundary') if isinstance(边界状态,dict) else None#最近边界
        头=会话.请求头()#当前头
        路由=头.get('config') if isinstance(头,dict) else None#头路由
        对齐=isinstance(边界,dict) and 边界.get('kind')=='start' and isinstance(路由,dict) and 路由.get('provider')==选项.get('provider') and 路由.get('model')==选项.get('model')#头与请求一致
        if not 对齐:#还没对齐
            return#跳过
        自身._开始待处理(会话,状态,待处理,{'provider':选项['provider'],'model':选项['model']})#启动

    def _会话已拆除(自身,会话):
        '会话离开时取消它的标题工作'
        状态=自身._工作.get(会话)#工作状态
        if 状态 is None:#没有
            return#跳过
        活动=状态.get('active')#在途
        if 活动 is not None:#有在途
            活动['controller'].abort(会话标题错误('session disposed during title generation'))#取消
        自身._工作.pop(会话,None)#忘掉

    def _开始待处理(自身,会话,状态,待处理,路由):
        '取走这一修订，并在线程里调用提供方'
        if 状态.get('pending') is 待处理:#仍是这一份
            状态['pending']=None#取走
        def 任务():
            '修订仍当前时才启动'
            if 自身._登记 is not 待处理['registration'] or 待处理['registration']['closing'] or 自身._工作.get(会话) is not 状态 or 状态['revision']!=待处理['revision']:#已过期
                return#丢弃
            工作=自身._激活(待处理,状态)#激活
            try:#生成
                自身._运行提供方(会话,工作,路由)#提交
            except Exception as 错误:#失败
                if 工作['signal'].is_set() or not 自身._服务仍活动():#取消或已停
                    return#忽略
                自身.ctx.日志.警告('session "'+str(会话.id)+'": automatic title generation failed: '+str(错误))#警告
        自身._推迟(任务,待处理['registration'])#脱离

    def _运行提供方(自身,会话,工作,路由):
        '执行并接受当前修订'
        try:#生成与提交
            自身._断言当前(会话,工作)#仍当前
            自身._确保回退(会话)#先有回退
            自身._断言当前(会话,工作)#回退后仍当前
            事件列表=会话.snapshotEvents()#同一快照
            消息列表=_收集标题消息(事件列表,工作['throughSeq'])#水位内消息
            当前标题=折叠会话标题(事件列表)#水位外的当前标题也算
            请求={'session':会话,'messages':消息列表,'signal':工作['signal']}#请求
            if 路由 is not None:#有路由
                请求['route']=路由#带上
            if 当前标题 is not None:#已有标题
                请求['currentTitle']=当前标题#带上
            结果=工作['registration']['provider']['generate'](请求)#生成
            自身._断言当前(会话,工作)#生成后仍当前
            接受=自身._校验结果(结果,消息列表)#校验
            来源={'kind':'provider','provider':工作['registration']['provider']['id']}#来源
            if 'model' in 接受:#带模型
                来源['model']=接受['model']#带上
            会话.append('session/title',{'title':接受['title'],'messageSeqs':list(接受['messageSeqs']),'source':来源})#追加
            return 自身.获取(会话)#再读
        finally:#无论成败
            状态=自身._工作.get(会话)#工作状态
            if 状态 is not None and 状态.get('active') is 工作:#仍是这一份
                状态['active']=None#清掉

    def _校验结果(自身,结果,消息列表):
        '对照请求里的消息校验提供方输出'
        if 结果 is None or not isinstance(结果,dict):#不是对象
            raise 会话标题错误('session-title provider returned an invalid result')#拒绝
        if not isinstance(结果.get('title'),str):#标题不是字符串
            raise 会话标题错误('session-title provider title must be a string')#拒绝
        标题=归一化会话标题(结果['title'],自身._配置['maxTitleBytes'])#归一
        if len(标题)==0:#空
            raise 会话标题错误('session-title provider returned an empty title')#拒绝
        序号列表=结果.get('messageSeqs')#来源序号
        if not isinstance(序号列表,list) or len(序号列表)==0:#空
            raise 会话标题错误('session-title provider must identify at least one source message seq')#拒绝
        顺序={消息['seq']:下标 for 下标,消息 in enumerate(消息列表)}#请求内位置
        接受序号=[]#接受的序号
        先前=-1#上一位置
        for 序号 in 序号列表:#逐个
            合法=not isinstance(序号,bool) and isinstance(序号,int) and 序号>=0 and 序号<=安全整数上限#安全整数
            位置=顺序.get(序号)#请求内位置
            if not 合法 or 位置 is None or 位置<=先前:#缺失、重复或乱序
                raise 会话标题错误('session-title provider messageSeqs must be unique, ordered seqs from the request')#拒绝
            接受序号.append(序号)#收下
            先前=位置#前移
        模型=None#默认无模型
        if 'model' in 结果 and 结果['model'] is not None:#给了模型
            候选=结果['model']#候选
            if not isinstance(候选,dict) or not isinstance(候选.get('provider'),str) or len(候选.get('provider') or '')==0 or not isinstance(候选.get('model'),str) or len(候选.get('model') or '')==0:#非法
                raise 会话标题错误('session-title provider result model must contain non-empty provider and model strings')#拒绝
            模型={'provider':候选['provider'],'model':候选['model']}#拷贝
        接受={'title':标题,'messageSeqs':接受序号}#结果
        if 模型 is not None:#有模型
            接受['model']=模型#带上
        return 接受#结果

    def _断言当前(自身,会话,工作):
        '提供方、修订、会话或信号过期则失败'
        自身._断言服务活动()#仍在运行
        if 工作['signal'].is_set():#已取消
            原因=工作['signal'].原因()#原因
            raise 原因 if isinstance(原因,BaseException) else 会话标题错误('aborted')#抛出原因
        状态=自身._工作.get(会话)#工作状态
        if 自身._登记 is not 工作['registration'] or 状态 is None or 状态.get('active') is not 工作 or 状态['revision']!=工作['revision'] or 自身.ctx.sessions.get(会话.id) is not 会话:#状态变了却没取消
            raise 会话标题错误('session title generation state changed without cancellation')#拒绝

    def _激活(自身,待处理,状态,上游=None):
        '发布这一修订的在途调用'
        控制器=_中止源()#本调用取消
        信号列表=[控制器,自身._生命周期]#服务寿命
        if 上游 is not None:#调用方信号
            信号列表.append(上游)#并入
        工作={**待处理,'controller':控制器,'signal':_组合信号(*信号列表)}#在途
        状态['active']=工作#发布
        return 工作#在途

    def _取代(自身,状态,原因):
        '取消更旧的在途调用并前进修订'
        活动=状态.get('active')#在途
        if 活动 is not None:#有在途
            活动['controller'].abort(会话标题错误(原因))#取消
        状态['pending']=None#丢掉待处理
        状态['revision']=状态.get('revision',0)+1#前进
        return 状态['revision']#新修订

    def _工作状态(自身,会话):
        '取出或创建会话工作状态'
        状态=自身._工作.get(会话)#已有
        if 状态 is None:#没有
            状态={'revision':0,'pending':None,'active':None}#初值
            自身._工作[会话]=状态#记下
        return 状态#状态

    def _标题输入(自身,会话):
        '读取 titleInput；缺席按空状态'
        输入=自身.ctx.sessionProjections.状态(会话,'titleInput')#投影
        if 输入 is None:#缺席
            return dict(空标题输入)#空
        return 输入#状态

    def _推迟(自身,任务,登记=None):
        '把工作放到线程里，拆除时能等它停'
        完成=threading.Event()#完成
        def 跑():
            '活动时才执行'
            try:#执行
                if 自身._服务仍活动():#仍在运行
                    任务()#执行
            finally:#无论成败
                完成.set()#完成
                自身._在途.discard(完成)#摘掉
                if 登记 is not None:#有登记
                    登记['active'].discard(完成)#摘掉
        线程=threading.Thread(target=跑,daemon=True)#后台
        完成._线程=线程#排空时跳过自己
        自身._在途.add(完成)#服务要等
        if 登记 is not None:#提供方也要等
            登记['active'].add(完成)#记下
        线程.start()#启动

    def _跟踪(自身,任务,登记):
        '同步执行，但仍计入拆除等待'
        完成=threading.Event()#完成
        完成._线程=threading.current_thread()#排空跳过调用方
        自身._在途.add(完成)#服务要等
        登记['active'].add(完成)#提供方要等
        try:#执行
            return 任务()#结果
        finally:#无论成败
            完成.set()#完成
            自身._在途.discard(完成)#摘掉
            登记['active'].discard(完成)#摘掉

    def _排空(自身,集合):
        '等待集合里还没结束、且不是当前线程的工作'
        while len(集合)>0:#还有
            当前=list(集合)#快照
            for 完成 in 当前:#逐个
                线程=getattr(完成,'_线程',None)#执行线程
                if 线程 is threading.current_thread():#就是自己
                    集合.discard(完成)#不能等自己
                    continue#下一个
                完成.wait()#等停
                集合.discard(完成)#摘掉

    def _校验提供方(自身,提供方):
        '发布前拒绝畸形登记'
        if 提供方 is None or not isinstance(提供方,dict):#不是对象
            raise 会话标题错误('session-title provider must be an object')#拒绝
        if not isinstance(提供方.get('id'),str) or len(提供方['id'])==0:#空 id
            raise 会话标题错误('session-title provider id must be a non-empty string')#拒绝
        if 提供方.get('automatic') not in ('first-prompt','all-prompts'):#节奏非法
            raise 会话标题错误('session-title provider automatic mode is invalid')#拒绝
        if not callable(提供方.get('generate')):#没有生成
            raise 会话标题错误('session-title provider "'+提供方['id']+'" requires generate()')#拒绝

    def _追加回退(自身,会话,首条):
        '用确定性回退覆盖当前标题'
        标题=回退会话标题(首条['text'],自身._配置['fallbackMaxWords'],自身._配置['fallbackMaxBytes'])#回退
        if len(标题)==0:#导不出
            return#不追加
        会话.append('session/title',{'title':标题,'messageSeqs':[首条['seq']],'source':{'kind':'fallback'}})#追加

    def _确保回退(自身,会话):
        '还没有标题时写第一条确定性回退'
        自身._断言服务活动()#仍在运行
        当前=自身.获取(会话)#已有
        if 当前 is not None:#已有标题
            return 当前#不覆盖
        输入=自身._标题输入(会话)#输入
        首条=输入['first'] if 输入 is not None else None#首条
        if 首条 is None:#没有合格文本
            return None#无标题
        标题=回退会话标题(首条['text'],自身._配置['fallbackMaxWords'],自身._配置['fallbackMaxBytes'])#回退
        if len(标题)==0:#导不出
            return None#无标题
        状态=自身._工作状态(会话)#工作状态
        with 自身._锁:#同一会话只写一次
            已有等待=状态.get('fallback')#别人在写
            if 已有等待 is None:#自己写
                等待=threading.Event()#完成
                状态['fallback']=等待#占位
            else:#等别人
                等待=None#标记为等待方
        if 等待 is None:#别人在写
            已有等待.wait()#等完
            return 自身.获取(会话)#再读
        try:#自己写
            自身._断言服务活动()#仍在运行
            if 自身.ctx.sessions.get(会话.id) is not 会话:#不在线
                raise 会话标题错误('session "'+str(会话.id)+'" is not live in this store')#拒绝
            已接受=自身.获取(会话)#期间可能已有
            if 已接受 is not None:#已有
                return 已接受#不覆盖
            会话.append('session/title',{'title':标题,'messageSeqs':[首条['seq']],'source':{'kind':'fallback'}})#追加
            return 自身.获取(会话)#再读
        finally:#无论成败
            状态.pop('fallback',None)#放锁
            等待.set()#唤醒等待方

def 应用(上下文,配置值):
    '注册会话标题服务'
    会话标题服务(上下文,配置值)#构造即登记

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置模式#框架槽
default=默认#框架槽
