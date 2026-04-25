This script support adding these parameters to comicinfo.xml

To understanding the format
1. 1st row: parameter name, each of them in input_v*.xlsx, comicinfo_v*.py, and comicinfo.xml are same
2. 2nd row: defenition in kavita wiki, https://wiki.kavitareader.com/guides/metadata/comics/
3. 3rd row: specific format or default format if there is no key-in value
4. 4th row: remarks from dev or users

| Comicicinfo | Kavita | Format | Remarks |
|:---        |:---    |:---    |:---     |
| Title | Chapter Title | No specific format | No remarks yet |
| Series | Name | No specific format | No remarks yet |
| Number | Issue/Chapter number | No specific format | No remarks yet |
| Count | Publication Status | No specific format | No remarks yet |
| Summary | Summary| No specific format | No remarks yet |
| Year, Month, Day | Release Date | Integer | No remarks yet |
| Writer | Writer | No specific format | Maybe effect by word encoding |
| Penciller, Inker, Colorist, Letterer, CoverArtist, Editor | Penciller, Inker, Colorist, Letterer, CoverArtist, Editor | Default leave blank | No remarks yet |
| Publisher | Publisher | No specific format | No remarks yet |
| Genre | Genres | No specific format | No remarks yet |
| Tags | Tags | No specific format | If you also keep epub, tags of epub equals to Genre(s) in Kavita |
| Web | Web Links (Also used for matching in CBLs) | No specific format | No remarks yet |
| PageCount | Length (This is aggregated on the Series) | Default leave blank | No remarks yet |
| LanguageISO | Language | ja, zh-Hant(Traditional Chinese), zh-Hans(Simplified Chinese) etc. | No remarks yet |
| Format | Special | Default value is "Digital" | No remarks yet |
| BlackAndWhite | Kavita's wiki does not define this, but comicinfo define as colour type | Default value is "No" | No remarks yet |
| Manga | Kavita's wiki does not define this, but comicinfo define as ebook type | Default value is "YesAndRightToLeft" | No remarks yet |
| Characters | Characters(not shown in wiki) | No specific format | No remarks yet |
| Teams | Teams or Circle(not shown in wiki) | No specific format | No remarks yet |
| AgeRating | Age Rating | See below | No remarks yet |

Age Rating should follow format below, the series take the highest Age Rating(aka most mature).
- Unknown
- Rating Pending
- Early Childhood
- Everyone
- G
- Everyone 10+
- PG
- Kids to Adults
- Teen
- MA15+
- Mature 17+
- M
- R18+
- Adults Only 18+
- X18+
### Highly Recommend Using:
- Unknown
- Rating Pending
- G
- PG
- M
- R18+