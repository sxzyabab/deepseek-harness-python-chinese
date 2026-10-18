'按标签记住最后看见的页和缩放'
from ....存储 import 声明存储

__all__=['创建pdf存储']

def 创建pdf存储():
    '最后可见页和缩放偏好按标签隔开'
    def 初值():
        '空表'
        return {'byTab':{}}
    def 页(草稿,标签标识,页号):
        '记下所选的、从 1 起算的页'
        已有=草稿['byTab'][标签标识] if 标签标识 in 草稿['byTab'] else {}
        下一=dict(已有)
        下一['page']=页号
        草稿['byTab'][标签标识]=下一
    def 缩放(草稿,标签标识,比例):
        '记下缩放。还没有页则从第 1 页起'
        已有=草稿['byTab'][标签标识] if 标签标识 in 草稿['byTab'] else {}
        页号=已有['page'] if 'page' in 已有 else 1
        草稿['byTab'][标签标识]={'page':页号,'zoom':比例}
    def 遗忘(草稿,标签标识):
        '丢掉已关闭标签的偏好'
        留下={}
        for 标识,值 in 草稿['byTab'].items():
            if 标识!=标签标识:
                留下[标识]=值
        草稿['byTab']=留下
    return 声明存储({'init':初值,'actions':{'page':页,'zoom':缩放,'forget':遗忘}})
