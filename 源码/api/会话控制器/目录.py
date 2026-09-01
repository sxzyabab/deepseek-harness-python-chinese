"""把在线 LLM 注册表投影为浏览器模型目录。

对齐上游 `session-controller/src/catalog.ts`。公开面仅中文名。
"""
from .工具 import 取字段,解开#辅助

__all__=['构建模型目录']#仅中文公开名

def 构建模型目录(上下文,默认选择=None):#构建模型目录
    """无需会话即可构建模型目录。"""
    if 默认选择 is None:#缺省
        默认选择=上下文.agentDefaultModel.currentSelection()#部署默认
    提供方们=上下文.llm.listProviders()#列出提供方
    目录项=[]#分组与失败
    for 提供方 in 提供方们:#逐个
        try:#列模型
            模型们=解开(上下文.llm.listModels(取字段(提供方,'id')))#模型列表
            条目们=[]#组内模型
            for 模型 in 模型们:#逐个模型
                解析=解开(上下文.llm.resolveModelInfo(取字段(提供方,'id'),取字段(模型,'id')))#解析
                推理=None#推理元数据
                if 取字段(解析,'reasoning') is not None:#有推理
                    努力们=[#努力列表
                        {'id':取字段(项,'id'),'name':取字段(项,'name'),**({} if 取字段(项,'description') is None else {'description':取字段(项,'description')})}
                        for 项 in (取字段(取字段(解析,'reasoning'),'efforts') or [])
                    ]#结束
                    推理={'efforts':努力们,**({} if 取字段(取字段(解析,'reasoning'),'defaultEffort') is None else {'defaultEffort':取字段(取字段(解析,'reasoning'),'defaultEffort')})}#推理对象
                条目={#模型条目
                    'id':取字段(模型,'id'),#id
                    'name':取字段(模型,'name'),#名
                    **({} if 取字段(模型,'description') is None else {'description':取字段(模型,'description')}),#描述
                    **({} if 推理 is None else {'reasoning':推理}),#推理
                }#条目结束
                条目们.append(条目)#收集
            目录项.append({'kind':'group','group':{'id':取字段(提供方,'id'),'name':取字段(提供方,'name'),'models':条目们}})#成功组
        except Exception as 错误:#提供方失败
            目录项.append({'kind':'failure','failure':{'id':取字段(提供方,'id'),'name':取字段(提供方,'name'),'message':str(错误)}})#失败项
    return {#目录
        'default':dict(默认选择) if isinstance(默认选择,dict) else {'provider':取字段(默认选择,'provider'),'model':取字段(默认选择,'model'),**({} if 取字段(默认选择,'reasoningEffort') is None else {'reasoningEffort':取字段(默认选择,'reasoningEffort')})},#默认
        'routableProviders':[取字段(项,'id') for 项 in 提供方们],#可路由提供方
        'groups':[取字段(项,'group') for 项 in 目录项 if 取字段(项,'kind')=='group' and len(取字段(取字段(项,'group'),'models') or [])>0],#非空组
        'failures':[取字段(项,'failure') for 项 in 目录项 if 取字段(项,'kind')=='failure'],#失败
    }#结束
