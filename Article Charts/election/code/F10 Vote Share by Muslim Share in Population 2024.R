
ge_2019[, Seat_Labour := ifelse(PartyNameWinner=="LAB", 1, 0)]
ge_2019[, VoteShare_Sans_C_L := 1 - VoteShare_CON - VoteShare_LAB]

## Assemble All Data Together:
ge_2024[, Seat_Labour := ifelse(PartyNameWinner=="LAB", 1, 0)]
ge_2024[, VoteShare_Sans_C_L := 1 - VoteShare_CON - VoteShare_LAB]

t1 <- ge_2024[!is.na(ShareMuslimReligion), 
              list(GE_ElectionYear, ShareMuslimReligion, VoteShare_CON, 
                   VoteShare_LAB, VoteShare_Sans_C_L, Seat_Labour)]
t2 <- ge_2019[!is.na(ShareMuslimReligion), 
              list(GE_ElectionYear, ShareMuslimReligion, VoteShare_CON, 
                   VoteShare_LAB, VoteShare_Sans_C_L, Seat_Labour)]

combined_data <- rbind(t1, t2)

# Bin ShareMuslimReligion into intervals and calculate midpoints
bin_width <- 0.10
combined_data[, ShareMuslimReligion_bin := cut(ShareMuslimReligion, 
                                               breaks = seq(0, max(ShareMuslimReligion) + bin_width, by = bin_width), 
                                               include.lowest = TRUE)]
combined_data[, ShareMuslimReligion_mid := (as.numeric(sub("[\\[(](.+),.*", "\\1", as.character(ShareMuslimReligion_bin))) + 
                                              as.numeric(sub(".*,([^]]*)\\]", "\\1", as.character(ShareMuslimReligion_bin)))) / 2]

combined_data[ShareMuslimReligion_mid>0.425, ShareMuslimReligion_mid := c(0.425)]
# Compute the average vote shares within each bin
combined_data_avg <- combined_data[, .(VoteShare_CON = mean(VoteShare_CON, na.rm = T),
                                       VoteShare_LAB = mean(VoteShare_LAB, na.rm = T),
                                       VoteShare_Sans_C_L = mean(VoteShare_Sans_C_L, na.rm = T)),
                                   by = list(ShareMuslimReligion_mid, GE_ElectionYear)]


# Convert the averaged data.table to long format
t1_long_avg <- melt(combined_data_avg[GE_ElectionYear==2024,], id.vars = "ShareMuslimReligion_mid", 
                    measure.vars = c("VoteShare_CON", "VoteShare_LAB",
                                     "VoteShare_Sans_C_L"),
                    variable.name = "Party", value.name = "VoteShare")

t1_long_avg[Party=="VoteShare_CON", Party := c("Conservative")]
t1_long_avg[Party=="VoteShare_LAB", Party := c("Labour")]
t1_long_avg[Party=="VoteShare_Sans_C_L", Party := c("Others")]

t2_long_avg <- melt(combined_data_avg[GE_ElectionYear==2019,], id.vars = "ShareMuslimReligion_mid", 
                    measure.vars = c("VoteShare_CON", "VoteShare_LAB", 
                                     "VoteShare_Sans_C_L"),
                    variable.name = "Party", value.name = "VoteShare")

party_colors <- c("Conservative" = "#0073e6",  
                  "Labour" = "red",
                  "Others" = "lightgray")  

# Create the stacked area plot
ggplot(t1_long_avg, aes(x = ShareMuslimReligion_mid, y = VoteShare, fill = Party)) +
  geom_area(alpha = 0.6, size = 0.5, colour = "white") +
  scale_fill_manual(values = party_colors) +
  geom_line(data = subset(combined_data_avg[GE_ElectionYear==2019,], ShareMuslimReligion_mid >= min(t1_long_avg$ShareMuslimReligion_mid) & 
                            ShareMuslimReligion_mid <= max(t1_long_avg$ShareMuslimReligion_mid)), 
            aes(x = ShareMuslimReligion_mid, y = VoteShare_Sans_C_L, fill = NULL), color = "black") +
  geom_line(data = subset(combined_data_avg[GE_ElectionYear==2019,], ShareMuslimReligion_mid >= min(t1_long_avg$ShareMuslimReligion_mid) & 
                            ShareMuslimReligion_mid <= max(t1_long_avg$ShareMuslimReligion_mid)), 
            aes(x = ShareMuslimReligion_mid, y = VoteShare_Sans_C_L + VoteShare_LAB, fill = NULL), color = "black") +
  labs(x = "Share of Muslim Population", y = "Average Vote Share", title = "Average Vote Share by Party and Share of Muslim Population") +
  labs(title = "Party Vote Shares by Share of Muslim Population",
       subtitle = "Black lines show outcomes from the 2019 General Election",
       x = "Share of Muslim Population",
       y = "Party Vote Share",
       caption = "Notes: The figure presents data for England and Wales only.\nData Source: https://commonslibrary.parliament.uk/constituency-boundary-review-data-for-new-constituencies/\nCredits: Apurav Bhatiya, University of Birmingham") +
  scale_x_continuous(labels = percent_format(accuracy = 1)) + # convert x-axis to percentage
  scale_y_continuous(labels = percent_format(accuracy = 1)) + # convert y-axis to percentage
  theme_minimal() +
  theme(legend.position = "bottom", legend.title = element_blank(),
        title = element_text(size = 14),
        axis.text.x = element_text(size = 14),  # Increase x-axis label and tick font size
        axis.text.y = element_text(size = 14),  # Increase y-axis label and tick font size
        axis.title.x = element_text(size = 14),  # Increase x-axis title font size
        axis.title.y = element_text(size = 14),   # Increase y-axis title font size
        plot.caption = element_text(hjust = 0, face = "italic", size = 8)
  )
ggsave("figures/F10 MuslimShare_PartyVoteShare_2024.jpeg", 
       width = 8, height = 6, dpi = 300)




