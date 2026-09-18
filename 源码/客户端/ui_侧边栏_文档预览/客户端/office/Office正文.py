"""Office 拥有源加载、转换失败与缺字体提示，环绕共享 PDF 视图。"""
from .字体提示 import 字体提示#缺字体提示

__all__=['Office正文']#仅中文公开名

def Office正文(属性):
    """加载一次 Office 修订并保留至标签关闭。属性为合成 props。"""
    标签信息=属性['useTabInfo']()#标签信息
    标签=标签信息['tab']#标签
    动作=属性['actions']#动作
    读=属性['read']#读
    保留标签=属性['retainTab']#保留
    描述失败=属性['describeFailure']#描述失败
    资源地址=属性['resourceAddress']#地址
    翻译=属性['t']#翻译
    内容=属性['content']#内容
    请求=内容 if 内容.get('kind')=='renderer' else None#渲染器请求
    if 请求 is None:#非渲染器
        return None#空
    修订=请求.get('revision')#修订
    持有=属性['useStore'](lambda 状态:状态['byTab'].get(标签['id']))#持有
    视图=持有 if 持有 is not None and 持有.get('revision')==修订 else None#匹配视图
    保留标签(标签['id'],标签.get('signal'))#保留
    if 视图 is not None and 视图.get('failure') is not None:#失败
        return {'kind':'office-failed','code':视图['failure']['code'],'message':视图['failure']['message'],'retry':翻译('retry')}#失败面
    if 视图 is None or 视图.get('file') is None:#加载中
        return {'kind':'office-loading','label':翻译('loading')}#加载
    文件=视图['file']#文件
    return {#成功面
        'kind':'office-body',
        'fontNotice':字体提示({'resourceAddress':资源地址,'sourceVersion':文件.get('version'),'fonts':文件.get('missingFonts',[]),'t':翻译}),
        'pdf':{'kind':'bytes','data':文件.get('data')},
    }#结束
