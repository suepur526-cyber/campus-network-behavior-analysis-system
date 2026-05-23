# 基于 Python 的校园网用户行为分析系统

本项目是一个面向毕业设计和答辩演示的校园网用户行为分析系统。系统围绕校园网日志数据展开，提供日志接入、数据清洗、行为统计、异常检测、可视化展示、日志查询、CSV 导出、目录采集和测试报告等完整功能。

系统采用 Python + Flask 技术栈开发，默认使用 SQLite 数据库，便于本地运行和答辩演示；也支持通过 `DATABASE_URL` 切换到 MySQL。项目业务逻辑保持清晰，功能链路是真实可运行的端到端流程。

## 一、项目功能

- 管理员登录、退出登录和受保护页面访问控制。
- 默认管理员账号初始化。
- 支持 CSV、JSON、TXT 和类 Syslog 文本日志解析。
- 支持日志字段标准化、时间格式转换、数值异常修正、缺失字段补齐和重复记录去除。
- 支持手动上传日志文件并导入数据库。
- 支持生成验证数据并导入系统。
- 支持从 `data/ingest` 目录采集日志文件。
- 目录采集支持文件名和 SHA256 哈希去重，避免重复导入。
- 总览仪表盘展示日志总数、用户数、总流量和异常数量。
- 用户行为分析包括：
  - 流量趋势
  - 访问热力图
  - 协议分布
  - 访问类别分布
  - 用户类型分布
  - 应用分布
  - 用户画像
  - 用户流量排行
- 异常检测包括：
  - 基于规则的高频连接、异常大流量、端口扫描、可疑访问检测
  - 基于 KMeans 和 Isolation Forest 的机器学习异常检测
- 异常告警列表支持分页展示。
- 日志查询支持关键词、用户类型、协议和异常状态筛选。
- 支持按当前查询条件导出 CSV 文件。
- 支持 Matplotlib 静态流量趋势图接口。
- 支持系统状态和测试报告展示。
- 提供 pytest 自动化测试，覆盖核心后端功能和 API 流程。

## 二、技术栈

- Python 3.11
- Flask
- Flask-SQLAlchemy
- SQLite，默认本地数据库
- MySQL，可通过 `DATABASE_URL` 切换
- Pandas
- NumPy
- scikit-learn
- KMeans
- Isolation Forest
- Matplotlib
- ECharts
- HTML / CSS / JavaScript
- pytest

## 三、项目结构

```text
.
+-- app/
|   +-- __init__.py
|   +-- config.py
|   +-- models.py
|   +-- routes.py
|   +-- services/
|   |   +-- analytics.py
|   |   +-- anomaly.py
|   |   +-- auth.py
|   |   +-- cleaning.py
|   |   +-- collector.py
|   |   +-- importer.py
|   |   +-- log_parser.py
|   |   +-- sample_data.py
|   |   +-- status.py
|   +-- static/
|   +-- templates/
+-- data/
|   +-- ingest/
+-- docs/
+-- tests/
+-- conftest.py
+-- requirements.txt
+-- run.py
```

## 四、快速启动

安装依赖：

```powershell
python -m pip install -r requirements.txt
```

初始化数据库：

```powershell
$env:FLASK_APP = "run.py"
flask init-db
```

生成样例日志并执行异常检测：

```powershell
flask seed-data
flask detect-anomalies
```

启动系统：

```powershell
python run.py
```

访问地址：

```text
http://127.0.0.1:5000/login
```

默认管理员账号：

```text
用户名：admin
密码：admin123
```

## 五、主要页面

| 页面 | 地址 | 说明 |
|:--|:--|:--|
| 登录页面 | `/login` | 管理员登录认证 |
| 总览仪表盘 | `/` | 查看日志总量、用户数量、流量趋势和异常概况 |
| 日志接入 | `/import` | 上传日志、生成验证数据、导入数据库 |
| 日志查询 | `/logs` | 日志筛选、分页查询和 CSV 导出 |
| 行为分析 | `/analysis` | 用户行为统计、热力图、用户画像和排行 |
| 异常检测 | `/anomalies` | 执行异常检测并查看告警列表 |
| 测试报告 | `/report` | 查看系统状态、质量指标、性能指标和测试用例 |

## 六、数据库配置

系统默认使用 SQLite：

```text
campus_network.db
```

如果需要切换到 MySQL，可以先创建数据库：

```sql
CREATE DATABASE campus_network CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

然后配置环境变量：

```powershell
$env:DATABASE_URL = "mysql+pymysql://root:your_password@127.0.0.1:3306/campus_network?charset=utf8mb4"
$env:SECRET_KEY = "replace-with-a-random-secret"
$env:FLASK_APP = "run.py"
flask init-db
flask seed-data
flask detect-anomalies
python run.py
```

如果不设置 `DATABASE_URL`，系统会自动使用 SQLite。

## 七、测试方式

运行自动化测试：

```powershell
pytest -q
```

当前本地验证结果：

```text
17 passed
```

测试覆盖内容包括：

- 页面路由渲染
- 健康检查接口
- 登录和退出登录
- 未登录访问保护
- 样例数据生成
- CSV / JSON / TXT 日志解析
- 数据清洗与去重
- 数据库导入
- 行为分析 API
- 日志筛选查询
- CSV 导出
- 异常检测
- 目录采集
- 系统状态和测试报告接口

## 八、答辩演示建议

推荐演示顺序：

1. 使用管理员账号登录系统。
2. 打开总览仪表盘，介绍日志数量、用户数量、流量趋势和异常数量。
3. 打开日志接入页面，演示生成验证数据或上传日志文件。
4. 打开日志查询页面，演示筛选、分页和 CSV 导出。
5. 打开行为分析页面，说明流量趋势、协议分布、访问热力图、用户画像和用户排行。
6. 打开异常检测页面，点击执行异常检测。
7. 说明规则检测和机器学习检测的区别。
8. 打开测试报告页面，展示系统状态、质量指标、性能指标和测试用例结果。
9. 如需证明系统可运行，可现场执行 `pytest -q`。

## 九、真实部署说明

- 正式部署时应设置强随机 `SECRET_KEY`。
- 多用户或长期运行场景建议使用 MySQL 或 PostgreSQL。
- 真实校园网日志应先进行脱敏处理，避免泄露用户隐私。
- 真实设备日志可通过定时任务、Rsyslog、Filebeat 等方式放入采集目录。
- 对公网部署时建议配置 HTTPS、反向代理、访问控制和数据备份。

## 十、说明

本系统是毕业设计项目，重点展示校园网日志数据从接入、清洗、分析、异常检测到可视化展示的完整流程。系统没有直接接入真实校园网设备，但使用结构化验证日志覆盖典型访问行为和异常场景，能够完整验证系统功能链路。
