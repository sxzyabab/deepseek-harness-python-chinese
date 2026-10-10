'内容块结构辅助'
import json,math#引用字符串与 base64 长度
from .永不 import 断言永不#穷尽断言

__all__=(#仅中文公开名
    '解析图片附件访问','仅文本图片文案','请求图片句柄文案','卸载图片文案',
    '内容含图片','内容含文件','文件句柄文案','投影文件为文本',
    '投影图片为仅文本','投影卸载图片','必需图片卸载',
    '卸载图片前缀张数','按政策卸载请求图片','投影工具更新',
)#公开面结束

def 引用串(值):#JSON 引用字符串
    '带引号转义'
    return json.dumps(值,ensure_ascii=False)#JSON 字符串

def 图片身份(引用):#图片身份文案
    '附件展示身份'
    if 'name' not in 引用:#无展示名
        return str(引用['attachmentId'])#只用附件 id
    return f"{引用串(引用['name'])} ({引用['attachmentId']})"#名加 id

def 扩展名(媒体类型):#媒体类型到扩展名
    '媒体类型到扩展名'
    if 媒体类型=='image/png':#png
        return '.png'#png
    if 媒体类型=='image/jpeg':#jpeg
        return '.jpg'#jpeg
    if 媒体类型=='image/webp':#webp
        return '.webp'#webp
    if 媒体类型=='image/gif':#gif
        return '.gif'#gif
    断言永不(媒体类型,'image extension')#穷尽

def 归一化访问文案(引用,访问):#归一化访问说明
    '只读副本路径与尺寸说明'
    return (
        f" Normalized copy (read-only; may be resized or re-encoded): {引用串(访问['readonlyPath'])}"
        f" ({引用['width']}x{引用['height']}px, {引用['mediaType']})."
        ' Source dimensions, format, and byte size may differ.'
        f" Copy to a writable path ending in {扩展名(引用['mediaType'])} before editing."
    )#说明

def 解析图片附件访问(附件,映射宿主路径,引用):#解析图片执行世界访问
    '把某一附件提供方的宿主对象位置桥进已挂载的工具执行世界'
    宿主路径=附件.图像宿主路径(引用)#宿主路径
    if 宿主路径 is None:#无映射
        return None#不可用
    只读路径=映射宿主路径(宿主路径)#映射到执行世界
    return None if 只读路径 is None else {'readonlyPath':只读路径}#有路径才返回

def 仅文本图片文案(引用):#仅文本模型占位
    '不能接受某一持久图片引用的模型所看到的稳定文本'
    摘要=str(引用['attachmentId'])[len('sha256:'):len('sha256:')+8]#短摘要
    return f'[image omitted because this model accepts text only; attachment sha256:{摘要}]'#仅文本占位

def 请求图片句柄文案(引用,版本,访问=None):#请求图片句柄文案
    '某一精确请求图片的稳定面向模型句柄'
    预览=f"Image {图片身份(引用)}; request preview {版本['width']}x{版本['height']}px."#预览行
    if 访问 is None:#无路径
        return f'{预览} It may be resized or re-encoded; source dimensions, format, and byte size may differ.'#无路径说明
    return 预览+归一化访问文案(引用,访问)#带路径说明

def 卸载图片文案(引用,访问=None):#卸载图片占位
    '请求上限省略时的稳定按图占位'
    身份=f'image omitted to fit request image limits; {图片身份(引用)}.'#身份句
    if 访问 is None:#无路径
        return f'[{身份} No local normalized image path is available; ask the user to attach it again if needed.]'#无可读路径
    return f'[{身份}{归一化访问文案(引用,访问)}]'#带路径

def 内容含图片(内容):#内容是否含图片块
    '有类型的模型内容是否含图片块'
    for 块 in 内容:#逐块
        if 块.get('type')=='image':#本块是图片
            return True#本块是图片
    return False#没有图片

def 内容含文件(内容):#内容是否含文件块
    '有类型的模型内容是否含文件块'
    for 块 in 内容:#逐块
        if 块.get('type')=='file':#本块是文件
            return True#本块是文件
    return False#无文件

def 文件句柄文案(引用,只读路径):#文件句柄文案
    '某一持久文件引用的稳定面向模型句柄'
    摘要=str(引用['attachmentId'])[len('sha256:'):len('sha256:')+8]#短摘要
    身份=f"File {引用串(引用['name'])} ({引用['bytes']} bytes, sha256:{摘要})"#身份
    if 只读路径 is None:#无路径
        return f'[{身份} was uploaded, but the current execution environment cannot access a readable path. Report that limitation if its contents are needed; do not claim to have read it.]'#不可读
    return (
        f'[{身份}: verbatim read-only copy saved at {引用串(只读路径)}. Read that path with your file tools when its contents are needed; '
        'copy it to a writable location before modifying it. When delegating file work, include this saved path in the delegation prompt; '
        'only subagents sharing this execution environment can read it.]'
    )#带路径句柄

def 替换文件为句柄(块列表,解析路径):#替换文件为句柄
    '把每个文件出现处替换成句柄文本'
    下一=None#惰性副本
    for 下标,块 in enumerate(块列表):#逐块
        if 块.get('type')=='file':#文件块
            if 下一 is None:#首次
                下一=list(块列表[:下标])#拷贝前缀
            下一.append({'type':'text','text':文件句柄文案(块['attachment'],解析路径(块['attachment']))})#句柄
            continue#下一块
        if 下一 is not None:#已开副本
            下一.append(块)#原样压入
    return 块列表 if 下一 is None else 下一#无变更则原数组

def 投影文件为文本(消息列表,解析路径):#文件投影为句柄文本
    '把持久文件历史投影成每条模型路由的确定性句柄文本'
    if not any(内容含文件(消息.get('content') or []) for 消息 in 消息列表):#无文件
        return 消息列表#原样
    结果=[]#投影后
    for 消息 in 消息列表:#逐消息
        内容=替换文件为句柄(消息.get('content') or [],解析路径)#替换
        if 内容 is 消息.get('content'):#无变
            结果.append(消息)#原样
        else:#有变
            结果.append({**消息,'content':内容})#浅拷贝
    return 结果#投影后

def base64长度(字节):#算 base64 长度
    '原始图片字节的 Base64 长度，含填充'
    return math.ceil(字节/3)*4#按 3 字节一组

def 收集图片长度(块列表,长度表,政策):#收集图片长度
    '按请求块顺序收集已表示图片长度'
    for 块 in 块列表:#逐块
        if 块.get('type')=='image':#图片
            if 'byteLength' in 政策 and 政策['byteLength'] is not None:#自定义
                字节=政策['byteLength'](块['attachment'])#自定义长度
            else:#归一化
                字节=块['attachment']['bytes']#归一化字节
            长度表.append(base64长度(字节) if 政策.get('representation')=='base64' else 字节)#记账

def 替换最旧图片(块列表,剩余,占位):#替换最旧图片
    '替换前 remaining.count 个图片出现处'
    下一=None#惰性副本
    for 下标,块 in enumerate(块列表):#逐块
        if 块.get('type')=='image' and 剩余['count']>0:#还需替换
            剩余['count']-=1#减一张
            if 下一 is None:#拷贝前缀
                下一=list(块列表[:下标])#前缀
            下一.append({'type':'text','text':占位(块['attachment'])})#占位
            continue#下一块
        if 下一 is not None:#已开副本
            下一.append(块)#原样
    return 块列表 if 下一 is None else 下一#结果

def 替换图片为仅文本(块列表):#仅文本替换图片
    '为仅文本模型替换每个图片出现处'
    下一=None#惰性副本
    for 下标,块 in enumerate(块列表):#逐块
        if 块.get('type')=='image':#图片
            if 下一 is None:#拷贝前缀
                下一=list(块列表[:下标])#前缀
            下一.append({'type':'text','text':仅文本图片文案(块['attachment'])})#仅文本占位
            continue#下一块
        if 下一 is not None:#已开副本
            下一.append(块)#原样
    return 块列表 if 下一 is None else 下一#结果

def 替换卸载图片(块列表,占位):#替换已卸载图片
    '把每个 offloaded 出现处换成占位文本'
    下一=None#惰性副本
    for 下标,块 in enumerate(块列表):#逐块
        if 块.get('type')=='image' and 块.get('offloaded') is True:#已卸载出现
            if 下一 is None:#拷贝前缀
                下一=list(块列表[:下标])#前缀
            下一.append({'type':'text','text':占位(块['attachment'])})#占位
            continue#下一块
        if 下一 is not None:#已开副本
            下一.append(块)#原样
    return 块列表 if 下一 is None else 下一#结果

def 投影卸载图片(消息列表,占位):#投影表面已卸载出现
    '把表面的已卸载出现投影成确定性文本；卸载集合是表面事实，占位文案由路由拥有'
    结果=[]#投影后
    for 消息 in 消息列表:#逐消息
        内容=替换卸载图片(消息.get('content') or [],占位)#替换
        if 内容 is 消息.get('content'):#无变
            结果.append(消息)#原样
        else:#有变
            结果.append({**消息,'content':内容})#浅拷贝
    return 结果#投影后

def 收集保留图片长度(块列表,长度表,政策,版本字节):#收集未卸载图片长度
    '按请求块顺序收集保留出现的已表示长度'
    for 块 in 块列表:#逐块
        if 块.get('type')=='image':#图片
            if 块.get('offloaded') is True:#已卸载不计
                continue#跳过
            字节=版本字节(块)#精确请求版本字节
            长度表.append(base64长度(字节) if 政策.get('representation')=='base64' else 字节)#记账

def 必需图片卸载(消息列表,政策,版本字节):#还需卸载的最旧张数
    '在精确表示字节下，路由预算还要求再卸载多少张最旧保留出现；零表示已能放下'
    长度表=[]#长度表
    for 消息 in 消息列表:#逐消息
        收集保留图片长度(消息.get('content') or [],长度表,政策,版本字节)#收集
    return 卸载图片前缀张数(长度表,政策)#前缀张数

def 投影图片为仅文本(消息列表):#仅文本投影图片
    '把持久图片历史投影成精确仅文本模型的确定性文本'
    if not any(内容含图片(消息.get('content') or []) for 消息 in 消息列表):#无图片
        return 消息列表#原样
    结果=[]#投影后
    for 消息 in 消息列表:#逐消息
        内容=替换图片为仅文本(消息.get('content') or [])#替换
        if 内容 is 消息.get('content'):#无变
            结果.append(消息)#原样
        else:#有变
            结果.append({**消息,'content':内容})#浅拷贝
    return 结果#投影后

def 卸载图片前缀张数(长度表,政策):#计算卸载前缀张数
    '超出路由预算后按整张数与字节量子移除的最旧图片出现处张数'
    总计=sum(长度表)#总字节
    超额张数=0 if 'maxImages' not in 政策 else max(0,len(长度表)-政策['maxImages'])#超额张数
    超额字节=0 if 'maxBytes' not in 政策 else max(0,总计-政策['maxBytes'])#超额字节
    if 超额张数==0 and 超额字节==0:#未超预算
        return 0#零
    张数量子=政策.get('countQuantum') if 政策.get('countQuantum') is not None else 1#张数量子
    字节量子=政策.get('byteQuantum') if 政策.get('byteQuantum') is not None else 1#字节量子
    移除张数=0 if 超额张数==0 else math.ceil(超额张数/张数量子)*张数量子#按量子取整张数
    移除字节=0 if 超额字节==0 else math.ceil(超额字节/字节量子)*字节量子#按量子取整字节
    张数=0#已计入张数
    已移字节=0#已计入字节
    for 图字节 in 长度表:#从最旧开始
        字节目标满=(移除字节==0) or (已移字节>=移除字节 if 字节量子==1 else 已移字节>移除字节)#字节目标
        if 张数>=移除张数 and 字节目标满:#两目标都满
            break#停
        已移字节+=图字节#累加字节
        张数+=1#累加张数
    return 张数#前缀张数

def 按政策卸载请求图片(消息列表,政策):#按政策卸载请求图片
    '返回确定性的瞬时投影：超出路由预算后替换最旧图片'
    长度表=[]#长度表
    for 消息 in 消息列表:#逐消息
        收集图片长度(消息.get('content') or [],长度表,政策)#收集
    张数=卸载图片前缀张数(长度表,政策)#要替换张数
    if 张数==0:#无需卸载
        return 消息列表#原样
    剩余={'count':张数}#可变剩余
    结果=[]#投影后
    for 消息 in 消息列表:#逐消息
        内容=替换最旧图片(消息.get('content') or [],剩余,政策['placeholder'])#替换最旧
        if 内容 is 消息.get('content'):#无变
            结果.append(消息)#原样
        else:#有变
            结果.append({**消息,'content':内容})#浅拷贝
    return 结果#投影后

def 去掉开发者消息(消息列表):#去掉开发者消息
    '不支持工具更新的路由不接收开发者消息'
    保留=[消息 for 消息 in 消息列表 if 消息.get('role')!='developer']#非开发者
    if len(保留)==len(消息列表):#没有开发者
        return 消息列表#原样
    return 保留#去掉后

def 工具声明表(工具列表,模式,历史):#按模式构造声明表
    '从会话折叠历史构造提供方声明，不改已记录的活动工具'
    声明={}#按名
    for 工具 in 历史['tools']:#基线声明
        声明[工具['name']]=工具#基线
    for 更新 in 历史['updates']:#后来的追加
        for 工具 in 更新['additions']:#追加定义
            if 工具['name'] not in 声明:#尚未声明
                副本=dict(工具)#稍后在记录位置激活
                副本['deferLoading']=True#推迟载入
                声明[工具['name']]=副本#记下
    if 模式=='in-history':#移除块只停用，不丢掉历史定义
        return 声明#保留全部
    if 模式=='addition-only':#不能移除时，声明表必须去掉不活动工具
        活跃=set()#当前活动名
        if 工具列表 is not None:#有当前声明
            for 工具 in 工具列表:#当前活动
                活跃.add(工具['name'])#记下
        for 名 in list(声明.keys()):#不活动则删
            if 名 not in 活跃:#不活动
                del 声明[名]#去掉
        return 声明#只留活动
    断言永不(模式)#封闭联合之外

def 投影工具更新(消息列表,工具列表,工具更新=None,历史=None):#按路由投影工具更新
    '按路由声明的工具更新模式投影消息与提供方声明'
    if 工具更新 is None:#不支持的路由只要立即可用的工具
        即时工具=工具列表#默认原声明
        if 工具列表 is not None and any(工具.get('deferLoading') is True for 工具 in 工具列表):#有推迟
            即时工具=[]#去掉推迟标记
            for 工具 in 工具列表:#逐个
                副本=dict(工具)#拷贝
                副本.pop('deferLoading',None)#去掉推迟
                即时工具.append(副本)#记下
        return {'messages':去掉开发者消息(消息列表),'tools':即时工具}#无更新消息
    if 历史 is None:#当前模式无法解析过去更新引用的定义
        return {'messages':去掉开发者消息(消息列表),'tools':工具列表}#只用当前声明
    消息号=set()#本请求里的开发者消息
    for 消息 in 消息列表:#收集
        if 消息.get('role')=='developer' and 'id' in 消息:#开发者
            消息号.add(消息['id'])#记下
    for 更新 in 历史['updates']:#辅助前缀可能丢掉激活所需的更新
        if 更新['messageId'] not in 消息号:#缺更新
            return {'messages':去掉开发者消息(消息列表),'tools':工具列表}#退回当前声明
    声明=工具声明表(工具列表,工具更新,历史)#本路由声明
    更新号=set(更新['messageId'] for 更新 in 历史['updates'])#当前声明系列
    已提供=set()#已经可用的工具
    for 工具 in 历史['tools']:#推迟的基线要等第一次保留追加
        if 工具.get('deferLoading') is not True:#立即可用
            已提供.add(工具['name'])#记下
    投影=[]#投影后的消息
    for 消息 in 消息列表:#逐条
        if 消息.get('role')!='developer':#普通消息
            投影.append(消息)#原样
            continue#下一条
        if 消息.get('id') not in 更新号:#更早的声明系列不管当前工具集
            continue#丢掉
        内容=[]#本条保留的块
        for 块 in 消息.get('content') or []:#逐块
            种类=块.get('type')#块类型
            if 种类=='tool-addition':#只激活尚未可用的已声明工具
                if 块.get('toolName') not in 声明 or 块.get('toolName') in 已提供:#已可用或未声明
                    continue#丢掉
                已提供.add(块['toolName'])#变为可用
                内容.append(块)#保留
            elif 种类=='tool-removal':#仅 in-history 能通过历史停用
                if 工具更新!='in-history':#addition-only
                    continue#丢掉
                if 块.get('toolName') not in 已提供:#本来就不可用
                    continue#丢掉
                已提供.remove(块['toolName'])#停用
                内容.append(块)#保留
            else:#其它块保留内容和顺序
                内容.append(块)#保留
        if len(内容)==0:#空了
            continue#丢掉整条
        原内容=消息.get('content') or []#原块
        if len(内容)==len(原内容):#没有删块
            投影.append(消息)#原样
        else:#删过块
            投影.append({**消息,'content':内容})#浅拷贝
    未变=len(投影)==len(消息列表)#长度相同才可能原样
    if 未变:#再比身份
        下标=0#下标
        while 下标<len(投影):#逐条
            if 投影[下标] is not 消息列表[下标]:#身份变了
                未变=False#变了
                break#停
            下标+=1#下一条
    return {'messages':消息列表 if 未变 else 投影,'tools':list(声明.values())}#声明按插入顺序
