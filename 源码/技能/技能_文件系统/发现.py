"""本地技能根发现与技能文件解析。"""
import os,re,stat#路径、正则与文件状态
import yaml#外部依赖胶水（PyYAML）
from ...工具.工作区路径 import (#共用家目录与监视路径，禁止本包内联假实现
    规范化监视路径,#监视路径规范化
    解析主目录,#解析 dsh 家目录
    有错误码,#ENOENT/ENOTDIR 判定
    主目录名,#默认 .dsh 名
    主目录环境键,#DSH_HOME
)#工作区路径权威实现

技能名正则=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')#公开技能名：kebab-case
捆绑技能排名=600#打包技能提供方与本地捆绑根的标准优先排名
项目dsh排名=100#项目 .dsh/skills 排名
项目agents排名=200#项目 .agents/skills 排名
自定义排名=300#自定义根排名
用户dsh排名=400#用户 .dsh/skills 排名
用户agents排名=500#用户 .agents/skills 排名
解析dsh家目录=解析主目录#本包沿用旧名，委托 home_paths

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 试取(对象,键):#读取可选字段
    """读取可选字段，缺席为 None。"""
    return 取字段(对象,键,None)#缺席为空

def 有自有(对象,键):#对齐 Object.hasOwn
    """对齐 Object.hasOwn。"""
    if 对象 is None:#空对象
        return False#没有
    if isinstance(对象,dict):#映射
        return 键 in 对象#映射键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:#没有字典
        return False#没有
    return 键 in 字典#自有

def 已中止(信号):#信号是否已中止
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    if getattr(信号,'aborted',False):#英文旗标
        return True#已中止
    if getattr(信号,'已中止',False):#中文旗标
        return True#已中止
    return False#未中止

def 中止原因(信号):#取出中止原因
    """取出中止原因。"""
    if 信号 is None:#无信号
        return None#无原因
    原因=getattr(信号,'reason',None)#英文原因
    if 原因 is not None:#有英文原因
        return 原因#英文原因
    return getattr(信号,'原因',None)#中文原因

def 抛若中止(信号):#已中止则抛出完备错误
    """已中止的查找抛出完备 Error。"""
    if 信号 is None:#无信号
        return#仍活着
    if hasattr(信号,'throwIfAborted'):#英文 API
        信号.throwIfAborted()#已中止则抛
        return#仍活着
    if hasattr(信号,'抛若中止'):#中文 API
        信号.抛若中止()#已中止则抛
        return#仍活着
    if not 已中止(信号):#仍活着
        return#不抛
    原因=中止原因(信号)#中止原因
    if isinstance(原因,BaseException):#已是异常
        raise 原因#原样抛
    错=Exception('aborted')#非异常则包装
    错.cause=原因#挂上原因
    raise 错#抛出

def 听中止(信号,回调):#登记一次性 abort 回调
    """登记一次性 abort 回调。"""
    if 信号 is None:#无信号
        return#不登记
    if hasattr(信号,'addEventListener'):#Web API
        信号.addEventListener('abort',回调,{'once':True})#只听一次
        return#已登记
    if hasattr(信号,'加入监听'):#中文 API
        信号.加入监听('abort',回调,{'once':True})#只听一次

def 是技能名(名称):#校验公开 kebab-case 技能名
    """判断字符串是否为合法 kebab-case 技能名。"""
    return 技能名正则.fullmatch(名称) is not None#匹配公开文法

def 错误消息(错误):#任意失败→消息
    """任意失败渲染成消息。"""
    return str(错误)#常规渲染

def 是否缺失路径错误(错误):#路径不存在或不是目录
    """路径不存在或不是目录。"""
    return 有错误码(错误,'ENOENT') or 有错误码(错误,'ENOTDIR')#Node 缺失码

def 是否缺失技能路径错误(错误):#技能路径缺失（含 fs 服务码）
    """技能路径缺失（含 fs 服务码）。"""
    if 是否缺失路径错误(错误):#Node 缺失
        return True#缺失
    if 有错误码(错误,'FS_NOT_FOUND'):#fs 服务未找到
        return True#缺失
    if 有错误码(错误,'FS_NOT_DIRECTORY'):#fs 服务非目录
        return True#缺失
    return False#其它错误

def 断言正整数(字段,数值):#配置正整数断言
    """配置正整数断言，加载时大声失败。"""
    是整数=isinstance(数值,int) and not isinstance(数值,bool)#排除布尔
    if isinstance(数值,float) and 数值.is_integer() and not isinstance(数值,bool):#整值浮点
        是整数=True#当作整数
    if (not 是整数) or 数值<1:#非正整数
        raise TypeError('skill-filesystem: '+字段+' must be a positive integer')#加载时大声失败

def 变更工具名(行动者):#第一方变更工具名
    """只认 edit/write 第一方变更工具。"""
    if 行动者 is None:#无 actor
        return None#不认
    if isinstance(行动者,dict):#映射
        if 'name' not in 行动者:#无名
            return None#不认
        名称=行动者['name']#工具名
    else:#对象
        if not hasattr(行动者,'name'):#无名
            return None#不认
        名称=行动者.name#工具名
    if 名称=='edit' or 名称=='write':#只认 edit/write
        return 名称#工具名
    return None#其它工具不认

def 可选文件系统(上下文):#上下文上可选的 fs 服务
    """上下文上可选的 fs 服务。"""
    反射=getattr(上下文,'reflect',None)#反射层
    if 反射 is not None and hasattr(反射,'获取服务'):#有获取服务
        return 反射.获取服务('fs',False)#宽松读取，没有则 None
    if hasattr(上下文,'获取服务'):#上下文获取服务
        return 上下文.获取服务('fs',False)#宽松读取
    if hasattr(上下文,'get'):#英文 get
        return 上下文.get('fs',False)#宽松读取
    return None#没有反射

def 读技能文本(上下文,路径,信号=None,信任宿主=False):#读技能文本
    """读技能文本：非信任根走策略 fs，否则宿主直读。"""
    抛若中止(信号)#入口查取消
    文件系统服务=可选文件系统(上下文)#可选 fs 服务
    if 文件系统服务 is not None and (not 信任宿主):#非信任根走策略 fs
        return 经文件系统读技能文本(上下文,文件系统服务,路径,信号)#经 fs 服务读
    try:#宿主直读
        抛若中止(信号)#读前再查取消
        with open(路径,'r',encoding='utf-8') as 文件:#Node 读文件
            return 文件.read()#UTF-8 文本
    except Exception as 错误:#读失败
        抛若中止(信号)#取消优先
        if 是否缺失技能路径错误(错误):#缺失则没有
            return None#没有此技能
        raise 错误#其它错误上抛

def 经文件系统读技能文本(上下文,文件系统服务,路径,信号=None):#经 fs 服务读文本
    """经 fs 服务解析、stat 并读 UTF-8 文本。"""
    抛若中止(信号)#入口查取消
    try:#解析失败可能是缺失
        目标=文件系统服务.解析(路径)#策略解析
    except Exception as 错误:#解析失败
        if 是否缺失技能路径错误(错误):#缺失则没有
            return None#没有
        raise 错误#其它错误上抛
    抛若中止(信号)#解析后再查取消
    try:#stat 失败可能是缺失
        信息=文件系统服务.状态(目标,信号)#取类型
    except Exception as 错误:#stat 失败
        抛若中止(信号)#取消优先
        if 是否缺失技能路径错误(错误):#缺失则没有
            return None#没有
        raise 错误#其它错误上抛
    if 信息 is None:#不存在
        return None#没有
    if 取字段(信息,'type')!='file':#非文件则没有
        return None#没有
    try:#读文本失败可能是非文本
        return 文件系统服务.读文本(目标,信号)#读 UTF-8
    except Exception as 错误:#读失败
        抛若中止(信号)#取消优先
        if 是否缺失技能路径错误(错误):#缺失则没有
            return None#没有
        if not 有错误码(错误,'FS_NOT_TEXT'):#非“不是文本”则上抛
            raise 错误#其它错误
        上下文.logger.warn('skill file '+路径+' ignored: '+文件系统读错误消息(目标,错误))#记非文本
        return None#忽略

def 文件系统读错误消息(目标,错误):#fs 读失败消息
    """fs 读失败消息。"""
    return 'failed to read text file at '+str(取字段(目标,'displayPath'))+': '+错误消息(错误)#展示路径 + 原因

def 找结束frontmatter(原文,起点):#找结束 --- 行
    """找结束 --- 行。"""
    行起点=起点#当前行起点
    while 行起点<=len(原文):#扫到文末
        下一换行=原文.find('\n',行起点)#下一换行
        行结束=len(原文) if 下一换行<0 else 下一换行#行结束
        行=原文[行起点:行结束]#当前行含可能的 CR
        if 行.endswith('\r'):#去掉行尾 CR
            行=行[:-1]#去掉 CR
        if 行=='---':#结束标记
            正文起点=len(原文) if 下一换行<0 else 下一换行+1#正文起点
            return {'start':行起点,'bodyStart':正文起点}#标记起点与正文起点
        if 下一换行<0:#文末仍未闭合
            return None#未闭合
        行起点=下一换行+1#下一行
    return None#未找到

def 解析frontmatter(原文):#拆 YAML frontmatter
    """拆 YAML frontmatter。"""
    第一行结束=原文.find('\n')#第一行结束
    if 第一行结束<0:#单行无 frontmatter
        return None#没有
    第一行=原文[0:第一行结束]#第一行含可能的 CR
    if 第一行.endswith('\r'):#去掉行尾 CR
        第一行=第一行[:-1]#去掉 CR
    if 第一行!='---':#必须以 --- 起
        return None#没有
    起点=第一行结束+1#YAML 起点
    闭合=找结束frontmatter(原文,起点)#找结束 ---
    if 闭合 is None:#未闭合
        return None#没有
    yaml文本=原文[起点:闭合['start']]#YAML 文本
    解析结果=yaml.safe_load(yaml文本)#解析
    if not isinstance(解析结果,dict):#必须是对象
        return None#数组/标量/空非法
    return {'data':解析结果,'body':原文[闭合['bodyStart']:]}#数据 + 正文

def 字符串字段(数据,键):#非空字符串字段
    """非空字符串字段，空串当缺失。"""
    字段值=数据.get(键)#取值
    if isinstance(字段值,str) and len(字段值)>0:#非空字符串
        return 字段值#收下
    return None#缺或空

def 可选字符串(数据,键):#可选非空字符串，缺则空对象
    """可选非空字符串，缺则空对象以便展开。"""
    字段值=数据.get(键)#取值
    if isinstance(字段值,str) and len(字段值)>0:#非空字符串
        return {键:字段值}#便于展开
    return {}#不展开

def 拒绝旧调用键(数据,旧键,规范键):#拒绝旧键名
    """拒绝旧驼峰调用键。"""
    if 有自有(数据,旧键):#出现旧键
        raise Exception('frontmatter field "'+旧键+'" is unsupported; use "'+规范键+'"')#指向规范键

def frontmatter布尔(数据,键):#frontmatter 布尔，缺则 None
    """frontmatter 布尔；缺席为 None，非法则抛错。"""
    if not 有自有(数据,键):#键不存在
        return None#缺席
    字段值=数据[键]#取值
    if isinstance(字段值,bool):#真布尔
        return 字段值#收下
    if 字段值==1 or 字段值=='1':#1 / '1'
        return True#为真
    if 字段值==0 or 字段值=='0':#0 / '0'
        return False#为假
    if isinstance(字段值,str):#大小写不敏感的词
        规范=字段值.lower()#规范化后再比
        if 规范=='true' or 规范=='yes' or 规范=='on':#真词
            return True#为真
        if 规范=='false' or 规范=='no' or 规范=='off':#假词
            return False#为假
    raise TypeError('frontmatter field "'+键+'" must be a boolean')#其它类型非法

def 解析调用策略(数据):#从 frontmatter 解析调用策略
    """从 frontmatter 解析调用策略。"""
    拒绝旧调用键(数据,'disableModelInvocation','disable-model-invocation')#拒绝旧驼峰键
    拒绝旧调用键(数据,'modelInvocable','disable-model-invocation')#拒绝新驼峰键
    拒绝旧调用键(数据,'userInvocable','user-invocable')#拒绝驼峰用户键
    禁用模型调用=frontmatter布尔(数据,'disable-model-invocation')#禁用模型调用
    用户可调用=frontmatter布尔(数据,'user-invocable')#用户可调用
    return {'modelInvocable':禁用模型调用!=True,'userInvocable':用户可调用!=False}#默认两面都允许

def 可选元数据(数据):#可选 metadata 对象
    """可选 metadata 对象；缺或非法则不展开。"""
    字段值=数据.get('metadata')#取值
    if isinstance(字段值,dict):#普通对象
        return {'metadata':字段值}#收下
    return {}#缺或非法则不展开

def 解析技能文件(路径,上下文,信号=None,信任宿主=False):#读并解析技能文件
    """读并解析技能文件；缺失或非法则 None。"""
    原文=读技能文本(上下文,路径,信号,信任宿主)#读文本
    抛若中止(信号)#读后再查取消
    if 原文 is None:#缺失
        return None#当作没有此技能
    try:#非法 YAML 则忽略文件
        解析结果=解析frontmatter(原文)#拆 --- 块
    except Exception as 错误:#YAML 抛错
        上下文.logger.warn('skill file '+路径+' ignored: invalid YAML frontmatter: '+错误消息(错误))#记非法 YAML
        return None#忽略
    if not 解析结果:#缺 frontmatter
        上下文.logger.warn('skill file '+路径+' ignored: missing YAML frontmatter')#记缺失
        return None#忽略
    名称=字符串字段(解析结果['data'],'name')#必填名
    描述=字符串字段(解析结果['data'],'description')#必填描述
    if 名称 is None or 描述 is None:#缺字段
        上下文.logger.warn('skill file '+路径+' ignored: frontmatter requires name and description')#记缺字段
        return None#忽略
    if not 是技能名(名称):#名不合法
        上下文.logger.warn('skill file '+路径+' ignored: invalid skill name "'+名称+'"')#记非法名
        return None#忽略
    try:#非法 invocation 则忽略文件
        调用=解析调用策略(解析结果['data'])#解析禁用/用户可调用
    except Exception as 错误:#策略非法
        上下文.logger.warn('skill file '+路径+' ignored: invalid invocation frontmatter: '+错误消息(错误))#记非法策略
        return None#忽略
    结果={'name':名称,'description':描述,'invocation':调用,'content':解析结果['body'].strip()}#解析成功
    结果.update(可选字符串(解析结果['data'],'whenToUse'))#可选何时使用
    结果.update(可选元数据(解析结果['data']))#可选元数据对象
    return 结果#解析结果

def 节点条目种类(完整路径,是目录,是文件,是符号链接,上下文):#Dirent→种类，跟随符号链接
    """Dirent→种类，跟随符号链接。"""
    if 是目录:#目录
        return 'directory'#目录
    if 是文件:#普通文件
        return 'file'#普通文件
    if not 是符号链接:#非符号链接的特殊文件
        return None#跳过
    try:#跟随符号链接
        信息=os.stat(完整路径)#跟随后的 stat
        if stat.S_ISDIR(信息.st_mode):#链接到目录
            return 'directory'#目录
        if stat.S_ISREG(信息.st_mode):#链接到文件
            return 'file'#文件
        return None#链接到特殊文件
    except Exception as 错误:#跟随失败
        上下文.logger.warn('skill entry '+完整路径+' ignored: failed to follow symbolic link: '+错误消息(错误))#记失败
        return None#跳过

def 经节点列技能根条目(根,上下文):#经宿主列目录
    """经宿主列目录。"""
    try:#缺失则空列表
        扫描=os.scandir(根['path'])#带类型读取
    except Exception as 错误:#列目录失败
        if 是否缺失技能路径错误(错误):#根不存在
            return []#无技能
        raise 错误#其它错误上抛
    结果=[]#映射结果
    for 条目 in 扫描:#逐条判定种类
        路径=os.path.join(根['path'],条目.name)#绝对路径
        种类=节点条目种类(路径,条目.is_dir(follow_symlinks=False),条目.is_file(follow_symlinks=False),条目.is_symlink(),上下文)#跟随符号链接
        结果.append({'name':条目.name,'type':种类 if 种类 is not None else 'other','path':路径})#未知种类标 other
    return 结果#根条目

def 经文件系统列技能根条目(根,文件系统服务):#经 fs 服务列目录
    """经 fs 服务列目录。"""
    try:#缺失则空列表
        目标=文件系统服务.解析(根['path'])#策略解析
        条目们=文件系统服务.列目录(目标)#列目录
    except Exception as 错误:#列目录失败
        if 是否缺失技能路径错误(错误):#根不存在则无技能
            return []#空列表
        raise 错误#其它错误上抛
    结果=[]#映射结果
    for 条目 in 条目们:#逐条
        目标对象=取字段(条目,'target')#子目标
        结果.append({'name':取字段(条目,'name'),'type':取字段(条目,'type'),'path':取字段(目标对象,'displayPath')})#用展示路径
    return 结果#根条目

def 列技能根条目(根,上下文):#列根：fs 服务或宿主
    """列根：非信任根走策略 fs，否则宿主。"""
    文件系统服务=可选文件系统(上下文)#可选文件系统服务
    if 文件系统服务 is not None and 根.get('trustedHost')!=True:#非信任根走策略 fs
        return 经文件系统列技能根条目(根,文件系统服务)#经 fs
    return 经节点列技能根条目(根,上下文)#捆绑/无 fs 走宿主

def 按名(条目):#排序键
    """按条目名排序。"""
    return 条目['name']#名称

def 发现根(根,上下文,提供方名):#扫描一个技能根
    """扫描一个技能根，返回候选列表。"""
    技能们=[]#本根候选
    条目们=列技能根条目(根,上下文)#列出根下条目
    条目们=sorted(条目们,key=按名)#按名排序后稳定枚举
    for 条目 in 条目们:#逐条
        if 根.get('skipSystem') and 条目['name']=='.system':#用户 dsh 跳过 .system
            continue#跳过
        if 条目['type']=='directory':#目录包
            定位器={'path':os.path.join(条目['path'],'SKILL.md'),'directory':条目['path']}#SKILL.md + 包目录
        elif 条目['type']=='file' and 条目['name'].endswith('.md'):#扁平 md
            定位器={'path':条目['path'],'directory':根['path']}#文件 + 根作基目录
        else:#其它条目忽略
            continue#非技能布局
        解析结果=解析技能文件(定位器['path'],上下文,None,根.get('trustedHost')==True)#捆绑根走宿主直读
        if 解析结果 is None:#缺失或非法 frontmatter
            continue#跳过
        候选={'name':解析结果['name'],'description':解析结果['description'],'invocation':解析结果['invocation'],'provider':提供方名,'source':根['source'],'rank':根['rank'],'locator':定位器,'resourceBase':{'kind':'directory','path':定位器['directory']},'path':定位器['path']}#组装候选
        if 'whenToUse' in 解析结果:#可选何时使用
            候选['whenToUse']=解析结果['whenToUse']#何时使用
        if 'metadata' in 解析结果:#可选元数据
            候选['metadata']=解析结果['metadata']#元数据
        技能们.append(候选)#收入候选
    return 技能们#本根候选

def 经文件系统路径存在(路径,文件系统服务):#经 fs 服务探测存在
    """经 fs 服务探测存在。"""
    try:#后端可能拒绝或隐藏此候选
        目标=文件系统服务.解析(路径)#策略解析
    except Exception:#解析失败
        return False#当不存在
    try:#stat 瞬时失败只让这个 git 根候选不可用
        return 文件系统服务.状态(目标) is not None#有 stat 即存在
    except Exception:#stat 失败
        return False#当不存在

def 经节点路径存在(路径):#经宿主探测存在
    """经宿主 access 探测存在。"""
    try:#缺失是向上走时期待的
        os.stat(路径)#探测可访问
        return True#存在
    except Exception:#不可访问
        return False#当不存在

def 路径存在(路径,文件系统服务):#路径是否存在
    """路径是否存在。"""
    if 文件系统服务 is not None:#有 fs 服务
        return 经文件系统路径存在(路径,文件系统服务)#走策略 fs
    return 经节点路径存在(路径)#走宿主

def 查找项目根(工作目录,文件系统服务):#向上找含 .git 的目录
    """向上找含 .git 的目录；没有则退回 cwd。"""
    当前=工作目录#从 cwd 开始
    while True:#直到文件系统根
        if 路径存在(os.path.join(当前,'.git'),文件系统服务):#找到 .git
            return 当前#项目根
        父路径=os.path.dirname(当前)#上一层
        if 父路径==当前:#没有 .git 则退回 cwd
            return 工作目录#回退
        当前=父路径#继续向上
