
library(data.table)
library(zoo)
library(readxl)
library(scales)
library(ggplot2)

## Set Working Directory:
setwd("/Users/finn/Documents/GitHub/RADataHub/Article Charts/election")

##################
## GE 2010
##################

ge_2010 <- read_excel("data/1918-2019election_results_by_pcon.xlsx",
                      sheet = "2010", skip = 3)

## Remove columns which are all NA:
ge_2010 <- ge_2010[,c(which(sapply(ge_2010, typeof)!="logical"))]

## Rename Columns:
names(ge_2010) <- c("ID", "Constituency", "County", "Region_or_Country", "Country", "ElectorateSize",
                    "Votes_CON", "VoteShare_CON", "Votes_LIBDEM", "VoteShare_LIBDEM",
                    "Votes_LAB", "VoteShare_LAB", "Votes_UKIP", "VoteShare_UKIP",
                    "Votes_GREEN", "VoteShare_GREEN", "Votes_SNP", "VoteShare_SNP",
                    "Votes_PLAID_CYMRU", "VoteShare_PLAID_CYMRU", "Votes_DUP", "VoteShare_DUP",
                    "Votes_SINN_FEIN", "VoteShare_SINN_FEIN", "Votes_SDLP", "VoteShare_SDLP",
                    "Votes_UUP", "VoteShare_UUP", "Votes_ALLIANCE", "VoteShare_ALLIANCE",
                    "Votes_OTHER", "VoteShare_OTHER", "VotesTotal", "Turnout")

setDT(ge_2010)

## Drop Notes at the end:
ge_2010 <- ge_2010[-which(is.na(ID)),]

## Party Name Winner:
t1 <- ge_2010[, list(VoteShare_CON, VoteShare_LIBDEM, VoteShare_LAB,
                     VoteShare_UKIP, VoteShare_GREEN, 
                     VoteShare_SNP, VoteShare_PLAID_CYMRU, VoteShare_DUP,
                     VoteShare_SINN_FEIN, VoteShare_SDLP,
                     VoteShare_UUP, VoteShare_ALLIANCE, VoteShare_OTHER)]

ge_2010[, PartyNameWinner := colnames(t1)[apply(t1,1,which.max)]]
ge_2010[, PartyNameWinner := gsub("VoteShare_", "", PartyNameWinner)]
ge_2010[, PartyNameRunnerUp := colnames(t1)[apply(t1,1,function(x)which(x==sort(x, decreasing = T)[2])[1])]]
ge_2010[, PartyNameRunnerUp := gsub("VoteShare_", "", PartyNameRunnerUp)]
ge_2010[, WinMargin := apply(t1, 1, FUN = function(x) x[order(x, decreasing = T)[1]]) - 
          apply(t1, 1, FUN = function(x) x[order(x, decreasing = T)[2]])]

## Create ENOP:
ge_2010[is.na(VoteShare_CON), VoteShare_CON := c(0)]
ge_2010[is.na(VoteShare_LIBDEM), VoteShare_LIBDEM := c(0)]
ge_2010[is.na(VoteShare_LAB), VoteShare_LAB := c(0)]
ge_2010[is.na(VoteShare_SNP), VoteShare_SNP := c(0)]
ge_2010[is.na(VoteShare_PLAID_CYMRU), VoteShare_PLAID_CYMRU := c(0)]
ge_2010[is.na(VoteShare_UKIP), VoteShare_UKIP := c(0)]
ge_2010[is.na(VoteShare_GREEN), VoteShare_GREEN := c(0)]
ge_2010[is.na(VoteShare_DUP), VoteShare_DUP := c(0)]
ge_2010[is.na(VoteShare_SINN_FEIN), VoteShare_SINN_FEIN := c(0)]
ge_2010[is.na(VoteShare_SDLP), VoteShare_SDLP := c(0)]
ge_2010[is.na(VoteShare_UUP), VoteShare_UUP := c(0)]
ge_2010[is.na(VoteShare_ALLIANCE), VoteShare_ALLIANCE := c(0)]
ge_2010[is.na(VoteShare_OTHER), VoteShare_OTHER := c(0)]

ge_2010[, ENOP := 1/(VoteShare_CON*VoteShare_CON + VoteShare_LIBDEM*VoteShare_LIBDEM
                     + VoteShare_LAB*VoteShare_LAB + VoteShare_SNP*VoteShare_SNP
                     + VoteShare_PLAID_CYMRU*VoteShare_PLAID_CYMRU
                     + VoteShare_UKIP*VoteShare_UKIP
                     + VoteShare_GREEN*VoteShare_GREEN
                     + VoteShare_DUP*VoteShare_DUP + VoteShare_SINN_FEIN*VoteShare_SINN_FEIN
                     + VoteShare_SDLP*VoteShare_SDLP + VoteShare_UUP*VoteShare_UUP
                     + VoteShare_ALLIANCE*VoteShare_ALLIANCE + VoteShare_OTHER*VoteShare_OTHER)]

## Election Year:
ge_2010[, GE_ElectionYear := c(2010)]

## Subset and save:
ge_2010 <- ge_2010[, list(ID, Constituency, County, Region_or_Country, Country, ElectorateSize,
                          Turnout, PartyNameWinner, PartyNameRunnerUp, WinMargin, GE_ElectionYear, 
                          VoteShare_CON, VoteShare_LAB, VoteShare_LIBDEM, VoteShare_SNP, 
                          VoteShare_GREEN, VoteShare_PLAID_CYMRU, VoteShare_UKIP, 
                          VoteShare_OTHER, ENOP)]
ge_2010[, VoteShare_Remaining := VoteShare_OTHER + VoteShare_GREEN + VoteShare_UKIP]


##################
## GE 2015
##################

ge_2015 <- read_excel("data/1918-2019election_results_by_pcon.xlsx",
                      sheet = "2015", skip = 3)

## Remove columns which are all NA:
ge_2015 <- ge_2015[,c(which(sapply(ge_2015, typeof)!="logical"))]

## Rename Columns:
names(ge_2015) <- c("ID", "Constituency", "County", "Region_or_Country", "Country", "ElectorateSize",
                    "Votes_CON", "VoteShare_CON", "Votes_LIBDEM", "VoteShare_LIBDEM",
                    "Votes_LAB", "VoteShare_LAB", "Votes_UKIP", "VoteShare_UKIP",
                    "Votes_GREEN", "VoteShare_GREEN", "Votes_SNP", "VoteShare_SNP",
                    "Votes_PLAID_CYMRU", "VoteShare_PLAID_CYMRU", "Votes_DUP", "VoteShare_DUP",
                    "Votes_SINN_FEIN", "VoteShare_SINN_FEIN", "Votes_SDLP", "VoteShare_SDLP",
                    "Votes_UUP", "VoteShare_UUP", "Votes_ALLIANCE", "VoteShare_ALLIANCE",
                    "Votes_OTHER", "VoteShare_OTHER", "VotesTotal", "Turnout")

setDT(ge_2015)

## Drop Notes at the end:
ge_2015 <- ge_2015[-which(is.na(ID)),]

## Party Name Winner:
t1 <- ge_2015[, list(VoteShare_CON, VoteShare_LIBDEM, VoteShare_LAB,
                     VoteShare_UKIP, VoteShare_GREEN, 
                     VoteShare_SNP, VoteShare_PLAID_CYMRU, VoteShare_DUP,
                     VoteShare_SINN_FEIN, VoteShare_SDLP,
                     VoteShare_UUP, VoteShare_ALLIANCE, VoteShare_OTHER)]

ge_2015[, PartyNameWinner := colnames(t1)[apply(t1,1,which.max)]]
ge_2015[, PartyNameWinner := gsub("VoteShare_", "", PartyNameWinner)]
ge_2015[, PartyNameRunnerUp := colnames(t1)[apply(t1,1,function(x)which(x==sort(x, decreasing = T)[2])[1])]]
ge_2015[, PartyNameRunnerUp := gsub("VoteShare_", "", PartyNameRunnerUp)]
ge_2015[, WinMargin := apply(t1, 1, FUN = function(x) x[order(x, decreasing = T)[1]]) - 
          apply(t1, 1, FUN = function(x) x[order(x, decreasing = T)[2]])]

## Create ENOP:
ge_2015[is.na(VoteShare_CON), VoteShare_CON := c(0)]
ge_2015[is.na(VoteShare_LIBDEM), VoteShare_LIBDEM := c(0)]
ge_2015[is.na(VoteShare_LAB), VoteShare_LAB := c(0)]
ge_2015[is.na(VoteShare_SNP), VoteShare_SNP := c(0)]
ge_2015[is.na(VoteShare_PLAID_CYMRU), VoteShare_PLAID_CYMRU := c(0)]
ge_2015[is.na(VoteShare_UKIP), VoteShare_UKIP := c(0)]
ge_2015[is.na(VoteShare_GREEN), VoteShare_GREEN := c(0)]
ge_2015[is.na(VoteShare_DUP), VoteShare_DUP := c(0)]
ge_2015[is.na(VoteShare_SINN_FEIN), VoteShare_SINN_FEIN := c(0)]
ge_2015[is.na(VoteShare_SDLP), VoteShare_SDLP := c(0)]
ge_2015[is.na(VoteShare_UUP), VoteShare_UUP := c(0)]
ge_2015[is.na(VoteShare_ALLIANCE), VoteShare_ALLIANCE := c(0)]
ge_2015[is.na(VoteShare_OTHER), VoteShare_OTHER := c(0)]

ge_2015[, ENOP := 1/(VoteShare_CON*VoteShare_CON + VoteShare_LIBDEM*VoteShare_LIBDEM
                     + VoteShare_LAB*VoteShare_LAB + VoteShare_SNP*VoteShare_SNP
                     + VoteShare_PLAID_CYMRU*VoteShare_PLAID_CYMRU
                     + VoteShare_UKIP*VoteShare_UKIP
                     + VoteShare_GREEN*VoteShare_GREEN
                     + VoteShare_DUP*VoteShare_DUP + VoteShare_SINN_FEIN*VoteShare_SINN_FEIN
                     + VoteShare_SDLP*VoteShare_SDLP + VoteShare_UUP*VoteShare_UUP
                     + VoteShare_ALLIANCE*VoteShare_ALLIANCE + VoteShare_OTHER*VoteShare_OTHER)]

## Election Year:
ge_2015[, GE_ElectionYear := c(2015)]

## Subset and save:
ge_2015 <- ge_2015[, list(ID, Constituency, County, Region_or_Country, Country, ElectorateSize,
                          Turnout, PartyNameWinner, PartyNameRunnerUp, WinMargin, GE_ElectionYear, 
                          VoteShare_CON, VoteShare_LAB, VoteShare_LIBDEM, VoteShare_SNP, 
                          VoteShare_GREEN, VoteShare_PLAID_CYMRU, VoteShare_UKIP, VoteShare_OTHER, ENOP)]
ge_2015[, VoteShare_Remaining := VoteShare_OTHER + VoteShare_GREEN + VoteShare_UKIP]


##################
## GE 2017
##################

ge_2017 <- read_excel("data/1918-2019election_results_by_pcon.xlsx",
                      sheet = "2017", skip = 3)

## Remove columns which are all NA:
ge_2017 <- ge_2017[,c(which(sapply(ge_2017, typeof)!="logical"))]

## Rename Columns:
names(ge_2017) <- c("ID", "Constituency", "County", "Region_or_Country", "Country", "ElectorateSize",
                    "Votes_CON", "VoteShare_CON", "Votes_LIBDEM", "VoteShare_LIBDEM",
                    "Votes_LAB", "VoteShare_LAB", "Votes_UKIP", "VoteShare_UKIP",
                    "Votes_GREEN", "VoteShare_GREEN", "Votes_SNP", "VoteShare_SNP",
                    "Votes_PLAID_CYMRU", "VoteShare_PLAID_CYMRU", "Votes_DUP", "VoteShare_DUP",
                    "Votes_SINN_FEIN", "VoteShare_SINN_FEIN", "Votes_SDLP", "VoteShare_SDLP",
                    "Votes_UUP", "VoteShare_UUP", "Votes_ALLIANCE", "VoteShare_ALLIANCE",
                    "Votes_OTHER", "VoteShare_OTHER", "VotesTotal", "Turnout")

setDT(ge_2017)

## Drop Notes at the end:
ge_2017 <- ge_2017[-which(is.na(ID)),]

## Party Name Winner:
t1 <- ge_2017[, list(VoteShare_CON, VoteShare_LIBDEM, VoteShare_LAB,
                     VoteShare_UKIP, VoteShare_GREEN, 
                     VoteShare_SNP, VoteShare_PLAID_CYMRU, VoteShare_DUP,
                     VoteShare_SINN_FEIN, VoteShare_SDLP,
                     VoteShare_UUP, VoteShare_ALLIANCE, VoteShare_OTHER)]

ge_2017[, PartyNameWinner := colnames(t1)[apply(t1,1,which.max)]]
ge_2017[, PartyNameWinner := gsub("VoteShare_", "", PartyNameWinner)]
ge_2017[, PartyNameRunnerUp := colnames(t1)[apply(t1,1,function(x)which(x==sort(x, decreasing = T)[2])[1])]]
ge_2017[, PartyNameRunnerUp := gsub("VoteShare_", "", PartyNameRunnerUp)]
ge_2017[, WinMargin := apply(t1, 1, FUN = function(x) x[order(x, decreasing = T)[1]]) - 
          apply(t1, 1, FUN = function(x) x[order(x, decreasing = T)[2]])]

## Create ENOP:
ge_2017[is.na(VoteShare_CON), VoteShare_CON := c(0)]
ge_2017[is.na(VoteShare_LIBDEM), VoteShare_LIBDEM := c(0)]
ge_2017[is.na(VoteShare_LAB), VoteShare_LAB := c(0)]
ge_2017[is.na(VoteShare_SNP), VoteShare_SNP := c(0)]
ge_2017[is.na(VoteShare_PLAID_CYMRU), VoteShare_PLAID_CYMRU := c(0)]
ge_2017[is.na(VoteShare_UKIP), VoteShare_UKIP := c(0)]
ge_2017[is.na(VoteShare_GREEN), VoteShare_GREEN := c(0)]
ge_2017[is.na(VoteShare_DUP), VoteShare_DUP := c(0)]
ge_2017[is.na(VoteShare_SINN_FEIN), VoteShare_SINN_FEIN := c(0)]
ge_2017[is.na(VoteShare_SDLP), VoteShare_SDLP := c(0)]
ge_2017[is.na(VoteShare_UUP), VoteShare_UUP := c(0)]
ge_2017[is.na(VoteShare_ALLIANCE), VoteShare_ALLIANCE := c(0)]
ge_2017[is.na(VoteShare_OTHER), VoteShare_OTHER := c(0)]

ge_2017[, ENOP := 1/(VoteShare_CON*VoteShare_CON + VoteShare_LIBDEM*VoteShare_LIBDEM
                     + VoteShare_LAB*VoteShare_LAB + VoteShare_SNP*VoteShare_SNP
                     + VoteShare_PLAID_CYMRU*VoteShare_PLAID_CYMRU
                     + VoteShare_UKIP*VoteShare_UKIP
                     + VoteShare_GREEN*VoteShare_GREEN
                     + VoteShare_DUP*VoteShare_DUP + VoteShare_SINN_FEIN*VoteShare_SINN_FEIN
                     + VoteShare_SDLP*VoteShare_SDLP + VoteShare_UUP*VoteShare_UUP
                     + VoteShare_ALLIANCE*VoteShare_ALLIANCE + VoteShare_OTHER*VoteShare_OTHER)]

## Election Year:
ge_2017[, GE_ElectionYear := c(2017)]

## Subset and save:
ge_2017 <- ge_2017[, list(ID, Constituency, County, Region_or_Country, Country, ElectorateSize,
                          Turnout, PartyNameWinner, PartyNameRunnerUp, WinMargin, GE_ElectionYear, 
                          VoteShare_CON, VoteShare_LAB, VoteShare_LIBDEM, VoteShare_GREEN,
                          VoteShare_SNP, VoteShare_PLAID_CYMRU, VoteShare_UKIP, 
                          VoteShare_OTHER, ENOP)]
ge_2017[, VoteShare_Remaining := VoteShare_OTHER + VoteShare_GREEN + VoteShare_UKIP]


##################
## GE 2019
##################

ge_2019 <- read_excel("data/1918-2019election_results_by_pcon.xlsx",
                      sheet = "2019", skip = 3)

## Remove columns which are all NA:
ge_2019 <- ge_2019[,c(which(sapply(ge_2019, typeof)!="logical"))]

## Rename Columns:
names(ge_2019) <- c("ID", "Constituency", "County", "Region_or_Country", "Country", "ElectorateSize",
                    "Votes_CON", "VoteShare_CON", "Votes_LAB", "VoteShare_LAB",
                    "Votes_LIBDEM", "VoteShare_LIBDEM", "Votes_BREXIT", "VoteShare_BREXIT",
                    "Votes_GREEN", "VoteShare_GREEN", "Votes_SNP", "VoteShare_SNP",
                    "Votes_PLAID_CYMRU", "VoteShare_PLAID_CYMRU", "Votes_DUP", "VoteShare_DUP",
                    "Votes_SINN_FEIN", "VoteShare_SINN_FEIN", "Votes_SDLP", "VoteShare_SDLP",
                    "Votes_UUP", "VoteShare_UUP", "Votes_ALLIANCE", "VoteShare_ALLIANCE",
                    "Votes_OTHER", "VoteShare_OTHER", "VotesTotal", "Turnout")

setDT(ge_2019)

## Drop Notes at the end:
ge_2019 <- ge_2019[-which(is.na(ID)),]

## Party Name Winner:
t1 <- ge_2019[, list(VoteShare_CON, VoteShare_LAB, VoteShare_LIBDEM,
                     VoteShare_BREXIT, VoteShare_GREEN, VoteShare_SNP,
                     VoteShare_PLAID_CYMRU, VoteShare_DUP,
                     VoteShare_SINN_FEIN, VoteShare_SDLP,
                     VoteShare_UUP, VoteShare_ALLIANCE, VoteShare_OTHER)]

ge_2019[, PartyNameWinner := colnames(t1)[apply(t1,1,which.max)]]
ge_2019[, PartyNameWinner := gsub("VoteShare_", "", PartyNameWinner)]
ge_2019[, PartyNameRunnerUp := colnames(t1)[apply(t1,1,function(x)which(x==sort(x, decreasing = T)[2])[1])]]
ge_2019[, PartyNameRunnerUp := gsub("VoteShare_", "", PartyNameRunnerUp)]
ge_2019[, WinMargin := apply(t1, 1, FUN = function(x) x[order(x, decreasing = T)[1]]) - 
          apply(t1, 1, FUN = function(x) x[order(x, decreasing = T)[2]])]

## Create ENOP:
ge_2019[is.na(VoteShare_CON), VoteShare_CON := c(0)]
ge_2019[is.na(VoteShare_LIBDEM), VoteShare_LIBDEM := c(0)]
ge_2019[is.na(VoteShare_LAB), VoteShare_LAB := c(0)]
ge_2019[is.na(VoteShare_SNP), VoteShare_SNP := c(0)]
ge_2019[is.na(VoteShare_PLAID_CYMRU), VoteShare_PLAID_CYMRU := c(0)]
ge_2019[is.na(VoteShare_BREXIT), VoteShare_BREXIT := c(0)]
ge_2019[is.na(VoteShare_GREEN), VoteShare_GREEN := c(0)]
ge_2019[is.na(VoteShare_DUP), VoteShare_DUP := c(0)]
ge_2019[is.na(VoteShare_SINN_FEIN), VoteShare_SINN_FEIN := c(0)]
ge_2019[is.na(VoteShare_SDLP), VoteShare_SDLP := c(0)]
ge_2019[is.na(VoteShare_UUP), VoteShare_UUP := c(0)]
ge_2019[is.na(VoteShare_ALLIANCE), VoteShare_ALLIANCE := c(0)]
ge_2019[is.na(VoteShare_OTHER), VoteShare_OTHER := c(0)]

ge_2019[, ENOP := 1/(VoteShare_CON*VoteShare_CON + VoteShare_LIBDEM*VoteShare_LIBDEM
                     + VoteShare_LAB*VoteShare_LAB + VoteShare_SNP*VoteShare_SNP
                     + VoteShare_PLAID_CYMRU*VoteShare_PLAID_CYMRU
                     + VoteShare_GREEN*VoteShare_GREEN
                     + VoteShare_BREXIT*VoteShare_BREXIT
                     + VoteShare_DUP*VoteShare_DUP + VoteShare_SINN_FEIN*VoteShare_SINN_FEIN
                     + VoteShare_SDLP*VoteShare_SDLP + VoteShare_UUP*VoteShare_UUP
                     + VoteShare_ALLIANCE*VoteShare_ALLIANCE + VoteShare_OTHER*VoteShare_OTHER)]

## Election Year:
ge_2019[, GE_ElectionYear := c(2019)]

## Subset and save:
ge_2019 <- ge_2019[, list(ID, Constituency, County, Region_or_Country, Country, ElectorateSize,
                          Turnout, PartyNameWinner, PartyNameRunnerUp, WinMargin, GE_ElectionYear, 
                          VoteShare_CON, VoteShare_LAB, VoteShare_LIBDEM, VoteShare_SNP,
                          VoteShare_GREEN, VoteShare_PLAID_CYMRU, VoteShare_BREXIT, 
                          VoteShare_OTHER, ENOP)]
setnames(ge_2019, "VoteShare_BREXIT", "VoteShare_UKIP")
ge_2019[, VoteShare_Remaining := VoteShare_OTHER + VoteShare_GREEN + VoteShare_UKIP]

######################
## Update 2019 with other variables:

## Muslim Share:
qdb_2019 <- setDT(read_excel("data/Religion_2021census.xlsx"))

qdb_2019_1 <- qdb_2019[,.(TotalPop = sum(Con_num, na.rm = T)),
                       by=list(ONSConstID)]
qdb_2019_2 <- qdb_2019[Religion=="Muslim", list(ONSConstID, Con_num)]
setnames(qdb_2019_2, "Con_num", "Muslim")

qdb_2019_1 <- merge(qdb_2019_1, qdb_2019_2, by=c("ONSConstID"), all.x = T)
qdb_2019_1[, ShareMuslimReligion := Muslim/TotalPop]
qdb_2019_1 <- qdb_2019_1[, list(ONSConstID, ShareMuslimReligion)]

nrow(ge_2019)
ge_2019 <- merge(ge_2019, qdb_2019_1, by.x=c("ID"),
                 by.y=c("ONSConstID"), all.x = T)
nrow(ge_2019)


##############################
## Get 2024:
##############################

ge_2024 <- setDT(read_excel("data/GE2024_results.xlsx"))
ge_2024[, GE_ElectionYear := c(2024)]

## Rename Columns:
setnames(ge_2024, old = names(ge_2024), new = sub("^(.*)_vote_share$", "VoteShare_\\1", names(ge_2024)))
setnames(ge_2024, old = names(ge_2024), new = sub("^(.*)_votes$", "Votes_\\1", names(ge_2024)))
setnames(ge_2024, "VoteShare_LD", "VoteShare_LIBDEM")
setnames(ge_2024, "Votes_LD", "Votes_LIBDEM")
setnames(ge_2024, "VoteShare_REF", "VoteShare_REFORM")
setnames(ge_2024, "Votes_REF", "Votes_REFORM")
setnames(ge_2024, "VoteShare_GRN", "VoteShare_GREEN")
setnames(ge_2024, "Votes_GRN", "Votes_GREEN")

## Total Votes:
ge_2024[, TotalVotes := rowSums(.SD, na.rm = T), .SDcols = names(ge_2024)[grep("Votes_", names(ge_2024))]]

## Vote Shares by 100:
cols_to_modify <- names(ge_2024)[grep("VoteShare_", names(ge_2024))]
ge_2024[, (cols_to_modify) := lapply(.SD, function(x) x / 100), .SDcols = cols_to_modify]

## Party Name Winner:
t1 <- ge_2024[, .SD, .SDcols = names(ge_2024)[grep("VoteShare_", names(ge_2024))]]

ge_2024[, PartyNameWinner := colnames(t1)[apply(t1,1,which.max)]]
ge_2024[, PartyNameWinner := gsub("VoteShare_", "", PartyNameWinner)]
ge_2024[, PartyNameRunnerUp := colnames(t1)[apply(t1,1,function(x)which(x==sort(x, decreasing = T)[2])[1])]]
ge_2024[, PartyNameRunnerUp := gsub("VoteShare_", "", PartyNameRunnerUp)]
ge_2024[, WinMargin := apply(t1, 1, FUN = function(x) x[order(x, decreasing = T)[1]]) - 
          apply(t1, 1, FUN = function(x) x[order(x, decreasing = T)[2]])]

cols_to_update <- names(ge_2024)[grep("Votes_|VoteShare_", names(ge_2024))]

# Apply the operation to each column
ge_2024[, (cols_to_update) := lapply(.SD, function(x) fifelse(is.na(x), 0, x)), 
        .SDcols = cols_to_update]

## Turnout:
ge_2024[, Turnout := TotalVotes/ElectorateSize]

## Update 2024 with Muslim Share:
ew_2024 <- setDT(read_excel("data/Demographic-data-for-new-parliamentary-constituencies-May-2024.xlsx", 
                            sheet = "EW_data", skip = 2))
setnames(ew_2024, "New constituency name", "Constituency_Name")
setnames(ew_2024, "Constituency value", "Value")
rel_muslim <- ew_2024[Topic=="Religion" & Variable=="Muslim", list(Constituency_Name, Value)]
setnames(rel_muslim, "Value", "ShareMuslimReligion")
rel_muslim[Constituency_Name=="Weston-super-Mare", Constituency_Name := c("Weston-Super-Mare")]

nrow(ge_2024)
ge_2024 <- merge(ge_2024, rel_muslim, by=c("Constituency_Name"), all.x = T)
nrow(ge_2024)

## Update information on incumbent:
load(file="data/GE_2024_Cand.rda")
setnames(ge_2024_cand, "Region", "Region_or_Country")
nrow(ge_2024)
ge_2024 <- merge(ge_2024, ge_2024_cand, by=c("Constituency_Name"), all.x = T)
nrow(ge_2024)

## Update information on Brexit referendum:
brexit <- setDT(read_excel("data/2016 Brexit referendum estimates on 2024 boundaries.xlsx"))
brexit[Constituen=="Weston-super-Mare", Constituen := c("Weston-Super-Mare")]

ge_2024[, VoteShare_Sans_C_L := 1 - VoteShare_CON - VoteShare_LAB - 
          VoteShare_LIBDEM - VoteShare_GREEN - VoteShare_REFORM]

ge_2024 <- merge(ge_2024, brexit, by.x=c("Constituency_Name"),
                 by.y=c("Constituen"), all.x = T)

ge_2010_2024 <- rbind(ge_2010, ge_2015, ge_2017, ge_2019, ge_2024, fill = T)

###########################################################
## Add Candidate Names:
###########################################################

## Top 4 Candidates in Conservative Leadership Contest 2022:
ge_2010_2024[Constituency %in% c("RICHMOND (YORKS)", "RICHMOND AND NORTHALLERTON") & GE_ElectionYear >= 2015, 
             CandidateName := c("Rishi Sunak")]
ge_2010_2024[Constituency=="PORTSMOUTH NORTH" & GE_ElectionYear >= 2010, 
             CandidateName := c("Penny Mordaunt")] ## present in election debate 2
ge_2010_2024[Constituency %in% c("SAFFRON WALDEN") & GE_ElectionYear %in% c(2017, 2019), 
             CandidateName := c("Kemi Badenoch")]
ge_2010_2024[Constituency %in% c("NORTH WEST ESSEX") & GE_ElectionYear==2024, 
             CandidateName := c("Kemi Badenoch")]
ge_2010_2024[Constituency %in% c("NORFOLK SOUTH WEST", "SOUTH WEST NORFOLK") 
             & GE_ElectionYear >= 2010, CandidateName := c("Liz Truss")]

## Other Conservative Candidates:
ge_2010_2024[Constituency %in% c("STRATFORD-ON-AVON")
             & GE_ElectionYear %in% c(2010, 2015, 2017, 2019), 
             CandidateName := c("Nadhim Zahawi")] ## standing down for 2024
ge_2010_2024[Constituency %in% c("TONBRIDGE AND MALLING", "TONBRIDGE & MALLING") 
             & GE_ElectionYear >= 2015, CandidateName := c("Tom Tugendhat")] ## From Tonbridge in 2024
ge_2010_2024[Constituency %in% c("SURREY SOUTH WEST", "SOUTH WEST SURREY") 
             & GE_ElectionYear >= 2010, CandidateName := c("Jeremy Hunt")] ## From Godalming and Ash in 2024
ge_2010_2024[Constituency %in% c("FAREHAM") & GE_ElectionYear >= 2015, 
             CandidateName := c("Suella Braverman")] ## From Fareham and Waterlooville in 2024

## potential names for future Tory leadership
## Priti Patel, Suella Braverman, Robert Jenrick, Kemi Badenoch, Penny Mordaunt and Grant Shapps
ge_2010_2024[Constituency %in% c("WITHAM") & GE_ElectionYear >= 2010, 
             CandidateName := c("Priti Patel")]
ge_2010_2024[Constituency %in% c("NEWARK") & GE_ElectionYear >= 2015, 
             CandidateName := c("Robert Jenrick")]
ge_2010_2024[Constituency %in% c("WELWYN HATFIELD") & GE_ElectionYear >= 2010, 
             CandidateName := c("Grant Shapps")]

## Top Candidates from Labour Party
ge_2010_2024[Constituency %in% c("HOLBORN & ST PANCRAS", "HOLBORN AND ST PANCRAS")
             & GE_ElectionYear >= 2015, CandidateName := c("Keir Starmer")] ## party leader
ge_2010_2024[Constituency %in% c("ASHTON UNDER LYNE", "ASHTON-UNDER-LYNE")
             & GE_ElectionYear >= 2015, CandidateName := c("Angela Rayner")] ## present in election debate 2
ge_2010_2024[Constituency %in% c("LEEDS WEST", "LEEDS WEST AND PUDSEY")
             & GE_ElectionYear >= 2010, CandidateName := c("Rachel Reeves")]
ge_2010_2024[Constituency %in% c("NORMANTON, PONTEFRACT AND CASTLEFORD", 
                                 "NORMANTON, PONTEFRACT & CASTLEFORD",
                                 "PONTEFRACT, CASTLEFORD AND KNOTTINGLEY")
             & GE_ElectionYear >= 2010, CandidateName := c("Yvette Cooper")]
ge_2010_2024[Constituency %in% c("TOTTENHAM") & GE_ElectionYear >= 2010, 
             CandidateName := c("David Lammy")]
ge_2010_2024[Constituency %in% c("RAWMARSH AND CONISBROUGH", "WENTWORTH AND DEARNE",
                                 "WENTWORTH & DEARNE") & GE_ElectionYear >= 2010, 
             CandidateName := c("John Healey")]
ge_2010_2024[Constituency %in% c("WOLVERHAMPTON SOUTH EAST") & GE_ElectionYear >= 2010, 
             CandidateName := c("Pat McFadden")]
ge_2010_2024[Constituency %in% c("BIRMINGHAM, LADYWOOD", "BIRMINGHAM LADYWOOD") & GE_ElectionYear >= 2010, 
             CandidateName := c("Shabana Mahmood")]
ge_2010_2024[Constituency %in% c("ILFORD NORTH") & GE_ElectionYear >= 2010, 
             CandidateName := c("Wes Streeting")]
ge_2010_2024[Constituency %in% c("HOUGHTON AND SUNDERLAND SOUTH", "HOUGHTON & SUNDERLAND SOUTH")
             & GE_ElectionYear >= 2010, 
             CandidateName := c("Bridget Phillipson")]
ge_2010_2024[Constituency %in% c("DONCASTER NORTH") & GE_ElectionYear >= 2010, 
             CandidateName := c("Ed Miliband")]
ge_2010_2024[Constituency %in% c("LEICESTER WEST") & GE_ElectionYear >= 2010, 
             CandidateName := c("Liz Kendall")]
ge_2010_2024[Constituency %in% c("SHEFFIELD, HEELEY", "SHEFFIELD HEELEY") & GE_ElectionYear >= 2010, 
             CandidateName := c("Louise Haigh")]
ge_2010_2024[Constituency %in% c("STALYBRIDGE AND HYDE", "STALYBRIDGE & HYDE") & GE_ElectionYear >= 2010, 
             CandidateName := c("Jonathan Reynolds")]
ge_2010_2024[Constituency %in% c("HOVE AND PORTSLADE", "HOVE") & GE_ElectionYear >= 2010, 
             CandidateName := c("Peter Kyle")]
ge_2010_2024[Constituency %in% c("CROYDON NORTH", "STREATHAM AND CROYDON NORTH") & GE_ElectionYear >= 2010, 
             CandidateName := c("Steve Reed")]

## Top Candidates from Liberal Democrats Party
ge_2010_2024[Constituency %in% c("KINGSTON AND SURBITON", "KINGSTON & SURBITON")
             & GE_ElectionYear >= 2015, CandidateName := c("Ed Davey")] ## party leader
ge_2010_2024[Constituency %in% c("ST ALBANS") & GE_ElectionYear >= 2017, 
             CandidateName := c("Daisy Cooper")] ## present in election debate 2
ge_2010_2024[Constituency %in% c("SUSSEX MID") & GE_ElectionYear == 2015, 
             CandidateName := c("Daisy Cooper")] ## present in election debate 2
ge_2010_2024[Constituency %in% c("SUFFOLK COASTAL") & GE_ElectionYear == 2010, 
             CandidateName := c("Daisy Cooper")] ## present in election debate 2

## Top Candidates from Reform UK Party
ge_2010_2024[Constituency %in% c("CLACTON") & GE_ElectionYear >= 2024, 
             CandidateName := c("Nigel Farage")] ## party leader

## Top Candidates from SNP
ge_2010_2024[Constituency %in% c("ABERDEEN SOUTH") & GE_ElectionYear >= 2019, 
             CandidateName := c("Stephen Flynn")] ## party leader

## Top Candidates from Green Party
ge_2010_2024[Constituency %in% c("WAVENEY VALLEY") & GE_ElectionYear >= 2024, 
             CandidateName := c("Adrian Ramsay")] ## party co-leader
ge_2010_2024[Constituency %in% c("BRISTOL WEST") & GE_ElectionYear==2019, 
             CandidateName := c("Carla Denyer")] ## party co-leader
ge_2010_2024[Constituency %in% c("BRISTOL CENTRAL") & GE_ElectionYear==2024, 
             CandidateName := c("Carla Denyer")] ## party co-leader


#################################################################
#### DATA FOR OLDER ELECTIONS
#################################################################

## Save Cumulative Data for older elections:
ge_1924_1951_agg <- 
  data.table(year = c(1924, 1929, 1931, 1935, 1945, 1950, 1951),
             Total_Seats = c(615, 615, 615, 615, 640, 625, 625),
             Conservative_Seats = c(412, 260, 470, 386, 197, 298, 321),
             Conservative_Leader = c("Stanley Baldwin", "Stanley Baldwin", 
                                     "Stanley Baldwin", "Stanley Baldwin",
                                     "Winston Churchill", "Winston Churchill", 
                                     "Winston Churchill"),
             Conservative_Leader_VS = c(1, 0.629, 1, 1,
                                        0.7253, 0.5961, 0.6296),
             Conservative_Leader_VS_LastElection = c(0.673, 1, 0.629, 1,
                                                     0.590, 0.7253, 0.5961),
             Labour_Seats = c(151, 287, 52, 154, 393, 315, 295),
             Labour_Leader = c("Ramsay MacDonald", "Ramsay MacDonald", 
                               "Arthur Henderson", "Clement Attlee",
                               "Clement Attlee", "Clement Attlee",
                               "Clement Attlee"),
             Labour_Leader_VS = c(0.531, 0.725, 0.4303, 0.665,
                                  0.838, 0.6046, 0.6679),
             Labour_Leader_VS_LastElection = c(0.556, 0.531, 0.462, 0.505,
                                               0.665, 0.838, 0.6046),
             PM_BeforeElection = c("Ramsay MacDonald", "Stanley Baldwin", 
                                   "Ramsay MacDonald", "Ramsay MacDonald", 
                                   "Winston Churchill", "Clement Attlee", 
                                   "Clement Attlee"),
             PM_BeforeElection_VoteShare = c(0.531, 0.629, 0.55, 0.318, 0.7253, 
                                             0.6046, 0.6679),
             PM_BeforeElection_WinMargin = c(0.062, 0.356, 0.113, -0.364, 0.45, 
                                             0.347, 0.3358),
             Party_BeforeElection = c("Labour", "Conservative", 
                                      "National Labour", "National Labour", 
                                      "Conservative", "Labour", 
                                      "Labour"),
             Electorate = c(20592487, 28421729, 26962509, 29523893, 33067342, 34292162, 34620574),
             Total_Votes = c(15856215, 21685779, 20599357, 20991488, 24073025, 28771124, 28596594),
             Conservative_Votes = c(7418983, 8252527, 11377022, 10025083, 8716211, 12492404, 13717850),
             Labour_Votes = c(5281626, 8048968, 6081826, 7984988, 11967746, 13266176, 13948883))

ge_1955_2019_agg <- 
  data.table(year = c(1955, 1959, 1964, 1966, 1970, 1974.166, 1974.833, 1979,
                      1983, 1987, 1992, 1997, 2001, 2005, 2010, 2015, 2017, 2019),
             Total_Seats = c(630, 630, 630, 630, 630, 635, 635, 635,
                             650, 650, 651, 659, 659, 646, 650, 650,
                             650, 650),
             Conservative_Seats = c(345, 365, 304, 253, 330, 297, 277, 339,
                                    397, 376, 336, 165, 166, 198, 306, 330,
                                    317, 365),
             Conservative_Leader = c("Anthony Eden", "Harold Macmillan", 
                                     "Alec Douglas-Home", "Edward Heath",
                                     "Edward Heath", "Edward Heath",
                                     "Edward Heath", "Margaret Thatcher",
                                     "Margaret Thatcher", "Margaret Thatcher",
                                     "John Major", "John Major", 
                                     "William Hague", "Michael Howard",
                                     "David Cameron", "David Cameron",
                                     "Theresa May", "Boris Johnson"),
             Conservative_Leader_VS = c(0.6448, 0.70, 0.666, 0.481,
                                        0.530, 0.491, 0.505, 0.525,
                                        0.511, 0.539, 0.662, 0.553,
                                        0.589, 0.539, 0.588, 0.602,
                                        0.648, 0.526),
             Conservative_Leader_VS_LastElection = c(0.6048, 0.682, 0.574, 0.474,
                                                     0.481, 0.530, 0.491, 0.44,
                                                     0.525, 0.511, 0.636, 0.662,
                                                     0.489, 0.450, 0.493, 0.588,
                                                     0.658, 0.508),
             Labour_Seats = c(277, 258, 317, 364, 288, 301, 319, 269,
                              209, 229, 271, 418, 412, 355, 258, 232, 262,
                              202),
             Labour_Leader = c("Clement Attlee", "Hugh Gaitskell", 
                               "Harold Wilson", "Harold Wilson", 
                               "Harold Wilson", "Harold Wilson", 
                               "Harold Wilson", "James Callaghan",
                               "Michael Foot", "Neil Kinnock",
                               "Neil Kinnock", "Tony Blair",
                               "Tony Blair", "Tony Blair",
                               "Gordon Brown", "Ed Miliband", 
                               "Jeremy Corbyn", "Jeremy Corbyn"),
             Labour_Leader_VS = c(0.6573, 0.586, 0.639, 0.664,
                                  0.631, 0.567, 0.608, 0.593,
                                  0.700, 0.713, 0.743, 0.712,
                                  0.649, 0.589, 0.645, 0.524,
                                  0.73, 0.643),
             Labour_Leader_VS_LastElection = c(0.6679, 0.6515, 0.549, 0.639,
                                               0.664, 0.631, 0.567, 0.520,
                                               0.692, 0.594, 0.713, 0.605,
                                               0.712, 0.649, 0.581, 0.473,
                                               0.602, 0.73),
             PM_BeforeElection = c("Winston Churchill", "Harold Macmillan",
                                   "Alec Douglas-Home", "Harold Wilson",
                                   "Harold Wilson", "Edward Heath",
                                   "Harold Wilson", "James Callaghan",
                                   "Margaret Thatcher", "Margaret Thatcher",
                                   "John Major", "John Major", 
                                   "Tony Blair", "Tony Blair", 
                                   "Gordon Brown", "David Cameron",
                                   "Theresa May", "Theresa May"),
             PM_BeforeElection_VoteShare = c(0.7302, 0.70, 0.66, 0.664, 0.631, 0.491,
                                             0.608, 0.593, 0.511, 0.539, 0.662, 0.553,
                                             0.649, 0.589, 0.645, 0.602, 0.648, 0.577),
             PM_BeforeElection_WinMargin = c(0.4604, 0.40, 0.478, 0.338, 0.292, 0.233,
                                             0.31, 0.216, 0.243, 0.222, 0.493, 0.318,
                                             0.44, 0.445, 0.502, 0.43, 0.455, 0.333),
             Party_BeforeElection = c("Conservative", "Conservative",
                                      "Conservative", "Labour",
                                      "Labour", "Conservative",
                                      "Labour", "Labour",
                                      "Conservative", "Conservative",
                                      "Conservative", "Conservative",
                                      "Labour", "Labour", 
                                      "Labour", "Conservative",
                                      "Conservative", "Conservative"),
             Electorate = c(34843397, 35403624, 35918374, 35969323, 39313242,
                            39748708, 40094923, 41080739, 42188634, 43199971,
                            43261356, 43879781, 44389534, 44215814, 45603078,
                            46231212, 46808407, 47414262),
             Total_Votes = c(26759729, 	27862652, 27657148, 27264747, 28305534,
                             31321982, 29189104, 31221362, 30671137, 32529578,
                             33614074, 31286284, 26367383, 27148510, 29687604,
                             30697525, 32204184, 32014110),
             Conservative_Votes = c(13310891, 13750875, 12002642, 11418455, 13145123,
                                    11872180, 10462565, 13697923, 13012316,
                                    13760583, 14093007, 9600943, 8357615, 8784915,
                                    10703754, 11299609, 13636684, 13966454),
             Labour_Votes = c(12405254, 12216172, 12205808, 13096629, 12208758,
                              11645616, 11457079, 11532218, 8456934, 10029807,
                              11560484, 13518167, 10724953, 9552436, 8609527,
                              9347273, 12877918, 10269051))


ge_2024_agg <- data.table(year = c(2024),
                          Total_Seats = c(650),
                          Conservative_Seats = c(121),
                          Conservative_Leader = c("Rishi Sunak"),
                          Conservative_Leader_VS = c(0.475),
                          Conservative_Leader_VS_LastElection = c(0.636),
                          Labour_Seats = c(411),
                          Labour_Leader = c("Keir Starmer"),
                          Labour_Leader_VS = c(0.489),
                          Labour_Leader_VS_LastElection = c(0.645),
                          PM_BeforeElection = c("Rishi Sunak"),
                          PM_BeforeElection_VoteShare = c(0.475),
                          PM_BeforeElection_WinMargin = c(0.251),
                          Party_BeforeElection = c("Conservative"),
                          Electorate = c(47558348),
                          Total_Votes = c(28792897),
                          Conservative_Votes = c(6827112),
                          Labour_Votes = c(9731363))

ge_1924_2024_agg <- rbind(ge_1924_1951_agg, ge_1955_2019_agg, ge_2024_agg)

ge_1924_2024_agg[, GE_Year := as.character(year)]
ge_1924_2024_agg[GE_Year=="1974.166", GE_Year := c("1974 - Feb")]
ge_1924_2024_agg[GE_Year=="1974.833", GE_Year := c("1974 - Oct")]


##################################################################
## SUMMARY STATISTICS:

## Labour Victory Margin in constituencies gained this time:
summary(ge_2024[IncumbentLabour==0 & PartyNameWinner=="LAB",]$WinMargin)

write.csv(ge_2010, "intermediate/ge_2010.csv", row.names = FALSE)
write.csv(ge_2015, "intermediate/ge_2015.csv", row.names = FALSE)
write.csv(ge_2017, "intermediate/ge_2017.csv", row.names = FALSE)
write.csv(ge_2019, "intermediate/ge_2019.csv", row.names = FALSE)
write.csv(ge_2024, "intermediate/ge_2024.csv", row.names = FALSE)
write.csv(ge_2010_2024, "intermediate/ge_2010_2024.csv", row.names = FALSE)
write.csv(ge_1924_2024_agg, "intermediate/ge_1924_2024_agg.csv", row.names = FALSE)
