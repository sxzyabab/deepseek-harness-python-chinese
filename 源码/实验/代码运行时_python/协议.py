"""Node 宿主与 CPython 子进程之间的无版本 fd-3 JSON-lines 线路协议。

对齐上游 `code-runtime-python/src/protocol.ts`。宿主把每条入站帧当敌对流量校验。
"""
import json,math,re#JSON、数值与整数令牌扫描
协议文件描述符=3#fd-3 引导通道
线路帧字段角色={#各帧字段 required/optional 角色
    'BootMessage':{'type':'required','cpuSeconds':'required','addressSpaceBytes':'required','maxLogBytes':'required','maxValueBytes':'required','namespaces':'required'},
    'Namespace':{'global':'required','names':'required','errorClass':'optional'},
    'RunMessage':{'type':'required','program':'required'},
    'BootAckMessage':{'type':'required'},
    'CallMessage':{'type':'required','id':'required','global':'required','name':'required','args':'required'},
    'LogMessage':{'type':'required','text':'required','truncated':'optional'},
    'DoneErrorField':{'kind':'required','message':'required'},
    'DoneMessage':{'type':'required','value':'optional','error':'optional'},
    'ErrorClass':{'name':'required','memberNameProperty':'required'},
    'ReplyOk':{'type':'required','id':'required','ok':'required','value':'required'},
    'ReplyErr':{'type':'required','id':'required','ok':'required','message':'required'},
}#角色表结束
线路帧字段={#投影成排序后的 required/optional 数组
    帧名:{
        'required':sorted([键 for 键,角色 in 字段.items() if 角色=='required']),
        'optional':sorted([键 for 键,角色 in 字段.items() if 角色=='optional']),
    }
    for 帧名,字段 in 线路帧字段角色.items()
}#线路帧字段结束

__all__=[#仅中文公开名
    '协议文件描述符','线路帧字段',
    '日志截断标记','编码json纯','检查完成值','含不安全整数字面量','含非无损数字','校验子进程帧',
]#公开面结束

def 日志截断标记(最大字节):#日志预算耗尽标记
    """与 Python 侧 LogBuffer 使用同一字面量。"""
    return '[dsh-code-runtime-python] log capture truncated at '+str(最大字节)+' bytes'#标记行

def 标量json(当前):#编码单个 JSON 标量
    """超出安全整数范围时用 BigInt 风格十进制。"""
    if isinstance(当前,float) and 当前.is_integer() and not _是安全整数(当前):#超大整数 double
        return str(int(当前))#精确十进制
    return json.dumps(当前,separators=(',',':'))#普通标量

def 编码json纯(值):#非递归 JSON 编码
    """与紧凑 JSON.stringify 对齐，除超大整数用精确十进制。"""
    片段=[]#输出片段
    任务=[值]#显式栈
    while 任务:#DFS 栈
        当前=任务.pop()#栈顶
        if isinstance(当前,str):#已编码片段
            片段.append(当前)#追加
            continue#下一个
        if isinstance(当前,list):#数组
            片段.append('[')#开括号
            任务.append(']')#闭括号任务
            for 索引 in range(len(当前)-1,-1,-1):#逆序入栈
                if 索引<len(当前)-1:任务.append(',')#逗号
                任务.append(当前[索引])#元素
            continue#下一个
        if isinstance(当前,dict):#对象
            片段.append('{')#开花括号
            任务.append('}')#闭括号任务
            键们=list(当前.keys())#键列表
            for 索引 in range(len(键们)-1,-1,-1):#逆序
                键=键们[索引]#当前键
                if 索引<len(键们)-1:任务.append(',')#逗号
                任务.append(当前[键])#值
                任务.append(json.dumps(键,separators=(',',':'))+':')#键前缀
            continue#下一个
        片段.append(标量json(当前))#标量
    return ''.join(片段)#合并

def _是安全整数(值):#对齐 Number.isSafeInteger
    """排除布尔与非整数。"""
    if isinstance(值,bool):#布尔
        return False#不是整数
    if isinstance(值,int):#整数
        return abs(值)<=9007199254740991#MAX_SAFE_INTEGER
    if isinstance(值,float) and math.isfinite(值) and 值.is_integer():#整型 double
        return abs(值)<=9007199254740991#范围内
    return False#其它

def _json字符串字节上限(文本,最大字节):#不分配转义副本的字符串 JSON 字节数
    """超过上限返回 None。"""
    字节=2#两侧引号
    if 字节>最大字节:#已超
        return None#失败
    索引=0#游标
    while 索引<len(文本):#扫描
        码=ord(文本[索引])#码点
        if 码 in (0x22,0x5c,0x08,0x09,0x0a,0x0c,0x0d):#短转义
            字节+=2#两字节
        elif 码<0x20:#其它控制符
            字节+=6#\uXXXX
        elif 码<0x80:#ASCII
            字节+=1#一字节
        elif 码<0x800:#两字节 UTF-8
            字节+=2#两字节
        elif 0xD800<=码<=0xDBFF and 索引+1<len(文本):#代理对
            下一=ord(文本[索引+1])#下一单元
            if 0xDC00<=下一<=0xDFFF:#合法对
                字节+=4#四字节 UTF-8
                索引+=1#吃掉低位
            else:#孤立高位
                字节+=6#\uXXXX
        elif 0xD800<=码<=0xDFFF:#孤立代理
            字节+=6#\uXXXX
        else:#三字节 BMP
            字节+=3#三字节
        if 字节>最大字节:#超预算
            return None#失败
        索引+=1#前进
    return 字节#精确字节数

def 检查完成值(值,最大字节):#计量完成值并检查无损性
    """over-budget 优先于 non-lossless。"""
    字节=0#累计
    非无损=False#是否见到非无损数
    栈=[值]#显式栈
    while 栈:#遍历
        当前=栈.pop()#栈顶
        if isinstance(当前,(int,float)) and not isinstance(当前,bool):#数字
            if not math.isfinite(当前) or 当前==0.0 and str(当前).startswith('-'):#非有限或负零
                非无损=True#记下
            字节+=len(标量json(当前).encode('utf-8'))#数字字节
        elif isinstance(当前,str):#字符串
            字符串字节=_json字符串字节上限(当前,最大字节-字节)#计量
            if 字符串字节 is None:#超预算
                return {'ok':False,'reason':'over-budget'}#超预算
            字节+=字符串字节#累加
        elif isinstance(当前,list):#数组
            字节+=2+max(0,len(当前)-1)#括号与逗号
            if 字节+len(当前)>最大字节:#下界剪枝
                return {'ok':False,'reason':'over-budget'}#超预算
            栈.extend(当前)#子元素
        elif isinstance(当前,dict):#对象
            计数=len(当前)#键数
            字节+=2+max(0,计数-1)#括号与逗号
            if 字节+计数*4>最大字节:#下界剪枝
                return {'ok':False,'reason':'over-budget'}#超预算
            for 键,子 in 当前.items():#键值
                键字节=_json字符串字节上限(键,最大字节-字节)#键转义
                if 键字节 is None:#超预算
                    return {'ok':False,'reason':'over-budget'}#超预算
                字节+=键字节+1#键与冒号
                栈.append(子)#值
        else:#null/bool
            字节+=len(标量json(当前).encode('utf-8'))#标量
        if 字节>最大字节:#超预算
            return {'ok':False,'reason':'over-budget'}#超预算
    if 非无损:#见到非无损数
        return {'ok':False,'reason':'non-lossless'}#非无损
    return {'ok':True,'bytes':字节}#通过

def 含不安全整数字面量(行):#扫描原始 JSON 行
    """跳过字符串字面量后检查整数令牌。"""
    索引=0#游标
    while 索引<len(行):#扫描
        字符=行[索引]#当前字符
        if 字符=='"':#字符串
            索引+=1#进入字符串
            while 索引<len(行):#扫字符串
                if 行[索引]=='\\':#转义
                    索引+=2#跳过转义
                    continue#继续
                if 行[索引]=='"':#结束
                    索引+=1#吃掉引号
                    break#退出字符串
                索引+=1#前进
            continue#继续外层
        if 字符=='-' or 字符.isdigit():#数字令牌
            结束=索引+1#结束游标
            while 结束<len(行) and (行[结束].isdigit() or 行[结束] in '.eE+-'):#延续
                结束+=1#扩展
            令牌=行[索引:结束]#切片
            if re.fullmatch(r'-?\d+',令牌):#纯整数
                解析=float(令牌)#double 解析
                if not math.isfinite(解析):#Infinity
                    return True#不安全
                if not _是安全整数(解析) and int(令牌)!=int(解析):#真正丢精度
                    return True#不安全
            索引=结束#跳到令牌后
            continue#继续
        索引+=1#前进
    return False#安全

def _自有值(记录,键):#遍历自有键值
    """yield 每个自有 enumerable 值。"""
    if isinstance(记录,dict):#映射
        for 键名 in 记录:#键
            yield 记录[键名]#值
    else:#其它对象
        for 键名 in 记录:#尽力遍历
            try:
                if 键名 in 记录:yield 记录[键名]#值
            except Exception:
                break#停止

def 含非无损数字(值):#检查是否含非有限或负零
    """迭代遍历，避免宽对象复制。"""
    游标们=[[值]]#每层一个游标列表
    while 游标们:#层栈
        层=游标们[-1]#当前层
        if not 层:#层耗尽
            游标们.pop()#弹出
            continue#上一层
        当前=层.pop()#当前值
        if isinstance(当前,(int,float)) and not isinstance(当前,bool):#数字
            if not math.isfinite(当前) or 当前==0.0 and str(当前).startswith('-'):#非有限或负零
                return True#命中
        elif isinstance(当前,list):#数组
            游标们.append(iter(当前))#子层
        elif isinstance(当前,dict):#对象
            游标们.append(iter(_自有值(当前)))#子层
    return False#干净

def 校验子进程帧(原始):#重建入站子进程帧
    """畸形帧返回 None 并静默丢弃。"""
    if not isinstance(原始,dict):#非对象
        return None#丢弃
    类型=原始.get('type')#判别
    if 类型=='boot-ack':#启动确认
        return {'type':'boot-ack'}#重建
    if 类型=='log':#日志
        文本=原始.get('text')#文本
        if not isinstance(文本,str):#非法
            return None#丢弃
        出={'type':'log','text':文本}#重建
        if 原始.get('truncated') is True:#仅 true 算截断
            出['truncated']=True#带上
        return 出#返回
    if 类型=='call':#调用
        编号=原始.get('id')#相关 id
        全局=原始.get('global')#命名空间
        名字=原始.get('name')#成员名
        if (not isinstance(编号,(int,float)) or not math.isfinite(编号) or 编号==0.0 and str(编号).startswith('-')
            or not isinstance(全局,str) or not isinstance(名字,str)):#非法 id/全局/名字
            return None#丢弃
        if 'args' not in 原始:#缺 args
            return None#丢弃
        实参=原始['args']#参数
        if 含非无损数字(实参):#非无损参数
            return None#丢弃
        return {'type':'call','id':编号,'global':全局,'name':名字,'args':实参}#重建
    if 类型=='done':#完成
        错误=原始.get('error')#错误字段
        if 错误 is None:#无错误
            return {'type':'done'} if 'value' not in 原始 else {'type':'done','value':原始.get('value')}#重建
        if not isinstance(错误,dict):#非法错误
            return None#丢弃
        种类=错误.get('kind')#错误种类
        消息=错误.get('message')#错误消息
        if 种类 not in ('exception','invalid-output','output-limit') or not isinstance(消息,str):#非法
            return None#丢弃
        出={'type':'done','error':{'kind':种类,'message':消息}}#重建
        if 'value' in 原始:#可同时带 value
            出['value']=原始.get('value')#保留
        return 出#返回
    return None#未知类型
