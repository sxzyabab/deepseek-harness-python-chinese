"""worker 侧的 `node:path`：POSIX 算法，从 Node 实现转写。它不是 worker 主机
`posixPath` 上的表面：该辅助在分割前做规范化，故 `dirname('/a/b/..')` 给出 `/`
而 Node 给出 `/a/b`。`node:` 代理必须回答 Node 所答，因为 VFS 路径按 Node
语义构建。`win32` 成员抛错：worker 主机报告 `process.platform === 'linux'`。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/path.ts`。
公开面中文名；Node 面经别名与 default 暴露英文名。
"""
import json#诊断序列化
from ....storage.路径 import dsh根#VFS根

__all__=[#中文与Node面
    '解析','规范化','是否绝对','连接','相对','目录名','基名','扩展名',
    '格式化','拆解','分隔符','定界符','到命名空间路径',
    'resolve','normalize','isAbsolute','join','relative','dirname','basename','extname',
    'format','parse','sep','delimiter','toNamespacedPath','posix','win32','__esModule','default',
]#公开结束

字符点=46#点字符码
字符斜杠=47#斜杠字符码

def 当前目录():#当前工作目录
    """有 process.cwd 则用，否则 VFS 根。"""
    进程=globals().get('process')#全局process
    if 进程 is None: return dsh根#无process
    取目录=进程.get('cwd') if isinstance(进程,dict) else getattr(进程,'cwd',None)#cwd面
    if callable(取目录): return 取目录()#有则用
    return dsh根#否则VFS根

def 断言路径(路径):#断言路径为串
    """非串则抛 TypeError。"""
    if not isinstance(路径,str):#非串
        raise TypeError(f'Path must be a string. Received {json.dumps(路径)}')#类型错误

def 规范化段串(路径,允许越过根):#规范化段串
    """解析 `.` 与 `..` 段；`允许越过根` 为相对输入保留前导 `..`。"""
    结果=''#结果
    上段长=0#上一段长度
    上斜杠=-1#上一斜杠下标
    点数=0#连续点数
    码=0#当前字符码
    下标=0#游标
    while 下标<=len(路径):#含哨兵位
        if 下标<len(路径): 码=ord(路径[下标])#读字符
        elif 码==字符斜杠: break#末尾已是斜杠结束
        else: 码=字符斜杠#哨兵斜杠
        if 码==字符斜杠:#段边界
            if 上斜杠==下标-1 or 点数==1:#空段或.
                pass#跳过
            elif 点数==2:#..
                if (len(结果)<2 or 上段长!=2
                    or ord(结果[len(结果)-1])!=字符点
                    or ord(结果[len(结果)-2])!=字符点):#非已是..
                    if len(结果)>2:#可回退一段
                        末斜杠=结果.rfind('/')#找上一段
                        if 末斜杠==-1:#无斜杠
                            结果=''#清空
                            上段长=0#长度清零
                        else:#有斜杠
                            结果=结果[:末斜杠]#截到上一段
                            上段长=len(结果)-1-结果.rfind('/')#新段长
                        上斜杠=下标#记斜杠
                        点数=0#点数清零
                        下标+=1#推进
                        continue#下一段
                    elif len(结果)!=0:#短结果清空
                        结果=''#清空
                        上段长=0#长度清零
                        上斜杠=下标#记斜杠
                        点数=0#点数清零
                        下标+=1#推进
                        continue#下一段
                if 允许越过根:#允许越过根
                    结果+='/..' if len(结果)>0 else '..'#保留..
                    上段长=2#段长2
            else:#普通段
                if len(结果)>0: 结果+=f'/{路径[上斜杠+1:下标]}'#追加段
                else: 结果=路径[上斜杠+1:下标]#首段
                上段长=下标-上斜杠-1#段长
            上斜杠=下标#记斜杠
            点数=0#点数清零
        elif 码==字符点 and 点数!=-1:#计点
            点数+=1#累加点
        else:#非点非斜杠
            点数=-1#作废点数
        下标+=1#推进
    return 结果#交回

def 解析(*路径们):#解析绝对路径
    """将路径序列解析为绝对路径。"""
    累积=''#累积
    绝对=False#是否已绝对
    下标=len(路径们)-1#自右向左
    while 下标>=0 and not 绝对:#自右向左
        路径=路径们[下标]#当前段
        断言路径(路径)#断言串
        if len(路径)==0:#空段跳过
            下标-=1#推进
            continue#下一段
        累积=路径 if len(累积)==0 else f'{路径}/{累积}'#前置拼接
        绝对=ord(路径[0])==字符斜杠#是否绝对
        下标-=1#推进
    if not 绝对:#仍相对
        基址=当前目录()#工作目录
        累积=基址 if len(累积)==0 else f'{基址}/{累积}'#拼基址
        绝对=ord(基址[0])==字符斜杠#基址是否绝对
    已规范=规范化段串(累积,not 绝对)#规范化
    if 绝对: return f'/{已规范}'#绝对加根
    return 已规范 if len(已规范)>0 else '.'#相对或点

def 规范化(路径):#规范化路径
    """规范化路径，解析 `.`、`..` 与重复分隔符。"""
    断言路径(路径)#断言串
    if len(路径)==0: return '.'#空为点
    绝对路径=ord(路径[0])==字符斜杠#是否绝对
    尾斜杠=ord(路径[len(路径)-1])==字符斜杠#尾斜杠
    已规范=规范化段串(路径,not 绝对路径)#规范化段
    if len(已规范)==0:#空结果
        if 绝对路径: return '/'#绝对根
        return './' if 尾斜杠 else '.'#相对点
    if 尾斜杠: 已规范+='/'#保留尾斜杠
    return f'/{已规范}' if 绝对路径 else 已规范#加根或否

def 是否绝对(路径):#是否绝对
    """路径是否绝对。"""
    断言路径(路径)#断言串
    return len(路径)>0 and ord(路径[0])==字符斜杠#以斜杠起

def 连接(*路径们):#连接路径
    """用分隔符连接路径段，再规范化。"""
    if len(路径们)==0: return '.'#无段为点
    累积=None#累积
    for 路径 in 路径们:#遍历段
        断言路径(路径)#断言串
        if len(路径)==0: continue#空跳过
        累积=路径 if 累积 is None else f'{累积}/{路径}'#拼接
    return '.' if 累积 is None else 规范化(累积)#规范化

def 相对(源路径,目标):#相对路径
    """从一处到另一处的相对路径。"""
    断言路径(源路径)#断言源
    断言路径(目标)#断言目标
    if 源路径==目标: return ''#相同
    源解析=解析(源路径)#解析源
    目标解析=解析(目标)#解析目标
    if 源解析==目标解析: return ''#解析后相同
    源段=[段 for 段 in 源解析.split('/') if len(段)>0]#源段
    目标段=[段 for 段 in 目标解析.split('/') if len(段)>0]#目标段
    公共=0#公共前缀长
    while 公共<len(源段) and 公共<len(目标段) and 源段[公共]==目标段[公共]: 公共+=1#计公共
    上溯=['..']*(len(源段)-公共)#上溯
    return '/'.join(上溯+目标段[公共:])#拼相对

def 目录名(路径):#目录名
    """路径的目录部分（词汇层面）。"""
    断言路径(路径)#断言串
    if len(路径)==0: return '.'#空为点
    有根=ord(路径[0])==字符斜杠#有根
    终点=-1#截断点
    仍尾斜杠=True#仍在尾斜杠
    for 下标 in range(len(路径)-1,0,-1):#自后向前
        if ord(路径[下标])==字符斜杠:#遇斜杠
            if not 仍尾斜杠:#已过非斜杠
                终点=下标#截断于此
                break#结束
        else:#非斜杠
            仍尾斜杠=False#离开尾斜杠
    if 终点==-1: return '/' if 有根 else '.'#无父
    if 有根 and 终点==1: return '/'#双斜杠根
    return 路径[:终点]#截目录

def 基名(路径,后缀=None):#基名
    """路径的最后部分，可选去掉后缀。"""
    断言路径(路径)#断言串
    起点=0#起点
    终点=-1#终点
    仍尾斜杠=True#仍在尾斜杠
    if 后缀 is not None and len(后缀)>0 and len(后缀)<=len(路径):#有后缀
        if 后缀==路径: return ''#整路径即后缀
        后缀游标=len(后缀)-1#后缀游标
        首非斜杠终点=-1#首个非斜杠终点
        for 下标 in range(len(路径)-1,-1,-1):#自后向前
            码=ord(路径[下标])#字符码
            if 码==字符斜杠:#斜杠
                if not 仍尾斜杠:#已过非斜杠
                    起点=下标+1#段起点
                    break#结束
                continue#跳过尾斜杠
            if 首非斜杠终点==-1:#首次非斜杠
                仍尾斜杠=False#离开尾斜杠
                首非斜杠终点=下标+1#记终点
            if 后缀游标>=0:#仍在匹配后缀
                if 码==ord(后缀[后缀游标]):#匹配
                    后缀游标-=1#推进
                    if 后缀游标==-1: 终点=下标#后缀起点
                else:#失配
                    后缀游标=-1#停匹配
                    终点=首非斜杠终点#用全段
        if 起点==终点: 终点=首非斜杠终点#空后缀修正
        elif 终点==-1: 终点=len(路径)#无匹配用全长
        return 路径[起点:终点]#切片
    for 下标 in range(len(路径)-1,-1,-1):#无后缀扫描
        if ord(路径[下标])==字符斜杠:#斜杠
            if not 仍尾斜杠:#已过非斜杠
                起点=下标+1#段起点
                break#结束
        elif 终点==-1:#首次非斜杠
            仍尾斜杠=False#离开尾斜杠
            终点=下标+1#记终点
    return '' if 终点==-1 else 路径[起点:终点]#切片或空

def 扩展名(路径):#扩展名
    """最后路径段的扩展名，含前导点。"""
    断言路径(路径)#断言串
    点起点=-1#点起点
    段起点=0#段起点
    终点=-1#终点
    仍尾斜杠=True#仍在尾斜杠
    点前状态=0#点前状态
    for 下标 in range(len(路径)-1,-1,-1):#自后向前
        码=ord(路径[下标])#字符码
        if 码==字符斜杠:#斜杠
            if not 仍尾斜杠:#已过非斜杠
                段起点=下标+1#段起点
                break#结束
            continue#跳过尾斜杠
        if 终点==-1:#首次非斜杠
            仍尾斜杠=False#离开尾斜杠
            终点=下标+1#记终点
        if 码==字符点:#点
            if 点起点==-1: 点起点=下标#首点
            elif 点前状态!=1: 点前状态=1#多点
        elif 点起点!=-1:#点后非点
            点前状态=-1#有效扩展
    if (点起点==-1 or 终点==-1 or 点前状态==0
        or (点前状态==1 and 点起点==终点-1 and 点起点==段起点+1)):#无有效扩展
        return ''#无扩展
    return 路径[点起点:终点]#切片扩展

def 格式化(路径对象):#组装路径
    """由解析后的各部分构建路径。"""
    目录=路径对象.get('dir')#目录
    if 目录 is None: 目录=路径对象.get('root') or ''#根或空
    基=路径对象.get('base')#基名
    if 基 is None: 基=f"{路径对象.get('name') or ''}{路径对象.get('ext') or ''}"#拼
    if 目录=='': return 基#无目录
    return f'{目录}{基}' if 目录==路径对象.get('root') else f'{目录}/{基}'#根或斜杠

def 拆解(路径):#解析路径
    """将路径拆为 root/dir/base/ext/name。"""
    断言路径(路径)#断言串
    基=基名(路径)#基名
    扩展=扩展名(路径)#扩展
    修剪=路径.rstrip('/') if len(路径)>1 else 路径#去尾斜杠
    末斜杠=修剪.rfind('/')#最后斜杠
    根='/' if 是否绝对(路径) else ''#根
    if 修剪=='': 目录=根#空
    elif 末斜杠==-1: 目录=''#无斜杠
    elif 末斜杠==0: 目录='/'#根斜杠
    else: 目录=修剪[:末斜杠]#截目录
    名=基[:len(基)-len(扩展)] if len(扩展)>0 else 基#无扩展名
    return {'root':根,'dir':目录,'base':基,'ext':扩展,'name':名}#各部分

分隔符='/'#斜杠
定界符=':'#冒号
sep=分隔符#Node面
delimiter=定界符#Node面

def 到命名空间路径(路径):#命名空间路径
    """此处不存在 Windows 命名空间前缀。"""
    return 路径#原样

def win32成员(名称):#win32成员工厂
    """触达表示平台分支走错。"""
    def 拒绝(*位置参数,**关键字参数):#不可达
        """抛不可达。"""
        raise Exception(f'web-preview: node:path.win32.{名称} is unreachable — the worker host reports platform "linux"')#不可达
    return 拒绝#交回

#Node面英文别名
resolve=解析#解析
normalize=规范化#规范化
isAbsolute=是否绝对#是否绝对
join=连接#连接
relative=相对#相对
dirname=目录名#目录名
basename=基名#基名
extname=扩展名#扩展名
format=格式化#格式化
parse=拆解#拆解
toNamespacedPath=到命名空间路径#命名空间

win32={#win32命名空间
    'resolve':win32成员('resolve'),#resolve桩
    'normalize':win32成员('normalize'),#normalize桩
    'isAbsolute':win32成员('isAbsolute'),#isAbsolute桩
    'join':win32成员('join'),#join桩
    'relative':win32成员('relative'),#relative桩
    'dirname':win32成员('dirname'),#dirname桩
    'basename':win32成员('basename'),#basename桩
    'extname':win32成员('extname'),#extname桩
    'format':win32成员('format'),#format桩
    'parse':win32成员('parse'),#parse桩
    'toNamespacedPath':win32成员('toNamespacedPath'),#toNamespacedPath桩
    'sep':'\\',#反斜杠
    'delimiter':';',#分号
}#win32结束

posix面={#POSIX表面
    'resolve':解析,'normalize':规范化,'isAbsolute':是否绝对,'join':连接,#函数
    'relative':相对,'dirname':目录名,'basename':基名,'extname':扩展名,#续
    'format':格式化,'parse':拆解,'sep':分隔符,'delimiter':定界符,#常量
    'toNamespacedPath':到命名空间路径,#辅助
}#posix面结束

class _posix命名空间(dict):#posix命名空间
    """POSIX 成员集：模块表面，外加 Node 的自引用命名空间。"""

    def __getitem__(自身,键):#点号/下标
        """自引用 posix / 交叉 win32。"""
        if 键=='posix': return 自身#自引用
        if 键=='win32': return win32#交叉引用
        return dict.__getitem__(自身,键)#其余

    def __getattr__(自身,键):#属性访问
        """属性访问转发。"""
        try:#尝试
            return 自身[键]#下标
        except KeyError:#无
            raise AttributeError(键)#属性错误

posix=_posix命名空间(posix面)#posix命名空间
__esModule=True#CJS互操作
default=posix#默认导出posix
