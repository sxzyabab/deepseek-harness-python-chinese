'web 子命令用 pywebbridge 打开 dsh 页面；其他入口仍未完成'
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

from flask import Response
def web启动(*,host:str,#绑定地址，拒绝0.0.0.0
    port:int,#端口，须为数字；0表示系统分配
    trusted_host:str=None,#信任的authority；官方可重复，这里只能收一个
    ):
    '在本进程里起 pywebbridge，握手后的窗口直接交给 dsh 页面。'
    from pywebbridge.服务 import 服务器
    from .源码.客户端.web.启动 import 网页应用入口
    if host=='0.0.0.0':
        报错('错误：网页只监听本机')
    if trusted_host is not None and trusted_host=='':
        报错('错误：--trusted-host 需要一个名字')
    应用=服务器()
    已挂=[]
    @应用.桥接页面路由('/')
    def 首页(窗口):
        try:
            文档=窗口.document
            根=文档.getElementById('root')
            if 根 is None:
                根=文档.createElement('div')
                根.id='root'
                文档.body.appendChild(根)
            入口=网页应用入口(根)
            入口.运行()
            已挂.append(入口)
        except Exception:
            import traceback
            traceback.print_exc()
            raise
    @应用.route('/favicon.ico')
    def 图标():
        return Response(大肥鱼图标_黑,mimetype='image/svg+xml')
    '/.well-known/appspecific/com.chrome.devtools.json'
    应用.启动(主机=host,端口=port,调试=True)

def 无头启动(*task:str):#任务词，空格拼接；全空白是用法错误
    ...#应用插件解析，不是启动器

大肥鱼图标_黑='''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="50.000000" height="50.000000" viewBox="0 0 50 50" fill="none">
	<path id="path" d="M48.8354 10.0479C48.3232 9.79199 48.1025 10.2798 47.8032 10.5278C47.7007 10.6079 47.6143 10.7119 47.5273 10.8076C46.7793 11.624 45.9048 12.1597 44.7622 12.0957C43.0923 12 41.666 12.5356 40.4058 13.8398C40.1377 12.2319 39.2476 11.272 37.8926 10.6558C37.1836 10.3359 36.4668 10.0156 35.9702 9.31982C35.6235 8.82373 35.5293 8.27197 35.356 7.72754C35.2456 7.3999 35.1353 7.06396 34.7651 7.00781C34.3633 6.94385 34.2056 7.2876 34.0479 7.57568C33.418 8.75195 33.1733 10.0479 33.1973 11.3599C33.2524 14.312 34.4736 16.6641 36.8999 18.3359C37.1758 18.5278 37.2466 18.7197 37.1597 19C36.9946 19.5757 36.7974 20.1357 36.624 20.7119C36.5137 21.0801 36.3486 21.1597 35.9624 21C34.6309 20.4321 33.481 19.5918 32.4644 18.5757C30.7393 16.8721 29.1792 14.9917 27.2334 13.52C26.7764 13.1758 26.3193 12.856 25.8467 12.5518C23.8618 10.584 26.1069 8.96777 26.627 8.77588C27.1704 8.57568 26.8159 7.8877 25.0591 7.896C23.3022 7.90381 21.6953 8.50391 19.647 9.30371C19.3477 9.42383 19.0322 9.51172 18.7095 9.58398C16.8501 9.22363 14.9199 9.14355 12.9033 9.37598C9.10596 9.80762 6.07275 11.6396 3.84326 14.7681C1.16455 18.5278 0.53418 22.7998 1.30664 27.2559C2.11768 31.9521 4.46582 35.8398 8.07373 38.8799C11.8159 42.0322 16.1255 43.5762 21.041 43.2803C24.0269 43.104 27.3516 42.6963 31.1016 39.4561C32.0469 39.936 33.0396 40.1279 34.686 40.272C35.9546 40.3921 37.1758 40.208 38.1211 40.0078C39.6021 39.688 39.4995 38.2881 38.9639 38.0322C34.623 35.9678 35.5762 36.8081 34.71 36.1279C36.9155 33.4639 40.2402 30.6958 41.54 21.728C41.6426 21.0161 41.5557 20.5679 41.54 19.9917C41.5322 19.6396 41.6108 19.5039 42.0049 19.4639C43.0923 19.3359 44.1479 19.0317 45.1167 18.4878C47.9292 16.9199 49.064 14.3438 49.3315 11.2559C49.3711 10.7837 49.3237 10.2959 48.8354 10.0479ZM24.3262 37.8398C20.1196 34.4639 18.0791 33.3521 17.2358 33.3999C16.4482 33.4482 16.5898 34.3682 16.7632 34.9678C16.9443 35.5601 17.1812 35.9683 17.5117 36.4878C17.7402 36.832 17.8979 37.3442 17.2832 37.728C15.9282 38.584 13.5728 37.4399 13.4624 37.3838C10.7207 35.7358 8.42822 33.5601 6.81348 30.584C5.25342 27.7197 4.34766 24.6479 4.19775 21.3677C4.1582 20.5757 4.38672 20.2959 5.15869 20.1519C6.17529 19.96 7.22314 19.9199 8.23926 20.0718C12.5327 20.7119 16.1885 22.6719 19.2529 25.7759C21.002 27.5439 22.3252 29.6558 23.6885 31.7202C25.1377 33.9121 26.6978 36 28.6831 37.7119C29.3843 38.312 29.9434 38.7681 30.479 39.104C28.8643 39.2881 26.1699 39.3281 24.3262 37.8398ZM26.3433 24.6001C26.3433 24.248 26.6191 23.9678 26.9658 23.9678C27.0444 23.9678 27.1152 23.9839 27.1782 24.0078C27.2651 24.04 27.3438 24.0879 27.4067 24.1602C27.5171 24.272 27.5801 24.4321 27.5801 24.6001C27.5801 24.9521 27.3042 25.2319 26.9575 25.2319C26.6108 25.2319 26.3433 24.9521 26.3433 24.6001ZM32.6064 27.8799C32.2046 28.0479 31.8027 28.1919 31.4165 28.208C30.8179 28.2397 30.1641 27.9922 29.8096 27.688C29.2583 27.2158 28.8643 26.9521 28.6987 26.1279C28.6279 25.7759 28.6675 25.2319 28.7305 24.9199C28.8721 24.248 28.7144 23.8159 28.2495 23.4238C27.8716 23.104 27.3911 23.0161 26.8633 23.0161C26.666 23.0161 26.4849 22.9277 26.3511 22.856C26.1304 22.7441 25.9492 22.4639 26.1226 22.1201C26.1777 22.0078 26.4458 21.7358 26.5088 21.688C27.2256 21.272 28.0527 21.4077 28.8169 21.7197C29.5259 22.0161 30.0615 22.5601 30.834 23.3281C31.6216 24.2559 31.7632 24.5117 32.2124 25.208C32.5669 25.752 32.8901 26.312 33.1104 26.9521C33.2446 27.3521 33.0713 27.6802 32.6064 27.8799Z" fill="#000" fill-opacity="1.000000" fill-rule="nonzero"/>
</svg>'''

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
    'web 子命令打开本机页面；其他入口仍未完成'
    令牌=sys.argv[1:]
    if len(令牌)>0 and 令牌[0]=='web':
        主机='127.0.0.1'#缺省只听本机
        端口=8080#缺省端口
        下标=1
        while 下标<len(令牌):
            当前=令牌[下标]
            if 当前 in ('-h','--help'):
                sys.stdout.write('用法: pydsh web [--host 127.0.0.1] [--port 8080]\n')
                return
            if 当前=='--host' or 当前.startswith('--host='):
                内联=当前.split('=',1)[1] if 当前.startswith('--host=') else None
                主机,下标=吃带值('--host',内联,下标,令牌,'错误：缺少 --host 的值')
                continue
            if 当前=='--port' or 当前.startswith('--port='):
                内联=当前.split('=',1)[1] if 当前.startswith('--port=') else None
                端口文本,下标=吃带值('--port',内联,下标,令牌,'错误：缺少 --port 的值')
                try:
                    端口=int(端口文本)
                except ValueError:
                    报错('错误：端口必须是整数')
                continue
            报错('错误：无法识别的 web 参数')
        web启动(host=主机, port=端口)
        return
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

if __name__ in {'__main__','__mp_main__'}:
    main()
