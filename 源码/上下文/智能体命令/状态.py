"""会话可见的工作区指令状态与动态调和。"""
import os,weakref#路径与按会话弱引用缓存
from ...模型后端.llm import 创建用户消息#导入用户消息构造
from .摘要 import 指令内容摘要,去空白指令摘要#导入内容摘要
from .文件 import (
    祖先链,#根到cwd目录链
    后代目录之间,#触及路径之间的后代目录
    寻找项目根,#寻找项目根
    探测作用域指令,#探测作用域候选
    读取作用域指令,#读取已探测候选
    相对展示,#相对展示路径
)#从文件导入结束
from .渲染 import (
    候选作用域键,#按候选组成作用域键
    解码作用域键,#解码作用域键
    指令作用域键,#由展示路径得到作用域键
    渲染指令变更,#渲染调和批次
    用户全局目录,#用户全局目录占位
    用户全局文件,#用户全局文件名
)#从渲染导入结束

名称='agent-instructions'#插件名，来源记录与加载器诊断共用
name=名称#Cordis 插件名

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
    等待=getattr(值,'等待',None)#可等待
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

def 工作区上下文钩子(文本,变更们):#构造带变更记录的工作区上下文消息
    """组装带来源与变更的用户消息。"""
    return 创建用户消息({#组装用户消息
        'content':[{'type':'text','text':文本}],#单文本块
        'source':{'kind':'agent-instructions','form':'instructions','changes':变更们},#带来源与变更
    })#createUserMessage结束

def 工作区上下文消息(文本):#构造基线工作区上下文消息
    """为已渲染基线构建用户角色消息。"""
    return 创建用户消息({#组装用户消息
        'content':[{'type':'text','text':文本}],#单文本块
        'source':{'kind':'plugin','plugin':名称},#插件来源，不含变更清单
    })#createUserMessage结束

def 是否工作区上下文来源(来源):#判断来源是否为带changes数组的工作区指令
    """收窄为工作区来源。"""
    if 来源 is None:#空来源
        return False#否
    return 取字段(来源,'kind')=='agent-instructions' and isinstance(取字段(来源,'changes'),list)#判别与changes

def 是否记录(值):#判断是否为普通对象记录
    """非None对象且非数组。"""
    return isinstance(值,dict) and 值 is not None#映射即记录

def 工作区指令变更们(来源):#从未知changes抽出合法变更
    """逐项校验并收集合法变更。"""
    变更们=[]#收集合法项
    for 值 in 取字段(来源,'changes') or []:#逐项校验
        if not 是否记录(值):#非对象则跳过
            continue#跳过
        动作=取字段(值,'action')#动作
        if 动作 not in ('set','replace','remove'):#动作非法
            continue#跳过
        if not isinstance(取字段(值,'scope'),str) or not isinstance(取字段(值,'path'),str):#scope与path必须是字符串
            continue#跳过
        摘要=取字段(值,'digest')#可选摘要
        if 摘要 is not None and not isinstance(摘要,str):#digest若出现必须是字符串
            continue#跳过
        项={'action':动作,'scope':取字段(值,'scope'),'path':取字段(值,'path')}#收下合法变更
        if 摘要 is not None:#有摘要才带上
            项['digest']=摘要#带上
        变更们.append(项)#收下
    return 变更们#返回合法变更

def 同一指令变更(甲,乙):#比较两次变更是否同一转移
    """动作、作用域、路径、摘要都相同。"""
    return 取字段(甲,'action')==取字段(乙,'action') and 取字段(甲,'scope')==取字段(乙,'scope') and 取字段(甲,'path')==取字段(乙,'path') and 取字段(甲,'digest')==取字段(乙,'digest')#四字段相同

def 可见指令变更们(智能体,权威消息们):#收集表面可见的最新每作用域变更
    """作用域到最新可见变更。"""
    表面序号=set(智能体.session.surface.nodes)#当前表面节点序号
    可见={}#按作用域覆盖写入
    for 序号,事件 in enumerate(智能体.session.events):#扫描持久事件
        if 取字段(事件,'type')!='user/message' or not 是否工作区上下文来源(取字段(取字段(事件,'data'),'source')):#只看工作区用户消息
            continue#跳过
        for 变更 in 工作区指令变更们(取字段(取字段(事件,'data'),'source')):#抽出变更
            if 序号 in 表面序号:#仅表面可见的事件才算
                可见[变更['scope']]=变更#覆盖
    for 消息 in 权威消息们:#权威消息后写，覆盖日志
        if not 是否工作区上下文来源(取字段(消息,'source')):#非工作区来源跳过
            continue#跳过
        for 变更 in 工作区指令变更们(取字段(消息,'source')):#抽出变更
            可见[变更['scope']]=变更#覆盖该作用域
    return 可见#返回可见状态

def 基线指令状态(文件们):#由基线文件得到变更与版本
    """把渲染后保留的基线文件转成比较与元数据缓存状态。"""
    变更们={}#基线变更
    版本们={}#版本缓存种子
    for 文件 in 文件们:#逐个保留文件
        摘要=指令内容摘要(文件['content'])#精确内容身份
        变更={'action':'set','scope':指令作用域键(文件['displayPath']),'path':文件['displayPath'],'digest':摘要}#基线一律为set
        变更们[变更['scope']]=变更#记下变更
        if 取字段(文件,'version') is not None:#有提供方版本才进缓存
            版本们[变更['scope']]={#写入版本状态
                'path':文件['displayPath'],#展示路径
                'version':文件['version'],#提供方版本
                'digest':摘要,#精确摘要
                'trimmedDigest':去空白指令摘要(文件['content']),#去空白摘要
            }#版本状态结束
    return {'changes':变更们,'versions':版本们}#返回两张表

def 会话版本表(会话,缓存):#取或创建会话的作用域状态表
    """按会话隔离的可变表。"""
    表=缓存.get(会话)#已有表
    if 表 is None:#该会话第一次
        表={}#新建空表
        缓存[会话]=表#挂到弱引用缓存
    return 表#返回可变表

def 保留指令版本更新(更新们,已渲染变更):#过滤出渲染真正代表的缓存更新
    """只保留已被渲染变更代表的缓存更新。"""
    return [更新 for 更新 in 更新们 if any(同一指令变更(更新['change'],变更) for 变更 in 已渲染变更)]#变更完全匹配才保留

def 应用指令版本更新(会话,更新们,缓存):#提交版本缓存更新
    """应用元数据缓存转移，不保留指令正文。"""
    if len(更新们)==0:#没有更新则不动
        return#结束
    表=会话版本表(会话,缓存)#取该会话表
    for 更新 in 更新们:#按顺序应用
        if 取字段(更新,'state') is None:#无state表示删除
            表.pop(更新['change']['scope'],None)#删除
        else:#否则写入新状态
            表[更新['change']['scope']]=更新['state']#写入
    if len(表)==0:#空表则丢掉弱引用条目
        try:#WeakKeyDictionary支持del
            del 缓存[会话]#丢掉
        except KeyError:#已不在
            pass#放过

def 相对作用域(项目根,目录):#目录转成相对项目根的作用域目录分量
    """根自身用 .。"""
    作用域=相对展示(项目根,目录)#相对展示
    return '.' if len(作用域)==0 or 作用域=='.' else 作用域#根自身用.

def 调和指令上下文(智能体,已解析,版本缓存,文件系统,选项):#调和可见状态与提供方文件
    """比较可见状态与提供方可见文件并渲染转移。未变或不可用时为 None。"""
    会话=智能体.session#当前会话
    有效=可见指令变更们(智能体,选项['authorityMessages'])#当前可见每作用域状态
    工作目录=取字段(取字段(会话,'header'),'cwd') or os.getcwd()#会话cwd，缺则用进程cwd
    项目根=取字段(选项,'projectRoot')#已选定根
    if 项目根 is None:#未选定
        项目根=寻找项目根(工作目录,已解析['projectRootMarkers'],文件系统,取字段(选项,'signal'))#否则向上寻找
    作用域们=set()#本轮要探测的作用域
    基线作用域=set()#基线链上的作用域
    def 加目录作用域(目标,目录):#把某目录的基线与覆盖候选都加入集合
        """加入基线与本地覆盖候选。"""
        for 候选 in 已解析['instructionFileCandidates']:#基线候选
            目标.add(候选作用域键(目录,候选))#加入
        for 候选 in 已解析['localInstructionFileCandidates']:#本地覆盖
            目标.add(候选作用域键(目录,候选))#加入
    def 加项目作用域(目标,目录):#绝对目录转相对作用域再加入
        """相对项目根后加入。"""
        加目录作用域(目标,相对作用域(项目根,目录))#相对项目根
    基线作用域.add(候选作用域键(用户全局目录,用户全局文件))#用户全局始终属于基线
    for 目录 in 祖先链(项目根,工作目录):#根到cwd的项目作用域
        加项目作用域(基线作用域,目录)#加入
    if 选项.get('includeBaselineScopes'):#本轮参与基线
        for 作用域 in 基线作用域:#纳入基线作用域
            作用域们.add(作用域)#纳入
    for 消息 in 选项['scopeMessages']:#待处理提示里的作用域
        if not 是否工作区上下文来源(取字段(消息,'source')):#非工作区来源跳过
            continue#跳过
        for 变更 in 工作区指令变更们(取字段(消息,'source')):#抽出变更作用域
            if (not 选项.get('includeBaselineScopes')) and 变更['scope'] in 基线作用域:#不参与基线时跳过基线作用域
                continue#跳过
            作用域们.add(变更['scope'])#纳入提示作用域
    for 作用域 in 有效.keys():#可见状态里的作用域
        if (not 选项.get('includeBaselineScopes')) and 作用域 in 基线作用域:#不参与基线时跳过
            continue#跳过
        拆=解码作用域键(作用域)#拆目录
        if 拆['directory']==用户全局目录:#全局固定文件
            作用域们.add(候选作用域键(用户全局目录,用户全局文件))#加入
        else:#该目录全部候选，避免漏掉兄弟
            加目录作用域(作用域们,拆['directory'])#加入
    for 触及路径 in 选项['touchedPaths']:#工具触及的路径
        for 目录 in 后代目录之间(工作目录,触及路径):#嵌套目录也要调和
            加项目作用域(作用域们,目录)#加入
    版本表=会话版本表(会话,版本缓存)#本会话版本表
    已见绝对=set()#本轮已见绝对路径，防止同一文件重复渲染
    已保留去空白={}#目录到已保留去空白摘要
    def 登记去空白(目录,摘要):#登记摘要；若已存在则返回True表示重复
        """同目录去重登记。"""
        摘要集=已保留去空白.get(目录)#该目录摘要集
        if 摘要集 is None:#第一次见到该目录
            摘要集=set()#新建
            已保留去空白[目录]=摘要集#挂上
        if 摘要 in 摘要集:#已有则为重复
            return True#重复
        摘要集.add(摘要)#记下新摘要
        return False#不是重复
    项们=[]#待渲染变更项
    版本更新=[]#待提交缓存更新
    def 排队移除(作用域,路径):#排队一次移除
        """声明移除并删缓存。"""
        变更={'action':'remove','scope':作用域,'path':路径}#移除变更
        项们.append({'change':变更,'file':{'absolutePath':'removed:'+作用域,'displayPath':路径,'content':''}})#占位文件供渲染器索引
        版本更新.append({'change':变更})#无state表示删缓存
    按目录={}#按目录分组作用域，同目录是一个去重权威组
    for 作用域 in 作用域们:#分组
        目录=解码作用域键(作用域)['directory']#拆目录
        列表=按目录.get(目录)#该目录已有列表
        if 列表 is None:#新建列表
            按目录[目录]=[作用域]#新建
        else:#追加
            列表.append(作用域)#追加
    for 目录,目录作用域们 in 按目录.items():#按目录处理，一组内失败则整组回滚
        探测作用域们=[]#实际要探测的作用域
        排除集=选项.get('excludedBaselineScopes')#可选排除集
        for 作用域 in 目录作用域们:#先处理被预算排除的基线作用域
            if 排除集 is not None and 作用域 in 基线作用域 and 作用域 in 排除集:#被排除
                先前=有效.get(作用域)#可见旧状态
                if 先前 is None or 先前['action']=='remove':#本来就没有则清缓存
                    版本表.pop(作用域,None)#清缓存
                else:#否则声明移除
                    排队移除(作用域,先前['path'])#声明移除
            else:#需要探测
                探测作用域们.append(作用域)#纳入探测列表
        项起点=len(项们)#本组开始前的渲染项长度，失败时回滚
        更新起点=len(版本更新)#本组开始前的更新长度
        新增绝对=[]#本组新登记的绝对路径
        先前版本={作用域:版本表.get(作用域) for 作用域 in 探测作用域们}#探测前的缓存快照
        for 作用域 in 探测作用域们:#逐个探测
            先前=有效.get(作用域)#该作用域可见旧状态
            探测=探测作用域指令(作用域,项目根,已解析,文件系统,取字段(选项,'signal'))#三分探测
            if 探测['kind']=='unavailable':#提供方暂时失败
                if 先前 is None or 先前['action']=='remove':#本来就没有可见内容则跳过该候选
                    continue#跳过
                del 项们[项起点:]#丢掉本组已排队的渲染项
                del 版本更新[更新起点:]#丢掉本组已排队的缓存更新
                for 候选作用域,先前缓存 in 先前版本.items():#恢复探测前缓存
                    if 先前缓存 is None:#探测前没有则删
                        版本表.pop(候选作用域,None)#删
                    else:#否则写回旧值
                        版本表[候选作用域]=先前缓存#写回
                for 绝对路径 in 新增绝对:#撤回本轮路径登记
                    已见绝对.discard(绝对路径)#撤回
                已保留去空白.pop(目录,None)#撤回本目录去重登记
                break#该目录其余候选不再探测
            if 探测['kind']=='absent':#确认缺失
                if 先前 is None or 先前['action']=='remove':#本来就没有则清缓存
                    版本表.pop(作用域,None)#清缓存
                else:#否则声明移除
                    排队移除(作用域,先前['path'])#声明移除
                continue#下一作用域
            探测文件=探测['file']#存在则取出探测文件
            if 探测文件['absolutePath'] in 已见绝对:#同一绝对路径已处理
                continue#跳过
            已见绝对.add(探测文件['absolutePath'])#登记路径
            新增绝对.append(探测文件['absolutePath'])#计入本组，失败时撤回
            缓存态=版本表.get(作用域)#快路径缓存
            if (#版本、路径、可见摘要都未变
                缓存态 is not None#有缓存
                and 缓存态['path']==探测文件['displayPath']#展示路径相同
                and 缓存态['version']==探测文件['version']#提供方版本相同
                and 先前 is not None#表面仍有内容
                and 先前['action']!='remove'#不是已移除
                and 先前['path']==缓存态['path']#可见路径与缓存一致
                and 先前.get('digest')==缓存态['digest']#可见摘要与缓存一致
            ):#未改且先前已渲染
                if 登记去空白(目录,缓存态['trimmedDigest']):#变成同目录重复则移除
                    排队移除(作用域,先前['path'])#移除
                continue#不必再读正文
            文件=读取作用域指令(探测文件,已解析['maxSourceBytes'],文件系统,取字段(选项,'signal'))#按上限读取
            if 文件 is None:#超限或不可读则跳过，不发出转移
                continue#跳过
            当前摘要=指令内容摘要(文件['content'])#精确摘要
            去空白摘要=去空白指令摘要(文件['content'])#去空白摘要
            if 登记去空白(目录,去空白摘要):#同目录去空白重复
                if 先前 is not None and 先前['action']!='remove':#表面仍有则声明移除
                    排队移除(作用域,先前['path'])#声明移除
                else:#否则只清缓存
                    版本表.pop(作用域,None)#清缓存
                continue#不渲染重复内容
            下一版本={'path':文件['displayPath'],'version':探测文件['version'],'digest':当前摘要,'trimmedDigest':去空白摘要}#新的版本状态
            if 先前 is not None and 先前['action']!='remove' and 先前['path']==文件['displayPath'] and 先前.get('digest')==当前摘要:#内容未变，只是缓存过期
                版本表[作用域]=下一版本#就地刷新缓存，不发渲染转移
                continue#下一作用域
            动作='set' if 先前 is None or 先前['action']=='remove' else 'replace'#没有旧内容则set，否则replace
            变更={'action':动作,'scope':作用域,'path':文件['displayPath'],'digest':当前摘要}#组装变更
            项们.append({'change':变更,'file':文件})#排队渲染
            版本更新.append({'change':变更,'state':下一版本})#排队写入缓存
    if len(项们)==0:#没有任何转移
        return None#无
    渲染=渲染指令变更(项们,已解析['maxBytes'])#按预算渲染
    if len(渲染['text'])==0 or len(渲染['changes'])==0:#通知-only则放弃
        return None#放弃
    return {#返回要进入的上下文与应提交的缓存更新
        'context':工作区上下文钩子(渲染['text'],渲染['changes']),#带变更清单的用户消息
        'versionUpdates':保留指令版本更新(版本更新,渲染['changes']),#只提交被渲染代表的更新
    }#返回对象结束
