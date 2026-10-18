'已加载的 Office 预览在正文重挂后仍留着，直到重载或标签关闭'
from ....存储 import 声明存储

__all__=['创建Office存储']

def 创建Office存储():
    '在会话内按标签保留 Office 内容'
    def 初值():
        '空表'
        return {'byTab':{}}
    def 加载中(草稿,标签标识,修订):
        '开始这一修订'
        草稿['byTab'][标签标识]={'revision':修订}
    def 完成(草稿,标签标识,修订,文件):
        '这一修订的 PDF 字节'
        草稿['byTab'][标签标识]={'revision':修订,'file':文件}
    def 失败(草稿,标签标识,修订,失败信息):
        '这一修订的失败'
        草稿['byTab'][标签标识]={'revision':修订,'failure':失败信息}
    def 遗忘(草稿,标签标识):
        '标签关了就丢掉'
        留下={}
        for 标识,值 in 草稿['byTab'].items():
            if 标识!=标签标识:
                留下[标识]=值
        草稿['byTab']=留下
    return 声明存储({
        'init':初值,
        'actions':{'loading':加载中,'complete':完成,'failed':失败,'forget':遗忘},
    })
