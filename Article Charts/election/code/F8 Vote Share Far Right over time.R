
t1 <- ge_2010_2024[, list(VoteShare_UKIP, VoteShare_REFORM,
                          GE_ElectionYear)]

t1 <- melt(t1, id.vars = "GE_ElectionYear")
t1[, variable := gsub("VoteShare_", "", variable)]
t1 <- t1[value!=0,]
t1 <- t1[!(GE_ElectionYear==2024 & variable=="UKIP"),]

# Custom colors
candidate_colors <- c(
  "REFORM" = "purple",
  "LAB" = "red",
  "CON" = "#0073e6",
  "LIBDEM" = "yellow",
  "GREEN" = "green",
  "UKIP" = "#DDA0DD"
)

# Custom labels for the legend
legend_labels <- c(
  "CON" = "Conservative",
  "LAB" = "Labour",
  "LIBDEM" = "Liberal\nDemocrats",
  "SNP" = "SNP",
  "Sans_C_L" = "Others",
  "GREEN" = "Green",
  "REFORM" = "Reform UK",
  "UKIP" = "UKIP"
)


ggplot(t1, aes(x = as.factor(GE_ElectionYear), y = value, fill=variable, label = variable)) +
  geom_boxplot() +
  coord_flip() +
  scale_y_continuous(labels = percent_format(accuracy = 1)) + # convert y-axis to percentage
  scale_fill_manual(values = candidate_colors, labels = legend_labels) +
  labs(title = "Constituency Level Far Right Vote Share Over Time",
       x = "General Election Year",
       y = "Vote Share",
       caption = "Credits: Apurav Bhatiya, University of Birmingham") +
  theme_minimal() +
  theme(legend.position = "bottom", legend.title = element_blank(),
        title = element_text(size = 14),
        axis.text.x = element_text(size = 14),  # Increase x-axis label and tick font size
        axis.text.y = element_text(size = 14),  # Increase y-axis label and tick font size
        axis.title.x = element_text(size = 14),  # Increase x-axis title font size
        axis.title.y = element_text(size = 14),   # Increase y-axis title font size
        plot.caption = element_text(hjust = 0, face = "italic", size = 8)
  )
ggsave("figures/F8 VoteShare_FarRight_OverTime.jpeg", 
       width = 8, height = 6, dpi = 300)

