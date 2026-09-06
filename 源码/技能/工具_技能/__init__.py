"""持久会话技能目录与面向模型的 skill 加载工具。"""
import hashlib#目录条目摘要用 SHA-256
import json#目录条目规范 JSON 编码
import re#技能手势正则与空白压缩
from ...依赖.schemastery import 数字字段#配置字段
from ...内核.工具 import 定义工具#定义面向模型的工具
from ...模型后端.llm import 创建用户消息#构造用户消息
from ...工具.超时 import 若已中止则抛出#工具取消信号
from ..技能 import (#技能 seam 公开符号
    转义文本,#转义目录描述
    是否模型可调用,#模型面是否可调用
    是否技能名,#公开技能名文法
    是否用户可调用,#用户面是否可调用
    渲染技能内容,#规范技能块
)#技能 seam 导入结束
__all__=[#仅中文公开名；Cordis 英文槽不入表
    '名称','注入','目录描述默认最大长度','技能手势','配置','应用','工具技能错误',
]#公开面结束

名称='tool-skill'#Cordis插件名
注入=['agents','tools','skills']#依赖智能体、工具与技能服务
目录描述默认最大长度=500#目录描述默认最大长度
技能手势=re.compile(r'(^|\s)/([a-z0-9]+(?:-[a-z0-9]+)*)(?=\s|\Z)',re.ASCII)#用户显式/name手势
配置={#面向模型的技能目录配置
    'catalogDescriptionMaxLength':数字字段(默认值=目录描述默认最大长度),#默认500
}#配置模式结束

class 工具技能错误(Exception):
    """本包异常基类。错误消息原样英文。"""

def 浅拷贝基址(基址):
    """浅拷贝提供方给出的资源基址记录。基址是 dict。"""
    拷贝={}#目标记录
    if 'kind' in 基址:#有种类
        拷贝['kind']=基址['kind']#写入种类
    if 'path' in 基址:#有路径
        拷贝['path']=基址['path']#写入路径
    if 'url' in 基址:#有网址
        拷贝['url']=基址['url']#写入网址
    if 'description' in 基址:#有描述
        拷贝['description']=基址['description']#写入描述
    return 拷贝#浅拷贝结果

def 查找选项(智能体,信号):
    """按智能体会话工作目录、取消信号与观察作用域构造查找选项。智能体是跨包 dict。"""
    会话=智能体['session']#会话记录
    头=会话['header']#会话头
    工作目录=头['cwd'] if 'cwd' in 头 else None#工作区根可缺
    return {'cwd':工作目录,'signal':信号,'scope':智能体}#查找选项

def 目录源条目(技能列表,描述最大长度):
    """与渲染出的目录行镜像的持久条目列表，供非模型消费方使用。技能是 dict。"""
    结果=[]#源条目
    for 技能 in 技能列表:#逐条投影
        结果.append({'name':技能['name'],'description':目录描述(技能['description'],描述最大长度)})#一条目录源条目
    return 结果#源条目

def 校验正整数(名,值,下限=1):
    """配置入口正整数断言，排除布尔，非法则在加载时大声失败。"""
    if isinstance(值,bool):#布尔不是整数
        raise 工具技能错误('tool-skill: '+名+' must be an integer greater than or equal to '+str(下限))#加载时大声失败
    if isinstance(值,float) and 值.is_integer():#整值浮点
        值=int(值)#收成int
    if not isinstance(值,int) or 值<下限:#非整数或低于下限
        raise 工具技能错误('tool-skill: '+名+' must be an integer greater than or equal to '+str(下限))#加载时大声失败

def 目录描述(值,最大长度):
    """规范化、长度受限的描述，恰好是目录发布它的样子（未转义）。按字符数截断。"""
    规范化=re.sub(r'\s+',' ',值,count=0,flags=re.ASCII).strip()#空白压成单空格
    if len(规范化)<=最大长度:#未超上限
        return 规范化#原文
    return 规范化[0:最大长度-3]+'...'#超长加省略号

def 渲染目录条目(条目列表):
    """面向模型的目录行，从源所记录的同一批条目投影。伪 XML 转义属于此框架，不属于已发布事实，因此在此施加且永不存储。名称已经技能名文法校验，不含可转义字符。条目是 dict。"""
    行列表=[]#模型行
    for 条目 in 条目列表:#逐条
        行列表.append('- `'+条目['name']+'`: '+转义文本(条目['description']))#反引号名加转义描述
    return 行列表#模型行

def 摘要目录条目(条目列表):
    """目录身份基于持久条目列表，而不是渲染出的散文。变的是条目；周围的 system-reminder 框架是写给模型的，不得决定是否需要重新发布。条目是 dict。"""
    片段列表=[]#规范片段
    for 条目 in 条目列表:#逐条JSON而不是分隔符
        片段列表.append(json.dumps([条目['name'],条目['description']],ensure_ascii=False,separators=(',',':'),allow_nan=False))#加引号才能让边界精确
    规范='\n'.join(片段列表)#规范文本
    return hashlib.sha256(规范.encode('utf-8')).hexdigest()#十六进制摘要

def 读取目录条目(来源):
    """一条持久目录消息的条目，记录不可用则 None。会话事件可能是恢复、分叉或外部写入的种子，种子校验只保证来源对象带非空 kind；不可读记录被当作不是本插件的目录，而不是在步进监听器里抛错。来源是 dict。"""
    if 来源 is None or 'entries' not in 来源:#可能缺失
        return None#不是本目录
    条目列表=来源['entries']#条目表
    if not isinstance(条目列表,(list,tuple)):#不是数组则不是本目录
        return None#不是本目录
    可读=[]#可读条目
    for 条目 in 条目列表:#逐条校验
        if 条目 is None:#空条目
            return None#非整表可读则放弃
        if isinstance(条目,(str,bytes,int,float,bool)):#原语不是条目
            return None#非整表可读则放弃
        if 'name' not in 条目 or 'description' not in 条目:#缺字段
            return None#非整表可读则放弃
        名=条目['name']#技能名
        描述=条目['description']#描述
        if isinstance(名,str) is False or 名=='' or isinstance(描述,str) is False:#名非空、描述为字符串
            return None#非整表可读则放弃
        可读.append({'name':名,'description':描述})#收下
    return 可读#整表可读

def 事件来源种类(事件):
    """读会话事件 data.source.kind。事件是跨包 dict。"""
    if 'data' not in 事件:#无数据
        return None#无种类
    数据=事件['data']#事件数据
    if 数据 is None or 'source' not in 数据:#无来源
        return None#无种类
    来源=数据['source']#来源
    if 来源 is None or 'kind' not in 来源:#无种类
        return None#无种类
    return 来源['kind']#种类

def 消息来源种类(消息):
    """读消息 source.kind。消息是跨包 dict。"""
    if 'source' not in 消息:#无来源
        return None#无种类
    来源=消息['source']#来源
    if 来源 is None or 'kind' not in 来源:#无种类
        return None#无种类
    return 来源['kind']#种类

def 目录历史(智能体):
    """从近到远扫描会话事件，返回最近可见目录摘要以及是否曾发布过可读目录。智能体是跨包 dict。"""
    会话=智能体['session']#会话
    表面=会话['surface'] if 'surface' in 会话 else None#会话表面
    节点=表面['nodes'] if 表面 is not None and 'nodes' in 表面 else None#当前表面可见的序号
    可见=set(节点 if 节点 is not None else [])#可见序号集合
    事件列表=会话['events'] if 'events' in 会话 else []#事件流
    if 事件列表 is None:#没有事件流
        事件列表=[]#空流
    曾发布=False#是否曾发布过
    下标=len(事件列表)-1#从近到远
    while 下标>=0:#扫描
        事件=事件列表[下标]#下标在范围内
        下标-=1#前进
        if 'type' not in 事件 or 事件['type']!='user/message':#非用户消息
            continue#跳过
        if 事件来源种类(事件)!='skill-catalog':#非目录消息
            continue#跳过
        数据=事件['data']#事件数据
        条目列表=读取目录条目(数据['source'])#宽松读条目
        if 条目列表 is None:#不可读则跳过
            continue#跳过
        摘要=摘要目录条目(条目列表)#该条目录身份
        曾发布=True#至少发布过一次
        if 'seq' in 事件 and 事件['seq'] in 可见:#最近可见的那份
            return {'visibleDigest':摘要,'published':曾发布}#可见摘要
    return {'published':曾发布}#没有可见目录，但可能曾发布过

def 目录消息(消息列表):
    """扫描本步消息，返回第一份可读技能目录及其条目。消息是 dict。"""
    if 消息列表 is None:#没有消息
        return None#本步没有
    for 消息 in 消息列表:#扫描本步
        if 消息来源种类(消息)!='skill-catalog':#非目录
            continue#跳过
        条目列表=读取目录条目(消息['source'])#宽松读
        if 条目列表 is not None:#第一份可读目录
            return {'message':消息,'entries':条目列表}#带回条目
    return None#本步没有

def 已调用技能名(消息列表):
    """从声称用户消息中取出 /name 手势词元，按首次出现去重。扫描直接用户输入的每一个文本块；其它来源不能伪造手势。消息是 dict。"""
    名称列表=[]#首次出现序
    if 消息列表 is None:#没有消息
        return 名称列表#空
    for 消息 in 消息列表:#扫描声称批次
        if 消息来源种类(消息)!='user':#只认用户来源
            continue#跳过
        if 'content' not in 消息:#没有内容
            continue#跳过
        内容=消息['content']#内容块
        if 内容 is None:#没有内容
            continue#跳过
        for 块 in 内容:#每个内容块
            if 'type' not in 块 or 块['type']!='text':#只扫文本
                continue#跳过
            if 'text' not in 块:#无文本
                continue#跳过
            文本=块['text']#文本
            if isinstance(文本,str) is False:#非字符串
                continue#跳过
            for 匹配 in re.finditer(技能手势,文本):#全局手势
                名=匹配.group(2)#捕获的技能名
                if 名 is not None and 名 not in 名称列表:#首次出现才收
                    名称列表.append(名)#收下
    return 名称列表#去重后的名

def 渲染目录消息(条目列表):
    """构造首次发布的 catalog 形态用户消息。"""
    行列表=[#面向模型的框架（字面量不翻译）
        '<system-reminder>',#系统提醒开
        'A skill is a reusable set of task-specific instructions. The following skills are available in this session:',#技能说明
        '',#空行
        '<available_skills>',#可用技能开
    ]#框架前半
    行列表.extend(渲染目录条目(条目列表))#条目行
    行列表.extend([#框架后半
        '</available_skills>',#可用技能闭
        '',#空行
        "If the user names a skill, or the task clearly matches a skill's description, call the `skill` tool with the exact skill name before taking task actions. Load all applicable skills, then follow their full instructions. This catalog contains summaries only; do not infer or follow a skill's instructions until it has been loaded.",#调用指引
        'A user may also invoke a skill directly; its <skill_content> block then appears in this conversation. Follow it, and do not call the `skill` tool again for that skill.',#用户直调说明
        '</system-reminder>',#系统提醒闭
    ])#框架后半结束
    return 创建用户消息({#构造catalog形态用户消息
        'content':[{#单一文本块
            'type':'text',#文本
            'text':'\n'.join(行列表),#按行拼接
        }],#内容结束
        'source':{#持久目录源
            'kind':'skill-catalog',#来源标签
            'form':'catalog',#目录形态
            'entries':条目列表,#恰好这些条目
        },#来源结束
    })#创建结束

def 渲染目录更新(条目列表):
    """构造带 update 标记的替换目录用户消息。"""
    if len(条目列表)==0:#空替换与非空替换文案不同
        可用性=[#清空
            'No skills are currently available through the `skill` tool. Do not use names from earlier skill catalogs.',#不要用旧名
            'A user may still invoke a skill directly; its <skill_content> block then appears in this conversation. Follow it, and do not call the `skill` tool for it.',#用户仍可直调
        ]#清空文案结束
    else:#非空替换
        可用性=[#非空替换
            'Use only names in this replacement catalog. If the user names a listed skill, or the task clearly matches its description, call the `skill` tool with the exact name before acting.',#只用新目录
            'A user may also invoke a skill directly; its <skill_content> block then appears in this conversation. Follow it, and do not call the `skill` tool again for that skill.',#用户直调说明
        ]#非空文案结束
    行列表=[#替换框架（字面量不翻译）
        '<system-reminder>',#系统提醒开
        'The available skill catalog changed. This complete catalog replaces every earlier available-skills list in this session:',#整表替换
        '',#空行
        '<available_skills>',#可用技能开
    ]#框架前半
    行列表.extend(渲染目录条目(条目列表))#条目行
    行列表.extend(['</available_skills>','']+可用性+['</system-reminder>'])#闭标签与指引
    return 创建用户消息({#带update的目录消息
        'content':[{#单一文本块
            'type':'text',#文本
            'text':'\n'.join(行列表),#按行拼接
        }],#内容结束
        'source':{#持久替换源
            'kind':'skill-catalog',#来源标签
            'form':'catalog',#目录形态
            'update':True,#标记替换
            'entries':条目列表,#恰好这些条目
        },#来源结束
    })#创建结束

def 取出决策消息(决策):
    """取出步进决策上的消息列表。决策是跨包 dict。缺键或 None 当空列表。"""
    if 'messages' not in 决策:#缺键
        return []#空
    消息列表=决策['messages']#消息
    if 消息列表 is None:#空
        return []#空
    return list(消息列表)#拷贝

def 应用(上下文,配置值=None):
    """注册面向模型的技能加载器及其与可见性匹配的持久会话目录。仅当调用方智能体解析到本插件恰好这次工具注册时才发出目录；限制或同名作用域遮蔽因此会同时去掉模式与其调用指引。"""
    if 配置值 is None:#缺省空配置
        配置值={}#空配置
    目录描述最大长度=配置值['catalogDescriptionMaxLength'] if 'catalogDescriptionMaxLength' in 配置值 else 目录描述默认最大长度#解析上限
    校验正整数('catalogDescriptionMaxLength',目录描述最大长度,3)#最小3，为省略号留位置
    def 渲染(参数,值):
        """把结构化技能结果渲染成规范 skill_content 文本块。"""
        return [{'type':'text','text':渲染技能内容(值)}]#单个文本块
    def 执行(参数,执行上下文):
        """按精确技能名加载模型可调用技能正文。参数与执行上下文是跨包 dict。"""
        名=参数['name'] if 'name' in 参数 else None#技能名参数
        if 是否技能名(名) is False:#名不合法
            raise 工具技能错误('invalid skill name "'+str(名)+'"')#非法名
        智能体=执行上下文['agent']#调用方智能体
        查找=查找选项(智能体,执行上下文['signal'] if 'signal' in 执行上下文 else None)#cwd加取消加观察作用域
        摘要=None#目录里的摘要
        for 项 in 上下文.skills.列出(查找):#先在目录里找
            if 项['name']==名:#名称匹配
                摘要=项#记下
                break#已找到
        if 摘要 is None:#目录没有
            raise 工具技能错误('skill "'+名+'" is unknown or no longer available')#未知或已消失
        if 是否模型可调用(摘要) is False:#用户专用技能
            raise 工具技能错误('skill "'+名+'" is not available for model invocation')#模型不可调用
        技能=上下文.skills.获取(名,查找)#加载正文
        if 技能 is None:#加载后消失
            raise 工具技能错误('skill "'+名+'" is unknown or no longer available')#未知或已消失
        if 是否模型可调用(技能) is False:#定义上不可调用
            raise 工具技能错误('skill "'+名+'" is not available for model invocation')#模型不可调用
        结果={'name':技能['name'],'provider':技能['provider'],'content':技能['content']}#结构化结果
        if 'resourceBase' in 技能 and 技能['resourceBase'] is not None:#有基址则展开
            结果['resourceBase']=浅拷贝基址(技能['resourceBase'])#浅拷贝基址
        return 结果#结构化结果
    def 呈现调用(参数):
        """调用时通用读卡片。参数是工具入参 dict。"""
        return {#通用读卡片
            'card':'generic',#通用卡片
            'title':'Load skill '+参数['name'],#标题
            'kind':'read',#读种类
            'rawInput':参数['name'],#原始输入
        }#卡片结束
    技能工具=定义工具({#面向模型的skill工具
        'name':'skill',#工具名
        'description':'Load the full instructions for an available skill. Call this with the exact skill name from the session skill catalog before acting on a task that names or clearly matches that skill.',#工具描述
        'parameters':{#参数模式
            'name':{'type':'string','required':True,'description':'The exact skill name from the available skills list.'},#技能名参数
        },#参数结束
        'output':{#结构化输出加渲染
            'schema':{#输出JSON模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#字段
                    'name':{'type':'string','required':True},#技能名
                    'provider':{'type':'string','required':True},#提供方
                    'resourceBase':{#可选资源基址
                        'oneOf':[#三种形态
                            {#目录
                                'type':'object',#对象
                                'additionalProperties':False,#禁止额外字段
                                'properties':{#字段
                                    'kind':{'type':'string','required':True,'const':'directory'},#目录种类
                                    'path':{'type':'string','required':True},#基目录路径
                                },#字段结束
                            },#目录结束
                            {#URL
                                'type':'object',#对象
                                'additionalProperties':False,#禁止额外字段
                                'properties':{#字段
                                    'kind':{'type':'string','required':True,'const':'url'},#URL种类
                                    'url':{'type':'string','required':True},#基URL
                                },#字段结束
                            },#URL结束
                            {#不透明
                                'type':'object',#对象
                                'additionalProperties':False,#禁止额外字段
                                'properties':{#字段
                                    'kind':{'type':'string','required':True,'const':'opaque'},#不透明种类
                                    'description':{'type':'string','required':True},#描述
                                },#字段结束
                            },#不透明结束
                        ],#oneOf结束
                    },#resourceBase结束
                    'content':{'type':'string','required':True},#技能正文
                },#字段结束
            },#schema结束
            'render':渲染,#模型看到规范技能块
        },#output结束
        'execute':执行,#加载技能正文
        'presentCall':呈现调用,#UI卡片
    })#定义结束
    上下文.tools.登记(技能工具)#挂到工具注册表
    def 用户调用监听(载荷,下一步,*剩余):
        """用户显式技能调用：声称用户消息里以空白为界的 /name 若是用户可调用技能，则把渲染后的正文作为指令上下文追加在本步其余注入之后。载荷是跨包 dict。"""
        决策=下一步()#瀑布同步，先让后面的含目录跑完
        if 决策['kind']=='reject':#拒绝则不注入
            return 决策#原样返回
        名称列表=已调用技能名(载荷['messages'] if 'messages' in 载荷 else None)#声称用户消息里的/name
        if len(名称列表)==0:#无手势
            return 决策#保持
        信号=载荷['signal'] if 'signal' in 载荷 else None#取消信号
        若已中止则抛出(信号)#注入前查取消
        智能体=载荷['agent']#本步智能体
        查找=查找选项(智能体,信号)#查找上下文
        注入列表=[]#待追加的指令消息
        for 名 in 名称列表:#按首次出现序
            技能=上下文.skills.获取(名,查找)#加载定义
            若已中止则抛出(信号)#每次加载后查取消
            if 技能 is None or 是否用户可调用(技能) is False:#未知名与用户禁用仍是普通散文
                continue#不认则跳过
            注入列表.append(创建用户消息({#构造注入消息
                'content':[{'type':'text','text':渲染技能内容(技能)}],#规范技能块
                'source':{'kind':'skill-invocation','name':名,'form':'instructions'},#注入来源
            }))#push结束
        if len(注入列表)==0:#没有可注入的
            return 决策#保持
        return {'kind':'enter','messages':取出决策消息(决策)+注入列表}#目录之后追加指令
    上下文.监听('agent/pre-step',用户调用监听)#用户调用监听器
    def 目录监听(载荷,下一步,*剩余):
        """在工具之后注册，使反向拆除先去掉指引。恰好这次定义身份防止仅同名 skill 的作用域遮蔽继承本目录。载荷是跨包 dict。"""
        决策=下一步()#瀑布同步，先跑后续监听器
        if 决策['kind']=='reject':#拒绝则不动目录
            return 决策#原样返回
        信号=载荷['signal'] if 'signal' in 载荷 else None#取消信号
        若已中止则抛出(信号)#快照前查取消
        智能体=载荷['agent']#本步智能体
        工具可见=上下文.tools.获取(技能工具['name'],智能体) is 技能工具#恰好是本注册才发目录
        if 工具可见 is True:#工具可见才发现
            快照=上下文.skills.快照(查找选项(智能体,信号))#拍完整快照
        else:#不可见则空且完整
            快照={'skills':[],'complete':True}#用于撤回旧目录
        若已中止则抛出(信号)#快照后查取消
        if 快照['complete'] is False:#不完整发现不发布
            return 决策#保留上次完好
        技能列表=[]#只广告模型可调用
        快照技能=快照['skills'] if 'skills' in 快照 else []#技能表
        if 快照技能 is None:#空
            快照技能=[]#空
        for 项 in 快照技能:#过滤
            if 是否模型可调用(项):#模型可调用
                技能列表.append(项)#收下
        条目列表=目录源条目(技能列表,目录描述最大长度)#持久条目
        摘要=摘要目录条目(条目列表)#条目身份
        历史=目录历史(智能体)#会话里上次可见目录
        已有=目录消息(取出决策消息(决策))#本步已有的目录消息
        if 'visibleDigest' in 历史 and 历史['visibleDigest']==摘要:#表面已是这份目录
            if 已有 is None:#本步没有重复注入
                return 决策#保持
            过滤后=[]#去掉重复注入
            已有标识=已有['message']['id']#已有目录消息id
            for 消息 in 取出决策消息(决策):#过滤
                if 消息['id']!=已有标识:#不是重复目录
                    过滤后.append(消息)#保留
            return {'kind':'enter','messages':过滤后}#去掉重复注入
        if 已有 is not None and 摘要目录条目(已有['entries'])==摘要:#本步注入已是目标
            return 决策#保持
        if ('published' not in 历史 or 历史['published'] is False) and len(技能列表)==0:#从未发布且现在仍空
            if 已有 is None:#不要发空的首次目录
                return 决策#保持
            过滤后=[]#去掉误注入
            已有标识=已有['message']['id']#已有目录消息id
            for 消息 in 取出决策消息(决策):#过滤
                if 消息['id']!=已有标识:#不是误注入目录
                    过滤后.append(消息)#保留
            return {'kind':'enter','messages':过滤后}#去掉误注入
        if 'published' in 历史 and 历史['published'] is True:#已发布过则走替换文案
            目录=渲染目录更新(条目列表)#替换目录
        else:#首次目录
            目录=渲染目录消息(条目列表)#首次目录
        if 已有 is None:#本步还没有目录消息
            return {'kind':'enter','messages':取出决策消息(决策)+[目录]}#追加
        替换后=[]#按id替换
        已有标识=已有['message']['id']#已有目录消息id
        for 消息 in 取出决策消息(决策):#扫描
            if 消息['id']==已有标识:#就是这份
                替换后.append(目录)#换成新目录
            else:#其它消息
                替换后.append(消息)#原样
        return {'kind':'enter','messages':替换后}#按id替换
    上下文.监听('agent/pre-step',目录监听)#目录监听器

name=名称#Cordis 插件名槽
inject=注入#Cordis 依赖槽
Config=配置#Cordis 配置槽
apply=应用#Cordis 入口槽
default=应用#Cordis 默认导出槽
