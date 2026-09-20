"""插件拥有的人类命令注册表，由交互 UI 适配器共享。"""
import re,uuid#命令名形态与实例令牌
from ...依赖.工具 import 获取内部数据#读事件总线内部成员
from ...内核.作用域 import 具名条目,作用域层集#具名登记与作用域层
from ...typert.协议 import 远程服务,远程 as _远程#Remote 服务基类与装饰器
from ...工具.超时 import 已中止,若已中止则抛出#中止入口
from ...附件.附件 import 附件错误,准入编码图像批次#附件错误与图片准入
from .标识构造 import 命令定义标识,命令标识#命令定义身份与生命周期配对标识
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

命令名形态=re.compile(r'^[a-z][a-z0-9_-]*\Z',re.ASCII)#合法命令名形态
斜杠命令形态=re.compile(r'^/([a-z][a-z0-9_-]*)(?=\Z|[\t\n\r ])',re.ASCII)#斜杠命令行拆分
安全整数上限=9007199254740991#外来JSON校验点
空附件=()#无附件调用共享的空附件值

class 命令错误(Exception):#本包登记与执行失败
    """命令登记、执行或中止失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 解析命令(行):#解析斜杠命令行
    """解析一条精确斜杠命令，不归一化其尾部输入。完整候选命令行不是命令时为 None。"""
    匹配=斜杠命令形态.match(行)#匹配斜杠名
    if 匹配 is None:#不是命令行
        return None#未解析
    名=匹配.group(1)#取出命令名
    if 名 is None:#类型守卫：正则一旦匹配第一捕获组必有
        return None#未解析
    return {'name':名,'rawInput':行[匹配.end(0):]}#名字与逐字尾部输入

def 渲染抛出(值):#把抛出值收成文本
    """渲染任意抛出值，不信任其字符串强制转换。"""
    try:#尝试字符串化
        return str(值)#普通强制转换
    except Exception:#强制转换自己又抛
        return '<unrenderable thrown value>'#不可渲染占位

def 归一化定义(定义):#校验并冻结定义
    """在无效命令元数据到达 UI 协议之前拒绝它。定义是 dict。"""
    名=定义['name'] if 'name' in 定义 else None#命令名
    if 名 is None or 命令名形态.fullmatch(名) is None:#名字不合法
        raise TypeError('command name "'+str(名)+'" must match '+str(命令名形态.pattern))#拒绝非法名
    摘要=定义['description'] if 'description' in 定义 else None#摘要
    if not isinstance(摘要,str):#摘要必须是字符串
        raise TypeError('command "'+名+'" description must be a string')#拒绝非字符串摘要
    if len(摘要.strip())==0:#摘要不得空白
        raise TypeError('command "'+名+'" description must not be empty')#拒绝空摘要
    处理=定义['handler'] if 'handler' in 定义 else None#处理函数
    if not callable(处理):#必须有处理函数
        raise TypeError('command "'+名+'" handler must be a function')#拒绝非函数处理
    输入=None#归一化后的输入
    if 'input' in 定义:#提供了 input
        原始输入=定义['input']#未信任的输入描述
        提示=原始输入['hint'] if isinstance(原始输入,dict) and 'hint' in 原始输入 else None#hint
        if (not isinstance(原始输入,dict)) or (not isinstance(提示,str)):#hint 必须是字符串
            raise TypeError('command "'+名+'" input hint must be a string')#拒绝非法 hint
        if len(提示.strip())==0:#hint 不得空白
            raise TypeError('command "'+名+'" input hint must not be empty')#拒绝空 hint
        输入={'hint':提示}#冻结 hint
        if 'attachments' in 原始输入 and 原始输入['attachments'] is not None:#提供了附件旗标
            附件旗=原始输入['attachments']#附件旗标
            if not isinstance(附件旗,bool):#附件标志必须是布尔
                raise TypeError('command "'+名+'" input attachments flag must be a boolean')#拒绝非法附件标志
            if 附件旗 is True:#仅真值写入 attachments
                输入['attachments']=True#接受附件
    归一={'name':名,'description':摘要,'handler':处理}#完整定义
    if 'definitionId' in 定义:#可选定义身份
        归一['definitionId']=定义['definitionId']#带上定义身份
    if 输入 is not None:#可选输入
        归一['input']=输入#带上输入
    if 'recordInput' in 定义:#可选是否记录输入
        归一['recordInput']=定义['recordInput']#带上旗标
    描述={'name':归一['name'],'description':归一['description']}#给 UI 的不可变视图
    if 'definitionId' in 归一:#可选定义身份
        描述['definitionId']=归一['definitionId']#带上定义身份
    if 输入 is not None:#可选输入
        描述['input']=输入#带上输入
    return {'definition':归一,'descriptor':描述}#内部登记项

def 归一化结果(命令,值):#校验处理结果
    """在注册表边界校验并剥离未信任的处理函数结果。值是 dict。"""
    if (not isinstance(值,dict)) or ('kind' not in 值):#必须是带 kind 的对象
        raise TypeError('command "'+命令+'" handler must return a CommandResult')#拒绝非结果
    种类=值['kind']#判别标签
    if 种类=='success':#成功分支
        结果={'kind':'success'}#冻结成功结果
        if 'text' in 值:#可选文本
            文本=值['text']#文本
            if not isinstance(文本,str):#可选文本必须是字符串
                raise TypeError('command "'+命令+'" success text must be a string when supplied')#拒绝非法成功文本
            结果['text']=文本#带上文本
        if 'sourceEventSeq' in 值:#提供了序号
            序号=值['sourceEventSeq']#序号
            if isinstance(序号,bool) or not isinstance(序号,int) or 序号<0 or 序号>安全整数上限:#必须非负安全整数
                raise TypeError('command "'+命令+'" success sourceEventSeq must be a non-negative safe integer when supplied')#拒绝非法序号
            结果['sourceEventSeq']=序号#带上序号
        return 结果#成功结果
    if 种类=='error':#失败分支
        文本=值['text'] if 'text' in 值 else None#错误文本
        if (not isinstance(文本,str)) or len(文本.strip())==0:#错误文本必须非空
            raise TypeError('command "'+命令+'" error text must be a non-empty string')#拒绝空错误文本
        return {'kind':'error','text':文本}#冻结失败结果
    raise TypeError('command "'+命令+'" returned unknown result kind "'+str(种类)+'"')#未知 kind

def 准入命令附件(存储,附件列表,解析文件回执):
    """准入混合命令批次并恢复其原始图片/文件顺序。附件列表是提交附件。"""
    文件表={}#回执到文件引用
    for 附件 in 附件列表:#先解析全部文件回执
        if 附件['type']!='file':#非文件
            continue#跳过
        回执=附件['receiptId']#回执 id
        if 回执 in 文件表:#已解析
            continue#跳过
        文件=解析文件回执(回执)#解析回执
        if 文件 is None:#未知回执
            raise 附件错误('File upload receipt is unknown for this session.','ATTACHMENT_NOT_FOUND')#报告未找到
        文件表[回执]=文件#记下文件引用
    图像列表=[]#收集编码图片
    for 附件 in 附件列表:#再收集图片
        if 附件['type']!='image':#非图片
            continue#跳过
        项={'mediaType':附件['mediaType'],'data':附件['data']}#编码图片
        if 'name' in 附件:#可选名
            项['name']=附件['name']#带上名
        图像列表.append(项)#压入
    图像引用=准入编码图像批次(存储,图像列表) if len(图像列表)>0 else []#准入图片
    图像游标=0#图片游标
    块列表=[]#按提交顺序的块
    for 附件 in 附件列表:#按原序重建
        if 附件['type']=='image':#图片槽
            块列表.append({'type':'image','attachment':图像引用[图像游标]})#压入图片块
            图像游标+=1#推进游标
            continue#下一附件
        块列表.append({'type':'file','attachment':文件表[附件['receiptId']]})#压入文件块
    return 块列表#有序块列表

def 按名(项):#描述按名排序
    """有效视图里名字唯一，按 name 排序。"""
    return 项['name']#名字

def 取层命令(层):#合并时取本层命令表
    """取出一层的具名命令登记。"""
    return 层.命令#本层命令

class 命令层:#一层全局或作用域层所拥有的全部命令登记
    """一层全局或作用域层所拥有的全部命令登记。"""
    def __init__(自身,作用域):#按作用域构造层
        """创建一层带其所有权作用域专用诊断的命令层。全局登记时作用域为 None。"""
        def 重复错误(名):#重复登记时报错
            """重复登记诊断。"""
            if 作用域 is None:#全局
                return 命令错误('command "'+名+'" is already registered (for a per-agent variant, mount a command-injected plugin under that agent\'s `agent.ctx`)')#全局重复
            return 命令错误('command "'+名+'" is already registered in this scope')#作用域内重复
        自身.命令=具名条目(重复错误)#本层具名登记

    def 是否空(自身):#层是否为空
        """本层是否没有任何命令登记。"""
        return 自身.命令.是否空()#转给具名条目

class 命令运行时(远程服务):#人类命令注册表
    """人类命令注册表。普通上下文上的定义是全局的；经智能体上下文的命令注入子上下文登记的定义，对该智能体遮蔽全局项。"""
    def __init__(自身,上下文):#把本服务登记为 commands
        """以 commands 名安装服务。"""
        super().__init__(上下文,'commands')#以 commands 名安装远程服务
        def 建层(作用域):#层工厂
            """按作用域建层。"""
            return 命令层(作用域)#建层
        def 层变():#层变则通知观察者
            """层变则通知观察者。"""
            自身.通知变更()#扇出注册表变更
        自身.层集=作用域层集(建层,层变)#全局加作用域层
        自身.命令序号=0#配对序号
        自身.实例令牌=uuid.uuid4().hex[:8]#实例令牌
        自身.文件回执解析器=None#由 Session 上传所有者安装的可选解析器

    def 登记(自身,定义):#登记一条命令
        """登记一条全局或调用智能体作用域的命令。定义是 dict。"""
        已登记=归一化定义(定义)#先校验冻结
        def 插入(层):#插入具名条目
            """插入具名条目。"""
            return 层.命令.插入(已登记['definition']['name'],已登记)#插入
        return 自身.层集.副作用(自身.ctx,插入,{'标签':'commands.register()'})#按调用上下文装进层

    def 登记文件回执解析器(自身,解析器):#登记文件回执解析器
        """登记解析命令提交所用暂存文件回执的唯一权威。返回移除该精确解析器的拆除器。"""
        if 自身.文件回执解析器 is not None:#已有解析器
            raise 命令错误('commands: a file receipt resolver is already registered')#拒绝重复登记
        自身.文件回执解析器=解析器#装上解析器
        def 拆除():#移除本实例
            """仅移除本实例。"""
            if 自身.文件回执解析器 is 解析器:#仍是本次
                自身.文件回执解析器=None#清空
        return 拆除#拆除器

    @_远程('list')
    def 列出(自身,智能体):#列出有效描述
        """列出一个智能体的有效不可变命令描述。作用域遮蔽之后按名排序。"""
        列表=[项['descriptor'] for 项 in 自身.视图(智能体).values()]#只要描述
        列表.sort(key=按名)#按名排序
        return 列表#不可变视图

    def 查找(自身,智能体,名):#按名查找定义
        """解析一条有效命令定义。"""
        视图=自身.视图(智能体)#有效视图
        if 名 not in 视图:#未找到
            return None#缺席
        return 视图[名]['definition']#定义

    @_远程('execute')
    def 执行(自身,智能体,行,提交附件,信号):#解析并执行命令行
        """解析并执行一条已知命令，不把它发给模型。处理函数按同步调用写死。"""
        已解析=解析命令(行)#先拆句法
        if 已解析 is None:#不是命令行
            return None#未解析
        视图=自身.视图(智能体)#有效视图
        if 已解析['name'] not in 视图:#未知命令
            return None#未解析
        命令=视图[已解析['name']]#命中项
        if 已中止(信号):#已取消则不进入处理
            若已中止则抛出(信号)#抛出中止原因
            raise 命令错误('command aborted')#默认文案
        配对标识=自身.铸造命令标识()#铸造本次配对 id
        运行载荷={'commandId':配对标识,'name':已解析['name'],'source':{'kind':'user'}}#写入开始事件
        定义=命令['definition']#内部定义
        if 'recordInput' not in 定义 or 定义['recordInput'] is not False:#按定义决定是否记录输入
            运行载荷['args']=已解析['rawInput']#带上逐字输入
        自身.追加生命周期(智能体.session,'command/run',运行载荷)#run 事件
        def 结算(结果):#结算并写 done
            """写入 command/done 并返回已结算执行。"""
            完成载荷={'commandId':配对标识,'kind':结果['kind']}#结算事件
            if 'text' in 结果:#可选文本
                完成载荷['text']=结果['text']#带上文本
            if 结果['kind']=='success' and 'sourceEventSeq' in 结果:#成功时可带权威序号
                完成载荷['sourceEventSeq']=结果['sourceEventSeq']#带上序号
            自身.追加生命周期(智能体.session,'command/done',完成载荷)#done 事件
            return {'commandId':配对标识,'result':结果}#冻结已结算执行
        附件块=空附件#默认无附件
        if len(提交附件)>0:#有提交附件
            输入=定义['input'] if 'input' in 定义 else None#输入描述
            if 输入 is None or ('attachments' not in 输入) or 输入['attachments'] is not True:#命令不接受附件
                return 结算({'kind':'error','text':'/'+已解析['name']+' does not accept attachments'})#错误结算
            存储=自身.ctx.获取服务('attachments',False)#取附件存储
            if 存储 is None:#未组合附件存储
                return 结算({'kind':'error','text':'/'+已解析['name']+': attachments are unavailable because no attachment store is composed'})#错误结算
            try:#准入附件
                def 解析回执(回执标识):#解析文件回执
                    """Session 作用域回执解析。"""
                    if 自身.文件回执解析器 is None:#未安装
                        return None#未知
                    return 自身.文件回执解析器(智能体,回执标识)#解析
                附件块=准入命令附件(存储,提交附件,解析回执)#混合批次准入
            except 附件错误 as 错误:#已知附件错误
                return 结算({'kind':'error','text':str(错误)})#错误结算
            except BaseException as 错误:#准入失败
                自身.失败结算(智能体.session,已解析['name'],配对标识,错误)#内含写 done
                raise 错误#仍抛出
            if 已中止(信号):#准入期间取消
                取消错误=命令错误('command aborted')#归一化取消
                自身.失败结算(智能体.session,已解析['name'],配对标识,取消错误)#内含写 done
                若已中止则抛出(信号)#抛出中止原因
                raise 取消错误#抛出取消
        调用={'commandId':配对标识,'agent':智能体,'rawInput':已解析['rawInput'],'attachments':附件块,'signal':信号}#冻结调用
        try:#调用处理函数
            输出=定义['handler'](调用)#同步处理
            结果=归一化结果(已解析['name'],输出)#校验结果
        except BaseException as 错误:#处理失败或中止
            自身.失败结算(智能体.session,已解析['name'],配对标识,错误)#内含写 done
            raise 错误#仍抛出处理函数错误
        return 结算(结果)#成功结算

    def 失败结算(自身,会话,命令,配对标识,错误):#失败路径写 done
        """抛出的处理函数或准入失败时，内含的 command/done 错误追加。"""
        if isinstance(错误,Exception) and len(错误.args)>0 and isinstance(错误.args[0],str):#对齐 Error.message
            失败文本=错误.args[0]#失败文本
        else:#非标准异常
            失败文本=渲染抛出(错误)#渲染抛出值
        try:#尝试追加
            自身.追加生命周期(会话,'command/done',{#写入失败结算
                'commandId':配对标识,#配对 id
                'kind':'error',#失败
                'text':失败文本,#失败文本
            })#done 事件结束
        except BaseException as 追加错误:#done 追加自己失败
            自身.ctx.日志.警告('command "'+命令+'": command/done append failed: '+渲染抛出(追加错误))#内含追加失败

    def 铸造命令标识(自身):#铸造配对 id
        """铸造下一个配对 id。"""
        自身.命令序号+=1#实例内递增
        return 命令标识('cmd-'+自身.实例令牌+'-'+str(自身.命令序号))#前缀加序号

    def 追加生命周期(自身,会话,类型,数据):#追加生命周期事件
        """直接追加一条仅日志生命周期事件。"""
        return 会话.追加(类型,数据)#两参数仅日志追加

    def 视图(自身,智能体):#有效命令视图
        """先解析全局定义，再叠上精确作用域遮蔽。"""
        return 自身.层集.合并(智能体,取层命令)#合并各层具名条目

    def 通知变更(自身):#扇出注册表变更
        """通知每个注册表观察者。回调按同步写死。"""
        参数=['commands/change']#派发参数
        事件总线=获取内部数据(自身.ctx,'属性链')['事件']#事件总线，不经壳
        for 回调 in 获取内部数据(事件总线,'解析监听器')(事件总线,'emit',参数):#取出全部监听器
            try:#独立执行
                回调()#同步回调
            except BaseException as 错误:#同步抛出
                自身.ctx.日志.警告('commands/change listener threw: '+渲染抛出(错误))#警告同步失败

__all__=[#仅中文公开名
    '命令名形态','斜杠命令形态','安全整数上限',
    '解析命令','渲染抛出','归一化定义','归一化结果','准入命令附件',
    '命令错误','命令层','命令运行时','命令定义标识','命令标识',
    '命令输入描述字段','命令结果种类','命令成功结果字段','命令失败结果字段',
    '命令执行字段','命令描述字段','命令来源映射','命令来源','命令运行载荷字段','命令完成载荷字段',
]#公开面结束
name='commands'#Cordis插件名
default=命令运行时#Cordis默认导出
