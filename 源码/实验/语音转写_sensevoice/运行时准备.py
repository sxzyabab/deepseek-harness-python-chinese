import hashlib,json,os,platform,sys,uuid
import requests
from ...工具.超时 import 若已中止则抛出,已中止,取超时
from .下载错误 import 分类下载失败,语音下载错误
from .模型源列表 import 排序模型源

__all__=['检查运行时','下载资产','准备运行时']

支持平台=('darwin-arm64','darwin-x64','linux-arm64','linux-x64','win32-x64')

def 平台键():
    """当前宿主平台。"""
    系统=sys.platform
    架构=platform.machine().lower()
    if 架构 in ('amd64','x86_64'):
        架构='x64'
    elif 架构 in ('aarch64','arm64'):
        架构='arm64'
    return 系统+'-'+架构

def 匹配资产(路径,资产,信号):
    """大小与 sha256 都对才算命中。"""
    若已中止则抛出(信号)
    if not os.path.isfile(路径):
        if not os.path.exists(路径):
            return False
        raise RuntimeError('Speech asset is not a regular file: '+路径)
    if os.path.getsize(路径)!=资产['bytes']:
        return False
    摘要=hashlib.sha256()
    with open(路径,'rb') as 文件:
        while True:
            若已中止则抛出(信号)
            块=文件.read(1024*1024)
            if not 块:
                break
            摘要.update(块)
    return 摘要.hexdigest()==资产['sha256']

def 解析运行时(配置):
    """钉死平台与锁文件路径。"""
    键=平台键()
    if 键 not in 支持平台:
        raise RuntimeError('Local speech is unavailable for '+键)
    锁路径=os.path.join(os.path.dirname(__file__),'运行时','静态资产.json')
    with open(锁路径,'r',encoding='utf-8') as 文件:
        锁=json.load(文件)
    模型根=配置['modelDirectory'] or os.path.join(配置['dataRoot'],'models','sensevoice-onnx')
    路径={
        'model':os.path.join(模型根,锁['models'][配置['precision']]['name']),
        'tokens':os.path.join(模型根,锁['tokens']['name']),
        'vad':配置['vadModelPath'] or os.path.join(配置['dataRoot'],'models','silero',锁['vad']['name']),
        'worker':os.path.join(os.path.dirname(__file__),'工作者.py'),
    }
    return {'lock':锁,'modelRoot':模型根,'paths':路径}

def 校验运行时(配置,路径,锁,信号):
    """托管文件必须对得上钉死的大小与哈希。"""
    若已中止则抛出(信号)
    for 项 in (路径['model'],路径['tokens'],路径['vad']):
        if not os.path.exists(项):
            return False
    待核=[]
    if 配置['modelDirectory'] is None:
        待核.append((路径['model'],锁['models'][配置['precision']]))
        待核.append((路径['tokens'],锁['tokens']))
    if 配置['vadModelPath'] is None:
        待核.append((路径['vad'],锁['vad']))
    for 文件路径,资产 in 待核:
        if not 匹配资产(文件路径,资产,信号):
            return False
    若已中止则抛出(信号)
    return True

def 检查运行时(配置,信号):
    """只检查缓存，不下载、不写、不启动工作者。"""
    解析=解析运行时(配置)
    if 校验运行时(配置,解析['paths'],解析['lock'],信号):
        return 解析['paths']
    return None

def 下载资产(资产,根,信号,报告=None):
    """下到唯一部分文件，校验后原子发布。"""
    if 报告 is None:
        def 报告(状态):
            """空进度。"""
            return
    若已中止则抛出(信号)
    目标=os.path.join(根,资产['name'])
    部分=目标+'.'+uuid.uuid4().hex+'.part'
    源=requests.compat.urlparse(资产['url']).scheme+'://'+requests.compat.urlparse(资产['url']).netloc
    try:
        os.makedirs(根,exist_ok=True)
        if 匹配资产(目标,资产,信号):
            return 目标
        try:
            应答=requests.get(资产['url'],stream=True,timeout=60)
            源=应答.url.split('/')[0]+'//'+应答.url.split('/')[2] if '://' in 应答.url else 源
            if not 应答.ok:
                raise 语音下载错误({'resource':资产['name'],'source':源,'reason':'http','status':应答.status_code})
            摘要=hashlib.sha256()
            完成字节=0
            def 发布():
                """下载进度。"""
                报告({'phase':'downloading','resource':资产['name'],'completedBytes':完成字节,'totalBytes':资产['bytes']})
            发布()
            with open(部分,'xb') as 文件:
                os.chmod(部分,0o600)
                for 块 in 应答.iter_content(65536):
                    若已中止则抛出(信号)
                    if not 块:
                        continue
                    完成字节+=len(块)
                    if 完成字节>资产['bytes']:
                        raise 语音下载错误({'resource':资产['name'],'source':源,'reason':'integrity'})
                    摘要.update(块)
                    文件.write(块)
                    发布()
            if 完成字节!=资产['bytes'] or 摘要.hexdigest()!=资产['sha256']:
                raise 语音下载错误({'resource':资产['name'],'source':源,'reason':'integrity'})
            若已中止则抛出(信号)
            os.replace(部分,目标)
            return 目标
        finally:
            if os.path.exists(部分):
                os.remove(部分)
    except Exception as 错误:
        超时=取超时(信号) is not None
        if (已中止(信号) and not 超时) or isinstance(错误,语音下载错误):
            raise 错误
        分类={'reason':'timeout'} if 超时 else 分类下载失败(错误)
        raise 语音下载错误({'resource':资产['name'],'source':源,**分类},错误)

def 准备运行时(_上下文,配置,信号,报告=None):
    """解析捆绑运行时并按需准备已校验 ONNX。"""
    if 报告 is None:
        def 报告(状态):
            """空进度。"""
            return
    解析=解析运行时(配置)
    锁=解析['lock']
    模型根=解析['modelRoot']
    路径=解析['paths']
    import time
    def 下载(资产,根,步骤):
        """缺失才下。"""
        if 匹配资产(os.path.join(根,资产['name']),资产,信号):
            return
        源表=配置['modelOrigins'] if 配置['modelOrigin'] is None else [配置['modelOrigin']]
        网址表=排序模型源(资产['url'],源表,配置['modelProbeTimeoutMs'],信号)
        下标=0
        while 下标<len(网址表):
            try:
                def 带步(状态,步=步骤):
                    """叠步骤。"""
                    报告({**状态,'step':步})
                下载资产({**资产,'url':网址表[下标]},根,信号,带步)
                return
            except Exception as 错误:
                最后=下标==len(网址表)-1
                if 已中止(信号) or not isinstance(错误,语音下载错误) or 错误.download['reason'] in ('storage','unknown') or 最后:
                    raise 错误
            下标+=1
    if 配置['modelDirectory'] is None:
        报告({'phase':'checking','step':'model','startedAt':int(time.time()*1000)})
        下载(锁['models'][配置['precision']],模型根,'model')
        下载(锁['tokens'],模型根,'model')
    if 配置['vadModelPath'] is None:
        报告({'phase':'checking','step':'vad','startedAt':int(time.time()*1000)})
        下载(锁['vad'],os.path.join(配置['dataRoot'],'models','silero'),'vad')
    报告({'phase':'checking','step':'verify','startedAt':int(time.time()*1000)})
    if not 校验运行时(配置,路径,锁,信号):
        raise RuntimeError('Speech model verification failed: missing or corrupted model files')
    return 路径
