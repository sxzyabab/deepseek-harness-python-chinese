"""LibreOffice kit 提供方：可复用转换器与私有磁盘输入输出。

公开面仅中文名。服务键 officeToPdf、远程方法名 render / generation 与配置键保持英文线协议。
"""
import base64,json,os,shutil,tempfile,threading,uuid
from ...依赖.schemastery import 正整数字段,自然数字段,字符串字段,列表字段
from ...依赖.libreoffice_kit import 创建转换器
from ...依赖.工具 import 聚合错误
from ...工具.超时 import 中止控制器,已中止,若已中止则抛出,合成信号
from ...typert.协议 import 远程服务,远程 as _远程
from ...api.工作区文件.类型 import 远程错误
from .异常 import office转pdf错误
from .标识构造 import office转pdf世代,office源键,office转pdf键
from .类型 import (
    office扩展名表,
    office转pdf优先级表,
    office转pdf错误码表,
    已渲染文档字节字段,
)
from .输出 import 读取pdf
from .队列 import 转换队列

__all__=[
    '包名','配置','office转pdf','office转pdf错误',
    'office源键','office转pdf世代','office转pdf键',
    'office扩展名表','office转pdf优先级表','office转pdf错误码表',
    '已渲染文档字节字段','读取pdf','转换队列',
]

包名='@deepseek-ai/dsh-office-to-pdf'
安全整数上限=9007199254740991#JSON 入口安全整数

配置={
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
}

class 转换槽:
    """一个并发槽：忙闲与可选转换器实例。"""
    def __init__(自身):
        """空闲槽。"""
        自身.忙碌=False
        自身.转换器=None

class office转pdf(远程服务):
    """提供方寿命内拥有全部转换器、排队调用与临时文件。"""
    Config=配置
    def __init__(自身,上下文,配置值):
        """用宿主上下文与已解析限额构造。"""
        super().__init__(上下文,'officeToPdf')
        自身.ctx=上下文
        自身._配置=配置值
        字体目录=配置值['fontDirectories'] if 'fontDirectories' in 配置值 else None
        if 字体目录 is not None:
            for 路径 in 字体目录:
                if not os.path.isabs(路径):
                    raise ValueError('fontDirectories must contain absolute paths.')
        if 配置值['maxSourceBytes']<配置值['maxInputBytes']:
            raise ValueError('maxSourceBytes must be at least maxInputBytes.')
        自身.世代=office转pdf世代(str(uuid.uuid4()))
        自身._远程寿命=中止控制器()
        自身._远程请求=set()
        自身._槽表=[]
        选项={'timeoutMs':配置值['timeoutMs'],'maxInputBytes':配置值['maxInputBytes'],'maxOutputBytes':配置值['maxOutputBytes'],
            'maxImageResolution':配置值['maxImageResolution'],'maxArchiveEntries':配置值['maxArchiveEntries'],
            'maxUncompressedBytes':配置值['maxUncompressedBytes'],'maxFontFiles':配置值['maxFontFiles'],
            'maxFontFileBytes':配置值['maxFontFileBytes'],'maxLoadedFontBytes':配置值['maxLoadedFontBytes']}
        if 字体目录 is not None:
            选项['fontDirectories']=字体目录
        字体回退=配置值['fontFallbacks'] if 'fontFallbacks' in 配置值 else None
        if 字体回退 is not None:
            选项['fontFallbacks']=字体回退
        自身._选项=选项
        def 转换字节入口(字节,扩展名,信号):
            """交给实例转换字节。"""
            return 自身._转换字节(字节,扩展名,信号)
        自身._队列=转换队列(配置值,自身.世代,转换字节入口)
        def 登记拆除():
            """纤程拆除时清理队列、Remote 与转换器。"""
            def 拆除():
                """同步拆除。"""
                自身._远程寿命.中止()
                自身._队列.拆除()
                for 请求结局 in list(自身._远程请求):
                    try:
                        请求结局.等待()
                    except BaseException:
                        pass#拆除不等待业务成功
                失败列表=[]
                for 槽 in 自身._槽表:
                    转换器=槽.转换器
                    if 转换器 is None:
                        continue
                    try:
                        转换器.拆除()
                    except BaseException as 错误:
                        失败列表.append(错误)
                if len(失败列表)>0:
                    raise 聚合错误(失败列表,'LibreOffice converter disposal failed.')
            return 拆除
        上下文.副作用(登记拆除,'officeToPdf.dispose()')

    def 转换(自身,请求,信号=None):
        """转换 Office 字节；不改源、不写 Session 事件。阻塞至结果。"""
        return 自身._队列.读取(请求,信号)

    @_远程
    def render(自身,工作区文件作用域,路径,优先级,信号):
        """Remote：经 Session 文件系统授权读并转换一个 Office 文件。"""
        上游=合成信号(信号,自身._远程寿命.信号)
        箱={'结果':None,'错误':None}
        完成=threading.Event()
        def 在线程执行():
            """工作线程执行渲染。"""
            try:
                箱['结果']=自身._渲染文件(工作区文件作用域,路径,优先级,上游)
            except BaseException as 错误:
                箱['错误']=错误
            finally:
                完成.set()
        class 远程结局:
            """只留等待。"""
            def 等待(自):
                """阻塞至结束。"""
                完成.wait()
                if 箱['错误'] is not None:
                    raise 箱['错误']
                return 箱['结果']
        结局=远程结局()
        自身._远程请求.add(结局)
        try:
            threading.Thread(target=在线程执行,daemon=True).start()
            return 结局.等待()
        finally:
            自身._远程请求.discard(结局)

    @_远程('generation')
    def 获取世代(自身,信号):
        """Remote 导出名 generation：返回当前提供方世代。"""
        若已中止则抛出(信号)
        return 自身.世代

    def _渲染文件(自身,作用域,路径,优先级,信号):
        """授权、读源并转换；失败映射为 Remote 错误。"""
        try:
            若已中止则抛出(信号)
            扩展名=os.path.splitext(路径)[1][1:].lower()
            if 扩展名 not in office扩展名表:
                raise office转pdf错误('unsupported-format','The path must end in doc, docx, xls, xlsx, ppt, or pptx.')
            文件=自身.ctx.获取服务('workspaceFiles')
            文件系统=自身.ctx.获取服务('fs')
            if 文件 is None or 文件系统 is None:
                raise office转pdf错误('unavailable','Office file rendering requires workspaceFiles and fs.')
            已授权=文件.readBytes(作用域,路径,{'offset':0,'length':1},信号)
            源状态=文件.stat(作用域,路径,信号)
            def 断言未变(当前):
                """路径或版本变化则拒绝。"""
                if 当前['absolutePath']!=源状态['absolutePath'] or 当前['version']!=源状态['version']:
                    raise office转pdf错误('source-changed','The source changed.')
            断言未变(已授权)
            若已中止则抛出(信号)
            def 延迟读(上游,最大字节):
                """准入后有界读源。"""
                目标=文件系统.解析(源状态['absolutePath'],{'signal':上游})
                信息=文件系统.状态(目标,上游)
                if 信息 is None or 信息['type']!='file':
                    raise office转pdf错误('source-changed','The source changed.')
                断言未变({'absolutePath':文件系统.进程路径(目标),'version':信息['version']})
                try:
                    字节=文件系统.读字节(目标,上游,最大字节)
                except BaseException as 原因:
                    if getattr(原因,'code',None)=='FS_TOO_LARGE':#按 code 字段识别过大
                        断言未变(文件.stat(作用域,路径,上游))
                        raise office转pdf错误('input-too-large','The source exceeds the reserved byte capacity.',原因)
                    raise
                若已中止则抛出(上游)
                断言未变(文件.stat(作用域,路径,上游))
                return {'bytes':字节,'version':源状态['version']}
            源键文本=json.dumps([作用域['sessionId'],作用域['workspaceRoot'],源状态['absolutePath']],ensure_ascii=False,separators=(',',':'))
            源描述={'key':office源键(源键文本),'version':源状态['version'],'read':延迟读}
            if 'bytes' in 源状态 and 源状态['bytes'] is not None:
                源描述['bytes']=源状态['bytes']
            结果=自身.转换({'extension':扩展名,'priority':优先级,'source':源描述},信号)
            若已中止则抛出(信号)
            return {'absolutePath':源状态['absolutePath'],'version':源状态['version'],'offset':0,'eof':True,
                'bytes':len(结果['pdf']),'data':base64.b64encode(结果['pdf']).decode('ascii'),
                'missingFonts':结果['missingFonts'],'generation':结果['generation']}
        except BaseException as 原因:
            if 已中止(信号):
                raise 远程错误('gateway/cancelled','The document preview was cancelled.',{},原因)
            if isinstance(原因,office转pdf错误):
                raise 远程错误('document-render/failed','Office conversion failed.',{'reason':原因.code},原因)
            raise

    def _转换字节(自身,字节,扩展名,信号):
        """在槽内写入临时目录、调用 kit、读回 PDF。"""
        若已中止则抛出(信号)
        槽=None
        for 候选 in 自身._槽表:
            if not 候选.忙碌:
                槽=候选
                break
        if 槽 is None:
            槽=转换槽()
            自身._槽表.append(槽)
        槽.忙碌=True
        目录=None
        try:
            if 槽.转换器 is None:
                try:
                    槽.转换器=创建转换器(自身._选项)
                except BaseException:
                    槽.转换器=None
                    raise
            转换器=槽.转换器
            若已中止则抛出(信号)
            目录=tempfile.mkdtemp(prefix='dsh-office-to-pdf-')
            输入路径=os.path.join(目录,'source.'+扩展名)
            输出路径=os.path.join(目录,'converted.pdf')
            句柄=os.open(输入路径,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            try:
                os.write(句柄,字节 if isinstance(字节,(bytes,bytearray)) else bytes(字节))
            finally:
                os.close(句柄)
            若已中止则抛出(信号)
            渲染结果=转换器.渲染({'inputPath':输入路径,'outputPath':输出路径},信号)
            若已中止则抛出(信号)
            try:
                pdf=读取pdf(输出路径,自身._配置['maxOutputBytes'],信号)
            except office转pdf错误:
                raise
            except BaseException as 原因:
                raise office转pdf错误('invalid-output','The converter PDF could not be read.',原因)
            若已中止则抛出(信号)
            return {'pdf':pdf,'missingFonts':list(渲染结果['missingFonts'])}
        except BaseException as 原因:
            若已中止则抛出(信号)
            if isinstance(原因,office转pdf错误):
                raise
            码=原因.code if hasattr(原因,'code') else None
            if 码 in ('input-too-large','output-too-large','invalid-document','unsupported-format','invalid-output','timeout','unavailable'):
                raise office转pdf错误(码,'LibreOffice conversion failed.',原因)
            raise office转pdf错误('failed','LibreOffice conversion failed.',原因)
        finally:
            try:
                if 目录 is not None:
                    shutil.rmtree(目录,ignore_errors=True)
            finally:
                槽.忙碌=False

Config=配置
default=office转pdf
