"""插件拥有的人类命令注册表，由交互 UI 适配器共享。"""
import re,uuid,threading#命令名形态、实例令牌与后台观察
from cordis.工具 import 承诺,是否thenable,已兑现#操作链承诺、可等待判定与立刻兑现
from scope import 具名条目,作用域层集#具名登记与作用域层
from typert.protocol import 远程服务,远程#Remote 服务基类与装饰器
from .品牌 import 命令标识#命令生命周期配对品牌
from .类型 import (#再导出类型面字段约定
    命令输入描述字段,#输入提示
    命令结果种类,#结果判别
    命令成功结果字段,#成功结果
    命令失败结果字段,#失败结果
    命令执行字段,#已结算执行
    命令描述字段,#UI 描述
    命令来源映射,#来源映射
    命令来源,#来源联合
    命令运行载荷字段,#run 载荷
    命令完成载荷字段,#done 载荷
)#类型再导出结束
from .远程 import TYPERT_REMOTE,远程贡献对象#Host-for-Client Remote 贡献

名称='commands'#Cordis 插件名
命令名形态=re.compile(r'^[a-z][a-z0-9_-]*$')#合法命令名形态
斜杠命令形态=re.compile(r'^/([a-z][a-z0-9_-]*)(?=$|[\t\n\r ])')#斜杠命令行拆分
缺席=object()#对齐 JS undefined，与显式 None 区分

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 有自有(对象,键):#对象是否自有该键
    """映射或对象是否带有该键。"""
    if 对象 is None:#空
        return False#无
    if isinstance(对象,dict):#映射
        return 键 in 对象#自有键
    return hasattr(对象,键)#属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 解析命令(行):#解析斜杠命令行
    """解析一条精确斜杠命令，不归一化其尾部输入。完整候选命令行不是命令时为 None。"""
    匹配=斜杠命令形态.match(行)#匹配斜杠名
    if 匹配 is None:#不是命令行
        return None#未解析
    名=匹配.group(1)#取出命令名
    if 名 is None:#类型守卫：正则一旦匹配第一捕获组必有
        return None#未解析
    return {'name':名,'rawInput':行[匹配.end(0):]}#名字与逐字尾部输入

def 中止错误(信号):#从信号构造中止错误
    """把任意中止原因收成一个稳定的拒绝 Error。"""
    原因=取字段(信号,'reason')#信号原因
    if isinstance(原因,BaseException):#已是异常
        return 原因#原样用
    if isinstance(原因,str):#字符串原因
        return Exception(原因)#包一层
    return Exception('command aborted')#默认文案

def 渲染抛出(值):#把抛出值收成文本
    """渲染任意抛出值，不信任其字符串强制转换。"""
    try:#尝试字符串化
        return str(值)#普通强制转换
    except Exception:#强制转换自己又抛
        return '<unrenderable thrown value>'#不可渲染占位

def 信号已中止(信号):#对齐 AbortSignal.aborted
    """英文 aborted 或中文 已中止 任一为真则视为已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if getattr(信号,'aborted',False) is True:#英文旗标
        return True#已中止
    if getattr(信号,'已中止',False) is True:#中文旗标
        return True#已中止
    return False#未中止

def 接中止(承诺值,信号):#把承诺接到取消信号
    """拥有它的 UI 请求一旦中止，就停止等待不合作的处理函数。"""
    if 信号已中止(信号):#已经中止则立刻拒绝
        拒绝=承诺()#拒绝承诺
        拒绝.拒绝(中止错误(信号))#按信号拒绝
        return 拒绝#立刻拒绝
    结果=承诺()#竞赛完成与中止
    已结算=[False]#只结算一次
    def 结算(回调):#幂等结算
        """只结算一次。"""
        if 已结算[0]:#已结算
            return#无事
        已结算[0]=True#标记
        回调()#执行结算
    def 在中止(*位置参数):#中止回调
        """按信号拒绝。"""
        结算(lambda:结果.拒绝(中止错误(信号)))#按信号拒绝
    def 等完成():#跟随原承诺
        """跟随原承诺兑现或拒绝。"""
        try:#等原承诺
            值=解开(承诺值)#等待
            结算(lambda:结果.兑现(值))#兑现结果
        except BaseException as 错误:#失败
            if isinstance(错误,BaseException) and not isinstance(错误,Exception):#BaseException 原样
                包装=错误#原样
            elif isinstance(错误,Exception):#已是 Exception
                包装=错误#原样
            else:#非 Error 则包一层
                包装=Exception('command handler rejected with a non-Error value: '+渲染抛出(错误))#包一层
                try:#挂 cause
                    包装.__cause__=错误#对齐 cause
                except Exception:#挂不上则忽略
                    pass#忽略
            结算(lambda:结果.拒绝(包装))#拒绝
    工作=threading.Thread(target=等完成)#后台等完成
    工作.daemon=True#不挡住退出
    工作.start()#启动
    if 信号已中止(信号):#挂监听前已中止
        在中止()#立刻处理
    else:#挂监听
        加监听=getattr(信号,'addEventListener',None)#DOM 风格
        if callable(加监听):#有监听 API
            加监听('abort',在中止,{'once':True})#只听一次中止
        else:#无 DOM 监听则靠处理函数自行检查
            pass#调用方用 aborted 旗标
    return 结果#竞赛承诺

def 归一化定义(定义):#校验并冻结定义
    """在无效命令元数据到达 UI 协议之前拒绝它。返回内部已登记项。"""
    名=取字段(定义,'name')#命令名
    if 名 is None or 命令名形态.fullmatch(名) is None:#名字不合法
        raise TypeError('command name "'+str(名)+'" must match '+str(命令名形态.pattern))#拒绝非法名
    摘要=取字段(定义,'description')#摘要
    if not isinstance(摘要,str):#摘要必须是字符串
        raise TypeError('command "'+名+'" description must be a string')#拒绝非字符串摘要
    if len(摘要.strip())==0:#摘要不得空白
        raise TypeError('command "'+名+'" description must not be empty')#拒绝空摘要
    处理=取字段(定义,'handler')#处理函数
    if not callable(处理):#必须有处理函数
        raise TypeError('command "'+名+'" handler must be a function')#拒绝非函数处理
    原始输入=取字段(定义,'input',缺席)#未信任的输入描述；缺席与 None 区分
    输入=None#归一化后的输入
    if 原始输入 is not 缺席:#提供了 input
        if (not isinstance(原始输入,dict)) or (not isinstance(取字段(原始输入,'hint'),str)):#hint 必须是字符串
            raise TypeError('command "'+名+'" input hint must be a string')#拒绝非法 hint
        if len(取字段(原始输入,'hint').strip())==0:#hint 不得空白
            raise TypeError('command "'+名+'" input hint must not be empty')#拒绝空 hint
        输入={'hint':取字段(原始输入,'hint')}#冻结 hint
    归一={'name':名,'description':摘要,'handler':处理}#完整定义
    if 输入 is not None:#可选输入
        归一['input']=输入#带上输入
    if 有自有(定义,'recordInput'):#可选是否记录输入
        归一['recordInput']=取字段(定义,'recordInput')#带上旗标
    描述={'name':归一['name'],'description':归一['description']}#给 UI 的不可变视图
    if 输入 is not None:#可选输入
        描述['input']=输入#带上输入
    return {'definition':归一,'descriptor':描述}#内部登记项

def 归一化结果(命令,值):#校验处理结果
    """在注册表边界校验并剥离未信任的处理函数结果。"""
    if (not isinstance(值,dict)) or (not 有自有(值,'kind')):#必须是带 kind 的对象
        raise TypeError('command "'+命令+'" handler must return a CommandResult')#拒绝非结果
    种类=取字段(值,'kind')#判别标签
    if 种类=='success':#成功分支
        文本=取字段(值,'text',缺席)#可选文本
        if 文本 is not 缺席 and not isinstance(文本,str):#可选文本必须是字符串
            raise TypeError('command "'+命令+'" success text must be a string when supplied')#拒绝非法成功文本
        序号=取字段(值,'sourceEventSeq',缺席)#可选序号
        if 序号 is not 缺席:#提供了序号
            if (not isinstance(序号,int)) or isinstance(序号,bool) or 序号<0:#必须非负安全整数
                raise TypeError('command "'+命令+'" success sourceEventSeq must be a non-negative safe integer when supplied')#拒绝非法序号
            if abs(序号)>9007199254740991:#超出 JS 安全整数
                raise TypeError('command "'+命令+'" success sourceEventSeq must be a non-negative safe integer when supplied')#拒绝非法序号
        结果={'kind':'success'}#冻结成功结果
        if 文本 is not 缺席:#可选文本
            结果['text']=文本#带上文本
        if 序号 is not 缺席:#可选权威序号
            结果['sourceEventSeq']=序号#带上序号
        return 结果#成功结果
    if 种类=='error':#失败分支
        文本=取字段(值,'text')#错误文本
        if (not isinstance(文本,str)) or len(文本.strip())==0:#错误文本必须非空
            raise TypeError('command "'+命令+'" error text must be a non-empty string')#拒绝空错误文本
        return {'kind':'error','text':文本}#冻结失败结果
    raise TypeError('command "'+命令+'" returned unknown result kind "'+str(种类)+'"')#未知 kind

class 命令层:#一层全局或作用域层所拥有的全部命令登记
    """一层全局或作用域层所拥有的全部命令登记。"""
    def __init__(自身,作用域):#按作用域构造层
        """创建一层带其所有权作用域专用诊断的命令层。全局登记时作用域为 None。"""
        def 重复错误(名):#重复登记时报错
            """重复登记诊断。"""
            if 作用域 is None:#全局
                return Exception('command "'+名+'" is already registered (for a per-agent variant, mount a command-injected plugin under that agent\'s `agent.ctx`)')#全局重复
            return Exception('command "'+名+'" is already registered in this scope')#作用域内重复
        自身.命令=具名条目(重复错误)#本层具名登记

    def 是否空(自身):#层是否为空
        """本层是否没有任何命令登记。"""
        return 自身.命令.是否空()#转给具名条目

class 命令运行时(远程服务):#人类命令注册表
    """人类命令注册表。普通上下文上的定义是全局的；经智能体上下文的命令注入子上下文登记的定义，对该智能体遮蔽全局项。"""
    def __init__(自身,上下文对象):#把本服务登记为 commands
        """以 commands 名安装服务。"""
        super().__init__(上下文对象,'commands')#以 commands 名安装远程服务
        def 建层(作用域):#层工厂
            """按作用域建层。"""
            return 命令层(作用域)#建层
        def 层变():#层变则通知观察者
            """层变则通知观察者。"""
            自身.通知变更()#扇出注册表变更
        自身.层集=作用域层集(建层,层变)#全局加作用域层
        自身.命令序号=0#配对序号：铸造命令标识背后按实例单调的计数器
        自身.实例令牌=uuid.uuid4().hex[:8]#实例令牌，使铸造的 id 在同一次恢复日志上跨进程重启仍唯一

    def 登记(自身,定义):#登记一条命令
        """登记一条全局或调用智能体作用域的命令。返回注销本定义的精确 effect disposer。"""
        已登记=归一化定义(定义)#先校验冻结
        def 插入(层):#插入具名条目
            """插入具名条目。"""
            return 层.命令.插入(已登记['definition']['name'],已登记)#插入
        return 自身.层集.副作用(自身.ctx,插入,{'标签':'commands.register()'})#按调用上下文装进层

    def 列出(自身,智能体):#列出有效描述
        """列出一个智能体的有效不可变命令描述。作用域遮蔽之后按名排序。"""
        列表=[项['descriptor'] for 项 in 自身.视图(智能体).values()]#只要描述
        列表.sort(key=lambda 项:取字段(项,'name'))#按名排序；有效视图里名字唯一
        return 列表#不可变视图按约定交出去

    @远程('list')
    def list(自身,智能体):#远程导出名 list → 列出
        """Remote 导出名 list。"""
        return 自身.列出(智能体)#转中文实现

    def 查找(自身,智能体,名):#按名查找定义
        """解析一条有效命令定义。返回作用域遮蔽项或全局定义。"""
        项=自身.视图(智能体).get(名)#有效视图上取值
        if 项 is None:#未找到
            return None#缺席
        return 项['definition']#定义

    def 执行(自身,智能体,行,信号):#解析并执行命令行
        """解析并执行一条已知命令，不把它发给模型。

        已解析命令的生命周期会被记录：调用处理函数之前追加 command/run，结算之后追加 command/done（抛出或中止的处理函数结算为 kind:error）。两者都是直接的仅日志追加——没有回合包住它们，持久化在普通检查点排空它们。准入未命中（句法或未知名）什么也不记——它们从未进入处理函数。command/run 追加失败会让执行大声失败；处理函数失败路径上的 command/done 追加失败被内含，使处理函数自己的错误仍是所报告的失败。
        """
        已解析=解析命令(行)#先拆句法
        if 已解析 is None:#不是命令行
            return None#未解析
        命令=自身.视图(智能体).get(已解析['name'])#按有效视图解析名
        if 命令 is None:#未知命令
            return None#未解析
        if 信号已中止(信号):#已取消则不进入处理
            raise 中止错误(信号)#抛出中止
        配对标识=自身.铸造命令标识()#铸造本次配对 id
        运行载荷={'commandId':配对标识,'name':已解析['name'],'source':{'kind':'user'}}#写入开始事件
        if 取字段(命令['definition'],'recordInput') is not False:#按定义决定是否记录输入
            运行载荷['args']=已解析['rawInput']#带上逐字输入
        自身.追加生命周期(智能体.session,'command/run',运行载荷)#run 事件
        调用={'commandId':配对标识,'agent':智能体,'rawInput':已解析['rawInput'],'signal':信号}#冻结调用
        try:#调用处理函数
            输出=命令['definition']['handler'](调用)#可能同步或异步
            可等待=输出 if 是否thenable(输出) else 已兑现(输出)#统一成可等待
            结果=归一化结果(已解析['name'],解开(接中止(可等待,信号)))#接到取消并校验结果
        except BaseException as 错误:#处理失败或中止
            if isinstance(错误,Exception) and len(错误.args)>0 and isinstance(错误.args[0],str):#对齐 Error.message
                失败文本=错误.args[0]#失败文本
            else:#非标准异常
                失败文本=渲染抛出(错误)#渲染抛出值
            try:#失败路径也要写 done
                自身.追加生命周期(智能体.session,'command/done',{#写入失败结算
                    'commandId':配对标识,#配对 id
                    'kind':'error',#失败
                    'text':失败文本,#失败文本
                })#done 事件结束
            except BaseException as 追加错误:#done 追加自己失败
                自身.ctx.logger.warn('command "'+已解析['name']+'": command/done append failed: '+渲染抛出(追加错误))#内含追加失败
            raise 错误#仍抛出处理函数错误
        完成载荷={'commandId':配对标识,'kind':结果['kind']}#成功路径写 done
        if 有自有(结果,'text'):#可选文本
            完成载荷['text']=结果['text']#带上文本
        if 结果['kind']=='success' and 有自有(结果,'sourceEventSeq'):#成功时可带权威序号
            完成载荷['sourceEventSeq']=结果['sourceEventSeq']#带上序号
        自身.追加生命周期(智能体.session,'command/done',完成载荷)#done 事件
        return {'commandId':配对标识,'result':结果}#冻结已结算执行

    @远程('execute')
    def execute(自身,智能体,行,信号):#远程导出名 execute → 执行
        """Remote 导出名 execute。"""
        return 自身.执行(智能体,行,信号)#转中文实现

    def 铸造命令标识(自身):#铸造配对 id
        """铸造下一个配对 id（单调；带实例令牌前缀，使恢复日志永不重复同一个）。"""
        自身.命令序号+=1#实例内递增
        return 命令标识('cmd-'+自身.实例令牌+'-'+str(自身.命令序号))#前缀加序号

    def 追加生命周期(自身,会话,类型,数据):#追加生命周期事件
        """直接追加一条仅日志生命周期事件：不为它打开回合，也不强迫刷新——持久化观察急切的 session/event 路径，并在普通检查点与拆除时排空，与其他独立插件事件一样。"""
        return 会话.追加(类型,数据)#两参数仅日志追加

    def 视图(自身,智能体):#有效命令视图
        """先解析全局定义，再叠上精确作用域遮蔽。"""
        return 自身.层集.合并(智能体,lambda 层:层.命令)#合并各层具名条目

    def 通知变更(自身):#扇出注册表变更
        """通知每个注册表观察者，且不让 UI 刷新变成负载关键路径。Cordis emit 用逐个监听：一次同步抛出会饿死后续，因此独立内含每个回调。"""
        参数=['commands/change']#dispatch 参数
        for 回调 in 自身.ctx.events.dispatch('emit',参数):#取出全部监听器
            try:#独立执行
                返回=回调()#可能返回 Promise
                if 是否thenable(返回):#异步拒绝也记日志
                    def 盯住(任务=返回):#收住拒绝
                        """把异步拒绝接到诊断。"""
                        try:#等待
                            任务.等待()#等待
                        except BaseException as 错误:#拒绝
                            自身.ctx.logger.warn('commands/change listener rejected: '+渲染抛出(错误))#警告异步失败
                    线=threading.Thread(target=盯住)#后台
                    线.daemon=True#不挡退出
                    线.start()#启动
            except BaseException as 错误:#同步抛出
                自身.ctx.logger.warn('commands/change listener threw: '+渲染抛出(错误))#警告同步失败

默认=命令运行时#默认导出命令运行时
