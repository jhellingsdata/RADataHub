
ge_1924_2024_agg[, Conservative_Party_VS := Conservative_Votes/Total_Votes]
ge_1924_2024_agg[, Labour_Party_VS := Labour_Votes/Total_Votes]
ge_1924_2024_agg[, Conservative_Share_Seats := Conservative_Seats/Total_Seats]
ge_1924_2024_agg[, Labour_Share_Seats := Labour_Seats/Total_Seats]

t2 <- ge_1924_2024_agg[, list(Labour_Leader_VS, Labour_Leader_VS_LastElection,
                              Labour_Party_VS, Labour_Share_Seats, Labour_Leader,
                              GE_Year)]
t2[, Labour_Leader_Year := paste(Labour_Leader, GE_Year, sep="; ")]
names(t2) <- gsub("Labour_", "", names(t2))
t2[, Party := c("Labour")]
t2[, Change_Party_VS := Party_VS - shift(Party_VS)]
t2[, Change_Share_Seats := Share_Seats - shift(Share_Seats)]
t2[, Change_Leader_VS := Leader_VS - Leader_VS_LastElection]
t2[, Leader_Year1 := sub("^[^ ]+ ", "", Leader_Year)]

t2[GE_Year==2024, LabelText := c("Starmer; 2024")]
t2[GE_Year==1997, LabelText := c("Blair; 1997")]

## Plot for Labour Leaders:
ggplot(t2, aes(x = Change_Leader_VS, y = Change_Share_Seats)) +
  geom_point(color= "red") +
  geom_text(aes(label = LabelText), vjust = -1, hjust = 1, size = 4, color = "red") +
  geom_hline(yintercept = 0, linetype = "dashed", color = "black") +
  geom_vline(xintercept = 0, linetype = "dashed", color = "black") +
  scale_x_continuous(labels = percent_format(accuracy = 1), limits = c(-0.25, 0.25)) + # convert y-axis to percentage
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(-0.50, 0.50)) + # convert y-axis to percentage
  labs(title = "Change in Seat Share vs Party Leader's Personal Vote Share",
       subtitle = "Labour Party (1924 - 2024)\nEach dot represents a general election",
       x = "Change in Party Leader's Vote Share\nin their own constituency\nfrom previous election",
       y = "Change in Seat Share\nin the parliament\nfrom previous election",
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
ggsave("figures/F3 Change_Labour_SeatShare_LeaderVoteShare_100years.jpeg", 
       width = 8, height = 6, dpi = 300)
