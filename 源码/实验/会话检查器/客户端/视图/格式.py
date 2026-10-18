'按类型生成横向预览，不改原始检查数据'

检查器预览上限=240#一行预览最多保留的字符数

def 预览(值,深度,隐藏根字段):
    '把一层值收成短文本。过深只留长度，单独一个字段不再重复字段名'
    if isinstance(值,str):#字符串
        return 值[:180]#只留前 180 个字符
    if 值 is None or isinstance(值,(bool,int,float)):#标量
        return str(值)#按文本显示
    if not isinstance(值,(dict,list)):#其余非容器
        return str(值)#直接转文本
    if 深度>1:#不再往下展开
        if isinstance(值,list):#列表
            return '['+str(len(值))+']'#只留长度
        return '{…}'#对象省略
    限定=None#增量类型只看指定字段
    if isinstance(值,dict) and isinstance(值.get('type'),str):#带类型的对象
        if 值['type']=='tool-call-delta':#工具调用增量
            限定=('argumentsDelta',)#只看参数增量
        elif 值['type']=='reasoning-delta':#推理增量
            限定=('text',)#只看文本
    项=[]#留下来的字段
    if isinstance(值,dict):#对象按插入顺序
        for 键,内容 in 值.items():#逐字段
            低=键.lower() if isinstance(键,str) else ''#比较用小写
            if 深度==0 and (低=='time' or 键 in 隐藏根字段):#顶层时间和表格已显示的列
                continue#跳过
            if 限定 is None:#普通记录
                if 低 in ('type','seq','sequence'):#类型和序号不进预览
                    continue#跳过
            elif 键 not in 限定:#不是这个增量要的字段
                continue#跳过
            项.append((键,内容))#留下
    if len(项)==1:#只有一个字段
        return 预览(项[0][1],深度+1,隐藏根字段)#不再写字段名
    片段=[]#前五项
    for 键,内容 in 项[:5]:#最多五项
        片段.append(str(键)+': '+预览(内容,深度+1,隐藏根字段))#键和短值
    return ' · '.join(片段)[:检查器预览上限]#拼起来再截断

def 检查器预览(值,隐藏根字段=()):
    '从第 0 层生成有界预览，省略类型、序号和顶层时间'
    return 预览(值,0,隐藏根字段)#从根开始
