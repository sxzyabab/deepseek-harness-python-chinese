"""持久会话技能目录与面向模型的 skill 加载工具。"""
import hashlib#目录条目摘要用 SHA-256
import json#目录条目规范 JSON 编码
import re#技能手势正则与空白压缩
from schemastery import 模式#导入配置模式
from tools import 定义工具#定义面向模型的工具
from llm import 创建用户消息#构造用户消息
from skill import (#技能 seam 公开符号
    转义文本,#转义目录描述
    是否模型可调用,#模型面是否可调用
    是否技能名,#公开技能名文法
    是否用户可调用,#用户面是否可调用
    渲染技能内容,#规范技能块
)#技能 seam 导入结束
from cordis.工具 import 是否thenable#可等待判定

名称='tool-skill'#Cordis插件名
注入=['agents','tools','skills']#依赖智能体、工具与技能服务
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
目录描述默认最大长度=500#目录描述默认最大长度
摘要算法=hashlib.sha256#SHA-256摘要
编码=json.dumps#JSON编码
编译正则=re.compile#编译正则
替换正则=re.sub#正则替换
查找全部=re.finditer#全局正则匹配
技能手势=编译正则(r'(^|\s)/([a-z0-9]+(?:-[a-z0-9]+)*)(?=\s|$)')#用户显式/name手势
配置=模式.对象({#面向模型的技能目录配置
    'catalogDescriptionMaxLength':模式.数字().默认(目录描述默认最大长度),#默认500
})#配置模式结束
Config=配置#Cordis配置模式

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
    return 值#同步值

def 是否整数(值):#对齐JS Number.isInteger
    """对齐 JS Number.isInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return True#整数
    if isinstance(值,float):#浮点
        return 值.is_integer()#整值浮点
    return False#其它类型

def 已中止(信号):#信号是否已中止
    """英文 aborted 或中文 已中止 任一为真则视为已中止。"""
    if 信号 is None:#无信号
        return False#无信号
    if getattr(信号,'aborted',False):#英文旗标
        return True#英文旗标
    if getattr(信号,'已中止',False):#中文旗标
        return True#中文旗标
    return False#未中止

def 中止原因(信号):#取出中止原因
    """取出中止原因。"""
    if 信号 is None:#无信号
        return None#无信号
    原因=getattr(信号,'reason',None)#英文原因
    if 原因 is not None:#有英文原因
        return 原因#英文原因
    return getattr(信号,'原因',None)#中文原因

def 抛若中止(信号):#已中止则抛出原因
    """已中止则抛出原因。"""
    if 信号 is None:#无信号
        return#无信号
    if hasattr(信号,'throwIfAborted'):#英文API
        信号.throwIfAborted()#英文API
        return#已抛或仍活
    if hasattr(信号,'抛若中止'):#中文API
        信号.抛若中止()#中文API
        return#已抛或仍活
    if not 已中止(信号):#仍活着
        return#仍活着
    原因=中止原因(信号)#中止原因
    if isinstance(原因,BaseException):#已是异常
        raise 原因#原样抛
    错=Exception('aborted')#非异常则包装
    错.cause=原因#挂上原因
    raise 错#抛出

def 浅拷贝基址(基址):#浅拷贝资源基址
    """浅拷贝提供方给出的资源基址记录。"""
    if isinstance(基址,dict):#映射
        return dict(基址)#浅拷贝
    拷贝={}#目标记录
    种类=取字段(基址,'kind')#基址种类
    if 种类 is not None:#有种类
        拷贝['kind']=种类#写入种类
    路径=取字段(基址,'path')#目录路径
    if 路径 is not None:#有路径
        拷贝['path']=路径#写入路径
    网址=取字段(基址,'url')#基URL
    if 网址 is not None:#有网址
        拷贝['url']=网址#写入网址
    描述=取字段(基址,'description')#不透明描述
    if 描述 is not None:#有描述
        拷贝['description']=描述#写入描述
    return 拷贝#浅拷贝结果

def 查找选项(智能体,信号):#构造技能查找选项
    """按智能体会话工作目录、取消信号与观察作用域构造查找选项。"""
    return {#查找上下文
        'cwd':取字段(取字段(取字段(智能体,'session'),'header'),'cwd'),#工作区根
        'signal':信号,#取消信号
        'scope':智能体,#观察作用域
    }#查找选项结束

def 目录源条目(技能们,描述最大长度):#摘要转目录源条目
    """与渲染出的目录行镜像的持久条目列表，供非模型消费方使用。"""
    结果=[]#源条目
    for 技能 in 技能们:#逐条投影
        结果.append({#一条目录源条目
            'name':取字段(技能,'name'),#技能名
            'description':目录描述(取字段(技能,'description'),描述最大长度),#规范化截断描述
        })#一条结束
    return 结果#源条目

def 断言正整数(名,值,下限=1):#配置正整数断言
    """配置正整数断言，非法则在加载时大声失败。"""
    if (not 是否整数(值)) or 值<下限:#非整数或低于下限
        raise Exception('tool-skill: '+名+' must be an integer greater than or equal to '+str(下限))#加载时大声失败

def 目录描述(值,最大长度):#压缩空白并截断
    """规范化、长度受限的描述，恰好是目录发布它的样子（未转义）。"""
    规范化=替换正则(r'\s+',' ',值).strip()#空白压成单空格
    if len(规范化)<=最大长度:#未超上限
        return 规范化#原文
    return 规范化[0:最大长度-3]+'...'#超长加省略号

def 渲染目录条目(条目们):#条目转模型行
    """面向模型的目录行，从源所记录的同一批条目投影。伪 XML 转义属于此框架，不属于已发布事实，因此在此施加且永不存储。名称已经技能名文法校验，不含可转义字符。"""
    行们=[]#模型行
    for 条目 in 条目们:#逐条
        行们.append('- `'+取字段(条目,'name')+'`: '+转义文本(取字段(条目,'description')))#反引号名加转义描述
    return 行们#模型行

def 摘要目录条目(条目们):#条目列表转摘要
    """目录身份基于持久条目列表，而不是渲染出的散文。变的是条目；周围的 system-reminder 框架是写给模型的，不得决定是否需要重新发布。"""
    片段们=[]#规范片段
    for 条目 in 条目们:#逐条JSON而不是分隔符
        片段们.append(编码([取字段(条目,'name'),取字段(条目,'description')],separators=(',',':'),ensure_ascii=False))#加引号才能让边界精确
    规范='\n'.join(片段们)#规范文本
    return 摘要算法(规范.encode('utf-8')).hexdigest()#十六进制摘要

def 读取目录条目(来源):#宽松读取目录条目
    """一条持久目录消息的条目，记录不可用则 None。会话事件可能是恢复、分叉或外部写入的种子，种子校验只保证来源对象带非空 kind；不可读记录被当作不是本插件的目录，而不是在步进监听器里抛错。"""
    条目们=取字段(来源,'entries')#可能缺失
    if not isinstance(条目们,(list,tuple)):#不是数组则不是本目录
        return None#不是本目录
    可读=[]#可读条目
    for 条目 in 条目们:#逐条校验
        if 条目 is None:#空条目
            return None#非整表可读则放弃
        if isinstance(条目,(str,bytes,int,float,bool)):#原语不是条目
            return None#非整表可读则放弃
        名=取字段(条目,'name')#技能名
        描述=取字段(条目,'description')#描述
        if (not isinstance(名,str)) or 名=='' or (not isinstance(描述,str)):#名非空、描述为字符串
            return None#非整表可读则放弃
        可读.append({'name':名,'description':描述})#收下
    return 可读#整表可读

def 目录历史(智能体):#会话目录历史
    """从近到远扫描会话事件，返回最近可见目录摘要以及是否曾发布过可读目录。"""
    表面=取字段(取字段(智能体,'session'),'surface')#会话表面
    节点=取字段(表面,'nodes')#当前表面可见的序号
    可见=set(节点 if 节点 is not None else [])#可见序号集合
    事件们=取字段(取字段(智能体,'session'),'events')#事件流
    if 事件们 is None:#没有事件流
        事件们=[]#空流
    曾发布=False#是否曾发布过
    下标=len(事件们)-1#从近到远
    while 下标>=0:#扫描
        事件=事件们[下标]#下标在范围内
        下标-=1#前进
        if 取字段(事件,'type')!='user/message':#非用户消息
            continue#跳过
        if 取字段(取字段(取字段(事件,'data'),'source'),'kind')!='skill-catalog':#非目录消息
            continue#跳过
        条目们=读取目录条目(取字段(取字段(事件,'data'),'source'))#宽松读条目
        if 条目们 is None:#不可读则跳过
            continue#跳过
        摘要=摘要目录条目(条目们)#该条目录身份
        曾发布=True#至少发布过一次
        if 取字段(事件,'seq') in 可见:#最近可见的那份
            return {'visibleDigest':摘要,'published':曾发布}#可见摘要
    return {'published':曾发布}#没有可见目录，但可能曾发布过

def 目录消息(消息们):#本步消息里的目录注入
    """扫描本步消息，返回第一份可读技能目录及其条目。"""
    if 消息们 is None:#没有消息
        return None#本步没有
    for 消息 in 消息们:#扫描本步
        if 取字段(取字段(消息,'source'),'kind')!='skill-catalog':#非目录
            continue#跳过
        条目们=读取目录条目(取字段(消息,'source'))#宽松读
        if 条目们 is not None:#第一份可读目录
            return {'message':消息,'entries':条目们}#带回条目
    return None#本步没有

def 已调用技能名(消息们):#提取/name手势
    """从声称用户消息中取出 /name 手势词元，按首次出现去重。扫描直接用户输入的每一个文本块；其它来源不能伪造手势。"""
    名称们=[]#首次出现序
    if 消息们 is None:#没有消息
        return 名称们#空
    for 消息 in 消息们:#扫描声称批次
        if 取字段(取字段(消息,'source'),'kind')!='user':#只认用户来源
            continue#跳过
        内容=取字段(消息,'content')#内容块
        if 内容 is None:#没有内容
            continue#跳过
        for 块 in 内容:#每个内容块
            if 取字段(块,'type')!='text':#只扫文本
                continue#跳过
            文本=取字段(块,'text')#文本
            if not isinstance(文本,str):#非字符串
                continue#跳过
            for 匹配 in 查找全部(技能手势,文本):#全局手势
                名=匹配.group(2)#捕获的技能名
                if 名 is not None and 名 not in 名称们:#首次出现才收
                    名称们.append(名)#收下
    return 名称们#去重后的名

def 渲染目录消息(条目们):#首次发布目录
    """构造首次发布的 catalog 形态用户消息。"""
    行们=[#面向模型的框架（字面量不翻译）
        '<system-reminder>',#系统提醒开
        'A skill is a reusable set of task-specific instructions. The following skills are available in this session:',#技能说明
        '',#空行
        '<available_skills>',#可用技能开
    ]#框架前半
    行们.extend(渲染目录条目(条目们))#条目行
    行们.extend([#框架后半
        '</available_skills>',#可用技能闭
        '',#空行
        "If the user names a skill, or the task clearly matches a skill's description, call the `skill` tool with the exact skill name before taking task actions. Load all applicable skills, then follow their full instructions. This catalog contains summaries only; do not infer or follow a skill's instructions until it has been loaded.",#调用指引
        'A user may also invoke a skill directly; its <skill_content> block then appears in this conversation. Follow it, and do not call the `skill` tool again for that skill.',#用户直调说明
        '</system-reminder>',#系统提醒闭
    ])#框架后半结束
    return 创建用户消息({#构造catalog形态用户消息
        'content':[{#单一文本块
            'type':'text',#文本
            'text':'\n'.join(行们),#按行拼接
        }],#内容结束
        'source':{#持久目录源
            'kind':'skill-catalog',#来源标签
            'form':'catalog',#目录形态
            'entries':条目们,#恰好这些条目
        },#来源结束
    })#创建结束

def 渲染目录更新(条目们):#替换已发布目录
    """构造带 update 标记的替换目录用户消息。"""
    if len(条目们)==0:#空替换与非空替换文案不同
        可用性=[#清空
            'No skills are currently available through the `skill` tool. Do not use names from earlier skill catalogs.',#不要用旧名
            'A user may still invoke a skill directly; its <skill_content> block then appears in this conversation. Follow it, and do not call the `skill` tool for it.',#用户仍可直调
        ]#清空文案结束
    else:#非空替换
        可用性=[#非空替换
            'Use only names in this replacement catalog. If the user names a listed skill, or the task clearly matches its description, call the `skill` tool with the exact name before acting.',#只用新目录
            'A user may also invoke a skill directly; its <skill_content> block then appears in this conversation. Follow it, and do not call the `skill` tool again for that skill.',#用户直调说明
        ]#非空文案结束
    行们=[#替换框架（字面量不翻译）
        '<system-reminder>',#系统提醒开
        'The available skill catalog changed. This complete catalog replaces every earlier available-skills list in this session:',#整表替换
        '',#空行
        '<available_skills>',#可用技能开
    ]#框架前半
    行们.extend(渲染目录条目(条目们))#条目行
    行们.extend(['</available_skills>','']+可用性+['</system-reminder>'])#闭标签与指引
    return 创建用户消息({#带update的目录消息
        'content':[{#单一文本块
            'type':'text',#文本
            'text':'\n'.join(行们),#按行拼接
        }],#内容结束
        'source':{#持久替换源
            'kind':'skill-catalog',#来源标签
            'form':'catalog',#目录形态
            'update':True,#标记替换
            'entries':条目们,#恰好这些条目
        },#来源结束
    })#创建结束

def 应用(上下文,配置值=None):#注册工具与两处pre-step
    """注册面向模型的技能加载器及其与可见性匹配的持久会话目录。仅当调用方智能体解析到本插件恰好这次工具注册时才发出目录；限制或同名作用域遮蔽因此会同时去掉模式与其调用指引。"""
    if 配置值 is None:#缺省空配置
        配置值={}#空配置
    目录描述最大长度=取字段(配置值,'catalogDescriptionMaxLength')#解析上限
    if 目录描述最大长度 is None:#未给出
        目录描述最大长度=目录描述默认最大长度#默认500
    断言正整数('catalogDescriptionMaxLength',目录描述最大长度,3)#最小3，为省略号留位置
    def 渲染(参数,值):#模型看到规范技能块
        """把结构化技能结果渲染成规范 skill_content 文本块。"""
        return [{'type':'text','text':渲染技能内容(值)}]#单个文本块
    def 执行(参数,执行上下文):#加载技能正文
        """按精确技能名加载模型可调用技能正文。"""
        名=取字段(参数,'name')#技能名参数
        if not 是否技能名(名):#名不合法
            raise Exception('invalid skill name "'+str(名)+'"')#非法名
        智能体=取字段(执行上下文,'agent')#调用方智能体
        查找=查找选项(智能体,取字段(执行上下文,'signal'))#cwd加取消加观察作用域
        摘要=None#目录里的摘要
        for 项 in 解开(上下文.skills.列出(查找)):#先在目录里找
            if 取字段(项,'name')==名:#名称匹配
                摘要=项#记下
                break#已找到
        if 摘要 is None:#目录没有
            raise Exception('skill "'+名+'" is unknown or no longer available')#未知或已消失
        if not 是否模型可调用(摘要):#用户专用技能
            raise Exception('skill "'+名+'" is not available for model invocation')#模型不可调用
        技能=解开(上下文.skills.获取(名,查找))#加载正文
        if 技能 is None:#加载后消失
            raise Exception('skill "'+名+'" is unknown or no longer available')#未知或已消失
        if not 是否模型可调用(技能):#定义上不可调用
            raise Exception('skill "'+名+'" is not available for model invocation')#模型不可调用
        结果={#结构化结果
            'name':取字段(技能,'name'),#技能名
            'provider':取字段(技能,'provider'),#提供方
            'content':取字段(技能,'content'),#正文
        }#结果字段
        基址=取字段(技能,'resourceBase')#可选资源基址
        if 基址 is not None:#有基址则展开
            结果['resourceBase']=浅拷贝基址(基址)#浅拷贝基址
        return 结果#结构化结果
    def 呈现调用(参数):#UI卡片
        """调用时通用读卡片。"""
        return {#通用读卡片
            'card':'generic',#通用卡片
            'title':'Load skill '+取字段(参数,'name'),#标题
            'kind':'read',#读种类
            'rawInput':取字段(参数,'name'),#原始输入
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
    def 用户调用监听(载荷,下一步,*剩余):#用户显式/name注入
        """用户显式技能调用：声称用户消息里以空白为界的 /name 若是用户可调用技能，则把渲染后的正文作为指令上下文追加在本步其余注入之后。"""
        决策=解开(下一步())#先让后面的含目录跑完
        if 取字段(决策,'kind')=='reject':#拒绝则不注入
            return 决策#原样返回
        名称们=已调用技能名(取字段(载荷,'messages'))#声称用户消息里的/name
        if len(名称们)==0:#无手势
            return 决策#保持
        信号=取字段(载荷,'signal')#取消信号
        抛若中止(信号)#注入前查取消
        智能体=取字段(载荷,'agent')#本步智能体
        查找=查找选项(智能体,信号)#查找上下文
        注入们=[]#待追加的指令消息
        for 名 in 名称们:#按首次出现序
            技能=解开(上下文.skills.获取(名,查找))#加载定义
            抛若中止(信号)#每次加载后查取消
            if 技能 is None or (not 是否用户可调用(技能)):#未知名与用户禁用仍是普通散文
                continue#不认则跳过
            注入们.append(创建用户消息({#构造注入消息
                'content':[{'type':'text','text':渲染技能内容(技能)}],#规范技能块
                'source':{'kind':'skill-invocation','name':名,'form':'instructions'},#注入来源
            }))#push结束
        if len(注入们)==0:#没有可注入的
            return 决策#保持
        消息们=list(取字段(决策,'messages') or [])#本步已有消息
        return {'kind':'enter','messages':消息们+注入们}#目录之后追加指令
    上下文.on('agent/pre-step',用户调用监听)#用户调用监听器
    def 目录监听(载荷,下一步,*剩余):#发布或替换或撤回会话目录
        """在工具之后注册，使反向拆除先去掉指引。恰好这次定义身份防止仅同名 skill 的作用域遮蔽继承本目录。"""
        决策=解开(下一步())#先跑后续监听器
        if 取字段(决策,'kind')=='reject':#拒绝则不动目录
            return 决策#原样返回
        信号=取字段(载荷,'signal')#取消信号
        抛若中止(信号)#快照前查取消
        智能体=取字段(载荷,'agent')#本步智能体
        工具可见=上下文.tools.获取(技能工具['name'],智能体) is 技能工具#恰好是本注册才发目录
        if 工具可见:#工具可见才发现
            快照=解开(上下文.skills.snapshot(查找选项(智能体,信号)))#拍完整快照
        else:#不可见则空且完整
            快照={'skills':[],'complete':True}#用于撤回旧目录
        抛若中止(信号)#快照后查取消
        if not 取字段(快照,'complete'):#不完整发现不发布
            return 决策#保留上次完好
        技能们=[]#只广告模型可调用
        for 项 in (取字段(快照,'skills') or []):#过滤
            if 是否模型可调用(项):#模型可调用
                技能们.append(项)#收下
        条目们=目录源条目(技能们,目录描述最大长度)#持久条目
        摘要=摘要目录条目(条目们)#条目身份
        历史=目录历史(智能体)#会话里上次可见目录
        已有=目录消息(取字段(决策,'messages'))#本步已有的目录消息
        if 取字段(历史,'visibleDigest')==摘要:#表面已是这份目录
            if 已有 is None:#本步没有重复注入
                return 决策#保持
            过滤后=[]#去掉重复注入
            已有标识=取字段(取字段(已有,'message'),'id')#已有目录消息id
            for 消息 in (取字段(决策,'messages') or []):#过滤
                if 取字段(消息,'id')!=已有标识:#不是重复目录
                    过滤后.append(消息)#保留
            return {'kind':'enter','messages':过滤后}#去掉重复注入
        if 已有 is not None and 摘要目录条目(取字段(已有,'entries'))==摘要:#本步注入已是目标
            return 决策#保持
        if (not 取字段(历史,'published')) and len(技能们)==0:#从未发布且现在仍空
            if 已有 is None:#不要发空的首次目录
                return 决策#保持
            过滤后=[]#去掉误注入
            已有标识=取字段(取字段(已有,'message'),'id')#已有目录消息id
            for 消息 in (取字段(决策,'messages') or []):#过滤
                if 取字段(消息,'id')!=已有标识:#不是误注入目录
                    过滤后.append(消息)#保留
            return {'kind':'enter','messages':过滤后}#去掉误注入
        if 取字段(历史,'published'):#已发布过则走替换文案
            目录=渲染目录更新(条目们)#替换目录
        else:#首次目录
            目录=渲染目录消息(条目们)#首次目录
        if 已有 is None:#本步还没有目录消息
            消息们=list(取字段(决策,'messages') or [])#拷贝
            return {'kind':'enter','messages':消息们+[目录]}#追加
        替换后=[]#按id替换
        已有标识=取字段(取字段(已有,'message'),'id')#已有目录消息id
        for 消息 in (取字段(决策,'messages') or []):#扫描
            if 取字段(消息,'id')==已有标识:#就是这份
                替换后.append(目录)#换成新目录
            else:#其它消息
                替换后.append(消息)#原样
        return {'kind':'enter','messages':替换后}#按id替换
    上下文.on('agent/pre-step',目录监听)#目录监听器

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
