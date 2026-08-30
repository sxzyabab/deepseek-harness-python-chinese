"""只读宿主插件清单页签。



对齐上游 `ui-settings-plugin-inventory/src/client/PluginInventorySettingsTab.tsx`。公开面仅中文名。

"""

from ...依赖 import cordis#外部依赖胶水


__all__=['插件清单页签','阶段文案键','模块短名','条目匹配']#仅中文公开名



阶段文案键={#fiber 阶段 → 文案键

    'pending':'pending',#等待依赖

    'loading':'loadingPhase',#加载中

    'active':'active',#已挂载

    'failed':'failed',#挂载失败

    'unloading':'unloading',#卸载中

}#阶段键结束



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺省#缺席

    return getattr(对象,键,缺省)#属性



def 解开(值):#承诺则等待否则原样

    """承诺则等待，否则原样返回。"""

    if 是否thenable(值):#可等待

        return 值.等待()#等待

    return 值#同步



def 模块短名(模块名):#压缩模块说明符

    """去掉作用域与常见前缀，不猜测 Loader id。"""

    去作用域=模块名[模块名.index('/')+1:] if 模块名.startswith('@') else 模块名#去作用域

    名=去作用域#工作副本

    if 名.startswith('cordis:'):#cordis 协议

        名=名[7:]#去掉

    if 名.startswith('cordis-plugin-'):#插件前缀

        名=名[14:]#去掉

    if 名.startswith('dsh-host-'):#宿主前缀

        名=名[9:]#去掉

    elif 名.startswith('dsh-client-'):#客户端前缀

        名=名[11:]#去掉

    elif 名.startswith('dsh-'):#通用 dsh

        名=名[4:]#去掉

    return 名#短名



def 条目匹配(条目,规范化查询):#本地目录查询是否命中

    """模块名或入口 id 含查询则命中。"""

    if len(规范化查询)==0:#空查询

        return True#全中

    for 值 in (取字段(条目,'moduleName',''),取字段(条目,'entryId','')):#候选

        if 规范化查询 in str(值).lower():#包含

            return True#命中

    return False#未命中



def 阶段标签(阶段,翻译):#阶段无障碍文案

    """null 阶段为未挂载。"""

    if 阶段 is None:#未观察

        return 翻译('unobserved')#未挂载

    return 翻译(阶段文案键[阶段])#阶段文案



class 插件清单页签:#设置页签组件

    """只读当前 Loader 清单；支持搜索与展开详情。"""

    def __init__(自身,属性):#按合成 props 构造

        """记下 props。"""

        自身.属性=属性#合成 props

        自身.请求序号=0#重试计数

        自身.查询=''#搜索框

        自身.展开标识=None#展开的 entryId

        自身.状态={'status':'loading'}#视图状态

        自身.存活=True#实例存活

        自身.刷新()#首读



    def 更新(自身,属性):#props 变更

        """刷新合成 props。"""

        自身.属性=属性#最新



    def 卸载(自身):#卸载

        """标死。"""

        自身.存活=False#死



    def 刷新(自身):#拉取清单

        """按 list 注入面读快照。"""

        自身.状态={'status':'loading'}#读中

        列表=取字段(自身.属性,'list')#远程 list

        try:#拉取

            快照=解开(列表()) if 列表 is not None else {'entries':[]}#结算

        except Exception:#失败

            if not 自身.存活:#已死

                return#丢弃

            自身.状态={'status':'error'}#错误

            return#结束

        if not 自身.存活:#已死

            return#丢弃

        自身.状态={'status':'ready','snapshot':快照}#就绪



    def 重试(自身):#失败后重试

        """重置为 loading 并再拉。"""

        自身.请求序号+=1#序号

        自身.刷新()#再拉



    def 设查询(自身,文本):#改搜索

        """更新查询并校正展开。"""

        自身.查询=文本#查询

        自身.校正展开()#校正



    def 切换展开(自身,入口标识):#展开/收起

        """同一 id 再点则收起。"""

        自身.展开标识=None if 自身.展开标识==入口标识 else 入口标识#切换



    def 过滤条目(自身):#按查询过滤

        """未就绪返回空列表。"""

        if 取字段(自身.状态,'status')!='ready':#未就绪

            return []#空

        快照=取字段(自身.状态,'snapshot') or {}#快照

        条目表=取字段(快照,'entries') or []#条目

        规范化=自身.查询.strip().lower()#规范化

        return [条目 for 条目 in 条目表 if 条目匹配(条目,规范化)]#过滤



    def 校正展开(自身):#展开项不在过滤结果则收起

        """过滤后展开项消失则清。"""

        if 自身.展开标识 is None:#无展开

            return#结束

        if not any(取字段(条目,'entryId')==自身.展开标识 for 条目 in 自身.过滤条目()):#不在

            自身.展开标识=None#收起



    def 视图(自身):#读视图模型

        """投影页签视图。"""

        翻译=取字段(自身.属性,'t',lambda 键,_=None:键)#文案

        状态名=取字段(自身.状态,'status')#状态

        结果={#基础

            'status':状态名,#状态

            'query':自身.查询,#查询

            'searchLabel':翻译('search'),#搜索文案

            'catalogLabel':翻译('catalog'),#目录标题

            'cssModule':'清单页签.module.css',#样式

        }#基础结束

        if 状态名=='loading':#读中

            结果['loadingText']=翻译('loading')#文案

            return 结果#返回

        if 状态名=='error':#错误

            结果['errorText']=翻译('error')#文案

            结果['retryText']=翻译('retry')#重试

            return 结果#返回

        快照=取字段(自身.状态,'snapshot') or {}#快照

        全部=取字段(快照,'entries') or []#全部

        过滤=自身.过滤条目()#过滤

        行表=[]#卡片行

        for 条目 in 过滤:#每条

            阶段=取字段(条目,'fiberPhase')#阶段

            启用=bool(取字段(条目,'enabled'))#启用

            状态文案=阶段标签(阶段,翻译)#阶段文案

            标题=模块短名(str(取字段(条目,'moduleName','')))#短名

            配置文案=翻译('enabledTag' if 启用 else 'disabledTag')#配置

            入口标识=取字段(条目,'entryId')#id

            打开=自身.展开标识==入口标识#是否展开

            行={#行视图

                'entryId':入口标识,#入口

                'moduleName':取字段(条目,'moduleName'),#全名

                'title':标题,#短名

                'enabled':启用,#启用

                'fiberPhase':阶段,#阶段

                'status':状态文案,#阶段文案

                'configuration':配置文案,#配置文案

                'open':打开,#展开

                'aria':f'{标题}, {状态文案}, {配置文案}' if 启用 else f'{标题}, {配置文案}',#无障碍

            }#行结束

            if 打开:#详情

                行['details']={#详情块

                    'configurationLabel':翻译('configuration'),#配置列

                    'configuration':配置文案,#配置值

                    'cordisLabel':翻译('cordis') if 启用 else None,#Cordis 列

                    'cordis':状态文案 if 启用 else None,#Cordis 值

                }#详情结束

            行表.append(行)#记入

        结果['entryCount']=len(过滤)#计数

        结果['totalCount']=len(全部)#总数

        结果['emptyText']=翻译('empty') if len(全部)==0 else None#空清单

        结果['emptySearchText']=翻译('emptySearch') if len(全部)>0 and len(过滤)==0 else None#无匹配

        结果['rows']=行表#行

        结果['cssModule']='清单页签.module.css'#样式

        return 结果#返回



    def __call__(自身,属性=None):#组件调用形

        """对齐 React 组件调用；返回视图。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.视图()#视图


