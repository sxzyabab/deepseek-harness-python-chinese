import threading
from urllib.parse import urljoin,urlparse
import requests
from ...工具.超时 import 截止,若已中止则抛出,已中止

__all__=['排序模型源']

def 探测(网址,信号,结果,锁):
    """一次 HEAD。"""
    try:
        若已中止则抛出(信号)
        应答=requests.head(网址,allow_redirects=True,timeout=30)
        if not 应答.ok:
            raise RuntimeError('Model source probe returned HTTP '+str(应答.status_code))
        with 锁:
            if 结果[0] is None and not 已中止(信号):
                结果[0]=网址
    except Exception:
        return

def 排序模型源(资产网址,源列表,超时毫秒,信号):
    """先成功的 HEAD 优先，其余保留作下载回退。"""
    若已中止则抛出(信号)
    路径=urlparse(资产网址).path
    网址表=[]
    已见=set()
    for 源 in 源列表:
        项=urljoin(源.rstrip('/')+'/',路径.lstrip('/'))
        if 项 not in 已见:
            已见.add(项)
            网址表.append(项)
    if len(网址表)==1:
        return 网址表
    句柄=截止(信号,超时毫秒,'SPEECH_SOURCE_PROBE_TIMEOUT')
    首选=[None]
    锁=threading.Lock()
    线程=[]
    for 网址 in 网址表:
        线=threading.Thread(target=探测,args=(网址,句柄.信号,首选,锁),daemon=True)
        线程.append(线)
        线.start()
    for 线 in 线程:
        线.join()
    句柄.释放()
    若已中止则抛出(信号)
    if 首选[0] is None:
        return 网址表
    return [首选[0]]+[项 for 项 in 网址表 if 项!=首选[0]]
