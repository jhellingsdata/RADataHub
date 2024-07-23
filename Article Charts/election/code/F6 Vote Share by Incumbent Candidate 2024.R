
ge_2024[, Seat_Labour := ifelse(PartyNameWinner=="LAB", 1, 0)]
ge_2024[, Seat_Conservative := ifelse(PartyNameWinner=="CON", 1, 0)]
ge_2024[, Seat_LibDem := ifelse(PartyNameWinner=="LIBDEM", 1, 0)]
ge_2024[, Seat_Other := ifelse(PartyNameWinner!="LAB" & 
                                 PartyNameWinner!="CON" & 
                                 PartyNameWinner!="LIBDEM" , 1, 0)]

t1 <- ge_2024[IncumbentLabourCand==1 & IncumbentLabour==1,
              .(Seat_CON = mean(Seat_Conservative, na.rm = T),
                Seat_LAB = mean(Seat_Labour, na.rm = T),
                Seat_Other = mean(Seat_Other, na.rm = T),
                Seat_LibDem = mean(Seat_LibDem, na.rm = T))]
t1[, Type := c("Labour\nIncumbent Candidate\nRe-Contesting")]
t1 <- melt(t1, id.vars = "Type")
t1$descrip <- c("Conservative Gain", "Labour Retain", "Other Gain", "Liberal Democrats Gain")

t2 <- ge_2024[IncumbentLabourCand==0 & IncumbentLabour==1,
              .(Seat_CON = mean(Seat_Conservative, na.rm = T),
                Seat_LAB = mean(Seat_Labour, na.rm = T),
                Seat_Other = mean(Seat_Other, na.rm = T),
                Seat_LibDem = mean(Seat_LibDem, na.rm = T))]
t2[, Type := c("Labour\nIncumbent Candidate\nNot Re-Contesting")]
t2 <- melt(t2, id.vars = "Type")
t2$descrip <- c("Conservative Gain", "Labour Retain", "Other Gain", "Liberal Democrats Gain")

t3 <- ge_2024[IncumbentConservativeCand==1 & IncumbentConservative==1,
              .(Seat_CON = mean(Seat_Conservative, na.rm = T),
                Seat_LAB = mean(Seat_Labour, na.rm = T),
                Seat_Other = mean(Seat_Other, na.rm = T),
                Seat_LibDem = mean(Seat_LibDem, na.rm = T))]
t3[, Type := c("Conservative\nIncumbent Candidate\nRe-Contesting")]
t3 <- melt(t3, id.vars = "Type")
t3$descrip <- c("Conservative Retain", "Labour Gain", "Other Gain", "Liberal Democrats Gain")

t4 <- ge_2024[IncumbentConservativeCand==0 & IncumbentConservative==1,
              .(Seat_CON = mean(Seat_Conservative, na.rm = T),
                Seat_LAB = mean(Seat_Labour, na.rm = T),
                Seat_Other = mean(Seat_Other, na.rm = T),
                Seat_LibDem = mean(Seat_LibDem, na.rm = T))]
t4[, Type := c("Conservative\nIncumbent Candidate\nNot Re-Contesting")]
t4 <- melt(t4, id.vars = "Type")
t4$descrip <- c("Conservative Retain", "Labour Gain", "Other Gain", "Liberal Democrats Gain")


t5 <- rbind(t1, t2, t3, t4)

t5[, value := round(value*100, 0)]
t5[grep("_CON", variable), party_color := rep("#0073e6", 4)]
t5[grep("_LAB", variable), party_color := rep("red", 4)]
t5[grep("_Other", variable), party_color := rep("gray", 4)]
t5[grep("_LibDem", variable), party_color := rep("orange", 4)]

# Custom labels for the legend
legend_labels <- c(
  "CON" = "Conservative",
  "LAB" = "Labour",
  "Sans_C_L" = "Others"
)

t5[, description := paste(descrip, ": ", value, "%", sep = "")]

# Create the ggplot
ggplot(t5[grep("Seat_", variable),], 
       aes(x = as.factor(Type), y = value, fill = variable, label = variable)) +
  geom_bar(stat = "identity", position = "dodge", width = 0.75) +
  coord_flip() +
  scale_fill_manual(values = setNames(t5[grep("Seat_", variable),]$party_color, 
                                      t5[grep("Seat_", variable),]$variable), 
                    labels = legend_labels) +
  geom_text(aes(label = description), position = position_dodge(width = 0.75), 
            vjust = +0.5, size = 4, angle = 0, hjust = -0.05) +
  ylim(0,130) +
  labs(title = "Share of Seats Gained/Retained by Incumbency Status",
       x = "",
       y = "",
       caption = "Credits: Apurav Bhatiya, University of Birmingham") +
  theme_minimal() +
  theme(legend.position = "none", legend.title = element_blank(),
        title = element_text(size = 14),
        axis.text.x = element_text(size = 14),  # Increase x-axis label and tick font size
        axis.text.y = element_text(size = 14),  # Increase y-axis label and tick font size
        axis.title.x = element_text(size = 14),  # Increase x-axis title font size
        axis.title.y = element_text(size = 14),   # Increase y-axis title font size
        plot.caption = element_text(hjust = 0, face = "italic", size = 8)
  )
ggsave("figures/F6 IncumbentCand_SeatRedistribution_2024.jpeg", 
       width = 8, height = 6, dpi = 300)

