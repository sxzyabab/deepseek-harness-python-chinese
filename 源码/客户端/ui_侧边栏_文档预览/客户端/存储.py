'预览自己的状态：读过的页，以及读者怎么看这些页'
from ...存储 import 声明存储

__all__=['新鲜','创建文本存储']

def 新鲜():
    '标签在读取、滚动、切换或应答任何事前的状态'
    return {
        'autoRefresh':True,
        'resourcesDirty':False,
        'loadRevision':0,
        'version':None,
        'observedVersion':None,
        'pages':{},
        'eof':False,
        'loading':False,
        'failure':None,
        'scrollTop':0,
        'wrap':True,
        'revision':None,
    }

def 分桶(状态,标签标识):
    '一个标签的桶，首次写入时创建'
    表=状态['byTab']
    if 标签标识 not in 表:
        表[标签标识]=新鲜()
    return 表[标签标识]

def 切换自动刷新(草稿,标签标识):
    '打开或关掉自动刷新'
    状态=分桶(草稿,标签标识)
    状态['autoRefresh']=not 状态['autoRefresh']

def 资源已变(草稿,标签标识):
    '依赖的文件元数据变了'
    分桶(草稿,标签标识)['resourcesDirty']=True

def 已选(草稿,标签标识,渲染器标识):
    '记下或清除显式查看器选择'
    桶=分桶(草稿,标签标识)
    if 渲染器标识 is None:
        if 'rendererId' in 桶:
            del 桶['rendererId']
        return
    桶['rendererId']=渲染器标识

def 加载中(草稿,标签标识,模式=None,观察版本=None,内容渲染器标识=None):
    '标记一次读取在飞行中。后到的页保留最初观察到的版本'
    状态=分桶(草稿,标签标识)
    if 状态['version'] is None and 状态['loading'] is False:
        状态['observedVersion']=观察版本
    if 内容渲染器标识 is None:
        if 'contentRendererId' in 状态:
            del 状态['contentRendererId']
    else:
        状态['contentRendererId']=内容渲染器标识
    状态['loading']=True
    状态['failure']=None
    if 模式 is not None:
        状态['mode']=模式

def 已渲染(草稿,标签标识,修订,版本):
    '渲染器自有加载完成。修订对不上就什么都不写'
    状态=草稿['byTab'][标签标识] if 标签标识 in 草稿['byTab'] else None
    if 状态 is None or 状态.get('mode')!='renderer' or 状态['loadRevision']!=修订:
        return
    状态['version']=版本
    状态['loading']=False

def 渲染器失败(草稿,标签标识,修订):
    '结束一次失败的渲染器加载'
    状态=草稿['byTab'][标签标识] if 标签标识 in 草稿['byTab'] else None
    if 状态 is None or 状态.get('mode')!='renderer' or 状态['loadRevision']!=修订:
        return
    状态['loading']=False

def 完成(草稿,标签标识,文件):
    '记下本视图的完整字节结果'
    状态=分桶(草稿,标签标识)
    状态['complete']=文件
    状态['version']=文件['version']
    状态['eof']=True
    状态['loading']=False
    状态['failure']=None

def 页(草稿,标签标识,页结果):
    '保留一页。较新文件版本会使旧版页失效'
    状态=分桶(草稿,标签标识)
    if 状态['version'] is not None and 状态['version']!=页结果['version']:
        状态['pages']={}
    状态['version']=页结果['version']
    状态['pages'][页结果['offset']]={'text':页结果['text'],'lines':页结果['lines']}
    状态['eof']=页结果['eof']
    状态['loading']=False
    状态['failure']=None

def 已失败(草稿,标签标识,失败):
    '记下页读取失败原因。已持有的页保留'
    状态=分桶(草稿,标签标识)
    状态['loading']=False
    状态['failure']=失败

def 重置(草稿,标签标识):
    '丢掉每一页、保留视图，以便从第一行重读'
    状态=分桶(草稿,标签标识)
    状态['resourcesDirty']=False
    状态['loadRevision']=状态['loadRevision']+1
    状态['pages']={}
    if 'complete' in 状态:
        del 状态['complete']
    状态['eof']=False
    状态['version']=None
    状态['observedVersion']=None
    状态['loading']=False
    状态['failure']=None

def 已滚动(草稿,标签标识,滚动顶):
    '记下一个标签正文滚到何处'
    分桶(草稿,标签标识)['scrollTop']=滚动顶

def 已切换换行(草稿,标签标识):
    '在换行与不换行之间切换一个标签'
    状态=分桶(草稿,标签标识)
    状态['wrap']=not 状态['wrap']

def 已导航(草稿,标签标识,修订):
    '记下正文已应答一次导航'
    分桶(草稿,标签标识)['revision']=修订

def 遗忘(草稿,标签标识):
    '丢掉一个标签的状态'
    留下={}
    for 标识,状态 in 草稿['byTab'].items():
        if 标识!=标签标识:
            留下[标识]=状态
    草稿['byTab']=留下

def 创建文本存储():
    '声明预览存储。apply 里铸造一次，正文和工具登记共用'
    def 初值():
        '空分桶表'
        return {'byTab':{}}
    return 声明存储({
        'init':初值,
        'actions':{
            'toggledAutoRefresh':切换自动刷新,
            'resourceChanged':资源已变,
            'selected':已选,
            'loading':加载中,
            'rendered':已渲染,
            'rendererFailed':渲染器失败,
            'complete':完成,
            'page':页,
            'failed':已失败,
            'reset':重置,
            'scrolled':已滚动,
            'toggledWrap':已切换换行,
            'navigated':已导航,
            'forget':遗忘,
        },
    })
