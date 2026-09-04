"""纯 ACP transcript 与会话日志归一化器。

对齐上游 `session-snapshot/src/normalize.ts`。公开面仅中文名。
"""
import json,re#JSON 与正则
from ...内核.会话 import 解码存储记录,打包块游程#会话编解码
from .身份 import 脱敏会话快照标识#身份脱敏

__all__=[#仅中文公开名
    '提取快照溢出路径','令牌化会话夹具工作目录','归一化标准输出','归一化会话日志',
    '归一化会话快照','归一化会话快照们','擦除系统提示词','擦除工具模式','擦除请求头','擦除会话快照',
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
Error=Exception#错误别名

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
    行们=原始日志.split('\n')#行
    首行=next((行 for 行 in 行们 if 行.strip()!=''),None)#首非空
    头=json.loads(首行) if 首行 is not None else {}#头
    工作目录=头['cwd'] if isinstance(头.get('cwd'),str) else ''#cwd
    基名=工作目录.replace('\\','/').rstrip('/').split('/')[-1] if 工作目录 else ''#basename
    if 基名=='':#无 basename
        raise Error('acp-snapshot: cannot tokenize a cwd without a basename')#无 basename
    上下文={'sessionIds':[],'cwd':工作目录}#上下文
    return '\n'.join(#重写
        行 if 行.strip()=='' else json.dumps(令牌化夹具值(json.loads(行),上下文,基名),ensure_ascii=False,separators=(',',':'))
        for 行 in 行们
    )#接合

def 归一化标准输出(原始标准出,上下文,选项=None):#归一化 stdout
    """把原始 stdout transcript 归一化为稳定期望输出。"""
    if 选项 is None:#缺省
        选项={}#空
    路径模式=选项.get('cwdPathMode') or 'canonical'#路径模式
    身份模式=选项.get('identityMode') or 'legacy'#身份模式
    行们=[行 for 行 in 原始标准出.split('\n') if 行.strip()!='']#非空行
    标识序={}#id 序号
    def 稳定标识(标识):#稳定 JSON-RPC id
        """按首次出现映射到序号。"""
        键=json.dumps(标识,ensure_ascii=False)#键
        if 键 not in 标识序:#新
            标识序[键]=len(标识序)+1#分配
        return 标识序[键]#返回
    帧们=[]#帧
    for 行 in 行们:#逐行
        帧=json.loads(行)#解析
        if 'id' in 帧 and 帧['id'] is not None:#有 id
            帧['id']=稳定标识(帧['id'])#稳定
        帧们.append(擦除值(帧,上下文,路径模式,身份模式))#擦除
    return '\n'.join(json.dumps(帧,ensure_ascii=False,separators=(',',':')) for 帧 in 帧们)+'\n'#NDJSON

def 解码序号范围(值):#解码序号范围内联
    """展开 sourceEventSeqs（内核尚未导出时内联）。"""
    if not isinstance(值,list):#非数组
        return 值#原样
    解码=[]#结果
    for 条目 in 值:#逐项
        if isinstance(条目,int) and not isinstance(条目,bool):#单
            解码.append(条目)#追加
        elif isinstance(条目,list) and len(条目)==2:#范围
            解码.extend(range(条目[0],条目[1]+1))#展开
        else:#其它
            解码.append(条目)#原样
    return 解码#返回

def 归一化会话日志(原始日志,上下文,选项=None):#归一化会话日志
    """将会话 JSONL 日志归一化为稳定期望输出。"""
    if 选项 is None:#缺省
        选项={}#空
    路径模式=选项.get('cwdPathMode') or 'canonical'#路径模式
    身份模式=选项.get('identityMode') or 'legacy'#身份模式
    行们=[行 for 行 in 原始日志.split('\n') if 行.strip()!='']#非空行
    记录们=[]#记录
    for 行 in 行们:#逐行
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
        if 'sourceEventSeqs' in 记录:#溯源
            记录['sourceEventSeqs']=解码序号范围(记录['sourceEventSeqs'])#解码
        记录们.append(擦除值(记录,上下文,路径模式,身份模式))#擦除
    return '\n'.join(json.dumps(记录,ensure_ascii=False,separators=(',',':')) for 记录 in 记录们)+'\n'#JSONL

def 重打包会话快照(原始日志):#重打包投影正文
    """重打包投影正文记录，使持久化冲刷边界不影响已提交快照。"""
    行们=[行 for 行 in 原始日志.split('\n') if 行.strip()!='']#非空行
    头=行们.pop(0)#头行
    下一序号=0#下一序号
    事件们=[]#事件
    for 行 in 行们:#逐行
        记录=json.loads(行)#解析
        if 是否打包行(记录):#打包行
            解码=解码存储记录({**记录,'seq0':下一序号,'time0':0})#解码
            if not isinstance(解码,list):#单
                解码=[解码]#包
            下一序号+=len(解码)#推进
            事件们.extend(解码)#收集
        else:#普通事件
            事件={**记录,'seq':下一序号,'time':0}#合成信封
            下一序号+=1#推进
            事件们.append(事件)#收集
    正文=[]#正文行
    for 存储 in 打包块游程(事件们):#打包
        投影=dict(存储)#拷贝
        省略信封(投影)#省略信封
        正文.append(json.dumps(投影,ensure_ascii=False,separators=(',',':')))#序列化
    return '\n'.join([头,*正文,''])#接合

def 擦除头内容(原始日志,选项):#擦除所选请求头载荷
    """变换所选请求头载荷。"""
    行们=原始日志.split('\n')#行
    输出=[]#输出
    for 行 in 行们:#逐行
        if 行.strip()=='':#空行
            输出.append(行)#保留
            continue#下一项
        记录=json.loads(行)#解析
        数据=记录.get('data')#数据
        if not isinstance(数据,dict):#无数据
            输出.append(行)#原样
            continue#下一项
        if 记录.get('type')=='request/header':#请求头
            头=数据.get('header')#头
            if not isinstance(头,dict):#无头
                输出.append(行)#原样
                continue#下一项
            触及=False#是否触及
            if 选项.get('system') and 'system' in 头:#擦系统
                头['system']=系统令牌#令牌
                触及=True#触及
            if 选项.get('tools') and 'tools' in 头:#擦工具
                头['tools']=工具令牌#令牌
                触及=True#触及
            输出.append(json.dumps(记录,ensure_ascii=False,separators=(',',':')) if 触及 else 行)#写回
        else:#其它
            输出.append(行)#原样
    return '\n'.join(输出)#接合

def 擦除系统提示词(原始日志):#擦除系统提示词
    """用 {{system}} 替换请求头中的系统提示词内容。"""
    return 擦除头内容(原始日志,{'system':True})#擦系统

def 擦除工具模式(原始日志):#擦除工具 schema
    """用 {{tools}} 替换完整请求头快照中的工具 schema。"""
    return 擦除头内容(原始日志,{'tools':True})#擦工具

def 擦除请求头(原始日志):#擦除全部头主体
    """用稳定令牌替换会话 JSONL 中所有臃肿请求头内容。"""
    return 擦除头内容(原始日志,{'system':True,'tools':True})#全擦

def 擦除会话快照(原始日志):#擦除会话快照
    """投影持久化会话日志同时标记化全部请求头主体。"""
    已擦=擦除请求头(原始日志)#先擦头
    记录索引=0#索引
    行们=[]#行
    for 行 in 已擦.split('\n'):#逐行
        if 行.strip()=='':#空
            行们.append(行)#保留
            continue#下一项
        记录=json.loads(行)#解析
        if 记录索引==0:#头
            记录索引+=1#推进
            if 记录.get('type')!='session':#必须会话头
                raise Error('session snapshot must start with a session header')#非法
            行们.append(行)#原样
            continue#下一项
        记录索引+=1#推进
        省略信封(记录)#省略信封
        行们.append(json.dumps(记录,ensure_ascii=False,separators=(',',':')))#写回
    return '\n'.join(行们)#接合

def 归一化会话快照(原始日志,上下文,选项=None):#归一化会话快照
    """为已提交 fixture 归一化并投影持久化会话 JSONL。"""
    return 重打包会话快照(擦除会话快照(归一化会话日志(原始日志,上下文,选项)))#组合

def 归一化会话快照们(原始日志们,上下文,选项=None):#归一化多份快照
    """用共享类型化身份脱敏归一化一个场景的主与子日志。"""
    if 选项 is None:#缺省
        选项={}#空
    return [#映射
        重打包会话快照(擦除会话快照(归一化会话日志(
            日志,{'sessionIds':[],'cwd':上下文['cwd'],**({'cwdAliases':上下文['cwdAliases']} if 'cwdAliases' in 上下文 else {})},
            {**选项,'identityMode':'preserve'},
        )))
        for 日志 in 脱敏会话快照标识(原始日志们)
    ]#返回

extractSnapshotSpillPaths=提取快照溢出路径#上游名
tokenizeSessionFixtureCwd=令牌化会话夹具工作目录#上游名
normalizeStdout=归一化标准输出#上游名
normalizeSessionLog=归一化会话日志#上游名
normalizeSessionSnapshot=归一化会话快照#上游名
normalizeSessionSnapshots=归一化会话快照们#上游名
scrubSystemPrompts=擦除系统提示词#上游名
scrubToolSchemas=擦除工具模式#上游名
scrubRequestHeaders=擦除请求头#上游名
scrubSessionSnapshot=擦除会话快照#上游名
