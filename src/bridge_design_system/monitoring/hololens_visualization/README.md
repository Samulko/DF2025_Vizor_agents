# HoloLens三圆交互可视化系统

用于Talk-Create-Build人机协作建造系统的实时参数可视化和交互控制界面

# 项目概述
本项目是一个专为HoloLens AR设备设计的三圆圈动态可视化系统，具备完全透明背景，圆圈悬浮在现实环境中，采用电竞动感风格。通过读取JSON数据实时更新圆圈大小和动画效果，为用户提供直观的参数可视化体验。

## 快速开始

### 系统要求
- **目标设备：** HoloLens 2（主要）+ 桌面浏览器（测试）
- **浏览器：** Edge、Chrome 90+、Safari 14+
- **文件协议：** 支持file://本地文件访问

### 启动步骤

**1. 确认数据文件存在**
```bash
# 确保存在主数据文件
ls src/bridge_design_system/monitoring/design_profile.json
```

**2. 启动应用**
- **HoloLens：** 浏览器打开 `file:///path/to/monitoring/hololens_visualization/index.html`
- **桌面测试：** 直接双击 `index.html` 文件

**3. 验证系统状态**
- 启动时：数字和圆圈同步随机变化（每0.5秒变2次）
- 连接成功：数字锁定，圆圈缓慢过渡到目标大小
- 稳定状态：数字静止，圆圈轻微呼吸浮动
- 数据更新：显示"Updated N times"计数器

## 🎯 系统功能

### 三圆圈动态显示
- **Weight（红色）：** 显示Self-Weight参数 (0-100)
- **Storage（黄色）：** 显示Storage参数 (0-100)  
- **Complexity（蓝色）：** 显示Complexity参数 (0-100)

### 系统状态说明
- **状态1：初始化** - 数字和圆圈同步随机变化（每0.5秒变2次）
- **状态2：数据锁定** - 数字锁定，圆圈过渡
- **状态3：稳定监听** - 数字静止，圆圈呼吸浮动
- **状态4：数据更新** - 数字切换，圆圈重新过渡，更新计数器

### 透明背景AR体验
- 页面背景完全透明
- 圆圈直接悬浮在真实环境画面上
- 适配HoloLens全屏或无边框浏览器模式

### 物理碰撞效果
- 圆圈边缘碰撞检测和轻微弹开效果
- 碰撞时触发视觉强调效果
- 增强AR环境下的真实感

### 透明度变化
- 圆圈保持固有颜色（红色、黄色、蓝色）
- 数值越低，透明度越高（最低20%透明度）
- 无连接中断状态，无红色警告

## 📊 数据接口

### 数据文件格式
系统读取 `../../design_profile.json` 文件：
```json
{
    "Self-Weight": 20,      // 0-100 整数，对应红色圆圈
    "Storage": 60,          // 0-100 整数，对应黄色圆圈  
    "Complexity": 20,       // 0-100 整数，对应蓝色圆圈
    "timestamp": 1640995200000  // Unix时间戳，用于变化检测
}
```

### 数据更新机制
- **轮询频率：** 每500ms检查文件变化（仅在稳定状态时）
- **变化检测：** 通过timestamp比较判断数据更新
- **实时响应：** 检测到变化时数字即时切换，圆圈重新过渡
- **更新计数：** 显示"Updated N times"指示器

## 🔧 故障排除

### 常见问题

1. **圆圈不显示**
   - 检查浏览器控制台是否有错误
   - 确认SVG元素是否正确创建
   - 验证配置文件路径是否正确

2. **动画不工作**
   - 检查CSS文件是否正确加载
   - 确认JavaScript文件加载顺序
   - 查看控制台是否有JavaScript错误

3. **数据不更新**
   - 检查design_profile.json文件路径
   - 确认数据格式是否正确
   - 验证字段映射配置

### 调试模式
在浏览器控制台执行：
```javascript
localStorage.setItem('debug', 'true');
location.reload();
```

## 🎮 使用指南

### 基础操作
1. **启动系统：** 打开index.html文件
2. **观察状态：** 系统自动进入初始化状态
3. **等待连接：** 成功读取数据后进入稳定状态
4. **监控变化：** 系统自动检测数据文件变化

### 状态观察
- **启动时：** 数字和圆圈同步随机变化（每0.5秒变2次）
- **连接成功：** 数字锁定，圆圈缓慢过渡到目标大小
- **稳定状态：** 数字静止，圆圈轻微呼吸浮动
- **数据更新：** 数字即时切换，圆圈重新过渡，更新计数器

## 🔗 与Geometry Agent集成

### 数据映射关系
- Self-Weight (0-100) → Number of Layer/height (6-14)
- Storage (0-100) → XY Size (3-13)
- Complexity (0-100) → Rotation Value (0-90)

### 工作流程
1. 用户调整参数 → HoloLens界面显示新数值
2. 保存数据 → 下载新的design_profile.json
3. 文件替换 → 用户手动替换原文件
4. Agent响应 → Geometry Agent检测文件变化
5. 模型生成 → 自动生成3个比例的3D模型(1.0x, 1.2x, 0.8x)

## 📁 项目结构

```
bridge_design_system/
├── monitoring/
│   ├── design_profile.json              # 🔗 数据接口文件
│   └── hololens_visualization/          # 🆕 本项目
│       ├── index.html                   # 主入口页面
│       ├── assets/
│       │   ├── css/                     # 样式文件
│       │   ├── js/                      # JavaScript模块
│       │   │   ├── core/                # 核心系统模块
│       │   │   ├── animation/           # 🆕 统一动画管理
│       │   │   │   ├── animationManager.js    # 主动画管理器
│       │   │   │   ├── collisionDetector.js   # 物理碰撞检测
│       │   │   │   └── animationUtils.js      # 动画工具函数
│       │   │   └── utils/               # 工具函数
│       │   └── config/                  # 配置文件
│       └── docs/
│           ├── README.md                # 本文件
│           └── plan.md                  # 开发计划
```

## 🛠️ 技术规格

**框架：** 原生JavaScript，无外部依赖
**渲染：** SVG图形，60fps性能
**数据：** JSON文件轮询，500ms更新间隔
**兼容性：** HoloLens 2, Chrome 90+, Edge 90+
**文件大小：** <500KB总体积
**响应时间：** <50ms状态切换延迟
**背景：** 完全透明，AR悬浮效果
**动画同步：** 数字和圆圈完全同步（每0.5秒变2次）
**物理效果：** 圆圈边缘碰撞检测和弹开效果

## 📞 支持与反馈

**项目团队：** Talk-Create-Build
**技术文档：** 详见plan.md开发文档
**问题反馈：** 通过Issues提交

---

**版本：** v1.1.0-Unified-Animation
**最后更新：** 2025年7月6日
**数据接口：** design_profile.json
**设备支持：** HoloLens 2
**开发阶段：** Phase 1 - 统一动画管理器驱动的动态可视化