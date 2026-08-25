[app]

# 应用元信息
title = 复古数独
package.name = sudoku
package.domain = org.local

# 源码与资源目录
source.dir = .
source.include_exts = py,ttf,png,jpg

# 版本号
version = 1.0

# 运行时依赖(仅 kivy 与标准库)
requirements = python3,kivy

# 竖屏应用
orientation = portrait

# iOS 上键盘弹出时不缩放窗口(避免布局错乱)
fullscreen = 0

# 入口脚本(与 main.py 一致)
# kivy-ios 默认会找 main.py,如需自定义可在此指定
# entry = main.py

[ios]

# 目标架构:仅 arm64(兼容所有 64 位 iPhone/iPad)
arch = arm64

# 最低支持 iOS 版本:iOS 14+
ios.deploy.min_ios_version = 14.0

# 应用图标(可选,需准备 1024x1024 png 放到项目根目录)
# icon.filename = icon.png

# 启动画面(可选)
# presplash.filename = presplash.png

[buildozer]

# 构建时是否使用 ccache 加速重编译
log_level = 2
warn_on_root = 1
