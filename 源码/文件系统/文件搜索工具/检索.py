"""面向模型的 `grep` 工具：用 ripgrep 正则搜索文件内容。执行通过子进程 seam 以普通 argv 向量直接拉起打包的 ripgrep 二进制，使用固定的面向行的 `rg --json` 命令，因此文件路径、行号与行文本无需按冒号拆分即可解析——本模块拥有面向模型的模式、参数校验、argv 构造、`--json` 记录解析、逐行预览保留、命中保留、分组与格式化；进程相关问题留在 `ctx.subprocess` 后面。"""
import json#按行解析rg --json NDJSON
from ...内核.工具 import 定义工具#导入工具定义器
from ...依赖 import cordis#外部依赖胶水
from .搜索核心 import 搜索错误,预览行,保留grep命中,跑ripgrep,改成工作目录相对,尽力保存格式化结果#导入搜索执行与保留
from .展示 import grep搜索元,搜索视图自元#导入卡片meta投影
from .直接调用 import 已接受直调值#导入顶层调用事后选择

检索最大命中数=250#内联命中默认上限
检索最大行字节=2000#单行预览默认字节上限

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 缺席(对象,键):#字段是否缺席
    """对齐字段 === undefined。"""
    if 对象 is None:#空对象
        return True#缺席
    if isinstance(对象,dict):#映射
        return 键 not in 对象#无键则缺席
    return not hasattr(对象,键)#无属性则缺席

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 校验包含(包含):#校验include为单条正向glob
    """拒绝不是「一条」正向 glob 过滤器的 include：空白字符串、否定模式（!…）以及逗号分隔列表。花括号组内的逗号可以。"""
    if len(包含.strip())==0:#空白则拒绝
        raise Exception('include must be a non-empty glob when given')#空白拒绝
    if 包含.startswith('!'):#否定glob不支持
        raise Exception('include must be a positive glob filter; negated patterns ("!…") are not supported')#否定拒绝
    花括号深度=0#花括号嵌套深度
    for 字符 in 包含:#逐字符扫描逗号是否在花括号外
        if 字符=='{':#进入花括号组
            花括号深度+=1#加深
        elif 字符=='}':#离开花括号组
            花括号深度=max(0,花括号深度-1)#深度不低于0
        elif 字符==',' and 花括号深度==0:#花括号外的逗号视为列表
            raise Exception('include must be one glob, not a comma-separated list (use {a,b} alternation instead)')#拒绝逗号分隔的多个glob

def 解析检索参数(参数):#校验并接受grep参数
    """校验模式 DSL 表达不了的取值约束：非空 pattern（空白仍是合法正则）、给出时非空白的 path、以及单条正向 include glob。否则抛出普通 Error。"""
    if len(取字段(参数,'pattern'))==0:#空正则拒绝
        raise Exception('pattern must be a non-empty string')#空正则拒绝
    if (not 缺席(参数,'path')) and len(取字段(参数,'path').strip())==0:#给出的path不得空白
        raise Exception('path must be a non-empty string when given')#给出的path不得空白
    if not 缺席(参数,'include'):#有include则校验为单条正向glob
        校验包含(取字段(参数,'include'))#校验
    出={'pattern':取字段(参数,'pattern')}#搜索正则
    if not 缺席(参数,'path'):#有path时带上
        出['path']=取字段(参数,'path')#可选搜索根
    if not 缺席(参数,'include'):#有include时带上
        出['include']=取字段(参数,'include')#可选单条正向glob
    return 出#已接受的输入

def 构造检索命令(输入):#构造rg --json argv
    """为一次 grep 调用构造固定的面向行的 rg --json argv。每个模型可控值都是普通 argv 元素——不存在 shell 层；pattern 与 include 以 --flag=value 形式传递，目标放在 -- 之后。"""
    部件=['--json','--regexp='+取字段(输入,'pattern')]#固定json输出与正则
    if not 缺席(输入,'include'):#有include则加一条正向glob
        部件.append('--glob='+取字段(输入,'include'))#正向glob
    if not 缺席(输入,'path'):#有path则放在--之后以免被当成旗标
        部件.append('--')#分隔旗标与路径
        部件.append(取字段(输入,'path'))#搜索根
    return 部件#完整argv（不含二进制）

def 畸形记录(细节,原因=None):#把畸形--json记录变成SEARCH_FAILED
    """统一的畸形输出失败：原始 rg --json 是内部传输，因此缺失或非法的响应字段导致搜索失败，而不是部分结果。"""
    选项={'cause':原因} if 原因 is not None else None#可选cause
    return 搜索错误('grep received malformed ripgrep --json output ('+细节+')','SEARCH_FAILED',选项)#带细节与可选cause

def 解析记录(行):#解析一行rg --json记录
    """把一行 rg --json NDJSON 解析成命中；非命中记录类型返回 None。不是 JSON 的行，或缺少路径/行号/行内容的 match 记录，抛出搜索错误 SEARCH_FAILED。行不是合法 UTF-8 的命中给出占位预览，而不是让整次搜索失败。"""
    try:#解析NDJSON行
        已解析=json.loads(行)#把一行解析成JSON
    except BaseException as 错误:#JSON.parse失败
        raise 畸形记录('a line is not JSON',错误)#非整JSON则判为格式错误
    if not isinstance(已解析,dict) or 已解析 is None:#必须是对象记录
        raise 畸形记录('a record is not an object')#非对象
    if 取字段(已解析,'type')!='match':#非match记录直接跳过
        return None#跳过
    数据=取字段(已解析,'data')#match的data
    if not isinstance(数据,dict) or 数据 is None:#match必须有data对象
        raise 畸形记录('a match record has no data')#缺少data
    路径对象=取字段(数据,'path')#路径对象
    路径文本=取字段(路径对象,'text') if isinstance(路径对象,dict) else None#从path.text取展示路径
    if not isinstance(路径文本,str):#缺少路径文本
        raise 畸形记录('a match record has no path text')#缺少路径
    行号=取字段(数据,'line_number')#行号
    if not isinstance(行号,(int,float)) or isinstance(行号,bool):#缺少行号
        raise 畸形记录('a match record has no line number')#缺少行号
    行内容=取字段(数据,'lines')#行内容对象
    if not isinstance(行内容,dict) or 行内容 is None:#缺少行内容对象
        raise 畸形记录('a match record has no line content')#缺少行内容
    文本=取字段(行内容,'text')#合法UTF-8行文本
    if isinstance(文本,str):#合法UTF-8行文本
        if 文本.endswith('\r\n'):#去掉CRLF
            文本=文本[:-2]#剥CRLF
        elif 文本.endswith('\n'):#去掉LF
            文本=文本[:-1]#剥LF
        return {'path':路径文本,'lineNumber':行号,'line':文本}#去掉行尾换行后作为命中
    if isinstance(取字段(行内容,'bytes'),str):#非UTF-8时ripgrep给base64 bytes
        return {'path':路径文本,'lineNumber':行号,'line':'(line is not valid UTF-8)'}#整次搜索不失败，用占位预览
    raise 畸形记录('a match record has neither line text nor bytes')#既无text也无bytes

def 解析检索命中(标准输出):#解析完整--json stdout为扁平命中
    """把完整的 rg --json stdout 解析成扁平命中，按输出顺序。只消费 match 记录。"""
    命中们=[]#按输出顺序收集命中
    for 行 in 标准输出.split('\n'):#按行拆NDJSON
        if len(行)==0:#空行跳过
            continue#跳过
        命中=解析记录(行)#解析一行，非match为None
        if 命中 is not None:#命中则追加
            命中们.append(命中)#追加
    return 命中们#返回扁平命中

def 命中名词(计数):#英文单复数名词
    """按数量选择 match / matches。"""
    return 'match' if 计数==1 else 'matches'#1用单数，其余用复数

def 格式化检索命中(命中们):#按文件分组格式化命中正文
    """按文件分组扁平命中（首次出现顺序），做成面向模型的正文：每个文件的展示路径，然后每条命中一行 Line N: <text>。"""
    按文件={}#路径到该文件命中
    顺序=[]#首次出现顺序
    for 命中 in 命中们:#按输出顺序分组
        路径=取字段(命中,'path')#文件路径
        if 路径 in 按文件:#已有该文件的分组
            按文件[路径].append(命中)#已有则追加
        else:#没有则新建
            按文件[路径]=[命中]#新建
            顺序.append(路径)#记下顺序
    段们=[]#每个文件一块文本
    for 路径 in 顺序:#按首次出现顺序输出
        组=按文件[路径]#该文件命中
        行们=['Line '+str(取字段(m,'lineNumber'))+': '+取字段(m,'line') for m in 组]#带行号的命中行
        段们.append(路径+'\n'+'\n'.join(行们))#路径后跟命中行
    return '\n\n'.join(段们)#文件块之间空一行

def 格式化检索输出(保留,溢出引用):#格式化面向模型的grep结果
    """格式化面向模型的 grep 结果：找到条数标题、按文件分组的保留命中，以及——结果被截断时——页脚。"""
    if 取字段(保留,'truncated'):#截断时报告已保留与总数
        标题='Found '+str(取字段(保留,'kept'))+' of '+str(取字段(保留,'seen'))+' matches'#截断标题
    else:#未截断时报告全部匹配数
        标题='Found '+str(取字段(保留,'seen'))+' '+命中名词(取字段(保留,'seen'))#未截断标题
    正文=格式化检索命中(取字段(保留,'items') or [])#按文件分组的正文
    if not 取字段(保留,'truncated'):#未截断则标题加正文
        return 标题+'\n\n'+正文#未截断
    if 溢出引用 is not None:#已保存则给定位与取回提示
        恢复='Full grep result stored at: '+str(取字段(溢出引用,'locator'))+'. '+str(取字段(溢出引用,'retrievalHint'))#恢复说明
    else:#未保存则建议收窄搜索
        恢复='The complete result could not be saved; narrow pattern, path, or include to see more.'#未保存说明
    return 标题+'\n\n'+正文+'\n\n('+恢复+')'#截断结果带页脚

def 格式化已保留检索(保留,溢出引用=None):#零命中与有命中的统一入口
    """为 Native 面格式化一份已保留的命中列表。"""
    if 取字段(保留,'seen')==0:#没有任何命中
        return 'No matches found'#零命中文案
    return 格式化检索输出(保留,溢出引用)#有命中则走完整格式化

def 呈现检索调用(参数):#调用中的搜索卡片
    """调用中展示：以 pattern（以及目标/include 过滤器）为标题的搜索卡片。"""
    何处=(' in '+取字段(参数,'path')) if not 缺席(参数,'path') else ''#有path则写入标题
    过滤=(' ('+取字段(参数,'include')+')') if not 缺席(参数,'include') else ''#有include则写入标题
    return {'card':'generic','title':'Grep '+取字段(参数,'pattern')+何处+过滤,'kind':'search','rawInput':取字段(参数,'pattern')}#通用搜索卡片

def 呈现检索结果(参数,结果):#完成调用后的搜索卡片展示
    """完成调用后的展示：从结果的 presentationMeta 投影搜索卡片。畸形或缺失的元数据回退到通用卡片。"""
    _=参数#视图从结果推导，不使用参数
    if 取字段(结果,'isError'):#错误结果不投影搜索卡片
        return None#通用回退
    视图=搜索视图自元(取字段(结果,'meta'))#从不透明meta收窄视图
    if 视图 is None or 取字段(视图,'shape')!='matches':#必须是matches形态
        return None#通用回退
    return 视图#返回搜索卡片

def 应用检索工具(上下文,上限):#注册grep工具与系统提示
    """注册 grep 工具及其系统提示指引。"""
    上下文.systemPrompt.段落({#挂上grep使用指引
        'name':'tool:grep',#段落名
        'order':104,#排序，紧随glob
        'text':'Use the grep tool — not shell grep or rg — to search file contents. Use read on a matched file when you need surrounding context.',#要求用本工具而非shell grep
    })#系统提示段落结束
    def 渲染(参数,值):#把规范值渲染成文本块
        """把规范值渲染成文本块。"""
        _=参数#渲染不依赖原始参数
        return [{'type':'text','text':格式化已保留检索(保留grep命中(取字段(值,'matches') or [],取字段(上限,'maxMatches'),取字段(上限,'maxLineBytes')))}]#按上限保留并格式化
    def 展示元(参数,值):#投影搜索卡片meta
        """投影搜索卡片 meta。"""
        _=参数#meta不依赖原始参数
        return grep搜索元(保留grep命中(取字段(值,'matches') or [],取字段(上限,'maxMatches'),取字段(上限,'maxLineBytes')),取字段(上限,'maxMetaBytes'))#与渲染共用同一保留结果
    def 执行(参数,执行上下文):#执行一次grep
        """校验后拉起打包的 rg --json。"""
        输入=解析检索参数(参数)#校验参数
        运行=解开(跑ripgrep(上下文,执行上下文,'grep',构造检索命令(输入),取字段(上限,'rawOutputMaxBytes'),取字段(上限,'graceMs'),取字段(上限,'stderrMaxBytes')))#拉起打包的rg --json
        if 取字段(运行,'noMatches'):#exit 1表示成功但零命中
            return 已兑现({'matches':[]})#零结果
        全部=[]#收集工作目录相对路径的命中
        for 原始 in 解析检索命中(取字段(运行,'stdout') or ''):#解析全部match记录
            全部.append({#一条展示用命中
                'path':改成工作目录相对(取字段(原始,'path'),取字段(运行,'workdir')),#绝对路径改成工作目录相对
                'lineNumber':取字段(原始,'lineNumber'),#1基行号
                'line':取字段(原始,'line'),#行文本（可能是非UTF-8占位）
            })#单条命中结束
        return 已兑现({'matches':全部})#返回全部命中，截断由事后策略处理
    工具=定义工具({#定义面向模型的grep工具
        'name':'grep',#工具名
        'description':'Search file contents with a ripgrep regular expression. Returns matching lines with line numbers, grouped by file. '#工具描述：按正则搜文件内容
            +'Returns the first '+str(取字段(上限,'maxMatches'))+' matches inline; a capped result reports where the complete match list was saved. '#内联条数上限与溢出保存说明
            +'Use read on a matched file for surrounding context.',#建议对命中文件再用read看上下文
        'parameters':{#面向模型的参数模式
            'pattern':{'type':'string','required':True,'description':'Regular expression to search for (ripgrep syntax).'},#必填ripgrep正则
            'path':{'type':'string','description':'File or directory to search. Defaults to the session workspace; a relative path resolves against it.'},#可选搜索根
            'include':{'type':'string','description':'One glob filter for which files to search (e.g. "*.ts", "*.{js,jsx}"). Not a list; negation is not supported.'},#可选单条正向glob
        },#parameters结束
        'timeoutMs':取字段(上限,'timeoutMs'),#协作超时预算
        'output':{#规范输出与渲染
            'schema':{#规范值JSON模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#属性
                    'matches':{#命中数组
                        'type':'array',#数组
                        'required':True,#必填
                        'items':{#每条命中
                            'type':'object',#对象
                            'additionalProperties':False,#禁止额外字段
                            'properties':{#命中字段
                                'path':{'type':'string','required':True},#文件路径
                                'lineNumber':{'type':'integer','required':True},#行号
                                'line':{'type':'string','required':True},#行文本
                            },#命中properties结束
                        },#items结束
                    },#matches结束
                },#schema.properties结束
            },#schema结束
            'render':渲染,#按上限渲染文本
            'presentationMeta':展示元,#投影搜索卡片meta
        },#output结束
        'execute':执行,#执行一次grep
        'presentCall':呈现检索调用,#调用中卡片
        'presentResult':呈现检索结果,#完成后卡片
    })#defineTool结束
    上下文.tools.登记(工具)#注册到工具表
    def 事后溢出(执行,结果,下一步,*剩余):#超额时把完整结果溢出保存
        """超额时把完整结果溢出保存。"""
        决策=解开(下一步())#先让下游策略处理
        值=已接受直调值(上下文,工具,执行,结果,决策)#仅顶层成功直调才投影
        if 值 is None:#无权溢出则原样返回下游决策
            return 决策#原样
        命中们=取字段(值,'matches') or []#规范值中的全部命中
        if len(命中们)<=取字段(上限,'maxMatches'):#未超额则无需溢出
            return 决策#原样
        #溢出产物保存完整结果：每行做预览，但保留每一条命中（无内联上限），因此恢复文件是完整搜索。
        已预览全部=[{#全部命中只截行不截条数
            'path':取字段(命中,'path'),#路径
            'lineNumber':取字段(命中,'lineNumber'),#行号
            'line':预览行(取字段(命中,'line'),取字段(上限,'maxLineBytes')),#行预览
        } for 命中 in 命中们]#预览列表
        溢出引用=解开(尽力保存格式化结果(#尽力保存完整格式化结果
            上下文,#插件上下文，机会性取spillStore
            执行,#执行身份，提供会话与调用id
            'grep-results.txt',#建议文件名
            'Found '+str(len(命中们))+' '+命中名词(len(命中们))+'\n\n'+格式化检索命中(已预览全部),#完整分组正文
        ))#trySaveFormattedResult结束
        接受={#接受并替换为带溢出定位的文本
            'kind':'accept',#接受此结果
            'content':[{#面向模型的文本内容
                'type':'text',#文本块
                'text':格式化已保留检索(保留grep命中(命中们,取字段(上限,'maxMatches'),取字段(上限,'maxLineBytes')),溢出引用),#内联保留页加溢出页脚
            }],#content结束
        }#替换结果
        if 取字段(决策,'additionalContexts') is not None:#下游附加上下文原样带上
            接受['additionalContexts']=取字段(决策,'additionalContexts')#附加上下文
        return 接受#post-execute替换结果
    上下文.on('tools/post-execute',事后溢出)#post-execute监听
