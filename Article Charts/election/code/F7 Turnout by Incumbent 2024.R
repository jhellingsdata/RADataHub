
ge_2024[, IncumbentStatus := ifelse(IncumbentLabour==1, "Labour\nIncumbent",
                                           ifelse(IncumbentConservative==1, "Conservative\nIncumbent",
                                                  ""))]


# Create the ggplot with box plot
ggplot(ge_2024[(IncumbentLabour==1) |
                 (IncumbentConservative==1)], 
       aes(x = as.factor(IncumbentStatus), y = Turnout)) +
  geom_boxplot(aes(fill = as.factor(IncumbentStatus))) +
  coord_flip() +
  scale_fill_manual(values = c("Labour\nIncumbent" = "red",
                               "Conservative\nIncumbent" = "#0073e6")) +
  scale_y_continuous(labels = percent_format(accuracy = 1)) + # convert y-axis to percentage
  labs(title = "Turnout by Incumbency Status",
       x = "",
       y = "Turnout",
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
ggsave("figures/F7 IncumbentParty_Turnout_2024.jpeg", 
       width = 8, height = 6, dpi = 300)

