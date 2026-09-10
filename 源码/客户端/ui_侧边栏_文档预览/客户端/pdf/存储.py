"""可恢复的 PDF 查看偏好；文档对象与画布仍属组件本地。

对齐上游 `ui-sidebar-documentpreview/src/client/pdf/store.ts`。公开面仅中文名。
"""

__all__=['默认pdf视图','创建pdf存储']#仅中文公开名

默认pdf视图={'page':1}#初始页


def 初值():
    """空分桶表。"""
    return {'byTab':{}}#初态


def 页(草稿,标签标识,页号):
    """记下所选 1 起算页。"""
    草稿['byTab'][标签标识]={'page':页号}#记下


def 遗忘(草稿,标签标识):
    """丢掉已关闭标签的偏好。"""
    草稿['byTab']={键:值 for 键,值 in 草稿['byTab'].items() if 键!=标签标识}#过滤


def 创建pdf存储():
    """声明按标签身份隔离的最后可见页。"""
    return {#规格
        'init':初值,
        'actions':{
            'page':页,
            'forget':遗忘,
        },
    }#结束
