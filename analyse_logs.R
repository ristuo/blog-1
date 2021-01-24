library(data.table)
suppressMessages(library(lubridate))
options(width=300)
df <- fread("logs.csv")
article_reads <- df[article != ""]
article_reads$datetime <- with_tz(as.POSIXct(article_reads$time, tz="GMT"), "Europe/Helsinki")
article_reads$date <- as.Date(article_reads$datetime)
reads_per_article <- article_reads[, .N, by = list(date, article)]
print(reads_per_article[order(date)])


