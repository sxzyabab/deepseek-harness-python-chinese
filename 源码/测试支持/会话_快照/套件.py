"""默认无密钥的 ACP 快照套件工厂与纯辅助。

对齐上游 `session-snapshot/src/suite.ts`。公开面仅中文名。
vitest 的 describe/it 以可运行用例表替代。
"""
import json,os,re#JSON、文件与正则
from ...内核.会话 import 是否可进表面类型#表面类型判定
from .测试架 import 运行场景#场景 harness
from .清单 import 解析快照清单#清单解析
from .身份 import 脱敏会话快照标识#身份脱敏
from .工作区 import 捕获期望工作区快照#期望工作区
from .归一化 import (#归一化
    提取快照溢出路径,归一化会话日志,归一化会话快照们,归一化标准输出,
    擦除请求头,擦除会话快照,擦除系统提示词,擦除工具模式,令牌化会话夹具工作目录,
)#归一化结束

__all__=[#仅中文公开名
    '场景是否跳过','标准输出期望变体','主张共享快照','断言唯一快照内容','会话夹具名',
    '夹具上下文','归一化请求头','归一化系统提示词','归一化工具模式','格式化工具模式快照',
    '解析工具模式快照','恢复钉住工具模式','格式化系统提示词快照','断言子系统提示词快照',
    '头变更计数','未知工具调用标识','刷新夹具替换','稳定夹具消息标识','稳定刷新日志',
    '定义ACP快照套件',
]#公开面结束

系统提示词快照='system-prompt.expected.md'#系统提示词快照文件名
工具模式快照='tool-schemas.expected.json'#工具 schema 快照文件名
视窗标准输出快照='stdout.expected.windows.jsonl'#Windows stdout 快照
工具令牌='{{tools}}'#工具令牌
打包块行类型=frozenset(['text-chunks','reasoning-chunks','tool-call-chunks'])#打包行类型
UUID模式=re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',re.I)#UUID
Error=Exception#错误别名

def 子工具模式快照(索引):#子工具 schema 文件名
    """返回某一子 fixture 索引的专用工具 schema sidecar。"""
    return f'tool-schemas.{索引}.expected.json'#按索引命名

def 子系统提示词快照(索引):#子系统提示词文件名
    """返回某一子 fixture 索引的专用系统提示词 sidecar。"""
    return f'system-prompt.{索引}.expected.md'#按索引命名

def 断言相等(实际,期望,消息=''):#相等断言
    """vitest expect().toEqual / toBe 替代。"""
    if 实际!=期望:#不等
        raise Error(消息 or f'{实际!r} != {期望!r}')#失败

def 断言真(条件,消息=''):#真断言
    """vitest expect().toBe(true) 替代。"""
    if not 条件:#假
        raise Error(消息 or 'expected true')#失败

def 断言大于(实际,下限,消息=''):#大于断言
    """vitest expect().toBeGreaterThan 替代。"""
    if not (实际>下限):#不大于
        raise Error(消息 or f'{实际!r} !> {下限!r}')#失败

def 读文本(路径):#读 utf-8 文本
    """读取整个文本文件。"""
    with open(路径,'r',encoding='utf-8') as 句柄:#打开
        return 句柄.read()#内容

def 写文本(路径,内容):#写 utf-8 文本
    """写入整个文本文件。"""
    with open(路径,'w',encoding='utf-8',newline='\n') as 句柄:#打开
        句柄.write(内容)#写入

def 场景是否跳过(场景,录制中,平台=None,有Pwsh=None):#场景是否跳过
    """本模式与宿主下场景运行测试是否跳过。"""
    if 平台 is None:#缺省
        平台='win32' if os.name=='nt' else 'posix'#平台
    if 录制中 and not 场景.get('recorded'):#录制跳过手写
        return True#跳过
    if 场景.get('posixOnly') is True and 平台=='win32':#Windows 跳过 POSIX
        return True#跳过
    return 场景.get('pwshOnly') is True and 有Pwsh is not True#无 pwsh 跳过

def 标准输出期望变体(场景,平台=None):#选 stdout 期望变体
    """选择共享 stdout 期望输出加上场景声明的任何平台原生断言。"""
    if 平台 is None:#缺省
        平台='win32' if os.name=='nt' else 'posix'#平台
    规范={'file':'stdout.expected.jsonl','cwdPathMode':'canonical'}#规范变体
    if 平台!='win32' or 场景.get('pinsNativeWindowsStdout') is not True:#仅规范
        return [规范]#仅规范
    return [规范,{'file':视窗标准输出快照,'cwdPathMode':'native'}]#加 Windows 原生

def 主张共享快照(主张表,源,场景,内容):#主张共享快照
    """记录一个场景对共享快照源生成的内容。"""
    先前=主张表.get(源)#先前
    if 先前 is not None and 先前['content']!=内容:#分歧
        raise Error(f"acp-snapshot: shared snapshot {源} diverged between {先前['scenario']} and {场景}")#分歧
    if 先前 is None:#首次
        主张表[源]={'scenario':场景,'content':内容}#登记

def 断言唯一快照内容(种类,快照们):#断言唯一
    """拒绝不同路径下字节相同的已提交快照。"""
    首路径={}#内容→路径
    for 快照 in 快照们:#逐份
        先前=首路径.get(快照['content'])#先前
        if 先前 is not None:#重复
            raise Error(f"acp-snapshot: identical {种类} snapshots appear in {先前} and {快照['path']}; reuse one source")#重复
        首路径[快照['content']]=快照['path']#登记

def 会话夹具名(名称们):#会话 fixture 名
    """校验并排序场景目录的会话 fixture 文件名。"""
    if 'session.jsonl' not in 名称们:#缺主
        raise Error('missing session.jsonl')#缺主
    子们=[]#子
    for 名 in 名称们:#逐名
        if 名=='session.jsonl':#主
            continue#跳过
        if not 名.startswith('session.') or not 名.endswith('.jsonl'):#非会话样
            continue#跳过
        匹配=re.match(r'^session\.([1-9]\d*)\.jsonl$',名)#匹配
        if 匹配 is None:#非法
            raise Error(f'invalid child session fixture name: {名}')#非法
        子们.append({'name':名,'index':int(匹配.group(1))})#追加
    子们.sort(key=lambda 项:项['index'])#排序
    for 偏移,子 in enumerate(子们):#连续
        期望=偏移+1#期望索引
        if 子['index']!=期望:#不连续
            raise Error(f'child session fixtures must be contiguous: expected session.{期望}.jsonl, found {子["name"]}')#不连续
    return ['session.jsonl',*[子['name'] for 子 in 子们]]#返回

def 会话夹具们(目录):#读目录会话 fixture 清单
    """读取一个场景目录已校验的会话 fixture 清单。"""
    名称=[名 for 名 in os.listdir(目录) if os.path.isfile(os.path.join(目录,名))]#文件名
    return 会话夹具名(名称)#校验排序

def 夹具上下文(夹具):#fixture 上下文
    """从 fixture 自有会话头推导归一化值。"""
    首行=next((行 for 行 in 夹具.split('\n') if 行.strip()!=''),'{}')#首行
    头=json.loads(首行)#头
    return {#上下文
        'sessionIds':[头['id']] if isinstance(头.get('id'),str) else [],#会话 id
        'cwd':头['cwd'] if isinstance(头.get('cwd'),str) else '\0no-cwd\0',#cwd
    }#返回

def 是否记录(值):#是否字典
    """非数组对象。"""
    return isinstance(值,dict)#字典

def 归一化头事件(原始日志,上下文):#归一化头事件
    """归一化请求头载荷同时保留原因。"""
    事件=[]#事件
    for 行 in 归一化会话日志(原始日志,上下文).split('\n'):#逐行
        if 行.strip()=='':#空
            continue#跳过
        记录=json.loads(行)#解析
        if 记录.get('type')=='request/header':#请求头
            数据=记录.get('data') or {}#数据
            事件.append({'header':数据.get('header'),'reason':数据.get('reason')})#追加
    return 事件#返回

def 钉住头载荷(原始日志,上下文):#钉住头载荷
    """拥有 sidecar 内容的头修订。"""
    return [事件['header'] for 事件 in 归一化头事件(原始日志,上下文) if 事件['reason']!='series']#过滤 series

def 从头取系统提示词(头们):#从头取系统提示词
    """从归一化头序列提取每个字符串系统提示词。"""
    结果=[]#结果
    for 头 in 头们:#逐头
        if not 是否记录(头):#非对象
            continue#跳过
        系统=头.get('system')#系统
        if isinstance(系统,str):#字符串
            结果.append(系统)#追加
    return 结果#返回

def 从头取工具模式(头们):#从头取工具 schema
    """从归一化头序列提取每个数组值工具目录。"""
    结果=[]#结果
    for 头 in 头们:#逐头
        if not 是否记录(头):#非对象
            continue#跳过
        工具=头.get('tools')#工具
        if isinstance(工具,list):#数组
            结果.append(工具)#追加
    return 结果#返回

def 归一化请求头(原始日志,上下文):#归一化请求头
    """会话 JSONL 中每个 request/header 的 data.header 载荷。"""
    return [事件['header'] for 事件 in 归一化头事件(原始日志,上下文)]#头列表

def 归一化系统提示词(原始日志,上下文):#归一化系统提示词
    """请求头携带的归一化字符串系统提示词。"""
    return 从头取系统提示词(归一化请求头(原始日志,上下文))#提示词

def 归一化工具模式(原始日志,上下文):#归一化工具 schema
    """请求头携带的归一化工具 schema 数组。"""
    return 从头取工具模式(归一化请求头(原始日志,上下文))#schema

def 格式化工具模式快照(初始,变更=None):#格式化工具 schema 快照
    """把完整工具 schema 序列渲染为规范可读 JSON。"""
    if 变更 is None:#缺省
        变更=[]#空
    return json.dumps({'initial':初始,'changes':变更},ensure_ascii=False,indent=2)+'\n'#美化 JSON

def 解析工具模式快照(快照):#解析工具 schema 快照
    """解析并校验工具 schema sidecar。"""
    解析=json.loads(快照)#解析
    if not 是否记录(解析):#非对象
        raise Error('acp-snapshot: tool-schema snapshot must be an object')#非对象
    初始=解析.get('initial')#初始
    变更=解析.get('changes')#变更
    if not isinstance(初始,list) or not isinstance(变更,list) or not all(isinstance(项,list) for 项 in 变更):#非法
        raise Error('acp-snapshot: tool-schema snapshot must carry array-valued initial and changes fields')#非法
    return {'initial':初始,'changes':变更}#返回

def 恢复钉住工具模式(头,模式们):#恢复钉住工具 schema
    """把一个 sidecar schema 集恢复进标记化钉头。"""
    if not 是否记录(头):#非对象
        raise Error('acp-snapshot: pinned request header must be an object')#非对象
    if 头.get('tools')!=工具令牌:#必须令牌
        raise Error(f'acp-snapshot: pinned request header tools must equal {工具令牌}')#令牌
    return {**头,'tools':list(模式们)}#恢复

def 格式化系统提示词快照(提示词,变更=None):#格式化系统提示词快照
    """把归一化提示词渲染为仓库友好的 Markdown 快照。"""
    if 变更 is None:#缺省
        变更=[]#空
    快照=提示词 if 提示词.endswith('\n') else 提示词+'\n'#首段
    for 索引,改 in enumerate(变更):#变更段
        快照+=f'\n<!-- request/header change {索引+1} -->\n\n'#标记
        快照+=改 if 改.endswith('\n') else 改+'\n'#段
    return 快照#返回

def 初始系统提示词快照(快照):#初始提示词部分
    """返回可能多头快照的初始提示词部分。"""
    标记=快照.find('\n<!-- request/header change ')#标记
    return 快照 if 标记<0 else 快照[:标记]#切片

def 断言子系统提示词快照(伴随,类钉,标签):#断言子提示词
    """拒绝无法拥有不同规范提示词文本的子提示词 sidecar。"""
    if 伴随.strip()=='':#空
        raise Error(f'{标签} must pin a non-empty prompt')#空
    if not 伴随.endswith('\n'):#缺换行
        raise Error(f'{标签} must end in a newline')#缺换行
    if 伴随==类钉:#相同
        raise Error(f'{标签} must differ from its class pin')#相同

def 头变更计数(原始日志):#头变更计数
    """统计会话 JSONL 中变更 request/header 快照数。"""
    计数=0#计数
    for 行 in 原始日志.split('\n'):#逐行
        if 行.strip()=='':#空
            continue#跳过
        记录=json.loads(行)#解析
        if 记录.get('type')=='request/header' and (记录.get('data') or {}).get('reason')=='change':#变更
            计数+=1#加一
    return 计数#返回

def 解析JSONL记录(文本):#解析 JSONL 记录
    """解析非空 JSONL 行。"""
    return [json.loads(行) for 行 in 文本.split('\n') if 行.strip()!='']#记录

def 完整消息(值):#完整已识别消息
    """收窄为 fixture 保留的完整已识别消息形状。"""
    if not 是否记录(值):#非对象
        return None#无
    if not isinstance(值.get('id'),str) or not UUID模式.match(值['id']):#id
        return None#无
    if not isinstance(值.get('role'),str) or not isinstance(值.get('content'),list) or not 是否记录(值.get('source')):#形态
        return None#无
    return 值#消息

def 表面事件消息(记录):#表面事件消息
    """返回一个表面事件携带的完整已识别消息。"""
    类型=记录.get('type')#类型
    if not isinstance(类型,str) or not 是否可进表面类型(类型):#非表面
        return None#无
    数据=记录.get('data')#数据
    if not 是否记录(数据):#无数据
        return None#无
    if 类型=='user/message':#用户
        消息=数据#消息
    elif 类型 in ('assistant/message','tool/result'):#助手/工具
        消息=数据.get('message')#消息
    else:#新形状
        raise Error(f'acp-snapshot: unsupported surface event type "{类型}"')#不支持
    return 完整消息(消息)#消息

def 记录消息们(记录):#记录拥有的消息
    """返回一个持久记录结构上拥有的完整消息身份。"""
    表面=表面事件消息(记录)#表面
    if 表面 is not None:#有表面
        return [表面]#单
    if 记录.get('type')!='agent/inbox/spliced' or not 是否记录(记录.get('data')) or not isinstance(记录['data'].get('inserted'),list):#非收件箱
        return []#空
    结果=[]#结果
    for 值 in 记录['data']['inserted']:#插入
        消息=完整消息(值)#消息
        if 消息 is not None:#有
            结果.append(消息)#追加
    return 结果#返回

def 规范JSON(值):#规范 JSON
    """按值而非插入顺序序列化。"""
    if isinstance(值,list):#数组
        return '['+','.join(规范JSON(项) for 项 in 值)+']'#数组
    if 是否记录(值):#对象
        return '{'+','.join(f'{json.dumps(键,ensure_ascii=False)}:{规范JSON(值[键])}' for 键 in sorted(值))+'}'#对象
    return json.dumps(值,ensure_ascii=False)#叶子

def 唯一消息标识(日志们):#唯一消息 id
    """索引 ID 与指纹相互唯一的无身份消息值。"""
    指纹按标识={}#id→指纹集
    标识按指纹={}#指纹→id 集
    for 日志 in 日志们:#逐日志
        for 记录 in 解析JSONL记录(日志):#逐记录
            for 消息 in 记录消息们(记录):#逐消息
                标识=消息['id']#id
                无标识={键:值 for 键,值 in 消息.items() if 键!='id'}#去 id
                指纹=规范JSON(无标识)#指纹
                指纹按标识.setdefault(标识,set()).add(指纹)#登记
                标识按指纹.setdefault(指纹,set()).add(标识)#登记
    唯一={}#唯一
    for 标识,指纹们 in 指纹按标识.items():#逐 id
        if len(指纹们)!=1:#多指纹
            continue#跳过
        指纹=next(iter(指纹们))#唯一指纹
        if len(标识按指纹.get(指纹,()))!=1:#多 id
            continue#跳过
        唯一[指纹]=标识#登记
    return 唯一#返回

def 夹具消息标识替换(日志们,夹具们):#消息 id 替换
    """跨场景新鲜与现有日志匹配未变完整消息。"""
    新鲜=唯一消息标识(日志们)#新鲜
    已有=唯一消息标识(夹具们)#已有
    替换={}#替换
    for 指纹,新标识 in 新鲜.items():#逐指纹
        旧标识=已有.get(指纹)#旧
        if 旧标识 is None or 新标识==旧标识:#无或相同
            continue#跳过
        替换[新标识]=旧标识#登记
    return 替换#返回

def 应用字面替换(内容,替换们):#应用字面替换
    """应用字面 fixture 替换而不改任何其他新鲜值。"""
    稳定=内容#可变
    for 项 in 替换们:#逐项
        稳定=稳定.replace(项['from'],项['to'])#替换
    return 稳定#返回

def 应用夹具消息标识(内容,替换):#应用消息 id 替换
    """仅重写已校验持久消息 ID 字段。"""
    行们=[]#行
    for 行 in 内容.split('\n'):#逐行
        if 行.strip()=='':#空
            行们.append(行)#保留
            continue#下一项
        记录=json.loads(行)#解析
        改=False#是否改
        for 消息 in 记录消息们(记录):#逐消息
            新=替换.get(消息['id'])#替换
            if 新 is None:#无
                continue#跳过
            消息['id']=新#写入
            改=True#改
        行们.append(json.dumps(记录,ensure_ascii=False,separators=(',',':')) if 改 else 行)#写回
    return '\n'.join(行们)#接合

def 稳定夹具消息标识(日志们,夹具们):#稳定消息 id
    """把已提交 UUID 带入新鲜会话 fixture 中未变、无歧义的消息。"""
    替换=夹具消息标识替换(日志们,夹具们)#替换表
    return [应用夹具消息标识(日志,替换) for 日志 in 日志们]#映射

def 打包时间们(记录):#打包行成员时间
    """一个打包行的成员时间，或普通记录为 None。"""
    if 记录.get('type') not in 打包块行类型:#非打包
        return None#无
    数据=记录.get('data') or {}#数据
    间隙=数据.get('dt') or []#间隙
    时间们=[记录.get('time0') or 0]#起点
    for 间隙值 in 间隙:#累加
        时间们.append(时间们[-1]+间隙值)#追加
    return 时间们#返回

def 逻辑记录们(记录们):#展开打包计时
    """展开打包计时信封，使刷新对齐跟随逻辑事件而非物理行。"""
    结果=[]#结果
    for 记录 in 记录们:#逐记录
        时间们=打包时间们(记录)#时间
        if 时间们 is None:#普通
            结果.append(记录)#追加
        else:#打包
            for 时间 in 时间们:#成员
                结果.append({'type':'assistant/chunk','time':时间})#伪成员
    return 结果#返回

def 未知工具调用标识(原始日志):#未知工具调用 id
    """找到结构化结果报告 UNKNOWN_TOOL 的工具调用。"""
    结果=[]#结果
    for 记录 in 解析JSONL记录(原始日志):#逐记录
        if 记录.get('type')!='tool/result':#非工具结果
            continue#跳过
        数据=记录.get('data')#数据
        if not 是否记录(数据):#无数据
            continue#跳过
        错误=数据.get('error')#错误
        if not 是否记录(错误) or 错误.get('code')!='UNKNOWN_TOOL':#非未知工具
            continue#跳过
        消息=数据.get('message')#消息
        源=消息.get('source') if 是否记录(消息) else None#源
        调用=源.get('callId') if 是否记录(源) else None#callId
        结果.append(调用 if isinstance(调用,str) else '<missing callId>')#追加
    return 结果#返回

def 刷新夹具替换(日志们,夹具们):#刷新 fixture 替换
    """为每日志会话 id、cwd 与溢出路径构建刷新回写替换。"""
    替换=[]#替换
    for 索引,日志 in enumerate(日志们):#逐日志
        内容=日志['content'] if 是否记录(日志) and 'content' in 日志 else 日志#内容
        新鲜行=解析JSONL记录(内容)#新鲜
        已有行=解析JSONL记录(夹具们[索引] if 索引<len(夹具们) else '')#已有
        新鲜头=新鲜行[0] if 新鲜行 else None#新鲜头
        已有头=已有行[0] if 已有行 else None#已有头
        for 字段 in ('id','cwd'):#字段
            来源=None if 新鲜头 is None else 新鲜头.get(字段)#来源
            目标=None if 已有头 is None else 已有头.get(字段)#目标
            if isinstance(来源,str) and isinstance(目标,str) and 来源 and 来源!=目标:#不同
                替换.append({'from':来源,'to':目标})#追加
        新鲜溢出=提取快照溢出路径(内容)#新鲜溢出
        已有溢出=提取快照溢出路径(夹具们[索引] if 索引<len(夹具们) else '')#已有溢出
        for 名,已有路径 in 已有溢出.items():#按名匹配
            新鲜路径=新鲜溢出.get(名)#新鲜
            if 新鲜路径 is not None and 新鲜路径!=已有路径:#不同
                替换.append({'from':新鲜路径,'to':已有路径})#追加
    return 替换#返回

def 保留夹具易变(记录,已有):#保留 fixture 易变字段
    """把已有 fixture 易变字段带入新鲜记录。"""
    if 已有 is None or 已有.get('type')!=记录.get('type'):#类型不同
        return#跳过
    if 记录.get('type')=='session':#会话头
        for 字段 in ('id','createdAt','cwd','parentSession'):#字段
            if 字段 in 记录 and 字段 in 已有:#双方有
                记录[字段]=已有[字段]#借出
        return#结束
    if 'time' in 记录 and 'time' in 已有:#事件时间
        记录['time']=已有['time']#借出
    if 记录.get('type')!='hook/result':#非 hook
        return#结束
    数据=记录.get('data')#数据
    已有数据=已有.get('data')#已有数据
    if 是否记录(数据) and 是否记录(已有数据) and 'durationMs' in 数据 and 'durationMs' in 已有数据:#时长
        数据['durationMs']=已有数据['durationMs']#借出

def 保留打包成员时间(记录,已有成员们):#保留打包成员时间
    """把逻辑成员时间带入新鲜打包行同时不碰其片段数组。"""
    if 记录.get('type') not in 打包块行类型:#非打包
        return#跳过
    数据=记录.get('data')#数据
    if not 是否记录(数据) or not isinstance(数据.get('dt'),list):#无间隙
        return#跳过
    if not 已有成员们:#无成员
        return#跳过
    首时间=已有成员们[0].get('time')#首时间
    if not isinstance(首时间,int) or isinstance(首时间,bool):#非安全整数近似
        return#跳过
    记录['time0']=首时间#写入起点
    if len(已有成员们)!=len(数据['dt'])+1:#长度不对齐
        return#跳过
    时间们=[]#时间
    for 成员 in 已有成员们:#逐成员
        时间=成员.get('time')#时间
        if not isinstance(时间,int) or isinstance(时间,bool):#非法
            return#跳过
        时间们.append(时间)#追加
    间隙=[时间们[索引+1]-时间们[索引] for 索引 in range(len(时间们)-1)]#间隙
    if any(not isinstance(间隙值,int) or isinstance(间隙值,bool) for 间隙值 in 间隙):#非法
        return#跳过
    数据['dt']=间隙#写入

def 保留归一化易变(新鲜,已有,归一新鲜,归一已有,字符串映射):#保留归一化易变
    """复用归一化值等于新鲜值的现有叶子。"""
    if isinstance(新鲜,list) and isinstance(已有,list) and isinstance(归一新鲜,list) and isinstance(归一已有,list):#数组
        if len(新鲜)!=len(已有) or len(新鲜)!=len(归一新鲜) or len(新鲜)!=len(归一已有):#不对齐
            return 新鲜#保留新鲜
        return [保留归一化易变(新鲜[索引],已有[索引],归一新鲜[索引],归一已有[索引],字符串映射) for 索引 in range(len(新鲜))]#映射
    if 是否记录(新鲜) and 是否记录(已有) and 是否记录(归一新鲜) and 是否记录(归一已有):#对象
        结果={}#结果
        for 键,值 in 新鲜.items():#逐键
            if 键 in 已有 and 键 in 归一新鲜 and 键 in 归一已有:#可合并
                结果[键]=保留归一化易变(值,已有[键],归一新鲜[键],归一已有[键],字符串映射)#递归
            else:#不可
                结果[键]=值#新鲜
        return 结果#返回
    if isinstance(新鲜,str) and isinstance(已有,str) and isinstance(归一新鲜,str) and 归一新鲜==归一已有:#字符串
        键=json.dumps([归一新鲜,新鲜],ensure_ascii=False)#映射键
        return 已有 if 字符串映射.get(键)==已有 else 新鲜#复用或新鲜
    return 已有 if 归一新鲜 is 归一已有 or 归一新鲜==归一已有 else 新鲜#叶子

def 归一化刷新记录(记录,上下文):#归一化刷新记录
    """用 fixture 比较同一契约归一化一条对齐记录。"""
    return json.loads(归一化会话日志(json.dumps(记录,ensure_ascii=False)+'\n',上下文))#单行归一化

def 收集归一化字符串映射(新鲜,已有,归一新鲜,归一已有,排除字符串,正向,反向):#收集字符串映射
    """把归一化等价字符串替换加入双射。"""
    if isinstance(新鲜,list) and isinstance(已有,list) and isinstance(归一新鲜,list) and isinstance(归一已有,list):#数组
        if len(新鲜)!=len(已有) or len(新鲜)!=len(归一新鲜) or len(新鲜)!=len(归一已有):#不对齐
            return True#结构差异由新鲜拥有
        return all(收集归一化字符串映射(新鲜[索引],已有[索引],归一新鲜[索引],归一已有[索引],排除字符串,正向,反向) for 索引 in range(len(新鲜)))#逐项
    if 是否记录(新鲜) and 是否记录(已有) and 是否记录(归一新鲜) and 是否记录(归一已有):#对象
        for 键,值 in 新鲜.items():#逐键
            if 键 not in 已有 or 键 not in 归一新鲜 or 键 not in 归一已有:#缺键
                continue#跳过
            if not 收集归一化字符串映射(值,已有[键],归一新鲜[键],归一已有[键],排除字符串,正向,反向):#冲突
                return False#失败
        return True#成功
    if (#非可映射字符串
        not isinstance(新鲜,str)
        or not isinstance(已有,str)
        or not isinstance(归一新鲜,str)
        or 归一新鲜!=归一已有
        or 新鲜==已有
        or 新鲜 in 排除字符串
        or 已有 in 排除字符串
    ):
        return True#跳过
    新鲜键=json.dumps([归一新鲜,新鲜],ensure_ascii=False)#正向键
    已有键=json.dumps([归一新鲜,已有],ensure_ascii=False)#反向键
    已映射已有=正向.get(新鲜键)#已映射
    已映射新鲜=反向.get(已有键)#已映射
    if (已映射已有 is not None and 已映射已有!=已有) or (已映射新鲜 is not None and 已映射新鲜!=新鲜):#冲突
        return False#失败
    正向[新鲜键]=已有#登记
    反向[已有键]=新鲜#登记
    return True#成功

def 归一化字符串映射们(记录们,新鲜记录们,已有记录们,新鲜上下文,已有上下文):#日志级双射
    """为归一化等价字符串构建日志级双射。"""
    排除=set()#排除消息 id
    for 记录 in [*新鲜记录们,*已有记录们]:#逐记录
        for 消息 in 记录消息们(记录):#逐消息
            排除.add(消息['id'])#排除
    正向={}#正向
    反向={}#反向
    已有索引=0#已有游标
    for 记录索引,记录 in enumerate(记录们):#逐记录
        已有记录=已有记录们[已有索引] if 已有索引<len(已有记录们) else None#已有
        成员数=len(打包时间们(记录) or [None])#成员数
        if 记录.get('type')=='session/title' and (已有记录 is None or 已有记录.get('type')!='session/title'):#插入标题
            continue#不推进
        if 成员数>1:#打包
            已有成员=已有记录们[已有索引:已有索引+成员数]#切片
            if len(已有成员)!=成员数 or any(成员.get('type')!='assistant/chunk' for 成员 in 已有成员):#不对齐
                return None#禁用
        else:#单行
            if 已有记录 is None or 已有记录.get('type')!=记录.get('type'):#不对齐
                return None#禁用
            if not 收集归一化字符串映射(#收集
                记录,已有记录,
                归一化刷新记录(新鲜记录们[记录索引],新鲜上下文),
                归一化刷新记录(已有记录,已有上下文),
                排除,正向,反向,
            ):
                return None#冲突
        已有索引+=成员数#推进
    return 正向 if 已有索引==len(已有记录们) else None#完整对齐才返回

def 稳定刷新日志(新鲜,已有,替换们,新鲜上下文):#稳定刷新日志
    """重写新鲜回放日志，使重复刷新不搅动易变 fixture 字段。"""
    新鲜记录们=解析JSONL记录(新鲜)#新鲜记录
    稳定=应用字面替换(新鲜,替换们)#字面稳定
    已有记录们=逻辑记录们(解析JSONL记录(已有))#逻辑已有
    记录们=解析JSONL记录(稳定)#稳定记录
    已有上下文=夹具上下文(已有)#已有上下文
    字符串映射=归一化字符串映射们(记录们,新鲜记录们,已有记录们,新鲜上下文,已有上下文)#双射
    已有索引=0#游标
    先前事件时间=None#先前时间
    for 索引 in range(len(记录们)):#逐记录
        记录=记录们[索引]#记录
        已有记录=已有记录们[已有索引] if 已有索引<len(已有记录们) else None#已有
        成员数=len(打包时间们(记录) or [None])#成员数
        插入标题=记录.get('type')=='session/title' and (已有记录 is None or 已有记录.get('type')!='session/title')#插入标题
        if 插入标题:#插入标题
            if not isinstance(先前事件时间,int) or isinstance(先前事件时间,bool):#无前时间
                raise Error('acp-snapshot: inserted title has no preceding event time')#失败
            记录['time']=先前事件时间#写入
        else:#普通对齐
            if 字符串映射 is not None and 成员数==1 and 已有记录 is not None and 已有记录.get('type')==记录.get('type'):#可复用
                记录=保留归一化易变(#保留
                    记录,已有记录,
                    归一化刷新记录(新鲜记录们[索引],新鲜上下文),
                    归一化刷新记录(已有记录,已有上下文),
                    字符串映射,
                )#结束
                记录们[索引]=记录#写回
            保留打包成员时间(记录,已有记录们[已有索引:已有索引+成员数])#打包时间
            保留夹具易变(记录,已有记录)#易变字段
            已有索引+=成员数#推进
        if isinstance(记录.get('time'),int) and not isinstance(记录.get('time'),bool):#记录时间
            先前事件时间=记录['time']#更新
    return '\n'.join(json.dumps(记录,ensure_ascii=False,separators=(',',':')) for 记录 in 记录们)+'\n'#接合

def 类名(场景):#头类名
    """场景所属头组合类。"""
    return 场景.get('headerClass') or 'default'#默认类

def 定义ACP快照套件(选项):#定义 ACP 快照套件
    """把场景表注册为可运行用例表（对齐 vitest describe/it 树）。"""
    智能体=选项['agent']#待测智能体
    快照目录=选项['snapshotsDir']#快照目录
    场景们=选项['scenarios']#场景列表
    模式=选项['mode']#模式
    有Pwsh=选项.get('hasPwsh')#有 pwsh
    录制中=模式=='record'#是否录制
    刷新中=模式=='refresh'#是否刷新
    子模式='record' if 录制中 else 'replay'#子模式
    按名={}#场景名→场景
    for 场景 in 场景们:#登记
        if 场景['name'] in 按名:#重复
            raise Error(f'acp-snapshot: duplicate scenario name "{场景["name"]}"')#重复
        按名[场景['name']]=场景#登记
        for 字段 in ('systemPromptSource','toolSchemasSource'):#源字段
            if 场景.get(字段) is not None and 场景.get('pinsHeader') is not True:#非法
                raise Error(f'acp-snapshot: {场景["name"]}.{字段} is only valid on a header-pinning scenario')#非法
    钉按类={}#类→钉场景
    for 场景 in 场景们:#收集钉
        if 场景.get('pinsHeader') is not True:#非钉
            continue#跳过
        类=类名(场景)#类
        if 类 in 钉按类:#分裂
            raise Error(f'acp-snapshot: header class "{类}" pinned by both {钉按类[类]["name"]} and {场景["name"]}')#分裂
        钉按类[类]=场景#登记
    for 场景 in 场景们:#每类有钉
        if 类名(场景) not in 钉按类:#缺钉
            raise Error(f'acp-snapshot: no scenario pins the request-header content of class "{类名(场景)}" (needed by {场景["name"]})')#缺钉
    def 解析源(钉场景,字段,标签):#解析共享源
        """解析钉场景引用的 sidecar 源场景。"""
        源名=钉场景.get(字段) or 钉场景['name']#源名
        源=按名.get(源名)#源
        if 源 is None:#未知
            raise Error(f'acp-snapshot: {钉场景["name"]} names unknown {标签} source "{源名}"')#未知
        if 源.get('pinsHeader') is not True:#非钉
            raise Error(f'acp-snapshot: {钉场景["name"]} names non-pinning {标签} source "{源名}"')#非钉
        if 源.get(字段) is not None and 源.get(字段)!=源['name']:#不自有
            raise Error(f'acp-snapshot: {钉场景["name"]} names {标签} source "{源名}", which does not own its sidecar')#不自有
        期望变更=钉场景.get('expectedHeaderChanges') or 0#期望
        源变更=源.get('expectedHeaderChanges') or 0#源变更
        if 源变更!=期望变更:#不一致
            raise Error(f'acp-snapshot: {钉场景["name"]} and {源名} declare different header-change counts for shared {标签}')#不一致
        return 源#返回
    提示词源按类={类:解析源(钉,'systemPromptSource','system-prompt snapshot') for 类,钉 in 钉按类.items()}#提示词源
    模式源按类={类:解析源(钉,'toolSchemasSource','tool-schema snapshot') for 类,钉 in 钉按类.items()}#schema 源
    提示词所有者={源['name'] for 源 in 提示词源按类.values()}#提示词所有者
    模式所有者={源['name'] for 源 in 模式源按类.values()}#schema 所有者
    提示词主张={}#共享提示词主张
    模式主张={}#共享 schema 主张
    用例=[]#用例表
    def 运行场景用例(场景):#单场景用例
        """回放/录制/刷新一个场景并做全部比较。"""
        if 场景是否跳过(场景,录制中,有Pwsh=有Pwsh):#跳过
            return {'skipped':True}#跳过
        目录=os.path.join(快照目录,场景['name'])#场景目录
        清单路径=os.path.join(目录,'snapshot.yml')#清单
        解析快照清单(读文本(清单路径),清单路径)#校验清单
        输入=json.loads(读文本(os.path.join(目录,'input.json')))#输入脚本
        覆盖文件=os.path.join(目录,'replay.override.json')#覆盖
        工作区=os.path.join(目录,'workspace')#工作区
        夹具文件=会话夹具们(目录) if not 录制中 else []#fixture 清单
        子夹具=夹具文件[1:]#子
        比较日志=场景['comparesLog'] if 'comparesLog' in 场景 else 场景.get('hasModelTurn')#比较日志
        运行选项={#运行选项
            'agent':智能体,#智能体
            'mode':子模式,#模式
            'fixtureFile':os.path.join(目录,'session.jsonl'),#主 fixture
        }#选项起点
        if 场景.get('env') is not None:#环境
            运行选项['env']=场景['env']#写入
        if os.path.isfile(覆盖文件):#有覆盖
            运行选项['overrideFile']=覆盖文件#写入
        if not 录制中 and 子夹具:#回放子
            运行选项['childFiles']=[os.path.join(目录,名) for 名 in 子夹具]#写入
        if os.path.isdir(工作区):#有工作区
            运行选项['workspaceDir']=工作区#写入
        if 场景.get('prepareWorkspace') is not None:#准备
            运行选项['prepareWorkspace']=场景['prepareWorkspace']#写入
        if 场景.get('workspaceParent') is not None:#父目录
            运行选项['workspaceParent']=场景['workspaceParent']#写入
        if 场景.get('configPath') is not None:#配置
            运行选项['configPath']=场景['configPath']#写入
        结果=运行场景(输入,运行选项)#运行
        for 日志 in 结果['sessionLogs']:#拒未知工具
            断言相等(未知工具调用标识(日志['content']),[],f"session {日志['id']}: snapshot scenarios must not accept UNKNOWN_TOOL")#断言
        上下文={#归一化上下文
            'sessionIds':[
                *([结果['sessionId']] if 结果.get('sessionId') is not None else []),
                *[日志['id'] for 日志 in 结果['sessionLogs']],
            ],#会话 id
            'cwd':结果['cwd'],#cwd
            'cwdAliases':结果.get('cwdAliases') or [],#别名
        }#上下文结束
        子模式钉=set(场景.get('pinsChildToolSchemas') or [])#子 schema 钉
        子提示钉=set(场景.get('pinsChildSystemPrompts') or [])#子提示钉
        可移植夹具=令牌化会话夹具工作目录 if 场景.get('workspaceParent') is None else (lambda 日志:日志)#可移植
        写会话夹具=(录制中 and 场景.get('recorded') and 场景.get('hasModelTurn')) or (刷新中 and 比较日志)#是否写
        if 写会话夹具:#写热/刷新 fixture
            断言大于(len(结果['sessionLogs']),0,f'{模式} produced no session log to harvest')#有日志
            if 刷新中:#刷新长度
                断言相等(len(结果['sessionLogs']),len(夹具文件),f'expected {len(夹具文件)} session logs (parent + children)')#长度
            输出文件=['session.jsonl',*[f'session.{索引+1}.jsonl' for 索引 in range(len(结果['sessionLogs'])-1)]]#输出名
            已有夹具=[]#已有
            for 名 in 输出文件:#逐名
                路径=os.path.join(目录,名)#路径
                已有夹具.append(读文本(路径) if os.path.isfile(路径) else '')#读
            刷新替换=刷新夹具替换(结果['sessionLogs'],已有夹具) if 刷新中 else []#替换
            if 刷新中:#刷新稳定
                新鲜夹具=[擦除会话快照(可移植夹具(稳定刷新日志(日志['content'],已有夹具[索引],刷新替换,上下文))) for 索引,日志 in enumerate(结果['sessionLogs'])]#新鲜
            else:#录制擦除
                新鲜夹具=[擦除会话快照(可移植夹具(日志['content'])) for 日志 in 结果['sessionLogs']]#新鲜
            输出夹具=脱敏会话快照标识(稳定夹具消息标识(新鲜夹具,已有夹具))#脱敏
            for 索引,内容 in enumerate(输出夹具):#写出
                写文本(os.path.join(目录,输出文件[索引]),内容)#写
            if 录制中:#删陈旧子
                输出名集=set(输出文件)#集合
                for 名 in list(os.listdir(目录)):#逐文件
                    if re.match(r'^session\.[1-9]\d*\.jsonl$',名) and 名 not in 输出名集 and os.path.isfile(os.path.join(目录,名)):#陈旧
                        os.remove(os.path.join(目录,名))#删除
                夹具文件=输出文件#更新清单
            if 场景.get('pinsHeader') is True:#钉场景写 sidecar
                主日志=结果['sessionLogs'][0]#主
                钉头=钉住头载荷(主日志['content'],上下文)#钉头
                提示词们=从头取系统提示词(钉头)#提示词
                断言大于(len(提示词们),0,f'{模式} produced no system prompt to snapshot')#有提示词
                提示快照=格式化系统提示词快照(提示词们[0],提示词们[1:])#快照
                提示源=提示词源按类.get(类名(场景)) or 场景#源
                提示路径=os.path.join(快照目录,提示源['name'],系统提示词快照)#路径
                主张共享快照(提示词主张,提示路径,场景['name'],提示快照)#主张
                写文本(提示路径,提示快照)#写
                模式集=从头取工具模式(钉头)#schema
                断言大于(len(模式集),0,f'{模式} produced no tool schemas to snapshot')#有 schema
                断言相等(len(模式集),len(提示词们),f'{模式} produced a tool-schema sequence that differs from its prompt sequence')#对齐
                工具快照=格式化工具模式快照(模式集[0],模式集[1:])#快照
                模式源=模式源按类.get(类名(场景)) or 场景#源
                模式路径=os.path.join(快照目录,模式源['name'],工具模式快照)#路径
                主张共享快照(模式主张,模式路径,场景['name'],工具快照)#主张
                写文本(模式路径,工具快照)#写
            for 索引 in 子模式钉:#子 schema sidecar
                日志=结果['sessionLogs'][索引] if 索引<len(结果['sessionLogs']) else None#日志
                断言真(日志 is not None,f'{模式}: no child session log at index {索引} to snapshot schemas from')#存在
                模式集=从头取工具模式(钉住头载荷(日志['content'],上下文))#schema
                断言大于(len(模式集),0,f'{模式}: child {索引} produced no tool schemas to snapshot')#有
                写文本(os.path.join(目录,子工具模式快照(索引)),格式化工具模式快照(模式集[0],模式集[1:]))#写
            for 索引 in 子提示钉:#子提示 sidecar
                日志=结果['sessionLogs'][索引] if 索引<len(结果['sessionLogs']) else None#日志
                断言真(日志 is not None,f'{模式}: no child session log at index {索引} to snapshot a prompt from')#存在
                提示词们=从头取系统提示词(钉住头载荷(日志['content'],上下文))#提示词
                断言大于(len(提示词们),0,f'{模式}: child {索引} produced no system prompt to snapshot')#有
                写文本(os.path.join(目录,子系统提示词快照(索引)),格式化系统提示词快照(提示词们[0]))#写
        for 期望 in 标准输出期望变体(场景):#stdout 变体
            标准出=归一化标准输出(结果['rawStdout'],上下文,{'cwdPathMode':期望['cwdPathMode']})#归一化
            期望路径=os.path.join(目录,期望['file'])#路径
            if 刷新中:#刷新写出
                写文本(期望路径,标准出)#写
            断言相等(标准出,读文本(期望路径),f"{期望['file']} mismatch")#比较
        if 比较日志:#比较会话日志
            断言相等(len(结果['sessionLogs']),len(夹具文件),'this scenario must persist one log per session fixture')#1:1
            收获=[日志['content'] for 日志 in 结果['sessionLogs']]#收获
            夹具内容=[读文本(os.path.join(目录,名)) for 名 in 夹具文件]#已提交
            夹具上下文们=[夹具上下文(项) for 项 in 夹具内容]#上下文
            夹具归一={'sessionIds':[标识 for 项 in 夹具上下文们 for 标识 in 项['sessionIds']],'cwd':夹具上下文们[0]['cwd']}#合并
            实际快照=归一化会话快照们(收获,上下文)#实际
            期望快照=归一化会话快照们(夹具内容,夹具归一)#期望
            for 索引,实际 in enumerate(实际快照):#逐份
                断言相等(实际,期望快照[索引],f'{夹具文件[索引]} mismatch')#比较
        钉场景=钉按类.get(类名(场景)) or 场景#类钉
        提示源=提示词源按类.get(类名(场景)) or 钉场景#提示源
        模式源=模式源按类.get(类名(场景)) or 钉场景#schema 源
        钉目录=os.path.join(快照目录,钉场景['name'])#钉目录
        钉夹具=读文本(os.path.join(钉目录,'session.jsonl'))#钉 fixture
        钉住=钉住头载荷(钉夹具,夹具上下文(钉夹具))#钉头
        提示快照=读文本(os.path.join(快照目录,提示源['name'],系统提示词快照))#提示 sidecar
        初始提示=初始系统提示词快照(提示快照)#初始段
        断言相等(len(钉住),1+(钉场景.get('expectedHeaderChanges') or 0),f"the pinning fixture ({钉场景['name']}) has an unexpected request/header count")#计数
        工具快照=读文本(os.path.join(快照目录,模式源['name'],工具模式快照))#schema sidecar
        工具模式=解析工具模式快照(工具快照)#解析
        钉模式集=[工具模式['initial'],*工具模式['changes']]#序列
        断言相等(len(钉模式集),len(钉住),f"the schema source ({模式源['name']}) has an unexpected tool-schema count")#对齐
        钉头们=[恢复钉住工具模式(头,钉模式集[索引]) for 索引,头 in enumerate(钉住)]#恢复
        子钉模式={}#子 schema
        for 索引 in 子模式钉:#逐索引
            解析=解析工具模式快照(读文本(os.path.join(目录,子工具模式快照(索引))))#解析
            子钉模式[索引]=[解析['initial'],*解析['changes']]#登记
        子钉提示={}#子提示
        for 索引 in 子提示钉:#逐索引
            子钉提示[索引]=读文本(os.path.join(目录,子系统提示词快照(索引)))#登记
        for 日志索引,日志 in enumerate(结果['sessionLogs']):#逐日志头均匀性
            子模式=子钉模式.get(日志索引)#子 schema
            期望变更=(场景.get('expectedHeaderChanges') or 0) if 场景.get('pinsHeader') is True and 日志索引==0 else 0#期望变更
            断言相等(头变更计数(日志['content']),期望变更,f"session {日志['id']}: changed request/header count")#计数
            头事件=归一化头事件(擦除系统提示词(日志['content']),上下文)#头事件
            头们=[事件['header'] for 事件 in 头事件]#头
            提示词们=归一化系统提示词(日志['content'],上下文)#提示词
            模式集=归一化工具模式(日志['content'],上下文)#schema
            断言相等(len(提示词们),len(头们),f"session {日志['id']}: every request/header must carry a string system prompt")#对齐
            断言相等(len(模式集),len(头们),f"session {日志['id']}: every request/header must carry an array-valued tools field")#对齐
            if 子模式 is not None:#子 schema 计数
                断言相等(len(子模式),1+头变更计数(日志['content']),f"session {日志['id']}: {子工具模式快照(日志索引)} has an unexpected tool-schema count")#计数
            修订=0#修订
            for 键,头 in enumerate(头们):#逐头
                if 头事件[键].get('reason')=='change':#变更
                    修订+=1#加一
                类钉=钉头们[修订] if 期望变更>0 else 钉头们[0]#类钉
                期望=类钉 if 子模式 is None else {**类钉,'tools':子模式[修订]}#期望头
                断言相等(头,期望,f"session {日志['id']}: request/header #{键+1} diverged from the pinned ({钉场景['name']}) header")#比较
                if 期望变更==0:#初始提示
                    子提示=子钉提示.get(日志索引)#子提示
                    源标签=子系统提示词快照(日志索引) if 子提示 is not None else f"{提示源['name']}/{系统提示词快照}"#标签
                    断言相等(格式化系统提示词快照(提示词们[键]),子提示 if 子提示 is not None else 初始提示,f"session {日志['id']}: initial system prompt #{键+1} diverged from {源标签}")#比较
            if 场景.get('pinsHeader') is True and 日志索引==0:#钉场景变更 sidecar
                钉头=钉住头载荷(日志['content'],上下文)#钉头
                钉提示=从头取系统提示词(钉头)#提示
                钉模式=从头取工具模式(钉头)#schema
                断言相等(格式化系统提示词快照(钉提示[0],钉提示[1:]),提示快照,f"session {日志['id']}: changed system prompts diverged from {提示源['name']}/{系统提示词快照}")#提示
                断言相等(格式化工具模式快照(钉模式[0],钉模式[1:]),工具快照,f"session {日志['id']}: changed tool schemas diverged from {模式源['name']}/{工具模式快照}")#schema
        清单=解析快照清单(读文本(清单路径),清单路径)#再读清单
        if (清单.get('workspace') or {}).get('final') is True:#最终工作区
            期望工作区=捕获期望工作区快照(os.path.join(目录,'workspace.expected'))#期望
            断言相等(结果.get('finalWorkspace'),期望工作区,f"{场景['name']}: complete final workspace")#比较
        else:#未声明变更
            断言相等(结果.get('finalWorkspace'),结果.get('initialWorkspace'),f"{场景['name']}: a changed workspace requires workspace.final")#不变
        return {'skipped':False,'result':结果}#完成
    for 场景 in 场景们:#注册场景用例
        用例.append({'name':f"snapshot: {场景['name']}",'run':(lambda 场景=场景:运行场景用例(场景))})#用例
    def 断言无孤儿():#无孤儿目录
        """每个场景目录必须已注册。"""
        磁盘=sorted(名 for 名 in os.listdir(快照目录) if os.path.isdir(os.path.join(快照目录,名)))#磁盘
        已登记=sorted(场景['name'] for 场景 in 场景们)#已登记
        断言相等(磁盘,已登记,'acp-snapshot: orphan or missing scenario dirs')#比较
    用例.append({'name':'fixtures:no-orphans','run':断言无孤儿})#用例
    def 断言必需文件():#必需文件在场
        """每个已注册场景有其必需 fixture 文件。"""
        for 场景 in 场景们:#逐场景
            名=场景['name']#名
            目录=os.path.join(快照目录,名)#目录
            文件=[项 for 项 in os.listdir(目录) if os.path.isfile(os.path.join(目录,项))]#文件
            清单路径=os.path.join(目录,'snapshot.yml')#清单
            断言真(os.path.isfile(清单路径),f'{名}/snapshot.yml')#存在
            清单=解析快照清单(读文本(清单路径),清单路径)#解析
            断言相等(清单.get('profile'),智能体.get('profile') or 'acp',f'{名}: manifest profile')#profile
            断言真(清单.get('session') is None,f'{名}: ACP scenarios own their session')#无 session
            def 子索引(模式):#子 sidecar 索引
                """从文件名提取子索引集合。"""
                结果=set()#索引集
                for 项 in 文件:#逐文件
                    匹配=re.match(模式,项)#匹配
                    if 匹配 is not None:#命中
                        结果.add(int(匹配.group(1)))#登记
                return 结果#返回
            断言相等(子索引(r'^tool-schemas\.([1-9]\d*)\.expected\.json$'),set(场景.get('pinsChildToolSchemas') or []),f'{名}: child tool-schema sidecars must match pinsChildToolSchemas')#schema
            断言相等(子索引(r'^system-prompt\.([1-9]\d*)\.expected\.md$'),set(场景.get('pinsChildSystemPrompts') or []),f'{名}: child system-prompt sidecars must match pinsChildSystemPrompts')#提示
            断言真(os.path.isfile(os.path.join(目录,'input.json')),f'{名}/input.json')#input
            断言真(os.path.isfile(os.path.join(目录,'stdout.expected.jsonl')),f'{名}/stdout.expected.jsonl')#stdout
            断言相等(os.path.isfile(os.path.join(目录,视窗标准输出快照)),场景.get('pinsNativeWindowsStdout') is True,f'{名}/{视窗标准输出快照} presence must match pinsNativeWindowsStdout')#windows
            断言真(os.path.isfile(os.path.join(目录,'session.jsonl')),f'{名}/session.jsonl')#session
            断言相等(os.path.isfile(os.path.join(目录,'replay.override.json')),场景.get('overridden') is True,f'{名}/replay.override.json presence must match overridden')#override
            断言相等(os.path.isfile(os.path.join(目录,系统提示词快照)),名 in 提示词所有者,f'{名}/{系统提示词快照} presence must match snapshot-source ownership')#提示
            断言相等(os.path.isfile(os.path.join(目录,工具模式快照)),名 in 模式所有者,f'{名}/{工具模式快照} presence must match snapshot-source ownership')#schema
            会话夹具们(目录)#清单校验
    用例.append({'name':'fixtures:required-files','run':断言必需文件})#用例
    def 断言恰一钉():#每类恰一钉
        """每个头类恰好一个钉场景。"""
        钉={}#类→名列表
        for 场景 in 场景们:#逐场景
            if 场景.get('pinsHeader') is not True:#非钉
                continue#跳过
            类=类名(场景)#类
            钉.setdefault(类,[]).append(场景['name'])#登记
        断言相等({类:len(名们) for 类,名们 in 钉.items()},{类:1 for 类 in 钉按类},'exactly one pin per header class')#计数
        for 场景 in 场景们:#每场景有类钉
            断言真(类名(场景) in 钉按类,f'class "{类名(场景)}" (scenario {场景["name"]}) has a pin')#有钉
    用例.append({'name':'fixtures:one-pin-per-class','run':断言恰一钉})#用例
    def 断言钉组合():#钉组合 sidecar
        """每个钉 fixture 与其引用 sidecar 组合良构。"""
        for 场景 in 钉按类.values():#逐钉
            提示源=提示词源按类.get(类名(场景)) or 场景#提示源
            模式源=模式源按类.get(类名(场景)) or 场景#schema 源
            夹具=读文本(os.path.join(快照目录,场景['name'],'session.jsonl'))#fixture
            头们=钉住头载荷(夹具,夹具上下文(夹具))#头
            提示快照=读文本(os.path.join(快照目录,提示源['name'],系统提示词快照))#提示
            断言相等(len(头们),1+(场景.get('expectedHeaderChanges') or 0),f"{场景['name']}: unexpected request/header count")#计数
            工具快照=读文本(os.path.join(快照目录,模式源['name'],工具模式快照))#schema
            工具模式=解析工具模式快照(工具快照)#解析
            模式集=[工具模式['initial'],*工具模式['changes']]#序列
            断言相等(len(模式集),len(头们),f"{模式源['name']}: tool-schema sequence must match {场景['name']}'s header sequence")#对齐
            for 索引,头 in enumerate(头们):#逐头
                恢复钉住工具模式(头,模式集[索引])#必须令牌
            断言大于(len(提示快照),0,f"{提示源['name']}/{系统提示词快照} must not be empty")#非空
            断言真(提示快照.endswith('\n'),f"{提示源['name']}/{系统提示词快照} must end in a newline")#换行
            断言相等(工具快照,格式化工具模式快照(工具模式['initial'],工具模式['changes']),f"{模式源['name']}/{工具模式快照} must use canonical JSON formatting")#规范
            断言相等(头变更计数(夹具),场景.get('expectedHeaderChanges') or 0,f"{场景['name']}: a pinning fixture must carry exactly its declared changed headers")#变更
    用例.append({'name':'fixtures:pin-sidecars','run':断言钉组合})#用例
    def 断言唯一共享():#共享快照唯一
        """每个不同提示词与工具 schema 快照只存一份。"""
        提示们=[{'path':f'{所有者}/{系统提示词快照}','content':读文本(os.path.join(快照目录,所有者,系统提示词快照))} for 所有者 in 提示词所有者]#提示
        模式们=[{'path':f'{所有者}/{工具模式快照}','content':读文本(os.path.join(快照目录,所有者,工具模式快照))} for 所有者 in 模式所有者]#schema
        断言唯一快照内容('system-prompt',提示们)#提示唯一
        断言唯一快照内容('tool-schema',模式们)#schema 唯一
    用例.append({'name':'fixtures:unique-shared','run':断言唯一共享})#用例
    def 断言子伴随():#子 sidecar 规范
        """每个声明的子 sidecar 规范且命名真实子项。"""
        for 场景 in 场景们:#逐场景
            目录=os.path.join(快照目录,场景['name'])#目录
            文件=会话夹具们(目录)#fixture
            for 索引 in 场景.get('pinsChildToolSchemas') or []:#子 schema
                断言真(索引<len(文件),f"{场景['name']}: child schema pin {索引} must name an existing session.<n>.jsonl fixture")#存在
                名=子工具模式快照(索引)#文件名
                伴随=读文本(os.path.join(目录,名))#内容
                解析=解析工具模式快照(伴随)#解析
                断言相等(伴随,格式化工具模式快照(解析['initial'],解析['changes']),f"{场景['name']}/{名} must use canonical JSON formatting")#规范
                断言大于(len(解析['initial']),0,f"{场景['name']}/{名} must pin at least one schema")#非空
            for 索引 in 场景.get('pinsChildSystemPrompts') or []:#子提示
                断言真(索引<len(文件),f"{场景['name']}: child prompt pin {索引} must name an existing session.<n>.jsonl fixture")#存在
                名=子系统提示词快照(索引)#文件名
                伴随=读文本(os.path.join(目录,名))#内容
                提示源=提示词源按类.get(类名(场景)) or 场景#类源
                类钉=读文本(os.path.join(快照目录,提示源['name'],系统提示词快照))#类钉
                断言子系统提示词快照(伴随,初始系统提示词快照(类钉),f"{场景['name']}/{名}")#断言
    用例.append({'name':'fixtures:child-sidecars','run':断言子伴随})#用例
    def 断言规范存储():#规范 fixture 存储
        """每个已提交 JSONL 有合法工具结果与规范存储。"""
        for 场景 in 场景们:#逐场景
            目录=os.path.join(快照目录,场景['name'])#目录
            文件=会话夹具们(目录)#fixture
            for 名 in 文件:#逐文件
                夹具=读文本(os.path.join(目录,名))#内容
                断言相等(未知工具调用标识(夹具),[],f"{场景['name']}/{名} contains UNKNOWN_TOOL")#未知工具
                断言真('/private{{cwd}}' not in 夹具,f"{场景['name']}/{名} carries a non-canonical macOS cwd token")#mac 令牌
                断言相等(擦除系统提示词(夹具),夹具,f"{场景['name']}/{名} carries an unscrubbed system prompt")#提示已擦
                断言相等(擦除工具模式(夹具),夹具,f"{场景['name']}/{名} carries unscrubbed tool schemas")#schema 已擦
                if 场景.get('pinsHeader') is not True:#非钉
                    断言相等(擦除请求头(夹具),夹具,f"{场景['name']}/{名} carries unscrubbed header content")#头已擦
            夹具们=[读文本(os.path.join(目录,名)) for 名 in 文件]#全部
            断言相等(脱敏会话快照标识(夹具们),夹具们,f"{场景['name']}: identity redaction fixed point")#不动点
    用例.append({'name':'fixtures:canonical-storage','run':断言规范存储})#用例
    return {'cases':用例,'runAll':lambda:[项['run']() for 项 in 用例]}#套件句柄

scenarioSkipped=场景是否跳过#上游名
stdoutExpectedVariants=标准输出期望变体#上游名
claimSharedSnapshot=主张共享快照#上游名
assertUniqueSnapshotContents=断言唯一快照内容#上游名
sessionFixtureNames=会话夹具名#上游名
fixtureContext=夹具上下文#上游名
normalizedHeaders=归一化请求头#上游名
normalizedSystemPrompts=归一化系统提示词#上游名
normalizedToolSchemas=归一化工具模式#上游名
formatToolSchemasSnapshot=格式化工具模式快照#上游名
parseToolSchemasSnapshot=解析工具模式快照#上游名
restorePinnedToolSchemas=恢复钉住工具模式#上游名
formatSystemPromptSnapshot=格式化系统提示词快照#上游名
assertChildSystemPromptSnapshot=断言子系统提示词快照#上游名
headerChangeCount=头变更计数#上游名
unknownToolCallIds=未知工具调用标识#上游名
refreshFixtureReplacements=刷新夹具替换#上游名
stabilizeFixtureMessageIds=稳定夹具消息标识#上游名
stabilizeRefreshLog=稳定刷新日志#上游名
defineAcpSnapshotSuite=定义ACP快照套件#上游名
