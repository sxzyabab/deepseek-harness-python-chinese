import os#绝对路径判定
from ...依赖 import include#外部依赖胶水
from ...依赖.工具 import 获取内部数据,聚合错误#隔离表与聚合失败
包含=include.包含#Include 组载体
路径转文件url=include.路径转文件url#路径转 file URL
from ...内核.作用域 import 获取作用域,获取作用域父#作用域键与父链
from .预设 import 预设错误,预设挂载错误#本包错误

__all__=[#仅中文公开名
    '活预设挂载','泄漏服务','常驻挂载于','智能体服务','未激活行','挂载预设',
]#公开面结束

已挂载={}#配置对象 id → 已挂载子树
harness基址={}#配置对象 id → harness 基址
挂载列表=[]#活挂载记录列表

class 预设树(包含):
    """Include 子类：为审计发布其树与 fiber，且从不写回它读过的文件。"""
    def __init__(自身,ctx,配置):
        """构造并按配置身份发布树与 fiber。"""
        super().__init__(ctx,配置)#交给 Include
        已挂载[id(配置)]={'tree':自身,'fiber':ctx.纤程}#按配置身份发布

    def 导入(自身,名称,外层栈=None):
        """从 harness 而不是从预设解析裸说明符。"""
        说明符=路径转文件url(名称) if os.path.isabs(名称) else 名称#绝对路径先变 file URL
        配置标识=id(自身.配置)#配置身份
        基址=harness基址[配置标识] if 配置标识 in harness基址 else None#挂载前记录的 harness 基址
        if 基址 is None:#无基址则走继承解析
            return super().导入(说明符,外层栈)#继承
        if 名称.startswith('.') or 名称.startswith('cordis:'):#相对与内建
            return super().导入(名称,外层栈)#走树基址
        内部=自身.所属上下文.加载器.内部加载器#内部加载器
        if 内部 is None:#无内部加载器
            return super().导入(说明符,外层栈)#回退
        return 内部.import_(说明符,基址,{})#相对 harness 基址导入裸名

    def 写入(自身):
        """预设是输入，从来不是持久化目标。"""
        return#空操作

def 修剪已拆除挂载():
    """丢掉子树已不在的每条记录。"""
    存活=[]#仍活
    for 挂载 in 挂载列表:#每条记录
        if 挂载['fiber'].编号 is not None:#仍活
            存活.append(挂载)#保留
    挂载列表.clear()#清空
    挂载列表.extend(存活)#写回

def 活预设挂载():
    """仍安装着的每份预设组合。"""
    修剪已拆除挂载()#先修剪
    return list(挂载列表)#快照

def 在光纤内(光纤,根):
    """`fiber` 是否就是 `root` 本身，或挂在其任何子树里。光纤是纤程对象。"""
    当前=光纤#从待测往上走
    while True:#沿父链
        if 当前 is 根:#撞上根
            return True#属于
        父上下文=当前.父上下文#父上下文
        if 父上下文 is None:#无父
            return False#到顶
        父=父上下文.纤程#父 fiber
        if 父 is 当前:#到顶仍未撞上
            return False#到顶
        当前=父#继续向上

def 泄漏服务(上下文对象,挂载光纤):
    """已挂载子树发布进根域的服务名。实现是 服务实现 对象。"""
    存储=上下文对象.反射.存储#服务实现存储
    根隔离=获取内部数据(上下文对象.根,'属性链')['隔离']#根域隔离表
    泄漏=[]#泄漏名
    for 键,实现 in list(存储.items()):#每个存储槽
        if 实现 is None:#空槽
            continue#跳过
        名=实现.名称#服务名
        光纤=实现.纤程#提供方光纤
        if not 在光纤内(光纤,挂载光纤):#不是本子树
            continue#跳过
        if 名 in 根隔离 and 根隔离[名] is 键:#存在根域符号下即泄漏
            泄漏.append(名)#记下
    泄漏.sort()#字典序
    return 泄漏#泄漏名

def 常驻挂载于(智能体上下文):
    """一个智能体所加入的常驻组合。"""
    智能体键=获取作用域(智能体上下文)#智能体作用域键
    if 智能体键 is None:#无作用域
        return None#未加入
    常驻键=获取作用域父(智能体键)#常驻父键
    if 常驻键 is None:#无父链接
        return None#未加入
    for 候选 in 活预设挂载():#按父键匹配
        if 候选['key'] is 常驻键:#键相同，按引用
            return 候选#命中
    return None#未找到

def 智能体服务(上下文对象,智能体,名):
    """一个智能体对其预设所挂服务的实例。智能体是对象，带 ctx。"""
    挂载=常驻挂载于(智能体.ctx)#智能体加入的常驻挂载
    if 挂载 is None:#未加入
        return None#无
    存储=上下文对象.反射.存储#服务实现存储
    挂载光纤=挂载['fiber']#子树 fiber
    for 实现 in list(存储.values()):#每个实现
        if 实现 is None:#空槽
            continue#跳过
        if 实现.名称!=名:#名字不匹配
            continue#跳过
        if 在光纤内(实现.纤程,挂载光纤):#本子树发布的
            return 实现.值#命中
    return None#预设未挂该服务

def 未激活行(树):
    """未到达可用状态的行，每行渲染成一条诊断。条目是插件配置对象。"""
    树.等待()#等子树沉降
    行列表=[]#诊断行
    for 条目 in 树.列出插件配置():#每个条目
        if 条目.已禁用:#禁用行不算
            continue#跳过
        光纤=条目.纤程#条目 fiber
        选项=条目.选项#选项 dict
        标识=选项['id'] if 'id' in 选项 else None#条目 id
        插件名=选项['name'] if 'name' in 选项 else None#插件名
        if 光纤 is None:#无 fiber
            行列表.append(str(标识)+' ('+str(插件名)+'): never started')#从未启动
            continue#下一条
        try:#等 fiber 激活
            光纤.等待()#等激活
        except Exception as 错误:#导入或激活失败
            行列表.append(str(标识)+' ('+str(插件名)+'): '+挂载细节(错误))#失败诊断
            continue#下一条
        缺失=[]#仍缺的注入
        for 名 in 光纤.依赖表:#注入表
            if 光纤.所属上下文.获取服务(名,False) is None:#仍缺
                缺失.append(名)#记下
        if len(缺失)>0:#仍在等
            行列表.append(str(标识)+' ('+str(插件名)+'): waiting for '+', '.join(缺失))#等待中
    return 行列表#诊断列表

def 挂载细节(错误):
    """挂载失败的可报告文本。"""
    if isinstance(错误,聚合错误):#聚合失败
        行=[str(错误)]#聚合消息
        for 原因 in 错误.错误列表:#每个原因
            行.append('- '+挂载细节(原因))#展平
        return '\n'.join(行)#拼接
    return str(错误)#单错误消息

def 挂载预设(智能体上下文,预设):
    """在智能体上下文下挂载预设，且仅在每一行都可用后返回。预设是 dict。"""
    作用域=获取作用域(智能体上下文)#作用域键
    if 作用域 is None:#无作用域会污染进程内每个智能体
        raise 预设错误(
            'agent-presets: refusing to mount preset "'+预设['id']+'" into an unscoped context; '
            +'its registrations would apply to every agent in the process'
        )#拒绝
    配置={'path':路径转文件url(预设['path'])}#组合文件的 file URL
    基址=智能体上下文.基准网址#宿主基址
    if 基址 is not None:#有基址
        harness基址[id(配置)]=基址#记录 harness 基址
    修剪已拆除挂载()#修剪死记录
    句柄=智能体上下文.启动插件(预设树,配置)#插入预设子树
    try:#等待沉降并审计
        句柄.等待()#等子树沉降
        配置标识=id(配置)#配置身份
        if 配置标识 not in 已挂载:#未发布
            raise 预设错误('mounted subtree did not publish its entry tree')#异常
        子树=已挂载[配置标识]#构造器发布的树与 fiber
        树=子树['tree']#条目树
        光纤=子树['fiber']#真实 fiber
        不可用=未激活行(树)#未激活行
        if len(不可用)>0:#有行不可用
            raise 预设错误(str(len(不可用))+' row(s) did not activate:\n'+'\n'.join(不可用))#拒绝半组合
        泄漏=泄漏服务(智能体上下文,光纤)#根域泄漏
        if len(泄漏)>0:#有进程全局服务
            raise 预设错误(
                'row(s) published process-global service(s) ['+', '.join(泄漏)+']; '
                +'a preset service must sit behind an `isolate` realm or move to the host composition'
            )#拒绝泄漏
        挂载列表.append({'presetId':预设['id'],'fiber':光纤,'key':获取作用域(智能体上下文)})#登记活挂载
    except Exception as 错误:#子树沉降、审计与本包错误统一包成预设挂载错误
        try:#拆除本子树
            句柄.拆除()#拆除
        except Exception:#只吞本子树的拆除失败，类型随加载器与插件而变
            pass#吞掉
        raise 预设挂载错误(预设['id'],挂载细节(错误),错误)#包成预设挂载失败，不夹路径
