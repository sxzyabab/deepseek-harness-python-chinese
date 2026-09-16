
__all__=['中文','英文','图像预览键']#仅中文公开名

中文={
    'title':'图片',
    'preview':'图片预览：{name}',
    'loading':'正在读取…',
    'failed':'无法显示这张图片',
    'unsupported':'图片预览需要完整文件内容',
}

图像预览键=tuple(中文.keys())

英文={
    'title':'Image',
    'preview':'Image preview: {name}',
    'loading':'Reading…',
    'failed':'This image could not be displayed.',
    'unsupported':'Image preview requires the complete file contents.',
}
