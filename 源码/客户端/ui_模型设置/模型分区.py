"""模型设置分区：提供方行、装卡与编辑器卡片。

对齐上游 `ui-settings-models/src/client/ModelsSection.tsx`。公开面仅中文名。
"""
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定
from .仓库 import 推导密钥引用,错误文案,取字段,提供方可用,协议选项#仓库辅助
from .提供方编辑器 import 提供方编辑器#编辑卡片
from .自定义提供方卡片 import 自定义提供方卡片#创建卡片

__all__=[#仅中文公开名
    '模型分区','需要装卡','移除提供方档案','编辑目标自','提供方目标标签','提供方文案',
    'needsSetup','removeProviderProfile','providerTargetLabel','providerCopy',
]#公开面结束

def 解开(值):#承诺则等待
    """承诺则等待，否则原样。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 需要装卡(行,任一可用):#首跑姿态下是否打开装卡
    """已有可用提供方则普通行；整段提供方且密钥未配才装卡。"""
    if 任一可用:#已有可用
        return False#普通行
    条目=取字段(行,'entry') or {}#目录条目
    路径=取字段(条目,'settingsPath') or []#设置路径
    if len(路径)>0:#非整段
        return False#普通行
    凭证=取字段(行,'credential')#凭证态
    return 取字段(凭证,'configured') is not True#未配置密钥

needsSetup=需要装卡#上游名

def 移除提供方档案(接口,控制器,目标):#移除用户添加的提供方及其页管凭证
    """先卸凭证再 unset 设置；失败文案或成功后 reload 返回 None。"""
    try:#写线
        凭证引用=取字段(目标,'credentialRef')#可选托管引用
        if 凭证引用 is not None:#有凭证
            凭证=解开(接口.credentials.unset({'ref':凭证引用}))#卸凭证
            结果=取字段(凭证,'result')#结果
            if 取字段(结果,'ok') is not True:#失败
                return 取字段(取字段(结果,'error'),'message')#失败文案
        响应=解开(接口.settings.mutate({#unset 档案
            'ns':取字段(目标,'settingsNs'),
            'ops':[{'op':'unset','path':list(取字段(目标,'settingsPath') or [])}],
        }))#变更
        结果=取字段(响应,'result')#结果
        if 取字段(结果,'ok') is not True:#失败
            return 取字段(取字段(结果,'error'),'message')#失败文案
    except Exception as 错误:#传输拒绝
        return 错误文案(错误)#可重试
    解开(控制器.load())#刷新页
    return None#成功

removeProviderProfile=移除提供方档案#上游名

def 编辑目标自(行):#从接合行推导编辑器目标
    """托管凭证引用仅在约定引用且已配置可写时带上。"""
    条目=取字段(行,'entry') or {}#条目
    托管引用=推导密钥引用(取字段(条目,'provider') or '')#约定引用
    凭证=取字段(行,'credential')#凭证
    凭证引用=None#默认不带
    if (取字段(行,'apiKeyEnv')==托管引用
        and 取字段(凭证,'configured') is True
        and 取字段(凭证,'writable')):#页管凭证
        凭证引用=托管引用#带上
    目标={#编辑目标
        'provider':取字段(条目,'provider'),
        'displayName':取字段(条目,'displayName'),
        'settingsNs':取字段(条目,'settingsNs'),
        'settingsPath':list(取字段(条目,'settingsPath') or []),
    }#基础
    if 凭证引用 is not None:#有托管
        目标['credentialRef']=凭证引用#带上
    if 取字段(条目,'declared') is True:#适配器声明
        目标['declared']=True#带上
    return 目标#目标

def 提供方目标标签(目标):#可见身份
    """同名则仅路由，否则 显示名 (路由)。"""
    if 取字段(目标,'provider')==取字段(目标,'displayName'):#同名
        return 取字段(目标,'provider')#路由
    return f"{取字段(目标,'displayName')} ({取字段(目标,'provider')})"#组合

providerTargetLabel=提供方目标标签#上游名

def 提供方文案(模板,目标):#替换破坏性动作文案占位
    """{provider} → 目标标签。"""
    return 模板.replace('{provider}',提供方目标标签(目标))#替换

providerCopy=提供方文案#上游名

class 模型分区:#模型设置分区
    """一次一张编辑/装卡/创建卡；删除需确认。"""
    def __init__(自身,属性):#构造
        """记下 props 与本地 UI 态。"""
        自身.属性=属性#合成 props
        自身.编辑中=None#当前编辑目标
        自身.添加中=False#添加休眠提供方
        自身.删除目标=None#待删目标
        自身.删除中=False#删除在飞
        自身.删除失败=None#删除失败
        自身.已保存目标=None#保存成功公告身份
        自身.声明中=False#自定义创建卡
        自身.已关装卡=set()#本会话关掉的装卡
        自身.编辑器实例=None#当前提供方编辑器
        自身.创建卡实例=None#自定义创建卡

    def 更新(自身,属性):#props 变更
        """刷新。"""
        自身.属性=属性#最新

    def 读状态(自身):#读模型拼合快照
        """经 useSnapshot 或 controller.store。"""
        用=取字段(自身.属性,'useSnapshot')#选择器
        if 用 is not None:#有
            return 用(lambda 快照:快照) or {}#快照
        控制器=取字段(自身.属性,'controller')#控制器
        return 控制器.store.getSnapshot() if 控制器 is not None else {'status':'idle','rows':[]}#默认

    def 公告已存(自身,目标):#保存后公告
        """reload 后再用目录里的新名字。"""
        控制器=取字段(自身.属性,'controller')#控制器
        if 控制器 is None:#无
            自身.已保存目标=目标#直接
            return#结束
        解开(控制器.load())#刷新
        自身.已保存目标=目标#公告

    def 关编辑器(自身,已变,目标):#关编辑/添加/声明
        """清三态；变更则公告。"""
        自身.编辑中=None#清
        自身.添加中=False#清
        自身.声明中=False#清
        自身.编辑器实例=None#清
        自身.创建卡实例=None#清
        if 已变:#有变更
            自身.公告已存(目标)#公告

    def 关装卡(自身,已变,目标):#关首跑装卡
        """不碰其它卡片草稿。"""
        自身.已关装卡.add(取字段(目标,'provider'))#记下
        自身.编辑器实例=None#清实例
        if 已变:#有变更
            自身.公告已存(目标)#公告

    def 关删除(自身):#关删除对话框
        """删除在飞不可关。"""
        if 自身.删除中:#在飞
            return#结束
        自身.删除目标=None#清
        自身.删除失败=None#清

    def 确认删除(自身):#执行删除
        """幂等；失败留对话框。"""
        if 自身.删除目标 is None or 自身.删除中:#不可
            return#结束
        自身.删除中=True#在飞
        自身.删除失败=None#清
        接口=取字段(自身.属性,'api')#api
        控制器=取字段(自身.属性,'controller')#控制器
        失败=移除提供方档案(接口,控制器,自身.删除目标)#删
        if 失败 is not None:#失败
            自身.删除失败=失败#记下
        else:#成功
            自身.删除目标=None#关
        自身.删除中=False#闲

    def 渲染提供方编辑器(自身,目标,命名空间,关闭):#共用编辑器投影
        """声明路由带 declared。"""
        属性={#props
            'provider':取字段(目标,'provider'),#路由
            'displayName':取字段(目标,'displayName'),#显示名
            'namespace':命名空间,#ns
            'settingsPath':取字段(目标,'settingsPath'),#路径
            'api':取字段(自身.属性,'api'),#api
            't':取字段(自身.属性,'t'),#文案
            'readOnly':not 取字段(自身.读状态(),'writable',False),#只读
            'onClose':关闭,#关闭
        }#基础
        if 取字段(目标,'declared') is True:#手声明
            属性['declared']=True#带上
        自身.编辑器实例=提供方编辑器(属性)#实例
        return 自身.编辑器实例()#视图

    def 渲染(自身):#结构化视图
        """完整分区：行、装卡、添加、声明、删除确认。"""
        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案
        控制器=取字段(自身.属性,'controller')#控制器
        接口=取字段(自身.属性,'api')#api
        if 控制器 is None or 接口 is None or 取字段(自身.属性,'t') is None:#未注入
            return None#空
        状态=自身.读状态()#状态
        if 取字段(状态,'status')=='idle':#尚未拉
            控制器.load()#首读
            状态=自身.读状态()#再读
        if 取字段(状态,'status')=='error':#整页错误
            return {#错误面
                'type':'models-section',#类型
                'error':f"{翻译('loadFailed')}: {取字段(状态,'error') or ''}",#文案
                'retryLabel':翻译('retry'),#重试
                'onRetry':(lambda:控制器.load()),#重试
                'cssModule':'模型分区.module.css',#样式
            }#错误结束
        行们=取字段(状态,'rows') or []#接合行
        命名空间图=取字段(状态,'namespaces') or {}#ns 图
        def 取命名空间(名):#按名取 ns
            """dict 或带 get 的图。"""
            if isinstance(命名空间图,dict):#映射
                return 命名空间图.get(名)#取
            return 命名空间图.get(名) if hasattr(命名空间图,'get') else None#get
        已存行=None#保存公告行
        if 自身.已保存目标 is not None:#有公告
            for 行 in 行们:#找
                if 取字段(取字段(行,'entry'),'provider')==取字段(自身.已保存目标,'provider'):#匹配
                    已存行=行#记下
                    break#找到
        已存身份=自身.已保存目标 if 已存行 is None else {'provider':取字段(取字段(已存行,'entry'),'provider'),'displayName':取字段(取字段(已存行,'entry'),'displayName')}#身份
        任一可用=any(提供方可用(行) for 行 in 行们)#任一可用
        已配置=[行 for 行 in 行们 if 取字段(行,'configured')]#已配置行
        可添加=[行 for 行 in 行们 if not 取字段(行,'configured') and 取字段(取字段(行,'entry'),'settingsNs')!='']#可添加
        添加目标=自身.编辑中 if 自身.添加中 else None#添加目标
        添加命名空间=None if 添加目标 is None else 取命名空间(取字段(添加目标,'settingsNs'))#添加 ns
        协议们=协议选项(取命名空间('llm-pi-ai'))#协议
        投影行=[]#行投影
        for 行 in 已配置:#已配置
            目标=编辑目标自(行)#目标
            命名空间=取命名空间(取字段(目标,'settingsNs'))#ns
            if 命名空间 is None:#无 ns
                continue#跳过
            if 需要装卡(行,任一可用) and 取字段(目标,'provider') not in 自身.已关装卡:#装卡
                投影行.append({#装卡行
                    'kind':'setup',#装卡
                    'provider':取字段(目标,'provider'),#路由
                    'editor':自身.渲染提供方编辑器(目标,命名空间,lambda 变,标=目标:自身.关装卡(变,标)),#编辑器
                })#装卡结束
                continue#下一
            打开=not 自身.添加中 and 自身.编辑中 is not None and 取字段(自身.编辑中,'provider')==取字段(取字段(行,'entry'),'provider')#打开
            凭证=取字段(行,'credential')#凭证
            凭证已配=取字段(凭证,'configured') is True#已配
            凭证缺=not 凭证已配 and 取字段(行,'apiKeyEnv') is not None and 取字段(凭证,'configured') is False#缺
            行面={#普通行
                'kind':'row',#行
                'provider':取字段(取字段(行,'entry'),'provider'),#路由
                'displayName':取字段(取字段(行,'entry'),'displayName'),#显示名
                'customTag':翻译('customTag') if 取字段(取字段(行,'entry'),'declared') is True else None,#自定义标
                'credentialConfigured':凭证已配,#已配点
                'credentialMissing':凭证缺,#缺配点
                'credentialConfiguredLabel':翻译('credentialConfigured'),#已配文案
                'credentialMissingLabel':翻译('credentialMissing'),#缺配文案
                'editLabel':翻译('edit'),#编辑
                'editAria':提供方文案(翻译('editProvider'),目标),#编辑无障碍
                'onEdit':(lambda 标=目标,开=打开:(
                    自身.__setattr__('已保存目标',None),
                    自身.__setattr__('声明中',False),
                    自身.__setattr__('添加中',False),
                    自身.__setattr__('编辑中',None if 开 else 标),
                    自身.__setattr__('编辑器实例',None),
                    自身.__setattr__('创建卡实例',None),
                )),#编辑
                'removeLabel':翻译('remove') if 取字段(行,'removable') else None,#移除
                'removeAria':提供方文案(翻译('removeProvider'),目标) if 取字段(行,'removable') else None,#移除无障碍
                'removeDisabled':not 取字段(状态,'writable',False),#移除禁用
                'onRemove':(lambda 标=目标:(
                    自身.__setattr__('已保存目标',None),
                    自身.__setattr__('删除失败',None),
                    自身.__setattr__('删除目标',标),
                )) if 取字段(行,'removable') else None,#移除
                'editor':自身.渲染提供方编辑器(目标,命名空间,lambda 变,标=目标:自身.关编辑器(变,标)) if 打开 else None,#展开编辑器
            }#行结束
            投影行.append(行面)#记入
        添加块=None#添加区
        if 添加目标 is not None and 添加命名空间 is not None:#添加卡
            添加编辑=提供方编辑器({#编辑器
                'provider':取字段(添加目标,'provider'),#路由
                'displayName':取字段(添加目标,'displayName'),#显示名
                'hideTitle':True,#藏标题
                'namespace':添加命名空间,#ns
                'settingsPath':取字段(添加目标,'settingsPath'),#路径
                'api':接口,#api
                't':翻译,#文案
                'readOnly':not 取字段(状态,'writable',False),#只读
                'onClose':(lambda 变,标=添加目标:自身.关编辑器(变,标)),#关闭
            })#编辑器结束
            自身.编辑器实例=添加编辑#记下
            添加块={#添加卡
                'kind':'add',#添加
                'providerLabel':翻译('provider'),#提供方标签
                'provider':取字段(添加目标,'provider'),#当前
                'options':[{'value':取字段(取字段(行,'entry'),'provider'),'label':取字段(取字段(行,'entry'),'displayName')} for 行 in 可添加],#选项
                'onSelect':(lambda 值:(
                    自身.__setattr__('编辑中',编辑目标自(next(行 for 行 in 可添加 if 取字段(取字段(行,'entry'),'provider')==值))),
                    自身.__setattr__('编辑器实例',None),
                )),#切换
                'editor':添加编辑(),#编辑器
            }#添加结束
        elif 自身.声明中:#自定义创建
            自身.创建卡实例=自定义提供方卡片({#创建卡
                'taken':[取字段(取字段(行,'entry'),'provider') for 行 in 行们],#占用
                'protocols':协议们,#协议
                'revision':取字段(取命名空间('llm-pi-ai'),'revision',0),#修订
                'api':接口,#api
                't':翻译,#文案
                'readOnly':not 取字段(状态,'writable',False),#只读
                'onClose':(lambda 变:(
                    自身.__setattr__('声明中',False),
                    自身.__setattr__('创建卡实例',None),
                    控制器.load() if 变 else None,
                )),#关闭
            })#创建结束
            添加块={'kind':'declare','card':自身.创建卡实例()}#声明块
        else:#两个入口按钮
            添加块={#入口
                'kind':'actions',#动作
                'addLabel':翻译('add'),#添加
                'addDisabled':len(可添加)==0 or not 取字段(状态,'writable',False),#禁用
                'onAdd':(lambda:(
                    自身.__setattr__('已保存目标',None),
                    自身.__setattr__('声明中',False),
                    自身.__setattr__('添加中',True),
                    自身.__setattr__('编辑中',编辑目标自(可添加[0]) if len(可添加)>0 else None),
                    自身.__setattr__('创建卡实例',None),
                )),#添加
                'customLabel':翻译('customAdd'),#自定义
                'customDisabled':len(协议们)==0 or not 取字段(状态,'writable',False),#禁用
                'onCustom':(lambda:(
                    自身.__setattr__('已保存目标',None),
                    自身.__setattr__('添加中',False),
                    自身.__setattr__('编辑中',None),
                    自身.__setattr__('声明中',True),
                    自身.__setattr__('编辑器实例',None),
                )),#声明
            }#入口结束
        删除框=None#删除对话框
        if 自身.删除目标 is not None:#打开
            标=自身.删除目标#目标
            删述键='deleteDescriptionWithCredential' if 取字段(标,'credentialRef') is not None else 'deleteDescription'#说明键
            删除框={#对话框
                'title':提供方文案(翻译('deleteTitle'),标),#标题
                'description':提供方文案(翻译(删述键),标),#说明
                'closeLabel':翻译('close'),#关闭
                'cancelLabel':翻译('cancel'),#取消
                'confirmLabel':提供方文案(翻译('deleting' if 自身.删除中 else 'deleteConfirm'),标),#确认
                'deleting':自身.删除中,#在飞
                'error':自身.删除失败,#失败
                'onClose':自身.关删除,#关
                'onConfirm':自身.确认删除,#确认
            }#对话框结束
        return {#分区视图
            'type':'models-section',#类型
            'title':翻译('title'),#标题
            'intro':翻译('intro'),#介绍
            'readOnly':翻译('readOnly') if not 取字段(状态,'writable',False) and 取字段(状态,'status')=='ready' else None,#只读
            'savedNotice':提供方文案(翻译('savedProvider'),已存身份) if 已存身份 is not None else None,#已存公告
            'rows':投影行,#行
            'addBlock':添加块,#添加区
            'deleteDialog':删除框,#删除
            'status':取字段(状态,'status'),#加载态
            'writable':取字段(状态,'writable',False),#可写
            'cssModule':'模型分区.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 调用。"""
        if 属性 is not None:#有新
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
