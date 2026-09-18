
__all__=['新鲜','创建文本存储']#仅中文公开名


def 新鲜():
    """标签在读取、滚动、切换或应答任何事前的状态。"""
    return {#空桶
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
    }#新鲜结束


def _分桶(状态,标签标识):
    """一个标签的桶，首次写入时创建。状态为 dict。"""
    按标签=状态['byTab']#分桶表
    if 标签标识 not in 按标签:#尚未播种
        按标签[标签标识]=新鲜()#播种
    return 按标签[标签标识]#该桶


def 已选(草稿,标签标识,渲染器标识):
    """记下或清除显式查看器选择。"""
    桶=_分桶(草稿,标签标识)#该桶
    if 渲染器标识 is None:#清选择
        if 'rendererId' in 桶:#有键
            del 桶['rendererId']#删
    else:#记下
        桶['rendererId']=渲染器标识#选择


def 加载中(草稿,标签标识,模式=None,观察版本=None,内容渲染器标识=None):
    """标记一页读取在飞行中。"""
    状态=_分桶(草稿,标签标识)#该桶
    if 状态['version'] is None and not 状态['loading']:#首次观察
        状态['observedVersion']=观察版本#记下
    if 内容渲染器标识 is None:#清
        if 'contentRendererId' in 状态:#有
            del 状态['contentRendererId']#删
    else:#记下
        状态['contentRendererId']=内容渲染器标识#写
    状态['loading']=True#加载中
    状态['failure']=None#清失败
    if 模式 is not None:#有模式
        状态['mode']=模式#记下


def 已渲染(草稿,标签标识,修订,版本):
    """渲染器自有加载完成。"""
    状态=草稿['byTab'].get(标签标识)#桶
    if 状态 is None or 状态.get('mode')!='renderer' or 状态.get('loadRevision')!=修订:#过期
        return#停
    状态['version']=版本#版本
    状态['loading']=False#结束


def 完成(草稿,标签标识,文件):
    """记下本视图的完整字节结果。文件为 dict。"""
    状态=_分桶(草稿,标签标识)#该桶
    状态['complete']=文件#完整字节
    状态['version']=文件['version']#版本
    状态['eof']=True#已到末
    状态['loading']=False#结束加载
    状态['failure']=None#清失败


def 页(草稿,标签标识,页结果):
    """保留一页。来自较新文件版本的页会使旧版页失效。页结果为跨包 WorkspaceFileText dict。"""
    状态=_分桶(草稿,标签标识)#该桶
    if 状态['version'] is not None and 状态['version']!=页结果['version']:#换版
        状态['pages']={}#清空
    状态['version']=页结果['version']#版本
    状态['pages'][页结果['offset']]={'text':页结果['text'],'lines':页结果['lines']}#记下页
    状态['eof']=页结果['eof']#是否末尾
    状态['loading']=False#结束加载
    状态['failure']=None#清失败


def 已失败(草稿,标签标识,失败):
    """记下页读取失败原因；已持有的页保留。失败为跨包 RemoteFailure dict。"""
    状态=_分桶(草稿,标签标识)#该桶
    状态['loading']=False#结束加载
    状态['failure']=失败#记下


def 重置(草稿,标签标识):
    """丢掉每一页、保留视图，以便从第一行重读。"""
    状态=_分桶(草稿,标签标识)#该桶
    状态['loadRevision']=状态.get('loadRevision',0)+1#晋修订
    状态['pages']={}#清页
    if 'complete' in 状态:#有完整
        del 状态['complete']#清
    状态['eof']=False#未到末
    状态['version']=None#清版本
    状态['observedVersion']=None#清观察
    状态['loading']=False#结束加载
    状态['failure']=None#清失败


def 已滚动(草稿,标签标识,滚动顶):
    """记下一个标签正文滚到何处。"""
    _分桶(草稿,标签标识)['scrollTop']=滚动顶#记下


def 已切换换行(草稿,标签标识):
    """在换行与不换行之间切换一个标签。"""
    状态=_分桶(草稿,标签标识)#该桶
    状态['wrap']=not 状态['wrap']#翻转


def 已导航(草稿,标签标识,修订):
    """记下正文已应答一次导航。"""
    _分桶(草稿,标签标识)['revision']=修订#记下


def 遗忘(草稿,标签标识):
    """丢掉一个标签的状态，用于已消失的标签记录。"""
    草稿['byTab']={键:值 for 键,值 in 草稿['byTab'].items() if 键!=标签标识}#过滤


def 初值():
    """空分桶表。"""
    return {'byTab':{}}#初态


def 创建文本存储():
    """声明预览存储规格（init / actions），供登记收下；框架按会话铸造实例。"""
    return {#规格
        'init':初值,#播种
        'actions':{#动作写集合
            'selected':已选,#选择渲染器
            'loading':加载中,#加载中
            'rendered':已渲染,#渲染器完成
            'complete':完成,#完整字节
            'page':页,#一页
            'failed':已失败,#失败
            'reset':重置,#重置
            'scrolled':已滚动,#滚动
            'toggledWrap':已切换换行,#换行
            'navigated':已导航,#导航
            'forget':遗忘,#遗忘
        },#动作结束
    }#规格结束
