'插件市场远程记录与事件；线协议键保持英文'

__all__=[#仅中文说明名；记录本身是 dict，键不译
    '安装状态','详情来源','排序种类','详情失败原因',
]#公开面结束

安装状态=('not-installed','installed','update-available','different-version','provided')#安装状态
详情来源=('locale','readme','repository')#详细介绍来源
排序种类=('index','relevance','published','key')#搜索排序
详情失败原因=('too-large','network','denied','git-unavailable','invalid')#详情读失败原因

#远程错误码（上报码，不译）：
# plugin-market/invalid-index-url  details: url, reason
# plugin-market/unknown-index       details: url
# plugin-market/fetch-failed        details: url, reason
# plugin-market/invalid-index       details: url, path, reason
# plugin-market/invalid-query       details: field, reason
# plugin-market/settings-unavailable details: {}
# plugin-market/unknown-plugin      details: name, version
# plugin-market/detail-unavailable  details: reason
#事件名：plugin-market/changed
#服务键：pluginMarket
#查询键：text, category, labels, sort, offset, limit, refresh, fetchedAt
#sort.kind：index | relevance | published | key；direction：asc | desc
#结果键：url, title, description, metadata, fetchedAt, entries, total, nextOffset
#条目键：versions, defaultVersion, installation, install, compatibility
#详情：status=found|none；origin；markdown；document
#图片路由：GET /api/plugin-market/detail-file?document=&path=
