import json,math,re#json、有限数与正则
from ...依赖 import 工具,cordis#外部依赖胶水
from ...依赖.schemastery import 布尔字段,字符串字段,列表字段#配置字段
克隆=工具.克隆#深克隆工具参数
服务=cordis.服务#服务基类
from ..作用域 import (
    具名条目,#具名登记表
    匿名条目,#匿名登记表
    作用域层集,#全局+作用域层
    作用域目标,#按作用域过滤的路由载体
)#导入作用域表与载体
from .类型 import (
    组装上下文,#assemble 上下文
    提示词段落,#段落贡献
    提示词上下文,#动态上下文贡献
    已组装段落,#已解析段落
    已组装上下文,#已解析上下文
    工具提供结果,#工具提供方返回
    提示词组装,#组装结果
    系统提示词配置,#配置字段类型
)#再导出结构类型

#部署人设前缀/后缀的段落名。导出是因为组合可以替换本槽——Agent 预设用自己的人设遮蔽部署人设——两边点名同一段落才让替换生效而不是重复。
人设前缀段落名='deployment:persona-prefix'#部署人设前缀段落名
人设后缀段落名='deployment:persona-suffix'#部署人设后缀段落名
段落顺序表={
    'HARNESS_IDENTITY':-1000,#Harness 身份
    'DEPLOYMENT_PERSONA_PREFIX':0,#部署人设前缀
    'PLAN_POLICY':500,#计划策略
    'TEAM_POLICY':600,#团队策略
    'PTC_ONLY':800,#PTC
    'FILE_REFERENCE':900,#文件引用
    'TOOL_BASH':1000,#bash 工具
    'TOOL_PWSH':1010,#pwsh 工具
    'TOOL_READ':1100,#read
    'TOOL_WRITE':1200,#write
    'TOOL_EDIT':1300,#edit
    'TOOL_GLOB':1400,#glob
    'TOOL_GREP':1500,#grep
    'TOOL_JOBS':1600,#jobs
    'TOOL_PTY':1700,#pty
    'TOOL_WEB_SEARCH':2000,#web search
    'TOOL_WEB_FETCH':2100,#web fetch
    'TOOL_LSP':2200,#lsp
    'TOOL_SESSION_QUERY':2300,#session query
    'TOOL_GOAL':2400,#goal
    'TOOL_CORDIS':2500,#cordis
    'TOOL_WORKFLOW':2600,#workflow
    'TOOL_RALPH':2700,#ralph
    'TOOL_SUBAGENT':2800,#subagent
    'TOOL_REPORT':2900,#report
    'TOOL_COMPUTER_USE':3000,#computer use
    'MCP_SERVERS':3100,#MCP 服务器
    'TOOLS_SDK':5000,#SDK 工具
    'DELIVERABLE_FILE_REFERENCES':9000,#交付物文件引用
    'STRUCTURED_OUTPUT':9900,#结构化输出
    'HARNESS_SOURCE':10000,#Harness 源
    'WEB_SURFACE':10100,#Web 面
    'DEPLOYMENT_PERSONA_SUFFIX':10200,#部署人设后缀
}#中央段落顺序
#预设/子体遮蔽的单槽人设 = 前缀槽；与上列同出处，勿另写字面量
人设段落名=人设前缀段落名#遮蔽用段落名
人设顺序=段落顺序表['DEPLOYMENT_PERSONA_PREFIX']#与前缀槽同序
上下文顺序表={
    'SANDBOX_POLICY':110,#沙箱策略
    'APPROVAL_POLICY':115,#批准策略
    'SUBAGENT_DELEGATION':120,#子代理委派
}#中央上下文顺序
变量名规则=re.compile(r'^[a-z][a-z0-9_]*\Z',re.ASCII)#花括号之间的合法变量名
引用组规则=re.compile(r'^\{\{([^{}]*)\}\}',re.ASCII)#扫描位置上完整的 {{...}} 引用组
变量名规则文本='/'+变量名规则.pattern+'/'#诊断展示，按 /pattern/ 形态展示正则
工具顺序其余='<unlisted-tools>'#toolOrder 给未列出工具保留的标记

class 系统提示词错误(Exception):
    """内核系统提示词包的异常基类。"""

def 是否合法变量名(名):
    """对齐 /^[a-z][a-z0-9_]*$/.test：必须是字符串且整串匹配。"""
    if not isinstance(名,str):#必须是字符串
        return False#非字符串非法
    return 变量名规则.fullmatch(名) is not None#整串合法

def 是否有限数(值):
    """对齐 Number.isFinite：整数或浮点且有限，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是数字
    if isinstance(值,(int,float)):#整数或浮点
        return math.isfinite(值)#有限
    return False#其余不是

def 段落排序键(段):
    """按显式放置再按名确定性排序。"""
    return (段['order'],段['name'])#顺序再名字

def 工具名(工具):
    """取出工具名，供与区域无关的字典序（码元）排序。"""
    return 工具['name']#工具名

def 条目顺序(条目):
    """取出登记顺序，供升序稳定排序。"""
    return 条目['order']#顺序

def 校验工具顺序(工具顺序):
    """校验重复名与必需的其余项标记。已登记名更后在组装时检查，因为插件尚未加载。"""
    if 工具顺序 is None:#未配置
        return None#未配置则跳过
    已见=set()#已见名
    for 名 in 工具顺序:#逐个名
        if 名 in 已见:#重复
            raise 系统提示词错误('toolOrder lists "'+名+'" more than once')#不得重复
        已见.add(名)#记下
    if 工具顺序其余 not in 已见:#缺少占位
        raise 系统提示词错误('toolOrder must contain the "'+工具顺序其余+'" rest entry (where unlisted tools are inserted)')#必须含 rest
    return 工具顺序#原样返回

def 排序工具(工具列表,工具顺序,已知名):
    """应用配置的工具顺序，把未列出工具按字典序插在其余项。未知配置名失败；已知但被限制的名可以缺席。"""
    占用=None#占用保留名的工具
    for 工具 in 工具列表:#逐个可见工具
        if 工具['name']==工具顺序其余:#占用保留名
            占用=工具#找到保留名
            break#只需一个
    if 占用 is not None:#提供方返回了保留名
        raise 系统提示词错误('tool provider returned reserved tool name "'+工具顺序其余+'" (reserved for toolOrder\'s rest entry)')#保留名非法
    if 工具顺序 is None:#未配置
        工具列表.sort(key=工具名)#未配置则字典序
        return 工具列表#就地排序后返回
    未知名=[]#未知配置名
    for 名 in 工具顺序:#按配置顺序
        if 名!=工具顺序其余 and 名 not in 已知名:#未知配置名
            未知名.append(名)#收集未知名
    if len(未知名)>0:#有未知名
        已知名文本=', '.join(sorted(已知名)) or '(none)'#已知名或空
        复数='s' if len(未知名)>1 else ''#复数
        raise 系统提示词错误('toolOrder lists unregistered tool'+复数+' '+', '.join('"'+名+'"' for 名 in 未知名)+'; known tools: '+已知名文本)#组装时未知名失败
    已列出=set(工具顺序)#已列出集合
    其余=[]#未列出
    for 工具 in 工具列表:#收集未列出
        if 工具['name'] not in 已列出:#未列出
            其余.append(工具)#收下
    其余.sort(key=工具名)#未列出按字典序
    结果=[]#按配置展开
    for 名 in 工具顺序:#按配置名
        if 名==工具顺序其余:#其余项
            结果.extend(其余)#插入其余
        else:#具名项
            for 工具 in 工具列表:#按名展开
                if 工具['name']==名:#命中
                    结果.append(工具)#按名展开
    return 结果#规范顺序

def 渲染提示词(组装):
    """插值严格 `{{variable}}` 引用，丢掉空段落，其余用空行拼接。畸形、未知或未定义引用会抛；单独的 `{{` 后面没有任何 `}}` 是字面散文，替换值不再扫描。全部段落为空时返回空串。"""
    文本列表=[]#已插值非空段落
    for 段 in 组装['sections']:#逐段
        if 'interpolate' in 段 and 段['interpolate'] is False:
            文本=段['text']#不插值
        else:
            文本=插值(段,组装['variables'],'section')#插值
        if len(文本)>0:#非空
            文本列表.append(文本)#丢掉空
    return '\n\n'.join(文本列表)#空行拼接

def 渲染上下文快照(组装):
    """渲染完整动态上下文快照。无活动上下文时返回空串。"""
    return 拼接上下文章节(渲染上下文章节(组装))#先分段再拼接

def 拼接上下文章节(段落列表):
    """已渲染段落列表的面向模型快照文本。也需要段落的调用方渲染一次再在此拼接，因此一次请求不会把每个上下文插值两遍。无正文时返回空串。"""
    正文='\n\n'.join(段['text'] for 段 in 段落列表)#空行拼接正文
    if len(正文)==0:#无正文
        return ''#无正文则空
    return 'Current runtime context. This snapshot supersedes earlier runtime-context snapshots.\n\n'+正文#信封加正文

def 渲染上下文章节(组装):
    """同一份快照，保留为组装它的具名贡献。展示快照的消费方用它们把各部分归属到贡献子系统，而不再切开已拼接散文。"""
    结果=[]#非空贡献
    for 上下文块 in 组装['contexts']:#逐条上下文
        文本=插值(上下文块,组装['variables'],'context')#插值
        if len(文本)>0:#非空
            结果.append({'name':上下文块['name'],'text':文本})#丢掉空文本
    return 结果#已渲染章节

def 插值(输入,变量表,种类):
    """插值一段或一条上下文，并把诊断归属到其拥有输入。未登记名按自有键查找（对齐 Object.hasOwn），不经原型链。"""
    文本=输入['text']#源文本
    结果=''#已写出前缀
    上次=0#上次结束位置
    开=文本.find('{{')#下一引用
    while 开>=0:#还有 {{
        匹配=引用组规则.match(文本[开:])#尝试完整组
        if 匹配 is None:#不是完整组
            if 文本.find('}}',开+2)>=0:#后面有 }}，更后的闭合使这畸形
                raise 系统提示词错误('malformed prompt variable reference at "'+文本[开:开+16]+'…" in '+种类+' "'+输入['name']+'" (references are complete simple {{name}} groups)')#畸形引用
            结果+=文本[上次:开+2]#把 {{ 当字面写出
            上次=开+2#跳过 {{
            开=文本.find('{{',上次)#下一引用
            continue#下一引用
        名=匹配.group(0)[2:-2]#取出名字；{{}} 得到空名并走畸形引用路径
        if not 是否合法变量名(名):#名不合法
            raise 系统提示词错误('malformed prompt variable reference "{{'+名+'}}" in '+种类+' "'+输入['name']+'" (variable names match '+变量名规则文本+')')#畸形名
        if 名 not in 变量表:#未登记，对齐 Object.hasOwn
            已登记=list(变量表.keys())#已登记名
            已知=', '.join(已登记) if len(已登记)>0 else '(none)'#列出或空
            raise 系统提示词错误('unknown prompt variable "{{'+名+'}}" in '+种类+' "'+输入['name']+'"; registered variables: '+已知)#未知变量
        值=变量表[名]#取值
        if 值 is None:#本组装无值
            raise 系统提示词错误('prompt variable "{{'+名+'}}" has no value for this assembly ('+种类+' "'+输入['name']+'")')#未定义
        结果+=文本[上次:开]+值#前缀加替换
        上次=开+len(匹配.group(0))#跳过整组
        开=文本.find('{{',上次)#下一引用
    return 结果+文本[上次:]#接上尾巴

class 提示词层:#一个全局或作用域层
    """一个全局或作用域层拥有的全部提示词登记。"""
    def __init__(自身,作用域):#创建一层
        """创建一层；诊断文案针对其所有权作用域（全局为 None）。"""
        def 段落重复(名):#段落重复名诊断
            """段落重复名诊断。"""
            if 作用域 is None:#全局
                return Exception('prompt section "'+名+'" is already registered (for a per-agent override, register through that agent\'s `agent.ctx` instead)')#全局重复
            return Exception('prompt section "'+名+'" is already registered in this scope')#作用域重复
        def 上下文重复(名):#上下文重复名诊断
            """上下文重复名诊断。"""
            if 作用域 is None:#全局
                return Exception('prompt context "'+名+'" is already registered (for a per-agent override, register through that agent\'s `agent.ctx` instead)')#全局重复
            return Exception('prompt context "'+名+'" is already registered in this scope')#作用域重复
        def 变量重复(名):#变量重复名诊断
            """变量重复名诊断。"""
            if 作用域 is None:#全局
                return Exception('prompt variable "'+名+'" is already registered (for a per-agent value, register through that agent\'s `agent.ctx` instead)')#全局重复
            return Exception('prompt variable "'+名+'" is already registered in this scope')#作用域重复
        自身.段落=具名条目(段落重复)#段落表
        自身.上下文表=具名条目(上下文重复)#上下文表
        自身.运行时上下文抑制器=匿名条目()#运行时上下文抑制器
        自身.工具提供方=匿名条目()#工具提供方
        自身.变量=具名条目(变量重复)#变量表

    def 是否空(自身):#五张表都空
        """本层是否没有任何提示词登记。"""
        return 自身.段落.是否空() and 自身.上下文表.是否空() and 自身.运行时上下文抑制器.是否空() and 自身.工具提供方.是否空() and 自身.变量.是否空()#五张表都空

class 系统提示词(服务):#系统提示词服务
    """每次模型步骤前组装的提示词输入的注册表服务（ctx 键：`systemPrompt`）。"""
    配置={#Loader 配置模式
        'includeHarnessIdentity':布尔字段(默认值=True),#默认含身份
        'includeRuntimeContext':布尔字段(默认值=True),#默认含运行时上下文
        'personaPrefix':字符串字段(默认值=''),#人设前缀默认空
        'personaSuffix':字符串字段(默认值=''),#人设后缀默认空
        'toolOrder':列表字段(字符串字段(),默认值=None),#省略与空数组不同：空数组缺 rest 标记须在加载时失败
    }#配置模式

    def __init__(自身,ctx,配置):#构造服务
        """构造服务并登记内建段落。harness 拥有的开场独立于所选循环插件。"""
        super().__init__(ctx,'systemPrompt')#注册服务名（Cordis 键字面量）
        自身.工具顺序=校验工具顺序(配置['toolOrder'] if 'toolOrder' in 配置 else None)#校验工具顺序
        def 发出变更():#提供方变更通知
            """任一提示词提供方变更时发出；本注册表通知不过滤，因为全局变更影响每个作用域。"""
            自身.ctx.广播('system-prompt/change')#发出变更
        自身.层集=作用域层集(提示词层,发出变更)#作用域层
        含身份=配置['includeHarnessIdentity'] if 'includeHarnessIdentity' in 配置 else None#是否含身份
        if 含身份 is None:#缺省
            含身份=True#缺省为真
        if 含身份:#含身份
            自身.段落({
                'name':'harness:identity',#段落名
                'order':自身.获取段落顺序('HARNESS_IDENTITY'),#身份顺序
                'text':'You are an AI agent powered by DeepSeek Harness.',#身份文本
            })#登记身份段
        人设前缀=配置['personaPrefix'] if 'personaPrefix' in 配置 else None#人设前缀
        if 人设前缀 is None:#缺省
            人设前缀=''#缺省为空
        自身.段落({
            'name':人设前缀段落名,#前缀名
            'order':自身.获取段落顺序('DEPLOYMENT_PERSONA_PREFIX'),#前缀顺序
            'text':人设前缀,#前缀文本
        })#登记人设前缀
        人设后缀=配置['personaSuffix'] if 'personaSuffix' in 配置 else None#人设后缀
        if 人设后缀 is None:#缺省
            人设后缀=''#缺省为空
        自身.段落({
            'name':人设后缀段落名,#后缀名
            'order':自身.获取段落顺序('DEPLOYMENT_PERSONA_SUFFIX'),#后缀顺序
            'text':人设后缀,#后缀文本
        })#登记人设后缀
        含运行时=配置['includeRuntimeContext'] if 'includeRuntimeContext' in 配置 else None#是否含运行时上下文
        if 含运行时 is None:#缺省
            含运行时=True#缺省为真
        if not 含运行时:#关闭运行时上下文
            自身.抑制运行时上下文()#关闭运行时上下文

    def 段落(自身,段落):#登记段落
        """在调用上下文的作用域登记一段有序提示词。作用域段落遮蔽同名全局段落；同一层内重复与非有限顺序会抛。登记与拆除发出 `system-prompt/change`。返回精确 Cordis effect 拆除器。"""
        if not 是否有限数(段落['order']):#顺序非有限
            raise TypeError('prompt section "'+段落['name']+'" order must be a finite number')#必须有限
        def 插入(层):#插入本段落
            """插入本段落到该层具名表。"""
            return 层.段落.插入(段落['name'],段落)#插入
        return 自身.层集.副作用(自身.ctx,插入,{'标签':'systemPrompt.section()'})#挂上 effect

    def 获取段落顺序(自身,名):
        """解析仓库提示词段落的中央放置序号。"""
        return 段落顺序表[名]#段落顺序

    def 获取上下文顺序(自身,名):
        """解析仓库运行时上下文的中央放置序号。"""
        return 上下文顺序表[名]#上下文顺序

    def 上下文(自身,上下文块):#登记上下文
        """在调用上下文的作用域登记有序动态上下文。作用域条目遮蔽同名全局条目。返回精确 Cordis effect 拆除器。"""
        if not 是否有限数(上下文块['order']):#顺序非有限
            raise TypeError('prompt context "'+上下文块['name']+'" order must be a finite number')#必须有限
        def 插入(层):#插入本上下文
            """插入本上下文到该层具名表。"""
            return 层.上下文表.插入(上下文块['name'],上下文块)#插入
        return 自身.层集.副作用(自身.ctx,插入,{'标签':'systemPrompt.context()'})#挂上 effect

    def 抑制运行时上下文(自身):#抑制运行时上下文
        """在调用上下文的作用域抑制每一条动态运行时上下文贡献，不改拥有或强制那些事实的服务。多个抑制器保持独立可拆除。返回精确 Cordis effect 拆除器。"""
        def 追加(层):#追加抑制器
            """追加一条独立可拆除的抑制标记。"""
            return 层.运行时上下文抑制器.追加(True)#追加
        return 自身.层集.副作用(自身.ctx,追加,{'标签':'systemPrompt.suppressRuntimeContext()'})#挂上 effect

    def 工具(自身,提供方):#登记工具提供方
        """在调用上下文的作用域登记一个工具模式提供方。全局与匹配的作用域提供方都贡献；返回保留的其余项名会使组装失败。返回精确 Cordis effect 拆除器。"""
        def 追加(层):#追加提供方
            """追加本工具模式提供方。"""
            return 层.工具提供方.追加(提供方)#追加
        return 自身.层集.副作用(自身.ctx,追加,{'标签':'systemPrompt.tools()'})#挂上 effect

    def 变量(自身,名,提供方):#登记变量
        """在调用上下文的作用域登记一个提示词变量。作用域值遮蔽全局；非法或重复名会抛。提供方可返回 None（对齐 undefined），但渲染引用该值的段落随后失败。返回精确 Cordis effect 拆除器。"""
        if not 是否合法变量名(名):#名不合法
            raise 系统提示词错误('invalid prompt variable name "'+名+'" (must match '+变量名规则文本+')')#非法名
        def 插入(层):#插入本变量
            """插入本变量提供方到该层具名表。"""
            return 层.变量.插入(名,提供方)#插入
        return 自身.层集.副作用(自身.ctx,插入,{'标签':'systemPrompt.variable()'})#挂上 effect

    def 组装(自身,上下文=None):#组装提示词
        """组装全局与作用域提供方，脱离工具参数，应用规范排序，再执行组装瀑布。作用域段落与变量遮蔽全局。返回的瀑布值是权威的，除了有效完整段落之后被还原成唯一提示词段落，以及活动抑制器强制清空上下文。"""
        if 上下文 is None:#缺省
            上下文={}#缺省空上下文
        作用域=上下文['scope'] if 'scope' in 上下文 else None#观察作用域
        作用域层列表=自身.层集.链上层(作用域)#链上层
        运行时上下文已抑制=not 自身.层集.全局.运行时上下文抑制器.是否空()#全局抑制
        if not 运行时上下文已抑制:#全局没有
            for 层 in 作用域层列表:#链上
                if not 层.运行时上下文抑制器.是否空():#该层有抑制
                    运行时上下文已抑制=True#链上有抑制
                    break#已抑制
        变量表={}#变量表；作用域变量遮蔽全局
        for 名,提供方 in 自身.层集.全局.变量.诸条目():#先全局
            变量表[名]=提供方(上下文)#先全局
        for 层 in 作用域层列表:#再叠链，最远在前，因此最近作用域赢得一个名
            for 名,提供方 in 层.变量.诸条目():#该层变量
                变量表[名]=提供方(上下文)#近者覆盖
        def 取段落(层):#取出该层段落表
            """取出该层段落表，供作用域合并。"""
            return 层.段落#段落表
        def 取上下文(层):#取出该层上下文表
            """取出该层上下文表，供作用域合并。"""
            return 层.上下文表#上下文表
        段落按名=自身.层集.合并(作用域,取段落)#合并段落；作用域遮蔽全局
        上下文按名=自身.层集.合并(作用域,取上下文)#合并上下文
        提供方列表=list(自身.层集.全局.工具提供方.诸值())#快照全局
        for 层 in 作用域层列表:#快照链上
            提供方列表.extend(层.工具提供方.诸值())#快照链上
        收集=[]#可见模式
        已知名=set()#限制前名称
        for 提供方 in 提供方列表:#逐个提供方
            结果=提供方(上下文)#求值
            模式列表=[]#投影模式
            for 工具 in 结果['schemas']:#可见模式
                模式列表.append({
                    'name':工具['name'],#工具名
                    'description':工具['description'],#描述
                    'parameters':克隆(工具['parameters']),#脱离参数
                })#一条模式
            已接受已知=结果['knownNames'] if 'knownNames' in 结果 else None#限制前名
            if 已接受已知 is None:#未给
                已接受已知=[]#从可见模式收
                for 工具 in 模式列表:#可见名
                    已接受已知.append(工具['name'])#可见名
            收集.extend(模式列表)#收集可见
            for 名 in 已接受已知:#记下已知
                已知名.add(名)#记下已知
        段落定义=list(段落按名.values())#合并后的段落
        段落定义.sort(key=段落排序键)#按序再按名
        完整定义=[]#完整段落
        for 段 in 段落定义:#收集完整
            if 'complete' in 段 and 段['complete'] is True:#完整
                完整定义.append(段)#收下
        if len(完整定义)>1:#多于一个完整
            raise 系统提示词错误('multiple complete prompt sections are active: '+', '.join(json.dumps(段['name'],ensure_ascii=False,separators=(',',':'),allow_nan=False) for 段 in 完整定义))#组装失败
        完整段落=None#记下完整段
        段落列表=[]#已组装段落
        for 段 in 段落定义:#解析文本
            文本值=段['text']#文本或提供方
            if callable(文本值):#提供方
                文本值=文本值(上下文)#求值
            已组装={'name':段['name'],'text':文本值}#已组装
            if 'interpolate' in 段:#显式插值开关
                已组装['interpolate']=段['interpolate']#透传到已组装
            if 'complete' in 段 and 段['complete'] is True:#完整
                完整段落=dict(已组装)#记下完整
            段落列表.append(已组装)#收集
        if 运行时上下文已抑制:#抑制则空
            上下文列表=[]#抑制则空
        else:#按序解析
            上下文定义=list(上下文按名.values())#合并后的上下文
            上下文定义.sort(key=条目顺序)#按序
            上下文列表=[]#已解析上下文
            for 条目 in 上下文定义:#解析文本
                文本值=条目['text']#文本或提供方
                if callable(文本值):#提供方
                    文本值=文本值(上下文)#求值
                上下文列表.append({'name':条目['name'],'text':文本值})#收集
        组装结果={
            'sections':段落列表,#段落
            'contexts':上下文列表,#上下文
            'tools':排序工具(收集,自身.工具顺序,已知名),#规范顺序
            'variables':变量表,#变量
        }#组装结果
        def 内建(*位置参数):#瀑布内建
            """瀑布内建：交回本轮从登记表建出的组装。"""
            return 组装结果#原样
        已变换=自身.ctx.链式拦截(作用域目标(自身,作用域),'system-prompt/assemble',组装结果,上下文,内建)#执行瀑布
        if 完整段落 is None and not 运行时上下文已抑制:#无需还原
            return 已变换#无需还原
        结果=dict(已变换)#保留其余
        if 完整段落 is not None:#完整段独占
            结果['sections']=[完整段落]#完整段独占
        if 运行时上下文已抑制:#抑制则清空
            结果['contexts']=[]#抑制则清空
        return 结果#结果

# 事件声明（仅文档；经作用域载体派发）：
# system-prompt/assemble(assembly, context, next) @mode waterfall：已组装段落、上下文、工具与变量上的专家瀑布。作用域过滤派发：作用域监听器只收到该作用域的组装。返回值是权威的。所给信号只控制这次显式组装请求。已登记的完整段落在本瀑布之后被还原。
# system-prompt/change() @mode emit：任一提示词提供方变更时发出；不过滤。

__all__=(
    '人设前缀段落名','人设后缀段落名','人设段落名','人设顺序','工具顺序其余',
    '渲染提示词','渲染上下文快照','拼接上下文章节','渲染上下文章节',
    '系统提示词',
    '组装上下文','提示词段落','提示词上下文','已组装段落','已组装上下文',
    '工具提供结果','提示词组装','系统提示词配置',
)#仅中文公开名；Cordis 槽 Config/default 另见类与模块尾

系统提示词.Config=系统提示词.配置#Cordis Config 槽
default=系统提示词#Cordis 默认导出槽
