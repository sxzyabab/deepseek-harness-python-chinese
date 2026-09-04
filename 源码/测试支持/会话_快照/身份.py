"""已提交会话快照的关系保持身份脱敏。

对齐上游 `session-snapshot/src/identity.ts`。公开面仅中文名。
"""
import json,re#JSON 与正则

__all__=['脱敏会话快照标识']#仅中文公开名

UUID片段模式=re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',re.I)#UUID 片段
旧式令牌模式=re.compile(r'^\{\{(?:sessionId|messageId)\}\}$')#旧式令牌
规范令牌模式=re.compile(r'^\{\{(session|message|approval|workflow|command|rpc|retry|id):([1-9]\d*)\}\}$')#规范令牌
标识键模式=re.compile(r'(?:^id$|Id$|Ids$)')#id 键名模式
文中消息模式=re.compile(r'\bas message ([0-9a-f-]{36})\b',re.I)#文中消息 id
匿名用户模式=re.compile(r'\bAnonymous user: ([0-9a-f-]{36})\b',re.I)#匿名用户

def 是否记录(值):#是否字典
    """值是否为非数组对象。"""
    return isinstance(值,dict)#字典

def 解析日志(日志):#解析日志
    """按行解析 JSONL。"""
    记录们=[json.loads(行) for 行 in 日志.splitlines() if 行.strip()!='']#解析每行
    return {'records':记录们,'trailingNewline':日志.endswith('\n')}#解析结果

def 消息标识(值):#提取消息 id
    """识别消息对象形态的 id。"""
    if not 是否记录(值):#非字典
        return None#无
    if not isinstance(值.get('id'),str):#无 id
        return None#无
    if not isinstance(值.get('role'),str):#无 role
        return None#无
    if not isinstance(值.get('content'),list):#无 content
        return None#无
    if not 是否记录(值.get('source')):#无 source
        return None#无
    return 值['id']#消息 id

def 是脱敏候选(值):#是否候选脱敏
    """字符串是否为脱敏候选。"""
    return bool(UUID片段模式.search(值) or 旧式令牌模式.match(值) or 规范令牌模式.match(值))#是否候选

def 脱敏会话快照标识(日志们):#脱敏会话快照 id
    """替换易变不透明 id，同时跨父与其子日志保持相等关系。"""
    已解析=[解析日志(日志) for 日志 in 日志们]#解析全部日志
    令牌表={}#值到令牌
    种类计数={}#种类计数
    def 认领(值,种类,始终=False):#认领身份
        """为值分配类型化令牌。"""
        if not isinstance(值,str) or 值=='' or 值 in 令牌表:#跳过
            return#跳过
        if not 始终 and not 是脱敏候选(值):#非候选
            return#跳过
        规范=规范令牌模式.match(值)#匹配规范令牌
        if 规范 is not None:#已是规范令牌
            规范种类=规范.group(1)#种类
            序=int(规范.group(2))#序号
            种类计数[规范种类]=max(种类计数.get(规范种类,0),序)#抬高计数
            令牌表[值]=值#规范令牌原样保留
            return#结束
        下一=种类计数.get(种类,0)+1#下一序号
        种类计数[种类]=下一#写计数
        令牌表[值]=f'{{{{{种类}:{下一}}}}}'#分配新令牌
    for 日志 in 已解析:#认领会话头
        头=日志['records'][0] if 日志['records'] else None#首行
        if 头 is not None and 头.get('type')=='session':#会话头
            认领(头.get('id'),'session',True)#会话头 id
    def 收集(值,记录类型=None):#收集身份
        """递归收集身份字段。"""
        if isinstance(值,str):#字符串
            for 匹配 in 文中消息模式.finditer(值):#文中消息 id
                认领(匹配.group(1),'message')#认领
            for 匹配 in 匿名用户模式.finditer(值):#匿名用户
                认领(匹配.group(1),'id')#认领
            return#结束
        if isinstance(值,list):#数组
            for 项 in 值:#递归
                收集(项,记录类型)#递归
            return#结束
        if not 是否记录(值):#非字典
            return#结束
        消息=消息标识(值)#消息对象 id
        if 消息 is not None:#消息对象
            认领(消息,'message')#认领
        for 子键,项 in 值.items():#遍历字段
            if 记录类型 in ('approval/asked','approval/decided'):#审批记录
                if 子键=='id':#审批 id
                    认领(项,'approval')#认领
            elif 子键=='commandId':#命令 id
                认领(项,'command',True)#认领
            elif 子键=='rpcId':#RPC id
                认领(项,'rpc',True)#认领
            elif 子键=='retryId':#重试 id
                认领(项,'retry')#认领
            elif 子键=='runId':#工作流 id
                认领(项,'workflow')#认领
            elif 标识键模式.search(子键):#通用 id 键
                认领(项,'id')#认领
            收集(项,记录类型)#递归
    for 日志 in 已解析:#收集全部
        for 记录 in 日志['records']:#逐记录
            收集(记录,记录.get('type'))#收集
    替换表=sorted(令牌表.items(),key=lambda 项:len(项[0]),reverse=True)#长优先替换
    def 替换(值):#应用替换
        """递归应用令牌替换。"""
        if isinstance(值,str):#字符串
            if 值 in 令牌表:#精确命中
                return 令牌表[值]#精确命中
            输出=值#可变输出
            for 源,令牌 in 替换表:#子串替换
                输出=输出.replace(源,令牌)#替换
            return 输出#返回
        if isinstance(值,list):#数组
            return [替换(项) for 项 in 值]#映射
        if 是否记录(值):#字典
            return {键:替换(项) for 键,项 in 值.items()}#递归
        return 值#原样
    结果=[]#结果
    for 日志 in 已解析:#重写每份日志
        内容='\n'.join(json.dumps(替换(记录),ensure_ascii=False,separators=(',',':')) for 记录 in 日志['records'])#重序列化
        结果.append(内容+'\n' if 日志['trailingNewline'] else 内容)#恢复尾换行
    return 结果#返回

redactSessionSnapshotIds=脱敏会话快照标识#上游名
