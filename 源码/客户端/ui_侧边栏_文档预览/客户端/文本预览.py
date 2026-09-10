"""文本预览的正文：文件内容，或未展示的原因。

对齐上游 `ui-sidebar-documentpreview/src/client/TextPreview.tsx`。公开面仅中文名。
无 React：正文为视图模型，产出结构树 dict。两处来源在此汇合：标准资源钩的元数据与本类型存储所持内容。
"""
from .失败行 import 失败行#失败行
from .远程过程调用 import 宿主文件#宿主文件
from .文档.注册表 import 匹配文档预览#匹配
from .文本 import 纯文本体标识#纯文本 id
from .文本.行 import 已载入页,末已载行#行辅助
from .加载指示器 import 加载指示器#加载

__all__=['文本预览','样式表']#仅中文公开名

样式表=''#样式见旁路 文本预览.module.css


def 文本预览(
    取标签信息,取资源,取存储,动作,
    加载页,重载页,加载全部,重载全部,
    取文档预览,渲染槽,翻译,
):
    """产出迄今所读内容及其控件结构，或进度行。"""
    标签信息=取标签信息()#标签信息
    标签=标签信息['tab']#标签
    导航=标签['navigation']#导航
    信号=标签['signal'] if 'signal' in 标签 else None#寿命
    元=取资源(标签['contentId'])#元数据快照
    可读=元.get('status')!='none'#可读
    文件=宿主文件(标签['contentId'])#会话文件
    状态=取存储(lambda 总:总['byTab'][标签['id']] if 标签['id'] in 总['byTab'] else None)#桶
    定义列表=取文档预览(lambda 值:值)#定义
    已匹配=匹配文档预览(定义列表,文件['path'])#匹配
    兜底=None#纯文本
    for 项 in 定义列表:#找兜底
        if 项.get('id')==纯文本体标识:#纯文本
            兜底=项#记下
            break#停
    候选=list(已匹配)+( [兜底] if 兜底 is not None else [] )#候选
    所选=None#所选
    if 状态 is not None and 'rendererId' in 状态:#有选择
        for 项 in 候选:#找
            if 项.get('id')==状态['rendererId']:#命中
                所选=项#记下
                break#停
    if 所选 is None and len(候选)>0:#自动
        所选=候选[0]#首个
    if 状态 is None or 所选 is None:#尚无
        if 元.get('status')=='none':#无资源
            return {'kind':'status','line':翻译('resourceUnavailable')}#不可用
        return {'kind':'status','loading':加载指示器(翻译('loading'))}#加载中
    模式=所选.get('loading')#模式
    当前=状态 if (状态.get('mode') if 'mode' in 状态 else 'text-pages')==模式 else None#当前桶
    页表=当前['pages'] if 当前 is not None and 'pages' in 当前 else {}#页
    已载=已载入页(页表)#有序
    已载至=末已载行(已载)#末行
    有内容=len(已载)>0 or (当前 is not None and 'complete' in 当前 and 当前['complete'] is not None)#有内容
    展示路径=(元['value']['absolutePath'] if 元.get('value') is not None and 'absolutePath' in 元['value'] else None)
    if 展示路径 is None and 当前 is not None and 'complete' in 当前 and 当前['complete'] is not None:
        展示路径=当前['complete'].get('absolutePath')
    if 展示路径 is None:
        展示路径=文件['path']
    参数=导航['params'] if 'params' in 导航 else None#参数
    行号=参数['line'] if 参数 is not None and 'line' in 参数 else None#行
    内容=None#文档内容
    if 模式=='bytes-complete':#完整字节
        if 当前 is not None and 'complete' in 当前 and 当前['complete'] is not None:
            内容={'kind':'bytes','data':当前['complete']['data']}#字节
    elif 当前 is not None and len(已载)>0:#文本页
        内容={#文本
            'kind':'text',
            'pages':已载,
            'text':'\n'.join(页['text'] for 页 in 已载 if 页['lines']>0),
            'eof':当前['eof'],
        }#结束
    观察版本=元['value']['version'] if 元.get('value') is not None and 'version' in 元['value'] else None
    已变更=(
        当前 is not None and 当前.get('version') is not None and 观察版本 is not None
        and 观察版本!=当前['version'] and 观察版本!=当前.get('observedVersion')
    )#变更
    return {#结构
        'kind':'text-preview',
        'url':标签['contentId'],
        'rendererId':所选['id'],
        'path':展示路径,
        'wrap':状态.get('wrap',True),
        'candidates':[{'id':项['id'],'title':项['title']()} for 项 in 候选],
        'selectedId':所选['id'],
        'selectedTitle':所选['title'](),
        'showWrap':所选.get('wrap') is True,
        'changed':已变更,
        'metaFailure':失败行(翻译,元['failure']) if 元.get('failure') is not None and 有内容 else None,
        'content':内容,
        'hasContent':有内容,
        'failure':失败行(翻译,当前['failure']) if 当前 is not None and 当前.get('failure') is not None else None,
        'eof':当前['eof'] if 当前 is not None else True,
        'loading':当前['loading'] if 当前 is not None else False,
        'mode':模式,
        'line':行号,
        'loadedThrough':已载至,
        'labels':{#文案
            'loading':翻译('loading'),
            'loadMore':翻译('loadMore'),
            'changed':翻译('changed'),
            'reloadNow':翻译('reloadNow'),
            'reload':翻译('reload'),
            'openWith':翻译('openWith'),
            'retry':翻译('retry'),
            'wrapEnable':翻译('wrap.enable'),
            'wrapDisable':翻译('wrap.disable'),
            'wrapAria':翻译('wrap.aria'),
            'rendererUnavailable':翻译('rendererUnavailable',{'name':所选['title']()}),
        },
    }#结束
