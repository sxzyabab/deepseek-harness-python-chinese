"""`sidebarTextpreview` 命名空间词典。

对齐上游 `ui-sidebar-textpreview/src/client/locales.ts`。公开面仅中文名；词典键与英文字面量保持上游。
失败行是本文件的重点：读不出一页时要说清哪一类出错，各自对应不同下一步。
"""

__all__=['中文','英文','侧栏文本预览文案键']#仅中文公开名

中文={#简体中文词条（键集合的权威源）
    'loading':'正在读取…',#读取中
    'loadMore':'加载更多',#加载更多
    'changed':'文件已被修改，显示的还是旧内容。',#已变更提示
    'reloadNow':'重新载入',#立刻重载
    'reload':'重新读取文件',#工具：重读
    'wrap':'自动换行',#工具：换行
    'error.notFound':'这个文件不在了。可能已被移动或删除。',#不存在
    'error.outsideWorkspace':'这个文件在工作区之外，侧栏不会读取它。',#工作区外
    'error.tooLarge':'这一页太大，侧栏不读取超过 {limit} 的页。',#超限
    'error.notText':'这不是文本文件，没法在这里查看。',#非文本
    'error.notRegularFile':'这不是一个普通文件，没有可显示的文本。',#非普通文件
    'error.unavailable':'读取失败：{message}',#其它失败
    'retry':'重试',#重试
}#中文词典结束

英文={#英文词条，对照中文权威源核验键齐全
    'loading':'Reading…',#读取中
    'loadMore':'Load more',#加载更多
    'changed':'The file has changed; this is the older text.',#已变更提示
    'reloadNow':'Reload',#立刻重载
    'reload':'Read the file again',#工具：重读
    'wrap':'Wrap lines',#工具：换行
    'error.notFound':'That file is gone. It may have been moved or deleted.',#不存在
    'error.outsideWorkspace':'That file is outside the workspace, so the sidebar will not read it.',#工作区外
    'error.tooLarge':'That page is too large; the sidebar does not read pages above {limit}.',#超限
    'error.notText':'That is not a text file, so it cannot be shown here.',#非文本
    'error.notRegularFile':'That is not a regular file, so it has no text to show.',#非普通文件
    'error.unavailable':'Read failed: {message}',#其它失败
    'retry':'Retry',#重试
}#英文词典结束

侧栏文本预览文案键=tuple(中文.keys())#由中文词典键推导的键域
