"""shell 内建：读取或改动 shell 自身状态（目录、环境、退出状态）而非文件系统的程序。

对齐上游 `webworker-runtime/src/shell/programs/builtins.ts`。公开面仅中文名。
"""
import threading as 线程#睡眠可取消
from datetime import datetime as 日期时间,timezone as 时区#ISO时间
from ..展开 import 读变量#读变量
from ..文件系统访问 import 在目录解析#路径解析
from .选项 import 解析选项#选项解析

__all__=['内建程序']#仅中文公开名

信号退出码=130#信号结束命令时报告的状态

def cd程序(argv,io,state,fs):#cd程序
    """切换工作目录。"""
    目标=argv[1] if len(argv)>1 else state['environment'].get('HOME','/')#目标路径词
    if 目标=='-':#回到OLDPWD
        路径=state['variables'].get('OLDPWD',state['cwd'])#旧目录
    else:#普通解析
        路径=在目录解析(state['cwd'],目标)#解析目标
    统计=fs['stat'](路径)#查询目标
    if 统计 is None:#不存在
        io['err'](f'cd: {目标}: No such file or directory\n')#诊断
        return 1#失败
    if not 统计['directory']:#非目录
        io['err'](f'cd: {目标}: Not a directory\n')#诊断
        return 1#失败
    state['variables']['OLDPWD']=state['cwd']#记住旧目录
    state['cwd']=路径#切换目录
    # `$PWD` 是脚本读回的内容，因此必须跟随真实目录。
    if 'PWD' in state['environment']:#同步PWD
        state['environment']['PWD']=路径#写入
    return 0#成功

def pwd程序(argv,io,state,fs=None):#pwd程序
    """打印工作目录。"""
    io['out'](f"{state['cwd']}\n")#打印
    return 0#成功

def export程序(argv,io,state,fs=None):#export程序
    """导出环境变量。"""
    选项=解析选项(argv)#解析选项
    if len(选项['operands'])==0:#无操作数则列出
        for 名,值 in sorted(state['environment'].items()):#打印环境
            io['out'](f'declare -x {名}="{值}"\n')#打印
        return 0#成功
    for 操作数 in 选项['operands']:#逐操作数
        分隔=操作数.find('=')#等号位置
        if 分隔<0:#无赋值
            # 导出已有 shell 变量将其移入环境。
            state['environment'][操作数]=state['variables'].get(操作数,state['environment'].get(操作数,''))#导出已有
            continue#下一操作数
        state['environment'][操作数[:分隔]]=操作数[分隔+1:]#名=值写入环境
    return 0#成功

def unset程序(argv,io,state,fs=None):#unset程序
    """取消变量。"""
    待删=set(argv[1:])#待删名集合
    def 过滤(源):#过滤函数
        """去掉已删名。"""
        return {名:值 for 名,值 in 源.items() if 名 not in 待删}#过滤
    state['environment']=过滤(state['environment'])#过滤环境
    state['variables']=过滤(state['variables'])#过滤变量
    return 0#成功

def env程序(argv,io,state,fs=None):#env程序
    """打印环境。"""
    for 名,值 in sorted(state['environment'].items()):#打印
        io['out'](f'{名}={值}\n')#行
    return 0#成功

def exit程序(argv,io,state,fs=None):#exit程序
    """请求退出。"""
    if len(argv)<2:#无参用上一状态
        状态=state['lastStatus']#上一
    else:#解析
        try:#整数
            状态=int(argv[1],10) or 0#目标状态
        except ValueError:#非法
            状态=0#零
    state['exitRequested']=状态#请求退出
    return 状态#返回该状态

def test程序(argv,io,state,fs):#test程序
    """`test` / `[`：生成命令行使用的文件与字符串谓词。"""
    if argv[0]=='[':#方括号形式
        词们=list(argv[1:-1] if len(argv)>1 and argv[-1]==']' else argv[1:])#剥]
    else:#test形式
        词们=list(argv[1:])#谓词词
    def 状态码(值):#布尔转退出码
        """真0假1。"""
        return 0 if 值 else 1#转换
    def 路径统计(操作数):#路径stat
        """相对cwd查询。"""
        return fs['stat'](在目录解析(state['cwd'],操作数))#stat
    if len(词们)==1:#单操作数非空
        return 状态码(词们[0]!='')#非空
    if len(词们)==2:#一元
        运算符=词们[0]#运算符
        操作数=词们[1] if len(词们)>1 else ''#操作数
        if 运算符=='-e':#存在
            return 状态码(路径统计(操作数) is not None)#存在
        if 运算符=='-f':#普通文件
            统计=路径统计(操作数)#查询
            return 状态码(统计 is not None and 统计['directory'] is False)#文件
        if 运算符=='-d':#目录
            统计=路径统计(操作数)#查询
            return 状态码(统计 is not None and 统计['directory'] is True)#目录
        if 运算符=='-s':#非空
            统计=路径统计(操作数)#查询
            return 状态码((0 if 统计 is None else 统计['size'])>0)#非空
        if 运算符 in ('-r','-w'):#可读写近似为存在
            return 状态码(路径统计(操作数) is not None)#存在
        if 运算符=='-z':#空串
            return 状态码(操作数=='')#空
        if 运算符=='-n':#非空串
            return 状态码(操作数!='')#非空
        if 运算符=='!':#非
            return 状态码(操作数=='')#非
        io['err'](f'test: {运算符}: unsupported unary operator\n')#诊断
        return 2#用法错
    if len(词们)==3:#二元
        左,运算符,右=词们[0],词们[1],词们[2]#拆三词
        if 运算符 in ('=','=='):#相等
            return 状态码(左==右)#等
        if 运算符=='!=':#不等
            return 状态码(左!=右)#不等
        if 运算符=='-eq':#数值等
            return 状态码(float(左)==float(右))#等
        if 运算符=='-ne':#数值不等
            return 状态码(float(左)!=float(右))#不等
        if 运算符=='-lt':#小于
            return 状态码(float(左)<float(右))#小于
        if 运算符=='-le':#小于等于
            return 状态码(float(左)<=float(右))#小于等于
        if 运算符=='-gt':#大于
            return 状态码(float(左)>float(右))#大于
        if 运算符=='-ge':#大于等于
            return 状态码(float(左)>=float(右))#大于等于
        io['err'](f'test: {运算符}: unsupported binary operator\n')#诊断
        return 2#用法错
    io['err']('test: unsupported expression\n')#复杂表达式拒
    return 2#用法错

def sleep程序(argv,io,state,fs=None):#sleep程序
    """睡眠；可被信号取消。"""
    try:#解析秒数
        秒数=float(argv[1] if len(argv)>1 else '')#间隔秒数
    except ValueError:#非法
        秒数=float('nan')#非有限
    if not (秒数==秒数) or 秒数<0:#非法间隔（NaN或负）
        io['err'](f"sleep: invalid time interval '{argv[1] if len(argv)>1 else ''}'\n")#诊断
        return 2#用法错
    # 被杀的命令必须立刻落定：等满整个间隔会在信号到达后仍长时间占用调用方进程句柄。
    完成=线程.Event()#等待事件
    被杀=[False]#是否被杀
    def 中止():#中止回调
        """信号到达。"""
        被杀[0]=True#标记
        完成.set()#唤醒
    信号=state.get('signal')#取消信号
    if 信号 is not None and 信号.get('aborted') is True:#已中止则立刻
        return 信号退出码#信号码
    def 监听(事件名,回调,一次=False):#挂监听
        """对齐 addEventListener。"""
        监听们=信号.setdefault('_listeners',{})#监听表
        监听们.setdefault(事件名,[]).append((回调,一次))#登记
    if 信号 is not None and hasattr(信号,'get'):#有信号面
        if 'addEventListener' in 信号:#可调用面
            信号['addEventListener']('abort',中止,{'once':True})#挂一次
        else:#dict面
            监听('abort',中止,True)#挂
    定时=线程.Timer(秒数,完成.set)#定时结束
    定时.start()#启动
    完成.wait()#等待或被杀
    定时.cancel()#清定时器
    if 信号 is not None and 'removeEventListener' in 信号:#卸监听
        信号['removeEventListener']('abort',中止)#卸
    return 信号退出码 if 被杀[0] or (信号 is not None and 信号.get('aborted') is True) else 0#信号码或成功

def date程序(argv,io,state=None,fs=None):#date程序
    """打印ISO时间。"""
    io['out'](f"{日期时间.now(时区.utc).isoformat().replace('+00:00','Z')}\n")#ISO时间
    return 0#成功

def seq程序(argv,io,state=None,fs=None):#seq程序
    """打印数字序列。"""
    数字们=[]#解析缓冲
    for 值 in argv[1:]:#逐参
        try:#整数
            数字们.append(int(值,10))#收录
        except ValueError:#非法
            数字们.append(float('nan'))#占位
    第一=数字们[0] if len(数字们)>0 else None#第一
    第二=数字们[1] if len(数字们)>1 else None#第二
    第三=数字们[2] if len(数字们)>2 else None#第三
    起点=第一 if len(数字们)>1 else 1#起点
    步长=第二 if len(数字们)>2 else 1#步长
    if len(数字们)>2:#三参
        终点=第三#终点
    elif len(数字们)>1:#两参
        终点=第二#终点
    else:#一参
        终点=第一#终点
    if 终点 is None or not (终点==终点) or 步长==0:#非法边界
        io['err']('seq: expected numeric bounds\n')#诊断
        return 2#用法错
    值=起点#游标
    while (值<=终点 if 步长>0 else 值>=终点):#逐值
        io['out'](f'{值}\n')#打印
        值+=步长#推进
    return 0#成功

def printenv程序(argv,io,state,fs=None):#printenv程序
    """`printenv NAME`，脚本在名称是计算得出时更偏好它而非 `echo $NAME`。"""
    名=argv[1] if len(argv)>1 else None#变量名
    if 名 is None:#无名则列环境
        for 键,值 in sorted(state['environment'].items()):#打印
            io['out'](f'{键}={值}\n')#行
        return 0#成功
    值=读变量(state,名)#读变量
    if 值 is None:#未设置
        return 1#失败
    io['out'](f'{值}\n')#打印值
    return 0#成功

def 恒真(argv=None,io=None,state=None,fs=None):#恒真
    """true。"""
    return 0#成功

def 恒假(argv=None,io=None,state=None,fs=None):#恒假
    """false。"""
    return 1#失败

def 空命令(argv=None,io=None,state=None,fs=None):#空命令
    """冒号命令。"""
    return 0#成功

内建程序={#内建表
    'cd':cd程序,#切换目录
    'pwd':pwd程序,#打印目录
    'export':export程序,#导出
    'unset':unset程序,#取消设置
    'env':env程序,#打印环境
    'printenv':printenv程序,#打印变量
    'exit':exit程序,#退出
    'test':test程序,#测试
    '[':test程序,#[别名
    'sleep':sleep程序,#睡眠
    'date':date程序,#日期
    'seq':seq程序,#序列
    'true':恒真,#恒真
    'false':恒假,#恒假
    ':':空命令,#空命令
}#内建程序结束
