"""把在线 LLM 注册表投影为浏览器模型目录。"""
__all__=['构建模型目录']#仅中文公开名

def 构建模型目录(上下文,默认选择=None):
    """无需会话即可构建模型目录。提供方与模型为 dict。"""
    if 默认选择 is None:#缺省
        默认选择=上下文.agentDefaultModel.currentSelection()#部署默认
    提供方列表=上下文.llm.listProviders()#列出提供方
    目录项=[]#分组与失败
    for 提供方 in 提供方列表:#逐个
        try:
            模型列表=上下文.llm.listModels(提供方['id'])#模型列表
            条目表=[]#组内模型
            for 模型 in 模型列表:#逐个模型
                解析=上下文.llm.resolveModelInfo(提供方['id'],模型['id'])#解析为 dict
                推理=None#推理元数据
                if 'reasoning' in 解析 and 解析['reasoning'] is not None:#有推理
                    推理块=解析['reasoning']#推理 dict
                    努力源=推理块['efforts'] if 'efforts' in 推理块 and 推理块['efforts'] is not None else []#努力列表
                    努力列表=[]#投影
                    for 项 in 努力源:#逐项
                        努力={'id':项['id'],'name':项['name']}#基础
                        if 'description' in 项 and 项['description'] is not None:#有描述
                            努力['description']=项['description']#描述
                        努力列表.append(努力)#收集
                    推理={'efforts':努力列表}#推理对象
                    if 'defaultEffort' in 推理块 and 推理块['defaultEffort'] is not None:#有默认
                        推理['defaultEffort']=推理块['defaultEffort']#默认
                条目={'id':模型['id'],'name':模型['name']}#模型条目
                if 'description' in 模型 and 模型['description'] is not None:#有描述
                    条目['description']=模型['description']#描述
                if 推理 is not None:#有推理
                    条目['reasoning']=推理#推理
                条目表.append(条目)#收集
            目录项.append({'kind':'group','group':{'id':提供方['id'],'name':提供方['name'],'models':条目表}})#成功组
        except (OSError,ValueError,TypeError,KeyError,AttributeError) as 错误:
            目录项.append({'kind':'failure','failure':{'id':提供方['id'],'name':提供方['name'],'message':str(错误)}})#失败项
    if isinstance(默认选择,dict):#已是映射
        默认=dict(默认选择)#拷贝
    else:#对象
        默认={'provider':默认选择.provider,'model':默认选择.model}#字段
        力度=getattr(默认选择,'reasoningEffort',None)#力度
        if 力度 is not None:#有力度
            默认['reasoningEffort']=力度#写入
    组列表=[]#非空组
    失败列表=[]
    for 项 in 目录项:#分类
        if 项['kind']=='group' and len(项['group']['models'])>0:#非空组
            组列表.append(项['group'])#收下
        if 项['kind']=='failure':
            失败列表.append(项['failure'])#收下
    return {#目录
        'default':默认,#默认
        'routableProviders':[项['id'] for 项 in 提供方列表],#可路由提供方
        'groups':组列表,#非空组
        'failures':失败列表,
    }
