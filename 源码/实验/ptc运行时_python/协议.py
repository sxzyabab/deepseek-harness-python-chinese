import json,math,re#编码、无损数与整数词

__all__=['协议文件描述符','线帧字段','日志截断标记','编码json纯值','检查完成值','含不安全整数词','含非无损数字','校验子帧']#仅中文公开名

协议文件描述符=3#子进程视角的帧通道 fd

线帧字段角色={#每帧必填/可选
    'BootMessage':{'type':'required','cpuSeconds':'required','addressSpaceBytes':'required','maxLogBytes':'required','maxValueBytes':'required','namespaces':'required'},#启动
    'Namespace':{'global':'required','names':'required','errorClass':'optional'},#命名空间
    'RunMessage':{'type':'required','program':'required'},#运行
    'BootAckMessage':{'type':'required'},#启动应答
    'CallMessage':{'type':'required','id':'required','global':'required','name':'required','args':'required'},#调用
    'LogMessage':{'type':'required','text':'required','truncated':'optional','open':'optional'},#日志
    'DoneErrorField':{'kind':'required','message':'required'},#完成错误
    'DoneMessage':{'type':'required','value':'optional','error':'optional'},#完成
    'ErrorClass':{'name':'required','memberNameProperty':'required'},#错误类
    'ReplyOk':{'type':'required','id':'required','ok':'required','value':'required'},#成功应答
    'ReplyErr':{'type':'required','id':'required','ok':'required','message':'required'},#失败应答
}#角色结束

线帧字段={}#投影为排序数组
for 帧名,角色 in 线帧字段角色.items():#逐帧
    必填=sorted(键 for 键,值 in 角色.items() if 值=='required')#必填
    可选=sorted(键 for 键,值 in 角色.items() if 值=='optional')#可选
    线帧字段[帧名]={'required':必填,'optional':可选}#记下

def 日志截断标记(最大字节):#共享截断文案
    """账本耗尽时的带内标记文本。"""
    return '[dsh-ptc-runtime-python] log capture truncated at '+str(最大字节)+' bytes'#标记

def 标量json(当前):#标量编码
    """null/布尔/有限数的 JSON 文本。超安全整数用精确十进制。"""
    if 当前 is None:#空
        return 'null'#空
    if 当前 is True:#真
        return 'true'#真
    if 当前 is False:#假
        return 'false'#假
    if isinstance(当前,bool):#防 bool 当 int
        return 'true' if 当前 else 'false'#布尔
    if isinstance(当前,int) and not isinstance(当前,bool) and (当前>9007199254740991 or 当前<-9007199254740991):#超安全
        return str(当前)#精确
    if isinstance(当前,float) and 当前.is_integer() and not math.isfinite(当前)==False:#整值浮点
        整=int(当前)#整
        if 整>9007199254740991 or 整<-9007199254740991:#超安全
            return str(整)#精确
    return str(当前)#其余

def 编码json纯值(值):#无递归编码
    """把 JSON.parse 产出的纯值编成紧凑 JSON，深度无上限。"""
    块=[]#片段
    任务=[{'value':值}]#栈
    while len(任务)>0:#弹栈
        项=任务.pop()#项
        if 'text' in 项:#字面
            块.append(项['text'])#追加
            continue#下
        当前=项['value']#值
        if isinstance(当前,str):#串
            块.append(json.dumps(当前,ensure_ascii=False))#串
        elif isinstance(当前,list):#数组
            块.append('[')#开
            任务.append({'text':']'})#闭
            for 下标 in range(len(当前)-1,-1,-1):#倒序
                if 下标<len(当前)-1:#逗号
                    任务.append({'text':','})#逗号
                任务.append({'value':当前[下标]})#元素
        elif isinstance(当前,dict):#对象
            块.append('{')#开
            任务.append({'text':'}'})#闭
            键表=list(当前.keys())#键
            for 下标 in range(len(键表)-1,-1,-1):#倒序
                键=键表[下标]#键
                if 下标<len(键表)-1:#逗号
                    任务.append({'text':','})#逗号
                任务.append({'value':当前[键]})#值
                任务.append({'text':json.dumps(键,ensure_ascii=False)+':'})#键
        else:#标量
            块.append(标量json(当前))#标量
    return ''.join(块)#拼接

def json串字节上限(文本,最大字节):#不分配转义副本
    """紧凑 JSON 串的 UTF-8 字节长；一超预算即停。"""
    字节=2#引号
    if 字节>最大字节:#超
        return None#超
    下标=0#扫描
    while 下标<len(文本):#逐码元
        码=ord(文本[下标])#码元
        if 码 in (0x22,0x5c,0x08,0x09,0x0a,0x0c,0x0d):#短转义
            字节+=2#两字节
        elif 码<0x20:#其它 C0
            字节+=6#\\uXXXX
        elif 码<0x80:#ASCII
            字节+=1#一
        elif 码<0x800:#两字节 UTF-8
            字节+=2#两
        elif 0xd800<=码<=0xdbff and 下标+1<len(文本):#高代理
            下一=ord(文本[下标+1])#下一
            if 0xdc00<=下一<=0xdfff:#成对
                字节+=4#四字节
                下标+=1#跳低
            else:#孤高
                字节+=6#转义
        elif 0xd800<=码<=0xdfff:#孤代理
            字节+=6#转义
        else:#其余 BMP
            字节+=3#三
        if 字节>最大字节:#超
            return None#超
        下标+=1#前
    return 字节#长

def 自有项(记录):#惰性项
    """产出对象自有可枚举项。"""
    for 键 in 记录:#逐键
        yield (键,记录[键])#项

def 自有值(记录):#惰性值
    """产出对象自有可枚举值。"""
    for 键 in 记录:#逐键
        yield 记录[键]#值

def 检查完成值(值,最大字节):#计量且查无损
    """计量完成值紧凑 JSON 字节并查非无损数；一超预算即停。"""
    字节=0#累计
    非无损=False#标记
    游标=[{'kind':'values','iter':iter([值])}]#根
    while len(游标)>0:#走
        当前游标=游标[-1]#顶
        try:#下一步
            步=next(当前游标['iter'])#步
        except StopIteration:#尽
            游标.pop()#弹
            continue#下
        if 当前游标['kind']=='entries':#对象项
            键,成员=步#拆
            键字节=json串字节上限(键,最大字节-字节)#键
            if 键字节 is None:#超
                return {'ok':False,'reason':'over-budget'}#超
            字节+=键字节+1#键与冒号
            当前=成员#值
        else:#值
            当前=步#值
        if isinstance(当前,bool):#布尔先于 int
            字节+=len(标量json(当前).encode('utf-8'))#布尔
        elif isinstance(当前,(int,float)):#数
            if isinstance(当前,float) and (not math.isfinite(当前) or math.copysign(1.0,当前)<0 and 当前==0.0):#非有限或负零
                非无损=True#记下
            字节+=len(标量json(当前).encode('utf-8'))#数
        elif isinstance(当前,str):#串
            串字节=json串字节上限(当前,最大字节-字节)#串
            if 串字节 is None:#超
                return {'ok':False,'reason':'over-budget'}#超
            字节+=串字节#串
        elif isinstance(当前,list):#数组
            字节+=2+(len(当前)-1 if len(当前)>1 else 0)#括号与逗号
            if 字节+len(当前)>最大字节:#超
                return {'ok':False,'reason':'over-budget'}#超
            游标.append({'kind':'values','iter':iter(当前)})#下潜
        elif isinstance(当前,dict):#对象
            计数=len(当前)#键数
            字节+=2+(计数-1 if 计数>1 else 0)#括号与逗号
            if 字节+计数*4>最大字节:#超
                return {'ok':False,'reason':'over-budget'}#超
            游标.append({'kind':'entries','iter':自有项(当前)})#下潜
        else:#其余标量
            字节+=len(标量json(当前).encode('utf-8'))#标量
        if 字节>最大字节:#超
            return {'ok':False,'reason':'over-budget'}#超
    if 非无损:#非无损
        return {'ok':False,'reason':'non-lossless'}#非无损
    return {'ok':True,'bytes':字节}#通过

def 含不安全整数词(行):#扫描源文本
    """行内是否有会在 JS 丢失精度的整数词。"""
    下标=0#扫描
    长=len(行)#长
    while 下标<长:#逐字
        字=行[下标]#字
        if 字=='"':#串
            下标+=1#进
            while 下标<长:#跳串
                if 行[下标]=='\\':#转义
                    下标+=1#跳
                elif 行[下标]=='"':#闭
                    break#停
                下标+=1#前
            下标+=1#过闭
            continue#下
        if 字=='-' or ('0'<=字<='9'):#数词
            尾=下标+1#尾
            while 尾<长:#扩
                次=行[尾]#次
                if ('0'<=次<='9') or 次 in '.eE+-':#成分
                    尾+=1#扩
                else:#停
                    break#停
            词=行[下标:尾]#词
            if re.fullmatch(r'-?\d+',词):#纯整数
                try:#解析
                    解析=float(词)#双精度
                except Exception:#无穷
                    return True#丢失
                if not math.isfinite(解析):#无穷
                    return True#丢失
                if (解析>9007199254740991 or 解析<-9007199254740991) and int(词)!=int(解析):#不往返
                    return True#丢失
            下标=尾#跳过
            continue#下
        下标+=1#前
    return False#无

def 含非无损数字(值):#O(深度) 游标
    """JSON.parse 值是否含非有限或负零。"""
    游标=[iter([值])]#根
    while len(游标)>0:#走
        当前游标=游标[-1]#顶
        try:#下一步
            当前=next(当前游标)#值
        except StopIteration:#尽
            游标.pop()#弹
            continue#下
        if isinstance(当前,bool):#跳过 bool
            continue#下
        if isinstance(当前,float):#浮点
            if not math.isfinite(当前) or (当前==0.0 and math.copysign(1.0,当前)<0):#非有限或负零
                return True#是
        elif isinstance(当前,list):#数组
            游标.append(iter(当前))#下潜
        elif isinstance(当前,dict):#对象
            游标.append(自有值(当前))#下潜
    return False#否

def 校验子帧(原始):#重建入站帧
    """校验并重建 fd-3 帧；垃圾返回 None。"""
    if not isinstance(原始,dict):#非对象
        return None#丢
    种=原始.get('type')#种
    if 种=='boot-ack':#应答
        return {'type':'boot-ack'}#重建
    if 种=='log':#日志
        if not isinstance(原始.get('text'),str):#非法
            return None#丢
        结果={'type':'log','text':原始['text']}#重建
        if 原始.get('truncated') is True:#截断
            结果['truncated']=True#字面真
        if 原始.get('open') is True:#未结束
            结果['open']=True#字面真
        return 结果#帧
    if 种=='call':#调用
        号=原始.get('id')#号
        if not isinstance(号,(int,float)) or isinstance(号,bool) or not math.isfinite(号) or (isinstance(号,float) and 号==0.0 and math.copysign(1.0,号)<0):#非法号
            return None#丢
        if not isinstance(原始.get('global'),str) or not isinstance(原始.get('name'),str):#非法名
            return None#丢
        if 'args' not in 原始:#缺参数
            return None#丢
        if 含非无损数字(原始['args']):#非无损
            return None#丢
        return {'type':'call','id':号,'global':原始['global'],'name':原始['name'],'args':原始['args']}#重建
    if 种=='done':#完成
        if 'error' not in 原始:#无错误
            if 'value' not in 原始:#无值
                return {'type':'done'}#空完成
            return {'type':'done','value':原始['value']}#带值
        错=原始['error']#错误
        if not isinstance(错,dict):#非法或 null
            return None#丢
        类=错.get('kind')#类
        文=错.get('message')#文
        if not isinstance(文,str):#非法
            return None#丢
        if 类 not in ('exception','invalid-output','output-limit'):#非法类
            return None#丢
        if 'value' not in 原始:#无值
            return {'type':'done','error':{'kind':类,'message':文}}#仅错
        return {'type':'done','value':原始['value'],'error':{'kind':类,'message':文}}#双带
    return None#丢
