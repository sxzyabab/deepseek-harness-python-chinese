"""在智能体作用域上下文下挂载一份预设组合，并在智能体发布前证明结果可用。

对齐上游 `agent-presets/src/mount.ts`。公开面仅中文名。
"""
import os#绝对路径判定
from ...依赖 import include,cordis#外部依赖胶水
包含=include.包含#Include 组载体
路径转文件url=include.路径转文件url#路径转 file URL
上下文类=cordis.上下文#隔离符号
from ...内核.作用域 import 获取作用域,获取作用域父#作用域键与父链
from .预设 import 预设挂载错误#挂载失败

__all__=[#仅中文公开名
    '活预设挂载','泄漏服务','常驻挂载于','智能体服务','未激活行','挂载预设',
]#公开面结束

已挂载={}#配置对象 id → 已挂载子树
harness基址={}#配置对象 id → harness 基址
挂载集=set()#活挂载集合（用 id 存记录字典不便，改用列表）
挂载列表=[]#活挂载记录列表

class 预设树(包含):#预设用的 Include
    """Include 子类：为审计发布其树与 fiber，且从不写回它读过的文件。"""
    def __init__(自身,ctx,配置):#构造并登记子树
        """构造并按配置身份发布树与 fiber。"""
        super().__init__(ctx,配置)#交给 Include
        已挂载[id(配置)]={'tree':自身,'fiber':ctx.fiber}#按配置身份发布

    def 导入(自身,名称,获取外层栈=None):#解析行上的模块
        """从 harness 而不是从预设解析裸说明符。"""
        说明符=路径转文件url(名称) if os.path.isabs(名称) else 名称#绝对路径先变 file URL
        基址=harness基址.get(id(自身.配置))#挂载前记录的 harness 基址
        if 基址 is None:#无基址则走继承解析
            return super().导入(说明符,获取外层栈)#继承
        if 名称.startswith('.') or 名称.startswith('cordis:'):#相对与内建
            return super().导入(名称,获取外层栈)#走树基址
        内部=getattr(自身.ctx.loader,'internal',None)#内部加载器
        if 内部 is None:#无内部加载器
            return super().导入(说明符,获取外层栈)#回退
        return 内部.导入(说明符,基址,{})#相对 harness 基址导入裸名

    def 写入(自身):#丢弃写回
        """预设是输入，从来不是持久化目标。"""
        return#空操作

def 修剪已拆除挂载():#修剪已拆除挂载
    """丢掉子树已不在的每条记录。"""
    存活=[]#仍活
    for 挂载 in 挂载列表:#每条记录
        if 取字段(挂载,'fiber').uid is not None:#仍活
            存活.append(挂载)#保留
    挂载列表.clear()#清空
    挂载列表.extend(存活)#写回

def 活预设挂载():#列出活挂载
    """仍安装着的每份预设组合。"""
    修剪已拆除挂载()#先修剪
    return list(挂载列表)#快照

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

def 在光纤内(光纤,根):#fiber 是否在子树内
    """`fiber` 是否就是 `root` 本身，或挂在其任何子树里。"""
    当前=光纤#从待测往上走
    while True:#沿父链
        if 当前 is 根:#撞上根
            return True#属于
        父上下文=取字段(当前,'parent')#父上下文
        if 父上下文 is None:#无父
            return False#到顶
        父=取字段(父上下文,'fiber')#父 fiber
        if 父 is 当前:#到顶仍未撞上
            return False#到顶
        当前=父#继续向上

def 泄漏服务(上下文对象,挂载光纤):#根域泄漏的服务名
    """已挂载子树发布进根域的服务名。"""
    存储=上下文对象.reflect.存储#服务实现存储
    根隔离=上下文对象.root.__dict__.get(上下文类.隔离) or {}#根域隔离表
    泄漏=[]#泄漏名
    for 键,实现 in list(存储.items()):#每个存储槽
        if 实现 is None:#空槽
            continue#跳过
        名=实现['name'] if isinstance(实现,dict) else 实现.name#服务名
        光纤=实现['fiber'] if isinstance(实现,dict) else 实现.fiber#提供方光纤
        if not 在光纤内(光纤,挂载光纤):#不是本子树
            continue#跳过
        if 根隔离.get(名) is 键:#存在根域符号下即泄漏
            泄漏.append(名)#记下
    泄漏.sort()#字典序
    return 泄漏#泄漏名

def 常驻挂载于(智能体上下文):#查找智能体加入的常驻挂载
    """一个智能体所加入的常驻组合。"""
    智能体键=获取作用域(智能体上下文)#智能体作用域键
    if 智能体键 is None:#无作用域
        return None#未加入
    常驻键=获取作用域父(智能体键)#常驻父键
    if 常驻键 is None:#无父链接
        return None#未加入
    for 候选 in 活预设挂载():#按父键匹配
        if 取字段(候选,'key') is 常驻键:#键相同
            return 候选#命中
    return None#未找到

def 智能体服务(上下文对象,智能体,名):#按智能体取预设内服务
    """一个智能体对其预设所挂服务的实例。"""
    挂载=常驻挂载于(取字段(智能体,'ctx'))#智能体加入的常驻挂载
    if 挂载 is None:#未加入
        return None#无
    存储=上下文对象.reflect.存储#服务实现存储
    挂载光纤=取字段(挂载,'fiber')#子树 fiber
    for 键,实现 in list(存储.items()):#每个存储槽
        if 实现 is None:#空槽
            continue#跳过
        实现名=实现['name'] if isinstance(实现,dict) else 实现.name#服务名
        if 实现名!=名:#名字不匹配
            continue#跳过
        光纤=实现['fiber'] if isinstance(实现,dict) else 实现.fiber#提供方
        if 在光纤内(光纤,挂载光纤):#本子树发布的
            return 实现['value'] if isinstance(实现,dict) else 实现.value#命中
    return None#预设未挂该服务

def 未激活行(树):#未激活行的诊断
    """未到达可用状态的行，每行渲染成一条诊断。"""
    行们=[]#诊断行
    for 条目 in 树.条目们():#每个条目
        if 取字段(条目,'disabled'):#禁用行不算
            continue#跳过
        光纤=取字段(条目,'fiber')#条目 fiber
        选项=取字段(条目,'options') or {}#选项
        标识=取字段(选项,'id')#条目 id
        插件名=取字段(选项,'name')#插件名
        if 光纤 is None:#无 fiber
            行们.append(str(标识)+' ('+str(插件名)+'): never started')#从未启动
            continue#下一条
        缺失=[]#仍缺的注入
        for 名 in (取字段(光纤,'inject') or {}):#注入表
            if 光纤.ctx.get(名) is None:#仍缺
                缺失.append(名)#记下
        if len(缺失)>0:#仍在等
            行们.append(str(标识)+' ('+str(插件名)+'): waiting for '+', '.join(缺失))#等待中
    return 行们#诊断列表

def 挂载细节(错误):#展平挂载失败文本
    """挂载失败的可报告文本。"""
    if not isinstance(错误,Exception):#非 Error
        return str(错误)#字符串化
    错误们=getattr(错误,'errors',None)#聚合原因
    if 错误们 is None:#单错误
        return str(错误)#消息
    行=[str(错误)]#聚合消息
    for 原因 in 错误们:#每个原因
        行.append('- '+挂载细节(原因))#展平
    return '\n'.join(行)#拼接

def 挂载预设(智能体上下文,预设):#挂载预设并审计
    """在智能体上下文下挂载预设，且仅在每一行都可用后返回。"""
    作用域=获取作用域(智能体上下文)#作用域键
    if 作用域 is None:#无作用域会污染进程内每个智能体
        raise Exception(
            'agent-presets: refusing to mount preset "'+取字段(预设,'id')+'" into an unscoped context; '
            +'its registrations would apply to every agent in the process'
        )#拒绝
    配置={'path':路径转文件url(取字段(预设,'path'))}#组合文件的 file URL
    基址=取字段(智能体上下文,'baseUrl')#宿主基址
    if 基址 is not None:#有基址
        harness基址[id(配置)]=基址#记录 harness 基址
    修剪已拆除挂载()#修剪死记录
    句柄=智能体上下文.plugin(预设树,配置)#插入预设子树
    try:#等待沉降并审计
        句柄.等待()#等子树沉降
        子树=已挂载.get(id(配置))#构造器发布的树与 fiber
        if 子树 is None:#未发布
            raise Exception('mounted subtree did not publish its entry tree')#异常
        树=子树['tree']#条目树
        光纤=子树['fiber']#真实 fiber
        不可用=未激活行(树)#未激活行
        if len(不可用)>0:#有行不可用
            raise Exception(str(len(不可用))+' row(s) did not activate:\n'+'\n'.join(不可用))#拒绝半组合
        泄漏=泄漏服务(智能体上下文,光纤)#根域泄漏
        if len(泄漏)>0:#有进程全局服务
            raise Exception(
                'row(s) published process-global service(s) ['+', '.join(泄漏)+']; '
                +'a preset service must sit behind an `isolate` realm or move to the host composition'
            )#拒绝泄漏
        挂载列表.append({'presetId':取字段(预设,'id'),'fiber':光纤,'key':获取作用域(智能体上下文)})#登记活挂载
    except Exception as 错误:#挂载失败则拆除半成品
        try:#拆除本子树
            句柄.dispose()#拆除
        except Exception:#只吞本子树的拆除失败
            pass#吞掉
        raise 预设挂载错误(取字段(预设,'id'),挂载细节(错误)+' ('+取字段(预设,'path')+')',错误)#包成预设挂载失败
