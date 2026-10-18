'审阅标签的查看状态：选中文件、左右或单栏、是否换行'
from ...存储 import 声明存储

__all__=['创建审阅存储']


def 桶(状态,标签标识):
    '没有这张签的桶就抛'
    签=状态['byTab'].get(标签标识)
    if 签 is None:
        raise Exception('ui-deliverables: no review state for tab "'+str(标签标识)+'"')
    return 签


def 初值():
    '每张签一个桶'
    return {'byTab':{}}


def 已导航(草稿,标签标识,修订,下标):
    '第一次导航播种左右对比且不换行，之后只改下标和修订'
    签=草稿['byTab'].get(标签标识)
    if 签 is None:
        草稿['byTab'][标签标识]={'index':下标,'split':True,'wrap':False,'navigated':修订}
    else:
        签['index']=下标
        签['navigated']=修订


def 已选(草稿,标签标识,下标):
    '改成另一份文件'
    桶(草稿,标签标识)['index']=下标


def 切换左右(草稿,标签标识):
    '单栏和左右对调'
    签=桶(草稿,标签标识)
    签['split']=not 签['split']


def 切换换行(草稿,标签标识):
    '换行开关'
    签=桶(草稿,标签标识)
    签['wrap']=not 签['wrap']


def 遗忘(草稿,标签标识):
    '签没了就丢掉它的桶'
    留下={}
    for 标识,签 in 草稿['byTab'].items():
        if 标识!=标签标识:
            留下[标识]=签
    草稿['byTab']=留下


def 创建审阅存储():
    '登记成独占 store，每个会话一份'
    return 声明存储({
        'init':初值,
        'actions':{
            'navigated':已导航,
            'selected':已选,
            'toggledSplit':切换左右,
            'toggledWrap':切换换行,
            'forget':遗忘,
        },
    })
