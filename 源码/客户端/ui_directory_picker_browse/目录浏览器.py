"""应用内工作区目录浏览器（Miller 视图 + 路径编辑 + 新建文件夹）。



对齐上游 `ui-directory-picker-browse/src/client/DirectoryBrowser.tsx`。公开面仅中文名。

纯消费注入的浏览调用；主人决定 Open 语义并拥有工作区创建错误面。

"""

import time#时钟与防抖



__all__=[#仅中文公开名

    '目录浏览器','慢扫描延迟毫秒','父腿等待毫秒','草稿预览防抖毫秒',

    '展示面包屑','分隔符于','层级目录','草稿目录','读草稿','可见条目','失败文案',

]#公开面结束



慢扫描延迟毫秒=300#慢扫描指示延迟

父腿等待毫秒=200#父腿等待上界

草稿预览防抖毫秒=250#草稿预览防抖



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺省#缺席

    return getattr(对象,键,缺省)#属性



def 失败文案(错误):#失败文本

    """Host 业务消息优先，否则 throw 文本。"""

    if 取字段(错误,'rpcError') is not None:#DirectoryBrowseError 形

        return 取字段(取字段(错误,'rpcError'),'message') or str(错误)#业务消息

    if isinstance(错误,Exception):#标准异常

        return str(错误)#message

    return str(错误)#强制字符串



def 展示面包屑(列举,主目录标签):#展示用面包屑

    """主目录子树内以本地化 Home 起链；外则全谱系。"""

    屑=取字段(列举,'crumbs') or []#屑

    家=取字段(列举,'home')#主目录

    家下标=-1#家在屑中的下标

    for 下标,项 in enumerate(屑):#找家

        if 取字段(项,'path')==家:#命中

            家下标=下标#记下

            break#找到

    if 家下标==-1:#不在子树

        return list(屑)#全谱系

    尾=屑[家下标+1:]#家之后

    return [{'name':主目录标签,'path':家,'hidden':False}]+list(尾)#Home + 尾



def 分隔符于(列举):#平台分隔符

    """从 home 路径推断；反斜杠则 Windows。"""

    家=取字段(列举,'home') or ''#主目录

    return '\\' if '\\' in 家 else '/'#分隔符



def 层级目录(列举):#当前层作为目录部分

    """自身路径，以分隔符结尾（根已是）。"""

    分隔=分隔符于(列举)#分隔符

    路径=取字段(列举,'path') or ''#路径

    return 路径 if 路径.endswith(分隔) else 路径+分隔#补分隔符



def 草稿目录(列举,草稿):#草稿的目录部分

    """到最后分隔符为止；无分隔符则 None。"""

    if 分隔符于(列举)=='\\':#Windows：正斜杠也分隔

        切=max(草稿.rfind('\\'),草稿.rfind('/'))#最后分隔

    else:#POSIX：反斜杠是合法名字符

        切=草稿.rfind('/')#仅正斜杠

    if 切==-1:#无分隔

        return None#尚未寻址目录

    return 草稿[:切+1]#含分隔符



def 读草稿(列举,草稿,已扫描):#草稿相对一层的读法

    """目录部分 + 过滤尾（仅当本层应答该目录）。"""

    目录=草稿目录(列举,草稿)#目录部分

    if 目录 is None:#无分隔

        return {'directory':None,'tail':None}#空

    应答=目录==层级目录(列举)#本层路径即该目录

    if not 应答 and 已扫描 is not None:#看扫描着陆

        应答=取字段(已扫描,'directory')==目录 and 取字段(已扫描,'landed')==取字段(列举,'path')#着陆匹配

    return {'directory':目录,'tail':草稿[len(目录):] if 应答 else None}#尾或 None



def 可见条目(条目们,选中路径,显示隐藏,过滤前缀):#一列可见行

    """选中豁免一切过滤；前缀无人匹配则整层显示。"""

    针=(过滤前缀 or '').lower()#小写针

    def 可显示(条目):#隐藏过滤

        """点前缀显式点出隐藏项。"""

        return 显示隐藏 or not 取字段(条目,'hidden') or 针.startswith('.')#显示条件

    def 匹配(条目):#前缀匹配

        """可显示且名前缀命中。"""

        return 可显示(条目) and str(取字段(条目,'name') or '').lower().startswith(针)#匹配

    收窄=针!='' and any(匹配(项) for 项 in 条目们)#有人匹配才收窄

    结果=[]#可见

    for 条目 in 条目们:#逐条

        if 取字段(条目,'path')==选中路径:#选中豁免

            结果.append(条目)#保留

            continue#下一条

        if 收窄:#收窄模式

            if 匹配(条目):#命中

                结果.append(条目)#保留

        elif 显示隐藏 or not 取字段(条目,'hidden'):#普通隐藏过滤

            结果.append(条目)#保留

    return 结果#可见列表



class 目录浏览器:#应用内目录浏览器状态机

    """Miller 视图 + 路径编辑 + 新建文件夹；关闭时返回 None。"""

    def __init__(自身,属性):#按 props 构造

        """播种状态；打开则立刻导航到主目录。"""

        自身.属性=属性#props

        自身.父层=None#左列列举

        自身.选中=None#选中行

        自身.子层=None#右列列举

        自身.加载中=False#扫描中

        自身.慢扫描=False#慢扫描指示

        自身.错误=None#告警文案

        自身.路径草稿=None#路径编辑草稿；None=面包屑模式

        自身.显示隐藏=False#显示隐藏

        自身.文件夹草稿=None#新建文件夹草稿；None=关闭

        自身.创建中=False#创建进行中

        自身.创建错误=None#创建告警

        自身.请求序号=0#请求世代

        自身.打开世代=0#打开世代

        自身.已扫描=None#上次草稿扫描

        自身.预览挂起=False#提交后挂起预览

        自身.扫描控制器=None#在飞中止句柄

        自身._打开边=取字段(属性,'open')#上一拍 open

        if 取字段(属性,'open'):#已打开

            自身.导航()#主目录



    def 更新(自身,属性):#props 变更

        """同步 props；处理 open 边沿。"""

        打开=取字段(属性,'open')#当前 open

        自身.属性=属性#最新

        if 打开 and not 自身._打开边:#上升沿

            自身.打开世代+=1#抬世代

            自身.父层=None#清空

            自身.选中=None#清空

            自身.子层=None#清空

            自身.创建中=False#清空

            自身.显示隐藏=False#重置

            自身.导航()#主目录

        elif not 打开 and 自身._打开边:#下降沿

            自身.打开世代+=1#抬世代

            自身.取代()#作废在飞

            自身.加载中=False#清加载

            自身.错误=None#清错误

            自身.路径草稿=None#关编辑

            自身.文件夹草稿=None#关新建

            自身.创建错误=None#清创建错误

        自身._打开边=打开#记下边



    def 翻译(自身,键,参数=None):#文案

        """绑定的 t。"""

        函数=取字段(自身.属性,'t',lambda 键,_=None:键)#翻译

        if 参数 is None:#无参

            return 函数(键)#键

        return 函数(键,参数)#带参



    def 取代(自身):#作废在飞扫描

        """抬序号并中止控制器。"""

        if 自身.扫描控制器 is not None:#有控制器

            中止=取字段(自身.扫描控制器,'abort')#中止

            if 中止 is not None:#可中止

                中止()#中止

            自身.扫描控制器=None#清

        自身.请求序号+=1#抬序号

        return 自身.请求序号#新序号



    def 启动列举(自身,路径):#发起一次列举

        """新控制器；返回序号与扫描结果。"""

        序号=自身.取代()#作废旧的

        控制器={'aborted':False}#控制器

        def 中止():#中止旗

            """标中止。"""

            控制器['aborted']=True#中止

        控制器['abort']=中止#挂上

        自身.扫描控制器=控制器#记下

        自身.慢扫描=False#重置慢扫描

        列举=取字段(自身.属性,'listDirectory')#列举调用

        结果=列举(路径,控制器) if 路径 is not None else 列举(None,控制器)#发起

        if hasattr(结果,'then'):#承诺

            return {'seq':序号,'scan':结果,'controller':控制器}#异步

        return {'seq':序号,'scan':结果,'controller':控制器}#同步



    def 解开扫描(自身,扫描):#结算扫描

        """承诺则等待。"""

        if hasattr(扫描,'then'):#承诺

            return 扫描.等待() if hasattr(扫描,'等待') else 扫描#等待

        if hasattr(扫描,'等待'):#可等待

            return 扫描.等待()#等待

        return 扫描#同步



    def 着陆(自身,路径,关编辑,宣告):#整视图着陆

        """选中锚定；远离显示根则两栏。"""

        包=自身.启动列举(路径)#发起

        序号=包['seq']#序号

        自身.加载中=True#加载

        if 宣告:#宣告失败

            自身.错误=None#清

        try:#扫描目标

            目标=自身.解开扫描(包['scan'])#目标层

        except Exception as 原因:#失败

            if 序号!=自身.请求序号:#过期

                return#丢弃

            自身.加载中=False#结束加载

            if 宣告:#宣告

                自身.错误=失败文案(原因)#告警

            return#结束

        if 序号!=自身.请求序号:#过期

            return#丢弃

        if not 关编辑 and 路径 is not None:#草稿扫描记下着陆

            自身.已扫描={'directory':路径,'landed':取字段(目标,'path')}#扫描记录

        def 单栏():#单栏着陆

            """目标独占。"""

            自身.父层=目标#左列

            自身.选中=None#无选中

            自身.子层=None#无右列

            自身.加载中=False#结束

            if 关编辑:#关编辑

                自身.路径草稿=None#关

            else:#草稿模式

                自身.错误=None#清错误

        屑=展示面包屑(目标,'')#显示链

        if len(屑)<2:#显示根

            单栏()#单栏

            return#结束

        屑链=取字段(目标,'crumbs') or []#原始屑

        if len(屑链)<2:#无父屑

            单栏()#单栏

            return#结束

        父屑=屑链[-2]#父屑

        try:#拉父层

            父包=自身.启动列举(取字段(父屑,'path'))#父腿；会抬序号——需改用 continueScan 语义

            # 父腿应共享序号：这里简化为接受新序号并校验父子一致

            父序号=父包['seq']#父序号

            父层=自身.解开扫描(父包['scan'])#父层

            if 父序号!=自身.请求序号:#过期

                return#丢弃

            分隔=分隔符于(父层)#分隔符

            def 折(值):#大小写折叠

                """Windows 忽略大小写。"""

                return 值.lower() if 分隔=='\\' else 值#折叠

            匹配=None#父层中的目标条目

            for 条目 in 取字段(父层,'entries') or []:#找匹配

                if 折(取字段(条目,'path') or '')==折(取字段(目标,'path') or ''):#命中

                    匹配=条目#记下

                    break#找到

            if 匹配 is None:#父窗截断

                单栏()#单栏

                return#结束

            自身.父层=父层#左列

            自身.选中=匹配#选中

            自身.子层=目标#右列

            自身.加载中=False#结束

            if 关编辑:#关编辑

                自身.路径草稿=None#关

            else:#草稿

                自身.错误=None#清

        except Exception:#父腿失败

            单栏()#单栏回退



    def 导航(自身,路径=None):#提交路径导航

        """编辑器关闭，失败宣告。"""

        自身.着陆(路径,True,True)#关编辑+宣告



    def 选定(自身,条目):#选中一行并预览子层

        """立即反映选中；子层异步到达。"""

        包=自身.启动列举(取字段(条目,'path'))#拉子层

        序号=包['seq']#序号

        if 自身.路径草稿 is not None:#编辑中选定

            自身.路径草稿=None#关编辑

        自身.选中=条目#选中

        自身.子层=None#清右列

        自身.加载中=True#加载

        自身.错误=None#清错误

        try:#扫描

            下一=自身.解开扫描(包['scan'])#子层

        except Exception as 原因:#失败

            if 序号!=自身.请求序号:#过期

                return#丢弃

            自身.加载中=False#结束

            自身.错误=失败文案(原因)#告警

            自身.选中=None#回退单栏

            return#结束

        if 序号!=自身.请求序号:#过期

            return#丢弃

        自身.子层=下一#右列

        自身.加载中=False#结束



    def 前进(自身,条目):#右列选定推进一层

        """子层变左列。"""

        if 自身.子层 is None:#无右列

            return#跳过

        自身.父层=自身.子层#推进

        自身.选定(条目)#再选



    def 取消路径编辑(自身):#放弃路径编辑

        """作废在飞并恢复面包屑。"""

        自身.取代()#作废

        自身.加载中=False#清加载

        自身.路径草稿=None#关编辑

        自身.错误=None#清错误

        if 自身.子层 is None:#无预览

            自身.选中=None#回退单栏

        if 自身.父层 is None:#无层

            自身.导航()#重开主目录



    def 确认打开(自身):#Open 按钮

        """采纳选中或当前层。"""

        目标=取字段(自身.选中,'path') if 自身.选中 is not None else 取字段(自身.父层,'path')#目标

        if 目标 is None:#无目标

            return#跳过

        打开=取字段(自身.属性,'onOpen')#确认

        if 打开 is not None:#有回调

            打开(目标)#采纳



    def 确认创建(自身):#创建文件夹

        """在目标下建子目录并选中。"""

        目标路径=取字段(自身.选中,'path') if 自身.选中 is not None else 取字段(自身.父层,'path')#目标

        if 目标路径 is None or 自身.文件夹草稿 is None or 自身.创建中:#不可创建

            return#跳过

        名=自身.文件夹草稿#原样名

        if 名.strip()=='':#全空白

            return#跳过

        自身.创建中=True#创建中

        自身.创建错误=None#清

        世代=自身.打开世代#打开世代

        创建=取字段(自身.属性,'createDirectory')#创建调用

        try:#创建

            已建=创建(目标路径,名)#建目录

            if hasattr(已建,'等待'):#承诺

                已建=已建.等待()#等待

        except Exception as 原因:#失败

            if 世代!=自身.打开世代:#过期

                return#丢弃

            自身.创建中=False#结束

            自身.创建错误=失败文案(原因)#告警

            return#结束

        if 世代!=自身.打开世代:#过期

            return#丢弃

        自身.创建中=False#结束

        自身.文件夹草稿=None#关新建

        包=自身.启动列举(目标路径)#重列目标

        序号=包['seq']#序号

        自身.加载中=True#加载

        自身.错误=None#清

        try:#重列

            层=自身.解开扫描(包['scan'])#层

        except Exception as 原因:#失败

            if 序号!=自身.请求序号:#过期

                return#丢弃

            自身.加载中=False#结束

            自身.错误=失败文案(原因)#告警

            return#结束

        if 序号!=自身.请求序号:#过期

            return#丢弃

        自身.父层=层#左列

        自身.加载中=False#结束

        自身.选定({'name':名,'path':已建,'hidden':False})#选中新建



    def 视图(自身):#读视图模型

        """关闭返回 None。"""

        if not 取字段(自身.属性,'open'):#关闭

            return None#不渲染

        屑源=自身.子层 if 自身.子层 is not None else 自身.父层#当前层

        键入前缀=None#过滤尾

        if 屑源 is not None and 自身.路径草稿 is not None:#编辑中

            键入前缀=读草稿(屑源,自身.路径草稿,自身.已扫描).get('tail')#尾

        屑=展示面包屑(屑源,自身.翻译('browser.home')) if 屑源 is not None else []#面包屑

        目标路径=取字段(自身.选中,'path') if 自身.选中 is not None else 取字段(自身.父层,'path')#Open 目标

        父惰性=取字段(自身.属性,'busy') or 自身.文件夹草稿 is not None#父控件惰性

        左列=可见条目(#左列可见

            取字段(自身.父层,'entries') or [],#条目

            取字段(自身.选中,'path'),#选中

            自身.显示隐藏,#隐藏开关

            键入前缀 if 自身.子层 is None else None,#仅单栏过滤

        ) if 自身.父层 is not None else []#无父则空

        右列=可见条目(#右列可见

            取字段(自身.子层,'entries') or [],#条目

            None,#右列无选中

            自身.显示隐藏,#隐藏开关

            键入前缀,#过滤

        ) if 自身.子层 is not None and 自身.选中 is not None else []#两栏才有

        return {#视图模型

            'title':自身.翻译('browser.title'),#标题

            'crumbs':屑,#面包屑

            'pathDraft':自身.路径草稿,#路径草稿

            'left':左列,#左列

            'right':右列,#右列

            'twoPane':自身.选中 is not None,#两栏

            'loading':自身.加载中,#加载

            'slowScan':自身.慢扫描,#慢扫描

            'error':自身.错误,#告警

            'truncated':取字段(自身.父层,'truncated') or 取字段(自身.子层,'truncated'),#截断

            'showHidden':自身.显示隐藏,#隐藏开关

            'folderDraft':自身.文件夹草稿,#新建草稿

            'creatingFolder':自身.创建中,#创建中

            'createError':自身.创建错误,#创建错误

            'targetPath':目标路径,#Open 目标

            'parentInert':父惰性,#父惰性

            'draftPending':自身.路径草稿 is not None,#草稿未提交

            'labels':{#文案

                'home':自身.翻译('browser.home'),#主目录

                'newFolder':自身.翻译('browser.newFolder'),#新建

                'open':自身.翻译('browser.open'),#打开

                'cancel':自身.翻译('browser.cancel'),#取消

                'loading':自身.翻译('browser.loading'),#加载中

                'truncated':自身.翻译('browser.truncated'),#截断

                'showHidden':自身.翻译('browser.showHidden'),#显示隐藏

                'editPath':自身.翻译('browser.editPath'),#编辑路径

                'create':自身.翻译('browser.create'),#创建

                'folderName':自身.翻译('browser.folderName'),#文件夹名

                'untitledFolder':自身.翻译('browser.untitledFolder'),#未命名

            },#文案结束

            'cssModule':'目录浏览器.module.css',#样式

        }#视图结束



    def __call__(自身,属性=None):#组件调用形

        """对齐 React 组件调用；返回视图或 None。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.视图()#视图


