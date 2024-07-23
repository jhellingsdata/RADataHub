
ge_1924_2024_agg[, Conservative_seat_share := Conservative_Seats/Total_Seats]
ge_1924_2024_agg[, Labour_seat_share := Labour_Seats/Total_Seats]

## rank of 2024 Conservative results:
ge_1924_2024_agg[, rank := rank(-Conservative_seat_share, na.last = T)]

ge_1924_2024_agg[year==2024,]$rank
nrow(ge_1924_2024_agg)

## plot seat share over time:

# Create a new column to indicate whether the year is 2024
ge_1924_2024_agg[, highlight := ifelse(year == 2024, "2024", "Other")]

ge_1924_2024_agg[, GE_Year := as.character(year)]
ge_1924_2024_agg[GE_Year=="1974.166", GE_Year := c("1974 - Feb")]
ge_1924_2024_agg[GE_Year=="1974.833", GE_Year := c("1974 - Oct")]

# Create the ggplot
ggplot(ge_1924_2024_agg, aes(x = reorder(GE_Year, Labour_seat_share), 
                             y = Labour_seat_share, fill = highlight)) +
  geom_bar(stat = "identity") +
  scale_fill_manual(values = c("2024" = "darkred", "Other" = "red")) +
  coord_flip() +
  geom_hline(yintercept = ge_1924_2024_agg[GE_Year==2024,]$Labour_seat_share, 
             linetype = "dashed", color = "black") +
  geom_text(aes(label = Labour_Leader), vjust = 0.5, size = 4, 
            angle = 0, hjust = -0.2) +
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, 0.80)) + # convert y-axis to percentage
  labs(title = "Keir Starmer vs Labour Leaders (1924 - 2024)",
       subtitle = "share of seats in the parliament",
       x = "General Election Year",
       y = "Seat Share",
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
ggsave("figures/F1 KeirStarmer_LabourLeaders_SeatShare_100years.jpeg", 
       width = 8, height = 6, dpi = 300)

