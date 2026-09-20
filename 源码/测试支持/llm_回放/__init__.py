import json,os,re,time,threading#JSON、文件、正则、节拍与挂起
from ...模型后端.llm import (#LLM 运行时
    语言模型适配器,语言模型错误,解析重试政策,断言永不,
)#LLM 导入
from ...模型后端.llm.助手流 import 展开助手流#展开嵌入助手流
from ...模型后端.llm.标识构造 import 推理力度标识#推理力度
from ...模型后端.llm.内容 import 请求图片句柄文案,卸载图片文案#图像句柄与卸载文案
from ...内核.会话 import 会话格式版本#当代版本
from ...会话.会话格式目录 import 会话格式目录,会话格式不支持迁移错误#格式目录

__all__=[#仅中文公开名
    '名称','依赖','应用','解析会话日志','解析会话头','派生回放脚本',
    '解析脚本条目','加载回放脚本','加载会话脚本','安装LLM回放',
    '准备会话快照夹具供比较',
]#公开面结束

名称='llm-replay'#插件名
依赖=['llm']
打包块行类型=frozenset(['text-chunks','reasoning-chunks','tool-call-chunks'])#打包块行类型
回放分片类型=frozenset([#合法分片类型
    'block-start','text-delta','reasoning-delta','tool-call-delta','block-end','usage','finish',
])#分片类型结束
请求占位开='{{fromRequest:'#占位开
请求占位闭='}}'#占位闭
工具令牌='{{tools}}'#工具 schema 令牌
工作目录令牌模式=re.compile(r'^\{\{cwd\}\}(?:/|$)')#cwd 令牌

if 会话格式目录.当前版本!=会话格式版本:#目录版本须与会话包一致
    raise Exception(#抛出版本不匹配
        f'llm-replay: format catalog v{会话格式目录.当前版本} '
        +f'does not match Session v{会话格式版本}',
    )#版本检查结束

def 规范化投影头(头):#规范化投影头
    """在物理校验前物化仅 fixture 的头省略与令牌。"""
    归一=dict(头)#浅拷贝
    if 头.get('version')==0 and 'delegationDepth' not in 头:#v0 缺深度
        归一['delegationDepth']=0#补零
    cwd=头.get('cwd')#cwd
    if isinstance(cwd,str) and 工作目录令牌模式.match(cwd):#cwd 令牌
        归一['cwd']=cwd.replace('{{cwd}}','/dsh-snapshot-cwd')#替换占位
    return 归一#返回头

def 规范化投影行(源):#规范化投影行
    """省略精确请求工具伴随令牌，并为校验物化投影工具名。"""
    记录=dict(源)#浅拷贝
    if 记录.get('type')!='request/header':#非请求头
        return 记录#原样
    数据=记录.get('data')#data
    if not isinstance(数据,dict):#非法 data
        return 记录#原样
    头=数据.get('header')#header
    if not isinstance(头,dict):#非法 header
        return 记录#原样
    工具=头.get('tools')#tools
    归一头=dict(头)#浅拷贝 header
    if 工具==工具令牌:#令牌则删键
        归一头.pop('tools',None)#删除 tools
    elif isinstance(工具,list) and len(工具)>0 and all(isinstance(名,str) and 名!='' for 名 in 工具):#工具名数组
        归一头['tools']=[{'name':名,'description':'','parameters':{}} for 名 in 工具]#物化工具
    else:#其他形态
        return 记录#原样返回
    记录['data']={**数据,'header':归一头}#写回 data
    return 记录#返回记录

def 恢复投影请求头(目标,源):#恢复投影请求头
    """恢复仅为满足已发布格式校验而物化的 fixture 令牌。"""
    目标数据=目标.get('data') if isinstance(目标.get('data'),dict) else {}#目标 data
    源数据=源.get('data') if isinstance(源.get('data'),dict) else {}#源 data
    目标头=目标数据.get('header') if isinstance(目标数据.get('header'),dict) else {}#目标 header
    源头=源数据.get('header') if isinstance(源数据.get('header'),dict) else {}#源 header
    源工具=源头.get('tools')#源 tools
    if 源工具!=工具令牌:#非令牌
        return 目标#原样
    return {#恢复 tools 令牌
        **目标,#保留目标
        'data':{#替换 data
            **目标数据,#保留 data
            'header':{**目标头,'tools':源工具},#恢复 tools
        },#data 结束
    }#返回结束

def 物理行基数(行):#物理行基数
    """返回一个物理行对确定性序号补全贡献多少逻辑事件。"""
    if 行.get('type') not in 打包块行类型:#非打包为 1
        return 1#1
    数据=行.get('data')#data
    if not isinstance(数据,dict):#非法为 1
        return 1#1
    载荷=数据.get('args' if 行.get('type')=='tool-call-chunks' else 'texts')#载荷
    return len(载荷) if isinstance(载荷,list) and len(载荷)>0 else 1#按长度

def 夹具格式错误(错误,头行,行号表,事件行号,物理行=None):#fixture 格式错误
    """附加最近物理源行，同时保留不支持迁移的分类。"""
    细节=错误.args[0] if isinstance(错误,BaseException) and 错误.args else str(错误)#详情
    原因=getattr(错误,'__cause__',None)#原因
    定位=原因.args[0] if isinstance(原因,BaseException) and 原因.args else 细节#定位串
    已发布行=re.match(r'^released Session row (\d+)',str(定位))#已发布行匹配
    事件=re.search(r'Session event (\d+)',str(定位)) or re.search(r' at seq (\d+)',str(定位)) or re.search(r'inherited Session cut (\d+)',str(定位))#事件匹配
    if 物理行 is not None:#物理行
        行号=行号表[物理行]#行号
    elif 已发布行 is not None:#已发布行
        下标=int(已发布行.group(1))#下标
        行号=行号表[下标] if 下标<len(行号表) else 头行#行号
    elif 事件 is None:#头
        行号=头行#头
    else:#事件行
        下标=int(事件.group(1))#下标
        行号=事件行号[下标] if 下标<len(事件行号) else 头行#事件行
    消息=f'session snapshot line {行号}: {细节}'#组装消息
    if isinstance(错误,会话格式不支持迁移错误):#不支持迁移
        return 会话格式不支持迁移错误(消息,错误)#同型包装
    return _带原因异常(消息,错误)#普通错误

def _带原因异常(消息,原因):#包装异常并保留 cause
    """创建 Exception 并挂上 __cause__。"""
    错误=Exception(消息)#普通错误
    错误.__cause__=原因#原因
    return 错误#返回

def 物化解析会话夹具(制品,源头):#物化解析视图
    """从已迁移制品物化公共回放视图。"""
    头=制品['header'] if isinstance(制品,dict) else getattr(制品,'header',{})#头
    继承=制品['inheritedEventCount'] if isinstance(制品,dict) else getattr(制品,'inheritedEventCount',0)#继承数
    事件=制品['events'] if isinstance(制品,dict) else getattr(制品,'events',())#事件
    return {#构造对象
        'id':头.get('id') if isinstance(头,dict) else '',#会话 id
        'createdAt':头.get('createdAt') if isinstance(头,dict) else 0,#创建时间
        'inheritedEventCount':int(继承),#继承数
        'events':list(事件),#事件副本
        'artifact':制品,#制品
        'sourceHeader':源头,#源头
    }#对象结束

def 解析会话夹具(文本):#解析会话 fixture
    """解析、补全、解码并迁移一个投影快照制品，不写回其源。"""
    头行号=None#头行号
    源头=None#源头
    恢复器=None#恢复器
    行号表=[]#物理行号
    事件行号=[]#事件行号
    体种=None#体种类
    下一序号=0#下一序号
    for 索引,行 in enumerate(文本.splitlines()):#逐行扫描
        if 行.strip()=='':#空行
            continue#跳过
        try:
            值=json.loads(行)
        except json.JSONDecodeError as 错误:
            raise Exception(f'会话快照第 {索引+1} 行不是合法 JSON') from 错误
        if not isinstance(值,dict):#须为对象
            raise Exception(f'会话快照第 {索引+1} 行必须是 JSON 对象')
        行号=索引+1#行号
        if 恢复器 is None:#头行
            头行号=行号#记头行
            源头=值#记源头
            try:#创建恢复器
                恢复器=会话格式目录.创建恢复(规范化投影头(值),{'recovery':'strict','validation':'current'})#创建
            except Exception as 错误:#创建失败
                raise 夹具格式错误(错误,行号,[],[])#带行号抛错
            continue#下一行
        记录=规范化投影行(值)#规范化行
        打包=记录.get('type') in 打包块行类型#是否打包行
        序号键='seq0' if 打包 else 'seq'#序号键
        时间键='time0' if 打包 else 'time'#时间键
        有序号=序号键 in 记录#有序号否
        有时间=时间键 in 记录#有时间否
        if 有序号!=有时间:#须成对
            raise Exception(f'session snapshot line {行号} must contain both {序号键} and {时间键}, or neither')#成对要求
        当前体种='complete' if 有序号 else 'projected'#当前体种
        if 体种 is not None and 当前体种!=体种:#禁止混用
            raise Exception(f'session snapshot line {行号} cannot mix projected and complete body rows')#混用错误
        体种=当前体种#记录体种
        if 当前体种=='projected':#投影行补全
            记录[序号键]=下一序号#写入序号
            记录[时间键]=0#写入零时间
        基数=物理行基数(记录)#物理行基数
        行号表.append(行号)#记录行号
        事件行号.extend([行号]*基数)#事件行号
        下一序号+=基数#推进序号
        try:#解码行
            恢复器.decodeRow(记录)#解码
        except Exception as 错误:#解码失败
            raise 夹具格式错误(错误,头行号,行号表,事件行号,len(行号表)-1)#带行号
    if 恢复器 is None or 源头 is None or 头行号 is None:#缺头
        raise Exception('会话快照必须以会话头开始')#缺头
    try:#完成恢复
        return 物化解析会话夹具(恢复器.finish(),源头)#物化视图
    except Exception as 错误:#完成失败
        raise 夹具格式错误(错误,头行号,行号表,事件行号)#带行号抛错

def 编码当前会话快照夹具(文本,已解析):#编码当前快照
    """编码一个已迁移 fixture 同时保留投影 cwd 与请求工具令牌。"""
    制品=已解析['artifact']#制品
    头字段=制品['header'] if isinstance(制品,dict) else getattr(制品,'header')#头
    继承=制品['inheritedEventCount'] if isinstance(制品,dict) else getattr(制品,'inheritedEventCount')#继承
    事件列表=制品['events'] if isinstance(制品,dict) else getattr(制品,'events')#事件
    头=dict(会话格式目录.编码当代头(头字段,继承))#编码当前头
    源cwd=已解析['sourceHeader'].get('cwd')#源 cwd
    if isinstance(源cwd,str) and 工作目录令牌模式.match(源cwd):#恢复令牌
        头['cwd']=源cwd#恢复
    源请求=[json.loads(行) for 行 in 文本.splitlines() if 行.strip()!=''][1:]#体行
    源请求=[行 for 行 in 源请求 if isinstance(行,dict) and 行.get('type')=='request/header']#仅请求头
    请求游标=0#请求游标
    输出行=[json.dumps(头,ensure_ascii=False,separators=(',',':'))]#头
    for 事件 in 事件列表:#逐事件
        已编码=会话格式目录.编码当代事件(事件)#编码
        类型=事件.get('type') if isinstance(事件,dict) else getattr(事件,'type',None)#类型
        if 类型!='request/header':#非请求头
            输出行.append(json.dumps(已编码,ensure_ascii=False,separators=(',',':')))#编码行
            continue#下一项
        源=源请求[请求游标]#对齐源
        请求游标+=1#推进
        输出行.append(json.dumps(恢复投影请求头(已编码 if isinstance(已编码,dict) else dict(已编码),源),ensure_ascii=False,separators=(',',':')))#恢复令牌
    输出='\n'.join(输出行)#拼 JSONL
    return 输出+('\n' if 文本.endswith('\n') else '')#保留尾换行

def 准备会话快照夹具供比较(文本):#准备快照比较
    """在内存中把一个持久或投影快照 fixture 转为当前物理格式，供期望输出比较。"""
    已解析=解析会话夹具(文本)#解析 fixture
    return 编码当前会话快照夹具(文本,已解析)#编码当前格式

def 请求图像句柄文本(引用,版本,访问=None):#请求图像句柄文本
    """兼容旧名；权威实现见 模型后端.llm.内容.请求图片句柄文案。"""
    return 请求图片句柄文案(引用,版本,访问)#委托

def 是否记录(值):#是否字典
    """值是否为非数组对象。"""
    return isinstance(值,dict)#字典

def 恰好这些键(值,键列表):#精确键集
    """精确键检查。"""
    return len(值)==len(键列表) and all(键 in 值 for 键 in 键列表)#匹配

def 解析会话日志(文本):#解析会话日志
    """将会话 .jsonl 缓冲解析为事件列表（经格式目录 createRestore 迁移）。"""
    return 解析会话夹具(文本)['events']#返回事件

def 解析会话头(文本):#解析会话头
    """从 JSONL 头读取回放身份与排序事实。"""
    已解析=解析会话夹具(文本)#解析 fixture
    return {#返回
        'id':已解析['id'],#会话 id
        'createdAt':已解析['createdAt'],#创建时间
        'inheritedEventCount':已解析['inheritedEventCount'],#继承事件数
    }#返回结束

def 派生回放脚本(事件列表):#派生回放脚本
    """从已记录会话日志重建每 stream() 回放脚本。"""
    脚本=[]#脚本
    def 关闭(键,分片列表):#关闭一次模型调用
        """压入分片条目或拒绝缺 finish。"""
        if len(分片列表)==0:#空则跳过
            return#跳过
        末=分片列表[-1]#末分片
        类型=末.get('type') if isinstance(末,dict) else getattr(末,'type',None)#类型
        if 类型!='finish':#缺 finish
            raise Exception(#需覆盖
                f'llm-replay: model call {键} ended without a finish chunk (a thrown stream); '
                +'this scenario needs a replay.override.json sidecar',
            )#缺 finish 需覆盖
        脚本.append({'kind':'chunks','chunks':list(分片列表)})#压入分片条目
    for 事件 in 事件列表:#遍历事件
        类型=事件.get('type') if isinstance(事件,dict) else getattr(事件,'type',None)#事件类型
        数据=事件.get('data') if isinstance(事件,dict) else getattr(事件,'data',None)#事件数据
        if 类型=='compaction/summary':#压缩摘要
            if isinstance(数据,dict) and 数据.get('llmStreamCall') is True:#LLM 流调用
                if 'rawOutput' not in 数据:#缺 rawOutput
                    raise Exception('llm-replay: compaction/summary marks an LLM stream call without rawOutput')#缺 rawOutput
                分片列表=[]#分片
                for 索引,块 in enumerate(数据['rawOutput']):#逐块
                    块类型=块.get('type') if isinstance(块,dict) else getattr(块,'type',None)#块类型
                    分片列表.append({'type':'block-start','index':索引,'blockType':块类型})#块开始
                    分片列表.append({'type':'block-end','index':索引,'block':块})#块结束
                if 数据.get('usage') is not None:#用量
                    分片列表.append({'type':'usage','usage':数据['usage']})#用量
                分片列表.append({'type':'finish','reason':{'kind':'stop'}})#结束
                脚本.append({'kind':'chunks','chunks':分片列表})#压入压缩调用
            continue#下一项
        if 类型!='assistant/message' and 类型!='assistant/attempt':#非助手结算
            continue#跳过
        回合=数据.get('turn') if isinstance(数据,dict) else getattr(数据,'turn',None)#回合
        步进=数据.get('step') if isinstance(数据,dict) else getattr(数据,'step',None)#步进
        流=数据.get('stream') if isinstance(数据,dict) else getattr(数据,'stream',None)#嵌入流
        分片列表=[成员['chunk'] for 成员 in 展开助手流(流 or [])]#展开分片
        关闭(f'{回合}/{步进}',分片列表)#关闭一次调用
    return 脚本#返回脚本

def 收集字符串(值,输出):#收集字符串叶子
    """按遍历顺序收集 JSON 兼容值的每个字符串叶子。"""
    if isinstance(值,str):#字符串
        输出.append(值)#叶子
        return
    if isinstance(值,list):#数组
        for 项 in 值:#递归
            收集字符串(项,输出)#递归
        return
    if 是否记录(值):#对象
        for 项 in 值.values():#递归
            收集字符串(项,输出)#递归

def 解析请求占位(模式,语料):#对照请求语料解析占位
    """对照请求语料解析一个占位模式；最后一次匹配胜出。"""
    import re as 正则#编译模式
    try:
        编译=正则.compile(模式)
    except 正则.error as 错误:
        raise Exception(f'llm-replay: fromRequest 模式非法 {模式!r}: {错误}')
    末次=None#末次匹配
    for 匹配 in 编译.finditer(语料):#逐匹配
        末次=匹配#取末次
    if 末次 is None:#无匹配
        raise Exception(f'llm-replay: fromRequest pattern {模式!r} matched nothing in the request')#无匹配
    return 末次.group(1) if 末次.lastindex else 末次.group(0)#首捕获或整匹配

def 替换字符串占位(文本,语料):#替换占位
    """替换脚本字符串中的每个 {{fromRequest:<pattern>}}。"""
    结果=''#输出
    游标=0#游标
    while True:#扫描
        开=文本.find(请求占位开,游标)#找开
        if 开==-1:#无更多
            return 结果+文本[游标:]#收尾
        闭=文本.find(请求占位闭,开+len(请求占位开))#找闭
        if 闭==-1:#未闭合
            raise Exception(f'llm-replay: fromRequest placeholder is unterminated in {文本!r}')#未闭合
        while 闭+len(请求占位闭)<len(文本) and 文本[闭+len(请求占位闭)]=='}':#连续 }
            闭+=1#延长
        模式=文本[开+len(请求占位开):闭]#取出模式
        结果+=文本[游标:开]+解析请求占位(模式,语料)#替换
        游标=闭+len(请求占位闭)#推进

def 替换值占位(值,语料):#深拷贝并解析占位
    """深拷贝 JSON 兼容值并解析脚本占位。"""
    if isinstance(值,str):#字符串
        return 替换字符串占位(值,语料) if 请求占位开 in 值 else 值#替换或原样
    if isinstance(值,list):#数组
        return [替换值占位(项,语料) for 项 in 值]#映射
    if 是否记录(值):#对象
        return {键:替换值占位(项,语料) for 键,项 in 值.items()}#递归
    return 值#原样

def 解析脚本条目(条目,消息列表):#解析脚本占位
    """对照实时请求解析 {{fromRequest:<regex>}} 占位。"""
    if 请求占位开 not in json.dumps(条目,ensure_ascii=False):#无占位
        return 条目#原样
    叶子=[]#叶子
    收集字符串(消息列表,叶子)#收集叶子
    return 替换值占位(条目,'\n'.join(叶子))#解析

def 物化会话令牌(条目,实时会话标识列表):#物化会话令牌
    """用实时会话 id 替换 {{session:N}}。"""
    if '{{session:' not in json.dumps(条目,ensure_ascii=False):#无会话令牌
        return 条目#原样
    import re as 正则#替换
    def 替换(值):#递归替换
        """替换字符串中的会话令牌。"""
        if isinstance(值,str):#字符串
            def 一次(匹配):#单次
                """按序取实时 id。"""
                序=int(匹配.group(1))#序号
                实时=实时会话标识列表[序-1] if 序-1<len(实时会话标识列表) else None#实时 id
                if 实时 is None:#未绑定
                    raise Exception(f'llm-replay: session token {{{{session:{序}}}}} was used before that recorded session bound')#未绑定
                return 实时#返回
            return 正则.sub(r'\{\{session:([1-9]\d*)\}\}',一次,值)#替换
        if isinstance(值,list):#数组
            return [替换(项) for 项 in 值]#映射
        if 是否记录(值):#对象
            return {键:替换(项) for 键,项 in 值.items()}#递归
        return 值#原样
    return 替换(条目)#返回

def 推断已启动子智能体(消息列表,实时会话标识列表):#推断子 id
    """从工具结果文本学习子 id。"""
    import re as 正则#匹配
    叶子=[]#叶子
    收集字符串(消息列表,叶子)#收集
    for 叶 in 叶子:#逐叶
        for 匹配 in 正则.finditer(r'started subagent ([^\s"\'<>]+)',叶):#匹配
            标识=匹配.group(1)#子 id
            if 标识 in 实时会话标识列表:#已有
                continue#跳过
            索引=next((候选 for 候选,值 in enumerate(实时会话标识列表) if 候选>0 and 值 is None),-1)#下一空位子槽
            if 索引<0:#无槽
                return
            实时会话标识列表[索引]=标识#预填

def 非法覆盖(文件,位置,细节):#覆盖非法
    """抛出覆盖非法。"""
    raise Exception(f'llm-replay: invalid override {文件}: {位置} {细节}')#覆盖非法

def 读取分片列表(值,文件,位置):#读分片数组
    """校验 StreamChunk 数组。"""
    if not isinstance(值,list):#必须数组
        非法覆盖(文件,位置,'chunks must be an array')#必须数组
    for 索引,分片 in enumerate(值):#逐项
        if not 是否记录(分片) or not isinstance(分片.get('type'),str) or 分片['type'] not in 回放分片类型:#未知
            非法覆盖(文件,f'{位置}.chunks[{索引}]','must have a known StreamChunk type')#未知分片类型
    return 值#断言分片数组

def 读回放条目(值,文件,位置):#读回放条目
    """解析一个 ReplayEntry。"""
    if not 是否记录(值):#必须对象
        非法覆盖(文件,位置,'must be an object')#必须对象
    种类=值.get('kind')#种类
    if 种类=='chunks':#分片
        if not 恰好这些键(值,['kind','chunks']):#字段非法
            非法覆盖(文件,位置,'has invalid chunks-entry fields')#非法
        return {'kind':'chunks','chunks':读取分片列表(值['chunks'],文件,位置)}#分片条目
    if 种类=='throw':#抛错
        已接受=值.get('accepted')#是否已接受
        键列表=['kind','chunks','message','code']+(['accepted'] if 已接受 is not None else [])#键集
        if not 恰好这些键(值,键列表):#字段非法
            非法覆盖(文件,位置,'has invalid throw-entry fields')#非法
        if not isinstance(值.get('message'),str) or 值['message']=='':#消息非法
            非法覆盖(文件,位置,'message must be a non-empty string')#非法
        if not isinstance(值.get('code'),str) or 值['code']=='':#码非法
            非法覆盖(文件,位置,'code must be a non-empty string')#非法
        if 已接受 is not None and not isinstance(已接受,bool):#accepted 非法
            非法覆盖(文件,位置,'accepted must be a boolean')#非法
        条目={'kind':'throw','chunks':读取分片列表(值['chunks'],文件,位置),'message':值['message'],'code':值['code']}#抛错条目
        if 已接受 is not None:#可选
            条目['accepted']=已接受#写入
        return 条目#返回
    if 种类=='hang':#挂起
        就绪=值.get('readyFile')#就绪文件
        键列表=['kind']+(['readyFile'] if 就绪 is not None else [])#键集
        if not 恰好这些键(值,键列表):#字段非法
            非法覆盖(文件,位置,'has invalid hang-entry fields')#非法
        if 就绪 is not None and (not isinstance(就绪,str) or 就绪==''):#就绪非法
            非法覆盖(文件,位置,'readyFile must be a non-empty string')#非法
        return {'kind':'hang',**({'readyFile':就绪} if 就绪 is not None else {})}#挂起条目
    非法覆盖(文件,位置,f'has unknown kind {种类!r}')#未知 kind

def 读覆盖文档(值,文件):#读覆盖文档
    """解析覆盖伴随文档。"""
    if isinstance(值,list):#整脚本替换
        return [读回放条目(条目,文件,f'entry {索引}') for 索引,条目 in enumerate(值)]#整替换
    if not 是否记录(值) or not 恰好这些键(值,['patches']) or not isinstance(值.get('patches'),list):#形态非法
        非法覆盖(文件,'document','must be a ReplayEntry[] or { patches: [...] }')#非法
    补丁列表=[]#补丁列表
    for 索引,项 in enumerate(值['patches']):#逐补丁
        位置=f'patch {索引}'#位置
        if not 是否记录(项) or not 恰好这些键(项,['at','entry']):#字段非法
            非法覆盖(文件,位置,'must contain exactly at and entry')#非法
        位置索引=项['at']#索引
        if not isinstance(位置索引,int) or isinstance(位置索引,bool) or 位置索引<0:#非法
            非法覆盖(文件,位置,'at must be a non-negative safe integer')#非法
        补丁列表.append({'at':位置索引,'entry':读回放条目(项['entry'],文件,f'{位置}.entry')})#补丁
    return {'patches':补丁列表}#增补形态

def 读主夹具(配置):#读主 JSONL，整脚本覆盖占用同路径时跳过
    """主 JSONL 存在且不是覆盖文件时解析。"""
    文件=配置['file']#主路径
    if not os.path.exists(文件) or 文件==配置.get('overrideFile'):#缺失或同路径覆盖
        return None#跳过
    with open(文件,'r',encoding='utf-8') as 句柄:#读
        return 解析会话夹具(句柄.read())#夹具

def 从夹具派生脚本(文件,夹具):#已迁移夹具派生
    """夹具缺席则失败。"""
    if 夹具 is None:#缺失
        raise Exception(f'llm-replay: fixture not found: {文件} — run `pnpm run test:snapshot:record` first')#缺失
    return 派生回放脚本(夹具['events'])#派生

def 解析回放脚本(配置,夹具):#覆盖或从夹具派生
    """有覆盖则整替换或按索引补丁。"""
    覆盖=配置.get('overrideFile')#覆盖路径
    if 覆盖 is not None and os.path.exists(覆盖):#有覆盖
        with open(覆盖,'r',encoding='utf-8') as 句柄:#读覆盖
            文档=读覆盖文档(json.loads(句柄.read()),覆盖)#读覆盖
        if isinstance(文档,list):#整替换
            return 文档#整替换
        脚本=从夹具派生脚本(配置['file'],夹具)#派生基线
        派生长度=len(脚本)#长度
        已见=set()#已见索引
        for 补丁 in 文档['patches']:#逐补丁
            if 补丁['at']>派生长度:#越界
                raise Exception(#越界
                    f"llm-replay: override patch index {补丁['at']} out of range "
                    +f"(derived script has {派生长度} call(s); == length appends): {覆盖}",
                )#越界
            if 补丁['at'] in 已见:#重复
                raise Exception(f"llm-replay: duplicate override patch index {补丁['at']}: {覆盖}")#重复
            已见.add(补丁['at'])#登记
            if 补丁['at']==派生长度:#追加
                脚本.append(补丁['entry'])#追加
            else:#替换
                脚本[补丁['at']]=补丁['entry']#应用补丁
        return 脚本#返回
    return 从夹具派生脚本(配置['file'],夹具)#无覆盖则派生

def 从文件派生脚本(文件):#从 JSONL 派生
    """从会话 JSONL 派生主脚本。"""
    if not os.path.exists(文件):#缺失
        raise Exception(f'llm-replay: fixture not found: {文件} — run `pnpm run test:snapshot:record` first')#缺失
    with open(文件,'r',encoding='utf-8') as 句柄:#读文件
        return 派生回放脚本(解析会话日志(句柄.read()))#解析并派生

def 加载回放脚本(配置):#加载主回放脚本
    """加载主会话的回放脚本。"""
    return 解析回放脚本(配置,读主夹具(配置))#主脚本

def 子脚本排序键(项):
    """按创建时刻与录制 id 排序。"""
    return (项['createdAt'],项['recordedId'])

def 加载会话脚本(配置):#加载主与子脚本
    """按绑定顺序加载主与子脚本。"""
    主夹具=读主夹具(配置)#主夹具
    主条目=解析回放脚本(配置,主夹具)#主条目
    主头=主夹具 if 主夹具 is not None else {'id':'','createdAt':0}#无头则默认
    主={'recordedId':主头['id'],'createdAt':主头['createdAt'],'entries':主条目,'primary':True}#主脚本
    子项列表=[]#子脚本
    for 子文件 in 配置.get('childFiles') or []:#逐子
        if not os.path.exists(子文件):#缺失
            raise Exception(f'llm-replay: child fixture not found: {子文件} — re-record the scenario')#缺失
        with open(子文件,'r',encoding='utf-8') as 句柄:#读子
            文本=句柄.read()#文本
        头=解析会话头(文本)#头
        自有事件=解析会话日志(文本)[头['inheritedEventCount']:]#自有事件
        子项列表.append({'recordedId':头['id'],'createdAt':头['createdAt'],'entries':派生回放脚本(自有事件),'primary':False})#子脚本
    子项列表.sort(key=子脚本排序键)#按创建序
    return [主,*子项列表]#主在前

class 回放适配器(语言模型适配器):#回放适配器
    """使已配置提供方目录可发现、且无提供方 I/O 的回放适配器。"""

    def __init__(自身,提供方列表,回放):#构造
        """记下提供方映射与回放实现。"""
        super().__init__()#基类
        自身._providers={项['id']:项 for 项 in 提供方列表}#提供方映射
        自身._replay=回放#回放实现

    def providerInfo(自身,提供方):#提供方简介
        """咨询信息。"""
        if 提供方 not in 自身._providers:#未知
            return super().providerInfo(提供方)#基类
        配置=自身._providers[提供方]#配置
        return {'id':提供方,'name':配置.get('name') or 提供方}#咨询信息

    def providerRetryPolicy(自身,提供方):#重试政策
        """可选提供方重试政策。"""
        if 提供方 not in 自身._providers:#未知
            return super().providerRetryPolicy(提供方)#基类
        配置=自身._providers[提供方]#配置
        if 'retryPolicy' not in 配置:#无
            return None#无
        政策=配置['retryPolicy']#政策
        return 解析重试政策(政策,f'llm-replay: provider "{提供方}" retryPolicy')#解析

    def imageRequestPricing(自身,提供方,模型):#图像计价
        """可选平坦视觉 token 价。"""
        配置=自身._providers.get(提供方)#配置
        模型列表=配置.get('models') if 配置 else None#模型列表
        命中=next((候 for 候 in (模型列表 or []) if 候.get('id')==模型),None)#命中模型
        视觉=None if 命中 is None else 命中.get('imageRequestTokens')#视觉价
        if 视觉 is None:#无
            return None#无
        def 计价(图像列表):#计价函数
            """按出现计价；卸载图视觉 token 为 0。"""
            结果=[]#行
            for 项 in 图像列表:#逐项
                if isinstance(项,dict):#带附件与卸载标记
                    引用=项.get('attachment')#附件
                    卸载=项.get('offloaded') is True#卸载
                else:#旧式裸引用
                    引用=项#引用
                    卸载=False#未卸载
                if 卸载:#卸载图
                    结果.append({'visualTokens':0,'text':卸载图片文案(引用)})#零视觉
                else:#在线附件
                    结果.append({'visualTokens':视觉,'text':请求图像句柄文本(引用,{'width':引用.get('width') if isinstance(引用,dict) else None,'height':引用.get('height') if isinstance(引用,dict) else None})})#计价
            return 结果#列表
        return {'priceImages':计价}#图像计价

    def listModels(自身,提供方):#列模型
        """列出咨询模型。"""
        if 提供方 not in 自身._providers:#未知
            return []#空
        配置=自身._providers[提供方]#配置
        结果=[]#结果
        for 模型 in 配置.get('models') or []:#逐模型
            项={'provider':提供方,'id':模型['id'],'name':模型.get('name') or 模型['id']}#基础
            if 模型.get('description') is not None:#描述
                项['description']=模型['description']#写入
            if 模型.get('inputModalities') is not None:#模态
                项['inputModalities']=list(模型['inputModalities'])#写入
            结果.append(项)#追加
        return 结果#列模型

    def resolveModel(自身,提供方,模型):#解析模型
        """解析模型元数据。"""
        if 提供方 not in 自身._providers:#未知
            return {'provider':提供方,'id':模型,'name':模型}#默认
        配置=自身._providers[提供方]#配置
        命中=next((候 for 候 in (配置.get('models') or []) if 候.get('id')==模型),None)#命中
        结果={'provider':提供方,'id':模型,'name':(命中.get('name') if 命中 else None) or 模型}#基础
        if 命中 is not None:#有配置
            if 命中.get('description') is not None:#描述
                结果['description']=命中['description']#写入
            if 命中.get('inputModalities') is not None:#模态
                结果['inputModalities']=list(命中['inputModalities'])#写入
            if 命中.get('contextWindow') is not None:#上下文
                结果['context']={'contextWindow':命中['contextWindow']}#写入
            if 命中.get('defaultMaxTokens') is not None:#默认上限
                结果['defaultMaxTokens']=命中['defaultMaxTokens']#写入
            if 命中.get('systemPromptUpdate') is not None:#系统提示词更新
                结果['systemPromptUpdate']=命中['systemPromptUpdate']#写入
            if 命中.get('reasoningEfforts') is not None:#推理
                推理={'efforts':[{'id':推理力度标识(标识),'name':标识} for 标识 in 命中['reasoningEfforts']]}#力度
                if 命中.get('defaultReasoningEffort') is not None:#默认力度
                    推理['defaultEffort']=推理力度标识(命中['defaultReasoningEffort'])#写入
                结果['reasoning']=推理#写入
        return 结果#解析模型

    def stream(自身,选项):#流式回放
        """委托回放实现。"""
        return 自身._replay(选项)#委托回放

def 节拍延迟(毫秒,信号):#节拍等待
    """等待毫秒；信号中止则抛 aborted。"""
    if 毫秒<=0:#无等待
        return
    截止=time.monotonic()+毫秒/1000#截止
    while time.monotonic()<截止:#等待
        if 信号 is not None and getattr(信号,'aborted',False):#中止
            raise Exception('aborted')#中止
        time.sleep(0.01)#短睡

def 回放条目流(条目,信号,节拍毫秒):#回放条目生成器
    """回吐已记录流，像真实适配器一样遵守中止。"""
    种类=条目['kind']#种类
    if 种类=='chunks':#分片
        for 分片 in 条目['chunks']:#逐分片
            if 信号 is not None and getattr(信号,'aborted',False):#中止
                raise Exception('aborted')#中止
            节拍延迟(节拍毫秒,信号)#节拍
            yield 分片#产出
        return
    if 种类=='throw':#抛错
        for 分片 in 条目['chunks']:#先发前缀
            if 信号 is not None and getattr(信号,'aborted',False):#中止
                raise Exception('aborted')#中止
            节拍延迟(节拍毫秒,信号)#节拍
            yield 分片#产出
        raise 语言模型错误(条目['message'],条目['code'])#抛已记录错误
    if 种类=='hang':#挂起
        yield {'type':'block-start','index':0,'blockType':'text'}#块开始
        yield {'type':'text-delta','index':0,'text':'partial'}#部分文本
        if 条目.get('readyFile') is not None:#就绪标记
            with open(条目['readyFile'],'w',encoding='utf-8') as 句柄:#写空文件
                句柄.write('')#就绪标记
        门闩=threading.Event()#挂起门闩
        def 中止回调():#中止
            """放行拒绝。"""
            门闩.set()#放行
        if 信号 is not None:#有信号
            if getattr(信号,'aborted',False):#已中止
                raise Exception('aborted')#中止
            if hasattr(信号,'addEventListener'):#DOM 风格
                信号.addEventListener('abort',中止回调,{'once':True})#监听
            elif hasattr(信号,'add_callback'):#回调风格
                信号.add_callback(中止回调)#监听
        门闩.wait()#等中止
        raise Exception('aborted')#中止
    断言永不(条目,'llm-replay replay entry')#穷尽

def 提供方已接受(条目):#是否到达 2xx 后提交点
    """脚本化提供方调用是否到达在线适配器的 2xx 后提交点。"""
    种类=条目['kind']#种类
    if 种类 in ('chunks','hang'):#成功类
        return True#接受
    if 种类=='throw':#抛错
        return 条目['accepted'] if 'accepted' in 条目 else len(条目['chunks'])>0#accepted 或有前缀
    return 断言永不(条目,'llm-replay acceptance entry')#穷尽

def 安装LLM回放(上下文,配置):#安装回放
    """安装每会话位置回放。"""
    节拍=配置.get('paceMs') or 0#节拍
    if not isinstance(节拍,int) or isinstance(节拍,bool) or 节拍<0:#非法
        raise Exception(f"llm-replay: paceMs must be a non-negative integer, got {配置.get('paceMs')!r}")#非法
    脚本列表=加载会话脚本(配置)#有序脚本
    绑定={}#绑定表
    实时会话标识列表=[None]*len(脚本列表)#实时 id 槽
    下一脚本=[0]#下一脚本索引
    匿名='\0anon\0'#无 sessionId 调用的键
    def 回放(选项):#回放实现
        """按会话推进游标并产出流。"""
        键=选项.get('sessionId') or 匿名#绑定键
        状态=绑定.get(键)#已绑定
        未记录=False#是否未记录会话
        if 状态 is None:#新会话
            if 下一脚本[0]>=len(脚本列表):#超出
                未记录=True#未记录
                状态={'entries':[],'cursor':0}#空
            else:#认领
                脚本索引=下一脚本[0]#索引
                下一脚本[0]+=1#推进
                状态={'entries':脚本列表[脚本索引]['entries'],'cursor':0}#绑定态
                绑定[键]=状态#绑定
                if 键!=匿名:#记录实时 id
                    实时会话标识列表[脚本索引]=键#记录
        已见=下一脚本[0]#已见脚本数
        总数=len(脚本列表)#总脚本
        索引=状态['cursor']#当前游标
        状态['cursor']=索引+1#推进游标
        条目=状态['entries'][索引] if 索引<len(状态['entries']) else None#条目
        def 生成():#生成器
            """产出回放分片。"""
            if 未记录:#未记录会话
                raise Exception(#未记录
                    f'llm-replay: a model call arrived from an unrecorded session (#{已见+1}); '
                    +f'the scenario recorded only {总数} session(s) — re-record it',
                )#未记录
            if 条目 is None:#耗尽
                raise Exception(#耗尽
                    f'llm-replay: script exhausted — session requested model call #{索引+1} '
                    +f"but its script has only {len(状态['entries'])}; re-record the scenario",
                )#耗尽
            推断已启动子智能体(选项.get('messages'),实时会话标识列表)#预填子 id
            已解析=解析脚本条目(物化会话令牌(条目,实时会话标识列表),选项.get('messages'))#解析占位
            if 选项.get('provider')=='deepseek-official' and 提供方已接受(已解析):#扩展副作用
                扩展=上下文.获取服务('deepseekLlmApiExtensions')#扩展
                if 扩展 is not None:#有扩展
                    信号=选项.get('signal')#信号
                    准备=扩展.prepare({#准备
                        'body':{'messages':[]},#空正文
                        'signal':信号,#信号
                        **({'sessionId':str(选项['sessionId'])} if 选项.get('sessionId') is not None else {}),#会话
                        **({'purpose':选项['purpose']} if 选项.get('purpose') is not None else {}),#用途
                    })#准备
                    准备.accept()#接受水位
            yield from 回放条目流(已解析,选项.get('signal'),节拍)#回放条目
        return 生成()#返回生成器
    提供方列表=配置.get('providers') or []#提供方
    if len(提供方列表)>0:#路由适配器
        拆除=上下文.llm.registerAdapter([项['id'] for 项 in 提供方列表],回放适配器(提供方列表,回放))#注册
    else:#catch-all 瀑布
        def 回放流(选项,下一):
            """用回放脚本代替下游流。"""
            return 回放(选项)#回放
        拆除=上下文.监听('llm/stream',回放流)#瀑布
    def 断言已消费():#断言已消费
        """拆除时消费检查。"""
        问题=[]#问题
        if 下一脚本[0]<len(脚本列表):#未绑定
            问题.append(f'{len(脚本列表)-下一脚本[0]} recorded script(s) never bound to a live session')#未绑定
        for 键,状态 in 绑定.items():#逐绑定
            if 状态['cursor']<len(状态['entries']):#欠载
                谁='the anonymous session' if 键==匿名 else f'session {键}'#身份
                问题.append(f"{谁} consumed {状态['cursor']}/{len(状态['entries'])} recorded call(s)")#欠载
        if 问题:#有问题
            raise Exception(f"llm-replay: fixture not fully consumed — {'; '.join(问题)}; the scenario drove fewer model calls than recorded")#欠载
    return {'dispose':拆除,'assertConsumed':断言已消费}#句柄

def 校验已配置模型(提供方列表):#校验模型配置
    """校验 inputModalities 与 imageRequestTokens。"""
    for 提供方 in 提供方列表 or []:#逐提供方
        for 模型 in 提供方.get('models') or []:#逐模型
            模态=模型.get('inputModalities')#模态
            if 模态 is not None and (not isinstance(模态,list) or not all(项 in ('text','image') for 项 in 模态)):#非法
                raise Exception(#模态非法
                    f'llm-replay: provider "{提供方["id"]}" model "{模型["id"]}" inputModalities '
                    +'must be an array containing only "text" and "image"',
                )#模态非法
            图像价=模型.get('imageRequestTokens')#图像价
            if 图像价 is not None and (not isinstance(图像价,int) or isinstance(图像价,bool) or 图像价<=0):#非法
                raise Exception(#图像价非法
                    f'llm-replay: provider "{提供方["id"]}" model "{模型["id"]}" imageRequestTokens '
                    +'must be a positive safe integer',
                )#图像价非法
            if 图像价 is not None and (模态 is None or 'image' not in 模态):#需 image 模态
                raise Exception(#需 image
                    f'llm-replay: provider "{提供方["id"]}" model "{模型["id"]}" imageRequestTokens '
                    +'requires inputModalities to include "image"',
                )#需 image
            系统提示更新=模型.get('systemPromptUpdate')#系统提示词更新
            if 系统提示更新 is not None and 系统提示更新!='in-history':#仅允许 in-history
                raise Exception(#非法更新策略
                    f'llm-replay: provider "{提供方["id"]}" model "{模型["id"]}" systemPromptUpdate '
                    +'must be "in-history" when present',
                )#非法更新策略

def 应用(上下文,配置=None):#Cordis 入口
    """从配置或环境安装回放。"""
    if 配置 is None:#缺省
        配置={}#空
    文件=配置.get('file') or os.environ.get('DSH_SNAPSHOT_FILE')#主 fixture
    if 文件 is None or 文件=='':#缺路径
        raise Exception('llm-replay: 需要夹具路径（Config.file 或 $DSH_SNAPSHOT_FILE）')#缺路径
    校验已配置模型(配置.get('providers'))#校验模型
    覆盖=配置.get('overrideFile') or os.environ.get('DSH_SNAPSHOT_OVERRIDE')#覆盖
    子环境=os.environ.get('DSH_SNAPSHOT_CHILD_FILES')#子环境
    if 'childFiles' not in 配置:#从环境
        子文件=子环境.split(os.pathsep) if 子环境 else []#分隔列表
    else:
        子文件=配置['childFiles']#子文件
    回放配置={'file':文件}#回放配置
    if 覆盖:#有覆盖
        回放配置['overrideFile']=覆盖#写入
    if 子文件:#有子
        回放配置['childFiles']=子文件#写入
    if 配置.get('providers') is not None:#提供方
        回放配置['providers']=配置['providers']#写入
    if 配置.get('paceMs') is not None:#节拍
        回放配置['paceMs']=配置['paceMs']#写入
    安装LLM回放(上下文,回放配置)#安装回放

apply=应用
name=名称
inject=依赖
