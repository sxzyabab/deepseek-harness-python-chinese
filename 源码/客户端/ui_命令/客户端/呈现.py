from ...ui_基础界面组件.icons import 图标下载16,图标列表笔16,图标目标16

__all__=['分区行名','宿主面','宿主面函数']

分区行名={
    'add':('file','goal','plan','feedback'),
    'commands':('compact','permission','model','export'),
}

def 宿主面函数(名,图标):
    '一条内置宿主命令的文案键和字形'
    return (名,{
        'label':'label.'+名,
        'description':'description.'+名,
        'icon':图标,
    })

宿主面=dict((
    宿主面函数('goal',图标目标16),
    宿主面函数('plan',图标列表笔16),
    宿主面函数('feedback',None),
    宿主面函数('compact',None),
    宿主面函数('permission',None),
    宿主面函数('export',图标下载16),
))
