"""有界源准入、共享内容转换与调用方拥有的 PDF 交付。"""
import hashlib,json,threading#内容摘要、源键序列化、任务线程
from concurrent.futures import Future as 原生结果#读取方结算
from ...工具.超时 import 中止控制器,已中止,若已中止则抛出,等待中止#中止原语
from .异常 import office转pdf错误#分类失败
from .标识构造 import office转pdf键#内容身份

__all__=['转换队列']#仅中文公开名

class 读取方:
    """一次准入读取的结算句柄。"""
    def __init__(自身,任务,源串,优先级,结局):
        """记下所属任务与结算 Future。"""
        自身.任务=任务#可迁移到同摘要任务
        自身.源串=源串#源定位串
        自身.优先级=优先级#foreground|background
        自身.结局=结局#Future
        自身.已清理=False#清理旗

class 转换任务:
    """一条共享转换工作。"""
    def __init__(自身,请求,优先级,控制器):
        """排队元数据与读取方集合。"""
        自身.请求=请求#转换请求
        自身.优先级=优先级#可被前台提权
        自身.控制器=控制器#中止控制器
        自身.读取方集=set()#读取方
        自身.源集=set()#源串集合
        自身.状态='queued'#queued|running|finished

class 转换队列:
    """一个转换世代拥有全部排队源、转换、读取方与保留 PDF。"""
    def __init__(自身,配置,世代,转换函数):
        """配置为已校验限额；转换函数执行一次准入转换并在临时清理后结算。"""
        自身._配置=配置#限额
        自身._世代=世代#提供方寿命
        自身._转换函数=转换函数#引擎入口
        自身._就绪={}#键 → 结果
        自身._别名={}#源串 → 键
        自身._源表={}#源串 → 任务
        自身._摘要表={}#键 → 任务
        自身._排队=[]#任务列表
        自身._线程表=set()#在途工作线程
        自身._任务集=set()#全部任务
        自身._已缓存字节=0#保留 PDF 字节
        自身._源字节=0#活动预留
        自身._运行中=0#并发转换数
        自身._后台数=0#后台运行数
        自身._读取方数=0#未完成读取方
        自身._已拆除=False#拆除旗
        自身._锁=threading.RLock()#队列互斥

    def 读取(自身,请求,信号=None):
        """准入元数据后再读源字节；跨授权读取方共享转换。阻塞至结果或失败。"""
        若已中止则抛出(信号)#入口
        with 自身._锁:#互斥
            if 自身._已拆除:#已拆
                raise 自身._不可用错误()#拒绝
            源侧=请求['source']#源描述
            if 'bytes' in 源侧 and 源侧['bytes'] is not None and 源侧['bytes']>自身._配置['maxInputBytes']:#已知过大
                raise office转pdf错误('input-too-large','The Office source exceeds maxInputBytes.')#拒绝
            源串=json.dumps([源侧['key'],源侧['version'],请求['extension']],ensure_ascii=False,separators=(',',':'))#源定位
            别名=自身._别名.get(源串)#缓存键
            缓存=None if 别名 is None else 自身._就绪.get(别名)#命中
            if 缓存 is not None:#别名命中
                自身._就绪.pop(缓存['cacheKey'],None)#LRU 挪尾
                自身._就绪[缓存['cacheKey']]=缓存#重插
                自身._别名.pop(源串,None)#重挂
                自身._别名[源串]=缓存['cacheKey']#别名
                return 自身._复制结果(缓存)#独立副本
            读取方上限=自身._配置['maxReaders']-1 if 请求['priority']=='background' else 自身._配置['maxReaders']#后台留一
            if 自身._读取方数>=读取方上限:#满
                raise 自身._忙碌错误()#拒绝
            if 请求['priority']=='background' and 自身._配置['maxBackgroundConversions']==0:#禁后台
                raise 自身._忙碌错误()#拒绝
            任务=自身._源表.get(源串)#已有任务
            if 任务 is None:#新建
                if len(自身._排队)>=自身._配置['maxQueuedJobs']:#队列满
                    过时=None#待踢
                    if 请求['priority']=='foreground':#前台可踢后台
                        for 项 in 自身._排队:#找后台
                            if 项.优先级=='background':#命中
                                过时=项#记下
                                break#停
                    if 过时 is None:#无可踢
                        raise 自身._忙碌错误()#拒绝
                    自身._失败结算(过时,自身._忙碌错误())#踢掉
                任务=转换任务(请求,请求['priority'],中止控制器())#新任务
                任务.源集.add(源串)#源
                自身._源表[源串]=任务#登记源
                自身._任务集.add(任务)#登记
                自身._排队.append(任务)#入队
            if 请求['priority']=='foreground':#提权
                任务.优先级='foreground'#前台
            自身._读取方数+=1#占名额
            结局=原生结果()#读取方 Future
            一方=读取方(任务,源串,请求['priority'],结局)#读取方
            任务.读取方集.add(一方)#挂上
            if 信号 is not None:#有取消
                def 监视中止(读=一方,信=信号,结=结局):
                    """信号中止后拒绝该读取方。"""
                    等待中止(信)#阻塞
                    with 自身._锁:#互斥
                        if 读.已清理:#已清理
                            return#忽略
                        自身._释放读取方(读)#释放
                        原因=None#中止原因
                        try:
                            若已中止则抛出(信)#取原因
                        except BaseException as 错:
                            原因=错#记下
                        if not 结.done():#未结算
                            if isinstance(原因,BaseException):#有原因异常
                                结.set_exception(原因)#拒绝
                            else:#无具体原因
                                结.set_exception(Exception('Office conversion cancelled'))#固定文案
                        if len(读.任务.读取方集)==0:#末位读取方
                            自身._取消任务(读.任务)#取消共享
                        自身._抽干()#放行排队
                threading.Thread(target=监视中止,daemon=True).start()#后台监视
            自身._抽干()#尝试开工
        return 结局.result()#阻塞至结算

    def 拆除(自身):
        """取消全部读取方并等到实际读取、转换与临时清理结束。"""
        with 自身._锁:#互斥
            自身._已拆除=True#标记
            for 任务 in list(自身._任务集):#逐任务
                自身._失败结算(任务,自身._不可用错误())#失败
            自身._就绪.clear()#清空缓存
            自身._别名.clear()#清空别名
            自身._已缓存字节=0#归零
            线程表=list(自身._线程表)#快照
        for 线程 in 线程表:#等待
            线程.join()#结算

    def _忙碌错误(自身):
        """准入上限。"""
        return office转pdf错误('busy','The document converter has reached its admission limit.')#忙碌

    def _不可用错误(自身):
        """提供方不可用。"""
        return office转pdf错误('unavailable','The document converter is unavailable.')#不可用

    def _复制结果(自身,结果):
        """独立 PDF 与字体列表。"""
        return {'pdf':bytes(结果['pdf']),'missingFonts':list(结果['missingFonts']),'cacheKey':结果['cacheKey'],'generation':结果['generation']}#副本

    def _释放读取方(自身,一方):
        """从任务摘掉读取方并调整优先级与源索引。"""
        任务=一方.任务#所属
        任务.读取方集.discard(一方)#摘掉
        if 任务.状态=='queued':#仍排队
            有前台=False#是否前台
            for 读 in 任务.读取方集:#扫
                if 读.优先级=='foreground':#前台
                    有前台=True#记下
                    break#停
            任务.优先级='foreground' if 有前台 else 'background'#降/升
        仍有同源=False#同源残留
        for 读 in 任务.读取方集:#扫
            if 读.源串==一方.源串:#同源
                仍有同源=True#记下
                break#停
        if not 仍有同源:#末位该源
            任务.源集.discard(一方.源串)#摘源
            if 自身._源表.get(一方.源串) is 任务:#仍指向本任务
                自身._源表.pop(一方.源串,None)#去源表
        一方.已清理=True#停止监视副作用
        自身._读取方数-=1#名额

    def _取消任务(自身,任务):
        """中止任务；若仍排队则出队。"""
        任务.控制器.中止()#中止
        if 任务.状态=='queued':#排队中
            if 任务 in 自身._排队:#在队
                自身._排队.remove(任务)#出队
            任务.状态='finished'#结束
            自身._任务集.discard(任务)#去集

    def _失败结算(自身,任务,错误):
        """拒绝全部读取方并取消任务。"""
        for 读 in list(任务.读取方集):#快照
            自身._释放读取方(读)#释放
            if not 读.结局.done():#未结算
                读.结局.set_exception(错误 if isinstance(错误,BaseException) else Exception(str(错误)))#拒绝
        自身._取消任务(任务)#取消

    def _预留字节数(自身,任务):
        """源预留：已知用 stat，否则整输入上限。"""
        字节=任务.请求['source']['bytes'] if 'bytes' in 任务.请求['source'] else None#可选
        if 字节 is None:#未知
            return max(1,自身._配置['maxInputBytes'])#整上限
        return max(1,字节)#已知

    def _抽干(自身):
        """在并发与容量允许时拉起排队任务。"""
        while not 自身._已拆除 and 自身._运行中<自身._配置['maxConcurrentConversions']:#可开
            前台在等=False#前台阻塞
            for 项 in 自身._排队:#扫
                if 项.优先级=='foreground':#前台
                    前台在等=True#记下
                    break#停
            选中=None#候选
            for 项 in 自身._排队:#找合格
                if 前台在等 and 项.优先级!='foreground':#后台让路
                    continue#跳
                预留=自身._预留字节数(项)#预留
                if 自身._源字节+预留>自身._配置['maxSourceBytes']:#容量不足
                    continue#跳
                if 项.优先级!='foreground':#后台
                    后台上限=min(自身._配置['maxBackgroundConversions'],max(1,自身._配置['maxConcurrentConversions']-1))#保留前台槽
                    if 自身._后台数>=后台上限:#满
                        continue#跳
                选中=项#命中
                break#停
            if 选中 is None:#无合格
                return#停
            自身._排队.remove(选中)#出队
            选中.状态='running'#运行
            是后台=选中.优先级=='background'#后台旗
            预留=自身._预留字节数(选中)#预留
            自身._运行中+=1#并发
            if 是后台:#后台
                自身._后台数+=1#计数
            自身._源字节+=预留#占容量
            def 跑任务(任务=选中,预留字节=预留,后台=是后台):
                """工作线程：执行并回收名额。"""
                try:
                    自身._执行任务(任务,预留字节)#主体
                except BaseException as 错误:
                    with 自身._锁:#互斥
                        自身._失败结算(任务,错误)#失败
                finally:
                    with 自身._锁:#互斥
                        自身._运行中-=1#回收
                        if 后台:#后台
                            自身._后台数-=1#回收
                        自身._源字节-=预留字节#回收
                        任务.状态='finished'#结束
                        自身._任务集.discard(任务)#去集
                        自身._线程表.discard(threading.current_thread())#去线程
                        自身._抽干()#继续
            线程=threading.Thread(target=跑任务,daemon=True)#工作线程
            自身._线程表.add(线程)#登记
            线程.start()#启动

    def _执行任务(自身,任务,预留):
        """读源、按摘要去重或转换，再结算读取方。"""
        信号=任务.控制器.信号#任务信号
        若已中止则抛出(信号)#入口
        输入=任务.请求['source']['read'](信号,预留)#延迟读
        若已中止则抛出(信号)#读后
        if 输入['version']!=任务.请求['source']['version']:#版本变
            raise office转pdf错误('source-changed','The source changed while waiting for conversion.')#拒绝
        if len(输入['bytes'])>预留:#超预留
            raise office转pdf错误('input-too-large','The source exceeds its reserved read capacity.')#拒绝
        摘要=hashlib.sha256()#SHA-256
        摘要.update(任务.请求['extension'].encode('utf-8'))#扩展名
        摘要.update(b'\0')#分隔
        摘要.update(输入['bytes'])#内容
        键=office转pdf键(str(自身._世代)+':'+摘要.hexdigest())#内容键
        with 自身._锁:#互斥
            缓存=自身._就绪.get(键)#内容命中
            if 缓存 is not None:#命中
                自身._就绪.pop(键,None)#LRU
                自身._就绪[键]=缓存#重插
                自身._结算(任务,缓存)#交付
                return
            已有=自身._摘要表.get(键)#在途同摘要
            if 已有 is not None and not 已中止(已有.控制器.信号):#可并入
                if 任务.优先级=='foreground':#提权
                    已有.优先级='foreground'#前台
                for 读 in list(任务.读取方集):#迁移读取方
                    读.任务=已有#改挂
                    已有.读取方集.add(读)#并入
                任务.读取方集.clear()#清空
                for 源 in list(任务.源集):#迁移源
                    已有.源集.add(源)#并入
                    自身._源表[源]=已有#改指
                任务.源集.clear()#清空
                return#由已有结算
            自身._摘要表[键]=任务#登记在途
        try:
            已转换=自身._转换函数(输入['bytes'],任务.请求['extension'],信号)#引擎
            若已中止则抛出(信号)#转换后
            结果={'pdf':已转换['pdf'],'missingFonts':list(已转换['missingFonts']),'cacheKey':键,'generation':自身._世代}#完整结果
            with 自身._锁:#互斥
                自身._保留(结果)#缓存
                自身._结算(任务,结果)#交付
        finally:
            with 自身._锁:#互斥
                if 自身._摘要表.get(键) is 任务:#仍是本任务
                    自身._摘要表.pop(键,None)#去表

    def _结算(自身,任务,结果):
        """交付全部读取方并维护源别名。"""
        for 源 in list(任务.源集):#清源索引表
            自身._源表.pop(源,None)#去掉
        if 结果['cacheKey'] in 自身._就绪:#已保留
            for 源 in list(任务.源集):#任务源集仍在
                自身._别名.pop(源,None)#重挂
                自身._别名[源]=结果['cacheKey']#别名
                while len(自身._别名)>自身._配置['maxSourceEntries']:#超别名上限
                    自身._别名.pop(next(iter(自身._别名)))#删最旧
        for 读 in list(任务.读取方集):#交付
            自身._释放读取方(读)#释放名额
            if not 读.结局.done():#未结算
                读.结局.set_result(自身._复制结果(结果))#兑现

    def _保留(自身,结果):
        """按条数与字节 LRU 保留成功 PDF。"""
        if len(结果['pdf'])>自身._配置['maxCachedBytes']:#单份过大
            return#不留
        while len(自身._就绪)>=自身._配置['maxCachedEntries'] or 自身._已缓存字节+len(结果['pdf'])>自身._配置['maxCachedBytes']:#超限
            if len(自身._就绪)==0:#空
                break#停
            旧键=next(iter(自身._就绪))#最旧
            最旧=自身._就绪.pop(旧键)#取出
            自身._已缓存字节-=len(最旧['pdf'])#减字节
            for 源,摘要键 in list(自身._别名.items()):#清别名
                if 摘要键==旧键:#命中
                    自身._别名.pop(源,None)#删
        自身._就绪[结果['cacheKey']]=结果#插入
        自身._已缓存字节+=len(结果['pdf'])#加字节
