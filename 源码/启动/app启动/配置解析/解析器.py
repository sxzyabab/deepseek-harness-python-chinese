"""进程内配置包路由：把裸包请求导向世代表选定的目录。"""
import os,sys,json,threading#路径、导入钩、清单与线程数据
from .遗留链接 import 是否配置模块回退链接#遗留投影判定
__all__=[#仅中文公开名
    '裸包名','安装配置解析','登记工作线程解析','取工作线程登记',
]#公开面结束

工作线程解析键='@deepseek-ai/dsh-app-boot/profile-resolution'#工作线程环境键
_工作线程登记=threading.local()#本线程继承的世代

def 裸包名(请求):
    """把裸请求拆成包名；非包请求返回 None。"""
    if not 请求 or 请求[0] in ('.','/','\\','#') or ':' in 请求:#相对、绝对、导入或内建协议
        return None#非包
    if 请求 in sys.builtin_module_names:#内建
        return None#非包
    第一=请求.find('/')#第一斜杠
    if 请求[0]!='@':#非作用域
        return 请求 if 第一<0 else 请求[:第一]#整段或到斜杠
    if 第一<0:#残缺作用域
        return None#非包
    第二=请求.find('/',第一+1)#第二斜杠
    return 请求 if 第二<0 else 请求[:第二]#作用域包名

def 规范路径(路径):
    """能解析则走真实路径，否则收成绝对路径。"""
    try:#真实路径
        return os.path.realpath(路径)#规范
    except OSError:#世代可能在目录物化前命名作用域
        return os.path.abspath(路径)#绝对

def 前缀列表(路径):
    """配置路径与规范路径各一条带分隔符的前缀。"""
    配置=os.path.abspath(路径)+os.sep#配置前缀
    规范=规范路径(路径)+os.sep#规范前缀
    return [配置] if 规范==配置 else [配置,规范]#去重

def 编译世代(世代):
    """把不可变世代表编译成带缓存的查找结构。世代为 dict。"""
    配置路径=前缀列表(世代['profilesDir'])#配置根前缀
    活动=前缀列表(世代['profileDir']) if 世代.get('profileDir') is not None else []#活动配置前缀
    条目={}#名 → 条目
    for 项 in 世代['entries']:#逐条
        条目[项['name']]=项#记下
    return {#编译结果
        'entries':条目,#条目表
        'profilesDir':世代['profilesDir'],#配置根
        'profileDir':世代.get('profileDir'),#活动配置
        'profilePaths':配置路径,#配置前缀
        'profile':活动,#活动前缀
        'localPackageNames':set(世代.get('localPackageNames') or []),#本地包
        'shared':set(os.path.join(前缀,'node_modules') for 前缀 in 配置路径),#共享回退
        'esmRoutes':{},#URL 路由缓存
        'cjsRoutes':{},#路径路由缓存
    }#结束

def 起于(路径,根列表):
    """路径是否落在任一根前缀下。"""
    for 根 in 根列表:#逐根
        if 路径.startswith(根):#命中
            return True
    return False#否

def 原生包目录(父,名):
    """按 Node 风格从父路径向上找 node_modules/名。"""
    当前=os.path.dirname(父)#从父目录起
    while True:#向上
        候选=os.path.join(当前,'node_modules',名)#候选
        if os.path.exists(os.path.join(候选,'package.json')):#有清单
            return 候选#命中
        上一=os.path.dirname(当前)#上一级
        if 上一==当前:#到根
            return None#未找到
        当前=上一#继续

def 同一解析(左,右):
    """两条路径或 file URL 是否同一条目。"""
    if 左==右:#字面相同
        return True
    左路径=左[5:] if 左.startswith('file:') else 左#去掉 scheme
    右路径=右[5:] if 右.startswith('file:') else 右#去掉 scheme
    if 左路径.startswith('///'):#三斜杠
        左路径=左路径[3:]#本地
    if 右路径.startswith('///'):#三斜杠
        右路径=右路径[3:]#本地
    return 规范路径(左路径.replace('/',os.sep))==规范路径(右路径.replace('/',os.sep))#规范后相同

class 解析路由:
    """指向不可变世代数据的可变指针。"""

    def __init__(自身,世代):
        """编译初代。"""
        自身.当前=编译世代(世代)#当前编译

    def 替换(自身,世代):
        """原子发布加性包表；作用域或已有映射变化则抛。"""
        条目={}#下一代条目
        for 项 in 世代['entries']:#逐条
            条目[项['name']]=项#记下
        if 世代['profilesDir']!=自身.当前['profilesDir'] or 世代.get('profileDir')!=自身.当前['profileDir']:#作用域变
            raise Exception('配置解析: 一代不能改变其配置档作用域')#拒绝
        for 名,当前 in 自身.当前['entries'].items():#已有映射
            下一=条目.get(名)#下一代
            if (下一 is None or not 同一解析(当前['packageDir'],下一['packageDir'])
                    or not 同一解析(当前['declarer'],下一['declarer'])
                    or 当前.get('version')!=下一.get('version')
                    or 当前.get('scope')!=下一.get('scope')):#映射变
                raise Exception('配置解析: 替换 '+json.dumps(名,ensure_ascii=False)+' 需要重启进程')#需重启
        本地=set(世代.get('localPackageNames') or [])#新本地
        for 名 in 自身.当前['localPackageNames']:#旧本地
            if 名 not in 本地:#删了本地包
                raise Exception('配置解析: 移除本地包 '+json.dumps(名,ensure_ascii=False)+' 需要重启进程')#需重启
        for 名 in 本地:#新本地
            if 名 not in 自身.当前['localPackageNames'] and 名 in 自身.当前['entries']:#用本地覆盖已有回退
                raise Exception('配置解析: 在本地覆盖 '+json.dumps(名,ensure_ascii=False)+' 需要重启进程')#需重启
        自身.当前=编译世代(世代)#发布

    def 作用域路由(自身,请求,父路由,世代,风格):
        """按本地候选与世代表决定一条请求的路由。父路由为 dict。"""
        父=父路由['parent']#父路径
        配置根=父路由['profilesDir']#配置根
        请求表=父路由['requests']#请求缓存
        名=裸包名(请求)#包名
        if 名 is None:#非包
            return None#无路由
        目标=世代['entries'].get(名)#世代条目
        候选列表=[]#本地候选
        for 搜索 in _搜索路径(父,名):#逐搜索路径
            if os.path.abspath(搜索) in 世代['shared']:#撞上共享回退则停
                break#停
            候选=os.path.join(搜索,名)#候选目录
            if os.path.isdir(候选) or os.path.exists(os.path.join(候选,'package.json')):#存在
                遗留=False#是否托管投影
                for 前缀 in 世代['profile']:#活动配置前缀
                    if 候选==os.path.join(前缀,'node_modules',名) and 是否配置模块回退链接(前缀[:-1],名):#托管投影
                        遗留=True#是
                        break#停
                if not 遗留:#非托管
                    候选列表.append({'packageDir':候选})#收下
        if len(候选列表)>0:#有本地候选
            选中=候选列表[0]#第一条
            状态={'route':{'kind':'native','packageDir':选中['packageDir']},'packageDir':选中['packageDir']}#原生
            请求表[请求]=状态#缓存
            return 状态#返回
        合格=(目标 is not None and 目标.get('scope')=='installation') or (
            目标 is not None and 目标.get('scope')=='profile' and 父路由['activeProfile']
        )#安装级或活动配置级
        之后=os.path.join(os.path.dirname(配置根),'package.json')#回退之后的锚
        if 合格:#走世代回退
            路由={'kind':'fallback','entry':目标,'after':之后}#回退
        else:#回退之后
            路由={'kind':'after-fallback','parent':之后}#之后
        状态={'route':路由}#状态
        if 路由['kind']=='fallback':#回退可缓存
            请求表[请求]=状态#缓存
        return 状态#返回

    def 本地包路由(自身,请求,父路由,世代):
        """活动配置上的本地包走原生。"""
        名=裸包名(请求)#包名
        if 名 is None or not 父路由['activeProfile'] or 名 not in 世代['localPackageNames']:#不匹配
            return None#无
        状态={'route':{'kind':'native'}}#原生
        父路由['requests'][请求]=状态#缓存
        return 状态#返回

    def 路由网址(自身,请求,父网址):
        """按父 URL 路由一条 ESM 风格请求。"""
        世代=自身.当前#当前编译
        父路由=世代['esmRoutes'].get(父网址)#缓存
        if 父路由 is False:#已判定不在作用域
            return None#无
        if 父路由 is not None and 请求 in 父路由['requests']:#命中请求缓存
            return 父路由['requests'][请求]#缓存
        if 父路由 is None:#尚未分类父
            配置下标=_前缀下标(父网址,世代['profilePaths'])#配置根
            活动下标=_前缀下标(父网址,世代['profile'])#活动配置
            if 配置下标<0 and 活动下标<0:#都不在
                世代['esmRoutes'][父网址]=False#钉死不在
                return None#无
            try:#URL 转路径
                父=_文件网址转路径(父网址)#路径
            except ValueError:#非法 URL
                世代['esmRoutes'][父网址]=False#钉死
                return None#无
            if 配置下标>=0:#配置根
                根=世代['profilePaths'][配置下标]#前缀
            else:#活动配置
                根=世代['profile'][活动下标]#前缀
            父路由={#父路由
                'parent':父,#父路径
                'profilesDir':根[:-1],#去掉分隔符
                'activeProfile':活动下标>=0,#是否活动配置
                'requests':{},#请求缓存
            }#结束
            世代['esmRoutes'][父网址]=父路由#记下
        本地=自身.本地包路由(请求,父路由,世代)#本地优先
        if 本地 is not None:#命中
            return 本地#返回
        return 自身.作用域路由(请求,父路由,世代,'esm')#作用域

    def 包目录(自身,说明符,父网址):
        """不要求导出即可定位裸包目录。"""
        名=裸包名(说明符)#包名
        if 名 is None:#非包
            return None#缺席
        状态=自身.路由网址(说明符,父网址)#路由
        if 状态 is not None and 状态['route']['kind']=='fallback':#世代回退
            return 状态['route']['entry']['packageDir']#目录
        if 状态 is not None and 状态.get('packageDir') is not None:#已解析目录
            return 状态['packageDir']#目录
        try:#父路径
            if 状态 is not None and 状态['route']['kind']=='after-fallback':#之后
                父=状态['route']['parent']#锚
            else:#父 URL
                父=_文件网址转路径(父网址)#路径
        except ValueError:#非法
            return None#缺席
        找到=原生包目录(父,名)#原生查找
        if 状态 is not None and 找到 is not None:#可缓存
            状态['packageDir']=找到#记下
        return 找到#目录

def _搜索路径(父,名):
    """从父路径向上列出 node_modules 搜索目录。"""
    路径=[]#列表
    当前=os.path.dirname(父)#起始
    while True:#向上
        路径.append(os.path.join(当前,'node_modules'))#搜索
        上一=os.path.dirname(当前)#上一级
        if 上一==当前:#到根
            return 路径#列表
        当前=上一#继续

def _前缀下标(值,前缀列表):
    """值落在哪条前缀下；没有则 -1。"""
    for 下标,前缀 in enumerate(前缀列表):#逐条
        转='file:///'+前缀.replace('\\','/') if not 值.startswith('file:') else 值#对齐
        if 值.startswith(前缀) or 转.startswith('file:///'+前缀.replace('\\','/')):#命中
            return 下标#下标
        if 值.startswith('file:///'+前缀.replace('\\','/')):# URL 命中
            return 下标#下标
    return -1#没有

def _文件网址转路径(网址):
    """file URL 转本地路径。"""
    if not 网址.startswith('file:'):#已是路径
        return 网址#原样
    路径=网址[5:]#去掉 scheme
    if 路径.startswith('///'):#三斜杠
        路径=路径[3:]#本地
    elif 路径.startswith('//'):#双斜杠
        路径=路径[2:]#本地
    return 路径.replace('/',os.sep)#分隔符

def 断言等价(实际,期望,请求,父):
    """校验与世代解析一致。"""
    if 同一解析(实际,期望):#相同
        return#通过
    raise Exception(
        '配置解析不一致: 请求 '+json.dumps(请求,ensure_ascii=False)+' 的磁盘结果与世代结果不同'
    )#不一致

class _配置查找器:
    """按世代表重定向裸导入的 meta_path 查找器。"""

    def __init__(自身,路由,行为):
        """绑路由与行为。"""
        自身.路由=路由#路由
        自身.行为=行为#enforce 或 verify

    def find_spec(自身,全名,路径,目标=None):
        """仅处理裸包顶层名。"""
        名=裸包名(全名)#包名
        if 名 is None or 名!=全名:#子模块或非包
            return None#交给其余查找器
        return None#包目录 API 已覆盖；导入仍走原生以免抢标准库

def 安装配置解析(世代,行为='enforce'):
    """在本进程安装一代配置解析。返回可替换世代或恢复原生的登记。"""
    路由=解析路由(世代)#路由
    查找器=_配置查找器(路由,行为)#查找器
    sys.meta_path.insert(0,查找器)#插入最前
    配置路径=前缀列表(世代['profilesDir'])#配置前缀
    if 世代.get('profileDir') is not None:#有活动配置
        配置路径=配置路径+前缀列表(世代['profileDir'])#并上
    配置网址=['file:///'+前缀.replace('\\','/') for 前缀 in 配置路径]#URL 前缀

    def 包目录(说明符,父网址):
        """公开包目录查找；verify 时对照原生。"""
        期望=路由.包目录(说明符,父网址)#世代
        if 行为!='verify' or not 起于(父网址,配置网址):#不校验
            return 期望#世代
        名=裸包名(说明符)#包名
        if 名 is None:#非包
            return 期望#原样
        try:#父路径
            父=_文件网址转路径(父网址)#路径
        except ValueError:#非法
            return 期望#原样
        实际=原生包目录(父,名)#磁盘
        if 实际 is None and 期望 is None:#都没有
            return 期望#通过
        if 实际 is not None and 期望 is not None and 同一解析(实际,期望):#相同
            return 期望#通过
        raise Exception(
            '配置解析不一致: 请求 '+json.dumps(说明符,ensure_ascii=False)+' 的磁盘选择与世代选择不同'
        )#不一致

    def 替换(下一):
        """替换世代。"""
        路由.替换(下一)#替换

    def 拆除():
        """恢复原生查找。"""
        if 查找器 in sys.meta_path:#仍在
            sys.meta_path.remove(查找器)#去掉

    return {'packageDir':包目录,'replace':替换,'dispose':拆除,'包目录':包目录,'替换':替换,'拆除':拆除}#登记

def 登记工作线程解析(世代,行为='enforce'):
    """为随后创建的工作线程发布一代。返回恢复先前数据的拆除器。"""
    先前=getattr(_工作线程登记,'值',None)#先前
    _工作线程登记.值={'generation':世代,'behavior':行为}#发布
    def 恢复():
        """恢复先前。"""
        _工作线程登记.值=先前#恢复
    return 恢复#拆除器

def 取工作线程登记():
    """读取本线程继承的配置解析登记。"""
    return getattr(_工作线程登记,'值',None)#登记或 None
