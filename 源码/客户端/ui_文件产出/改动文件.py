'改动文件卡视图工厂'
from nicegui import ui as 界面
__all__=['折叠改动行数','改动文件','画改动文件']#仅中文公开名

折叠改动行数=4#折叠前行数，与上游 COLLAPSED_ROWS 相同

def 路径末段(路径):#取末段
    '正斜杠或反斜杠分隔的末段'
    斜=路径.rfind('/')#正斜
    反=路径.rfind('\\')#反斜
    位=斜 if 斜>反 else 反#末分隔
    return 路径 if 位==-1 else 路径[位+1:]#末段

def 改动文件(属性):#视图
    '抬头与按行打开审阅。单文件只留抬头'
    改动=属性['changes']#摘要+seq
    翻译=属性['t']#文案
    打开审阅=属性['openReview']#打开
    工作目录=属性['cwd'] if 'cwd' in 属性 else None#cwd
    展开=属性['expanded'] if 'expanded' in 属性 else False#展开
    切换=属性['onToggle'] if 'onToggle' in 属性 else None#切换
    文件表=list(改动['files']) if 'files' in 改动 and 改动['files'] is not None else []#文件
    单文件=文件表[0] if 'total' in 改动 and 改动['total']==1 and len(文件表)>0 else None#单文件
    可折=单文件 is None and len(文件表)>折叠改动行数#可折
    行表=[] if 单文件 is not None else (文件表[:折叠改动行数] if 可折 and not 展开 else 文件表)#展示
    行视图=[]#行
    for 下标,文件 in enumerate(行表):#每行
        def 点行(序=下标):#打开该行
            'openReview(index)'
            打开审阅(序)#开
        计数=翻译('changes.binary') if 'binary' in 文件 and 文件['binary'] is True else (#二进制
            翻译('changes.oversized') if 'oversized' in 文件 and 文件['oversized'] is True else {#过大
                'added':翻译('changes.added',{'count':str(文件['added'])}),#增
                'deleted':翻译('changes.deleted',{'count':str(文件['deleted'])}),#删
            })#计数
        行视图.append({#行
            'display':文件['display'],#展示
            'path':文件['path'],#路径
            'cwd':工作目录,#cwd
            'counts':计数,#计数
            'aria':翻译('changes.viewDiff',{'name':文件['display']}),#无障碍
            'onClick':点行,#点击
        })#行结束
    def 点抬头():#开第一文件
        'openReview(0)'
        打开审阅(0)#开
    if 单文件 is not None and 'binary' in 单文件 and 单文件['binary'] is True:#二进制
        抬头计数=翻译('changes.binary')#二进制
    elif 单文件 is not None and 'oversized' in 单文件 and 单文件['oversized'] is True:#过大
        抬头计数=翻译('changes.oversized')#过大
    else:#行数
        抬头计数=None#用增减
    if 单文件 is not None:#单文件标题用文件名
        标题=翻译('changes.singleTitle',{'name':路径末段(单文件['path'] if 'path' in 单文件 else '')})#单文件
        无障碍=翻译('changes.viewDiff',{'name':单文件['display'] if 'display' in 单文件 else ''})#该文件
    else:#多文件
        标题=翻译('changes.title',{'count':str(改动['total'] if 'total' in 改动 else len(文件表))})#计数标题
        无障碍=翻译('changes.openReview')#整轮
    return {#视图
        'type':'changed-files',#类型
        'header':{#抬头
            'aria':无障碍,#无障碍
            'title':标题,#标题
            'added':翻译('changes.added',{'count':str(改动['added'] if 'added' in 改动 else 0)}),#增
            'deleted':翻译('changes.deleted',{'count':str(改动['deleted'] if 'deleted' in 改动 else 0)}),#删
            'counts':抬头计数,#单文件二进制或过大
            'onClick':点抬头,#点击
        },#抬头结束
        'rows':行视图,#行
        'toggle':{#折叠
            'expanded':展开,#展开
            'label':翻译('changes.collapse' if 展开 else 'changes.all',{'count':str(len(文件表))}),#文案
            'aria':翻译('changes.collapseAria' if 展开 else 'changes.expandAria',{'count':str(len(文件表))}),#无障碍
            'onToggle':切换,#切换
        } if 可折 else None,#可折才有
        'cssModule':'ChangedFiles.module.css',#样式
    }#视图结束

def 画改动文件(视):
    '抬头、逐行打开审阅，以及折叠'
    抬头=视['header']
    def 点抬头():
        '打开第一份审阅'
        抬头['onClick']()
    界面.button(抬头['title'],on_click=点抬头).props('flat no-caps')
    if 'counts' in 抬头 and isinstance(抬头['counts'],str) and 抬头['counts']!='':#单文件特殊计数
        界面.label(抬头['counts'])#二进制或过大
    else:#增减
        界面.label(抬头['added'])#增
        界面.label(抬头['deleted'])#删
    for 行 in 视['rows']:
        计数=行['counts']
        后缀=''
        if isinstance(计数,dict):
            后缀=' '+计数['added']+' '+计数['deleted']
        elif isinstance(计数,str) and 计数!='':
            后缀=' '+计数
        def 点行(_事件=None,回调=行['onClick']):
            '打开这一行的对比'
            回调()
        界面.button(行['display']+后缀,on_click=点行).props('flat no-caps align=left')
    折叠=视['toggle']
    if isinstance(折叠,dict) and 折叠['onToggle'] is not None:
        def 点折叠():
            '展开或收起改动'
            折叠['onToggle']()
        界面.button(折叠['label'],on_click=点折叠).props('flat no-caps')
