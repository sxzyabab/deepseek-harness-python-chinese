import threading#并发与中止
from uuid import uuid4 as 生成随机UUID#安装请求 id
from ...存储 import 创建快照存储#快照存储
from .呈现 import 短名#短名排序

__all__=['是否安装待决','行键','包视图','排序包表','插件装载控制','空闲安装']#仅中文公开名

空闲安装={#安装对话框空闲态
    'open':False,'spec':'','phase':'idle','inputError':None,'subject':None,'runs':[],
    'detailsOpen':False,'installed':None,'restartRequired':False,'failure':None,
    'approvedBuilds':[],'enabling':False,
}#空闲结束

class 远程应答错误(Exception):
    """拒绝应答或 Host 未能应用的变更。"""
    def __init__(自身,原因,码=None):
        """记下原因与可选拒码。"""
        super().__init__(原因)#消息
        自身.原因=原因#原因
        自身.码=码

def 是否安装待决(阶段):
    """安装是否仍由 Host 拥有。"""
    return 阶段 in ('starting','running','cancelling','applying')#待决

def 行键(入口标识):
    """忙碌表中一行占用的键。"""
    return f'row:{入口标识}'#键

def 包视图(组合包,插件表):
    """组合包与其行对应的存活条目合成视图。"""
    行表=[]#行
    for 行 in 组合包['rows']:#每行
        入口=行['entryId'] if 'entryId' in 行 else None#入口
        存活=None#存活条目
        if 入口 is not None:#有入口
            for 插件 in 插件表:
                if 插件['entryId']==入口:#命中
                    存活=插件#记下
                    break#停
        项={'rowId':行['rowId'],'moduleName':行['moduleName'],
            'enabled':存活['enabled'] if 存活 is not None and 'enabled' in 存活 else False,
            'phase':存活['fiberPhase'] if 存活 is not None and 'fiberPhase' in 存活 else None}#基础
        if 入口 is not None:项['entryId']=入口#入口
        if 存活 is not None and 'readOnlyReason' in 存活 and 存活['readOnlyReason'] is not None:
            项['readOnlyReason']=存活['readOnlyReason']#只读因
        行表.append(项)#加入
    视图={'name':组合包['name'],'installed':组合包['installed'],'optional':组合包['optional'],
        'enabled':组合包['enabled'],'rows':行表}#包
    if 'version' in 组合包 and 组合包['version'] is not None:视图['version']=组合包['version']#版本
    if 'description' in 组合包 and 组合包['description'] is not None:视图['description']=组合包['description']#描述
    if 'readOnlyReason' in 组合包 and 组合包['readOnlyReason'] is not None:视图['readOnlyReason']=组合包['readOnlyReason']#只读
    if 'error' in 组合包 and 组合包['error'] is not None:视图['error']=组合包['error']#错误
    return 视图#视图

def 排序包表(包表):
    """按人读短名排序，启停不挪卡片。"""
    def 短名键(包):
        """排序键。"""
        return 短名(包['name'])#短名
    return sorted(包表,key=短名键)#排序

def 失败构造(错误,种类,待允许=None):
    """对话框对失败变更的读法。"""
    结果={'reason':错误['diagnostic'] if 错误 is not None and 'diagnostic' in 错误 and 错误['diagnostic'] is not None else ''}#原因
    if 错误 is not None and 'code' in 错误:结果['code']=错误['code']
    if 种类 is not None:结果['kind']=种类#种类
    if 待允许 is not None and len(待允许)>0:结果['pendingBuilds']=list(待允许)#待允许
    return 结果#失败

def 原因串(错误):
    """抛出失败所说：拒绝原因或错误消息。"""
    if isinstance(错误,Exception):return str(错误)#消息
    return str(错误)

def 失败提示(错误,主体,序号):
    """失败提示：拒绝保留码，其余保留原文。"""
    码=错误.码 if isinstance(错误,远程应答错误) else None
    提示={'kind':'failed','reason':原因串(错误),'action':主体['action'],'seq':序号}#基础
    if 码 is not None:提示['code']=码
    if 'packageName' in 主体:提示['packageName']=主体['packageName']#包名
    return 提示#提示

def 结算运行表(运行表,退出码):
    """把仍开放的运行结算为 exitCode。"""
    结果=[]#新表
    for 运行 in 运行表:#每运行
        if 'exitCode' not in 运行:#未结算
            结果.append({**运行,'exitCode':退出码})#结算
        else:
            结果.append(运行)#已有
    return 结果#表

class 插件装载控制:#装载页状态拥有者
    """经 pluginManager Remote 读写 profile 的插件。"""
    def __init__(自身,上下文):
        """上下文提供 remote.pluginManager 与 remote.pluginInventory。"""
        自身.上下文=上下文#上下文
        自身.存储=创建快照存储({#初态
            'status':'idle','packages':[],'busy':[],'notice':None,
            'install':dict(空闲安装),'confirm':None,'highlight':None,
        })#存储
        自身.飞行中=None#飞行读取
        自身.再跑=False#需再跑
        自身.代次=0#代次
        自身.已拆除=False#拆除
        自身.待确认=None#待确认动作
        自身.检查中止=None#检查 Event
        自身.提示序号=0#提示序号

    def 取快照(自身):
        """读标签状态。"""
        return 自身.存储.getSnapshot()#快照

    def 拆除(自身):
        """停止发布并丢弃晚到结算。"""
        自身.已拆除=True#死
        自身.代次+=1#换代

    def 注入(自身,配置账本):
        """构造席位登记注入的面。"""
        return {#注入面
            'hooks':{'pluginManager':自身.存储,'configLedger':配置账本},#钩
            'ensure':自身.确保,#首读
            'refresh':自身.刷新,#刷新
            'openInstall':自身.开安装,#开对话框
            'closeInstall':自身.关安装,#关
            'editInstallSpec':自身.编辑安装规格,#编辑
            'runInstall':自身.跑安装触发,#安装
            'approveBuildsAndRetry':自身.允许构建并重试触发,#允许
            'cancelInstall':自身.取消安装触发,#取消
            'cancelInstallAndClose':自身.取消并关闭触发,#取消关
            'toggleInstallDetails':自身.切换安装详情,#详情
            'enableInstalled':自身.启用已安装触发,#启用
            'clearHighlight':自身.清高亮,#清亮
            'setEnabled':自身.设启用,#启停包
            'uninstall':自身.卸载,#卸载
            'confirm':自身.确认触发,#确认
            'cancelConfirm':自身.取消确认,#取消确认
            'setRowEnabled':自身.设行启用,#启停行
            'dismissNotice':自身.关掉提示,#关提示
        }#面结束

    def 确保(自身):
        """标签首次渲染时读 Host。"""
        if 自身.取快照()['status']=='idle':#空闲
            自身.加载()#加载

    def 刷新(自身):
        """再读 Host。"""
        自身.加载()#加载

    def 开安装(自身):
        """打开安装对话框。"""
        if not 是否安装待决(自身.取快照()['install']['phase']):#非待决
            自身._补丁({'install':{**空闲安装,'open':True}})#开

    def 关安装(自身):
        """关闭对话框；检查中则丢弃，Host 拥有的运行须先取消。"""
        if 是否安装待决(自身.取快照()['install']['phase']):#待决
            return#停
        自身._中止检查()#中止
        自身._补丁({'install':dict(空闲安装)})#关

    def 编辑安装规格(自身,文本):
        """编辑规格；检查或安装中不可改。"""
        安装=自身.取快照()['install']#安装
        if 安装['phase']=='checking' or 是否安装待决(安装['phase']):#锁定
            return#停
        if 安装['phase']=='idle':#空闲
            自身._补丁安装({'spec':文本,'inputError':None})#改规格
        else:#结果后重开
            自身._补丁安装({**空闲安装,'open':True,'spec':文本})#重开

    def 跑安装触发(自身):
        """触发安装。"""
        threading.Thread(target=自身._跑安装,daemon=True).start()#线程

    def 允许构建并重试触发(自身):
        """允许待决脚本并重试。"""
        threading.Thread(target=自身._允许构建并重试,daemon=True).start()#线程

    def 取消安装触发(自身):
        """取消安装。"""
        def 干活():
            """取消不关闭。"""
            自身._取消安装(False)#取消
        threading.Thread(target=干活,daemon=True).start()#线程

    def 取消并关闭触发(自身):
        """取消并关闭。"""
        def 干活():
            """取消并关。"""
            自身._取消安装(True)#取消关
        threading.Thread(target=干活,daemon=True).start()#线程

    def 切换安装详情(自身):
        """折叠/展开安装详情。"""
        自身._补丁安装({'detailsOpen':not 自身.取快照()['install']['detailsOpen']})#翻转

    def 启用已安装触发(自身):
        """启用刚装包。"""
        threading.Thread(target=自身._启用已安装,daemon=True).start()#线程

    def 清高亮(自身):
        """丢掉列表高亮。"""
        if 自身.取快照()['highlight'] is not None:#有亮
            自身._补丁({'highlight':None})

    def 设启用(自身,包名,启用):
        """把组合包放入或移出层列表。"""
        动作='enable' if 启用 else 'disable'#动作
        def 干活():
            """远程启停。"""
            自身._已应用(自身.上下文.remote.pluginManager.setBundleEnabled(包名,启用).等待(),包名)#应用
        def 跑启停():
            """在忙碌键下跑。"""
            自身._跑(包名,{'packageName':包名,'action':动作},干活)#跑
        threading.Thread(target=跑启停,daemon=True).start()#线程

    def 卸载(自身,包名):
        """请求确认后卸载。"""
        def 干活():
            """远程移除。"""
            自身._已应用(自身.上下文.remote.pluginManager.removeBundle(包名).等待(),包名)#应用
        def 待确认跑():
            """确认后跑卸载。"""
            自身._跑(包名,{'packageName':包名,'action':'uninstall'},干活)#跑
        自身.待确认=待确认跑#待确认
        自身._补丁({'confirm':{'action':'uninstall','packageName':包名}})#确认态

    def 确认触发(自身):
        """确认待决破坏动作。"""
        threading.Thread(target=自身._确认,daemon=True).start()#线程

    def 取消确认(自身):
        """取消确认。"""
        自身.待确认=None
        自身._补丁({'confirm':None})

    def 设行启用(自身,入口标识,启用):
        """启停组合包一行。"""
        动作='rowEnable' if 启用 else 'rowDisable'#动作
        键=行键(入口标识)#忙碌键
        def 干活():
            """远程启停行。"""
            自身._已应用(自身.上下文.remote.pluginManager.setPluginEnabled(入口标识,启用).等待(),入口标识)#应用
        def 跑行():
            """在忙碌键下跑。"""
            自身._跑(键,{'packageName':入口标识,'action':动作},干活)#跑
        threading.Thread(target=跑行,daemon=True).start()#线程

    def 关掉提示(自身):
        """关掉 toast。"""
        自身._补丁({'notice':None})

    def 安装进度(自身,进度):
        """跟随 Host 对本对话框安装的取消窗口。"""
        安装=自身.取快照()['install']#安装
        if 安装.get('requestId')!=进度['requestId'] or not 是否安装待决(安装['phase']):#无关
            return#停
        if 安装['phase']=='cancelling' and 进度['phase']=='installing':#取消优先
            return#停
        阶段='running' if 进度['phase']=='installing' else 进度['phase']#映射
        自身._补丁安装({'phase':阶段})#更新

    def 追加日志(自身,块):
        """把属于本安装的日志块折入 pnpm 命令。"""
        安装=自身.取快照()['install']#安装
        if 块['requestId']!=安装.get('requestId'):#无关
            return#停
        下标=-1
        for 序,运行 in enumerate(安装['runs']):#遍历
            if 运行['jobId']==块['jobId']:#命中
                下标=序#记下
                break#停
        if 下标==-1 and not 是否安装待决(安装['phase']):#晚到新作业
            return#停
        结算={} if 'exitCode' not in 块 else {'exitCode':块['exitCode']}#结算
        if 下标==-1:#新运行
            运行表=list(安装['runs'])+[{'jobId':块['jobId'],'command':' '.join(块['argv']),'cwd':块['cwd'],'output':块['text'],**结算}]#追加
        else:#追加输出
            运行表=[]#新表
            for 序,运行 in enumerate(安装['runs']):#遍历
                if 序==下标:#命中
                    运行表.append({**运行,'output':运行['output']+块['text'],**结算})#合并
                else:
                    运行表.append(运行)#原样
        自身._补丁安装({'runs':运行表})#更新

    def 加载(自身):
        """读组合包与行条目；飞行中则标记再跑。"""
        if 自身.已拆除:#已死
            return#停
        if 自身.飞行中 is not None:#飞行中
            自身.再跑=True#再跑
            自身.飞行中.wait()#等
            return#停
        事件=threading.Event()#完成事件
        自身.飞行中=事件#记下
        def 干活():
            """读取结算。"""
            try:
                自身._读取()#读
            finally:
                自身.飞行中=None
                事件.set()#完成
        threading.Thread(target=干活,daemon=True).start()#线程
        事件.wait()#阻塞至完成

    def _读取(自身):
        """合并重叠读取。"""
        while True:#循环
            自身.再跑=False
            自身.代次+=1#晋代
            代次=自身.代次#本代
            if 自身.取快照()['status']=='idle':#空闲
                自身._补丁({'status':'loading'})#加载中
            清单=自身.上下文.remote.pluginInventory.list().等待()#清单
            if 代次!=自身.代次:#过期
                return#停
            if not 清单['ok']:#失败
                自身._补丁({'status':'error'})#错误
                if not 自身.再跑:return#停
                continue#再跑
            值=清单['value']#值
            if 值.get('managementAvailable') is not True:#不可管
                自身._补丁({'status':'unavailable','packages':[]})#不可用
                if not 自身.再跑:return#停
                continue#再跑
            组合结果=[None]#槽
            插件结果=[None]#槽
            def 拉组合():
                """拉组合包。"""
                组合结果[0]=自身.上下文.remote.pluginManager.listBundles().等待()#等
            def 拉插件():
                """拉插件。"""
                插件结果[0]=自身.上下文.remote.pluginManager.listPlugins().等待()#等
            线1=threading.Thread(target=拉组合,daemon=True)#线
            线2=threading.Thread(target=拉插件,daemon=True)#线
            线1.start()
            线2.start()
            线1.join()#等
            线2.join()#等
            if 代次!=自身.代次:#过期
                return#停
            组合包=组合结果[0]#组合
            插件=插件结果[0]#插件
            if not 组合包['ok'] or not 插件['ok']:#失败
                自身._补丁({'status':'error'})#错误
                if not 自身.再跑:return#停
                continue#再跑
            自身._补丁({'status':'ready','packages':排序包表([包视图(包,插件['value']) for 包 in 组合包['value']])})#就绪
            if not 自身.再跑:#无需再跑
                return#停

    def _确认(自身):
        """执行待确认动作。"""
        待=自身.待确认#待
        自身.待确认=None
        自身._补丁({'confirm':None})
        if 待 is not None:#有
            待()#执行

    def _中止检查(自身):
        """丢弃飞行中的检查。"""
        if 自身.检查中止 is not None:#有
            自身.检查中止.set()#中止
            自身.检查中止=None

    def _已过时(自身,信号):
        """结算是否太晚。"""
        return 自身.已拆除 or (信号 is not None and 信号.is_set())#过时

    def _跑安装(自身):
        """检查规格后安装。"""
        状态=自身.取快照()#状态
        安装=状态['install']#安装
        规格=安装['spec'].strip()#规格
        if 安装['phase']=='checking' or 是否安装待决(安装['phase']) or 规格=='':#不可
            return#停
        if any(包['name']==规格 for 包 in 状态['packages']):#已装
            自身._补丁安装({'phase':'idle','inputError':{'problem':'already-installed','reason':规格}})#拒
            return#停
        自身._中止检查()#中止旧
        控制器=threading.Event()#中止
        自身.检查中止=控制器#记下
        自身._补丁安装({#检查中
            'phase':'checking','inputError':None,'subject':None,'runs':[],'detailsOpen':False,
            'installed':None,'restartRequired':False,'failure':None,'approvedBuilds':[],
        })#补丁
        检查=自身.上下文.remote.pluginManager.inspect(规格,控制器).等待()#检查
        if 自身._已过时(控制器):#过时
            return#停
        自身.检查中止=None#清
        if not 检查['ok']:#失败
            自身._补丁安装({'phase':'idle','inputError':{'problem':'unknown','reason':检查['error']['message']}})#拒
            return#停
        值=检查['value']#值
        if 值['status']=='refused':#拒绝
            自身._补丁安装({'phase':'idle','inputError':{'problem':值['problem'],'reason':值['reason']}})#拒
            return#停
        自身._开始安装({'spec':规格,**值})#开始

    def _开始安装(自身,主体,已允许=None):
        """把已检查规格交给 Host。"""
        规格=主体['spec']#规格
        请求标识=str(生成随机UUID())#请求 id
        自身._补丁安装({'phase':'starting','requestId':请求标识,'subject':主体,'runs':[],'failure':None,'installed':None,'approvedBuilds':[]})#起始
        选项={'enabled':False,'requestId':请求标识}#选项
        if 已允许 is not None:选项['approvedBuilds']=list(已允许)#已允许
        结果=自身.上下文.remote.pluginManager.installBundle(规格,选项).等待()#安装
        if 自身.已拆除 or 自身.取快照()['install'].get('requestId')!=请求标识:#过时
            return#停
        运行表=自身.取快照()['install']['runs']#运行
        if not 结果['ok']:#传输失败
            自身._补丁安装({'phase':'failed','runs':结算运行表(运行表,None),'failure':{'reason':结果['error']['message']}})#失败
        elif 结果['value']['application']=='cancelled':#取消
            自身.提示序号+=1#序号
            自身._再给规格({'kind':'cancelled','seq':自身.提示序号})#再给
        elif 结果['value']['application']=='failed':#失败
            包结果=结果['value']['packageResult'] if 'packageResult' in 结果['value'] else None#包结果
            退出=包结果['exitCode'] if 包结果 is not None and 'exitCode' in 包结果 else None#退出码
            种类=包结果['kind'] if 包结果 is not None and 'kind' in 包结果 else None#种类
            待=结果['value']['pendingBuilds'] if 'pendingBuilds' in 结果['value'] else None#待允许
            错误=结果['value']['error'] if 'error' in 结果['value'] else None#错误
            自身._补丁安装({'phase':'failed','runs':结算运行表(运行表,退出),'failure':失败构造(错误,种类,待)})#失败
        else:#成功
            值=结果['value']#值
            自身._补丁安装({#完成
                'phase':'done','runs':结算运行表(运行表,0),
                'installed':值['bundle'] if 'bundle' in 值 else None,
                'restartRequired':值['application']=='restart-required',
                'approvedBuilds':值['approvedBuilds'] if 'approvedBuilds' in 值 and 值['approvedBuilds'] is not None else [],
            })#完成
        自身.加载()#刷新

    def _允许构建并重试(自身):
        """允许失败运行留下的脚本并重跑。"""
        安装=自身.取快照()['install']#安装
        失败=安装['failure']#失败
        待=失败['pendingBuilds'] if 失败 is not None and 'pendingBuilds' in 失败 else None#待
        if 安装['phase']!='failed' or 安装['subject'] is None or 待 is None or len(待)==0:#不可
            return#停
        自身._开始安装(安装['subject'],待)#重跑

    def _取消安装(自身,关闭后=False):
        """离开检查/失败屏，或请 Host 停止运行。"""
        安装=自身.取快照()['install']#安装
        if not 关闭后 and 安装['phase'] in ('checking','failed'):#回编辑
            自身._中止检查()#中止
            自身._再给规格()#再给
            return#停
        if 安装['phase']!='running' or 'requestId' not in 安装 or 安装['requestId'] is None:#不可停
            return#停
        请求标识=安装['requestId']#id
        自身._补丁安装({'phase':'cancelling','failure':None})#取消中
        结果=自身.上下文.remote.pluginManager.cancelInstall(请求标识).等待()#取消
        当前=自身.取快照()['install']#当前
        if 自身.已拆除 or 当前.get('requestId')!=请求标识 or not 是否安装待决(当前['phase']):#过时
            return#停
        if not 结果['ok']:#未确认
            自身._补丁安装({'phase':'running','failure':{'reason':结果['error']['message'],'cancelUnconfirmed':True}})#未确认
            return#停
        状态=结果['value']['status']#状态
        if 状态=='cancelled':#已取消
            自身.提示序号+=1#序号
            提示={'kind':'cancelled','seq':自身.提示序号}#提示
            if 关闭后:#关闭
                自身._补丁({'install':dict(空闲安装),'notice':提示})#关
            else:
                自身._再给规格(提示)#再给
            自身.加载()#刷新
        elif 状态=='too-late':#太晚
            自身._补丁安装({'phase':'applying'})#应用中
        else:#未确认
            自身._补丁安装({'phase':'running','failure':{'reason':'','cancelUnconfirmed':True}})#未确认

    def _再给规格(自身,提示=None):
        """回到规格输入，保留规格。"""
        安装=自身.取快照()['install']#安装
        补丁={'install':{**空闲安装,'open':安装['open'],'spec':安装['spec']}}#再开
        if 提示 is not None:补丁['notice']=提示#提示
        自身._补丁(补丁)#发布

    def _启用已安装(自身):
        """启用刚装组合包并高亮。"""
        安装=自身.取快照()['install']#安装
        if 安装['phase']!='done' or 安装['enabling']:#不可
            return#停
        名=安装['installed']#包名
        自身._补丁安装({'enabling':True})#启用中
        if 名 is not None:#有包
            结果=自身.上下文.remote.pluginManager.setBundleEnabled(名,True).等待()#启用
            if 自身.已拆除:#已死
                return#停
            try:
                自身._已应用(结果,名)#应用
            except Exception as 错误:#失败
                自身.提示序号+=1#序号
                自身._补丁({'notice':失败提示(错误,{'packageName':名,'action':'enable'},自身.提示序号)})#提示
        自身._补丁({'install':dict(空闲安装),'highlight':名})#关并高亮
        自身.加载()#刷新

    def _跑(自身,键,主体,动作):
        """在忙碌键下跑动作，失败变提示，事后重读。"""
        if 自身.已拆除 or 键 in 自身.取快照()['busy']:#不可
            return#停
        自身._补丁({'busy':list(自身.取快照()['busy'])+[键],'notice':None})#忙碌
        try:
            动作()#执行
        except Exception as 错误:#失败
            自身.提示序号+=1#序号
            自身._补丁({'notice':失败提示(错误,主体,自身.提示序号)})#提示
        finally:
            自身._补丁({'busy':[项 for 项 in 自身.取快照()['busy'] if 项!=键]})#去忙碌
        自身.加载()#刷新

    def _已应用(自身,应答,包名):
        """发布变更结果。"""
        if not 应答['ok']:#拒绝
            raise 远程应答错误(应答['error']['message'])#抛
        结果=应答['value']#值
        应用=结果['application']#应用态
        if 应用=='failed':#失败
            错误=结果['error'] if 'error' in 结果 else None#错误
            诊断=错误['diagnostic'] if 错误 is not None and 'diagnostic' in 错误 else ''#诊断
            码=错误['code'] if 错误 is not None and 'code' in 错误 else None
            raise 远程应答错误(诊断,码)#抛
        if 应用=='cancelled':#取消
            自身.提示序号+=1#序号
            自身._补丁({'notice':{'kind':'cancelled','seq':自身.提示序号}})#提示
            return#停
        if 应用=='restart-required':#重启
            自身.提示序号+=1#序号
            自身._补丁({'notice':{'kind':'restart','packageName':包名,'seq':自身.提示序号}})#提示
            return#停
        if 应用=='overridden':#覆盖
            自身.提示序号+=1#序号
            自身._补丁({'notice':{'kind':'overridden','packageName':包名,'seq':自身.提示序号}})#提示
            return#停
        #applied：无事

    def _补丁(自身,下一):
        """合并状态补丁。"""
        if 自身.已拆除:#已死
            return#停
        自身.存储.set({**自身.取快照(),**下一})#发布

    def _补丁安装(自身,下一):
        """合并安装态补丁。"""
        自身._补丁({'install':{**自身.取快照()['install'],**下一}})#补丁
