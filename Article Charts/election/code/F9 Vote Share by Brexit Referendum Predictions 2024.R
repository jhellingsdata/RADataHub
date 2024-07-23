
combined_data <- ge_2024[!is.na(LeavePct), 
                         list(LeavePct, VoteShare_CON, VoteShare_LAB, 
                              VoteShare_LIBDEM, VoteShare_GREEN,
                              VoteShare_REFORM, VoteShare_Sans_C_L)]

# Bin LeavePct into intervals and calculate midpoints
bin_width <- 0.05
combined_data[, LeavePct_bin := cut(LeavePct, 
                                    breaks = seq(0, max(LeavePct) + bin_width, by = bin_width), 
                                    include.lowest = TRUE)]
combined_data[, LeavePct_mid := (as.numeric(sub("[\\[(](.+),.*", "\\1", as.character(LeavePct_bin))) + 
                                   as.numeric(sub(".*,([^]]*)\\]", "\\1", as.character(LeavePct_bin)))) / 2]

# Compute the average vote shares within each bin
combined_data_avg <- combined_data[, .(VoteShare_CON = mean(VoteShare_CON, na.rm = T),
                                       VoteShare_LAB = mean(VoteShare_LAB, na.rm = T),
                                       VoteShare_LIBDEM = mean(VoteShare_LIBDEM, na.rm = T),
                                       VoteShare_GREEN = mean(VoteShare_GREEN, na.rm = T),
                                       VoteShare_REFORM = mean(VoteShare_REFORM, na.rm = T),
                                       VoteShare_Sans_C_L = mean(VoteShare_Sans_C_L, na.rm = T)),
                                   by = list(LeavePct_mid)]

# Convert the averaged data.table to long format
t1_long_avg <- melt(combined_data_avg, id.vars = "LeavePct_mid", 
                    measure.vars = c("VoteShare_CON", "VoteShare_LAB", 
                                     "VoteShare_LIBDEM", "VoteShare_GREEN",
                                     "VoteShare_REFORM", "VoteShare_Sans_C_L"),
                    variable.name = "Party", value.name = "VoteShare")

t1_long_avg[Party=="VoteShare_CON", Party := c("Conservative")]
t1_long_avg[Party=="VoteShare_LAB", Party := c("Labour")]
t1_long_avg[Party=="VoteShare_LIBDEM", Party := c("Liberal\nDemocrats")]
t1_long_avg[Party=="VoteShare_GREEN", Party := c("Green")]
t1_long_avg[Party=="VoteShare_REFORM", Party := c("Reform UK")]
t1_long_avg[Party=="VoteShare_Sans_C_L", Party := c("Others")]

party_colors <- c("Conservative" = "#0073e6",  
                  "Labour" = "red",  
                  "Liberal\nDemocrats" = "orange",  
                  "Green" = "green",  
                  "Reform UK" = "purple",  
                  "Others" = "lightgray")  

# Create the stacked area plot
ggplot(t1_long_avg, aes(x = LeavePct_mid, y = VoteShare, fill = Party)) +
  geom_area(alpha = 0.6, size = 0.5, colour = "white") +
  scale_fill_manual(values = party_colors) +
  geom_vline(xintercept = 0.50, linetype = "dashed", color = "black") +
  labs(title = "Vote Share by Party and Predicted Leave Vote",
       x = "Predicted Leave Vote",
       y = "Party Vote Share",
       caption = "Data: 2016 Brexit Referendum estimates on 2024 boundaries by Professor Chris Hanretty.\nNotes: The figure excludes data for Northern Ireland.\nCredits: Apurav Bhatiya, University of Birmingham") +
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
ggsave("figures/F9 BrexitLeaveVote_PartyVoteShare_2024.jpeg", 
       width = 8, height = 6, dpi = 300)




