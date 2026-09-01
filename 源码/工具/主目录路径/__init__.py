"""DeepSeek Harness 用户数据共用的文件系统路径辅助。"""
import os,errno#路径与错误码
__all__=[#仅中文公开名
    '主目录名','默认主目录展示','主目录环境键','有错误码','规范化监视路径',
    '默认主目录','展开家目录路径','解析主目录','主目录路径','主目录展示',
]#公开面结束

主目录名='.dsh'#操作系统家目录下默认 DeepSeek Harness 主目录的目录名
默认主目录展示='~/'+主目录名#默认 DeepSeek Harness 主目录的稳定面向用户展示形式
主目录环境键='DSH_HOME'#覆盖默认 DeepSeek Harness 主目录的环境变量

def 有错误码(错误,码):#错误对象是否带某错误码
    """错误对象是否带某错误码。"""
    if 错误 is None:#空值
        return False#没有
    if getattr(错误,'code',None)==码:#已有 Node/服务码
        return True#命中
    if isinstance(错误,OSError):#宿主 OSError
        if 错误.errno==errno.ENOENT and 码=='ENOENT':#不存在
            return True#命中
        if 错误.errno==errno.ENOTDIR and 码=='ENOTDIR':#非目录
            return True#命中
    return False#未命中

def 规范化监视路径(路径):#规范化监视路径拼写
    """给原生文件系统监视器一份路径的规范拼写，即使最终分量尚不存在。最深的已存在祖先经 realpath 解析；后缀缺失时，还要证明该祖先是可枚举目录，再还原后缀。这防止 Windows 把普通文件祖先当成普通缺失，也防止短名别名与原生监视后端发出的长路径混用。"""
    当前=os.path.abspath(路径)#从相对当前目录的绝对路径开始
    缺失=[]#尚不存在、待还原的后缀分量
    while True:#向上找最深已存在祖先
        try:#尝试解析当前层真实路径
            规范=os.path.realpath(当前)#把现存祖先解析成规范路径
            if len(缺失)>0:#有缺失后缀，祖先必须是目录
                os.listdir(规范)#打开祖先以证明它是可枚举目录
            缺失.reverse()#按原顺序
            return os.path.join(规范,*缺失) if len(缺失)>0 else 规范#把缺失后缀接回
        except OSError as 错误:#realpath或listdir失败
            if not 有错误码(错误,'ENOENT'):#非缺失错误原样抛出
                raise 错误#原样抛出
            父路径=os.path.dirname(当前)#上溯一层父路径
            if 父路径==当前:#已到根仍缺失则无法继续
                raise 错误#无法继续
            缺失.append(os.path.basename(当前))#记下本层缺失分量
            当前=父路径#继续检查父路径

def 默认主目录():#默认主目录绝对路径
    """按平台路径规则解析默认 DeepSeek Harness 主目录。"""
    return os.path.join(os.path.expanduser('~'),主目录名)#操作系统家目录下的.dsh

def 展开家目录路径(路径):#展开家目录波浪号前缀
    """把受支持的波浪号前缀展开为操作系统家目录。"""
    if 路径=='~':#单独波浪号就是家目录
        return os.path.expanduser('~')#就是家目录
    if 路径.startswith('~/') or 路径.startswith('~\\'):#斜杠后接相对家目录的后缀
        return os.path.join(os.path.expanduser('~'),路径[2:])#相对家目录
    return 路径#无受支持前缀则原样返回

def 解析主目录(已配置=None,环境=None):#解析单根 harness 主目录
    """解析单根 DeepSeek Harness 主目录。优先级从高到低：显式配置路径、`$DSH_HOME`，然后 `~/.dsh`。harness 把全部用户数据放在一个根下。空或仅空白的 `$DSH_HOME` 视为未设置，因此空白覆盖绝不会把主目录解析成当前工作目录。"""
    if 环境 is None:#未传入环境映射
        环境=os.environ#进程环境
    来自环境=环境.get(主目录环境键)#读取DSH_HOME覆盖
    if 已配置 is not None:#配置优先
        选中=已配置#显式配置
    elif 来自环境 is not None and len(str(来自环境).strip())>0:#非空白环境变量
        选中=来自环境#环境覆盖
    else:#都没有
        选中=默认主目录()#默认~/.dsh
    return os.path.abspath(展开家目录路径(选中))#展开波浪号并规范化为绝对路径

def 主目录路径(*分段):#主目录下的拼接路径
    """把路径分段拼到已解析的 DeepSeek Harness 主目录上；空列表返回主目录本身。"""
    return os.path.join(解析主目录(),*分段)#在已解析主目录上拼接分段

def 主目录展示(已解析主目录):#主目录的面向用户标签
    """用符号形式描述已解析的 harness 主目录，供面向用户展示。从不返回绝对机器路径：默认主目录标为 `~/.dsh`，任何配置过的主目录标为 `$DSH_HOME`。"""
    return 默认主目录展示 if 已解析主目录==os.path.abspath(默认主目录()) else ('$'+主目录环境键)#默认用~/.dsh，覆盖用$DSH_HOME
