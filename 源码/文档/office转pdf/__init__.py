"""Host LibreOffice kit 提供方：可复用转换器与私有磁盘输入输出。

公开面仅中文名。包名 `@deepseek-ai/dsh-office-to-pdf`、服务键 `officeToPdf`、
Remote 方法名 `render` / `generation` 与配置键保持英文。Cordis 槽 Config/default 不入 `__all__`。
"""
import base64,json,os,shutil,tempfile,threading,uuid#线路编码、JSON、路径、清理、临时目录、远程请求、世代
from ...依赖.schemastery import 正整数字段,自然数字段,字符串字段,列表字段#配置字段
from ...依赖.libreoffice_kit import 创建转换器#kit 占位
from ...依赖.工具 import 聚合错误#拆除聚合
from ...工具.超时 import 中止控制器,已中止,若已中止则抛出,合成信号#中止
from ...typert.协议 import 远程服务,远程 as _远程#Remote 基类
from ...api.工作区文件.类型 import 远程错误#Remote 错误
from .异常 import office转pdf错误#分类失败
from .标识构造 import office转pdf世代,office源键,office转pdf键#身份
from .类型 import (#类型面
    office扩展名表,
    office转pdf优先级表,
    office转pdf错误码表,
    已渲染文档字节字段,
)
from .输出 import 读取pdf#有界 PDF 读
from .队列 import 转换队列#准入队列

__all__=[#仅中文公开名
    '包名','配置','office转pdf','office转pdf错误',
    'office源键','office转pdf世代','office转pdf键',
    'office扩展名表','office转pdf优先级表','office转pdf错误码表',
    '已渲染文档字节字段','读取pdf','转换队列',
]#公开面结束

#常量
包名='@deepseek-ai/dsh-office-to-pdf'#npm 包名
安全整数上限=9007199254740991#JSON 入口安全整数

配置={#部署默认
    'maxConcurrentConversions':正整数字段(默认值=2,最小=1,最大=安全整数上限),#最大并发转换
    'maxQueuedJobs':正整数字段(默认值=8,最小=1,最大=安全整数上限),#最大排队元数据
    'maxReaders':正整数字段(默认值=32,最小=1,最大=安全整数上限),#最大读取方
    'maxSourceBytes':正整数字段(默认值=104857600,最小=1,最大=安全整数上限),#最大源预留字节
    'maxBackgroundConversions':自然数字段(默认值=1,最小=0,最大=安全整数上限),#最大后台并发
    'maxCachedEntries':正整数字段(默认值=8,最小=1,最大=安全整数上限),#最大缓存条数
    'maxCachedBytes':正整数字段(默认值=134217728,最小=1,最大=安全整数上限),#最大缓存字节
    'maxSourceEntries':正整数字段(默认值=64,最小=1,最大=安全整数上限),#最大源别名
    'timeoutMs':正整数字段(默认值=60000,最小=1,最大=2147483647),#转换期限毫秒
    'maxInputBytes':正整数字段(默认值=50*1024*1024,最小=1,最大=安全整数上限-1),#最大输入
    'maxOutputBytes':正整数字段(默认值=100*1024*1024,最小=1,最大=安全整数上限-1),#最大输出
    'maxImageResolution':正整数字段(默认值=192,最小=1,最大=2147483647),#光栅 DPI
    'maxArchiveEntries':正整数字段(默认值=10000,最小=1,最大=安全整数上限),#OOXML 条目上限
    'maxUncompressedBytes':正整数字段(默认值=250*1024*1024,最小=1,最大=安全整数上限),#未压缩上限
    'fontDirectories':列表字段(字符串字段(最小长度=1),默认值=None),#绝对字体根，省略用 kit 默认
    'fontFallbacks':列表字段(列表字段(字符串字段(格式=r'.*\S.*'),最小数量=2),默认值=None),#含非空白的字体族名组
    'maxFontFiles':正整数字段(默认值=20000,最小=1,最大=安全整数上限),#字体文件数
    'maxFontFileBytes':正整数字段(默认值=256*1024*1024,最小=1,最大=安全整数上限),#单字体文件字节
    'maxLoadedFontBytes':正整数字段(默认值=512*1024*1024,最小=1,最大=安全整数上限),#加载字体字节
}#配置结束

class 转换槽:
    """一个并发槽：忙闲与可选转换器实例。"""
    def __init__(自身):
        """空闲槽。"""
        自身.忙碌=False#忙闲
        自身.转换器=None#kit 转换器

class office转pdf(远程服务):
    """提供方寿命内拥有全部转换器、排队调用与临时文件。"""
    Config=配置#静态配置模式
    def __init__(自身,上下文,配置值):
        """用宿主上下文与已解析限额构造。"""
        super().__init__(上下文,'officeToPdf')#服务键
        自身.ctx=上下文#上下文
        自身._配置=配置值#限额
        字体目录=配置值['fontDirectories'] if 'fontDirectories' in 配置值 else None#可选
        if 字体目录 is not None:#有目录
            for 路径 in 字体目录:#逐条
                if not os.path.isabs(路径):#非绝对
                    raise ValueError('fontDirectories must contain absolute paths.')#拒绝
        if 配置值['maxSourceBytes']<配置值['maxInputBytes']:#容量不足
            raise ValueError('maxSourceBytes must be at least maxInputBytes.')#拒绝
        自身.世代=office转pdf世代(str(uuid.uuid4()))#提供方世代
        自身._远程寿命=中止控制器()#Remote 寿命
        自身._远程请求=set()#在途 Remote 结局
        自身._槽表=[]#转换槽
        选项={'timeoutMs':配置值['timeoutMs'],'maxInputBytes':配置值['maxInputBytes'],'maxOutputBytes':配置值['maxOutputBytes'],
            'maxImageResolution':配置值['maxImageResolution'],'maxArchiveEntries':配置值['maxArchiveEntries'],
            'maxUncompressedBytes':配置值['maxUncompressedBytes'],'maxFontFiles':配置值['maxFontFiles'],
            'maxFontFileBytes':配置值['maxFontFileBytes'],'maxLoadedFontBytes':配置值['maxLoadedFontBytes']}#kit 选项
        if 字体目录 is not None:#有字体目录
            选项['fontDirectories']=字体目录#带上
        字体回退=配置值['fontFallbacks'] if 'fontFallbacks' in 配置值 else None#可选
        if 字体回退 is not None:#有回退
            选项['fontFallbacks']=字体回退#带上
        自身._选项=选项#保存
        def 转换字节入口(字节,扩展名,信号):
            """交给实例转换字节。"""
            return 自身._转换字节(字节,扩展名,信号)#委托
        自身._队列=转换队列(配置值,自身.世代,转换字节入口)#准入队列
        def 登记拆除():
            """纤程拆除时清理队列、Remote 与转换器。"""
            def 拆除():
                """同步拆除。"""
                自身._远程寿命.中止()#取消 Remote
                自身._队列.拆除()#排空队列
                for 请求结局 in list(自身._远程请求):#等 Remote
                    try:
                        请求结局.等待()#结算
                    except BaseException:
                        pass#拆除不等待业务成功
                失败列表=[]#拆除失败
                for 槽 in 自身._槽表:#逐槽
                    转换器=槽.转换器#实例
                    if 转换器 is None:#无
                        continue#跳
                    try:
                        转换器.拆除()#清理
                    except BaseException as 错误:
                        失败列表.append(错误)#记下
                if len(失败列表)>0:#有失败
                    raise 聚合错误(失败列表,'LibreOffice converter disposal failed.')#聚合
            return 拆除#拆除器
        上下文.副作用(登记拆除,'officeToPdf.dispose()')#登记

    def 转换(自身,请求,信号=None):
        """转换 Office 字节；不改源、不写 Session 事件。阻塞至结果。"""
        return 自身._队列.读取(请求,信号)#委托队列

    @_远程
    def render(自身,工作区文件作用域,路径,优先级,信号):
        """Remote：经 Session 文件系统授权读并转换一个 Office 文件。"""
        上游=合成信号(信号,自身._远程寿命.信号)#融合取消
        箱={'结果':None,'错误':None}#结算
        完成=threading.Event()#完成旗
        def 跑():
            """工作线程执行渲染。"""
            try:
                箱['结果']=自身._渲染文件(工作区文件作用域,路径,优先级,上游)#渲染
            except BaseException as 错误:
                箱['错误']=错误#记下
            finally:
                完成.set()#广播
        class 远程结局:
            """只留等待。"""
            def 等待(自):
                """阻塞至结束。"""
                完成.wait()#等
                if 箱['错误'] is not None:#失败
                    raise 箱['错误']#抛
                return 箱['结果']#成功
        结局=远程结局()#句柄
        自身._远程请求.add(结局)#登记
        try:
            threading.Thread(target=跑,daemon=True).start()#启动
            return 结局.等待()#阻塞
        finally:
            自身._远程请求.discard(结局)#去表

    @_远程('generation')
    def 获取世代(自身,信号):
        """Remote 导出名 generation：返回当前提供方世代。"""
        若已中止则抛出(信号)#中止
        return 自身.世代#世代

    def _渲染文件(自身,作用域,路径,优先级,信号):
        """授权、读源并转换；失败映射为 Remote 错误。"""
        try:
            若已中止则抛出(信号)#入口
            扩展名=os.path.splitext(路径)[1][1:].lower()#扩展名
            if 扩展名 not in office扩展名表:#不支持
                raise office转pdf错误('unsupported-format','The path must end in doc, docx, xls, xlsx, ppt, or pptx.')#拒绝
            文件=自身.ctx.获取服务('workspaceFiles')#可选
            文件系统=自身.ctx.获取服务('fs')#可选
            if 文件 is None or 文件系统 is None:#缺服务
                raise office转pdf错误('unavailable','Office file rendering requires workspaceFiles and fs.')#拒绝
            已授权=文件.readBytes(作用域,路径,{'offset':0,'length':1},信号)#授权探测
            源状态=文件.stat(作用域,路径,信号)#stat
            def 断言未变(当前):
                """路径或版本变化则拒绝。"""
                if 当前['absolutePath']!=源状态['absolutePath'] or 当前['version']!=源状态['version']:#变了
                    raise office转pdf错误('source-changed','The source changed.')#拒绝
            断言未变(已授权)#与探测一致
            若已中止则抛出(信号)#转换前
            def 延迟读(上游,最大字节):
                """准入后有界读源。"""
                目标=文件系统.解析(源状态['absolutePath'],{'signal':上游})#解析
                信息=文件系统.状态(目标,上游)#状态
                if 信息 is None or 信息['type']!='file':#非文件
                    raise office转pdf错误('source-changed','The source changed.')#拒绝
                断言未变({'absolutePath':文件系统.进程路径(目标),'version':信息['version']})#未变
                try:
                    字节=文件系统.读字节(目标,上游,最大字节)#读
                except BaseException as 原因:
                    if getattr(原因,'code',None)=='FS_TOO_LARGE':#过大（按 code 字段识别）
                        断言未变(文件.stat(作用域,路径,上游))#再确认
                        raise office转pdf错误('input-too-large','The source exceeds the reserved byte capacity.',原因)#映射
                    raise#原样
                若已中止则抛出(上游)#读后
                断言未变(文件.stat(作用域,路径,上游))#再确认
                return {'bytes':字节,'version':源状态['version']}#输入
            源键文本=json.dumps([作用域['sessionId'],作用域['workspaceRoot'],源状态['absolutePath']],ensure_ascii=False,separators=(',',':'))#源键
            源描述={'key':office源键(源键文本),'version':源状态['version'],'read':延迟读}#源
            if 'bytes' in 源状态 and 源状态['bytes'] is not None:#已知大小
                源描述['bytes']=源状态['bytes']#带上
            结果=自身.转换({'extension':扩展名,'priority':优先级,'source':源描述},信号)#转换
            若已中止则抛出(信号)#返回前
            return {'absolutePath':源状态['absolutePath'],'version':源状态['version'],'offset':0,'eof':True,
                'bytes':len(结果['pdf']),'data':base64.b64encode(结果['pdf']).decode('ascii'),
                'missingFonts':结果['missingFonts'],'generation':结果['generation']}#线路结果
        except BaseException as 原因:
            if 已中止(信号):#取消
                raise 远程错误('gateway/cancelled','The document preview was cancelled.',{},原因)#取消
            if isinstance(原因,office转pdf错误):#分类失败
                raise 远程错误('document-render/failed','Office conversion failed.',{'reason':原因.code},原因)#映射
            raise#原样

    def _转换字节(自身,字节,扩展名,信号):
        """在槽内写入临时目录、调用 kit、读回 PDF。"""
        若已中止则抛出(信号)#入口
        槽=None#选槽
        for 候选 in 自身._槽表:#找空闲
            if not 候选.忙碌:#空闲
                槽=候选#选用
                break#停
        if 槽 is None:#无空闲
            槽=转换槽()#新建
            自身._槽表.append(槽)#登记
        槽.忙碌=True#占用
        目录=None#临时目录
        try:
            if 槽.转换器 is None:#按需创建
                try:
                    槽.转换器=创建转换器(自身._选项)#kit
                except BaseException:
                    槽.转换器=None#失败清空
                    raise#抛出
            转换器=槽.转换器#实例
            若已中止则抛出(信号)#创建后
            目录=tempfile.mkdtemp(prefix='dsh-office-to-pdf-')#私有目录
            输入路径=os.path.join(目录,'source.'+扩展名)#输入
            输出路径=os.path.join(目录,'converted.pdf')#输出
            句柄=os.open(输入路径,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)#独占创建
            try:
                os.write(句柄,字节 if isinstance(字节,(bytes,bytearray)) else bytes(字节))#写入
            finally:
                os.close(句柄)#关闭
            若已中止则抛出(信号)#写后
            渲染结果=转换器.渲染({'inputPath':输入路径,'outputPath':输出路径},信号)#kit 渲染
            若已中止则抛出(信号)#渲染后
            try:
                pdf=读取pdf(输出路径,自身._配置['maxOutputBytes'],信号)#读 PDF
            except office转pdf错误:
                raise#原样
            except BaseException as 原因:
                raise office转pdf错误('invalid-output','The converter PDF could not be read.',原因)#映射
            若已中止则抛出(信号)#读后
            return {'pdf':pdf,'missingFonts':list(渲染结果['missingFonts'])}#结果为 dict
        except BaseException as 原因:
            若已中止则抛出(信号)#中止优先
            if isinstance(原因,office转pdf错误):#已分类
                raise#原样
            码=原因.code if hasattr(原因,'code') else None#引擎码
            if 码 in ('input-too-large','output-too-large','invalid-document','unsupported-format','invalid-output','timeout','unavailable'):#已知
                raise office转pdf错误(码,'LibreOffice conversion failed.',原因)#映射
            raise office转pdf错误('failed','LibreOffice conversion failed.',原因)#其余
        finally:
            try:
                if 目录 is not None:#有临时
                    shutil.rmtree(目录,ignore_errors=True)#清理
            finally:
                槽.忙碌=False#释放

#框架槽
Config=配置#Cordis 配置
default=office转pdf#Cordis 默认导出
