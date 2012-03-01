require(lattice)
require(latticeExtra)
setwd("~/Downloads/SaccadeTask/")
data = read.table('allData.log', header=T)
respAccuracy = aggregate(data$correct,list(data$pid,data$mode),mean)
colnames(respAccuracy) = c("pid","mode","respAccuracy")
p1 = xyplot(respAccuracy~mode,groups=pid,respAccuracy,type="l", auto.key=list(space="right"))
sacDirFreq = aggregate(data$X1st_saccade_direction, list(data$pid, data$mode), table)
sacDirFreq$left = sacDirFreq[3]$x[,1]
sacDirFreq$none = sacDirFreq[3]$x[,2]
sacDirFreq$right = sacDirFreq[3]$x[,3]
sacDirFreq[3] = NULL
colnames(sacDirFreq) = c("pid","mode","left","none","right")
sacDirFreq = reshape(sacDirFreq, idvar=c("pid","mode"), varying=list(3:5), direction="long")
rownames(sacDirFreq) = NULL
colnames(sacDirFreq) = c("pid","mode","direction","count")
sacDirFreq$direction = factor(sacDirFreq$direction, labels=c("left","none","right"))
p2 = barchart(count~direction|mode,groups=pid,sacDirFreq,type="l",auto.key=list(space="right"))
data$cue_lure = ifelse(data$X1st_saccade_direction=="left"&data$cue_side=="left",1,
                       ifelse(data$X1st_saccade_direction=="right"&data$cue_side=="right",1,
                              ifelse(data$X1st_saccade_direction=="none",-1,0)
                              )
                       )
data$controlledSaccade = ifelse(data$cue_lure==1&data$mode=="pro",1,ifelse(data$cue_lure==0&data$mode=="anti",1,ifelse(data$cue_lure==-1,-1,0)))
p3 = useOuterStrips(histogram(~controlledSaccade|pid+mode,data,scales=list(x=list(at=c(-1,0,1)))))
data.noNone = data[data$X1st_saccade_direction!="none",]
respAccuracy.noNone = aggregate(data.noNone$correct,list(data.noNone$pid,data.noNone$mode),mean)
sacAccuracy.noNone = aggregate(data.noNone$controlledSaccade,list(data.noNone$pid,data.noNone$mode),mean)
respAccuracy.noNone$sacAccuracy = sacAccuracy.noNone$x
colnames(respAccuracy.noNone) = c("pid","mode","respAccuracy","sacAccuracy")
respAccuracy.noNone$id = paste(respAccuracy.noNone$pid,respAccuracy.noNone$mode, sep="")
respAccuracy.noNone$color = ifelse(respAccuracy.noNone$mode=="anti",2,3)
respAccuracy.noNone$shape = rep(0:(length(unique(respAccuracy.noNone$pid))-1),2)
p4 = xyplot(respAccuracy~sacAccuracy,groups=id,respAccuracy.noNone,pch=respAccuracy.noNone$shape,col=respAccuracy.noNone$color,cex=2,lwt=2)


print(p1, position=c(0,.66,1,1), more=T)
print(p2, position=c(0,.33,1,.66), more=T)
print(p3, position=c(0,0,1,.33))