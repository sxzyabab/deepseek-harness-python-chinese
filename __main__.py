'尚未完成,请勿使用'
import argparse,inspect,sys,json
from dataclasses import dataclass
版本='0.0.0.dev0'

def 解析布尔(文本):
    值=文本.strip().lower()
    if 值 in ('1','true','yes','y','on'):
        return True
    if 值 in ('0','false','no','n','off'):
        return False
    raise argparse.ArgumentTypeError('不是布尔值: '+文本)

def 取类型转换(类型):
    if 类型 is inspect.Parameter.empty:
        return str
    if 类型 is bool:
        return 解析布尔
    if 类型 in (int,str,float):
        return 类型
    if 类型 is list:
        return str
    raise TypeError('不支持的参数类型: '+repr(类型))

def 从函数签名生成命令行参数(函数):#按函数签名生成argparse解析器
    签名=inspect.signature(函数)#取出参数种类、默认值、注解
    解析器=argparse.ArgumentParser()#空解析器
    for 名,参数 in 签名.parameters.items():#逐个形参
        种类=参数.kind#位置、*args、仅关键词、**kwargs
        if 种类 is inspect.Parameter.VAR_KEYWORD:#碰到**kwargs
            raise TypeError('不支持**'+名)#命令行映射不了不定关键词
        有默认=参数.default is not inspect.Parameter.empty#有没有默认值
        类型=参数.annotation#类型注解
        if 种类 is inspect.Parameter.VAR_POSITIONAL:#碰到*args
            元素类型=str if 类型 is inspect.Parameter.empty else 类型#没注解当字符串
            if 元素类型 is list:#注解写成了list
                元素类型=str#列表元素仍当字符串
            解析器.add_argument(名,nargs='*',type=取类型转换(元素类型),default=参数.default if 有默认 else [])#吃掉剩余位置参数
            continue#这个形参处理完
        if 类型 is list:#普通list参数
            if 种类 is inspect.Parameter.KEYWORD_ONLY or 有默认:#仅关键词或带默认
                解析器.add_argument('--'+名,dest=名,nargs='*',type=str,default=参数.default if 有默认 else [],required=(种类 is inspect.Parameter.KEYWORD_ONLY and not 有默认))#选项，可重复；仅关键词且无默认则必填
            else:#必选位置list
                解析器.add_argument(名,nargs='*',type=str)#位置上吃多个值
            continue#这个形参处理完
        if 类型 is bool and 有默认:#带默认的布尔，做成开关
            if 参数.default is False:#默认关
                解析器.add_argument('--'+名,dest=名,action='store_true')#写出则True
            elif 参数.default is True:#默认开
                解析器.add_argument('--no-'+名,dest=名,action='store_false')#写出则False
            else:#默认不是True/False
                raise TypeError('布尔默认值只能是True或False: '+名)#拒绝
            continue#这个形参处理完
        转换=取类型转换(类型)#int/str/float或布尔转换
        if 种类 is inspect.Parameter.KEYWORD_ONLY:#仅关键词
            解析器.add_argument('--'+名,dest=名,type=转换,default=参数.default if 有默认 else None,required=not 有默认)#无默认则必填选项
        elif 有默认:#普通可选参数
            解析器.add_argument('--'+名,dest=名,type=转换,default=参数.default)#带默认的选项
        else:#必选位置参数
            解析器.add_argument(名,type=转换)#位置必填
    return 解析器#交给parse_args


def 占位_main():
    命令行参数=vars(从函数签名生成命令行参数(运行).parse_args())
    运行(**命令行参数)

def 运行(*,
    profile:str,#选用$DSH_HOME/profiles/<name>，除裸-h外必填
    patch:str=None,#一份覆盖补丁路径；官方是可重复的--patch，这里只能收一个
    dump_config:bool=False,#打印组合后的有效配置后退出，不启动树
    dump_default_config:bool=False,#打印默认配置后退出，不启动树
    version:bool=False,#打印版本后退出
    ):
    if version:#版本模式优先
        print(版本)#与pyproject.toml一致
        return
    if dump_config and dump_default_config:#两种dump没有组合语义
        raise SystemExit('不能同时使用--dump-config和--dump-default-config')
    if dump_config or dump_default_config:#dump禁止再带应用参数，且不跑应用解析器
        raise SystemExit('dump需接到加载配置档与渲染配置转储')
    raise SystemExit('profile启动需叠patch、提供命令行快照再启动Loader树')#不要在这里调web启动/无头启动

def web启动(*,host:str,#绑定地址，拒绝0.0.0.0
    port:int,#端口，须为数字；0表示系统分配
    trusted_host:str=None,#信任的authority；官方可重复，这里只能收一个
    ):
    ...#应用插件解析，不是启动器

def 无头启动(*task:str):#任务词，空格拼接；全空白是用法错误
    ...#应用插件解析，不是启动器

##################################################################
@dataclass
class 启动信息:
    mode:str
    profile:str=None    
    defaultOnly:bool=False
    patches:list[str]=None
    args:list[str]=None

帮助示例='''
Examples:
  dsh --profile web                          boot the web profile (same as: dsh web)
  dsh --profile headless "run the tests"     answer one task, print the result, and exit
  dsh --profile tui --patch ./extra.yml      boot a custom profile with one extra overlay
  dsh --profile tui --resume <session>       arguments after the launcher flags reach the app
  dsh --profile web --help                   the web app's own flags and help
  dsh plugin --profile tui add <package>     install a plugin into the tui profile
'''

def 读版本():
    return 版本

def 报错(消息:str,错误码:int=1):
    sys.stderr.write(消息 if 消息.endswith('\n') else 消息+'\n')
    raise SystemExit(错误码)

def 打印启动器帮助():
    sys.stdout.write(
        'Usage: dsh [options] [args...]\n'
        'dsh: boot a DeepSeek Harness profile — an ordered stack of plugin-bundle patch layers under your own overrides.\n'
        'Arguments for the booted profile\'s app (see: dsh --profile <name> --help)\n'
        +帮助示例
    )
    raise SystemExit(0)

def 吃带值(标志,内联值,下标,令牌,缺值文案):
    if 内联值 is not None:
        return 内联值,下标+1
    下标+=1
    if 下标>=len(令牌):
        报错(缺值文案)
    return 令牌[下标],下标+1

def 解析启动调用(
    profile:str,
    patches:list,
    dumpConfig:bool,
    dumpDefaultConfig:bool,
    args:list,
    )->启动信息:
    if '' in patches:#--patch后面没给路径
        报错('错误：--patch 需要一个路径')
    if dumpConfig is not True and dumpDefaultConfig is not True:
        #两个dump都没开，按启动配置档走
        return 启动信息(
            mode='profile',
            profile=profile,
            patches=patches,
            args=args
            )
    if dumpConfig is True and dumpDefaultConfig is True:#两种dump不能一起用
        报错('错误：--dump-config 和 --dump-default-config 不能同时使用')
    #开了一个dump
    if len(args)>0:#dump不跑应用，不能再带应用参数
        报错('错误：转储配置不能带应用参数，收到了：'+
            ' '.join(json.dumps(a,ensure_ascii=False) for a in args))
    if dumpDefaultConfig is True and len(patches)>0:#默认转储只看组合包层
        报错('错误：--dump-default-config 只打印组合包层，不能带 --patch')
    return {
        'mode':'dump-config', #str
        'profile':profile, #str
        'defaultOnly':dumpDefaultConfig is True, #bool
        'patches':patches #list[str]
        }


def 存在父级选项(父级:dict)->bool:
    return (
        父级['profile'] is not None
        or 父级['patch'] is not None
        or 父级['dumpConfig'] is True
        or 父级['dumpDefaultConfig'] is True
    )

def 拒绝父级选项(子命令:str,选项:dict):
    '某些命令不允许带有父级选项'
    if 存在父级选项(选项):
        报错('error: '+子命令+' takes none of parent --profile, --patch, --dump-config, or --dump-default-config')

def 解析web(剩余:list,选项:dict):
    拒绝父级选项('web',选项)
    patches=[]
    dumpConfig=False
    dumpDefaultConfig=False
    下标=0
    while 下标<len(剩余):
        令牌=剩余[下标]
        if 令牌 in ('-V','--version'):
            print(读版本())
            raise SystemExit(0)
        if 令牌=='--':
            return 解析启动调用(
                'web',patches,
                dumpConfig,dumpDefaultConfig,
                剩余[下标+1:])
        if 令牌=='--patch' or 令牌.startswith('--patch='):
            内联=令牌.split('=',1)[1] if 令牌.startswith('--patch=') else None
            路径,下标=吃带值('--patch',内联,下标,剩余,'错误：--patch 需要一个路径')
            patches.append(路径)
            continue
        if 令牌=='--dump-config':
            dumpConfig=True
            下标+=1
            continue
        if 令牌=='--dump-default-config':
            dumpDefaultConfig=True
            下标+=1
            continue
        return 解析启动调用(
            'web',patches,
            dumpConfig,dumpDefaultConfig,
            剩余[下标:])
    return 解析启动调用(
        'web',patches,
        dumpConfig,dumpDefaultConfig,
        [])

def 解析plugin(剩余:list,选项:dict):
    拒绝父级选项('plugin',选项)
    profile=None
    args=[]
    下标=0
    while 下标<len(剩余):
        令牌=剩余[下标]
        if 令牌=='--profile' or 令牌.startswith('--profile='):
            内联=令牌.split('=',1)[1] if 令牌.startswith('--profile=') else None
            profile,下标=吃带值('--profile',内联,下标,剩余,'错误：--profile 需要一个名字')
            continue
        args.append(令牌)
        下标+=1
    if profile is None:
        报错('错误：--profile <name> 是必填的')
    if profile=='':
        报错('错误：--profile 需要一个名字')
    if len(args)==0:
        报错('错误：plugin 需要 pnpm 参数来转发（例如 add <package>）')
    return {
        'mode':'plugin',
        'profile':profile,
        'args':args
        }

def 解析dsh命令行参数(参数列表,版本)->启动信息:
    令牌=list(参数列表)
    profile=None
    patches=None
    dumpConfig=None
    dumpDefaultConfig=None
    下标=0
    while 下标<len(令牌):
        当前=令牌[下标]
        if 当前 in ('-V','--version'):
            print(版本)
            raise SystemExit(0)
        if 当前=='--':
            剩余=令牌[下标+1:]
            break
        if 当前=='--profile' or 当前.startswith('--profile='):
            内联=当前.split('=',1)[1] if 当前.startswith('--profile=') else None
            profile,下标=吃带值('--profile',内联,下标,令牌,'错误：--profile 需要一个名字')
            continue
        if 当前=='--patch' or 当前.startswith('--patch='):
            内联=当前.split('=',1)[1] if 当前.startswith('--patch=') else None
            路径,下标=吃带值('--patch',内联,下标,令牌,'错误：--patch 需要一个路径')
            if patches is None:
                patches=[]
            patches.append(路径)
            continue
        if 当前=='--dump-config':
            dumpConfig=True
            下标+=1
            continue
        if 当前=='--dump-default-config':
            dumpDefaultConfig=True
            下标+=1
            continue
        if 当前=='web':
            选项=启动信息(
                profile=profile,
                patches=patches,
                dumpConfig=dumpConfig,
                dumpDefaultConfig=dumpDefaultConfig
                )
            return 解析web(令牌[下标+1:],选项)
        if 当前=='plugin':
            选项=启动信息(
                profile=profile,
                patches=patches,
                dumpConfig=dumpConfig,
                dumpDefaultConfig=dumpDefaultConfig
                )
            return 解析plugin(令牌[下标+1:],选项)
        剩余=令牌[下标:]
        break
    else:
        剩余=[]
    选项=启动信息(
        profile=profile,
        patches=patches,
        dumpConfig=dumpConfig,
        dumpDefaultConfig=dumpDefaultConfig
        )
    if profile is None:
        if any(项 in ('-h','--help') for 项 in 剩余):
            打印启动器帮助()
        报错('错误：--profile <name> 是必填的')
    if profile=='':
        报错('错误：--profile 需要一个名字')
    return 解析启动调用(
        profile,
        patches or [],
        dumpConfig is True,
        dumpDefaultConfig is True,
        剩余
        )

def main():
    raise SystemExit('尚未完成,请勿使用')
    调用=解析dsh命令行参数(sys.argv[1:],读版本())
    模式=调用['mode']
    if 模式=='profile':
        跑配置(调用)
        return
    if 模式=='plugin':
        raise SystemExit(跑插件(调用['profile'],调用['args']))
    if 模式=='dump-config':
        跑转储(调用['profile'],调用['defaultOnly'],调用['patches'])
        return
    raise SystemExit('dsh: unhandled invocation mode '+json.dumps(调用,ensure_ascii=False))
