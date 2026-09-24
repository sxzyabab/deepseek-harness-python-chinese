__all__=['文件树错误','创建文件存储']

#工具
def _分桶(状态,标签标识):
    """`start` 之前没有桶。写者依赖这次播种。"""
    按标签=状态['byTab']
    if 标签标识 not in 按标签:
        raise 文件树错误('ui-sidebar-files: no tree for tab "'+str(标签标识)+'"')
    return 按标签[标签标识]


def 初值():
    return {'byTab':{}}


def 启动(草稿,标签标识,根):
    """根放进展开集，打开时不用再点一次。"""
    草稿['byTab'][标签标识]={'root':根,'levels':{},'expanded':[根],'scrollTop':0,'autoRefresh':True}

def 自动刷新(草稿,标签标识,启用):
    _分桶(草稿,标签标识)['autoRefresh']=启用

def 加载中(草稿,标签标识,路径):
    树=_分桶(草稿,标签标识)
    现=树['levels'][路径] if 路径 in 树['levels'] else None
    if 现 is None or ('kind' not in 现) or 现['kind']!='ready':
        树['levels'][路径]={'kind':'loading'}

def 已加载(草稿,标签标识,路径,层级):
    """层级为 dict：entries / truncated。已就绪级会裁掉消失的子目录。"""
    树=_分桶(草稿,标签标识)
    先前=树['levels'][路径] if 路径 in 树['levels'] else None
    if 先前 is not None and 'kind' in 先前 and 先前['kind']=='ready':
        目录名=set()
        for 项 in 层级['entries']:
            if 'type' in 项 and 项['type']=='directory':
                目录名.add(项['name'])
        for 项 in 先前['level']['entries']:
            if ('type' not in 项) or 项['type']!='directory' or 项['name'] in 目录名:
                continue
            已删=路径.rstrip('/\\')+'/'+项['name']
            前缀=已删+'/'
            树['expanded']=[值 for 值 in 树['expanded'] if 值!=已删 and not 值.startswith(前缀)]
            树['levels']={键:值 for 键,值 in 树['levels'].items() if 键!=已删 and not 键.startswith(前缀)}
    树['levels'][路径]={'kind':'ready','level':层级}

def 已失败(草稿,标签标识,路径,失败):
    """失败为跨包 RemoteFailure dict。已就绪级只叠 failure。"""
    树=_分桶(草稿,标签标识)
    级=树['levels'][路径] if 路径 in 树['levels'] else None
    if 级 is not None and 'kind' in 级 and 级['kind']=='ready':
        树['levels'][路径]={**级,'failure':失败}
    else:
        树['levels'][路径]={'kind':'failed','failure':失败}


def 已切换(草稿,标签标识,路径):
    """折叠后已加载的级仍留着。"""
    树=_分桶(草稿,标签标识)
    展开=树['expanded']
    if 路径 in 展开:
        树['expanded']=[项 for 项 in 展开 if 项!=路径]
    else:
        展开.append(路径)


def 已滚动(草稿,标签标识,滚动顶):
    """偏移单位是像素。"""
    _分桶(草稿,标签标识)['scrollTop']=滚动顶


def 重置(草稿,标签标识):
    """只清已加载级，不收起目录。"""
    _分桶(草稿,标签标识)['levels']={}


def 遗忘(草稿,标签标识):
    草稿['byTab']={键:值 for 键,值 in 草稿['byTab'].items() if 键!=标签标识}


#
class 文件树错误(Exception):
    """消息保持英文，调用方按字符串比对。"""

    def __init__(自身,消息):
        super().__init__(消息)


def 创建文件存储():
    """框架按会话铸造。动作名是线协议。"""
    return {
        'init':初值,
        'actions':{
            'autoRefresh':自动刷新,
            'start':启动,
            'loading':加载中,
            'loaded':已加载,
            'failed':已失败,
            'toggled':已切换,
            'scrolled':已滚动,
            'reset':重置,
            'forget':遗忘,
        },
    }
