setwd("~/Downloads/SaccadeTask/")
data = data.frame()
for (file in dir()) {
  pid = unlist(strsplit(file, "_"))[2]
  d = read.delim(file,header=T)
  d = d[d$event_details=="RESULT",]
  d$pid = rep(pid, nrow(d))
  data = rbind(data,d)
}
write.table(data, "allData.log", row.names=F)