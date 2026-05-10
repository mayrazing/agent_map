# 项目地图强制规则
找文件,找测试,找配置,排查功能,修改功能前，必须先用项目地图定位。禁止跳过地图直接搜源码,测试,配置或具体业务文件。

## 不用搜地图的情况
- 文件就在当前工作目录第一层，并且用户已经明确点名这个文件，可以直接打开或修改。
  - 例子:`AGENTS.md`、`map.py`。
  - 这个例外只适用于当前工作目录第一层文件；不适用于任何子目录里的文件。
- 用户直接提供了包含路径分隔符（`/`）的文件路径，可直接打开，无需搜地图。
  - 例子:`src/components/Foo.jsx`、`backend/service/UserService.java`
- 当前对话上下文中已有 `ide_opened_file` 标签指向该文件，路径已知，可直接打开。
- 本次会话已读过该文件（路径在上下文中），可直接操作，无需重新定位。
- 用户描述的文件名在项目中唯一（如组件名、类名），允许跳过第一跳，直接搜对应格式桶的 `code-index.json`。

## 必须搜地图的情况
- 需要进入任意文件夹查找。
- 需要搜索源码目录、测试目录、配置目录或具体业务文件。
- 用户只描述功能现象，未明确给出当前工作目录第一层文件名。
- 不确定目标文件在哪里。

会话开始时，先静默更新项目地图:
`rtk python3 map.py >/dev/null 2>&1 && echo "map.py done" || echo "map.py failed"`

要求:
- 只输出 `map.py done` 或 `map.py failed`
- 不把地图内容或脚本详细输出放进对话上下文
- 更新失败不阻断会话，后续仍按地图流程先查

## 强制查询顺序
### 1. 第一跳:只能搜小地图
首次定位命令的搜索目标只能是:
`.project-index/project-map.json`

格式:
`rtk rg "关键词1|关键词2|关键词3|...|关键词X" .project-index/project-map.json`

禁止第一跳搜索:
- 任意源码目录
- 任意测试目录
- 任意配置文件
- 任意具体业务文件
- `.project-index/<格式>/code-index.json`
- 多个目标混搜

### 2. 第二跳:只能搜详细索引
只有小地图命中后，才允许搜详细索引。
根 `.project-index/project-map.json` 里的 `buckets` 会指向各格式桶；第二跳必须按命中文件格式选择对应桶里的 `code-index.json`。

格式:
`rtk rg "候选路径|类名|函数名|关键词" .project-index/<格式>/code-index.json`

常用格式桶示例:
- `.jsx` 文件:`.project-index/jsx/code-index.json`
- `.js` 文件:`.project-index/js/code-index.json`
- `.java` 文件:`.project-index/java/code-index.json`
- `.xml` 文件:`.project-index/xml/code-index.json`
- `.yaml/.yml` 文件:`.project-index/yaml/code-index.json`
- `.properties` 文件:`.project-index/properties/code-index.json`
- `.sql` 文件:`.project-index/sql/code-index.json`
- `.css` 文件:`.project-index/css/code-index.json`

跨格式问题允许第二跳查多个格式桶，但每条命令的搜索目标仍只能是一个桶的 `code-index.json`。

例子:
`rtk rg "Settings|updateSettings|保存" .project-index/jsx/code-index.json`
`rtk rg "Settings|updateSettings" .project-index/java/code-index.json`
`rtk rg "UserSettingsMapper|update" .project-index/xml/code-index.json`

### 3. 第三跳:只打开候选文件
根据小地图和详细索引命中结果，挑最相关的候选文件（最多不超过 10 个），只读这些文件。
格式:
`rtk sed -n '1,220p' 候选文件`

## 直接搜源码的例外
只有以下情况允许直接搜源码,测试,配置或业务文件:
- 小地图无命中
- 重新运行 `map.py` 后仍无命中
- 已通过地图确定候选目录，且搜索范围缩到候选文件或候选小目录
- 用户明确要求做地图流程与直接源码搜索的 A/B token 对比
- 搜索目标是「值/内容」而非「名字」:代码索引只收录命名符号（函数名、组件名、类名、变量名），不收录具体值。凡搜索目标是 CSS class、字面字符串、数字常量、注释文字等「内容」时，地图必然无命中，直接搜源码。

## 地图定位失败处理
如果地图定位失败:
1. 先重新生成地图:
   `rtk python3 map.py >/tmp/pick_word_map.log 2>&1 && echo "map.py done" || echo "map.py failed"`
2. 再按强制查询顺序查一次
3. 如果仍然找不到，再正常使用 `rg`,`find`,打开文件定位

## 地图收益质疑处理
正常任务只走地图流程，不为了证明收益而额外跑“不用地图”的对照搜索。

当用户质疑地图是否省 token,要求证明,要求测试对比时，允许按同一真实任务跑一次 A/B 对照:
1. A 组:按地图流程执行，记录每条工具输出里的 `Original token count`
2. B 组:不用地图，直接在相关源码目录执行一次等价关键词搜索，记录工具输出里的 `Original token count`
3. 对比公式:`节省率 = (B 组 token - A 组 token) / B 组 token`

汇报时必须说明:B 组对照搜索本身会浪费 token，这次执行只为回应质疑和做对比；平时正常排查不要跑 B 组。

汇报用语必须区分:
- `直接搜源码对照值`:实际跑 B 组得到的数
- `地图定位实际值`:实际跑 A 组得到的数
- 禁止把对照值说成固定收益或全局收益，只能说“本次对比”

## 绝对禁止
- 直接 `cat .project-index/project-map.json`
- 直接 `cat .project-index/*/code-index.json`
- 第一跳直接搜源码,测试,配置或业务文件
- 第一跳把多个搜索目标混在一起
- 第二跳把详细索引和源码目录混在一起
- 第二跳搜索 `.project-index/*/code-index.json`
- 第二跳把多个格式桶混在一条命令里

