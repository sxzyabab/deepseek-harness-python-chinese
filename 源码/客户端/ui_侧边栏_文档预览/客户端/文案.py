
__all__=['中文','英文','侧栏文档预览文案键']#仅中文公开名

中文={#简体中文词典与键集真源
    'loading':'正在读取…',
    'loadMore':'加载更多',
    'changed':'文件已更新，当前显示为旧内容',
    'reloadNow':'重新载入',
    'reload':'重新读取文件',
    'wrap.enable':'自动换行',
    'wrap.disable':'取消换行',
    'wrap.aria':'自动换行',
    'openWith':'打开方式',
    'viewer.text':'纯文本',
    'resourceUnavailable':'文件资源服务不可用',
    'rendererUnavailable':'预览器 {name} 不可用',
    'unsupportedFile':'该格式文件暂时无法预览',
    'error.notFound':'文件不存在，可能已被移动或删除',
    'error.tooLarge':'单页内容超过 {limit} 上限，无法读取',
    'error.notText':'该格式文件暂时无法预览',
    'error.notRegularFile':'该路径不是普通文件，没有可显示的内容',
    'error.unavailable':'读取失败：{message}',
    'retry':'重试',
}#中文结束

侧栏文档预览文案键=tuple(中文.keys())#键联合

英文={#英文词典，对照中文键集
    'loading':'Reading…',
    'loadMore':'Load more',
    'changed':'The file has changed, showing the previous content.',
    'reloadNow':'Reload',
    'reload':'Read the file again',
    'wrap.enable':'Turn on line wrap',
    'wrap.disable':'Turn off line wrap',
    'wrap.aria':'Line wrap',
    'openWith':'Open with',
    'viewer.text':'Plain text',
    'resourceUnavailable':'The file resource service is unavailable.',
    'rendererUnavailable':'The {name} preview is unavailable.',
    'unsupportedFile':'Preview is not available for this file type yet.',
    'error.notFound':'File not found. It may have been moved or deleted.',
    'error.tooLarge':'This page exceeds the {limit} limit and cannot be read.',
    'error.notText':'Preview is not available for this file type yet.',
    'error.notRegularFile':'Not a regular file, nothing to display.',
    'error.unavailable':'Read failed: {message}',
    'retry':'Retry',
}#英文结束
