"""预览自持状态：已读页，以及读者如何看它们。

对齐上游 `ui-sidebar-textpreview/src/client/store.ts`。公开面仅中文名。
`file` 资源只带元数据，文本由本类型自取自持——按页、以每页起始的 1 起算行号为键。
视图状态（滚动偏移、换行、已应答的导航）必须活过正文：切走的 tab 卸载正文，
回来时应停在原处，而不是重读或跳回开篇。按 tab id 分桶，因为同文件两 tab 独立滚动。

一桶寿命等于其 tab 记录：面的首次读取在拥有方 `signal` 上挂一次监听，记录结束时忘掉桶；
从未读过的 tab 无桶可忘。
跨线 / 跨包值为 dict；本模块只导出工厂（模块级句柄会在插件重载间钉死身份）。
"""

__all__=['空白页态','创建文本预览存储']#仅中文公开名


def 空白页态():
    """一 tab 在尚未读、滚、切、应答前的空桶。"""
    return {#空桶
        'version':None,#尚未有页
        'pages':{},#按起始行号
        'eof':False,#未到文件尾
        'loading':False,#无在飞
        'failure':None,#无失败
        'scrollTop':0,#顶
        'wrap':True,#默认换行
        'revision':None,#尚未应答导航
    }#空桶结束


def _分桶(状态,标签标识):
    """取一 tab 的桶；首次写入时创建。状态为 dict。"""
    按标签=状态['byTab']#分桶表
    if 标签标识 not in 按标签:#尚未有
        按标签[标签标识]=空白页态()#播种
    return 按标签[标签标识]#该桶


def 初值():
    """空分桶表。"""
    return {'byTab':{}}#初态


def 加载中(草稿,标签标识):
    """标记一页读取在飞。"""
    _分桶(草稿,标签标识)['loading']=True#在飞


def 收入页(草稿,标签标识,页):
    """收下页。更新文件版本会使旧版页失效，正文不同时显示两版本。页为跨包 WorkspaceFileText dict。"""
    态=_分桶(草稿,标签标识)#该桶
    版本=页['version'] if 'version' in 页 else None#页版本
    if 态['version'] is not None and 态['version']!=版本:#版本变了
        态['pages']={}#丢掉旧页
    态['version']=版本#挂版本
    偏移=int(页['offset'])#起始行（1 起算）
    态['pages'][偏移]={'text':页['text'],'lines':页['lines']}#记下页
    态['eof']=页['eof'] is True if 'eof' in 页 else False#是否尾
    态['loading']=False#结算
    态['failure']=None#清失败


def 已失败(草稿,标签标识,失败):
    """记下页读失败原因；已持有页保留。失败为跨包 RemoteFailure dict。"""
    态=_分桶(草稿,标签标识)#该桶
    态['loading']=False#结算
    态['failure']=失败#记下


def 重置(草稿,标签标识):
    """丢掉全部页，保留视图，以便从首行重读。"""
    态=_分桶(草稿,标签标识)#该桶
    态['pages']={}#清页
    态['eof']=False#未尾
    态['version']=None#无版本
    态['failure']=None#清失败


def 已滚动(草稿,标签标识,滚动顶):
    """记下正文滚到何处（像素）。"""
    _分桶(草稿,标签标识)['scrollTop']=滚动顶#偏移


def 已切换换行(草稿,标签标识):
    """在换行与横向滚动之间切换。"""
    态=_分桶(草稿,标签标识)#该桶
    态['wrap']=not 态['wrap']#翻转


def 已导航(草稿,标签标识,修订):
    """记下正文已应答一次导航，以便重挂时恢复位置而非再跳。"""
    _分桶(草稿,标签标识)['revision']=修订#修订号


def 遗忘(草稿,标签标识):
    """忘掉已消失 tab 记录的桶。"""
    草稿['byTab']={键:值 for 键,值 in 草稿['byTab'].items() if 键!=标签标识}#过滤


def 创建文本预览存储():
    """声明预览存储规格（init / actions），供登记收下；框架按会话铸造实例。"""
    return {#规格进、句柄出（对齐 defineStore 入参）
        'init':初值,#播种
        'actions':{#动作写集合；每个动作点名所写 tab
            'loading':加载中,#标记在飞
            'page':收入页,#收下页
            'failed':已失败,#记下失败
            'reset':重置,#清页留视图
            'scrolled':已滚动,#记下滚动
            'toggledWrap':已切换换行,#切换换行
            'navigated':已导航,#记下导航应答
            'forget':遗忘,#删桶
        },#动作结束
    }#规格结束
