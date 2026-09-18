from ...远程模拟 import 成功信封,打开流脚本#成功信封与开流脚本

__all__=['远程默认应答']#仅中文公开名

远程默认应答={#启动期 Remote 端点的默认应答
    'unary':{#一元应答
        'session/list':成功信封({'items':[]}),#会话列表
        'settings/describe':成功信封({'writable':True,'hasDocument':False,'namespaces':[]}),#设置描述
        'session/modelCatalog':成功信封({#模型目录
            'default':{'provider':'deepseek-official','model':'deepseek-v4-flash'},#默认模型
            'routableProviders':[],#可路由提供方
            'groups':[],#分组
            'failures':[],#失败
        }),#session/modelCatalog结束
        'agentPresets/list':成功信封({'presets':[],'authorable':False}),#智能体预设列表
        'dynamicCordisRunner/syncInspectManifest':成功信封(None),#同步巡检清单
        'dynamicCordisRunner/inventory':成功信封([]),#动态运行器清单
        'credentials/describe':成功信封({}),#凭据描述
        'permissionPresets/catalog':成功信封({'options':[]}),#权限预设目录
    },#unary结束
    'streams':[#无脚本的流声明
        'session/follow',#会话跟随
    ],#streams结束
    'stream':{#带脚本的流
        'session/control':打开流脚本([{'type':'baseline','value':{'jobs':{},'projections':{}}}]),#会话控制
        'workspace/follow':打开流脚本([{'type':'baseline','value':{'items':[],'archivedSessionIds':[]}}]),#工作区跟随
    },#stream结束
}#远程默认应答结束
