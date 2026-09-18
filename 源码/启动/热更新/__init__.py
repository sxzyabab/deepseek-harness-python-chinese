"""串行化的模块与配置档配置重载。"""
import copy,json,os,re,sys,threading#路径、JSON、正则、线程与模块表
from watchfiles import watch as 监视变化,Change as 变化种类#内核文件监视
from ...依赖 import cordis#Cordis 运行时
from ...依赖.schemastery import 字符串字段,列表字段,自然数字段#配置字段
from ...依赖.工具 import 路径转文件url,文件url转路径#路径与 file URL 互转
from .错误 import 处理错误#构建失败诊断
from .监视配置 import 监视配置 as 精确监视配置#精确补丁路径监视
from ..app启动 import (#应用启动面
    读配置清单,配置补丁文件名,加载可选补丁,加载配置目录,#配置档读写
    启动包含表,未激活条目,激活诊断,启动错误,组合条目,#根 Include 与诊断
)#导入结束

服务=cordis.服务#服务基类
__all__=['热更新','重载信息']#仅中文公开名；Cordis 槽英文别名不入表

#常量
监视防抖毫秒=100#监视线程内防抖毫秒
遥测行编号='session-telemetry-otel'#遥测行 id
事件对照={#watchfiles 变化种类到中文事件名
    变化种类.added:'新增',#新增
    变化种类.modified:'修改',#修改
    变化种类.deleted:'删除',#删除
}#对照结束

#工具
def 规范路径(文件名):
    """按真实路径规范文件名；缺失时沿父目录回溯再拼回。"""
    try:#真实路径
        return os.path.realpath(文件名)#命中
    except OSError as 错误:#失败
        if getattr(错误,'errno',None) not in (2,3) and getattr(错误,'winerror',None)!=2:#非缺失
            raise#原样抛出
        父=os.path.dirname(文件名)#父目录
        if 父==文件名:#已到根
            raise#原样抛出
        return os.path.normpath(os.path.join(规范路径(父),os.path.basename(文件名)))#父规范后拼回

def 通配命中(文本,通配式):
    """按 glob 规则判断相对路径是否命中，支持 **、* 与 ?。"""
    文本=文本.replace('\\','/')#正斜杠
    通配式=通配式.replace('\\','/')#正斜杠
    段=[]#正则片段
    下标=0#扫描下标
    while 下标<len(通配式):#逐字符
        字=通配式[下标]#当前字符
        if 字=='*':#星号
            if 下标+1<len(通配式) and 通配式[下标+1]=='*':#双星
                段.append('.*')#跨目录
                下标+=2#吃掉 **
                continue#下一段
            段.append('[^/]*')#单层
            下标+=1#前进
        elif 字=='?':#单字符
            段.append('[^/]')#单字符
            下标+=1#前进
        else:#字面量
            段.append(re.escape(字))#转义
            下标+=1#前进
    return re.fullmatch(''.join(段),文本) is not None#整串匹配

def 是否外部模块(网址):
    """内建模块与第三方包不参与热更新。"""
    return 网址.startswith('node:') or '/node_modules/' in 网址 or '/site-packages/' in 网址#外部

class 重载信息:
    """一个待热更新插件的入口网址与运行时。"""
    def __init__(自身,入口网址,运行时):
        """保存入口网址与它的插件运行时。"""
        自身.入口网址=入口网址#模块网址
        自身.运行时=运行时#插件运行时

class 缓存备份:
    """一轮热更新里被清掉的模块缓存，失败时能原样放回去。"""
    def __init__(自身,内部加载器):
        """记下要操作的加载缓存。"""
        自身.内部加载器=内部加载器#内部加载器
        自身.加载缓存={}#网址到模块任务
        自身.模块表={}#模块名到模块对象

    def 清掉(自身,网址):
        """清掉一个网址在加载缓存与模块表里的记录。"""
        加载缓存=getattr(自身.内部加载器,'loadCache',None)#ESM 缓存
        if isinstance(加载缓存,dict):#字典缓存
            自身.加载缓存[网址]=加载缓存.pop(网址,None)#备份并清
        try:#本地路径
            规范=os.path.normpath(os.path.abspath(文件url转路径(网址)))#本地路径
        except Exception:#非 file URL
            return#只清加载缓存
        for 模块名,模块 in list(sys.modules.items()):#扫模块表
            文件=getattr(模块,'__file__',None)#模块文件
            if 文件 and os.path.normpath(os.path.abspath(文件))==规范:#命中
                自身.模块表[模块名]=模块#备份
                del sys.modules[模块名]#清掉

    def 回滚(自身):
        """把备份的模块缓存原样放回去。"""
        加载缓存=getattr(自身.内部加载器,'loadCache',None)#ESM 缓存
        if 加载缓存 is not None:#有缓存
            for 网址,任务 in 自身.加载缓存.items():#逐项
                if 任务 is not None:#有备份
                    加载缓存[网址]=任务#放回
        for 模块名,模块 in 自身.模块表.items():#模块表
            sys.modules[模块名]=模块#放回

#
class 热更新(服务):
    """监视源文件与配置档补丁，串行重载受影响的插件入口。"""
    def __init__(自身,上下文,配置):
        """登记 hmr 服务并解析基准目录。"""
        服务.__init__(自身,上下文,'hmr')#服务键线协议
        自身.配置=配置#插件配置
        自身.拥有上下文=上下文#拥有方上下文
        自身.__dict__[服务.初始化]=自身.初始化#依赖就绪后再监视
        自身.内部加载器=getattr(自身.所属上下文.加载器,'内部加载器',None)#模块图
        if 自身.内部加载器 is None:#拿不到
            raise RuntimeError('--expose-internals is required for HMR service')#拒绝
        基准=配置.get('base') if isinstance(配置,dict) else None#配置基准
        基准网址=getattr(上下文,'基准网址',None)#上下文基准
        if 基准网址:#有基准网址
            文本=str(基准网址)#统一字符串
            根目录=文件url转路径(文本) if 文本.startswith('file:') else os.path.abspath(文本)#本地根
        else:#无基准
            根目录=os.getcwd()#工作目录
        自身.基准目录=os.path.normpath(os.path.join(根目录,基准 or '.'))#监视基准
        自身.配置路径集=set()#已登记配置路径
        自身.暂存集=set()#待处理模块网址
        自身.外部集=set()#入口依赖，变了整进程退出
        自身.接受集=set()#应重载网址
        自身.拒绝集=set()#不应重载网址
        自身.监视器停止=None#主监视停止信号
        自身.监视线程=None#主监视线程
        自身.关闭中=False#是否已拆除
        自身.队列锁=threading.Lock()#独占队列
        自身.事务本地=threading.local()#嵌套事务标记
        自身.应用就绪事件=threading.Event()#应用就绪门闩
        自身.应用就绪值=True#默认已就绪
        自身.应用就绪事件.set()#放行
        自身.取外层栈=lambda:[]#省略 HMR 帧

    def 独占执行(自身,操作):
        """串行化调用方变更与自动重载路径；禁止嵌套。"""
        if getattr(自身.事务本地,'执行中',False):#嵌套
            raise RuntimeError('HMR transactions cannot be nested')#拒绝
        with 自身.队列锁:#串行
            if 自身.关闭中:#已拆除
                raise RuntimeError('HMR is disposed')#拒绝
            自身.事务本地.执行中=True#进入事务
            try:#执行
                return 操作()#结果
            finally:#收尾
                自身.事务本地.执行中=False#离开事务

    def 跑重载(自身,操作):
        """等应用就绪后再独占执行重载体。"""
        def 体():
            """门闩通过才跑。"""
            自身.应用就绪事件.wait()#等待
            if 自身.应用就绪值:#允许
                操作()#执行
        return 自身.独占执行(体)#独占

    def 事务中(自身):
        """当前线程是否正处于 HMR 事务内。"""
        return getattr(自身.事务本地,'执行中',False) is True#事务旗

    def 监视配置(自身,文件名,刷新):
        """经独占队列监视一条配置路径；返回拆除器。"""
        解析=os.path.abspath(文件名)#绝对路径
        路径列表=[解析,规范路径(文件名)]#原路径与规范路径
        if any(路径 in 自身.配置路径集 for 路径 in 路径列表):#重复
            raise RuntimeError('config path already registered: '+文件名)#拒绝
        for 路径 in 路径列表:#占用
            自身.配置路径集.add(路径)#登记
        try:#挂监视
            def 刷新体():
                """把刷新送进独占重载队列。"""
                自身.跑重载(刷新)#串行
            拆除=精确监视配置(自身.拥有上下文,文件名,自身.配置,刷新体,自身.事务中)#精确监视
            def 包装拆除():
                """拆除监视并释放路径占用。"""
                拆除()#拆精确监视
                for 路径 in 路径列表:#释放
                    自身.配置路径集.discard(路径)#摘掉
            return 包装拆除#拆除器
        except BaseException:#失败
            for 路径 in 路径列表:#回滚占用
                自身.配置路径集.discard(路径)#摘掉
            raise#原样抛出

    def 初始化(自身):
        """打开配置档与模块监视；yield 拆除器。"""
        def 清理():
            """关闭主监视并排空独占队列。"""
            自身.关闭中=True#标记拆除
            自身.应用就绪值=False#取消等待中的重载
            自身.应用就绪事件.set()#唤醒
            if 自身.监视器停止 is not None:#有停止信号
                自身.监视器停止.set()#停止
            if 自身.监视线程 is not None and 自身.监视线程.is_alive():#线程仍活
                自身.监视线程.join()#等待
            if not 自身.事务中():#事务外排空
                with 自身.队列锁:#占锁即排空
                    pass#空
        yield 清理#先交拆除
        配置档=自身.拥有上下文.获取服务('profileContext',False)#配置档上下文
        if 配置档 is None:#属性面
            配置档=getattr(自身.拥有上下文,'profileContext',None)#回落
        if 配置档 is not None:#有配置档
            就绪=自身.拥有上下文.获取服务('appReady',False)#应用就绪
            if 就绪 is None:#缺少
                raise RuntimeError('Profile HMR requires application readiness')#拒绝
            自身.应用就绪值=False#等就绪
            自身.应用就绪事件.clear()#关门
            def 当就绪():
                """应用已就绪。"""
                自身.应用就绪值=True#放行
                自身.应用就绪事件.set()#唤醒
            取消就绪=就绪.onReady(当就绪)#订阅
            def 拆就绪():
                """取消就绪订阅并拒绝后续重载。"""
                取消就绪()#取消
                自身.应用就绪值=False#拒绝
                自身.应用就绪事件.set()#唤醒等待方
                return None#无额外拆除
            yield 拆就绪#登记
            清单路径=os.path.join(配置档['dir'],'package.json')#清单
            补丁文件=[配置档['patchPath'],os.path.join(配置档['home'],配置补丁文件名)]#两层用户补丁
            上次输入=[None]#输入指纹
            上次组合包=[json.dumps(list(配置档.get('startedBundles') or []),ensure_ascii=False)]#启动组合包
            def 读配置档补丁():
                """内联读当前组合包层与用户补丁。"""
                配置=加载配置目录('dsh',配置档['dir'],配置档['installAnchor'],{'userLayer':False})#无用户层
                层补丁=[]#层
                for 层 in 配置.get('layers') or []:#各层
                    层补丁.extend(层.get('patches') or [])#展开
                用户=加载可选补丁('dsh',配置档['patchPath']) or []#用户层
                主目录=加载可选补丁('dsh',os.path.join(配置档['home'],配置补丁文件名)) or []#主目录层
                补丁=copy.deepcopy(层补丁+用户+主目录+list(配置档.get('overlays') or []))#脱离
                有遥测=any((行.get('id')==遥测行编号) for 行 in 组合条目([补丁]))#遥测行
                if (配置档.get('telemetryDisabledEnv') or '')!='' and 有遥测:#需禁用
                    补丁.append({'id':遥测行编号,'disabled':True})#追加
                return 补丁#有序补丁
            def 应用补丁(补丁):
                """经根 Include 更新补丁并等待激活诊断。"""
                条目=启动包含表.get(id(自身.拥有上下文.根))#根 Include
                if 条目 is None:#缺失
                    raise 启动错误('dsh: profile reload requires the root Include entry')#拒绝
                旧配置=条目.选项.get('config') if hasattr(条目,'选项') else {}#原配置
                非补丁={键:值 for 键,值 in (旧配置 or {}).items() if 键!='patches'}#去掉旧补丁
                条目.更新({'config':{**非补丁,'patches':补丁}})#事务更新
                加载器=自身.拥有上下文.获取服务('加载器',False)#Loader
                if 加载器 is not None:#仍在
                    加载器.等待()#等结算
                    for 插件配置 in 加载器.列出插件配置():#每条
                        光纤=插件配置.纤程#纤程
                        if 光纤 is not None:#有
                            try:#收拒绝
                                光纤.等待()#等待
                            except Exception:#不打断
                                pass#继续
                失败=未激活条目(自身.拥有上下文.根)#审计
                if len(失败)>0:#有失败
                    raise 启动错误(激活诊断('dsh','warning',失败).rstrip())#拒绝
            def 刷新配置档(仅清单):
                """清单或补丁变化时重读并应用。"""
                组合包=json.dumps((((读配置清单('dsh',配置档['dir']).get('dsh') or {}).get('profile') or {}).get('bundles') or []),ensure_ascii=False)#当前组合包
                if 仅清单 and 组合包==上次组合包[0]:#清单未变
                    return#跳过
                片段=[组合包]#指纹片段
                for 文件 in 补丁文件:#两层补丁
                    try:#读文本
                        with open(文件,'r',encoding='utf-8') as 句柄:#打开
                            片段.append(句柄.read())#正文
                    except FileNotFoundError:#缺失
                        片段.append(None)#空层
                输入=json.dumps(片段,ensure_ascii=False)#指纹
                if 输入==上次输入[0]:#无变化
                    return#跳过
                补丁=读配置档补丁()#重读
                应用补丁(补丁)#应用
                上次输入[0]=输入#推进
                上次组合包[0]=组合包#推进
            for 文件 in 补丁文件:#监视补丁
                自身.监视配置(文件,lambda 文件=文件:刷新配置档(False))#全量
            自身.监视配置(清单路径,lambda:刷新配置档(True))#仅清单
        根列表=自身.配置.get('root') or []#监视根
        if 自身.配置.get('base'):#有基准
            自身.所属上下文.日志.信息('watching %o in %s',根列表,自身.基准目录)#带基准
        else:#无基准
            自身.所属上下文.日志.信息('watching %o',根列表)#不带基准
        监视基准=os.path.realpath(自身.基准目录)#真实基准
        自身.外部集=自身.收集框架依赖()#入口依赖
        if len(根列表)>0:#需要主监视
            自身.打开主监视(监视基准,根列表)#启动

    def 收集框架依赖(自身):
        """从进程入口出发收集框架自身依赖的模块网址。"""
        if len(sys.argv)<1 or not sys.argv[0]:#无入口
            return set()#空
        加载缓存=getattr(自身.内部加载器,'loadCache',None)#缓存
        if 加载缓存 is None:#无图
            return set()#空
        入口=加载缓存.get(路径转文件url(os.path.abspath(sys.argv[0])))#入口任务
        return 自身.收集依赖(入口) if 入口 is not None else set()#依赖集

    def 打开主监视(自身,监视基准,根列表):
        """在后台线程监视模块根，变更经防抖进入独占队列。"""
        停止=threading.Event()#停止信号
        自身.监视器停止=停止#保存
        忽略模式=自身.配置.get('ignored') or []#忽略
        变更集=set()#相对路径批
        变更锁=threading.Lock()#保护变更集
        def 触发派发():
            """防抖后把变更集交给独占队列。"""
            with 变更锁:#快照
                批次=set(变更集)#拷贝
                变更集.clear()#清空
            自身.派发变更(监视基准,批次)#派发
        防抖派发=自身.所属上下文.防抖(触发派发,自身.配置.get('debounce') or 100)#防抖
        def 忽略路径(绝对路径):
            """任一忽略模式命中相对路径时为真。"""
            try:#相对
                相对=os.path.relpath(绝对路径,监视基准).replace('\\','/')#相对
            except ValueError:#跨盘
                return True#忽略
            return any(通配命中(相对,式) for 式 in 忽略模式)#命中
        def 现存根():
            """仍存在的绝对监视根。"""
            结果=[]#根
            for 根 in 根列表:#逐根
                绝对=根 if os.path.isabs(根) else os.path.join(监视基准,根)#绝对
                绝对=os.path.abspath(绝对)#规范
                if os.path.exists(绝对):#存在
                    结果.append(绝对)#收下
            return 结果#列表
        def 循环():
            """内核监视循环。"""
            while not 停止.is_set():#直到停止
                根=现存根()#当前根
                if not 根:#无可监视
                    停止.wait(0.5)#短等
                    continue#再试
                try:#监视
                    for 批次 in 监视变化(*根,stop_event=停止,debounce=监视防抖毫秒):#批次
                        for 种类,路径 in 批次:#逐项
                            if 忽略路径(路径):#忽略
                                continue#下一项
                            if 种类==变化种类.deleted and os.path.isdir(路径):#目录删除
                                continue#跳过
                            try:#相对路径
                                相对=os.path.relpath(os.path.abspath(路径),监视基准)#相对
                            except ValueError:#跨盘
                                continue#跳过
                            with 变更锁:#入批
                                变更集.add(相对.replace('\\','/'))#相对路径
                            防抖派发()#派发
                except Exception as 错误:#单轮失败
                    if 停止.is_set():#关闭
                        return#退出
                    自身.所属上下文.日志.警告(错误)#记警告
                    停止.wait(监视防抖毫秒/1000)#避空转
        线=threading.Thread(target=循环,daemon=True)#监视线程
        自身.监视线程=线#保存
        线.start()#启动

    def 派发变更(自身,监视基准,批次):
        """把一批路径变更分类为 Include 刷新、模块暂存或整进程退出。"""
        def 体():
            """独占体内处理。"""
            自身.应用就绪事件.wait()#等就绪
            if not 自身.应用就绪值:#已取消
                return#跳过
            包含集=set()#Include
            整重载=False#是否退出
            加载器=自身.所属上下文.加载器#加载器
            for 相对 in 批次:#逐路径
                文件名=规范路径(os.path.join(监视基准,相对))#规范绝对
                配置文件名=os.path.abspath(os.path.join(自身.基准目录,相对))#按配置基准
                if 文件名 in 自身.配置路径集 or 配置文件名 in 自身.配置路径集:#配置监视
                    continue#交给精确监视
                网址=路径转文件url(文件名)#模块网址
                if 网址 in 自身.外部集:#框架依赖
                    整重载=True#整进程
                    continue#下一项
                加载缓存=getattr(自身.内部加载器,'loadCache',None)#缓存
                if 加载缓存 is not None and 网址 in 加载缓存:#已加载模块
                    自身.暂存集.add(网址)#暂存
                    continue#下一项
                命中包含=None#Include
                for 插件配置 in 加载器.列出插件配置():#扫树
                    子树=getattr(插件配置,'子树',None)#子树
                    if 子树 is None:#无
                        continue#下一条
                    子文件=getattr(子树,'文件名',None)#配置文件
                    if 子文件 in (文件名,配置文件名):#命中
                        命中包含=子树#记下
                        break#停
                if 命中包含 is not None:#Include
                    包含集.add(命中包含)#收集
                else:#无处理器
                    自身.所属上下文.广播('hmr/change',网址)#广播
            if not 整重载 and len(包含集)==0 and len(自身.暂存集)==0:#无事
                return#结束
            if 整重载:#框架变了
                加载器.退出()#宿主重启
                return#结束
            for 包含 in 包含集:#刷新 Include
                包含.刷新()#读文件
            if len(自身.暂存集)>0:#有模块
                try:#部分重载
                    自身.部分重载()#重载
                finally:#清暂存
                    自身.暂存集=set()#清空
            加载器.等待()#等树
        try:#独占
            自身.独占执行(体)#执行
        except Exception as 错误:#失败
            自身.所属上下文.日志.警告(错误)#警告

    def 取链接(自身,网址):
        """取出该模块已链接的子模块网址。"""
        加载缓存=getattr(自身.内部加载器,'loadCache',None)#缓存
        if 加载缓存 is None:#无图
            return []#空
        任务=加载缓存.get(网址)#模块任务
        if 任务 is None:#未加载
            return []#空
        链接=getattr(任务,'linked',None)#子模块
        if 链接 is None:#无
            return []#空
        if callable(链接):#惰性
            链接=链接()#求值
        return [项.url if hasattr(项,'url') else str(项) for 项 in 链接]#网址列表

    def 收集依赖(自身,任务,已忽略=None):
        """从一个模块任务出发，递归收集属于用户代码的依赖网址。"""
        已忽略=已忽略 or set()#忽略集
        依赖=set()#结果
        def 遍历(当前):
            """跳过内建与第三方。"""
            网址=getattr(当前,'url',None)#网址
            if 网址 is None or 网址 in 已忽略 or 网址 in 依赖 or 是否外部模块(网址):#跳过
                return#结束
            依赖.add(网址)#记入
            for 子网址 in 自身.取链接(网址):#子
                加载缓存=getattr(自身.内部加载器,'loadCache',None)#缓存
                子=加载缓存.get(子网址) if 加载缓存 is not None else None#子任务
                if 子 is not None:#有任务
                    遍历(子)#递归
                elif not 是否外部模块(子网址):#仅网址
                    依赖.add(子网址)#记入
        遍历(任务)#从根
        return 依赖#依赖集

    def 分析变更(自身):
        """把暂存变更沿依赖方向扩散成接受集与拒绝集。"""
        自身.接受集=set(自身.暂存集)#直接改动
        自身.拒绝集=set(自身.外部集)#框架拒绝
        待定=[]#待判定
        for 网址 in 自身.暂存集:#直接改动
            for 子 in 自身.取链接(网址):#子模块
                if 子 not in 自身.接受集 and 子 not in 自身.拒绝集 and not 是否外部模块(子):#候选
                    待定.append(子)#入队
        while 待定:#推进
            有推进=False#本轮
            下标=0#扫描
            while 下标<len(待定):#扫
                网址=待定[下标]#当前
                接受=False#是否接受
                拒绝=True#暂定拒绝
                for 子 in 自身.取链接(网址):#子
                    if 子 in 自身.拒绝集 or 是否外部模块(子):#无关
                        continue#下一条
                    if 子 in 自身.接受集:#子要重载
                        接受=True#自身也要
                        break#停
                    拒绝=False#未定
                    if 子 not in 待定:#新节点
                        待定.append(子)#入队
                        有推进=True#推进
                if 接受 or 拒绝:#可定
                    待定.pop(下标)#出队
                    有推进=True#推进
                    (自身.接受集 if 接受 else 自身.拒绝集).add(网址)#归类
                else:#未定
                    下标+=1#下一个
            if not 有推进:#卡死
                break#停
        自身.拒绝集.update(待定)#剩余拒绝

    def 解析说明符(自身,说明符,父网址):
        """按内部加载器版本解析模块说明符，返回带 url 的结果。"""
        版本=getattr(自身.内部加载器,'version',None)#版本
        if 版本=='v1':#Node v1
            return 自身.内部加载器.resolve(说明符,父网址,{})#解析
        if 版本=='v2':#Node v2
            return 自身.内部加载器.resolveSync(父网址,{'specifier':说明符,'attributes':{}})#同步
        if 说明符.startswith('file:') or '://' in 说明符:#已是网址
            class 结果:
                """解析结果。"""
                url=说明符#网址
            return 结果()#结果
        if os.path.isabs(说明符):#绝对路径
            class 结果:
                """解析结果。"""
                url=路径转文件url(说明符)#网址
            return 结果()#结果
        父路径=文件url转路径(str(父网址)) if 父网址 and str(父网址).startswith('file:') else (str(父网址) if 父网址 else os.getcwd())#父目录
        if os.path.isfile(父路径):#父是文件
            父路径=os.path.dirname(父路径)#改目录
        候选=os.path.abspath(os.path.join(父路径,说明符))#拼接
        class 结果:
            """解析结果。"""
            url=路径转文件url(候选)#网址
        return 结果()#结果

    def 部分重载(自身):
        """清掉接受集的模块缓存，用新代码重挂受影响的插件。"""
        自身.分析变更()#分类
        重载表=自身.收集待重载插件()#待重载
        if not 重载表:#无
            自身.暂存集=set()#清暂存
            return#结束
        备份=缓存备份(自身.内部加载器)#备份
        for 网址 in 自身.接受集:#清缓存
            备份.清掉(网址)#逐个
        新插件表={}#入口到新插件
        try:#重导入
            for 信息 in 重载表.values():#逐个入口
                导出=自身.所属上下文.加载器.导入(信息.入口网址,自身.取外层栈)#导入
                新插件表[信息.入口网址]=自身.所属上下文.加载器.取出默认导出(导出)#默认导出
        except Exception as 原因:#导入失败
            处理错误(自身.所属上下文,原因)#诊断
            备份.回滚()#回滚缓存
            raise#抛出
        已换=[]#已替换
        try:#换插件
            for 旧插件,信息 in 重载表.items():#逐个
                if 信息.运行时 is None:#无运行时
                    continue#跳过
                自身.替换一个(旧插件,信息,新插件表[信息.入口网址])#替换
                已换.append((旧插件,信息))#记下
        except Exception:#失败
            备份.回滚()#缓存
            for 旧插件,信息 in 已换:#回滚插件
                try:#装回
                    自身.所属上下文.注册表.删除(新插件表[信息.入口网址])#拆新
                    自身.重挂纤程(旧插件,信息.运行时)#装旧
                except Exception as 错误:#回滚失败
                    自身.所属上下文.日志.警告(错误)#警告
            raise#抛出
        自身.所属上下文.加载器.等待()#等树
        自身.所属上下文.广播('hmr/reload',重载表)#广播
        自身.暂存集=set()#清暂存

    def 收集待重载插件(自身):
        """找出入口模块落在接受集依赖里的插件。"""
        分组={}#基准网址到插件名
        for 插件配置 in 自身.所属上下文.加载器.列出插件配置():#扫
            父组=getattr(插件配置,'父组',None)#父组
            if 父组 is None:#无
                continue#跳过
            树=getattr(父组,'所属树',None)#树
            if 树 is None:#无
                continue#跳过
            基准=getattr(树.所属上下文,'基准网址',None)#基准
            if 基准 is None:#无
                raise RuntimeError('HMR entry tree has no base URL')#拒绝
            分组.setdefault(基准,set()).add(插件配置.选项.get('name'))#登记名
        待检查={}#任务到插件
        加载缓存=getattr(自身.内部加载器,'loadCache',None)#缓存
        for 基准网址,名称集 in 分组.items():#分组
            for 名称 in 名称集:#每个名
                if not 名称:#空名
                    continue#跳过
                try:#解析
                    网址=自身.解析说明符(名称,基准网址).url#入口网址
                    if 网址 in 自身.拒绝集:#已拒绝
                        continue#跳过
                    任务=加载缓存.get(网址) if 加载缓存 is not None else None#任务
                    插件=None#导出
                    if 任务 is not None:#有任务
                        命名空间=getattr(getattr(任务,'module',None),'getNamespace',lambda:None)()#命名空间
                        插件=自身.所属上下文.加载器.取出默认导出(命名空间)#插件
                    if 任务 is None or 插件 is None:#不可重载
                        continue#跳过
                    待检查[任务]=插件#记下
                    自身.拒绝集.add(网址)#入口不扩散
                except Exception as 错误:#解析失败
                    自身.所属上下文.日志.警告(错误)#警告
        重载表={}#结果
        for 任务,插件 in 待检查.items():#检查依赖
            自身.拒绝集.discard(任务.url)#放开自身
            依赖=自身.收集依赖(任务,自身.拒绝集)#依赖树
            自身.拒绝集.add(任务.url)#再拒绝入口
            if not (依赖 & 自身.接受集):#无交集
                continue#跳过
            自身.接受集.update(依赖)#整链接受
            重载表[插件]=重载信息(任务.url,自身.所属上下文.注册表.取运行记录(插件))#记下
        return 重载表#待重载

    def 替换一个(自身,旧插件,信息,新插件):
        """拆掉旧插件，再用新插件重挂原纤程。"""
        try:#相对路径
            相对=os.path.relpath(文件url转路径(信息.入口网址),自身.基准目录)#日志路径
        except Exception:#失败
            相对=信息.入口网址#回落网址
        try:#拆除旧
            自身.所属上下文.注册表.删除(旧插件)#删除
        except Exception as 错误:#拆除失败
            自身.所属上下文.日志.警告('failed to dispose plugin at %C',相对)#摘要
            自身.所属上下文.日志.警告(错误)#详情
        try:#重挂
            自身.重挂纤程(新插件,信息.运行时)#装新
            自身.所属上下文.日志.信息('reload plugin at %C',相对)#成功
        except Exception as 错误:#失败
            自身.所属上下文.日志.警告('failed to reload plugin at %C',相对)#摘要
            自身.所属上下文.日志.警告(错误)#详情
            raise#触发回滚

    def 重挂纤程(自身,插件,运行时):
        """用新插件在每条旧纤程的父上下文上重新启动。"""
        for 旧纤程 in list(运行时.纤程表):#逐条
            if getattr(旧纤程.父上下文.纤程,'编号',None) is None:#父已拆
                continue#跳过
            新纤程=旧纤程.父上下文.注册表.启动插件(插件,旧纤程.原始配置,自身.取外层栈)#重挂
            新纤程.插件配置=旧纤程.插件配置#继承归属
            if 新纤程.插件配置 is not None:#有配置
                新纤程.插件配置.纤程=新纤程#改指向
            新纤程.等待()#等启动

热更新.inject=['加载器','定时器']#Cordis inject 槽
热更新.Config={#Cordis Config 槽
    'base':字符串字段(),#监视基准目录
    'root':列表字段(字符串字段(),默认值=['.']),#监视根
    'ignored':列表字段(字符串字段(),默认值=['**/node_modules','**/.*','cache','data']),#忽略模式
    'debounce':自然数字段(默认值=100),#变更防抖毫秒
}#Config 结束
default=热更新#Cordis 默认导出槽
