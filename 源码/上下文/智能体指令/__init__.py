"""兼容 AGENTS.md 的工作区指令加载器。基线指令在第一次请求之前进入持久上下文；成功的 fs 工具触及会把项目里嵌套、已改和已删的指令送进收件箱。插件生命周期读取使用可选的 ctx.fs 提供方，因此无提供方的产品把它挂成空操作。"""
import os,weakref#工作目录与按会话弱引用
from cordis.工具 import 是否thenable#可等待判定
from llm import 创建用户消息#导入用户消息构造
from .配置 import 配置,解析配置,工作区基线身份#导入配置解析与基线身份
from .文件 import 寻找项目根,加载基线指令集,发现基线指令文件,加载基线指令#导入项目根与基线加载
from .状态 import (
    应用指令版本更新,#提交版本缓存更新
    基线指令状态,#由基线文件得到变更
    名称,#插件名
    调和指令上下文,#动态调和
    工作区上下文消息,#基线上下文消息
)#从状态模块导入
from .渲染 import 渲染工作区上下文#再导出基线渲染

name=名称#Cordis插件名
注入=[]#不静态注入fs，缺提供方时空操作
inject=注入#Cordis依赖声明

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    等待=getattr(值,'等待',None)#兜底等待方法
    if callable(等待):#可等待
        return 等待()#等待
    return 值#同步值

def 若已中止则抛出(信号):#取消优先抛出
    """已取消则抛出。"""
    if 信号 is None:#无信号
        return#放过
    方法=getattr(信号,'throwIfAborted',None)#Node风格
    if callable(方法):#有方法
        方法()#抛出
        return#已检查
    if getattr(信号,'aborted',False):#已中止
        raise Exception('aborted')#取消

def 深相等(左,右):#深相等比较
    """比较两条载荷是否相同。"""
    return 左==右#结构化相等

def 可见基线来源(智能体,权威消息们):#找当前可见的基线来源
    """最新可见基线，没有则为 None。"""
    for 消息 in reversed(list(权威消息们)):#权威消息从新到旧
        来源=取字段(消息,'source')#消息来源
        if 取字段(来源,'kind')=='agent-instructions' and 取字段(来源,'baseline') is True:#找到基线标记
            return 来源#权威基线优先
    for 序号 in reversed(list(智能体.session.surface.nodes)):#表面节点从新到旧
        事件=智能体.session.events[序号]#取该序号事件
        数据=取字段(事件,'data')#事件数据
        来源=取字段(数据,'source')#来源
        if 取字段(事件,'type')=='user/message' and 取字段(来源,'kind')=='agent-instructions' and 取字段(来源,'baseline') is True:#表面基线
            return 来源#表面基线
    return None#没有可见基线

def 是否工作区上下文(消息):#判断是否为工作区指令上下文
    """来源判别标签。"""
    return 取字段(取字段(消息,'source'),'kind')=='agent-instructions'#来源判别标签

def 同上下文载荷(左,右):#比较两条上下文载荷是否相同
    """内容与来源深相等。"""
    return 深相等(取字段(左,'content'),取字段(右,'content')) and 深相等(取字段(左,'source'),取字段(右,'source'))#内容与来源

文件触及工具名=set(('read','write','edit'))#会触及文件路径的工具名

def 执行中的文件路径(执行):#从工具执行抽出file_path
    """不是读写改或参数非法则无路径。"""
    if 取字段(执行,'name') not in 文件触及工具名:#不是读写改则无路径
        return None#无
    参数=取字段(执行,'arguments')#参数
    if not isinstance(参数,dict) or 参数 is None:#参数必须是对象
        return None#无
    路径=取字段(参数,'file_path')#file_path
    if not isinstance(路径,str):#必须有字符串file_path
        return None#无
    路径=路径.strip()#去掉首尾空白
    return 路径 if len(路径)>0 else None#空串不当作路径

def 应用(上下文,配置值):#注册工作区指令插件
    """组装基线、调和增量，并把期望上下文同步进收件箱。"""
    已解析=解析配置(配置值)#解析运行时配置
    指令版本=weakref.WeakKeyDictionary()#按会话隔离的版本缓存
    基线准备=weakref.WeakKeyDictionary()#上次基线准备：身份与预算外作用域
    投影已拆除={'aborted':False}#插件拆除时取消进行中的投影
    执行触及={}#按执行令牌收集触及，供父执行合并
    def 拆除投影():#拆除时中止投影生命周期
        """取消进行中的投影。"""
        投影已拆除['aborted']=True#标记拆除
        执行触及.clear()#丢掉未完成的触及
    def 投影生命周期():#effect工厂：返回拆除器
        """登记拆除器。"""
        return 拆除投影#返回disposer
    上下文.effect(投影生命周期,'agent-instructions.projectionLifecycle')#拆除时中止投影生命周期
    class 投影信号:#投影生命周期取消信号
        """对齐 AbortSignal：aborted 与 throwIfAborted。"""
        @property#只读
        def aborted(自身):#是否已拆除
            """是否已拆除。"""
            return 投影已拆除['aborted']#拆除标记
        def throwIfAborted(自身):#已拆除则抛出
            """已拆除则抛出。"""
            if 投影已拆除['aborted']:#已拆除
                raise Exception('agent-instructions disposed')#取消进行中的投影
    投影生命周期信号=投影信号()#单例信号
    投影尾=weakref.WeakKeyDictionary()#每智能体的投影串行尾
    打开步骤=weakref.WeakKeyDictionary()#会话当前步骤是否仍打开
    步骤触及=weakref.WeakKeyDictionary()#打开步骤内暂存的触及，步骤结束后再投影
    def 组装(智能体,信号,已声明,待处理,触及路径们=None):#组装期望的工作区上下文消息
        """有期望上下文则返回。"""
        if 触及路径们 is None:#缺省空触及
            触及路径们=[]#空
        若已中止则抛出(信号)#进入前检查取消
        import math#有限预算
        if 已解析['maxBytes']<=0 or not math.isfinite(已解析['maxBytes']):#预算禁用
            return None#不加载
        文件系统=上下文.get('fs')#可选文件系统提供方
        if 文件系统 is None:#无提供方则空操作
            return None#空操作
        if len(触及路径们)==0 and len(待处理)>0:#无新触及且已有待处理则沿用第一条
            return 待处理[0]#沿用
        内容=[]#累积内容块
        变更们=[]#累积变更
        期望基线=False#本条是否携带基线标记
        权威消息=list(已声明)#可变的权威列表，后面可追加刚组装的基线
        工作目录=取字段(取字段(智能体.session,'header'),'cwd') or os.getcwd()#会话cwd
        项目根=寻找项目根(工作目录,已解析['projectRootMarkers'],文件系统,信号)#寻找项目根
        身份=工作区基线身份(已解析,工作目录,项目根)#发现与预算身份
        可见基线=可见基线来源(智能体,权威消息)#当前可见基线
        基线已在=可见基线 is not None#是否已有基线
        保留可见基线=取字段(可见基线,'baselineIdentity')==身份 if 可见基线 is not None else False#身份是否仍匹配
        已准备=基线准备.get(智能体.session)#上次准备
        排除基线作用域=None#本轮排除集
        if 保留可见基线 and 已准备 is not None and 已准备['identity']==身份:#身份匹配才能复用排除集
            排除基线作用域=已准备['excludedScopes']#复用预算外作用域
        下一准备=None#本轮要记下的准备
        if (not 基线已在) or (not 保留可见基线) or 排除基线作用域 is None:#需要加载或替换基线
            替换先前基线=基线已在 and (not 保留可见基线)#有旧基线但身份变了则整份替换
            指令集=加载基线指令集({#加载基线文件集
                'cwd':工作目录,#工作目录
                'dshHome':已解析['dshHome'],#家目录
                'projectRootMarkers':已解析['projectRootMarkers'],#根标记
                'maxBytes':已解析['maxBytes'],#渲染预算
                'maxSourceBytes':已解析['maxSourceBytes'],#单源上限
                'instructionFileCandidates':已解析['instructionFileCandidates'],#基线候选
                'localInstructionFileCandidates':已解析['localInstructionFileCandidates'],#本地覆盖
                'projectRoot':项目根,#项目根
                'replacePreviousBaseline':替换先前基线,#是否替换
                'signal':信号,#取消
            },文件系统)#提供方
            纳入=取字段(指令集,'included') or [] if 指令集 is not None else []#纳入文件
            观察=取字段(指令集,'observed') or [] if 指令集 is not None else []#观察文件
            基线=基线指令状态(纳入)#纳入文件的变更
            观察基线=基线指令状态(观察)#观察文件的变更
            排除集=set(观察基线['changes'].keys())#先放入全部观察作用域
            for 作用域 in 基线['changes'].keys():#再去掉实际纳入的
                排除集.discard(作用域)#去掉
            排除基线作用域=排除集#本轮排除集
            下一准备={'identity':身份,'excludedScopes':排除集}#记下供后续复用
            版本表=指令版本.get(智能体.session)#现有版本表
            if 版本表 is None and len(基线['versions'])>0:#没有表但有版本要写
                版本表={}#新建
                指令版本[智能体.session]=版本表#挂上
            if 版本表 is not None:#有表
                for 作用域,状态 in 基线['versions'].items():#用基线版本播种缓存
                    版本表[作用域]=状态#播种
            渲染文本=取字段(取字段(指令集,'rendered'),'text') if 指令集 is not None else ''#基线正文
            if (not 保留可见基线) and 指令集 is not None and len(渲染文本)>0:#需要发出新基线正文
                基线内容=取字段(工作区上下文消息(渲染文本),'content')#基线文本块
                内容.extend(基线内容)#先放入基线内容
                替换作用域=set(基线['changes'].keys())#新基线覆盖的作用域
                替换移除=[]#替换时要显式移除旧基线里不再出现的作用域
                if 替换先前基线:#替换
                    for 变更 in 取字段(可见基线,'changes') or []:#扫描旧基线变更
                        if 变更['action']=='remove' or 变更['scope'] in 替换作用域:#已经是移除或新基线仍有
                            continue#不必再移除
                        替换移除.append({'action':'remove','scope':变更['scope'],'path':变更['path']})#声明移除
                基线变更=替换移除+list(基线['changes'].values())#移除在前，set在后
                变更们.extend(基线变更)#记入本条变更
                权威消息.append(创建用户消息({#把新基线当作后续调和的权威
                    'content':基线内容,#基线内容
                    'source':{#基线来源
                        'kind':'agent-instructions',#工作区来源
                        'form':'instructions',#指令形态
                        'baseline':True,#基线标记
                        'baselineIdentity':身份,#身份
                        'changes':基线变更,#基线变更清单
                    },#source结束
                }))#权威消息结束
                期望基线=True#本条带基线标记
        调和选项={#调和选项
            'authorityMessages':权威消息,#含可能刚加入的基线
            'scopeMessages':待处理,#待处理提示
            'includeBaselineScopes':保留可见基线,#仅在保留可见基线时把基线作用域纳入调和
            'touchedPaths':触及路径们,#触及路径
            'projectRoot':项目根,#项目根
            'signal':信号,#取消
        }#选项骨架
        if 保留可见基线:#保留基线时才传排除集
            调和选项['excludedBaselineScopes']=排除基线作用域#排除集
        更新=调和指令上下文(智能体,已解析,指令版本,文件系统,调和选项)#再调和动态增量
        if 更新 is not None:#有增量上下文
            内容.extend(取字段(取字段(更新,'context'),'content') or [])#追加增量文本
            来源=取字段(取字段(更新,'context'),'source')#增量来源
            if 取字段(来源,'kind')=='agent-instructions':#来源必为本包
                变更们.extend(取字段(来源,'changes') or [])#追加增量变更
            应用指令版本更新(智能体.session,更新['versionUpdates'],指令版本)#提交被代表的缓存更新
        if 下一准备 is not None:#记下本轮准备
            基线准备[智能体.session]=下一准备#记下
        if len(内容)==0:#既无基线也无增量
            return None#无
        来源={#合并来源
            'kind':'agent-instructions',#工作区来源
            'form':'instructions',#指令形态
            'changes':变更们,#全部变更
        }#来源骨架
        if 期望基线:#有基线才打标记
            来源['baseline']=True#基线标记
            来源['baselineIdentity']=身份#身份
        return 创建用户消息({'content':内容,'source':来源})#组装最终期望消息
    def 同步收件箱(智能体,已声明,期望):#把期望上下文同步进收件箱
        """写入或清理下一步工作区上下文。"""
        待处理=[消息 for 消息 in 智能体.inbox.nextStep if 是否工作区上下文(消息)]#下一步里已有的工作区上下文
        已供给=False#期望是否已被权威或表面覆盖
        if 期望 is not None:#有期望
            已供给=any(同上下文载荷(消息,期望) for 消息 in 已声明)#已在本步声明
            if not 已供给:#再看表面
                for 序号 in 智能体.session.surface.nodes:#或已在表面
                    事件=智能体.session.events[序号]#取事件
                    if 取字段(事件,'type')=='user/message' and 同上下文载荷(取字段(事件,'data'),期望):#载荷相同
                        已供给=True#已供给
                        break#停
        if 期望 is None or 已供给:#不需要待处理上下文
            for 消息 in 待处理:#清掉多余待处理
                智能体.inbox.remove(取字段(消息,'id'))#删除
            return#同步结束
        可复用=None#能否复用已有待处理
        for 消息 in 待处理:#查找相同载荷
            if 同上下文载荷(消息,期望):#已有相同载荷
                可复用=消息#记下
                break#停
        if 可复用 is not None:#已有相同载荷
            for 消息 in 待处理:#只留这一条
                if 消息 is not 可复用:#其他
                    智能体.inbox.remove(取字段(消息,'id'))#删掉其他
            return#复用完成
        被替=待处理[0] if len(待处理)>0 else None#第一条待处理
        if 被替 is None:#没有则插入下一步
            智能体.inbox.prepend('next-step',期望)#插入
        else:#有则替换第一条
            智能体.inbox.replace(取字段(被替,'id'),期望)#替换
        for 消息 in 待处理[1:]:#删掉其余待处理
            智能体.inbox.remove(取字段(消息,'id'))#删除
    def 组装并同步(智能体,信号,已声明,触及路径们=None):#组装并同步收件箱
        """完成后无返回。"""
        if 触及路径们 is None:#缺省
            触及路径们=[]#空
        待处理=[消息 for 消息 in 智能体.inbox.nextStep if 是否工作区上下文(消息)]#当前待处理
        期望=组装(智能体,信号,已声明,待处理,触及路径们)#组装期望
        若已中止则抛出(信号)#同步前检查取消
        同步收件箱(智能体,已声明,期望)#写入收件箱
    def 排队投影(智能体,触及路径):#排队一次文件触及投影
        """同步串行跑投影；拆除后不再启动。"""
        if 投影已拆除['aborted']:#已拆除
            return#不再投影
        try:#投影可能失败
            组装并同步(智能体,投影生命周期信号,[],[触及路径])#叠在串行路径上组装同步
        except Exception as 错误:#吞掉投影失败以免断链
            if not 投影已拆除['aborted']:#拆除以外的失败记警告
                上下文.logger.warn('workspace instruction refresh failed: %o',错误)#记警告
        try:#清掉占位尾，避免弱引用表泄漏
            del 投影尾[智能体]#清掉
        except KeyError:#本无尾
            pass#放过
    def 等待投影(智能体):#等到该智能体投影队列排空
        """同步实现下投影已在排队时跑完。"""
        return#无挂起尾
    def 步骤已打开(会话):#判断会话是否有打开的步骤
        """从缓存或事件重放开关。"""
        已知=打开步骤.get(会话)#缓存的开关
        if 已知 is not None:#已跟踪则直接用
            return 已知#直接用
        打开=False#从事件重放开关
        for 事件 in 会话.events:#扫描全部事件
            种类=取字段(事件,'type')#事件类型
            if 种类=='step/start':#步骤开始
                打开=True#打开
            elif 种类 in ('step/end','turn/end'):#步骤或回合结束
                打开=False#关闭
        打开步骤[会话]=打开#记下
        return 打开#返回
    def 投影触及(触及):#按步骤边界决定立刻投影还是暂存
        """步骤已关闭则立刻排队，否则暂存。"""
        会话=触及['agent'].session#所属会话
        if not 步骤已打开(会话):#步骤已关闭
            排队投影(触及['agent'],触及['path'])#立刻排队投影
            return#处理完
        待存=步骤触及.get(会话)#打开步骤内的暂存
        if 待存 is None:#新建列表
            步骤触及[会话]=[触及]#新建
        else:#追加
            待存.append(触及)#追加
    def 会话事件(会话,事件):#跟踪步骤开关并在步骤结束时放出暂存触及
        """step/start 打开；turn/end 关闭；step/end 关闭并放出暂存。"""
        种类=取字段(事件,'type')#事件类型
        if 种类=='step/start':#步骤开始
            打开步骤[会话]=True#标记打开
            return#不必再看
        if 种类=='turn/end':#回合结束也关闭步骤
            打开步骤[会话]=False#标记关闭
            return#触及仍留到显式step/end处理
        if 种类!='step/end':#其他事件忽略
            return#忽略
        打开步骤[会话]=False#步骤结束
        待存=步骤触及.get(会话)#取出暂存
        if 待存 is None:#没有触及
            return#结束
        try:#清掉暂存
            del 步骤触及[会话]#清掉
        except KeyError:#已无
            pass#放过
        for 触及 in 待存:#步骤提交后再投影
            排队投影(触及['agent'],触及['path'])#投影
    上下文.on('session/event',会话事件)#跟踪步骤开关
    def 预步骤(参数,下一环):#预步骤：先委托再把工作区上下文折进本步
        """返回进入或拒绝。"""
        智能体=取字段(参数,'agent')#会话所有者
        消息们=取字段(参数,'messages')#已声明消息
        步骤=取字段(参数,'step')#步骤号
        信号=取字段(参数,'signal')#取消
        决定=解开(下一环())#先让后续监听器决定
        等待投影(智能体)#等文件触及投影排空
        待处理=[消息 for 消息 in 智能体.inbox.nextStep if 是否工作区上下文(消息)]#当前待处理上下文
        期望=组装(智能体,信号,消息们,待处理)#组装期望
        若已中止则抛出(信号)#同步前检查取消
        if 取字段(决定,'kind')=='reject' or (步骤==1 and len(取字段(决定,'messages') or [])==0):#拒绝或空首步
            同步收件箱(智能体,消息们,期望)#只同步收件箱，不进入本步
            return 决定#原样返回
        for 消息 in 待处理:#前进的步骤会结清待处理上下文
            智能体.inbox.remove(取字段(消息,'id'))#清掉待处理
        决定消息=取字段(决定,'messages') or []#决定消息
        if 期望 is None or any(同上下文载荷(消息,期望) for 消息 in 决定消息):#无期望或已覆盖
            return 决定#不插入
        最后声明=-1#最后一条已声明消息下标
        for 下标,消息 in enumerate(决定消息):#找最后声明
            if 消息 in 消息们:#属于已声明批次
                最后声明=下标#更新
        进入=list(决定消息)#拷贝
        进入.insert(最后声明+1,期望)#插在声明批次之后
        return {'kind':'enter','messages':进入}#带着插入后的消息进入
    上下文.on('agent/pre-step',预步骤)#预步骤瀑布
    def 工具结果(执行,结果):#工具结果：收集文件触及并在根执行提交
        """根执行按步骤边界投影；嵌套执行上交给父令牌。"""
        令牌=取字段(执行,'token')#执行令牌
        触及们=执行触及.pop(令牌,[])#本执行及其子执行累积的触及
        if (not 取字段(结果,'isError')) and 取字段(执行,'agent') is not None and (not getattr(取字段(执行,'signal'),'aborted',False)):#成功且未取消
            自身路径=执行中的文件路径(执行)#自身file_path
            if 自身路径 is not None:#有路径
                触及们.append({'agent':取字段(执行,'agent'),'path':自身路径})#记入触及
        父令牌=取字段(执行,'parent')#父执行令牌
        if 父令牌 is not None:#嵌套执行：交给父令牌，等根执行再投影
            if len(触及们)>0:#有触及要上交
                父触及=执行触及.get(父令牌)#父已有列表
                if 父触及 is None:#新建
                    执行触及[父令牌]=触及们#新建
                else:#追加
                    父触及.extend(触及们)#追加
            return#非根执行不投影
        for 触及 in 触及们:#根执行按步骤边界投影
            投影触及(触及)#投影
    上下文.on('tools/result',工具结果)#工具结果

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
