'没有存下的偏好时，回落到已登记的聊天视图'

__all__=['默认视图标识','轨迹视图标识','解析活动视图']

默认视图标识='chat'
轨迹视图标识='trajectory'

def 解析活动视图(页签列,选中标识):
    '先用存下的视图，没有再选聊天。两者都没登记则没有结果'
    选中=None
    if 选中标识 is not None:
        for 页 in 页签列:
            if 页['id']==选中标识:
                选中=页
                break
    if 选中 is not None:
        return 选中
    for 页 in 页签列:
        if 页['id']==默认视图标识:
            return 页
    return None
