"""持久终端工具结果的模型与 UI 渲染。"""
from ...工具.输出保留 import 文本保留器#导入文本保留器

截断标记='\n[output truncated]'#截断标记

def 字节长(文本):#UTF-8字节长度
    """对齐 TextEncoder.encode(...).byteLength。"""
    return len(文本.encode('utf-8'))#按utf8计

def 保留(文本,最大字节,种类):#按头或尾保留
    """按 head 或 tail 策略压进字节上限。"""
    保留器=文本保留器({'kind':种类,'maxBytes':最大字节})#构造保留器
    保留器.推入(文本)#推入全文
    return 保留器.收尾()['text']#取出保留文本

def 后缀适配(正文,后缀,最大字节):#正文加后缀并封顶
    """正文加后缀并封顶。"""
    固定字节=字节长(后缀)#后缀固定字节
    if 固定字节>=最大字节:#后缀已超则只留后缀尾
        return 保留(后缀,最大字节,'tail')#只留后缀尾
    return 保留(正文,最大字节-固定字节,'tail')+后缀#正文留尾再接后缀

def 前缀适配(前缀,正文,最大字节):#前缀加正文并封顶
    """前缀加正文并封顶。"""
    固定=前缀+截断标记#前缀加截断标记
    固定字节=字节长(固定)#固定部分字节
    if 固定字节>=最大字节:#固定部分已超则只留头
        return 保留(固定,最大字节,'head')#只留头
    return 前缀+保留(正文,最大字节-固定字节,'tail')+截断标记#前缀加正文尾再加标记

def 正文加后缀封顶(正文,元数据,上游截断,最大字节):#正文加元数据并封顶
    """正文加元数据并封顶。"""
    后缀=元数据+(截断标记 if 上游截断 else '')#元数据与上游截断标记
    完整=正文+后缀#完整文本
    if 字节长(完整)<=最大字节:#未超则原样
        return 完整#原样
    return 后缀适配(正文,元数据+截断标记,最大字节)#超则留正文尾并强制截断标记

def 封顶终端文本(文本,最大字节):#封顶一份完整终端确认
    """封顶一份完整终端确认，同时保住 UTF-8 切点。放得下时带截断标记。"""
    if 字节长(文本)<=最大字节:#未超则原样
        return 文本#原样
    标记字节=字节长(截断标记)#标记字节
    if 标记字节>=最大字节:#标记已超则只留标记尾
        return 保留(截断标记,最大字节,'tail')#只留标记尾
    return 保留(文本,最大字节-标记字节,'head')+截断标记#留头再加标记

def 渲染打开(结果,最大字节):#渲染一次已创建会话及其有界 MOTD
    """渲染一次已创建会话及其有界 MOTD，返回面向模型的会话确认。"""
    显示名=结果['name'] if 'name' in 结果 else None#可选显示名
    会话号=结果['sessionId']#会话id
    标签=会话号 if 显示名 is None else str(会话号)+' ('+str(显示名)+')'#id或带名
    前缀='started terminal session '+str(标签)+' [type: '+str(结果['type'])+']\n'#确认前缀
    开机原文=结果['motd'] if 'motd' in 结果 else None#开机信息
    开机=开机原文 if 开机原文 is not None and len(开机原文)>0 else '(no startup output)'#开机信息或占位
    完整=前缀+开机#完整确认
    if 字节长(完整)<=最大字节:#未超则原样
        return 完整#原样
    return 前缀适配(前缀,开机,最大字节)#超则前缀加MOTD尾

def 渲染发送(结果,最大字节):#渲染一次已结算的交互发送
    """渲染一次已结算的交互发送：终端输出加上等待/会话标记。"""
    视口原文=结果['viewport'] if 'viewport' in 结果 else None#视口
    视口=视口原文 if 视口原文 is not None and len(视口原文)>0 else '(no new output)'#视口或占位
    会话状态=结果['sessionStatus']#会话状态
    if 会话状态['kind']=='running':#仍在运行
        状态='running'#运行中
    else:#已退出
        退出码=会话状态['exitCode'] if 'exitCode' in 会话状态 else None#退出码
        信号=会话状态['signal'] if 'signal' in 会话状态 else None#信号
        状态=('exited code='+str(退出码 if 退出码 is not None else 'null')
            +' signal='+str(信号 if 信号 is not None else 'null'))#已退出摘要
    return 正文加后缀封顶(#正文加元数据封顶
        视口,#视口正文
        '\n[wait: '+str(结果['waitReason'])+']\n[session: '+状态+']',#等待与会话标记
        结果['truncated'] is True,#上游是否截断
        最大字节,#字节上限
    )#正文加后缀封顶结束

def 渲染发送读取(读取):#渲染一次增量后台操作读取
    """渲染一次增量后台操作读取：增量加上其上游截断标记。通用任务控制在加上任务状态后应用生产者的完整结果上限。"""
    增量原文=读取['delta'] if 'delta' in 读取 else None#增量
    增量=增量原文 if 增量原文 is not None else ''#缺席当空串
    if 增量.endswith('\n') or len(增量)==0:#已有换行或空
        分隔=''#无需补换行
    else:#需要补换行
        分隔='\n'#补换行
    if 读取['truncated'] is True:#上游截断
        return 增量+分隔+'[output truncated]'#增量后跟截断标记
    return 增量#仅增量

def 渲染读取(结果,最大字节):#渲染一页有界历史
    """渲染一页有界历史：页文本加上分页与截断标记。"""
    页原文=结果['text'] if 'text' in 结果 else None#页文本
    页文本=页原文 if 页原文 is not None and len(页原文)>0 else '(no retained output)'#页文本或占位
    return 正文加后缀封顶(#正文加分页封顶
        页文本,#页正文
        '\n[lines: '+str(结果['lineBegin'])+'-'+str(结果['lineEnd'])+' of '+str(结果['totalLines'])+']',#分页标记
        结果['truncated'] is True,#上游是否截断
        最大字节,#字节上限
    )#正文加后缀封顶结束

def 渲染列表(会话列表,最大字节):#渲染所有者可见的活会话
    """渲染所有者可见的活会话：每会话一行，或空标记。"""
    if 会话列表 is None or len(会话列表)==0:#空列表
        return '(no terminal sessions)'#空列表占位
    行列表=[]#逐会话一行
    for 会话 in 会话列表:#逐会话
        显示名=会话['name'] if 'name' in 会话 else None#可选显示名
        名段='' if 显示名 is None else ' ('+str(显示名)+')'#可选显示名
        进程号=会话['pid'] if 'pid' in 会话 else None#可选进程号
        进程段='' if 进程号 is None else ' pid='+str(进程号)#可选进程号
        会话状态=会话['status']#会话状态
        if 会话状态['kind']=='running':#仍在运行
            状态='running'#运行中
        else:#已退出
            退出码=会话状态['exitCode'] if 'exitCode' in 会话状态 else None#退出码
            信号=会话状态['signal'] if 'signal' in 会话状态 else None#信号
            状态=('exited code='+str(退出码 if 退出码 is not None else 'null')
                +' signal='+str(信号 if 信号 is not None else 'null'))#已退出摘要
        行列表.append(str(会话['sessionId'])+名段+' ['+str(会话['type'])+'] '+状态+进程段)#一行摘要
    文本='\n'.join(行列表)#用换行拼接
    return 正文加后缀封顶(文本,'',False,最大字节)#列表本身封顶
