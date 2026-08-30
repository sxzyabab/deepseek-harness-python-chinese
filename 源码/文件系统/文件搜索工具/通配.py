"""面向模型的 `glob` 工具：发现路径匹配 glob 的文件，按修改时间排序。执行通过子进程 seam 以普通 argv 向量直接拉起打包的 ripgrep 二进制——本模块拥有面向模型的模式、参数校验、argv 构造、结果解析、内联抽样与格式化；进程相关问题留在 `ctx.subprocess` 后面。"""
import os#平台路径分隔符
from ...内核.工具 import 定义工具#导入工具定义器
from ...依赖 import cordis#外部依赖胶水
from .搜索核心 import 跑ripgrep,改成工作目录相对,尽力保存格式化结果#导入搜索执行与溢出保存
from .展示 import glob搜索元,搜索视图自元#导入卡片meta投影
from .直接调用 import 已接受直调值#导入顶层调用事后选择

通配最大结果数=100#内联路径默认上限
通配版本控制排除=('.git','.svn','.hg','.bzr','.jj','.sl')#发现时排除的VCS目录名
分隔符=os.sep#执行平台路径分隔符

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

def 有自有(对象,键):#对齐 Object.hasOwn
    """对齐 Object.hasOwn。"""
    if isinstance(对象,dict):#映射
        return 键 in 对象#映射键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:#没有字典
        return False#没有字典
    return 键 in 字典#自有

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 解析通配参数(参数):#校验并接受glob参数
    """校验模式 DSL 表达不了的取值约束：非空白 `pattern`，以及给出时非空白的 `path`。否则抛出普通 Error。"""
    if len(取字段(参数,'pattern').strip())==0:#空白pattern拒绝
        raise Exception('pattern must be a non-empty string')#空白pattern拒绝
    出={'pattern':取字段(参数,'pattern')}#必填pattern
    if not 缺席(参数,'path'):#给出了path
        路径=取字段(参数,'path')#取出path
        if len(路径.strip())==0:#给出的path不得空白
            raise Exception('path must be a non-empty string when given')#空白path拒绝
        出['path']=路径#带上path
    return 出#已接受的输入

def 构造通配命令(输入):#构造rg --files argv
    """为一次 glob 调用构造固定的 `rg --files` argv。每个模型可控值都是普通 argv 元素——不存在 shell 层；搜索根放在 `--` 之后，因此以短横线开头的路径绝不会被解析成旗标。"""
    段们=[#固定的rg --files参数
        '--files',#列出文件而非搜索内容
        '--glob='+取字段(输入,'pattern'),#模型给定的glob
        '--sort=modified',#按修改时间排序
        '--no-ignore',#不尊重ignore文件
        '--hidden',#包含隐藏文件
    ]#固定段结束
    for 名 in 通配版本控制排除:#每个VCS名展开两条排除glob
        段们.append('--glob=!**/'+名)#任意深度目录剪枝
        段们.append('--glob=!**/'+名+'/**')#根在目录内时仍排除内容
    if not 缺席(输入,'path'):#有path则放在--之后以免被当成旗标
        段们.append('--')#分隔旗标与位置参数
        段们.append(取字段(输入,'path'))#搜索根
    return 段们#完整argv（不含二进制）

def 剥前导分隔符(路径):#去掉前导路径分隔符
    """只剥执行平台识别的前导分隔符。"""
    起点=0#第一个非分隔符下标
    while 起点<len(路径) and 路径[起点]==分隔符:#跳过前导分隔符
        起点+=1#前进
    return 路径[起点:]#剩下的路径

def 相对搜索根(路径,根):#相对搜索根的展示路径
    """选择顶层分组前去掉展示用的搜索根前缀。"""
    if 根=='.':#根为.时去掉./前缀
        前缀='.'+分隔符#平台上的./
        if 路径.startswith(前缀):#有./前缀
            return 路径[len(前缀):]#去掉./
        return 路径#无前缀原样
    根末=len(根)#从末尾回退分隔符
    while 根末>0 and 根[根末-1]==分隔符:#去掉根尾部分隔符
        根末-=1#回退
    修剪根=根[0:根末]#不含尾部分隔符的根
    if len(修剪根)==0:#根只剩分隔符则只剥路径前导分隔符
        return 剥前导分隔符(路径)#剥前导
    if 路径==修剪根:#路径就是根本身
        return ''#空相对
    if 路径.startswith(修剪根+分隔符):#路径在根之下
        return 路径[len(修剪根)+1:]#去掉根与分隔符
    return 路径#不在根下则原样返回

def 顶层段(路径):#取相对搜索根的顶层段
    """一条展示路径的前导路径段——该路径所在的、相对搜索根的顶层条目。没有分隔符的路径本身就是顶层条目。"""
    修剪=剥前导分隔符(路径)#先剥前导分隔符
    切口=修剪.find(分隔符)#第一个分隔符
    return 修剪 if 切口==-1 else 修剪[0:切口]#无分隔符则整段，否则取第一段

def 跨顶层抽样(路径们,最大条数,根='.'):#跨顶层条目轮询抽样
    """用跨完整结果顶层条目的轮询选择超额结果的内联页，而不是取其头部。每个顶层条目先分到一个名额，再给第二个；耗尽的组退出。"""
    组们={}#顶层键到该组全部路径
    活跃=[]#仍有未取路径的组
    for 路径 in 路径们:#按修改时间顺序建组
        键=顶层段(相对搜索根(路径,根))#相对搜索根的顶层段
        if 键 not in 组们:#首次见到该顶层
            条目们=[路径]#该组的路径列表
            组们[键]=条目们#登记新组
            活跃.append({'key':键,'items':条目们,'index':0,'current':路径})#第一轮即可取
        else:#已有该顶层
            组们[键].append(路径)#追加到组内，组内保持修改时间顺序
    已取={}#已抽入内联页的按组路径
    计数=0#已抽路径数
    while len(活跃)>0 and 计数<最大条数:#还有组且未抽满
        下一活跃=[]#下一轮仍有剩余的组
        for 组 in 活跃:#本轮每个组取一条
            if 计数>=最大条数:#页已满则停
                break#跳出本轮
            计数+=1#计入一条
            键=取字段(组,'key')#顶层键
            当前=取字段(组,'current')#本轮路径
            if 键 not in 已取:#该组第一条
                已取[键]=[当前]#新建桶
            else:#该组再追加
                已取[键].append(当前)#追加
            下标=取字段(组,'index')+1#组内下一候选
            条目们=取字段(组,'items')#组内全部路径
            if 下标<len(条目们):#未耗尽
                下一活跃.append({'key':键,'items':条目们,'index':下标,'current':条目们[下标]})#进入下一轮
        活跃=下一活跃#只保留仍有剩余的组
    页=[]#展平页
    for 键 in 已取:#保持首次出现的顶层顺序
        页.extend(已取[键])#该组已抽路径
    return {'items':页,'shown':len(已取),'total':len(组们)}#展平页并报告顶层覆盖



def 格式化通配页(条目们,已见,溢出引用,依据):#一页路径加页脚
    """格式化一页有界路径及其完整排序结果的恢复路径。"""
    正文='\n'.join(条目们)#路径每行一条
    if 溢出引用 is not None:#已保存则给定位与取回提示
        恢复='Full sorted result stored at: '+取字段(溢出引用,'locator')+'. '+取字段(溢出引用,'retrievalHint')#定位与取回
    else:#未保存则建议收窄搜索
        恢复='The complete result could not be saved; narrow pattern or path to see more.'#收窄建议
    return 正文+'\n\n(Showing '+str(len(条目们))+' of '+str(已见)+' paths'+依据+' '+恢复+')'#正文加展示条数与恢复



def 格式化通配输出(抽样,已见,溢出引用):#格式化抽样页与恢复说明
    """格式化截断抽样页及其完整结果恢复路径。扁平结果保留普通页脚，因为其抽样就是修改时间头部。"""
    if 取字段(抽样,'total')==已见:#完整结果每个路径都是独立顶层时
        依据='.'#扁平结果：页脚用句点接恢复句
    else:#跨顶层抽样说明
        依据=', sampled across '+str(取字段(抽样,'shown'))+' of the '+str(取字段(抽样,'total'))+' top-level entries this pattern matched instead of taken in modification-time order.'#跨顶层说明
        if 取字段(抽样,'shown')<取字段(抽样,'total'):#未覆盖全部顶层时建议收窄path
            依据=依据+' Narrow path to inspect a specific subtree.'#收窄建议
    return 格式化通配页(取字段(抽样,'items'),已见,溢出引用,依据)#交给统一页格式化



def 渲染通配路径(路径们,上限,根,溢出引用=None):#按上限渲染glob路径
    """相对其搜索根，为 Native 面有界并格式化一份规范路径列表。"""
    if len(路径们)==0:#零结果
        return 'No files found'#零结果文案
    if len(路径们)<=取字段(上限,'maxResults'):#未超额则整份按修改时间列出
        return '\n'.join(路径们)#整份列出
    if not 取字段(上限,'sampleOverCapGlobResults'):#部署选择取修改时间头部
        return 格式化通配页(路径们[0:取字段(上限,'maxResults')],len(路径们),溢出引用,'.')#取头部并带恢复页脚
    return 格式化通配输出(跨顶层抽样(路径们,取字段(上限,'maxResults'),根),len(路径们),溢出引用)#跨顶层抽样



def 通配卡片页(路径们,上限,根):#卡片与文本共用的内联页
    """已完成 glob 卡片展示的内联路径页，计算方式与渲染通配路径相同，因此卡片与文本对哪些路径活过上限意见一致。"""
    if len(路径们)<=取字段(上限,'maxResults'):#未超额则整份
        return {'items':路径们,'truncated':False}#整份
    if not 取字段(上限,'sampleOverCapGlobResults'):#取修改时间头部
        return {'items':路径们[0:取字段(上限,'maxResults')],'truncated':True}#头部截断
    return {'items':取字段(跨顶层抽样(路径们,取字段(上限,'maxResults'),根),'items'),'truncated':True}#跨顶层抽样



def 呈现通配调用(参数):#调用中的搜索卡片
    """调用中展示：以 pattern（以及根）为标题的搜索卡片。"""
    何处=(' in '+取字段(参数,'path')) if not 缺席(参数,'path') else ''#有path则写入标题
    return {'card':'generic','title':'Glob '+取字段(参数,'pattern')+何处,'kind':'search','rawInput':取字段(参数,'pattern')}#通用搜索卡片



def 呈现通配结果(参数,结果):#完成调用后的搜索卡片展示
    """完成调用后的展示：从结果的 presentationMeta 投影搜索卡片。畸形或缺失的元数据回退到通用卡片。"""
    if 取字段(结果,'isError'):#错误结果不投影搜索卡片
        return None#无搜索卡片
    视图=搜索视图自元(取字段(结果,'meta'))#从不透明meta收窄视图
    if 视图 is None or 取字段(视图,'shape')!='paths':#必须是paths形态
        return None#回退通用卡片
    return 视图#返回搜索卡片



def 应用通配工具(上下文,上限):#注册glob工具与系统提示
    """注册 glob 工具及其系统提示指引。"""
    if 取字段(上限,'sampleOverCapGlobResults'):#超额时系统提示用语
        超额指引='while a larger one is sampled across top-level entries, so it spans the tree instead of one subtree.'#跨顶层抽样
        超额描述='a larger result instead returns '+str(取字段(上限,'maxResults'))+' paths sampled across top-level entries'#跨顶层抽样
    else:#取修改时间头部
        超额指引='while a larger one keeps the modification-time-ordered head.'#取修改时间头部
        超额描述='a larger result returns the first '+str(取字段(上限,'maxResults'))+' paths in modification-time order'#取修改时间头部
    上下文.systemPrompt.段落({#挂上glob使用指引
        'name':'tool:glob',#段落名
        'order':103,#排序，在grep之前
        'text':'Use the glob tool — not shell find — to discover files by path pattern. A pattern with no "/" matches basenames at any depth, so "*" matches every file in the tree rather than its top level. '#要求用本工具而非shell find
            +'Results are files only, never directories, and include hidden and ignored files: a result that fits comes back in modification-time order, '+超额指引,#结果约定与超额策略
    })#系统提示段落结束
    def 渲染(参数,值):#按上限渲染文本
        """按上限渲染文本块。"""
        return [{'type':'text','text':渲染通配路径(取字段(值,'paths'),上限,取字段(值,'root'))}]#单个文本块
    def 展示元(参数,值):#投影搜索卡片meta
        """投影搜索卡片meta。"""
        页=通配卡片页(取字段(值,'paths'),上限,取字段(值,'root'))#与文本同一内联页
        return glob搜索元({'items':取字段(页,'items'),'truncated':取字段(页,'truncated'),'seen':len(取字段(值,'paths'))},取字段(上限,'maxMetaBytes'))#再按字节预算截meta
    def 执行(参数,执行上下文):#执行一次glob
        """校验后拉起打包的 rg --files。"""
        输入=解析通配参数(参数)#校验参数
        运行=解开(跑ripgrep(上下文,执行上下文,'glob',构造通配命令(输入),取字段(上限,'rawOutputMaxBytes'),取字段(上限,'graceMs'),取字段(上限,'stderrMaxBytes')))#拉起打包的rg --files
        根='.' if 缺席(输入,'path') else 改成工作目录相对(取字段(输入,'path'),取字段(运行,'workdir'))#展示用搜索根
        if 取字段(运行,'noMatches'):#exit 1表示成功但零文件
            return 已兑现({'root':根,'paths':[]})#空路径
        全部=[]#收集工作目录相对路径
        for 行 in 取字段(运行,'stdout').split('\n'):#rg --files每行一条路径
            if len(行)==0:#空行跳过
                continue#下一行
            全部.append(改成工作目录相对(行,取字段(运行,'workdir')))#绝对路径改成工作目录相对
        return 已兑现({'root':根,'paths':全部})#返回全部路径，截断由事后策略处理
    工具=定义工具({#定义面向模型的glob工具
        'name':'glob',#工具名
        'description':'Find files whose paths match a glob pattern. Returns matching file paths — never directories — '#工具描述：按glob发现文件
            +'including hidden and ignored files (VCS metadata directories are excluded). '#含隐藏与忽略，排除VCS
            +'Up to '+str(取字段(上限,'maxResults'))+' paths come back in modification-time order; '+超额描述+', '#内联上限与超额策略
            +'says so, and reports where the complete sorted list was saved. This tool does not enumerate directory entries.',#溢出定位且不列举目录项
        'parameters':{#面向模型的参数模式
            'pattern':{#必填glob
                'type':'string',#字符串
                'required':True,#必填
                'description':'Glob pattern to match file paths against (e.g. "**/*.ts", "src/**/*.test.js"). '#路径glob说明
                    +'A pattern with no "/" matches the basename at any depth, so "*" and "*.ts" both search the whole tree; include a separator to anchor the depth.',#无斜杠匹配任意深度基名
            },#pattern结束
            'path':{'type':'string','description':'Directory to search in. Defaults to the session workspace; a relative path resolves against it.'},#可选搜索根
        },#parameters结束
        'timeoutMs':取字段(上限,'timeoutMs'),#协作超时预算
        'output':{#规范输出与渲染
            'schema':{#规范值JSON模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#属性
                    'root':{'type':'string','required':True},#展示用搜索根
                    'paths':{'type':'array','required':True,'items':{'type':'string'}},#发现的文件路径
                },#schema.properties结束
            },#schema结束
            'render':渲染,#按上限渲染文本
            'presentationMeta':展示元,#投影搜索卡片meta
        },#output结束
        'execute':执行,#执行一次glob
        'presentCall':呈现通配调用,#调用中卡片
        'presentResult':呈现通配结果,#完成后卡片
    })#defineTool结束
    上下文.tools.登记(工具)#注册到工具表
    def 事后臂(执行上下文,结果,下一步,*剩余):#超额时把完整结果溢出保存
        """超额时把完整结果溢出保存。"""
        决策=解开(下一步())#先让下游策略处理
        值=已接受直调值(上下文,工具,执行上下文,结果,决策)#仅顶层成功直调才投影
        if 值 is None:#无权溢出则原样返回下游决策
            return 决策#原样
        路径们=取字段(值,'paths')#规范值中的全部路径
        if len(路径们)<=取字段(上限,'maxResults'):#未超额则无需溢出
            return 决策#原样
        溢出引用=解开(尽力保存格式化结果(上下文,执行上下文,'glob-results.txt','\n'.join(路径们)))#尽力保存完整排序列表
        接受={#接受并替换为带溢出定位的文本
            'kind':'accept',#接受此结果
            'content':[{'type':'text','text':渲染通配路径(路径们,上限,取字段(值,'root'),溢出引用)}],#内联页加溢出页脚
        }#替换骨架
        if 有自有(决策,'additionalContexts'):#下游附加上下文原样带上
            接受['additionalContexts']=取字段(决策,'additionalContexts')#附加上下文
        return 接受#post-execute替换结果
    上下文.on('tools/post-execute',事后臂)#post-execute监听
