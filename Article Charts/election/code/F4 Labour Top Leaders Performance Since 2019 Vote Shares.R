
t1 <- ge_2010_2024[CandidateName %in% c("Keir Starmer", "Angela Rayner",
                                        "Rachel Reeves", "Yvette Cooper",
                                        "David Lammy", "Wes Streeting", 
                                        "Bridget Phillipson")
                   & GE_ElectionYear>=2019,]


# Custom colors
red_shades <- c(
  "#ff9999", "#ff8080","#ff6666", "#ff4d4d",
  "#ff3333", "#ff1a1a", "#e60000")

# Create the ggplot
ggplot(t1, aes(x = factor(GE_ElectionYear, levels = c(2019, 2024)), 
               y = VoteShare_LAB, fill = CandidateName, label = CandidateName)) +
  geom_bar(stat = "identity", position = "dodge", width = 0.75) +
  coord_flip() +
  scale_fill_manual(values = red_shades) +
  geom_text(aes(label = CandidateName), position = position_dodge(width = 0.75), 
            vjust = +0.5, size = 4, angle = 0, hjust = -0.2) +
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, 1)) + # convert y-axis to percentage
  labs(title = "Labour Party Prominent Candidates Over Years",
       subtitle = "vote shares of candidates in their constituency",
       x = "General Election Year",
       y = "Vote Share",
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
ggsave("figures/F4 LeadersPerformanceOverYears_Labour.jpeg", 
       width = 8, height = 6, dpi = 300)

