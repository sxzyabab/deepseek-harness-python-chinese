"""面向模型的工作区指令渲染，受显式字节预算约束。"""
import math,os#截断预算与路径分量

系统提醒开='<system-reminder>'#系统提醒开标签
系统提醒闭='</system-reminder>'#系统提醒闭标签
工作区上下文开场='The following workspace instructions may be relevant to your work. '#工作区指令开场
工作区上下文开场+='Use them as guidance when applicable. More specific instructions take precedence over broader ones. '#更具体者优先
工作区上下文开场+='They do not override system, developer, or direct user instructions.'#不覆盖系统/开发者/用户指令
替换工作区上下文开场='This complete workspace instruction baseline replaces all earlier workspace instruction baselines. '+工作区上下文开场#整份基线替换先前基线
空替换工作区上下文开场='This complete workspace instruction baseline replaces all earlier workspace instruction baselines. '#空基线替换开场
空替换工作区上下文开场+='No workspace instructions are currently active.'#当前无活动工作区指令
压缩工作区上下文开场='Workspace instructions were omitted or truncated to fit the configured byte budget.'#预算裁剪开场
用户全局目录='user-global'#用户全局目录占位
用户全局文件='AGENTS.md'#用户全局固定文件名
作用域分隔='\u0000'#作用域键里目录与文件名的分隔，路径与文件名都不可能含NUL
def 字节长度(值):#计算UTF-8字节长度
    """按 utf8 计字符串字节长度。"""
    return len(值.encode('utf-8'))#按utf8计

def 截断Utf8(值,最大字节):#按UTF-8字节截断且不切断码点
    """按 UTF-8 字节截断且不切断码点。"""
    字节=值.encode('utf-8')#编码为字节
    if len(字节)<=最大字节:#已能装下则原样返回
        return 值#原样
    结束=max(0,math.trunc(最大字节))#预算切断点
    while 结束>0 and (字节[结束]&0xc0)==0x80:#续字节则继续回退
        结束-=1#排除该续字节
    return 字节[:结束].decode('utf-8')#解码切断后的前缀

def 转义指令帧正文(正文):#防止正文提前关闭系统提醒帧
    """转义闭标签，防止正文提前关闭系统提醒帧。"""
    return 正文.replace(系统提醒闭,'<\\/system-reminder>')#转义闭标签

def 章节文本(文件):#基线章节文本
    """路径标题加正文。"""
    return 'Instructions from: '+文件['displayPath']+'\n\n'+文件['content']#路径标题加正文

def 展示路径作用域(展示路径):#由展示路径得到作用域
    """从面向模型的路径推导逻辑指令作用域。返回 user-global、.，或所在的相对项目目录。"""
    if 展示路径=='~/.dsh/AGENTS.md' or 展示路径=='$DSH_HOME/AGENTS.md':#两种家目录展示都映射到用户全局
        return 用户全局目录#用户全局
    return os.path.dirname(展示路径).replace('\\','/') or '.'#其余用所在目录；根文件为.

def 候选作用域键(目录,候选名):#组成按候选划分的作用域键
    """为单个指令候选文件组成调和键。目录与文件名用 NUL 分隔。"""
    return 目录+作用域分隔+候选名#目录+NUL+文件名

def 指令作用域键(展示路径):#由展示路径得到候选作用域键
    """为已加载指令文件推导按候选划分的作用域键。"""
    return 候选作用域键(展示路径作用域(展示路径),os.path.basename(展示路径))#目录与文件名配对

def 解码作用域键(作用域):#解码作用域键
    """还原候选作用域键编码的目录与候选文件名。"""
    分隔=作用域.find(作用域分隔)#找NUL分隔
    if 分隔<0:#无分隔则整段当目录
        return {'directory':作用域,'candidateName':''}#整段当目录
    return {'directory':作用域[:分隔],'candidateName':作用域[分隔+1:]}#切开目录与文件名

def 追加章节文本(文件):#动态追加章节文本
    """拼追加说明与正文。"""
    作用域=展示路径作用域(文件['displayPath'])#该文件的逻辑作用域
    return '\n'.join([#拼追加说明
        'Additional instructions from: '+文件['displayPath'],#追加来源标题
        '',#空行
        'These instructions apply to work under `'+作用域+'`. Use them as guidance when relevant; more specific instructions take precedence. They do not override system, developer, or direct user instructions.',#适用范围与优先级
        '',#空行
        文件['content'],#文件正文
    ])#用换行拼起来

基线渲染风格={'intro':工作区上下文开场,'section':章节文本}#普通基线风格

def 基线风格(文件们,替换先前基线):#按是否替换选择基线开场
    """按是否替换选择基线开场。"""
    if 替换先前基线 is not True:#非替换用普通开场
        return 基线渲染风格#普通
    风格=dict(基线渲染风格)#沿用章节函数
    风格['intro']=空替换工作区上下文开场 if len(文件们)==0 else 替换工作区上下文开场#有无文件决定开场
    return 风格#替换风格

def 变更章节文本(项):#按变更动作渲染章节
    """按 set/replace/remove 渲染章节。"""
    变更=项['change']#状态转移
    文件=项['file']#当前文件
    if 变更['action']=='set':#新设置用追加章节
        return 追加章节文本(文件)#追加
    if 变更['action']=='remove':#移除
        return 'Instructions removed: '+变更['path']+'\n\nThe previously loaded instructions from this file no longer apply.'#声明旧指令失效
    return '\n'.join([#替换：文件在加载后已改
        'Updated instructions from: '+变更['path'],#更新来源标题
        '',#空行
        'This file changed after it was loaded. Use the following content instead of the previously loaded instructions from this file.',#改用新内容
        '',#空行
        文件['content'],#新正文
    ])#用换行拼起来

def 预算标记文本(最大字节,省略们,截断们):#预算诊断标记
    """拼预算裁剪诊断标记。"""
    if len(省略们)==0 and len(截断们)==0:#没有裁剪则无标记
        return ''#空
    片段=[]#诊断片段
    if len(省略们)>0:#有整份省略
        片段.append('omitted '+', '.join([文件['displayPath'] for 文件 in 省略们]))#列出省略路径
    if len(截断们)>0:#有截断
        片段.append('truncated '+', '.join([项['displayPath']+' from '+str(项['originalBytes'])+' to '+str(项['includedBytes'])+' bytes' for 项 in 截断们]))#列出截断记账
    return 'Workspace instruction budget '+str(最大字节)+' bytes: '+'; '.join(片段)#拼预算诊断

def 组装指令文本(文件们,最大字节,省略们,截断们,风格):#组装系统提醒帧内的指令正文
    """返回带帧的完整文本。"""
    标记=预算标记文本(最大字节,省略们,截断们)#预算标记
    块们=[块 for 块 in [标记,风格['intro']]+[风格['section'](文件) for 文件 in 文件们] if len(块)>0]#去掉空块
    return '\n'.join([系统提醒开,转义指令帧正文('\n\n'.join(块们)),系统提醒闭])#开标签、转义正文、闭标签

def 带截断内容(文件,纳入字节):#拷贝文件并截断正文
    """只改 content。"""
    拷贝=dict(文件)#浅拷贝
    拷贝['content']=截断Utf8(文件['content'],纳入字节)#截断正文
    return 拷贝#截断后文件

def 截断到装下(文件,已纳入,最大字节,省略们,风格):#二分截断单个文件直到整份文本装进预算
    """装得下的最长截断。"""
    原文字节=字节长度(文件['content'])#原文字节
    低=0#二分下界
    高=原文字节#二分上界
    最佳=带截断内容(文件,0)#目前最佳，初始为零内容
    while 低<=高:#二分寻找最大可纳入字节
        中=(低+高)//2#本轮尝试的纳入字节
        候选=带截断内容(文件,中)#按mid截断
        截断=[{'displayPath':文件['displayPath'],'originalBytes':原文字节,'includedBytes':字节长度(候选['content'])}]#本候选的截断记账
        文本=组装指令文本(已纳入+[候选],最大字节,省略们,截断,风格)#试渲染
        if 字节长度(文本)<=最大字节:#装得下
            最佳=候选#记下更长的可行截断
            低=中+1#尝试纳入更多
        else:#装不下
            高=中-1#减少纳入
    return 最佳#返回最佳截断

def 渲染指令上下文(文件们,最大字节,风格):#按预算渲染指令上下文
    """正文、省略、截断与代表文件。"""
    if 最大字节<=0 or not math.isfinite(最大字节):#非法预算
        return {'text':'','omitted':list(文件们),'truncated':[],'represented':[]}#全部当作省略
    完整=组装指令文本(文件们,最大字节,[],[],风格)#先试完整渲染
    if 字节长度(完整)<=最大字节:#完整装得下
        return {'text':完整,'omitted':[],'truncated':[],'represented':list(文件们)}#全部代表
    for 起点 in range(1,len(文件们)):#从最宽开始整份丢掉，保留更具体后缀
        纳入=文件们[起点:]#保留的后缀
        省略=[{'absolutePath':文件['absolutePath'],'displayPath':文件['displayPath']} for 文件 in 文件们[:起点]]#丢掉的前缀
        后缀文本=组装指令文本(纳入,最大字节,省略,[],风格)#试渲染后缀
        if 字节长度(后缀文本)<=最大字节:#后缀装得下则采用
            return {'text':后缀文本,'omitted':省略,'truncated':[],'represented':list(纳入)}#采用后缀
    最具体=文件们[-1] if len(文件们)>0 else None#最具体的一份
    if 最具体 is None:#空列表保护
        return {'text':'','omitted':[],'truncated':[],'represented':[]}#空
    省略=[{'absolutePath':文件['absolutePath'],'displayPath':文件['displayPath']} for 文件 in 文件们[:-1]]#其余全部省略
    原文字节=字节长度(最具体['content'])#最具体文件原文字节
    for 候选风格 in [风格,{**风格,'intro':压缩工作区上下文开场}]:#先原开场，再压缩开场
        截断文件=截断到装下(最具体,[],最大字节,省略,候选风格)#截断到能装下
        纳入字节=字节长度(截断文件['content'])#实际纳入字节
        截断=[{'displayPath':最具体['displayPath'],'originalBytes':原文字节,'includedBytes':纳入字节}]#截断记账
        文本=组装指令文本([截断文件],最大字节,省略,截断,候选风格)#试渲染
        if 字节长度(文本)<=最大字节:#装得下
            代表=[最具体] if 纳入字节>0 or 原文字节==0 else []#有内容或本就是空文件才算被代表
            return {'text':文本,'omitted':省略,'truncated':截断,'represented':代表}#返回截断结果
    截断=[{'displayPath':最具体['displayPath'],'originalBytes':原文字节,'includedBytes':0}]#零纳入的截断记账
    压缩通知=转义指令帧正文(预算标记文本(最大字节,省略,截断))#仅诊断标记
    带标题=转义指令帧正文('\n\n'.join([压缩通知,风格['section'](带截断内容(最具体,0))]))#标记加空内容标题
    if 字节长度(带标题)<=最大字节:#标题也装得下
        代表=[最具体] if 原文字节==0 else []#只有原本就是空文件才算被代表
        return {'text':带标题,'omitted':省略,'truncated':截断,'represented':代表}#返回带标题压缩
    文本=压缩通知 if 字节长度(压缩通知)<=最大字节 else 截断Utf8(压缩通知,最大字节)#标记本身再截
    return {'text':文本,'omitted':省略,'truncated':截断,'represented':[]}#仅通知，无代表文件

def 渲染指令变更(项们,最大字节):#渲染调和批次
    """渲染一批调和变更，只保留装得下的转移。返回受预算约束的提示词文本，以及实际被其代表的转移。"""
    按绝对={项['file']['absolutePath']:项 for 项 in 项们}#按绝对路径索引变更项
    def 章节(文件):#按文件找对应变更
        """按文件找对应变更章节。"""
        项=按绝对.get(文件['absolutePath'])#查找变更项
        return '' if 项 is None else 变更章节文本({**项,'file':文件})#找不到则空章节
    风格={'intro':'','section':章节}#变更批次风格：无开场，章节自带说明
    渲染=渲染指令上下文([项['file'] for 项 in 项们],最大字节,风格)#按预算渲染这些文件
    代表=set(文件['absolutePath'] for 文件 in 渲染['represented'])#被代表文件的绝对路径
    return {#只返回装进正文的变更
        'text':渲染['text'],#已渲染文本
        'changes':[项['change'] for 项 in 项们 if 项['file']['absolutePath'] in 代表],#原顺序过滤
    }#返回对象结束

def 渲染工作区指令集(文件们,选项):#渲染基线并返回纳入文件
    """渲染一份基线，以及在语义上被其代表的精确源文件。"""
    风格=基线风格(文件们,选项.get('replacePreviousBaseline'))#选择开场
    结果=渲染指令上下文(文件们,选项['maxBytes'],风格)#渲染
    公开={'text':结果['text'],'omitted':结果['omitted'],'truncated':结果['truncated']}#公开渲染
    return {'rendered':公开,'included':结果['represented']}#代表文件即纳入集

def 渲染工作区上下文(文件们,选项):#只返回公开渲染
    """按确定性优先级预算渲染基线指令链。"""
    return 渲染工作区指令集(文件们,选项)['rendered']#丢掉纳入集
