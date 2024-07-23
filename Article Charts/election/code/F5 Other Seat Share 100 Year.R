
ge_1924_2024_agg[, Other_seat_share := (Total_Seats - Conservative_Seats - Labour_Seats)/Total_Seats]

## rank of 2024 Conservative results:
ge_1924_2024_agg[, rank := rank(-Other_seat_share, na.last = T)]

ge_1924_2024_agg[year==2024,]$rank
nrow(ge_1924_2024_agg)

## plot seat share over time:

# Create a new column to indicate whether the year is 2024
ge_1924_2024_agg[, highlight := ifelse(year == 2024, "2024", "Other")]

ge_1924_2024_agg[, GE_Year := as.character(year)]
ge_1924_2024_agg[GE_Year=="1974.166", GE_Year := c("1974 - Feb")]
ge_1924_2024_agg[GE_Year=="1974.833", GE_Year := c("1974 - Oct")]

# Create the ggplot
ggplot(ge_1924_2024_agg, aes(x = reorder(GE_Year, Other_seat_share), 
                             y = Other_seat_share, fill = highlight)) +
  geom_bar(stat = "identity") +
  scale_fill_manual(values = c("2024" = "darkgrey", "Other" = "lightgray")) +
  coord_flip() +
  labs(title = "Seat Share of Parties Other Than\nConservative and Labour (1924 - 2024)",
       x = "General Election Year",
       y = "Seat Share in Parliament",
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
ggsave("figures/F5 Other_SeatShare_100years.jpeg", 
       width = 8, height = 6, dpi = 300)

