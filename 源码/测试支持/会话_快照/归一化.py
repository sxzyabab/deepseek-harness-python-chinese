import json,re#JSON 与正则
from ...内核.会话 import 解码存储记录,打包块游程#会话编解码
from ...内核.会话.序号范围 import 解码序号范围 as _内核解码序号范围#内核序号范围
from .身份 import 脱敏会话快照标识#身份脱敏

try:#比较前迁移到当前格式（可选；目录未就绪时跳过）
    from ..llm_回放 import 准备会话快照夹具供比较#fixture 迁移比较
except Exception:#导入失败
    准备会话快照夹具供比较=None#不可用

__all__=[#仅中文公开名
    '提取快照溢出路径','令牌化会话夹具工作目录','归一化标准输出','归一化会话日志',
    '归一化会话快照','归一化会话快照列表','擦除系统提示词','擦除工具模式','擦除模型请求主体','擦除请求头','擦除会话快照',
]#公开面结束

会话标识令牌='{{sessionId}}'#会话 id 令牌
消息标识令牌='{{messageId}}'#消息 id 令牌
已用令牌='{{usedTokens}}'#已用 token 令牌
工作目录令牌='{{cwd}}'#工作目录令牌
系统令牌='{{system}}'#系统提示词令牌
工具令牌='{{tools}}'#工具 schema 令牌
事件时间令牌='{{eventTime}}'#事件时间令牌
省略字节令牌='{{eventOmittedBytes}}'#省略字节令牌
打包块行类型=frozenset(['text-chunks','reasoning-chunks','tool-call-chunks'])#打包行类型
工作目录根路径模式=re.compile(r'\{\{cwd\}\}(?:[\\/][^\s<>"\'`]+)+')#cwd 根路径
路径标签模式=re.compile(r'(<path>)([^<]*)(</path>)')#path 标签
附加说明路径模式=re.compile(r'(Additional instructions from: )([^\r\n]+)')#附加说明路径
嵌入事件时间模式=re.compile(r'^(  "time": )\d+(?=,\r?$)',re.M)#嵌入事件时间
省略字节文案模式=re.compile(r'(\r?\n\r?\n\(Omitted )\d+( bytes\.)')#省略字节文案
目标事件区域模式=re.compile(#目标事件区域
    r'^Session [^\r\n]+ — [^\r\n]+\r?\nTarget event seq \d+:\r?\n```json\r?\n\{\r?\n[\s\S]*?(?=\r?\n```(?:\r?\n|$)|\r?\n\r?\n\(Omitted )',
)#区域结束
路径文本边界模式=re.compile(r'[\s<>\'"`()\[\]{},;:!?=]')#路径文本边界
文件URI前缀模式=re.compile(r'(?:^|[^a-z0-9+.-])file:\/\/\/?$',re.I)#file URI 前缀
UUID模式=re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',re.I)#UUID
本地溢出路径模式=re.compile(#本地溢出路径
    r'\{\{cwd\}\}[\\/]\.spill[\\/]session-[0-9a-f]{12}[\\/][0-9a-f]{12}-([A-Za-z0-9._~-]+?)'
    +r'(?=\. Use read with offset/limit|[\s)]|$)',
)#本地结束
快照溢出路径模式=re.compile(#快照溢出路径
    r'(?:[A-Za-z]:)?[\\/](?:tmp|t)[\\/](?:dsh-acp-snap-[0-9a-f]{9}|dsh-acp-snapshot-spill)[\\/]session-[0-9a-f]{12}[\\/][0-9a-f]{12}-([A-Za-z0-9._~-]+?)'
    +r'(?=\. Use read with offset/limit|[\s)]|$)',
)#快照结束
def 是否打包行(记录):#是否打包行
    """是否打包 fixture 行。"""
    return isinstance(记录.get('type'),str) and 记录['type'] in 打包块行类型#是否打包行

def 省略信封(记录):#省略信封字段
    """删除仅持久化信封字段。"""
    记录.pop('seq',None)#删序号
    记录.pop('time',None)#删时间
    记录.pop('seq0',None)#删起始序号
    记录.pop('time0',None)#删起始时间

def 规范化嵌入路径(值):#规范化嵌入路径
    """仅在生成的带路径文本标记内转换分隔符。"""
    值=路径标签模式.sub(lambda 匹配:匹配.group(1)+匹配.group(2).replace('\\','/')+匹配.group(3),值)#path 标签
    return 附加说明路径模式.sub(lambda 匹配:匹配.group(1)+匹配.group(2).replace('\\','/'),值)#附加说明

def 提取快照溢出路径(内容):#提取溢出路径
    """从会话日志提取每个快照模式溢出路径。"""
    结果={}#结果表
    for 匹配 in 快照溢出路径模式.finditer(内容):#逐匹配
        名=匹配.group(1)#文件名
        if 名 is None:#无捕获
            continue#跳过
        结果[名]=匹配.group(0)#写入完整路径
    return 结果#返回表

def 工作目录拼写(上下文):#cwd 拼写列表
    """返回生成 cwd 的每一种已知拼写，最具体优先。"""
    基础=list({上下文['cwd'],*(上下文.get('cwdAliases') or [])})#去重基础
    基础=[拼 for 拼 in 基础 if 拼]#去空
    mac别名=[f'/private{拼}' for 拼 in 基础 if 拼.startswith('/') and not 拼.startswith('/private/')]#mac 前缀
    return sorted({*基础,*mac别名},key=len,reverse=True)#长优先

def 是工作目录匹配(值,起点,长度):#是否 cwd 匹配边界
    """嵌入的 cwd 匹配是否在路径/文本边界起止。"""
    前=值[起点-1] if 起点>0 else None#前字符
    后=值[起点+长度] if 起点+长度<len(值) else None#后字符
    后后=值[起点+长度+1] if 起点+长度+1<len(值) else None#后后字符
    起合法=前 is None or 路径文本边界模式.match(前) or 文件URI前缀模式.search(值[:起点]) is not None#起始边界
    止合法=后 is None or 后 in '/\\' or 路径文本边界模式.match(后) or (后=='.' and (后后 is None or 路径文本边界模式.match(后后)))#结束边界
    return 起合法 and 止合法#双边合法

def 替换工作目录拼写(值,拼写,替换):#替换一种 cwd 拼写
    """替换一种 cwd 拼写，而不匹配仅共享其前缀的更长路径段。"""
    游标=0#游标
    输出=''#输出
    while 游标<len(值):#扫描
        匹配=值.find(拼写,游标)#找拼写
        if 匹配<0:#无匹配
            return 输出+值[游标:]#收尾
        结束=匹配+len(拼写)#匹配结束
        if 是工作目录匹配(值,匹配,len(拼写)):#合法边界
            输出+=值[游标:匹配]+替换#替换
            游标=结束#推进
        else:#非边界
            输出+=值[游标:结束]#原样保留
            游标=结束#推进
    return 输出#返回

def 替换工作目录(值,上下文,替换):#替换全部 cwd 拼写
    """用稳定令牌替换每一种已知 cwd 拼写。"""
    输出=值#可变输出
    for 拼写 in 工作目录拼写(上下文):#逐拼写
        输出=替换工作目录拼写(输出,拼写,替换)#替换
    return 输出#返回

def 擦除字符串(值,上下文,路径模式,身份模式):#擦除字符串身份
    """在字符串中用稳定令牌替换 cwd、会话 id 与散落 UUID。"""
    输出=替换工作目录(值,上下文,工作目录令牌)#先换 cwd
    输出=输出.replace(f'/private{工作目录令牌}',工作目录令牌)#折叠 private 前缀
    if 路径模式=='canonical':#规范路径
        输出=工作目录根路径模式.sub(lambda 匹配:匹配.group(0).replace('\\','/'),输出)#cwd 根路径
        输出=规范化嵌入路径(输出)#嵌入路径
    输出=本地溢出路径模式.sub(lambda 匹配:f"{{{{spillLocator:{匹配.group(1)}}}}}",输出)#本地溢出
    输出=快照溢出路径模式.sub(lambda 匹配:f"{{{{spillLocator:{匹配.group(1)}}}}}",输出)#快照溢出
    if 目标事件区域模式.search(输出):#目标区域
        输出=目标事件区域模式.sub(lambda 匹配:嵌入事件时间模式.sub(rf'\g<1>{事件时间令牌}',匹配.group(0)),输出)#擦时间
        输出=省略字节文案模式.sub(rf'\g<1>{省略字节令牌}\g<2>',输出)#擦省略字节
    if 身份模式=='legacy':#旧式身份
        for 标识 in 上下文['sessionIds']:#会话 id
            输出=输出.replace(标识,会话标识令牌)#替换
        输出=UUID模式.sub(会话标识令牌,输出)#散落 UUID
    return 输出#返回

def 擦除值(值,上下文,路径模式,身份模式,键=None):#递归擦除
    """递归擦除已解析 JSON 值。"""
    if isinstance(值,str):#字符串
        if 身份模式=='legacy' and 键=='messageId':#消息 id
            return 消息标识令牌#令牌
        已擦=擦除字符串(值,上下文,路径模式,身份模式)#擦除
        return 已擦.replace('\\','/') if 路径模式=='canonical' and 键=='path' else 已擦#path 规范
    if isinstance(值,list):#数组
        return [擦除值(项,上下文,路径模式,身份模式) for 项 in 值]#映射
    if isinstance(值,dict):#对象
        输出={子键:擦除值(子值,上下文,路径模式,身份模式,子键) for 子键,子值 in 值.items()}#递归
        if 值.get('sessionUpdate')=='usage_update' and isinstance(值.get('used'),(int,float)):#用量更新
            输出['used']=已用令牌#令牌
        return 输出#返回
    return 值#原样

def 转义正则(值):#转义正则
    """转义字面路径段。"""
    return re.escape(值)#转义

def 令牌化夹具字符串(值,上下文,基名):#令牌化字符串
    """替换末段为生成 cwd basename 的任意绝对拼写。"""
    精确=替换工作目录(值,上下文,工作目录令牌)#精确 cwd
    绝对=re.compile(#绝对 cwd
        rf'(?:[A-Za-z]:)?[\\/](?:[^\\/\s<>"]+[\\/])*{转义正则(基名)}'
        +r'(?=$|[\\/\s<>\'"()\[\]{},;:!?=])',
    )#模式结束
    return 绝对.sub(工作目录令牌,精确).replace(f'/private{工作目录令牌}',工作目录令牌)#折叠

def 令牌化夹具值(值,上下文,基名):#递归令牌化
    """递归替换生成 cwd 拼写。"""
    if isinstance(值,str):#字符串
        return 令牌化夹具字符串(值,上下文,基名)#令牌化
    if isinstance(值,list):#数组
        return [令牌化夹具值(项,上下文,基名) for 项 in 值]#映射
    if isinstance(值,dict):#对象
        return {键:令牌化夹具值(项,上下文,基名) for 键,项 in 值.items()}#递归
    return 值#原样

def 令牌化会话夹具工作目录(原始日志):#令牌化 fixture cwd
    """把生成工作区存为 {{cwd}} 同时保留每一个其他会话值。"""
    行列表=原始日志.split('\n')#行
    首行=next((行 for 行 in 行列表 if 行.strip()!=''),None)#首非空
    头=json.loads(首行) if 首行 is not None else {}#头
    工作目录=头['cwd'] if isinstance(头.get('cwd'),str) else ''#cwd
    基名=工作目录.replace('\\','/').rstrip('/').split('/')[-1] if 工作目录 else ''#basename
    if 基名=='':#无 basename
        raise Exception('acp-snapshot: 没有 basename 则无法把 cwd 分词')#无 basename
    上下文={'sessionIds':[],'cwd':工作目录}#上下文
    return '\n'.join(#重写
        行 if 行.strip()=='' else json.dumps(令牌化夹具值(json.loads(行),上下文,基名),ensure_ascii=False,separators=(',',':'))
        for 行 in 行列表
    )#接合

def 归一化标准输出(原始标准出,上下文,选项=None):#归一化 stdout
    """把原始 stdout transcript 归一化为稳定期望输出。"""
    if 选项 is None:#缺省
        选项={}#空
    路径模式=选项.get('cwdPathMode') or 'canonical'#路径模式
    身份模式=选项.get('identityMode') or 'legacy'#身份模式
    行列表=[行 for 行 in 原始标准出.split('\n') if 行.strip()!='']#非空行
    标识序={}#id 序号
    def 稳定标识(标识):#稳定 JSON-RPC id
        """按首次出现映射到序号。"""
        键=json.dumps(标识,ensure_ascii=False)#键
        if 键 not in 标识序:#新
            标识序[键]=len(标识序)+1#分配
        return 标识序[键]#返回
    帧列表=[]#帧
    for 行 in 行列表:#逐行
        帧=json.loads(行)#解析
        if 'id' in 帧 and 帧['id'] is not None:#有 id
            帧['id']=稳定标识(帧['id'])#稳定
        帧列表.append(擦除值(帧,上下文,路径模式,身份模式))#擦除
    return '\n'.join(json.dumps(帧,ensure_ascii=False,separators=(',',':')) for 帧 in 帧列表)+'\n'#NDJSON

def 解码序号范围(值):#解码序号范围
    """展开 sourceEventSeqs；非法形态原样返回以兼容归一化擦除。"""
    if not isinstance(值,list):#非数组
        return 值#原样
    try:#严格解码
        return _内核解码序号范围(值)#内核
    except TypeError:#非法形态
        return 值#原样

def 归一化会话日志(原始日志,上下文,选项=None):#归一化会话日志
    """将会话 JSONL 日志归一化为稳定期望输出。"""
    if 选项 is None:#缺省
        选项={}#空
    路径模式=选项.get('cwdPathMode') or 'canonical'#路径模式
    身份模式=选项.get('identityMode') or 'legacy'#身份模式
    行列表=[行 for 行 in 原始日志.split('\n') if 行.strip()!='']#非空行
    记录列表=[]#记录
    for 行 in 行列表:#逐行
        记录=json.loads(行)#解析
        if 记录.get('type')=='session':#会话头
            if 'createdAt' in 记录:#创建时间
                记录['createdAt']=0#归零
        elif 是否打包行(记录):#打包行
            if 'time0' in 记录:#时间锚
                记录['time0']=0#归零
            数据=记录.get('data')#数据
            if isinstance(数据,dict) and isinstance(数据.get('dt'),list):#dt 间隙
                数据['dt']=[0]*len(数据['dt'])#归零
        elif 'time' in 记录:#普通时间
            记录['time']=0#归零
        if 记录.get('type')=='hook/result' and isinstance(记录.get('data'),dict):#hook 结果
            if 'durationMs' in 记录['data']:#时长
                记录['data']['durationMs']=0#归零
        if 记录.get('type')=='goal/change' and isinstance(记录.get('data'),dict):#目标变更
            if 'createdAt' in 记录['data']:#创建
                记录['data']['createdAt']=0#归零
            if 'updatedAt' in 记录['data']:#更新
                记录['data']['updatedAt']=0#归零
        if 记录.get('type')=='subagent/catalog' and isinstance(记录.get('data'),dict):#子智能体目录
            if 'childCreatedAt' in 记录['data']:#子创建
                记录['data']['childCreatedAt']=0#归零
        if 'sourceEventSeqs' in 记录:#溯源
            记录['sourceEventSeqs']=解码序号范围(记录['sourceEventSeqs'])#解码
        记录列表.append(擦除值(记录,上下文,路径模式,身份模式))#擦除
    return '\n'.join(json.dumps(记录,ensure_ascii=False,separators=(',',':')) for 记录 in 记录列表)+'\n'#JSONL

def 重打包会话快照(原始日志):#重打包投影正文
    """重打包投影正文记录，使持久化冲刷边界不影响已提交快照。"""
    行列表=[行 for 行 in 原始日志.split('\n') if 行.strip()!='']#非空行
    头=行列表.pop(0)#头行
    下一序号=0#下一序号
    事件列表=[]#事件
    for 行 in 行列表:#逐行
        记录=json.loads(行)#解析
        if 是否打包行(记录):#打包行
            解码=解码存储记录({**记录,'seq0':下一序号,'time0':0})#解码
            if not isinstance(解码,list):#单
                解码=[解码]#包
            下一序号+=len(解码)#推进
            事件列表.extend(解码)#收集
        else:#普通事件
            事件={**记录,'seq':下一序号,'time':0}#合成信封
            下一序号+=1#推进
            事件列表.append(事件)#收集
    正文=[]#正文行
    for 存储 in 打包块游程(事件列表):#打包
        省略信封(存储)#原地省略信封
        正文.append(json.dumps(存储,ensure_ascii=False,separators=(',',':')))#序列化
    return '\n'.join([头,*正文,''])#接合

def 擦除模型请求内容(原始日志,选项):#擦除所选模型请求载荷
    """变换所选模型请求载荷。"""
    行列表=原始日志.split('\n')#行
    输出=[]#输出
    for 行 in 行列表:#逐行
        if 行.strip()=='':#空行
            输出.append(行)#保留
            continue#下一项
        记录=json.loads(行)#解析
        数据=记录.get('data')#数据
        if not isinstance(数据,dict):#无数据
            输出.append(行)#原样
            continue#下一项
        触及=False#是否触及
        if 选项.get('system') and 记录.get('type')=='system/message':#系统消息
            消息=数据.get('message')#消息
            if isinstance(消息,dict) and isinstance(消息.get('content'),list) and len(消息['content'])>0:#有内容
                块=消息['content'][0]#首块
                if isinstance(块,dict) and isinstance(块.get('text'),str):#有文本
                    块['text']=系统令牌#令牌
                    触及=True#触及
        if 选项.get('tools') and 记录.get('type')=='request/header':#请求头
            头=数据.get('header')#头
            if isinstance(头,dict) and 'tools' in 头:#有工具
                头['tools']=工具令牌#令牌
                触及=True#触及
        输出.append(json.dumps(记录,ensure_ascii=False,separators=(',',':')) if 触及 else 行)#写回
    return '\n'.join(输出)#接合

def 擦除系统提示词(原始日志):#擦除系统提示词
    """用 {{system}} 替换每个 system/message 的渲染提示词文本。"""
    return 擦除模型请求内容(原始日志,{'system':True})#擦系统

def 擦除工具模式(原始日志):#擦除工具 schema
    """用 {{tools}} 替换完整请求头快照中的工具 schema。"""
    return 擦除模型请求内容(原始日志,{'tools':True})#擦工具

def 擦除模型请求主体(原始日志):#擦除模型请求主体
    """用稳定令牌替换臃肿模型请求内容：system/message 提示词与请求头 tools。"""
    return 擦除模型请求内容(原始日志,{'system':True,'tools':True})#全擦

def 擦除请求头(原始日志):#兼容旧名
    """历史别名；等价于 {@link 擦除模型请求主体}。"""
    return 擦除模型请求主体(原始日志)#全擦

def 擦除会话快照(原始日志):#擦除会话快照
    """投影持久化会话日志同时标记化提示词文本与 schema 主体。"""
    已擦=擦除模型请求主体(原始日志)#先擦主体
    记录索引=0#索引
    行列表=[]#行
    for 行 in 已擦.split('\n'):#逐行
        if 行.strip()=='':#空
            行列表.append(行)#保留
            continue#下一项
        记录=json.loads(行)#解析
        if 记录索引==0:#头
            记录索引+=1#推进
            if 记录.get('type')!='session':#必须会话头
        raise Exception('会话快照必须以会话头开始')#非法
            行列表.append(行)#原样
            continue#下一项
        记录索引+=1#推进
        省略信封(记录)#省略信封
        行列表.append(json.dumps(记录,ensure_ascii=False,separators=(',',':')))#写回
    return '\n'.join(行列表)#接合

def 归一化会话快照(原始日志,上下文,选项=None):#归一化会话快照
    """为已提交 fixture 归一化并投影持久化会话 JSONL。"""
    return 重打包会话快照(擦除会话快照(归一化会话日志(原始日志,上下文,选项)))#组合

def 是否有会话格式版本(原始日志):#是否有格式版本
    """fixture 是否声明已发布 Session 格式，因而参与迁移烧入。"""
    首行=next((行 for 行 in 原始日志.splitlines() if 行.strip()!=''),None)#首非空行
    if 首行 is None:#缺头
        raise Exception('会话快照必须以会话头开始')#缺头
    头=json.loads(首行)#解析头
    if not isinstance(头,dict) or 头.get('type')!='session':#非 session 头
        raise Exception('会话快照必须以会话头开始')#缺头
    return 'version' in 头#是否有 version

def 归一化会话格式溯源(原始日志):#归一化格式溯源
    """仅为期望输出比较省略官方迁移后的制品头世代。"""
    行列表=[]#输出
    for 行 in 原始日志.split('\n'):#逐行
        if 行.strip()=='':#空行
            行列表.append(行)#原样
            continue#下一项
        记录=json.loads(行)#解析
        if 记录.get('type')!='session' or 'version' not in 记录:#非头或不含 version
            行列表.append(行)#原样
            continue#下一项
        记录.pop('version',None)#删 version
        行列表.append(json.dumps(记录,ensure_ascii=False,separators=(',',':')))#重序列化
    return '\n'.join(行列表)#拼回

def 归一化会话快照列表(原始日志列表,上下文,选项=None):#归一化多份快照
    """用共享类型化身份脱敏归一化一个场景的主与子日志。"""
    if 选项 is None:#缺省
        选项={}#空
    当前=[]#当前格式日志
    for 日志 in 原始日志列表:#逐份
        if 准备会话快照夹具供比较 is not None and 是否有会话格式版本(日志):#可迁移
            当前.append(准备会话快照夹具供比较(日志))#迁移到当前
        else:#原样
            当前.append(日志)#原样
    可比=[归一化会话格式溯源(日志) for 日志 in 当前]#抹格式溯源
    return [#映射
        重打包会话快照(擦除会话快照(归一化会话日志(
            日志,{'sessionIds':[],'cwd':上下文['cwd'],**({'cwdAliases':上下文['cwdAliases']} if 'cwdAliases' in 上下文 else {})},
            {**选项,'identityMode':'preserve'},
        )))
        for 日志 in 脱敏会话快照标识(可比)
    ]#返回
