此腳本支援將這些參數加入comicinfo.xml

理解其格式
1. 第一欄：參數名稱，每一個在input_v*.xlsx、comicinfo_v*.py、comicinfo.xml都是一樣的
2. 第二欄：Kavita wiki提供的定義，https://wiki.kavitareader.com/guides/metadata/comics/
3. 第三欄：指定格式或無輸入值時的預設格式，存在多元素時，預設用英文逗點分割
4. 第四欄：開發人員或用戶們的備註

| Comicinfo參數名稱 | Kavita對應欄位 | 格式 | 備註 |
|:---|:---|:---|:---|
| Title | 標題 | 無指定格式 | 暫無備註 |
| Series | 系列 | 無指定格式 | 暫無備註 |
| Number | 章節數 | 無指定格式 | 暫無備註 |
| Count | 出版狀況 | 無指定格式 | 暫無備註 |
| Summary | 結語 | 無指定格式 | 暫無備註 |
| Year, Month, Day | 出版日期 | 整數 | 暫無備註 |
| Writer | 作者 | 無指定格式 | [已確認受文字編碼影響](/%23問題排查手冊與comicinfo.xml備份/002.編碼錯誤.md) |
| Penciller, Inker, Colorist, Letterer, CoverArtist, Editor | Penciller, Inker, Colorist, Letterer, CoverArtist, Editor | 預設留空 | 暫無備註 |
| Publisher | 出版商 | 無指定格式 | 暫無備註 |
| Genre | 類型 | 無指定格式 | 暫無備註 |
| Tags | 標籤 | 無指定格式 | 如果你也持有epub，epub的「標籤」等同於Kavita的「類型」」 |
| Web | 網頁連結 | 無指定格式 | 暫無備註 |
| PageCount | 頁數、長度（此為系列數據的總和） | 預設留空 | 暫無備註 |
| LanguageISO | 語言 | 常用代碼範例「ja」（日文）「zh-Hant」（繁體中文）「zh-Hans」（簡體中文） | 暫無備註 |
| Format | 格式（直譯是特殊） | 預設值是「Digital」（電子品） | 暫無備註 |
| BlackAndWhite | Kavita的wiki沒給定義，但comicinfo定為顏色種類 | 預設值是「No」 | 暫無備註 |
| Manga | Kavita的wiki沒給定義，但comicinfo定為電子書種類 | 預設值是「YesAndRightToLeft」 | 暫無備註 |
| Characters | 角色（wiki沒列出） | 無指定格式 | 暫無備註 |
| Teams | 團隊或社團（wiki沒列出） | 無指定格式 | 暫無備註 |
| AgeRating | 年齡分級 | 參考下方 | 暫無備註 |

年齡分級應該遵照下方格式，系列會採計最高等級的年齡分級（換言之，年齡最成熟）。
- Unknown（未知）
- Rating Pending（待分級）
- Early Childhood（幼兒）
- Everyone（全年齡）
- G（普遍級）
- Everyone 10+
- PG（建議家長指導）
- Kids to Adults
- Teen（青少年）
- MA15+（15+）
- Mature 17+（17+）
- M（成熟）
- R18+（限制級）
- Adults Only 18+
- X18+（成人）
### 強烈推薦使用以下分級（澳洲分級）：
- Unknown
- Rating Pending
- G
- PG
- M
- R18+