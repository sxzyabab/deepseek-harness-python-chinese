__all__=['向导种类','页面地址','默认种子']#仅中文公开名

向导种类='guide'#向导签种类（线路字面量）


def 页面地址(种类):
    """页面签记录地址：`sidebar://<kind>`。调用方只点名种类，不拼地址。"""
    return 'sidebar://'+种类#页面地址


def 默认种子(标签表):
    """按已登记引导入口数量解析默认页面；零个或多个入口时回退向导。"""
    入口=list(标签表.guide())#引导入口
    唯一=len(入口)==1#恰一入口
    种类=入口[0]['kind'] if 唯一 else 向导种类#唯一则用其 kind
    定义=标签表.get(种类)#类型定义
    if 定义 is None:#未登记
        raise Exception('sidebarRight: 默认标签种类 "'+种类+'" 未登记')#拒绝
    取标题=定义['title'] if isinstance(定义,dict) else 定义.title#标题 thunk
    return {'kind':种类,'title':取标题(页面地址(种类))}#种子
